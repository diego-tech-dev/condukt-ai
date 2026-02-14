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

from missiongraph.parser import parse_file
from missiongraph.serialization import program_to_ast
from missiongraph.spec import AST_VERSION, TRACE_VERSION


DEFAULT_PROGRAMS = [
    "examples/ship_release.mgl",
    "examples/release_artifacts.mgl",
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run MissionGraph Python/Rust contract conformance checks."
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
        default="rust/missiongraph-rs/Cargo.toml",
        help="Path to rust bootstrap Cargo.toml",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable summary",
    )
    args = parser.parse_args(argv)

    root = ROOT
    programs = args.program or DEFAULT_PROGRAMS
    rust_manifest = (root / args.rust_manifest).resolve()

    summary = run_conformance_suite(
        root=root,
        programs=programs,
        rust_manifest=rust_manifest,
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
) -> dict[str, Any]:
    cases: list[dict[str, Any]] = []
    for program in programs:
        cases.append(
            run_case(
                root=root,
                program_path=Path(program),
                rust_manifest=rust_manifest,
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

    task_order = [task["name"] for task in ast.get("tasks", [])]

    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".ast.json",
        prefix="missiongraph-",
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


if __name__ == "__main__":
    raise SystemExit(main())
