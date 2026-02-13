from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .executor import ExecutionError, execute_program
from .parser import ParseError, parse_file, parse_literal
from .planner import build_execution_levels, build_execution_order, build_mermaid_graph
from .serialization import program_to_ast
from .validator import validate_program


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="mgl")
    sub = parser.add_subparsers(dest="command", required=True)

    parse_cmd = sub.add_parser("parse", help="Parse a .mgl program")
    parse_cmd.add_argument("program", type=str)

    validate_cmd = sub.add_parser("validate", help="Validate a .mgl program")
    validate_cmd.add_argument("program", type=str)
    validate_cmd.add_argument(
        "--capability",
        action="append",
        default=[],
        help="Capability names granted for validation",
    )
    validate_cmd.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable validation output",
    )

    plan_cmd = sub.add_parser("plan", help="Show execution order")
    plan_cmd.add_argument("program", type=str)
    plan_cmd.add_argument(
        "--capability",
        action="append",
        default=[],
        help="Capability names granted for validation",
    )

    graph_cmd = sub.add_parser("graph", help="Render plan graph as Mermaid")
    graph_cmd.add_argument("program", type=str)

    run_cmd = sub.add_parser("run", help="Execute a .mgl program")
    run_cmd.add_argument("program", type=str)
    run_cmd.add_argument(
        "--capability",
        action="append",
        default=[],
        help="Capability names granted to this run",
    )
    run_cmd.add_argument(
        "--var",
        action="append",
        default=[],
        help='Runtime variable as key=value (example: --var risk=0.2)',
    )
    run_cmd.add_argument(
        "--trace-out",
        type=str,
        default="",
        help="Optional path to write JSON trace output",
    )
    run_cmd.add_argument(
        "--sequential",
        action="store_true",
        help="Run tasks one-at-a-time even when DAG levels allow parallelism",
    )
    run_cmd.add_argument(
        "--max-parallel",
        type=int,
        default=4,
        help="Maximum workers to run concurrently per dependency level",
    )

    args = parser.parse_args(argv)

    if args.command == "parse":
        program = _safe_parse_file(args.program)
        if program is None:
            return 1
        print(json.dumps(program_to_ast(program), indent=2))
        return 0

    if args.command == "validate":
        program = _safe_parse_file(args.program)
        if program is None:
            return 1
        errors = validate_program(program, capabilities=set(args.capability))
        if args.json:
            print(
                json.dumps(
                    {
                        "program": str(Path(args.program).expanduser().resolve()),
                        "valid": not errors,
                        "errors": errors,
                    },
                    indent=2,
                )
            )
        else:
            if errors:
                for err in errors:
                    print(err, file=sys.stderr)
            else:
                print("valid")
        return 0 if not errors else 1

    if args.command == "plan":
        program = _safe_parse_file(args.program)
        if program is None:
            return 1
        errors = validate_program(program, capabilities=set(args.capability))
        if errors:
            for err in errors:
                print(err, file=sys.stderr)
            return 1
        levels = build_execution_levels(program.tasks)
        order = build_execution_order(program.tasks)
        print(
            json.dumps(
                {
                    "task_order": [task.name for task in order],
                    "levels": [[task.name for task in level] for level in levels],
                },
                indent=2,
            )
        )
        return 0

    if args.command == "graph":
        program = _safe_parse_file(args.program)
        if program is None:
            return 1
        errors = validate_program(program, capabilities=None)
        if errors:
            for err in errors:
                print(err, file=sys.stderr)
            return 1
        print(build_mermaid_graph(program.tasks))
        return 0

    if args.command == "run":
        program = _safe_parse_file(args.program)
        if program is None:
            return 1
        variables = _parse_vars(args.var)
        try:
            trace = execute_program(
                program,
                capabilities=set(args.capability),
                variables=variables,
                parallel=not args.sequential,
                max_parallel=args.max_parallel,
            )
        except ExecutionError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        print(json.dumps(trace, indent=2))
        if args.trace_out:
            path = Path(args.trace_out).expanduser().resolve()
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(trace, indent=2), encoding="utf-8")
        return 0 if trace["status"] == "ok" else 1

    print(f"unknown command: {args.command}", file=sys.stderr)
    return 1


def _parse_vars(raw_vars: list[str]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for item in raw_vars:
        if "=" not in item:
            raise ExecutionError(f"invalid --var format: {item}, expected key=value")
        key, value = item.split("=", 1)
        key = key.strip()
        if not key:
            raise ExecutionError(f"invalid --var key in '{item}'")
        result[key] = parse_literal(value.strip())
    return result


def _safe_parse_file(path: str):
    try:
        return parse_file(path)
    except ParseError as exc:
        print(str(exc), file=sys.stderr)
        return None


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
