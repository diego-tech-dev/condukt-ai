# Condukt Learnings

Last updated: 2026-02-14

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
