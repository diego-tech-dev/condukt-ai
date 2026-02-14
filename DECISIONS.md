# DECISIONS.md

Decision log for Condukt.

Format:
- `Date`
- `Status`: accepted, proposed, deprecated
- `Decision`
- `Rationale`
- `Consequences`

## 2026-02-13

Status: accepted
Decision: rename language and runtime project to Condukt.
Rationale: align naming with mission orchestration + DAG semantics.
Consequences: package name `condukt-ai`, CLI `mgl`, docs/examples updated.

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
Consequences: `rust/condukt-rs` provides AST checks and trace-skeleton emission against v1 contracts.

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
Decision: shape Rust `run-task` output to align with Condukt task-result fields.
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

## 2026-02-14

Status: accepted
Decision: pivot product direction to a TypeScript-first runtime while keeping Python as a temporary reference implementation.
Rationale: target users for agentic application development are concentrated in the TypeScript ecosystem; Python remains useful as behavioral reference during migration.
Consequences: added `ts/` runtime package and tests; Python/Rust tracks remain maintained for parity and backward context until TS workflow path is validated.

## 2026-02-14

Status: accepted
Decision: standardize task contracts on Standard Schema (`@standard-schema/spec`) for TypeScript runtime surfaces.
Rationale: contract portability should not lock users to a single validation library; Standard Schema allows Zod and other compliant schema libraries.
Consequences: TS pipeline contract validation consumes `StandardSchemaV1`; examples use Zod while preserving schema-library interoperability.

## 2026-02-14

Status: accepted
Decision: include retry policy controls directly in TypeScript task execution.
Rationale: transient LLM/provider failures are common, and retry behavior should be configurable at task boundaries with trace visibility.
Consequences: TS tasks now support `retries`, `backoffMs`, `jitterMs`, and `retryIf`; traces capture per-attempt history for diagnosis.

## 2026-02-14

Status: accepted
Decision: ship a built-in 10-minute TS quickstart with an intentionally broken variant.
Rationale: adoption risk is reduced when users can experience trace-based diagnosis without credentials or external setup.
Consequences: added `pnpm quickstart` and `pnpm quickstart:broken`, plus `ts/docs/TRACE_WALKTHROUGH.md` for deterministic diagnosis flow.

## 2026-02-14

Status: accepted
Decision: name the TypeScript runtime package `condukt-ai`.
Rationale: short, searchable, and aligned with the orchestration/conduct metaphor while avoiding saturated `agent/flow/graph` naming patterns.
Consequences: TS package metadata and docs now use `condukt-ai`; product branding is Condukt AI while Python/Rust runtime module paths remain `condukt` for now.

## 2026-02-14

Status: accepted
Decision: prepare `condukt-ai` for direct npm distribution with explicit export/file boundaries and release checks.
Rationale: user adoption requires installable package ergonomics and reproducible pre-publish quality gates.
Consequences: TS package now includes publish metadata (`repository`, `engines`, `exports`, `files`, `publishConfig`) and a `release:check` script plus publishing playbook.

## 2026-02-14

Status: accepted
Decision: enforce TS package quality and publish flow through GitHub Actions workflows.
Rationale: distribution reliability needs CI-enforced gates and repeatable publish mechanics beyond local developer runs.
Consequences: added `ts-quality` workflow for push/PR checks and `ts-publish` manual workflow that validates release artifacts before publishing with `NPM_TOKEN`.

## 2026-02-14

Status: accepted
Decision: instrument external time-to-diagnose trials with trace-derived expectations and JSONL metric records.
Rationale: proving the core value proposition requires measurable diagnosis speed/accuracy data across baseline vs Condukt workflows.
Consequences: TS runtime now includes diagnosis/trial helpers, a trial metrics CLI (`start`/`finish`/`report`), and documentation for repeatable external trial execution.

## 2026-02-14

Status: accepted
Decision: standardize TypeScript lint/format checks on Biome and enforce pnpm-only JS/TS package operations.
Rationale: fast deterministic linting plus one package-manager path reduces drift across local and CI workflows.
Consequences: added `ts/biome.json`, new TS scripts (`lint`, `format`, `typecheck`), updated CI quality/publish workflows, and removed npm-based pack/publish commands from TS release paths.

