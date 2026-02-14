from __future__ import annotations

import ast
from dataclasses import replace
import re
from pathlib import Path
from typing import Any, NamedTuple

from .models import Constraint, FieldSpec, Program, Task, VerifyCheck


class ParseError(ValueError):
    pass


_CONSTRAINT_RE = re.compile(r"^([A-Za-z_][\w\.]*)\s*(<=|>=|==|!=|<|>)\s*(.+)$")
_GOAL_RE = re.compile(r'^goal\s+"([^"]+)"\s*$')
_TYPE_DEF_RE = re.compile(r'^type\s+([A-Za-z_][A-Za-z0-9_]*)\s+"([^"]*)"\s*$')
_TASK_HEAD_RE = re.compile(
    r'^task\s+([A-Za-z_][A-Za-z0-9_\-]*)\s+uses\s+"([^"]+)"(?:\s+(.*))?\s*$'
)
_TASK_CLAUSE_SPLIT_RE = re.compile(r"\s+(requires|after|consumes|produces|with)\s+")
_CONTRACT_TASK_RE = re.compile(r"^task\s+([A-Za-z_][A-Za-z0-9_\-]*)\s*(.*)$")
_CONTRACT_CLAUSE_RE = re.compile(
    r'\b(input|output)\s+("[^"]*"|@[A-Za-z_][A-Za-z0-9_]*)'
)
_FIELD_SPEC_RE = re.compile(r"^([A-Za-z_][\w\.]*)\s*:\s*([A-Za-z_][A-Za-z0-9_]*\??)$")
_CAP_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_\-]*$")
_ARTIFACT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_\-]*$")
_ARTIFACT_TYPED_RE = re.compile(
    r"^([A-Za-z_][A-Za-z0-9_\-]*)(?::([A-Za-z_][A-Za-z0-9_]*))?$"
)
_RETRIES_RE = re.compile(r"^\d+$")
_RETRY_IF_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_DURATION_RE = re.compile(r"^(\d+(?:\.\d+)?)(ms|s)?$")
_RETRY_IF_VALUES = {"error", "timeout", "worker_failure"}
_VALID_SCHEMA_TYPES = {
    "any",
    "bool",
    "dict",
    "float",
    "int",
    "list",
    "none",
    "null",
    "number",
    "str",
}
_SCHEMA_TYPE_ALIASES = {
    "array": "list",
    "boolean": "bool",
    "integer": "int",
    "object": "dict",
    "string": "str",
}


class _ContractClause(NamedTuple):
    inline_schema: list[FieldSpec] | None
    type_ref: str | None
    line: int


class _TaskPolicy(NamedTuple):
    timeout_seconds: float | None
    retries: int
    retry_if: str
    backoff_seconds: float
    jitter_seconds: float


def parse_file(path: str | Path) -> Program:
    file_path = Path(path).expanduser().resolve()
    if file_path.suffix.lower() != ".mgl":
        raise ParseError(
            f"{file_path}: unsupported extension '{file_path.suffix}'. "
            "Condukt programs must use .mgl files"
        )
    text = file_path.read_text(encoding="utf-8")
    program = parse_program(text, source=str(file_path))
    program.source_path = file_path
    return program


