# Condukt Learnings

Last updated: 2026-02-14

Note:
- Entries below include historical learnings from the decommissioned Python/Rust runtime phase.
- As of 2026-02-14, active implementation scope is TypeScript-only (`ts/`).

Purpose:
- capture implementation learnings that are easy to forget
- preserve root causes and guardrails, not just outcomes
- make future autonomous runs safer and faster

Entry format:
- `Date`
- `Context`
- `Learning`
- `What changed`
- `Guardrail`

## 2026-02-14

Context:
- Decommissioned Python and Rust runtime tracks after TS runtime reached release-grade checks.

Learning:
- Multi-runtime scaffolding is useful during exploration, but once product direction is clear it creates avoidable maintenance drag and diluted execution.

What changed:
- Removed legacy runtime code, cross-runtime conformance scripts, and Python/Rust test suites from this repository.

Guardrail:
- Before adding a new runtime track, require a product-level justification and a clear owner; otherwise keep focus on TS runtime velocity.

## 2026-02-14

Context:
- Strengthened TS provider/model type-safety to reduce runtime misconfiguration errors.

Learning:
- Provider-level generics only deliver DX value when task builders (`llmTask`) preserve model-specific setting inference all the way to call sites.

What changed:
- Added model-aware provider contracts and per-model settings maps.
- Added compile-time type fixtures in `ts/typecheck/provider-models.typecheck.ts`.

Guardrail:
- Any new provider or model family must ship typed model IDs/settings and at least one compile-time fixture proving invalid settings fail typecheck.

## 2026-02-14

Context:
- Extended type-safety from provider models into dependency-output typing during pipeline composition.

Learning:
- Mutating builder APIs only preserve evolving type maps when users chain/reassign; typed inference cannot retroactively narrow an already-declared variable type.

What changed:
- Added `Pipeline.addLLMTask` with output-map generic accumulation and dependency-key-aware task context typing.
- Updated examples/tests to chain pipeline construction so inferred dependency output types remain precise.

Guardrail:
- For typed pipeline composition examples, prefer fluent chaining (or reassignment) to avoid falling back to initial pipeline type state.

## 2026-02-14

Context:
- Extended orchestration API to expose typed outputs on execution results.

Learning:
- Type-safe builder composition is incomplete if execution APIs erase types at the final handoff.

What changed:
- Added `runDetailed()` and `PipelineRunResult<TOutputs>` so execution returns typed outputs and task-result maps along with trace metadata.

Guardrail:
- Any new execution helper should preserve generic output maps instead of returning only untyped trace fragments.

## 2026-02-14

Context:
- Added dual-runtime conformance and golden parity gates.

Learning:
- Contract parity needs machine-readable checks (`--json`) at every runtime boundary.

What changed:
- Added JSON status output for Rust `check-ast`.
- Conformance harness now consumes Rust JSON payloads and validates versions/order/levels.

Guardrail:
- Keep all cross-runtime checks machine-readable first; human text output is secondary.

## 2026-02-14

Context:
- Expanded trace goldens to resilient-policy scenarios.

Learning:
- Normalization must include nested timestamp fields (for example retry attempt history), not only top-level task timestamps.

What changed:
- Trace normalizer now scrubs nested `provenance.attempts[].started_at/finished_at`.
- Goldens regenerated after normalization fix.

Guardrail:
- When adding new trace substructures with timestamps, update normalizer and golden tests in the same change.

## 2026-02-14

Context:
- Versioned AST/trace contracts were bumped and synchronized across Python and Rust.

Learning:
- Version governance only works if constants, schemas, goldens, and runtime checks move in lockstep.

What changed:
- Added contract-version consistency tests spanning Python constants, schema consts, Rust constants, and goldens.

Guardrail:
- Never bump contract versions without a single atomic change touching all contract surfaces.

## 2026-02-14

Context:
- Started Rust execution migration with `run-task`.

Learning:
- Migration confidence improves when partial runtimes emit full contract-shaped fields early (`error_code`, provenance, timestamps).

What changed:
- Rust `run-task` now outputs normalized task-result style records and explicit error mapping.

Guardrail:
- Treat partial runtime outputs as contract surfaces, not temporary internal debug formats.

## 2026-02-14

