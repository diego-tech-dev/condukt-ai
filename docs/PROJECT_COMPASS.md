# MissionGraph Project Compass

This document is the durable context for MissionGraph. It is the first file to read when resuming work.

Companion docs:
- `AGENTS.md` for agent entrypoint and execution workflow.
- `DECISIONS.md` for decision history.

## Purpose

MissionGraph is an intent-first orchestration language for agents.

It exists to make multi-agent work:
- explicit (`goal`, `constraints`, `plan`, `contracts`, `verify`)
- safe (typed contracts + capability checks)
- auditable (structured, versioned traces)
- portable across runtimes (stable AST/trace contracts)

## North Star

Given the same `.mgl` program and same worker behavior, any compliant runtime should produce semantically equivalent execution behavior and trace outputs.

## Current Scope (v1)

- Language file extension: `.mgl` only.
- Parser outputs a versioned AST (`ast_version = "1.1"`).
- Executor outputs a versioned trace (`trace_version = "1.1"`).
- Task graph supports dependency levels and parallel fan-out.
- Contracts are fail-fast on input and output schema violations.
- Conformance is guarded by golden tests and JSON schemas.

## Explicit Non-Goals (for now)

- No historical compatibility layer (`agentlang` removed).
- No `.apl` fallback support.
- No distributed scheduler; execution is local process orchestration.
- No advanced type system (generics/unions/recursive schemas) yet.
- No long-term commitment to Python runtime implementation.

## Hard Invariants

These should not be changed without a deliberate version bump:

- `.mgl` is the only accepted program extension.
- `spec/ast-v1.schema.json` is the AST contract.
- `spec/trace-v1.schema.json` is the trace contract.
- Error codes in `missiongraph/spec.py` are stable API surface.
- Golden outputs in `tests/golden/` define expected behavior.

## Architecture Snapshot

- Parser: `missiongraph/parser.py`
- AST serializer: `missiongraph/serialization.py`
- Planner: `missiongraph/planner.py`
- Executor: `missiongraph/executor.py`
- CLI: `missiongraph/cli.py`
- Spec constants: `missiongraph/spec.py`
- Schemas: `spec/ast-v1.schema.json`, `spec/trace-v1.schema.json`
- Conformance tests: `tests/test_end_to_end.py`, `tests/golden/*`

## Migration Strategy (Python -> Rust)

Python is the reference runtime, not the permanent target.

Rules for safe migration:
- Keep language semantics defined by AST/trace specs, not by Python behavior.
- Add conformance tests before changing semantics.
- Implement Rust parser/executor against the same schema contracts.
- Run dual-runtime conformance on the same golden suite.
- Only deprecate Python parity once Rust passes all conformance checks.

## Decision Log

### 2026-02-13

- Language renamed to MissionGraph.
- Primary extension set to `.mgl`.
- Legacy compatibility surface removed (no `agentlang`, no `.apl`).
- Added versioned contracts (`ast_version`, `trace_version`).
- Added normalized runtime `error_code` field.
- Added formal JSON schemas and golden fixtures.
- Added task execution policies in DSL (`with timeout/retries/backoff`).
- Runtime now supports timeout + retries + exponential backoff per task.
- Added explicit artifact contracts in `plan` (`consumes`/`produces`).
- Added grouped verify diagnostics in trace output (`verify_summary`).
- Added CLI preflight validation command (`mgl validate`).
- Added artifact-flow runnable example coverage (`examples/release_artifacts.mgl`).
- Added typed artifact contracts (`artifact:type`) for `consumes`/`produces`.
- Added retry policy controls (`retry_if`, jitter) in task execution policy.
- Added Rust bootstrap runtime (`rust/missiongraph-rs`) for contract-level conformance checks.
- Added deterministic retry seeding (`--retry-seed`) for reproducible retry behavior.
- Added multi-runtime conformance harness (`scripts/conformance.py`).
- Bumped v1 contracts to `ast_version = 1.1` and `trace_version = 1.1`.
- Added explicit contract version governance in `spec/VERSIONING.md` with consistency tests.
- Hardened Rust `check-ast` with DAG cycle detection and `--json` machine-readable reporting.
- Expanded Rust trace skeleton semantics to emit dependency-aware execution levels/mode/max parallel.
- Added dual-runtime golden conformance gate over `ship_release` + `release_artifacts` fixtures.
- Added Rust `run-task` prototype for single dependency-free worker execution.
- Aligned Rust `run-task` result shape with contract-style error/provenance/timestamp fields.
- Expanded parity matrix coverage to `release_fanout` and `release_resilient` with dedicated matrix tooling.

## Near-Term Direction

1. Expand Rust runtime from single-task prototype to multi-task execution flow.
2. Implement Rust retry/timeout loop parity and full trace assembly.

## Resume Checklist

When picking up work:

1. Read this file.
2. Run:
   - `python3 -m unittest discover -s tests -p "test_*.py"`
   - `python3 -m missiongraph parse examples/ship_release.mgl`
   - `python3 -m missiongraph run examples/ship_release.mgl --capability ci --capability prod_access --sequential`
   - `python3 scripts/conformance.py --json`
   - `python3 scripts/conformance.py --json --require-goldens`
   - `python3 scripts/parity_matrix.py --json`
3. Confirm no schema/golden drift unless intentional.

## Update Protocol

After each meaningful change:

- update `Decision Log` with date and decisions
- update `Near-Term Direction` if priorities change
- if contracts changed, follow `spec/VERSIONING.md` and update schemas/goldens/runtime constants together
