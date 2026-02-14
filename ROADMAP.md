# Condukt AI Roadmap

Last updated: 2026-02-14

Current sprint status: completed

## Autonomy Sprint (5 milestones)

1. `M1` Planning scaffolding
- Add durable planning docs (`ROADMAP.md`, `WORKLOG.md`).
- Define scope, sequencing, and done criteria for autonomous execution.

2. `M2` Artifact contracts (`produces`/`consumes`)
- Extend `plan` task syntax with explicit artifact declarations.
- Track artifact registry during execution.
- Enforce fail-fast artifact availability checks before task execution.

3. `M3` Verify diagnostics
- Add grouped verify summary with pass/fail counts.
- Include failed-check diagnostics with source lines.
- Keep existing `verify` list stable for compatibility.

4. `M4` CLI validation workflow
- Add `mgl validate` command for parse + static validation.
- Support optional machine-readable JSON output.
- Keep non-zero exit semantics for invalid programs.

5. `M5` Conformance and docs hardening
- Add end-to-end tests for artifacts + diagnostics + validate command.
- Add example `.mgl` program that demonstrates artifact flows.
- Update docs and decision log to preserve context continuity.

## Milestone Gate

For each milestone:
- implement minimal complete feature slice
- add/update tests
- run test suite
- update `WORKLOG.md`
- atomic commit + push

## Near-Term Backlog (after sprint)

1. Artifact schema typing (typed artifact payload contracts)
2. Policy enhancements (retry jitter, retry conditions)
3. Rust runtime bootstrap against existing AST/trace contracts

## Backlog Sprint (Autonomous)

Status: completed

1. `B1` Typed artifact payload contracts: completed
2. `B2` Policy enhancements (`retry_if`, jitter): completed
3. `B3` Rust runtime bootstrap: completed

## Quality Sprint (Autonomous)

Status: completed

1. `Q1` Deterministic retry seeding: completed
2. `Q2` Multi-runtime conformance harness: completed
3. `Q3` Contract/versioning governance checks: completed

## Next Sprint (Autonomous)

Status: completed

1. `N1` Rust contract CLI parity hardening: completed
2. `N2` Rust trace semantics expansion: completed
3. `N3` Dual-runtime golden conformance gate: completed

## Follow-up Sprint (Autonomous)

Status: completed

1. `F1` Rust worker execution prototype (single task path): completed
2. `F2` Rust task-result contract shaping (error_code/provenance): completed
3. `F3` Cross-runtime parity matrix for resilient policies: completed

## Execution Sprint (Autonomous)

Status: completed

1. `E1` Rust multi-task sequential execution (dependency order): completed
2. `E2` Rust retry/timeout policy loop parity for task execution: completed
3. `E3` Rust trace assembly for full-plan runs (tasks + verify summary): completed

## TS Pivot Sprint (Autonomous)

Status: completed

1. `T1` TypeScript core runtime bootstrap (Standard Schema contracts + trace-first pipeline): completed
2. `T2` Real LLM adapter hardening (OpenAI/Anthropic integration tests + retry policy): completed
3. `T3` 10-minute user path (`pnpm dlx`/template + demo trace walkthrough): completed

## Distribution Sprint (Autonomous)

Status: completed

1. `U1` TS package publish readiness (metadata/exports/files/release checks): completed
2. `U2` CI + release automation for TS package quality gates: completed
3. `U3` External trial instrumentation for time-to-diagnose metric capture: completed

## Trial Evidence Sprint (Autonomous)

Status: completed

1. `R1` Paired trial analytics by participant/scenario: completed
2. `R2` CLI quality gates for trial success criteria (speedup/accuracy/pairs): completed
3. `R3` Shareable markdown summary output + documentation refresh: completed

## Identity Alignment Sprint (Autonomous)

Status: completed

1. `I1` Align package/repo/docs identity to `condukt-ai`: completed
2. `I2` Legacy trial-mode compatibility (`condukt` -> `condukt-ai`) and input normalization: completed
3. `I3` Release guardrails for renamed identity (name checks + docs/CLI hardening): completed

## Trial Refactor Sprint (Autonomous)

Status: completed

1. `J1` Trial module split (`types`/`normalization`/`session`/`summary`): completed
2. `J2` Strict command-scoped parsing and validation in `trial-metrics` CLI: completed
3. `J3` Path-agnostic trace goldens + CLI integration coverage: completed

## TS-Only Consolidation Sprint (Autonomous)

Status: completed

1. `K1` Remove Python and Rust runtime tracks from repository: completed
2. `K2` Remove cross-runtime conformance/parity scripts and tests: completed
3. `K3` Rewrite root architecture docs for TS-only scope: completed

## Typed Provider DX Sprint (Autonomous)

Status: completed

1. `L1` Introduce provider/model generic typing surface in runtime API: completed
2. `L2` Enforce model-specific settings inference in `llmTask`: completed
3. `L3` Add compile-time type fixtures for provider/model contract safety: completed

## Typed Dependency Context Sprint (Autonomous)

Status: completed

1. `M1` Generic task/runtime context typing for dependency output inference: completed
2. `M2` Add `Pipeline.addLLMTask` typed builder path and migrate examples: completed
3. `M3` Add compile-time dependency-key fixtures and validate with release checks: completed

## Typed Run Result Sprint (Autonomous)

Status: completed

1. `N1` Add typed pipeline run API (`runDetailed`) returning trace + typed outputs: completed
2. `N2` Add runtime tests for typed run-output behavior: completed
3. `N3` Add compile-time run-output key safety fixtures and docs updates: completed

## Builder Guard Sprint (Autonomous)

Status: completed

1. `P1` Add compile-time duplicate task-id constraints for typed builders: completed
2. `P2` Add runtime fallback test coverage for dynamic duplicate IDs: completed
3. `P3` Update typecheck fixtures and docs for duplicate-id safety guarantees: completed

## Ecosystem Execution Sprint (Autonomous)

Status: completed

1. `E1` TanStack AI adapter integration for pipeline tasks: completed
2. `E2` Parallel execution for independent dependency levels: completed
3. `E3` Adaptive control-flow primitives for conditional execution: completed
4. `E4` Trials API extraction into dedicated package surface: completed
