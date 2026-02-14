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

## 2026-02-13

Status: accepted
Decision: emit grouped verify diagnostics under `verify_summary` in traces.
Rationale: speed up failure triage by exposing aggregate verify health and failed-check details with source lines.
Consequences: trace schema includes `verify_summary`, while existing `verify` entries remain stable for compatibility.

## 2026-02-13

Status: accepted
Decision: add `mgl validate` as first-class static validation command.
Rationale: provide a dedicated preflight path for CI/automation without executing workers.
Consequences: CLI supports human and JSON validation output with deterministic exit codes.

## 2026-02-13

Status: accepted
Decision: maintain runnable example programs as conformance assets, including artifact-flow scenarios.
Rationale: keep language features grounded in executable references and reduce doc/runtime drift.
Consequences: new examples and worker fixtures are treated as part of behavior coverage and regression testing.

## 2026-02-13

Status: accepted
Decision: support typed artifact contracts in `consumes`/`produces` via `artifact:type`.
Rationale: enforce payload compatibility at artifact boundaries without requiring every task I/O schema to inline artifact checks.
Consequences: parser/AST encode artifact type annotations, validator checks static compatibility, and runtime enforces typed consume/produce contracts.

## 2026-02-13

Status: accepted
Decision: extend retry policy with `retry_if` strategy and jittered delay.
Rationale: give orchestration-level control over retry eligibility and thundering-herd mitigation.
Consequences: `with` supports `retry_if` and `jitter`; executor retries conditionally and applies randomized delay on retries.

## 2026-02-13

Status: accepted
Decision: bootstrap a Rust reference runtime focused on AST/trace contract conformance.
Rationale: de-risk multi-runtime migration by validating shared contracts before full executor parity.
Consequences: `rust/missiongraph-rs` provides AST checks and trace-skeleton emission against v1 contracts.

## 2026-02-13

Status: accepted
Decision: add deterministic retry seeding support in runtime/CLI.
Rationale: make retry+jitter behavior reproducible across runs for debugging and CI stability.
Consequences: `execute_program` and `mgl run` accept a retry seed; per-task retry jitter uses deterministic seeded RNG when provided.
