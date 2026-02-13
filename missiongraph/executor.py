from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
import shlex
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .models import Constraint, FieldSpec, Program, Task, VerifyCheck
from .planner import build_execution_levels
from .safe_eval import EvalError, eval_expr
from .spec import (
    ERROR_CODE_ARTIFACT_CONSUME_MISSING,
    ERROR_CODE_ARTIFACT_OUTPUT_MISSING,
    ERROR_CODE_CONTRACT_INPUT_VIOLATION,
    ERROR_CODE_CONTRACT_OUTPUT_VIOLATION,
    ERROR_CODE_RUNTIME_EXECUTION_FAILURE,
    ERROR_CODE_WORKER_EXIT_NONZERO,
    ERROR_CODE_WORKER_OUTPUT_JSON_INVALID,
    ERROR_CODE_WORKER_TIMEOUT,
    TRACE_VERSION,
)
from .validator import validate_program


class ExecutionError(RuntimeError):
    pass


def execute_program(
    program: Program,
    capabilities: set[str] | None = None,
    variables: dict[str, Any] | None = None,
    parallel: bool = True,
    max_parallel: int = 4,
) -> dict[str, Any]:
    capabilities = capabilities or set()
    variables = variables or {}
    if max_parallel < 1:
        raise ExecutionError("max_parallel must be >= 1")

    errors = validate_program(program, capabilities=capabilities)
    if errors:
        raise ExecutionError("\n".join(errors))

    levels = build_execution_levels(program.tasks)
    ordered_tasks = [task for level in levels for task in level]
    started_at = _now()

    task_results: dict[str, dict[str, Any]] = {}
    trace_tasks: list[dict[str, Any]] = []
    shared_context: dict[str, Any] = dict(variables)
    artifact_registry: dict[str, Any] = {}

    for level in levels:
        payload_by_task: dict[str, dict[str, Any]] = {}
        input_failed = False

        for task in level:
            missing_artifacts = [
                artifact for artifact in task.consumes if artifact not in artifact_registry
            ]
            if missing_artifacts:
                failure = _build_artifact_failure_result(
                    task=task,
                    base_dir=program.base_dir,
                    missing_artifacts=missing_artifacts,
                )
                task_results[task.name] = failure
                trace_tasks.append(failure)
                input_failed = True
                break

            dep_payload = {dep: task_results[dep] for dep in task.after}
            payload = {
                "task": task.name,
                "goal": program.goal,
                "constraints": [_constraint_to_dict(c) for c in program.constraints],
                "dependencies": dep_payload,
                "artifacts": {
                    artifact: artifact_registry[artifact] for artifact in task.consumes
                },
                "variables": shared_context,
            }
            input_errors = _validate_schema(payload, task.input_schema)
            if input_errors:
                failure = _build_contract_failure_result(
                    task=task,
                    base_dir=program.base_dir,
                    stage="input",
                    errors=input_errors,
                )
                task_results[task.name] = failure
                trace_tasks.append(failure)
                input_failed = True
                break
            payload_by_task[task.name] = payload

        if input_failed:
            break

        level_results = _run_level(
            level=level,
            payload_by_task=payload_by_task,
            base_dir=program.base_dir,
            parallel=parallel,
            max_parallel=max_parallel,
        )

        level_failed = False
        for task in level:
            result = level_results[task.name]
            output_errors = _validate_schema(result.get("output", {}), task.output_schema)
            if output_errors:
                result["status"] = "error"
                result["confidence"] = 0.0
                result["error_code"] = ERROR_CODE_CONTRACT_OUTPUT_VIOLATION
                result["error"] = _merge_error(
                    result.get("error"),
                    f"output contract violation: {'; '.join(output_errors)}",
                )

            if result.get("status") == "ok":
                missing_output_artifacts = [
                    artifact for artifact in task.produces if artifact not in result["output"]
                ]
                if missing_output_artifacts:
                    result["status"] = "error"
                    result["confidence"] = 0.0
                    result["error_code"] = ERROR_CODE_ARTIFACT_OUTPUT_MISSING
                    result["error"] = _merge_error(
                        result.get("error"),
                        "declared produced artifact(s) missing from output: "
                        + ", ".join(missing_output_artifacts),
                    )
                else:
                    for artifact in task.produces:
                        artifact_registry[artifact] = result["output"][artifact]

            task_results[task.name] = result
            trace_tasks.append(result)
            if result.get("status") != "ok":
                level_failed = True

        for task in level:
            result = task_results[task.name]
            if result.get("status") != "ok":
                continue
            if isinstance(result.get("output"), dict):
                for key, value in result["output"].items():
                    if key not in task_results:
                        shared_context[key] = value

        if level_failed:
            break

    constraints_report = _evaluate_constraints(program.constraints, shared_context)
    verify_report = _evaluate_verify(program.verify, task_results, shared_context)
    verify_summary = _summarize_verify(verify_report)

    task_status_ok = all(task["status"] == "ok" for task in trace_tasks)
    constraints_ok = all(item["passed"] is not False for item in constraints_report)
    verify_ok = verify_summary["failed"] == 0
    overall_ok = task_status_ok and constraints_ok and verify_ok

    return {
        "trace_version": TRACE_VERSION,
        "goal": program.goal,
        "status": "ok" if overall_ok else "failed",
        "started_at": started_at,
        "finished_at": _now(),
        "capabilities": sorted(capabilities),
        "execution": {
            "mode": "parallel" if parallel and max_parallel > 1 else "sequential",
            "max_parallel": max_parallel if parallel else 1,
            "levels": [[task.name for task in level] for level in levels],
        },
        "task_order": [task.name for task in ordered_tasks],
        "tasks": trace_tasks,
        "constraints": constraints_report,
        "verify": verify_report,
        "verify_summary": verify_summary,
    }


