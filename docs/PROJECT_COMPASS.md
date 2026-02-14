# Condukt AI Project Compass

This document is the durable context for Condukt AI. It is the first file to read when resuming work.

Companion docs:
- `AGENTS.md` for agent entrypoint and execution workflow.
- `FOUNDATIONS.md` for language/runtime design baselines.
- `LEARNINGS.md` for implementation lessons and guardrails.
- `DECISIONS.md` for decision history.

## Purpose

Condukt AI is an intent-first orchestration language for agents.

It exists to make multi-agent work:
- explicit (`goal`, `constraints`, `plan`, `contracts`, `verify`)
- safe (typed contracts + capability checks)
- auditable (structured, versioned traces)
- portable across runtimes (stable AST/trace contracts)

Active product track:
- TypeScript contract-first pipeline runtime (`ts/`, package name `condukt-ai`) focused on fast agent workflow debugging via boundary contracts + structured traces.

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
- Error codes in `condukt/spec.py` are stable API surface.
- Golden outputs in `tests/golden/` define expected behavior.

## Architecture Snapshot

- Parser: `condukt/parser.py`
- AST serializer: `condukt/serialization.py`
- Planner: `condukt/planner.py`
- Executor: `condukt/executor.py`
- CLI: `condukt/cli.py`
- TypeScript runtime: `ts/src/pipeline.ts`
- TypeScript providers: `ts/src/providers.ts`
- Spec constants: `condukt/spec.py`
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

- Language renamed to Condukt.
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
- Added Rust bootstrap runtime (`rust/condukt-rs`) for contract-level conformance checks.
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
- Added `FOUNDATIONS.md` with explicit decisions/tradeoffs/migration paths across core language dimensions.
- Added Rust `run-plan` prototype with sequential dependency-order task execution and fail-fast semantics.
- Added Rust retry/timeout policy-loop parity (`timeout`, `retries`, `retry_if`, `backoff`, `jitter`) for both `run-task` and `run-plan`.
- Added Rust run-plan diagnostics assembly for `constraints`, `verify`, and grouped `verify_summary` outputs.
- Added TypeScript runtime prototype (`ts/`) with Standard Schema contracts, trace-first pipeline execution, and OpenAI/Anthropic adapters.
- Added TypeScript task retry policies with per-attempt trace history and provider integration tests.
- Added credential-free TS quickstart + broken-run walkthrough to demonstrate trace-based failure diagnosis in under 10 minutes.
- Named the TypeScript package `condukt-ai`.
- Added npm publish-readiness metadata and release validation scripts for `condukt-ai`.
- Added TS quality and publish GitHub Actions workflows for reproducible CI/release gates.
- Added TS trace-diagnosis and external-trial metric instrumentation (session start/finish/report with JSONL records).
- Added TS Biome lint/format baseline and pnpm-only package workflow enforcement.
- Migrated TS tests to Vitest while keeping non-Vite build/runtime tooling.
- Added paired trial analytics (participant+scenario matching) for stronger speedup measurement.
- Added trial report quality gates for speedup/accuracy/sample-threshold evaluation.
- Added markdown trial reporting output for shareable experiment artifacts.
- Aligned public package/repository identity on `condukt-ai`.

## Near-Term Direction

1. Run external user trials with `ts/docs/TRIALS.md` protocol, quality gates, and markdown exports for decision-ready baseline-vs-Condukt AI metrics.
2. Iterate TS API shape from trial feedback while preserving contract/trace core value.

## Resume Checklist

When picking up work:

1. Read this file.
2. Read `docs/FOUNDATIONS.md`.
3. Read `docs/LEARNINGS.md`.
4. Run:
   - `python3 -m unittest discover -s tests -p "test_*.py"`
   - `python3 -m condukt parse examples/ship_release.mgl`
   - `python3 -m condukt run examples/ship_release.mgl --capability ci --capability prod_access --sequential`
   - `python3 scripts/conformance.py --json`
   - `python3 scripts/conformance.py --json --require-goldens`
   - `python3 scripts/parity_matrix.py --json`
5. Confirm no schema/golden drift unless intentional.

## Update Protocol

After each meaningful change:

- update `Decision Log` with date and decisions
- update `Near-Term Direction` if priorities change
- if contracts changed, follow `spec/VERSIONING.md` and update schemas/goldens/runtime constants together