def parse_program(text: str, source: str = "<memory>") -> Program:
    lines = text.splitlines()
    goal: str | None = None
    type_defs: dict[str, list[FieldSpec]] = {}
    constraints: list[Constraint] = []
    tasks: list[Task] = []
    checks: list[VerifyCheck] = []
    task_contracts_raw: dict[str, dict[str, _ContractClause]] = {}

    idx = 0
    while idx < len(lines):
        raw = lines[idx]
        line = raw.strip()
        line_no = idx + 1
        if _is_ignored(line):
            idx += 1
            continue

        if line.startswith("goal "):
            if goal is not None:
                raise ParseError(f"{source}:{line_no}: duplicate goal declaration")
            goal = _parse_goal(line, source, line_no)
            idx += 1
            continue

        if line == "types {":
            idx, parsed = _parse_types_block(lines, idx + 1, source)
            for type_name, fields in parsed.items():
                if type_name in type_defs:
                    raise ParseError(
                        f"{source}:{line_no}: duplicate type definition '{type_name}'"
                    )
                type_defs[type_name] = fields
            continue

        if line == "constraints {":
            idx, parsed = _parse_constraints_block(lines, idx + 1, source)
            constraints.extend(parsed)
            continue

        if line == "plan {":
            idx, parsed = _parse_plan_block(lines, idx + 1, source)
            tasks.extend(parsed)
            continue

        if line == "verify {":
            idx, parsed = _parse_verify_block(lines, idx + 1, source)
            checks.extend(parsed)
            continue

        if line == "contracts {":
            idx, parsed = _parse_contracts_block(lines, idx + 1, source)
            for task_name, contract in parsed.items():
                if task_name in task_contracts_raw:
                    raise ParseError(
                        f"{source}:{line_no}: duplicate contracts for task '{task_name}'"
                    )
                task_contracts_raw[task_name] = contract
            continue

        raise ParseError(f"{source}:{line_no}: unexpected statement: {line}")

    if goal is None:
        raise ParseError(f"{source}: missing goal declaration")
    if not tasks:
        raise ParseError(f"{source}: missing plan block or task definitions")

    task_contracts = _resolve_task_contracts(
        task_contracts_raw=task_contracts_raw,
        type_defs=type_defs,
        source=source,
    )
    task_by_name = {task.name: task for task in tasks}
    unknown_contract_tasks = sorted(set(task_contracts) - set(task_by_name))
    if unknown_contract_tasks:
        raise ParseError(
            f"{source}: contracts defined for unknown task(s): "
            f"{', '.join(unknown_contract_tasks)}"
        )

    tasks = [
        replace(
            task,
            input_schema=task_contracts.get(task.name, {}).get("input", []),
            output_schema=task_contracts.get(task.name, {}).get("output", []),
        )
        for task in tasks
    ]

    return Program(
        goal=goal,
        types=type_defs,
        constraints=constraints,
        tasks=tasks,
        verify=checks,
    )


def parse_literal(raw: str) -> Any:
    value = raw.strip()
    lower = value.lower()
    if lower == "true":
        return True
    if lower == "false":
        return False
    if lower == "null":
        return None
    if re.fullmatch(r"[+-]?\d+", value):
        return int(value)
    if re.fullmatch(r"[+-]?\d+\.\d+", value):
        return float(value)
    if value.startswith('"') and value.endswith('"'):
        try:
            return ast.literal_eval(value)
        except (SyntaxError, ValueError) as exc:
            raise ParseError(f"invalid string literal: {value}") from exc
    return value


def _parse_goal(line: str, source: str, line_no: int) -> str:
    match = _GOAL_RE.match(line)
    if not match:
        raise ParseError(f'{source}:{line_no}: goal must look like: goal "your goal"')
    return match.group(1)


def _parse_constraints_block(
    lines: list[str], start: int, source: str
) -> tuple[int, list[Constraint]]:
    out: list[Constraint] = []
    idx = start
    while idx < len(lines):
        line_no = idx + 1
        line = lines[idx].strip()
        if _is_ignored(line):
            idx += 1
            continue
        if line == "}":
            return idx + 1, out
        match = _CONSTRAINT_RE.match(line)
        if not match:
            raise ParseError(
                f"{source}:{line_no}: invalid constraint syntax: {line}"
            )
        key, op, value_raw = match.groups()
        out.append(
            Constraint(
                key=key,
                op=op,
                value=parse_literal(value_raw),
                line=line_no,
            )
        )
        idx += 1
    raise ParseError(f"{source}:{start}: unterminated constraints block")


