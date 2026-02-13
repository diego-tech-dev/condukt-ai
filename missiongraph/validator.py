from __future__ import annotations

from pathlib import Path

from .models import Program
from .planner import PlanError, build_execution_order
from .safe_eval import EvalError, eval_expr


def validate_program(
    program: Program,
    capabilities: set[str] | None = None,
) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()

    for task in program.tasks:
        if task.name in seen:
            errors.append(f"line {task.line}: duplicate task name '{task.name}'")
        seen.add(task.name)

    for task in program.tasks:
        worker_path = _resolve_worker(program.base_dir, task.worker)
        if not worker_path.exists():
            errors.append(
                f"line {task.line}: worker '{task.worker}' does not exist "
                f"({worker_path})"
            )
        if task.timeout_seconds is not None and task.timeout_seconds <= 0:
            errors.append(
                f"line {task.line}: task '{task.name}' timeout_seconds must be > 0"
            )
        if task.retries < 0:
            errors.append(
                f"line {task.line}: task '{task.name}' retries must be >= 0"
            )
        if task.backoff_seconds < 0:
            errors.append(
                f"line {task.line}: task '{task.name}' backoff_seconds must be >= 0"
            )
        if task.backoff_seconds > 0 and task.retries == 0:
            errors.append(
                f"line {task.line}: task '{task.name}' backoff_seconds requires retries > 0"
            )
        if capabilities is not None:
            missing = sorted(task.requires - capabilities)
            if missing:
                errors.append(
                    f"line {task.line}: task '{task.name}' requires missing "
                    f"capabilities: {', '.join(missing)}"
                )

    producer_by_artifact: dict[str, str] = {}
    for task in program.tasks:
        for artifact in task.produces:
            producer = producer_by_artifact.get(artifact)
            if producer is not None and producer != task.name:
                errors.append(
                    f"line {task.line}: artifact '{artifact}' is produced by multiple tasks "
                    f"('{producer}', '{task.name}')"
                )
            else:
                producer_by_artifact[artifact] = task.name
        for artifact in task.consumes:
            if artifact in task.produces:
                errors.append(
                    f"line {task.line}: task '{task.name}' cannot both consume and produce "
                    f"artifact '{artifact}'"
                )

    ancestors_by_task = _build_ancestor_map(program)
    for task in program.tasks:
        for artifact in task.consumes:
            producer = producer_by_artifact.get(artifact)
            if producer is None:
                errors.append(
                    f"line {task.line}: task '{task.name}' consumes unknown artifact '{artifact}'"
                )
                continue
            if producer not in ancestors_by_task.get(task.name, set()):
                errors.append(
                    f"line {task.line}: task '{task.name}' consumes artifact '{artifact}' "
                    f"from '{producer}' but has no dependency path to that producer"
                )

    for check in program.verify:
        try:
            eval_expr(check.expression, {})
        except EvalError:
            # Name errors are expected here; syntax-level failure should be caught.
            pass
        except Exception as exc:  # pragma: no cover
            errors.append(
                f"line {check.line}: verify expression could not be parsed: {exc}"
            )

    try:
        build_execution_order(program.tasks)
    except PlanError as exc:
        errors.append(str(exc))

    return errors


def _resolve_worker(base_dir: Path, worker: str) -> Path:
    path = Path(worker)
    if path.is_absolute():
        return path
    return (base_dir / path).resolve()


def _build_ancestor_map(program: Program) -> dict[str, set[str]]:
    task_by_name = {task.name: task for task in program.tasks}
    memo: dict[str, set[str]] = {}
    visiting: set[str] = set()

    def _ancestors(task_name: str) -> set[str]:
        if task_name in memo:
            return memo[task_name]
        if task_name in visiting:
            return set()

        visiting.add(task_name)
        out: set[str] = set()
        task = task_by_name.get(task_name)
        if task is not None:
            for dep in task.after:
                if dep not in task_by_name:
                    continue
                out.add(dep)
                out.update(_ancestors(dep))
        visiting.remove(task_name)
        memo[task_name] = out
        return out

    return {name: _ancestors(name) for name in task_by_name}
