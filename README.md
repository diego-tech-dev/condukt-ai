# Condukt AI

Condukt AI is a TypeScript library for agent workflow orchestration with:

- contract-first task boundaries (Standard Schema compatible)
- structured traces for fast failure diagnosis
- LLM task adapters for OpenAI and Anthropic

The active product lives in `packages/core/` and is published as `condukt-ai`.
Documentation lives in `apps/web/` and is implemented with Astro Starlight.
Production docs domain: `https://condukt-ai.dev`.

## Quick Start

```bash
pnpm install
pnpm check
pnpm test
pnpm --filter @condukt-ai/web build
pnpm --filter condukt-ai quickstart
pnpm --filter condukt-ai quickstart:broken
```

## Package Usage

See `/packages/core/README.md` for install and API examples.

```bash
pnpm add condukt-ai zod
```

Trials/diagnosis helpers are available via the `condukt-ai/trials` subpath.

## Repository Layout

- `packages/core/`: active runtime, tests, docs, release scripts
- `apps/web/`: Astro Starlight docs site with Monaco simulation playground
- `docs/`: project context (`PROJECT_COMPASS.md`, `FOUNDATIONS.md`, `LEARNINGS.md`)
- `ROADMAP.md`, `WORKLOG.md`, `DECISIONS.md`: planning and decision history

## Legacy Track Note

On 2026-02-14, legacy Python/Rust runtime tracks and their conformance harnesses were removed from this repository. The project is now intentionally TypeScript-only.