def _parse_types_block(
    lines: list[str], start: int, source: str
) -> tuple[int, dict[str, list[FieldSpec]]]:
    out: dict[str, list[FieldSpec]] = {}
    idx = start
    while idx < len(lines):
        line_no = idx + 1
        line = lines[idx].strip()
        if _is_ignored(line):
            idx += 1
            continue
        if line == "}":
            return idx + 1, out

        match = _TYPE_DEF_RE.match(line)
        if not match:
            raise ParseError(f"{source}:{line_no}: invalid type syntax: {line}")
        type_name, schema_raw = match.groups()
        if type_name in out:
            raise ParseError(f"{source}:{line_no}: duplicate type '{type_name}'")
        out[type_name] = _parse_field_specs(
            schema_raw,
            source=source,
            line_no=line_no,
            kind=f"type {type_name}",
        )
        idx += 1
    raise ParseError(f"{source}:{start}: unterminated types block")


def _parse_plan_block(
    lines: list[str], start: int, source: str
) -> tuple[int, list[Task]]:
    out: list[Task] = []
    idx = start
    while idx < len(lines):
        line_no = idx + 1
        line = lines[idx].strip()
        if _is_ignored(line):
            idx += 1
            continue
        if line == "}":
            return idx + 1, out
        out.append(_parse_task_line(line, source, line_no))
        idx += 1
    raise ParseError(f"{source}:{start}: unterminated plan block")


def _parse_task_line(line: str, source: str, line_no: int) -> Task:
    match = _TASK_HEAD_RE.match(line)
    if not match:
        raise ParseError(
            f"{source}:{line_no}: invalid task syntax: {line}"
        )

    name, worker, tail = match.groups()
    requires: set[str] = set()
    after: list[str] = []
    consumes: list[str] = []
    produces: list[str] = []
    consumes_types: dict[str, str] = {}
    produces_types: dict[str, str] = {}
    policy = _TaskPolicy(
        timeout_seconds=None,
        retries=0,
        retry_if="error",
        backoff_seconds=0.0,
        jitter_seconds=0.0,
    )
    seen_clauses: set[str] = set()
    remaining = (tail or "").strip()

    while remaining:
        if remaining.startswith("requires "):
            if "requires" in seen_clauses:
                raise ParseError(
                    f"{source}:{line_no}: duplicate requires clause for task '{name}'"
                )
            clause, remaining = _consume_task_clause_value(remaining[len("requires "):])
            if not clause:
                raise ParseError(
                    f"{source}:{line_no}: requires clause cannot be empty for task '{name}'"
                )
            requires = _parse_capabilities(clause, source, line_no)
            seen_clauses.add("requires")
            continue

        if remaining.startswith("after "):
            if "after" in seen_clauses:
                raise ParseError(
                    f"{source}:{line_no}: duplicate after clause for task '{name}'"
                )
            clause, remaining = _consume_task_clause_value(remaining[len("after "):])
            if not clause:
                raise ParseError(
                    f"{source}:{line_no}: after clause cannot be empty for task '{name}'"
                )
            after = _parse_after(clause)
            seen_clauses.add("after")
            continue

        if remaining.startswith("consumes "):
            if "consumes" in seen_clauses:
                raise ParseError(
                    f"{source}:{line_no}: duplicate consumes clause for task '{name}'"
                )
            clause, remaining = _consume_task_clause_value(remaining[len("consumes "):])
            if not clause:
                raise ParseError(
                    f"{source}:{line_no}: consumes clause cannot be empty for task '{name}'"
                )
            consumes, consumes_types = _parse_artifact_names(
                clause,
                source,
                line_no,
                "consumes",
            )
            seen_clauses.add("consumes")
            continue

        if remaining.startswith("produces "):
            if "produces" in seen_clauses:
                raise ParseError(
                    f"{source}:{line_no}: duplicate produces clause for task '{name}'"
                )
            clause, remaining = _consume_task_clause_value(remaining[len("produces "):])
            if not clause:
                raise ParseError(
                    f"{source}:{line_no}: produces clause cannot be empty for task '{name}'"
                )
            produces, produces_types = _parse_artifact_names(
                clause,
                source,
                line_no,
                "produces",
            )
            seen_clauses.add("produces")
            continue

        if remaining.startswith("with "):
            if "with" in seen_clauses:
                raise ParseError(
                    f"{source}:{line_no}: duplicate with clause for task '{name}'"
                )
            clause, remaining = _consume_task_clause_value(remaining[len("with "):])
            policy = _parse_task_policy(clause, source, line_no)
            seen_clauses.add("with")
            continue

        token = remaining.split(maxsplit=1)[0]
        raise ParseError(
            f"{source}:{line_no}: unexpected task clause '{token}' in task '{name}'"
        )

    return Task(
        name=name,
        worker=worker,
        requires=requires,
        after=after,
        consumes=consumes,
        produces=produces,
        consumes_types=consumes_types,
        produces_types=produces_types,
        timeout_seconds=policy.timeout_seconds,
        retries=policy.retries,
        retry_if=policy.retry_if,
        backoff_seconds=policy.backoff_seconds,
        jitter_seconds=policy.jitter_seconds,
        line=line_no,
    )