def _run_level(
    level: list[Task],
    payload_by_task: dict[str, dict[str, Any]],
    base_dir: Path,
    parallel: bool,
    max_parallel: int,
) -> dict[str, dict[str, Any]]:
    if parallel and len(level) > 1 and max_parallel > 1:
        return _run_level_parallel(
            level=level,
            payload_by_task=payload_by_task,
            base_dir=base_dir,
            max_parallel=max_parallel,
        )
    return _run_level_sequential(level=level, payload_by_task=payload_by_task, base_dir=base_dir)


def _run_level_parallel(
    level: list[Task],
    payload_by_task: dict[str, dict[str, Any]],
    base_dir: Path,
    max_parallel: int,
) -> dict[str, dict[str, Any]]:
    task_by_name = {task.name: task for task in level}
    results: dict[str, dict[str, Any]] = {}
    max_workers = min(max_parallel, len(level))

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(_run_task, task, payload_by_task[task.name], base_dir): task.name
            for task in level
        }
        for future in as_completed(futures):
            task_name = futures[future]
            task = task_by_name[task_name]
            try:
                results[task_name] = future.result()
            except Exception as exc:  # pragma: no cover
                results[task_name] = _build_runtime_failure_result(
                    task=task,
                    base_dir=base_dir,
                    error=str(exc),
                )
    return results


def _run_level_sequential(
    level: list[Task],
    payload_by_task: dict[str, dict[str, Any]],
    base_dir: Path,
) -> dict[str, dict[str, Any]]:
    results: dict[str, dict[str, Any]] = {}
    for task in level:
        try:
            results[task.name] = _run_task(task, payload_by_task[task.name], base_dir)
        except Exception as exc:  # pragma: no cover
            results[task.name] = _build_runtime_failure_result(
                task=task,
                base_dir=base_dir,
                error=str(exc),
            )
    return results


