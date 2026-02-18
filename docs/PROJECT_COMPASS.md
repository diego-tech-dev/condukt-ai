# Condukt AI Project Compass

This document is the durable context for Condukt AI.

Companion docs:
- `AGENTS.md` for execution conventions.
- `FOUNDATIONS.md` for core design choices.
- `LEARNINGS.md` for implementation learnings and guardrails.
- `DECISIONS.md` for decision history.

## Purpose

Condukt AI is a TypeScript-first orchestration library for agent workflows.

It exists to make agent pipelines:
- safe at boundaries (typed contracts)
- observable (structured traces)
- fast to debug (explicit diagnosis surfaces)

## Product Focus

Primary track:
- npm package `condukt-ai` in `packages/core/`
- Standard Schema-compatible contracts
- deterministic, machine-readable traces
- practical CLI-assisted trial instrumentation for diagnosis-time measurement

## North Star

Minimize time-to-diagnose when an agent pipeline returns incorrect output.

The product should make it obvious:
- which task failed
- why it failed
- what contract or output violated expectations

## Current Scope

- TypeScript library runtime and examples in `packages/core/`
- Astro Starlight docs site in `apps/web/` (deployed to `condukt-ai.dev`)
- LLM provider adapters (OpenAI, Anthropic)
- Trial measurement tooling (`packages/core/scripts/trial-metrics.ts`)
- CI checks for both workspaces (runtime + docs site)

## Explicit Non-Goals

- No Python runtime track in this repository.
- No Rust runtime track in this repository.
- No multi-runtime parity/conformance harness maintenance.
- No DSL parser/runtime track in this repository.

## Architecture Snapshot

- Pipeline runtime: `packages/core/src/pipeline.ts`
- Contract validation: `packages/core/src/contracts.ts`
- Failure diagnosis: `packages/core/src/diagnostics.ts`
- Trial domain: `packages/core/src/trials/`
- Provider adapters: `packages/core/src/providers.ts`
- Release identity guard: `packages/core/src/release_identity.ts`
- Trial CLI: `packages/core/scripts/trial-metrics.ts`

## Resume Checklist

1. Read this file.
2. Read `docs/FOUNDATIONS.md`.
3. Read `docs/LEARNINGS.md`.
4. Run:
   - `pnpm install`
   - `pnpm lint`
   - `pnpm typecheck`
   - `pnpm test`
   - `pnpm build`
   - `pnpm docs:api:check`
   - `pnpm --filter @condukt-ai/web linkcheck`
   - `pnpm --filter condukt-ai release:check`
5. Continue from open roadmap/worklog milestones.

## Update Protocol

After each meaningful change:
- append decisions in `DECISIONS.md`
- update milestone status in `ROADMAP.md` and `WORKLOG.md`
- keep release/testing commands aligned with TS-only workflow