def _consume_task_clause_value(raw: str) -> tuple[str, str]:
    value = raw.strip()
    if not value:
        return "", ""
    match = _TASK_CLAUSE_SPLIT_RE.search(value)
    if match is None:
        return value, ""
    clause_value = value[: match.start()].strip()
    rest = f"{match.group(1)} {value[match.end():].strip()}".strip()
    return clause_value, rest


def _parse_task_policy(raw: str, source: str, line_no: int) -> _TaskPolicy:
    tokens = raw.split()
    if not tokens:
        raise ParseError(
            f"{source}:{line_no}: with clause must define task policy values"
        )
    if len(tokens) % 2 != 0:
        raise ParseError(
            f"{source}:{line_no}: with clause expects key/value pairs "
            "(timeout|retries|retry_if|backoff|jitter)"
        )

    timeout_seconds: float | None = None
    retries = 0
    retry_if = "error"
    backoff_seconds = 0.0
    jitter_seconds = 0.0
    seen: set[str] = set()

    for idx in range(0, len(tokens), 2):
        key = tokens[idx].lower()
        value = tokens[idx + 1]
        if key in seen:
            raise ParseError(
                f"{source}:{line_no}: duplicate policy key '{key}' in with clause"
            )
        seen.add(key)

        if key == "timeout":
            timeout_seconds = _parse_duration_seconds(
                value=value,
                source=source,
                line_no=line_no,
                field_name="timeout",
                allow_zero=False,
            )
            continue

        if key == "retries":
            if not _RETRIES_RE.fullmatch(value):
                raise ParseError(
                    f"{source}:{line_no}: retries must be a non-negative integer"
                )
            retries = int(value)
            continue

        if key == "backoff":
            backoff_seconds = _parse_duration_seconds(
                value=value,
                source=source,
                line_no=line_no,
                field_name="backoff",
                allow_zero=True,
            )
            continue

        if key == "jitter":
            jitter_seconds = _parse_duration_seconds(
                value=value,
                source=source,
                line_no=line_no,
                field_name="jitter",
                allow_zero=True,
            )
            continue

        if key == "retry_if":
            if not _RETRY_IF_RE.fullmatch(value):
                raise ParseError(
                    f"{source}:{line_no}: retry_if value is invalid: {value}"
                )
            normalized = value.lower()
            if normalized not in _RETRY_IF_VALUES:
                allowed = ", ".join(sorted(_RETRY_IF_VALUES))
                raise ParseError(
                    f"{source}:{line_no}: retry_if must be one of: {allowed}"
                )
            retry_if = normalized
            continue

        raise ParseError(
            f"{source}:{line_no}: unknown policy key '{key}' in with clause"
        )

    return _TaskPolicy(
        timeout_seconds=timeout_seconds,
        retries=retries,
        retry_if=retry_if,
        backoff_seconds=backoff_seconds,
        jitter_seconds=jitter_seconds,
    )