Context:
- Built parity matrix across core, artifact-flow, fanout, and resilient-policy programs.

Learning:
- A parity matrix makes coverage gaps visible; “one happy-path example passes” is not enough.

What changed:
- Added resilient/fanout goldens.
- Added `scripts/parity_matrix.py` with dedicated test coverage.

Guardrail:
- Any new language feature should add at least one representative parity row and golden pair.

## 2026-02-14

Context:
- Implemented Rust retry/timeout policy-loop behavior for worker execution.

Learning:
- Retry semantics depend on both status and `error_code`; preserving Python's `retry_if` gating logic avoids accidental over-retries.

What changed:
- Rust `run-task`/`run-plan` now run per-attempt loops with timeout kill handling, retry delay calculation, and provenance attempt history.
- Added CLI tests for retry success path, timeout-only retry mode, and dependency execution after retried tasks.

Guardrail:
- Any future retry-policy change must include both `run-task` and `run-plan` behavior tests, plus explicit checks on provenance `attempts`.

## 2026-02-14

Context:
- Added Rust trace diagnostics assembly (`constraints`, `verify`, `verify_summary`) in `run-plan`.

Learning:
- Diagnostics parity needs a stable evaluation context contract (`shared_context + task_results`) as much as task execution parity.

What changed:
- Rust run-plan now evaluates constraint and verify expressions post-execution, emits unresolved constraint reasons, and summarizes verify failures.
- Added tests for success, failed verify summary, and unresolved-constraint semantics.

Guardrail:
- When adding new expression forms, add explicit evaluator tests and verify-summary expectations before changing parser or runtime behavior.

## 2026-02-14

Context:
- Started the TypeScript product pivot for contract-first agent workflow execution.

Learning:
- Standard Schema keeps the contract layer reusable across libraries while preserving strict runtime validation.

What changed:
- Added `ts/` runtime with `Pipeline`, `llmTask`, and per-task structured traces.
- Bound task contracts to `StandardSchemaV1` and validated with `@standard-schema/spec`.
- Kept examples in Zod without coupling runtime interfaces to Zod-only types.

Guardrail:
- Keep contract interfaces library-agnostic at API boundaries; examples can be opinionated, runtime surfaces should not be.

## 2026-02-14

Context:
- Hardened TypeScript runtime behavior for real LLM-provider use.

Learning:
- Provider adapters need deterministic parse tests, and retry behavior needs explicit attempt history in traces to stay debuggable.

What changed:
- Added mocked integration tests for OpenAI/Anthropic provider JSON parsing.
- Added task retry policies with `retryIf` and backoff/jitter timing in TS runtime.
- Emitted per-task attempt histories in trace payloads.

Guardrail:
- Any retry or provider parser change must add/update deterministic tests that assert trace-level diagnosis fields.

## 2026-02-14

Context:
- Built a TS onboarding path intended to validate value quickly with no API keys.

Learning:
- A deterministic broken-path demo is critical for proving trace-debug value; happy-path demos alone do not expose diagnostic advantage.

What changed:
- Added `pnpm quickstart` and `pnpm quickstart:broken` demo scripts.
- Added walkthrough instructions that point users directly to `tasks[].error_code`, `contract_issues`, and `raw_output`.

Guardrail:
- Keep a credential-free broken demo path in-repo and ensure it remains runnable as part of onboarding updates.

## 2026-02-14

Context:
- Began TS package distribution hardening.

Learning:
- Shipping confidence improves when pack-time boundaries are explicit (`exports` + `files`) and release checks run before version bumps.

What changed:
- Added npm metadata for publish-ready package surface.
- Added `release:check` script and publishing runbook.

Guardrail:
- Any new public runtime surface must be reflected in `exports` and validated via `release:check` before publish.

## 2026-02-14

Context:
- Added CI and release automation for TS package distribution.

Learning:
- Local release scripts reduce mistakes, but CI workflows make quality gates enforceable and audit-friendly across contributors.

What changed:
- Added `ts-quality` workflow for check/test/build/release-check.
- Added manual `ts-publish` workflow with pre-publish validation and npm token auth.

Guardrail:
- Keep `ts-quality` and local `release:check` semantically aligned so CI and local release behavior do not drift.

## 2026-02-14

Context:
- Added external trial instrumentation for time-to-diagnose metrics.

