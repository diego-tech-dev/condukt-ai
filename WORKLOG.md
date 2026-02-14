# Condukt AI Worklog

## 2026-02-13

### Sprint: Autonomous 5-milestone run

Status: completed

Milestone status:
- `M1` Planning scaffolding: completed
- `M2` Artifact contracts (`produces`/`consumes`): completed
- `M3` Verify diagnostics: completed
- `M4` CLI validation workflow: completed
- `M5` Conformance and docs hardening: completed

Notes:
- Execution mode: autonomous implementation with atomic commits and frequent pushes.
- Stop conditions: only hard blockers (credentials, destructive-op requirement, or legal/safety conflict).
- Completed:
  - Added `ROADMAP.md` and initialized this worklog.
  - Implemented task-level artifact contracts (`consumes`/`produces`) with parser/validator/executor coverage.
  - Added `verify_summary` diagnostics in trace output (counts + failed-check details).
  - Added `mgl validate` command with optional JSON output.
  - Added artifact-flow example (`release_artifacts.mgl`) with dedicated worker and end-to-end coverage.

### Sprint: Autonomous backlog run

Status: completed

Milestone status:
- `B1` Typed artifact payload contracts: completed
- `B2` Policy enhancements (`retry_if`, jitter): completed
- `B3` Rust runtime bootstrap: completed

Notes:
- Added typed artifact contracts (`artifact:type`) in `consumes`/`produces`.
- Added static/runtime checks for artifact type compatibility.
- Added `retry_if` strategy and retry jitter controls in `with` task policies.
- Added `rust/condukt-rs` bootstrap CLI (`check-ast`, `trace-skeleton`) with Rust tests.

### Sprint: Autonomous quality run

Status: completed

Milestone status:
- `Q1` Deterministic retry seeding: completed
- `Q2` Multi-runtime conformance harness: completed
- `Q3` Contract/versioning governance checks: completed

Notes:
- Added deterministic retry seeding (`--retry-seed`) for reproducible jitter behavior.
- Added `scripts/conformance.py` to validate Python/Rust AST+trace contract alignment.
- Bumped contract versions to `ast_version = 1.1` and `trace_version = 1.1`.
- Added `spec/VERSIONING.md` and contract-version consistency tests across Python, schemas, Rust, and goldens.

### Sprint: Autonomous next run

Status: completed

Milestone status:
- `N1` Rust contract CLI parity hardening: completed
- `N2` Rust trace semantics expansion: completed
- `N3` Dual-runtime golden conformance gate: completed

Notes:
- Rust bootstrap validator now detects dependency cycles (`cycle detected in plan`).
- `mgl-rs check-ast` now supports `--json` machine-readable output.
- Python conformance harness now consumes Rust `check-ast --json` output for stronger contract assertions.
- Rust trace skeleton now computes dependency levels, execution mode, and max parallel width from AST dependencies.
- Conformance harness now checks Rust execution metadata (`execution.levels`, `mode`, `max_parallel`) against Python-derived expectations.
- Added `release_artifacts` AST/trace golden fixtures.
- Added dual-runtime golden gate (`python3 scripts/conformance.py --json --require-goldens`) and test coverage for Rust-vs-golden contract projection parity.

### Sprint: Autonomous follow-up run

Status: completed

Milestone status:
- `F1` Rust worker execution prototype (single task path): completed
- `F2` Rust task-result contract shaping (error_code/provenance): completed
- `F3` Cross-runtime parity matrix for resilient policies: completed

Notes:
- Added `mgl-rs run-task` prototype command for executing one dependency-free task worker from AST.
- Added Rust CLI tests for successful worker execution and dependency-rejection behavior.
- `run-task` now emits task-result style fields: `error_code`, `started_at`, `finished_at`, and merged provenance.
- Added Rust CLI coverage for non-zero worker exit mapping to `WORKER_EXIT_NONZERO`.
- Expanded conformance defaults and dual-runtime goldens to include `release_fanout` and `release_resilient`.
- Added `scripts/parity_matrix.py` and parity-matrix tests to make resilient-policy coverage explicit.

