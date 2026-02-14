# Condukt Foundations

Last updated: 2026-02-14

This document captures the active design baseline for the TypeScript-only Condukt AI runtime.

## 1) API And Type Model

Decision:
- TypeScript-first API with strict typing.
- Runtime contract validation via Standard Schema interface.
- No `any` in runtime/test code.

Why:
- Strong DX and explicit contract surfaces are core to Condukt's value.

Tradeoffs:
- Users in non-TypeScript ecosystems have extra integration friction.

Migration path:
- Add thin adapters/SDK wrappers later without changing core TS contract semantics.

## 2) Contract Boundaries

Decision:
- Validate task outputs and dependent inputs at boundaries.
- Fail fast on contract violations.

Why:
- Silent propagation of bad task outputs is the dominant failure mode.

Tradeoffs:
- Strict failures can surface more errors earlier during development.

Migration path:
- Add optional policy controls (for example soft-fail modes) without weakening default strict behavior.

## 3) Trace Model

Decision:
- Structured JSON traces are first-class runtime output.
- Traces must contain enough context for diagnosis without rerunning workflows.

Why:
- Time-to-diagnose is the primary success metric.

Tradeoffs:
- Extra trace payload volume.

Migration path:
- Add configurable trace verbosity tiers while preserving required diagnosis fields.

## 4) Execution Model

Decision:
- DAG-style task orchestration with retries/backoff/jitter policies.
- LLM providers integrated as task adapters.

Why:
- Covers common agent workflow patterns with deterministic behavior.

Tradeoffs:
- Not a distributed scheduler; scope stays local/runtime-library level.

Migration path:
- Add remote/distributed executors behind the same task/trace contracts later.

## 5) Tooling Strategy

Decision:
- `pnpm` for all JS/TS operations.
- Biome for lint/format and Vitest for tests.
- Release guardrails enforced by `pnpm release:check`.

Why:
- Fast feedback and deterministic release gates.

Tradeoffs:
- Toolchain choices constrain contributor preferences.

Migration path:
- Re-evaluate tooling only if it measurably blocks quality or velocity.

## 6) Scope Boundary

Decision:
- Repository is intentionally TypeScript-only.
- Python/Rust runtime tracks are decommissioned and no longer maintained.

Why:
- Single-track focus improves product velocity and reduces maintenance overhead.

Tradeoffs:
- No in-repo cross-runtime parity harness.

Migration path:
- If a second runtime is needed later, define it as a fresh initiative with clear product justification and contract tests grounded in the TS runtime behavior.
