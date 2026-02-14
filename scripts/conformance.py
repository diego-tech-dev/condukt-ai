#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from condukt.parser import parse_file
from condukt.serialization import program_to_ast
from condukt.spec import AST_VERSION, TRACE_VERSION


DEFAULT_PROGRAMS = [
    "examples/ship_release.mgl",
    "examples/release_artifacts.mgl",
    "examples/release_fanout.mgl",
    "examples/release_resilient.mgl",
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run Condukt Python/Rust contract conformance checks."
    )
    parser.add_argument(
        "--program",
        action="append",
        default=[],
        help="Program path to validate (repeatable). Defaults to built-in examples.",
    )
    parser.add_argument(
        "--rust-manifest",
        type=str,
        default="rust/condukt-rs/Cargo.toml",
        help="Path to rust bootstrap Cargo.toml",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable summary",
    )
    parser.add_argument(
        "--require-goldens",
        action="store_true",
        help="Require matching golden AST/trace contract projections for each program.",
    )
    args = parser.parse_args(argv)

    root = ROOT
    programs = args.program or DEFAULT_PROGRAMS
    rust_manifest = (root / args.rust_manifest).resolve()

    summary = run_conformance_suite(
        root=root,
        programs=programs,
        rust_manifest=rust_manifest,
        require_goldens=args.require_goldens,
    )

    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        print(_format_summary(summary))
    return 0 if summary["ok"] else 1


def run_conformance_suite(
    root: Path,
    programs: list[str],
    rust_manifest: Path,
    require_goldens: bool,
) -> dict[str, Any]:
    cases: list[dict[str, Any]] = []
    for program in programs:
        cases.append(
            run_case(
                root=root,
                program_path=Path(program),
                rust_manifest=rust_manifest,
                require_goldens=require_goldens,
            )
        )

    return {
        "ok": all(case["ok"] for case in cases),
        "programs": [case["program"] for case in cases],
        "cases": cases,
    }


def run_case(
    root: Path,
    program_path: Path,
    rust_manifest: Path,
    require_goldens: bool,
) -> dict[str, Any]:
    resolved_program = (root / program_path).resolve()
    case: dict[str, Any] = {
        "program": str(resolved_program),
        "ok": False,
        "errors": [],
    }

    if not resolved_program.exists():
        case["errors"].append(f"program does not exist: {resolved_program}")
        return case
    if not rust_manifest.exists():
        case["errors"].append(f"rust manifest does not exist: {rust_manifest}")
        return case

    try:
        ast = program_to_ast(parse_file(resolved_program))
    except Exception as exc:
        case["errors"].append(f"python parse failed: {exc}")
        return case

    case["python_ast_version"] = ast.get("ast_version")
    if ast.get("ast_version") != AST_VERSION:
        case["errors"].append(
            f"python AST version mismatch: {ast.get('ast_version')} != {AST_VERSION}"
        )
        return case

    if require_goldens:
        ast_golden_path, trace_golden_path = _golden_paths_for_program(
            root, resolved_program
        )
        if not ast_golden_path.exists():
            case["errors"].append(f"missing AST golden: {ast_golden_path}")
            return case
        if not trace_golden_path.exists():
            case["errors"].append(f"missing trace golden: {trace_golden_path}")
            return case
        try:
            ast_golden = json.loads(ast_golden_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            case["errors"].append(f"invalid AST golden JSON ({ast_golden_path}): {exc}")
            return case
        case["golden_ast_match"] = ast == ast_golden
        if ast != ast_golden:
            case["errors"].append("python AST does not match golden AST")
            return case

    try:
        expected_levels = _build_levels(ast.get("tasks", []))
    except ValueError as exc:
        case["errors"].append(f"python AST dependency resolution failed: {exc}")
        return case
    task_order = [name for level in expected_levels for name in level]
    expected_mode = (
        "parallel" if any(len(level) > 1 for level in expected_levels) else "sequential"
    )
    expected_max_parallel = max((len(level) for level in expected_levels), default=1)

    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".ast.json",
        prefix="condukt-",
        encoding="utf-8",
        delete=False,
    ) as handle:
        ast_file = Path(handle.name)
        handle.write(json.dumps(ast, indent=2))

    try:
        check_proc = _run_command(
            [
                "cargo",
                "run",
                "--manifest-path",
                str(rust_manifest),
                "--",
                "check-ast",
                str(ast_file),
                "--json",
            ],
            cwd=root,
        )
        try:
            check_payload = json.loads(check_proc.stdout)
        except json.JSONDecodeError as exc:
            case["errors"].append(
                f"rust check-ast returned invalid JSON: {exc}: {check_proc.stdout.strip()}"
            )
            return case
        case["rust_check_ok"] = check_payload.get("ok")
        case["rust_ast_version"] = check_payload.get("ast_version")
        if check_proc.returncode != 0:
            details = check_payload.get("errors") or [
                _format_process_failure("check-ast", check_proc)
            ]
            case["errors"].append(f"check-ast failed: {details}")
            return case
        if not check_payload.get("ok"):
            case["errors"].append(
                f"check-ast returned non-ok payload: {check_payload.get('errors', [])}"
            )
            return case
        if check_payload.get("ast_version") != AST_VERSION:
            case["errors"].append(
                f"rust AST version mismatch: {check_payload.get('ast_version')} != {AST_VERSION}"
            )
            return case

        trace_proc = _run_command(
            [
                "cargo",
                "run",
                "--manifest-path",
                str(rust_manifest),
                "--",
                "trace-skeleton",
                str(ast_file),
            ],
            cwd=root,
        )
        if trace_proc.returncode != 0:
            case["errors"].append(
                _format_process_failure("trace-skeleton", trace_proc)
            )
            return case

        try:
            rust_trace = json.loads(trace_proc.stdout)
        except json.JSONDecodeError as exc:
            case["errors"].append(f"rust trace-skeleton returned invalid JSON: {exc}")
            return case

        case["rust_trace_version"] = rust_trace.get("trace_version")
        if rust_trace.get("trace_version") != TRACE_VERSION:
            case["errors"].append(
                "rust trace_version mismatch: "
                f"{rust_trace.get('trace_version')} != {TRACE_VERSION}"
            )
        if rust_trace.get("goal") != ast.get("goal"):
            case["errors"].append("rust trace goal does not match python AST goal")
        if rust_trace.get("task_order") != task_order:
            case["errors"].append("rust trace task_order does not match python AST")
        execution = rust_trace.get("execution", {})
        case["rust_execution_mode"] = execution.get("mode")
        case["rust_execution_levels"] = execution.get("levels")
        if execution.get("levels") != expected_levels:
            case["errors"].append(
                "rust trace execution.levels does not match python dependency levels"
            )
        if execution.get("mode") != expected_mode:
            case["errors"].append(
                f"rust execution.mode mismatch: {execution.get('mode')} != {expected_mode}"
            )
        if execution.get("max_parallel") != expected_max_parallel:
            case["errors"].append(
                "rust execution.max_parallel mismatch: "
                f"{execution.get('max_parallel')} != {expected_max_parallel}"
            )
        if require_goldens:
            trace_golden = json.loads(trace_golden_path.read_text(encoding="utf-8"))
            case["golden_trace_contract_match"] = (
                _trace_contract_projection(rust_trace)
                == _trace_contract_projection(trace_golden)
            )
            if not case["golden_trace_contract_match"]:
                case["errors"].append(
                    "rust trace contract projection does not match golden trace"
                )
    finally:
        ast_file.unlink(missing_ok=True)

    case["ok"] = len(case["errors"]) == 0
    return case