Learning:
- Trial outcomes are only decision-grade when diagnosis correctness and elapsed time are captured together with a consistent expected failure boundary.

What changed:
- Added trace diagnosis helper (`diagnoseFailure`) and trial session/summary utilities in TS runtime.
- Added `ts/scripts/trial-metrics.ts` to persist trial records in JSONL and compute baseline-vs-Condukt summary stats.
- Added `ts/docs/TRIALS.md` protocol for repeatable external studies.

Guardrail:
- Do not record elapsed diagnosis time without expected diagnosis fields (`task` and/or `error_code`), or speed claims become unauditable.

## 2026-02-14

Context:
- Added TypeScript lint/format tooling and aligned package operations with pnpm-only conventions.

Learning:
- Tooling conventions only stick when local scripts and CI workflows enforce the same command surface.

What changed:
- Added Biome config and TS lint/format/typecheck scripts.
- Updated CI quality/publish workflows and release docs to remove npm command usage for TS package workflows.

Guardrail:
- Any new JS/TS workflow command must use `pnpm` and be represented in both package scripts and CI if it is release-critical.

## 2026-02-14

Context:
- Migrated TypeScript tests to Vitest.

Learning:
- Vitest improves test ergonomics and speed for a TS library package without requiring a Vite app or bundler migration.

What changed:
- Replaced `tsx --test` runner with Vitest scripts.
- Updated TS tests to use Vitest assertion APIs.

Guardrail:
- Keep `pnpm test` in CI and local release checks as the single source of truth for TS test execution.

## 2026-02-14

Context:
- Improved trial analytics to better reflect real baseline-vs-Condukt comparisons.

Learning:
- Speedup claims are stronger when they are computed on paired participant/scenario samples instead of only comparing mode-level medians.

What changed:
- Added paired trial summary metrics and pair-level records in TS trial analytics.
- Added tests for pair construction and latest-run selection semantics.

Guardrail:
- Any public claim about trial speedup should cite paired metrics when paired samples are available.

## 2026-02-14

Context:
- Added trial quality-gate checks to reporting flow.

Learning:
- Trials need explicit acceptance criteria; otherwise a dataset can look promising while still being too small or too noisy for decisions.

What changed:
- Added summary gate evaluator and CLI gate flags with failure diagnostics.
- Trial report now exits non-zero when required thresholds are not met.

Guardrail:
- Treat gate thresholds as part of experiment design, not post-hoc tuning after seeing results.

## 2026-02-14

Context:
- Added markdown export for trial summaries.

Learning:
- Decision velocity increases when trial reports can be exported in a single deterministic command instead of manual spreadsheet/doc stitching.

What changed:
- Added markdown renderer for trial summaries and CLI export options (`--markdown-out`, `--title`, `--max-pairs`).
- Included gate status/failures in markdown output when thresholds are configured.

Guardrail:
- Keep markdown report structure stable so downstream sharing/review workflows remain predictable.

## 2026-02-14

Context:
- Aligned public naming across package/repository-facing surfaces.

Learning:
- Early naming drift between package, repo, and docs creates avoidable onboarding friction even when runtime behavior is stable.

What changed:
- Renamed TS package identity and trial mode label to `condukt-ai`.
- Updated repository metadata links and publish docs for the new canonical name.

Guardrail:
- Keep one canonical external identifier (`condukt-ai`) for package/repo/docs, and treat internal module paths (`condukt`) as implementation details.

## 2026-02-14

Context:
- Added compatibility handling for legacy trial mode labels.

Learning:
- Renames should include explicit ingestion normalization paths, not just output renames, to preserve historical data usability.

What changed:
- Added trial mode normalization and strict trial-record normalization for report ingestion.
- Added test coverage for legacy mode alias and malformed record rejection.

Guardrail:
- When renaming externally visible enums/labels, keep a temporary compatibility alias plus deterministic validation errors.

## 2026-02-14

Context:
- Added release-time guardrails for renamed package identity.

Learning:
- Naming consistency requires executable checks; doc-only guidance drifts too easily under rapid iteration.

What changed:
- Added release identity validator and guard script.
- Wired guard into `release:check` so packaging fails on legacy-name drift.

Guardrail:
- Keep release guard required in the release path whenever external package/repo identity changes.