### Sprint: Autonomous execution run

Status: completed

Milestone status:
- `E1` Rust multi-task sequential execution (dependency order): completed
- `E2` Rust retry/timeout policy loop parity for task execution: completed
- `E3` Rust trace assembly for full-plan runs (tasks + verify summary): completed

Notes:
- Added `docs/FOUNDATIONS.md` to capture explicit language/runtime design baselines, tradeoffs, and migration paths across all core design dimensions.
- Added `docs/LEARNINGS.md` as a persistent memory track for implementation lessons and guardrails.
- Added Rust `run-plan` command for sequential dependency-order task execution from AST.
- Added Rust CLI coverage for run-plan order semantics and fail-fast behavior.
- Added Rust per-task execution policy parity (`timeout`, `retries`, `retry_if`, `backoff`, `jitter`) across `run-task` and `run-plan`.
- Added Rust CLI coverage for retry-to-success, timeout-only retry gating, and run-plan dependency execution after retries.
- Added Rust run-plan diagnostics assembly for `constraints`, `verify`, and `verify_summary` fields.
- Added Rust CLI coverage for successful verify summaries, explicit verify failures, and unresolved-constraint reporting (`passed: null`).

### Sprint: TypeScript pivot run

Status: completed

Milestone status:
- `T1` TypeScript core runtime bootstrap (Standard Schema contracts + trace-first pipeline): completed
- `T2` Real LLM adapter hardening (OpenAI/Anthropic integration tests + retry policy): completed
- `T3` 10-minute user path (`pnpm dlx`/template + demo trace walkthrough): completed

Notes:
- Added `ts/` package managed by `pnpm`.
- Added Standard Schema-first contract validation (`@standard-schema/spec`) to keep schema-library choice open.
- Added TypeScript `Pipeline` runtime with fail-fast task boundary contracts and structured per-task traces.
- Added OpenAI and Anthropic JSON provider adapters for real LLM-backed tasks.
- Added `llmTask` helper and runnable 3-step example (`ts/examples/research-write.ts`).
- Added TypeScript tests for success path, contract violation diagnostics, and dependency validation.
- Added task-level retry policy in TS runtime (`retries`, `backoffMs`, `jitterMs`, `retryIf`) with attempt history in traces.
- Added TS provider tests with mocked HTTP responses for OpenAI and Anthropic JSON parsing behavior.
- Added TS quickstart demo (`pnpm quickstart` / `pnpm quickstart:broken`) that writes a trace and demonstrates boundary-failure diagnosis.
- Added 10-minute walkthrough doc at `ts/docs/TRACE_WALKTHROUGH.md`.
- Renamed TS package to `condukt-ai`.

### Sprint: Distribution run

Status: completed

Milestone status:
- `U1` TS package publish readiness (metadata/exports/files/release checks): completed
- `U2` CI + release automation for TS package quality gates: completed
- `U3` External trial instrumentation for time-to-diagnose metric capture: completed

Notes:
- Started npm publish-readiness hardening for the `condukt-ai` package.
- Added publish metadata (`exports`, `files`, `repository`, `engines`, `publishConfig`) and release scripts (`release:check`, `prepack`) to `ts/package.json`.
- Added package publishing runbook at `ts/docs/PUBLISHING.md`.
- Added local `ts/LICENSE` to ensure packaged license inclusion.
- Regenerated normalized trace goldens after canonical workspace path rename to keep conformance deterministic.
- Added GitHub Actions quality workflow (`.github/workflows/ts-quality.yml`) for TS typecheck/tests/build/release-check gates on push/PR.
- Added GitHub Actions manual publish workflow (`.github/workflows/ts-publish.yml`) using `NPM_TOKEN`.
- Added trace diagnosis helpers (`diagnoseFailure`) and trial instrumentation utilities (`createTrialSession`, `completeTrialSession`, `summarizeTrialRecords`) in TS runtime.
- Added trial metrics CLI (`ts/scripts/trial-metrics.ts`) with start/finish/report commands writing JSONL records.
- Added trial instrumentation docs (`ts/docs/TRIALS.md`) and TS test coverage for diagnosis/trial metrics behavior.