def _run_command(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


def _format_process_failure(
    step: str,
    proc: subprocess.CompletedProcess[str],
) -> str:
    stderr = proc.stderr.strip()
    stdout = proc.stdout.strip()
    details = stderr or stdout or "<no output>"
    return f"{step} failed (exit={proc.returncode}): {details}"


def _format_summary(summary: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append(f"overall: {'ok' if summary['ok'] else 'failed'}")
    for case in summary["cases"]:
        status = "ok" if case["ok"] else "failed"
        lines.append(f"- {status}: {case['program']}")
        for err in case["errors"]:
            lines.append(f"  - {err}")
    return "\n".join(lines)


def _build_levels(tasks: list[dict[str, Any]]) -> list[list[str]]:
    names = [str(task["name"]) for task in tasks]
    if len(set(names)) != len(names):
        raise ValueError("duplicate task names")

    in_degree = {name: 0 for name in names}
    children: dict[str, list[str]] = {name: [] for name in names}
    position = {name: idx for idx, name in enumerate(names)}

    for task in tasks:
        task_name = str(task["name"])
        for dep in task.get("after", []) or []:
            dep_name = str(dep)
            if dep_name not in children:
                raise ValueError(
                    f"task '{task_name}' depends on unknown task '{dep_name}'"
                )
            children[dep_name].append(task_name)
            in_degree[task_name] += 1

    for dep_name in children:
        children[dep_name].sort(key=lambda child: position.get(child, 1_000_000))

    ready = [name for name in names if in_degree[name] == 0]
    levels: list[list[str]] = []
    seen = 0
    while ready:
        current = ready
        levels.append(current)
        seen += len(current)
        next_ready: list[str] = []
        for node in current:
            for child in children[node]:
                in_degree[child] -= 1
                if in_degree[child] == 0:
                    next_ready.append(child)
        ready = next_ready

    if seen != len(names):
        unresolved = [name for name in names if in_degree[name] > 0]
        raise ValueError(f"cycle detected in plan: {', '.join(unresolved)}")
    return levels


def _golden_paths_for_program(root: Path, program_path: Path) -> tuple[Path, Path]:
    stem = program_path.stem
    golden_dir = root / "tests" / "golden"
    return (
        golden_dir / f"{stem}.ast.json",
        golden_dir / f"{stem}.trace.normalized.json",
    )


def _trace_contract_projection(trace: dict[str, Any]) -> dict[str, Any]:
    return {
        "trace_version": trace.get("trace_version"),
        "goal": trace.get("goal"),
        "execution": trace.get("execution"),
        "task_order": trace.get("task_order"),
    }


if __name__ == "__main__":
    raise SystemExit(main())