def _run_task(task: Task, payload: dict[str, Any], base_dir: Path) -> dict[str, Any]:
    command = _resolve_worker_command(task.worker, base_dir)
    max_attempts = task.retries + 1
    attempt_history: list[dict[str, Any]] = []
    result: dict[str, Any] | None = None

    for attempt in range(1, max_attempts + 1):
        result = _run_task_attempt(
            task=task,
            payload=payload,
            command=command,
            base_dir=base_dir,
            attempt=attempt,
            max_attempts=max_attempts,
        )
        attempt_history.append(
            {
                "attempt": attempt,
                "status": result.get("status"),
                "error_code": result.get("error_code"),
                "error": result.get("error"),
                "started_at": result.get("started_at"),
                "finished_at": result.get("finished_at"),
            }
        )
        if result.get("status") == "ok":
            break
        if attempt < max_attempts:
            delay = _retry_delay_seconds(task.backoff_seconds, attempt)
            if delay > 0:
                time.sleep(delay)

    if result is None:  # pragma: no cover
        raise RuntimeError("task execution produced no result")

    if max_attempts > 1:
        result["provenance"]["attempts"] = attempt_history
    return result


def _run_task_attempt(
    task: Task,
    payload: dict[str, Any],
    command: list[str],
    base_dir: Path,
    attempt: int,
    max_attempts: int,
) -> dict[str, Any]:
    started_at = _now()
    timeout_seconds = task.timeout_seconds if task.timeout_seconds is not None else None

    try:
        proc = subprocess.run(
            command,
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout_seconds,
        )
        stdout = proc.stdout.strip()
        stderr = proc.stderr.strip()
        return _build_task_result(
            task=task,
            command=command,
            base_dir=base_dir,
            started_at=started_at,
            finished_at=_now(),
            stdout=stdout,
            stderr=stderr,
            return_code=proc.returncode,
            parsed=_parse_worker_output(stdout, proc.returncode),
            attempt=attempt,
            max_attempts=max_attempts,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = _coerce_stream_text(exc.stdout).strip()
        stderr = _coerce_stream_text(exc.stderr).strip()
        parsed = {
            "status": "error",
            "output": {},
            "confidence": 0.0,
            "error_code": ERROR_CODE_WORKER_TIMEOUT,
            "error": f"worker timed out after {task.timeout_seconds:g}s",
        }
        return _build_task_result(
            task=task,
            command=command,
            base_dir=base_dir,
            started_at=started_at,
            finished_at=_now(),
            stdout=stdout,
            stderr=stderr,
            return_code=None,
            parsed=parsed,
            attempt=attempt,
            max_attempts=max_attempts,
        )


def _build_task_result(
    task: Task,
    command: list[str],
    base_dir: Path,
    started_at: str,
    finished_at: str,
    stdout: str,
    stderr: str,
    return_code: int | None,
    parsed: dict[str, Any],
    attempt: int,
    max_attempts: int,
) -> dict[str, Any]:
    if return_code not in (None, 0) and parsed.get("status") == "ok":
        parsed["status"] = "error"
        parsed["error_code"] = ERROR_CODE_WORKER_EXIT_NONZERO
        parsed["error"] = _merge_error(
            parsed.get("error"),
            f"worker exited with return code {return_code}",
        )

    output = parsed.get("output")
    if not isinstance(output, dict):
        output = {"value": output}

    confidence = parsed.get("confidence", 0.5 if parsed.get("status") == "ok" else 0.0)
    try:
        confidence = float(confidence)
    except (TypeError, ValueError):
        confidence = 0.0

    default_provenance = {
        "worker": str(_resolve_worker_path(task.worker, base_dir)),
        "command": " ".join(shlex.quote(part) for part in command),
        "return_code": return_code,
        "stdout_sha256": hashlib.sha256(stdout.encode("utf-8")).hexdigest(),
    }
    if max_attempts > 1:
        default_provenance["attempt"] = attempt
        default_provenance["max_attempts"] = max_attempts
    if task.timeout_seconds is not None:
        default_provenance["timeout_seconds"] = task.timeout_seconds
    if task.retries > 0:
        default_provenance["retries"] = task.retries
    if task.backoff_seconds > 0:
        default_provenance["backoff_seconds"] = task.backoff_seconds
    if task.consumes:
        default_provenance["consumes"] = task.consumes
    if task.produces:
        default_provenance["produces"] = task.produces
    provenance = parsed.get("provenance")
    if not isinstance(provenance, dict):
        provenance = {}
    provenance = {**default_provenance, **provenance}

    result = {
        "task": task.name,
        "worker": task.worker,
        "status": parsed.get("status", "error"),
        "confidence": confidence,
        "output": output,
        "error_code": parsed.get("error_code"),
        "error": parsed.get("error"),
        "started_at": started_at,
        "finished_at": finished_at,
        "provenance": provenance,
    }
    if stderr:
        result["stderr"] = stderr
    return result


def _parse_worker_output(stdout: str, return_code: int) -> dict[str, Any]:
    if stdout:
        try:
            candidate = json.loads(stdout)
            if not isinstance(candidate, dict):
                raise ValueError("worker output must be a JSON object")
            return candidate
        except (json.JSONDecodeError, ValueError) as exc:
            return {
                "status": "error",
                "output": {},
                "confidence": 0.0,
                "error_code": ERROR_CODE_WORKER_OUTPUT_JSON_INVALID,
                "error": f"worker output is not valid JSON: {exc}",
            }
    return {
        "status": "ok" if return_code == 0 else "error",
        "output": {},
        "confidence": 0.5 if return_code == 0 else 0.0,
    }


def _coerce_stream_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def _retry_delay_seconds(backoff_seconds: float, attempt: int) -> float:
    if backoff_seconds <= 0:
        return 0.0
    return backoff_seconds * float(2 ** (attempt - 1))


def _resolve_worker_command(worker: str, base_dir: Path) -> list[str]:
    path = _resolve_worker_path(worker, base_dir)
    if path.suffix == ".py":
        return [sys.executable, str(path)]
    if path.suffix in {".js", ".mjs", ".cjs"}:
        if shutil.which("node") is None:
            raise ExecutionError("node is required for JavaScript workers")
        return ["node", str(path)]
    if path.suffix == ".ts":
        tsx_bin = shutil.which("tsx")
        if tsx_bin is not None:
            return [tsx_bin, str(path)]
        raise ExecutionError("tsx is required for TypeScript workers")
    raise ExecutionError(
        f"unsupported worker type '{path.suffix}' for task worker '{worker}'"
    )


def _resolve_worker_path(worker: str, base_dir: Path) -> Path:
    path = Path(worker)
    if path.is_absolute():
        return path
    return (base_dir / path).resolve()


def _validate_schema(payload: dict[str, Any], schema: list[FieldSpec]) -> list[str]:
    errors: list[str] = []
    for field in schema:
        exists, value = _resolve_path(payload, field.path)
        if not exists:
            if field.optional:
                continue
            errors.append(
                f"missing required field '{field.path}' (line {field.line})"
            )
            continue
        if not _matches_type(value, field.expected_type):
            errors.append(
                f"field '{field.path}' expected {field.expected_type} "
                f"but got {_value_type_name(value)} (line {field.line})"
            )
    return errors


def _resolve_path(payload: dict[str, Any], path: str) -> tuple[bool, Any]:
    current: Any = payload
    for token in path.split("."):
        if isinstance(current, dict) and token in current:
            current = current[token]
            continue
        return False, None
    return True, current


def _matches_type(value: Any, expected_type: str) -> bool:
    if expected_type == "any":
        return True
    if expected_type in {"none", "null"}:
        return value is None
    if expected_type == "bool":
        return isinstance(value, bool)
    if expected_type == "str":
        return isinstance(value, str)
    if expected_type == "int":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected_type == "float":
        return isinstance(value, float)
    if expected_type == "number":
        return (
            (isinstance(value, int) and not isinstance(value, bool))
            or isinstance(value, float)
        )
    if expected_type == "dict":
        return isinstance(value, dict)
    if expected_type == "list":
        return isinstance(value, list)
    return False


def _value_type_name(value: Any) -> str:
    if value is None:
        return "none"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        return "str"
    if isinstance(value, dict):
        return "dict"
    if isinstance(value, list):
        return "list"
    return value.__class__.__name__


def _build_contract_failure_result(
    task: Task,
    base_dir: Path,
    stage: str,
    errors: list[str],
) -> dict[str, Any]:
    now = _now()
    return {
        "task": task.name,
        "worker": task.worker,
        "status": "error",
        "confidence": 0.0,
        "output": {},
        "error_code": ERROR_CODE_CONTRACT_INPUT_VIOLATION,
        "error": f"{stage} contract violation: {'; '.join(errors)}",
        "started_at": now,
        "finished_at": now,
        "provenance": {
            "worker": str(_resolve_worker_path(task.worker, base_dir)),
            "contract_stage": stage,
            "contract_only": True,
        },
    }


def _build_artifact_failure_result(
    task: Task,
    base_dir: Path,
    missing_artifacts: list[str],
) -> dict[str, Any]:
    now = _now()
    return {
        "task": task.name,
        "worker": task.worker,
        "status": "error",
        "confidence": 0.0,
        "output": {},
        "error_code": ERROR_CODE_ARTIFACT_CONSUME_MISSING,
        "error": (
            "missing required artifact(s): " + ", ".join(missing_artifacts)
        ),
        "started_at": now,
        "finished_at": now,
        "provenance": {
            "worker": str(_resolve_worker_path(task.worker, base_dir)),
            "artifact_stage": "consume",
            "missing_artifacts": missing_artifacts,
            "artifact_only": True,
        },
    }


def _build_runtime_failure_result(
    task: Task,
    base_dir: Path,
    error: str,
) -> dict[str, Any]:
    now = _now()
    return {
        "task": task.name,
        "worker": task.worker,
        "status": "error",
        "confidence": 0.0,
        "output": {},
        "error_code": ERROR_CODE_RUNTIME_EXECUTION_FAILURE,
        "error": f"runtime execution failure: {error}",
        "started_at": now,
        "finished_at": now,
        "provenance": {
            "worker": str(_resolve_worker_path(task.worker, base_dir)),
            "runtime_failure": True,
        },
    }


def _merge_error(existing: Any, appended: str) -> str:
    if isinstance(existing, str) and existing.strip():
        return f"{existing}; {appended}"
    return appended


def _evaluate_constraints(
    constraints: list[Constraint], context: dict[str, Any]
) -> list[dict[str, Any]]:
    report: list[dict[str, Any]] = []
    for item in constraints:
        if item.key not in context:
            report.append(
                {
                    "line": item.line,
                    "expression": _constraint_expression(item),
                    "passed": None,
                    "reason": f"unresolved key: {item.key}",
                }
            )
            continue
        expression = _constraint_expression(item)
        try:
            passed = bool(eval_expr(expression, context))
            report.append(
                {
                    "line": item.line,
                    "expression": expression,
                    "passed": passed,
                }
            )
        except EvalError as exc:
            report.append(
                {
                    "line": item.line,
                    "expression": expression,
                    "passed": False,
                    "reason": str(exc),
                }
            )
    return report


def _evaluate_verify(
    checks: list[VerifyCheck],
    task_results: dict[str, dict[str, Any]],
    context: dict[str, Any],
) -> list[dict[str, Any]]:
    report: list[dict[str, Any]] = []
    eval_context = {**context, **task_results}
    for check in checks:
        try:
            passed = bool(eval_expr(check.expression, eval_context))
            report.append(
                {
                    "line": check.line,
                    "expression": check.expression,
                    "passed": passed,
                }
            )
        except EvalError as exc:
            report.append(
                {
                    "line": check.line,
                    "expression": check.expression,
                    "passed": False,
                    "reason": str(exc),
                }
            )
    return report


def _summarize_verify(report: list[dict[str, Any]]) -> dict[str, Any]:
    failures = [
        {
            "line": item["line"],
            "expression": item["expression"],
            "reason": item.get("reason"),
        }
        for item in report
        if item.get("passed") is False
    ]
    return {
        "total": len(report),
        "passed": len(report) - len(failures),
        "failed": len(failures),
        "failures": failures,
    }


def _constraint_to_dict(constraint: Constraint) -> dict[str, Any]:
    return {
        "key": constraint.key,
        "op": constraint.op,
        "value": constraint.value,
        "line": constraint.line,
    }


def _constraint_expression(constraint: Constraint) -> str:
    value = json.dumps(constraint.value)
    return f"{constraint.key} {constraint.op} {value}"


def _now() -> str:
    return datetime.now(tz=timezone.utc).isoformat()