### Sprint: TS tooling conventions

Status: completed

Notes:
- Added Biome configuration at `ts/biome.json`.
- Added TS scripts: `pnpm lint`, `pnpm format`, and `pnpm typecheck`.
- Updated `pnpm check` and `pnpm release:check` to include lint/typecheck and pnpm-based pack validation.
- Updated TS GitHub workflows to run lint and to publish with `pnpm publish`.
- Updated agent conventions to enforce pnpm-only JS/TS workflow and no TypeScript `any`.

### Sprint: TS test runner migration

Status: completed

Notes:
- Migrated TS tests from `tsx --test` to Vitest (`pnpm test`, `pnpm test:watch`).
- Updated TS test files to Vitest assertions/imports.
- Kept runtime/build path unchanged (`tsc` + `tsx` for scripts), no Vite bundler integration required.

### Sprint: Trial evidence run

Status: completed

Milestone status:
- `R1` Paired trial analytics by participant/scenario: completed
- `R2` CLI quality gates for trial success criteria (speedup/accuracy/pairs): completed
- `R3` Shareable markdown summary output + documentation refresh: completed

Notes:
- Added paired trial analysis in TS summary output (`paired` block with pair-level speedup stats).
- Updated trial report output to include paired sample count and median paired speedup.
- Added TS unit coverage for pairing logic and latest-run selection.
- Added TS trial quality-gate evaluation (`min_records`, `min_accuracy`, `min_pairs`, `min_paired_speedup`) with explicit failure reasons.
- Added trial CLI gate flags (`--min-records`, `--min-accuracy`, `--min-pairs`, `--min-speedup`) with non-zero exit on gate failure.
- Added markdown trial summary renderer and `--markdown-out` export path in trial CLI.
- Added report formatting controls (`--title`, `--max-pairs`) and docs for gate-driven shareable reporting.

### Sprint: Naming alignment run

Status: completed

Notes:
- Renamed external TS package identity to `condukt-ai` and aligned docs/examples accordingly.
- Updated trial mode labels and report fields from `condukt` to `condukt-ai`.
- Updated repository metadata links to `github.com/diego-tech-dev/condukt-ai`.

### Sprint: Identity alignment run

Status: completed

Milestone status:
- `I1` Align package/repo/docs identity to `condukt-ai`: completed
- `I2` Legacy trial-mode compatibility (`condukt` -> `condukt-ai`) and input normalization: completed
- `I3` Release guardrails for renamed identity (name checks + docs/CLI hardening): completed

Notes:
- Renamed GitHub repository to `diego-tech-dev/condukt-ai`.
- Updated TS package metadata, trial mode labels, and docs/examples to `condukt-ai`.
- Updated normalized trace goldens for canonical workspace rename (`condukt` -> `condukt-ai` path segment).
- Added trial-mode normalization (`condukt` alias -> `condukt-ai`) in runtime and CLI.
- Added strict trial-record input normalization for report ingestion with line-numbered validation errors.
- Added release identity validator (`ts/src/release_identity.ts`) and CLI guard (`pnpm release:guard`).
- Integrated release identity guard into `pnpm release:check` and added TS guard unit tests.

### Sprint: Trial refactor run

Status: completed

Milestone status:
- `J1` Trial module split (`types`/`normalization`/`session`/`summary`): completed
- `J2` Strict command-scoped parsing and validation in `trial-metrics` CLI: completed
- `J3` Path-agnostic trace goldens + CLI integration coverage: completed

Notes:
- Split `ts/src/trials.ts` into focused modules under `ts/src/trials/` while preserving public API exports.
- Hardened `ts/scripts/trial-metrics.ts` parser with explicit command/flag validation, typed option parsing, and early failures for malformed flags.
- Added end-to-end CLI integration coverage in `ts/test/trial-metrics-cli.test.ts` for `start`/`finish`/`report` workflow plus boolean-flag validation.
- Normalized golden trace worker provenance to `workers/<file>` and updated Python trace normalization to remove machine-specific path prefixes.

