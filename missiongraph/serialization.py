from __future__ import annotations

from typing import Any

from .models import Program, Task
from .spec import AST_VERSION


def program_to_ast(program: Program) -> dict[str, Any]:
    return {
        "ast_version": AST_VERSION,
        "goal": program.goal,
        "types": {
            name: [
                {
                    "path": spec.path,
                    "type": spec.expected_type,
                    "optional": spec.optional,
                    "line": spec.line,
                }
                for spec in specs
            ]
            for name, specs in sorted(program.types.items())
        },
        "constraints": [
            {"key": c.key, "op": c.op, "value": c.value, "line": c.line}
            for c in program.constraints
        ],
        "tasks": [_task_to_ast(t) for t in program.tasks],
        "verify": [{"line": c.line, "expression": c.expression} for c in program.verify],
    }


def _task_to_ast(task: Task) -> dict[str, Any]:
    item = {
        "name": task.name,
        "worker": task.worker,
        "requires": sorted(task.requires),
        "after": task.after,
        "input_schema": [
            {
                "path": spec.path,
                "type": spec.expected_type,
                "optional": spec.optional,
                "line": spec.line,
            }
            for spec in task.input_schema
        ],
        "output_schema": [
            {
                "path": spec.path,
                "type": spec.expected_type,
                "optional": spec.optional,
                "line": spec.line,
            }
            for spec in task.output_schema
        ],
        "line": task.line,
    }
    if task.consumes:
        item["consumes"] = task.consumes
    if task.produces:
        item["produces"] = task.produces
    if task.consumes_types:
        item["consumes_types"] = dict(sorted(task.consumes_types.items()))
    if task.produces_types:
        item["produces_types"] = dict(sorted(task.produces_types.items()))
    if task.timeout_seconds is not None:
        item["timeout_seconds"] = task.timeout_seconds
    if task.retries > 0:
        item["retries"] = task.retries
    if task.backoff_seconds > 0:
        item["backoff_seconds"] = task.backoff_seconds
    return item
