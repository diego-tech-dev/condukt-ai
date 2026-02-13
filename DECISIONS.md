# DECISIONS.md

Decision log for MissionGraph.

Format:
- `Date`
- `Status`: accepted, proposed, deprecated
- `Decision`
- `Rationale`
- `Consequences`

## 2026-02-13

Status: accepted
Decision: rename language and runtime project to MissionGraph.
Rationale: align naming with mission orchestration + DAG semantics.
Consequences: package name `missiongraph`, CLI `mgl`, docs/examples updated.

## 2026-02-13

Status: accepted
Decision: use `.mgl` as the only valid program extension.
Rationale: remove ambiguity and avoid `.apl` conflict.
Consequences: parser rejects non-`.mgl`; tests enforce this.

## 2026-02-13

Status: accepted
Decision: keep Python as reference runtime; design for future Rust runtime parity.
Rationale: maximize iteration speed now while preserving portability path.
Consequences: semantic contracts are defined by schemas + goldens, not Python internals.

## 2026-02-13

Status: accepted
Decision: enforce versioned contracts for AST and trace (`1.0`).
Rationale: create stable interchange surface for multi-runtime conformance.
Consequences: `ast_version` and `trace_version` are required and schema-governed.

## 2026-02-13

Status: accepted
Decision: keep fail-fast typed input/output contracts on tasks.
Rationale: improve safety and observability in multi-agent workflows.
Consequences: runtime stops on first contract violation and emits normalized error codes.

## 2026-02-13

Status: accepted
Decision: execute by dependency levels with optional parallel fan-out.
Rationale: preserve DAG correctness while improving throughput on independent tasks.
Consequences: traces include execution levels/mode/max parallel settings.

## 2026-02-13

Status: accepted
Decision: require conformance goldens for stable behavior.
Rationale: make cross-runtime parity measurable and regression-resistant.
Consequences: `tests/golden/` is part of compatibility contract and must be updated intentionally.

## 2026-02-13

Status: accepted
Decision: add task execution policies to `plan` via `with timeout/retries/backoff`.
Rationale: support resilient orchestration in the DSL without pushing retry logic into each worker.
Consequences: parser, AST schema, and executor now include policy semantics; runtime applies timeout + retries + exponential backoff per task.

## 2026-02-13

Status: accepted
Decision: add explicit task artifact contracts in `plan` via `consumes` and `produces`.
Rationale: make inter-task data dependencies first-class instead of implicit output-key coupling.
Consequences: parser/AST include artifact clauses, validator enforces producer-path correctness, and executor fails fast on missing artifacts.
