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
Decision: enforce versioned contracts for AST and trace (`1.x`, current `1.1`).
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

## 2026-02-13

Status: accepted
Decision: add a first-class Python/Rust conformance harness script.
Rationale: continuously verify that runtime contract surfaces stay aligned across implementations.
Consequences: `scripts/conformance.py` validates AST/trace contract compatibility for selected `.mgl` programs and is covered by tests.

## 2026-02-14

Status: accepted
Decision: bump AST/trace contract minor versions from `1.0` to `1.1` and codify versioning governance.
Rationale: versioning rules should be explicit and test-enforced before adding more runtime surface area.
Consequences: runtime constants, schemas, goldens, Rust bootstrap constants, and governance docs/tests move in lockstep for any future version bump.

## 2026-02-14

Status: accepted
Decision: harden Rust `check-ast` with cycle detection and JSON report output.
Rationale: bootstrap CLI should be directly usable by automation and should reject invalid DAGs consistently with planner semantics.
Consequences: Rust validation now detects dependency cycles; `check-ast --json` emits machine-readable status used by conformance tooling/tests.

## 2026-02-14

Status: accepted
Decision: make Rust trace-skeleton execution metadata dependency-aware.
Rationale: contract conformance is stronger when Rust emits execution levels/order derived from AST dependencies instead of source-order placeholders.
Consequences: Rust trace skeleton now computes topological levels/mode/max parallel; conformance harness validates these fields against Python-derived expectations.

## 2026-02-14

Status: accepted
Decision: enforce dual-runtime golden conformance as a first-class gate.
Rationale: conformance checks should be anchored to durable fixtures, not only ad-hoc example runs.
Consequences: added `release_artifacts` AST/trace goldens, expanded golden tests, and added `scripts/conformance.py --require-goldens` gate to assert Python AST + Rust trace contract parity against goldens.

## 2026-02-14

Status: accepted
Decision: add Rust `run-task` as a single-task worker execution prototype.
Rationale: begin migration beyond contract-only checks by exercising real worker invocation in Rust on a minimal, controlled slice.
Consequences: `mgl-rs run-task` executes one dependency-free task with JSON input/output reporting; tests cover successful execution and dependency rejection behavior.

## 2026-02-14

Status: accepted
Decision: shape Rust `run-task` output to align with MissionGraph task-result fields.
Rationale: migration confidence improves when Rust execution surfaces (`status`, `error_code`, `provenance`, timestamps) follow the same contract language as Python traces.
Consequences: Rust run-task now emits normalized `error_code`, `started_at`, `finished_at`, and merged provenance defaults; non-zero exits map to `WORKER_EXIT_NONZERO`.

## 2026-02-14

Status: accepted
Decision: make resilient-policy scenarios part of the cross-runtime parity matrix and conformance defaults.
Rationale: parity claims should explicitly cover fanout and retry/backoff policy programs, not only basic sequential cases.
Consequences: added `release_fanout` and `release_resilient` goldens, expanded conformance defaults, added `scripts/parity_matrix.py`, and test-gated resilient/fanout parity rows.

## 2026-02-14

Status: accepted
Decision: publish explicit foundations baseline in `docs/FOUNDATIONS.md`.
Rationale: core language/runtime choices (including open decisions) should be durable, reviewable, and resumable without relying on chat context.
Consequences: each major design dimension now records decision state, rationale, tradeoffs, migration path, and agent-specific constraints.

## 2026-02-14

Status: accepted
Decision: maintain a dedicated implementation learning log in `docs/LEARNINGS.md`.
Rationale: important execution lessons (root causes + guardrails) are different from architecture decisions and should persist across agent sessions.
Consequences: resume workflow now includes a memory track of operational learnings to reduce repeated mistakes.

## 2026-02-14

Status: accepted
Decision: add Rust `run-plan` command for sequential dependency-order execution.
Rationale: migration needs a full-plan execution slice beyond single-task prototypes to validate end-to-end task ordering and fail-fast behavior.
Consequences: Rust CLI now executes plan DAGs sequentially with dependency payload wiring and emits trace-shaped outputs with executed task results.

## 2026-02-14

Status: accepted
Decision: align Rust worker execution with policy-loop semantics (`timeout`, `retries`, `retry_if`, `backoff`, `jitter`).
Rationale: resilient execution behavior is a core runtime contract and must behave consistently across runtimes during migration.
Consequences: Rust `run-task` and `run-plan` now execute per-attempt policy loops, emit retry attempt history in provenance, and map timeout failures to `WORKER_TIMEOUT`.

## 2026-02-14

Status: accepted
Decision: assemble Rust `run-plan` trace diagnostics for `constraints`, `verify`, and `verify_summary`.
Rationale: full-plan trace parity requires post-execution diagnostics, not only task-result emission.
Consequences: Rust `run-plan` now evaluates constraint/verify expressions against runtime context, emits grouped verify failures, and factors diagnostics into overall trace status.