## 2026-02-14

Status: accepted
Decision: adopt Vitest as the TypeScript test runner while keeping the existing non-Vite library build path.
Rationale: Vitest provides faster feedback and stronger test ergonomics for mocks, watch mode, and future coverage without requiring a Vite app/tooling migration.
Consequences: TS test scripts now use Vitest (`pnpm test`, `pnpm test:watch`) and TS test files use Vitest assertions.

## 2026-02-14

Status: accepted
Decision: compute trial speedup with participant+scenario paired analysis in addition to global mode medians.
Rationale: unpaired aggregate medians can distort diagnosis-speed claims when baseline and condukt-ai samples come from different cohorts.
Consequences: TS trial summaries now include a `paired` section with pair count, pair-level entries, and paired median/p90 speedup metrics.

## 2026-02-14

Status: accepted
Decision: enforce configurable trial quality gates at report time.
Rationale: external trials need objective pass/fail criteria to avoid subjective interpretation of small or low-quality datasets.
Consequences: trial reporting now supports threshold gates for record count, accuracy, paired sample count, and paired speedup, with non-zero exit code when thresholds are not met.

## 2026-02-14

Status: accepted
Decision: generate shareable markdown trial reports directly from the trial CLI.
Rationale: trial outcomes need a portable artifact for async review and decision-making without requiring custom post-processing.
Consequences: trial reporting now supports `--markdown-out`, optional title/pair limits, and includes gate status in the exported markdown when thresholds are configured.

## 2026-02-14

Status: accepted
Decision: align public package and repository identity on `condukt-ai`.
Rationale: one canonical external name reduces ambiguity during adoption and avoids package-name confusion.
Consequences: npm package metadata, trial mode labels, and documentation now use `condukt-ai`; repository remote targets `github.com/diego-tech-dev/condukt-ai`.

## 2026-02-14

Status: accepted
Decision: keep backward compatibility for legacy trial mode label `condukt` while normalizing to canonical `condukt-ai`.
Rationale: existing trial datasets and scripts may still emit legacy mode labels; hard breaks would reduce continuity during rename rollout.
Consequences: trial CLI accepts legacy mode input and report ingestion normalizes legacy records to canonical mode with validation.

## 2026-02-14

Status: accepted
Decision: enforce a release identity guard for `condukt-ai` metadata and docs before packaging.
Rationale: rename regressions are easy to miss across docs and package metadata; automated guardrails reduce publish risk.
Consequences: added `pnpm release:guard` and integrated it into `pnpm release:check`, with failing checks for legacy-name drift.

## 2026-02-14

Status: accepted
Decision: split trial instrumentation into focused modules and enforce strict command-scoped trial CLI flag parsing.
Rationale: the single trial module and permissive flag parsing were growing brittle as trial features expanded, making it harder to evolve safely.
Consequences: trial logic now lives in dedicated modules (`types`, `normalization`, `session`, `summary`), CLI rejects unknown/malformed flags early, and trial report ingestion remains backward-compatible via explicit mode normalization.

## 2026-02-14

Status: accepted
Decision: normalize worker provenance paths in golden trace comparisons.
Rationale: absolute local workspace paths created false golden diffs when repos were moved or renamed.
Consequences: golden traces now store `workers/<file>` paths and end-to-end normalization strips machine-specific prefixes before comparison.

## 2026-02-14

Status: accepted
Decision: decommission Python and Rust runtime tracks and keep Condukt AI repository scope TypeScript-only.
Rationale: active product direction and release workflow are fully centered on the `condukt-ai` TS package; maintaining legacy runtimes no longer provides sufficient value for the ongoing roadmap.
Consequences: removed Python/Rust runtime code, `.mgl` examples/spec artifacts, and cross-runtime conformance/parity test harnesses; root project docs now describe a TS-only architecture.

## 2026-02-14

Status: accepted
Decision: make provider/model-level type safety a first-class API contract in the TS runtime.
Rationale: preventing model-setting mismatches at compile time improves workflow correctness and DX for multi-provider agent pipelines.
Consequences: `LLMProvider` is now generic over model IDs and per-model settings maps, `llmTask` infers model-specific settings from the selected provider/model, and typecheck now includes dedicated compile-time provider typing fixtures.