def _parse_duration_seconds(
    value: str,
    source: str,
    line_no: int,
    field_name: str,
    allow_zero: bool,
) -> float:
    match = _DURATION_RE.fullmatch(value.lower())
    if match is None:
        raise ParseError(
            f"{source}:{line_no}: {field_name} must be like 5s, 250ms, or 0.5s"
        )
    amount_raw, unit = match.groups()
    seconds = float(amount_raw)
    if unit == "ms":
        seconds /= 1000.0
    if allow_zero:
        if seconds < 0:
            raise ParseError(f"{source}:{line_no}: {field_name} must be >= 0")
    elif seconds <= 0:
        raise ParseError(f"{source}:{line_no}: {field_name} must be > 0")
    return seconds


def _parse_verify_block(
    lines: list[str], start: int, source: str
) -> tuple[int, list[VerifyCheck]]:
    out: list[VerifyCheck] = []
    idx = start
    while idx < len(lines):
        line_no = idx + 1
        line = lines[idx].strip()
        if _is_ignored(line):
            idx += 1
            continue
        if line == "}":
            return idx + 1, out
        out.append(VerifyCheck(expression=line, line=line_no))
        idx += 1
    raise ParseError(f"{source}:{start}: unterminated verify block")


def _parse_contracts_block(
    lines: list[str], start: int, source: str
) -> tuple[int, dict[str, dict[str, _ContractClause]]]:
    out: dict[str, dict[str, _ContractClause]] = {}
    idx = start
    while idx < len(lines):
        line_no = idx + 1
        line = lines[idx].strip()
        if _is_ignored(line):
            idx += 1
            continue
        if line == "}":
            return idx + 1, out
        task_name, input_schema, output_schema = _parse_contract_line(
            line, source, line_no
        )
        if task_name in out:
            raise ParseError(
                f"{source}:{line_no}: duplicate contract declaration for task '{task_name}'"
            )
        out[task_name] = {"input": input_schema, "output": output_schema}
        idx += 1
    raise ParseError(f"{source}:{start}: unterminated contracts block")


def _parse_contract_line(
    line: str, source: str, line_no: int
) -> tuple[str, _ContractClause, _ContractClause]:
    match = _CONTRACT_TASK_RE.match(line)
    if not match:
        raise ParseError(
            f"{source}:{line_no}: invalid contracts syntax: {line}"
        )

    task_name, tail = match.groups()
    clauses: dict[str, _ContractClause] = {}
    for clause in _CONTRACT_CLAUSE_RE.finditer(tail):
        kind = clause.group(1)
        if kind in clauses:
            raise ParseError(
                f"{source}:{line_no}: duplicate '{kind}' clause for task '{task_name}'"
            )
        token = clause.group(2)
        if token.startswith("@"):
            clauses[kind] = _ContractClause(
                inline_schema=None,
                type_ref=token[1:],
                line=line_no,
            )
        else:
            raw_schema = token[1:-1]
            clauses[kind] = _ContractClause(
                inline_schema=_parse_field_specs(
                    raw_schema,
                    source=source,
                    line_no=line_no,
                    kind=kind,
                ),
                type_ref=None,
                line=line_no,
            )

    if not clauses:
        raise ParseError(
            f"{source}:{line_no}: contract must include input and/or output clause"
        )

    remaining = _CONTRACT_CLAUSE_RE.sub("", tail).strip()
    if remaining:
        raise ParseError(
            f"{source}:{line_no}: unexpected contract tokens: {remaining}"
        )

    return (
        task_name,
        clauses.get("input", _ContractClause(None, None, line_no)),
        clauses.get("output", _ContractClause(None, None, line_no)),
    )


