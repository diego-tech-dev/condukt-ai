#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from conformance import DEFAULT_PROGRAMS, ROOT, run_conformance_suite


FEATURE_BY_STEM = {
    "ship_release": "core-sequential",
    "release_artifacts": "artifact-flow",
    "release_fanout": "parallel-fanout",
    "release_resilient": "resilient-policies",
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build cross-runtime parity matrix from MissionGraph conformance checks."
    )
    parser.add_argument(
        "--program",
        action="append",
        default=[],
        help="Program path to include (repeatable). Defaults to built-in matrix set.",
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
        help="Emit machine-readable matrix payload",
    )
    args = parser.parse_args(argv)

    programs = args.program or DEFAULT_PROGRAMS
    rust_manifest = (ROOT / args.rust_manifest).resolve()
    summary = run_conformance_suite(
        root=ROOT,
        programs=programs,
        rust_manifest=rust_manifest,
        require_goldens=True,
    )
    matrix = _build_matrix(summary)

    if args.json:
        print(json.dumps(matrix, indent=2))
    else:
        print(_format_matrix(matrix))
    return 0 if matrix["ok"] else 1


def _build_matrix(summary: dict[str, Any]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for case in summary["cases"]:
        program = str(case["program"])
        stem = Path(program).stem
        rows.append(
            {
                "feature": FEATURE_BY_STEM.get(stem, stem),
                "program": program,
                "ok": case["ok"],
                "python_ast_version": case.get("python_ast_version"),
                "rust_ast_version": case.get("rust_ast_version"),
                "rust_trace_version": case.get("rust_trace_version"),
                "rust_execution_mode": case.get("rust_execution_mode"),
                "golden_ast_match": case.get("golden_ast_match"),
                "golden_trace_contract_match": case.get(
                    "golden_trace_contract_match"
                ),
                "errors": case.get("errors", []),
            }
        )

    return {
        "ok": summary["ok"] and all(row["ok"] for row in rows),
        "programs": [row["program"] for row in rows],
        "rows": rows,
    }


def _format_matrix(matrix: dict[str, Any]) -> str:
    lines = [f"overall: {'ok' if matrix['ok'] else 'failed'}"]
    for row in matrix["rows"]:
        status = "ok" if row["ok"] else "failed"
        lines.append(
            f"- {status}: {row['feature']} ({Path(row['program']).name}) "
            f"[mode={row['rust_execution_mode']}]"
        )
        for err in row["errors"]:
            lines.append(f"  - {err}")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