### Sprint: TS-only consolidation run

Status: completed

Milestone status:
- `K1` Remove Python and Rust runtime tracks from repository: completed
- `K2` Remove cross-runtime conformance/parity scripts and tests: completed
- `K3` Rewrite root architecture docs for TS-only scope: completed

Notes:
- Removed legacy runtime source trees (`condukt/`, `rust/condukt-rs/`) and Python worker/example/spec assets tied to the old `.mgl` track.
- Removed Python-based conformance/parity tooling and the full Python/Rust test suite.
- Rewrote root docs (`README.md`, `docs/PROJECT_COMPASS.md`, `docs/FOUNDATIONS.md`) to reflect TS-only product scope.

### Sprint: Typed provider DX run

Status: completed

Milestone status:
- `L1` Introduce provider/model generic typing surface in runtime API: completed
- `L2` Enforce model-specific settings inference in `llmTask`: completed
- `L3` Add compile-time type fixtures for provider/model contract safety: completed

Notes:
- Refactored `ts/src/providers.ts` to expose model-aware provider generics and exported provider model catalogs (`OPENAI_MODELS`, `ANTHROPIC_MODELS`).
- Updated `llmTask` typing in `ts/src/pipeline.ts` so `modelSettings` are inferred from selected provider/model instead of generic untyped task-level knobs.
- Added compile-time provider typing fixtures under `ts/typecheck/` and moved `pnpm typecheck` to `tsconfig.typecheck.json` to enforce these contracts.
- Expanded provider runtime tests to validate request payload shaping for chat vs reasoning settings.

### Sprint: Typed dependency context run

Status: completed

Milestone status:
- `M1` Generic task/runtime context typing for dependency output inference: completed
- `M2` Add `Pipeline.addLLMTask` typed builder path and migrate examples: completed
- `M3` Add compile-time dependency-key fixtures and validate with release checks: completed

Notes:
- Refactored `TaskRuntimeContext`, `TaskDefinition`, and `LLMTaskDefinition` to carry output/dependency generics.
- Added `Pipeline<TOutputs>` accumulation and `addLLMTask(...)` to make dependency outputs typed from declared `after` keys.
- Migrated TS examples and core pipeline tests to builder chaining without manual `as` casts for dependency outputs.
- Added compile-time dependency fixtures at `ts/typecheck/pipeline-dependencies.typecheck.ts`.

### Sprint: Typed run result run

Status: completed

Milestone status:
- `N1` Add typed pipeline run API (`runDetailed`) returning trace + typed outputs: completed
- `N2` Add runtime tests for typed run-output behavior: completed
- `N3` Add compile-time run-output key safety fixtures and docs updates: completed

Notes:
- Added `PipelineRunResult<TOutputs>` and `Pipeline.runDetailed()` returning typed `outputs`/`taskResults` plus full trace.
- Kept `Pipeline.run()` as a trace-only convenience wrapper for backward-compatible callsites.
- Added runtime test coverage for typed output retrieval and updated README usage to show `runDetailed()` output access.
- Extended typecheck fixtures to assert output-key safety on `runDetailed()` results.

### Sprint: Builder guard run

Status: completed

Milestone status:
- `P1` Add compile-time duplicate task-id constraints for typed builders: completed
- `P2` Add runtime fallback test coverage for dynamic duplicate IDs: completed
- `P3` Update typecheck fixtures and docs for duplicate-id safety guarantees: completed

Notes:
- Added duplicate-id type constraints to `addTask` and `addLLMTask` so chained builder composition rejects repeated static task IDs.
- Added runtime test for duplicate IDs introduced through dynamic string IDs to preserve fail-fast behavior beyond static typing.
- Extended dependency typecheck fixtures with duplicate-id compile-time assertions.