def _parse_field_specs(
    raw: str, source: str, line_no: int, kind: str
) -> list[FieldSpec]:
    if not raw.strip():
        return []
    out: list[FieldSpec] = []
    seen: set[str] = set()
    for part in [chunk.strip() for chunk in raw.split(",")]:
        if not part:
            raise ParseError(
                f"{source}:{line_no}: invalid empty field in {kind} schema"
            )
        match = _FIELD_SPEC_RE.match(part)
        if not match:
            raise ParseError(
                f"{source}:{line_no}: invalid field spec '{part}' in {kind} schema"
            )
        path, type_token = match.groups()
        optional = type_token.endswith("?")
        normalized_type = _normalize_schema_type(type_token[:-1] if optional else type_token)
        if normalized_type is None:
            raise ParseError(
                f"{source}:{line_no}: unsupported type '{type_token}' in {kind} schema"
            )
        if path in seen:
            raise ParseError(
                f"{source}:{line_no}: duplicate field '{path}' in {kind} schema"
            )
        seen.add(path)
        out.append(
            FieldSpec(
                path=path,
                expected_type=normalized_type,
                optional=optional,
                line=line_no,
            )
        )
    return out


def _normalize_schema_type(type_token: str) -> str | None:
    token = type_token.strip().lower()
    token = _SCHEMA_TYPE_ALIASES.get(token, token)
    if token in _VALID_SCHEMA_TYPES:
        return token
    return None


def _resolve_task_contracts(
    task_contracts_raw: dict[str, dict[str, _ContractClause]],
    type_defs: dict[str, list[FieldSpec]],
    source: str,
) -> dict[str, dict[str, list[FieldSpec]]]:
    out: dict[str, dict[str, list[FieldSpec]]] = {}
    for task_name, clauses in task_contracts_raw.items():
        out[task_name] = {
            "input": _resolve_contract_clause(
                clauses.get("input"),
                type_defs=type_defs,
                source=source,
            ),
            "output": _resolve_contract_clause(
                clauses.get("output"),
                type_defs=type_defs,
                source=source,
            ),
        }
    return out


def _resolve_contract_clause(
    clause: _ContractClause | None,
    type_defs: dict[str, list[FieldSpec]],
    source: str,
) -> list[FieldSpec]:
    if clause is None:
        return []
    if clause.inline_schema is not None:
        return clause.inline_schema
    if clause.type_ref is None:
        return []
    if clause.type_ref not in type_defs:
        available = ", ".join(sorted(type_defs)) or "<none>"
        raise ParseError(
            f"{source}:{clause.line}: unknown type '{clause.type_ref}' in contract "
            f"(available: {available})"
        )
    return [replace(field, line=clause.line) for field in type_defs[clause.type_ref]]


def _parse_capabilities(raw: str | None, source: str, line_no: int) -> set[str]:
    if raw is None:
        return set()
    caps: set[str] = set()
    for token in [part.strip() for part in raw.split(",") if part.strip()]:
        if token.startswith("capability."):
            token = token.split(".", 1)[1]
        if not _CAP_RE.fullmatch(token):
            raise ParseError(
                f"{source}:{line_no}: invalid capability name: {token}"
            )
        caps.add(token)
    return caps


def _parse_after(raw: str | None) -> list[str]:
    if raw is None:
        return []
    return [part.strip() for part in raw.split(",") if part.strip()]


def _parse_artifact_names(
    raw: str,
    source: str,
    line_no: int,
    clause_name: str,
) -> tuple[list[str], dict[str, str]]:
    artifacts: list[str] = []
    artifact_types: dict[str, str] = {}
    seen: set[str] = set()
    for token in [part.strip() for part in raw.split(",") if part.strip()]:
        typed_match = _ARTIFACT_TYPED_RE.fullmatch(token)
        if typed_match is None:
            raise ParseError(
                f"{source}:{line_no}: invalid artifact name '{token}' in {clause_name}"
            )
        artifact, type_token = typed_match.groups()
        if not _ARTIFACT_RE.fullmatch(artifact):
            raise ParseError(
                f"{source}:{line_no}: invalid artifact name '{artifact}' in {clause_name}"
            )
        if artifact in seen:
            raise ParseError(
                f"{source}:{line_no}: duplicate artifact '{artifact}' in {clause_name}"
            )
        seen.add(artifact)
        artifacts.append(artifact)
        if type_token is not None:
            artifact_types[artifact] = type_token
    return artifacts, artifact_types


def _is_ignored(line: str) -> bool:
    return not line or line.startswith("#")
