from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Constraint:
    key: str
    op: str
    value: Any
    line: int


@dataclass(frozen=True)
class FieldSpec:
    path: str
    expected_type: str
    optional: bool
    line: int


@dataclass(frozen=True)
class Task:
    name: str
    worker: str
    requires: set[str] = field(default_factory=set)
    after: list[str] = field(default_factory=list)
    timeout_seconds: float | None = None
    retries: int = 0
    backoff_seconds: float = 0.0
    input_schema: list[FieldSpec] = field(default_factory=list)
    output_schema: list[FieldSpec] = field(default_factory=list)
    line: int = 0


@dataclass(frozen=True)
class VerifyCheck:
    expression: str
    line: int


@dataclass
class Program:
    goal: str
    types: dict[str, list[FieldSpec]] = field(default_factory=dict)
    constraints: list[Constraint] = field(default_factory=list)
    tasks: list[Task] = field(default_factory=list)
    verify: list[VerifyCheck] = field(default_factory=list)
    source_path: Path | None = None

    @property
    def base_dir(self) -> Path:
        if self.source_path is None:
            return Path.cwd()
        return self.source_path.parent
