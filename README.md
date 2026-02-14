# Condukt AI

Condukt AI is a TypeScript library for agent workflow orchestration with:

- contract-first task boundaries (Standard Schema compatible)
- structured traces for fast failure diagnosis
- LLM task adapters for OpenAI and Anthropic

The active product lives in `ts/` and is published as `condukt-ai`.

## Quick Start

```bash
cd ts
pnpm install
pnpm check
pnpm test
pnpm quickstart
pnpm quickstart:broken
```

## Package Usage

See `/ts/README.md` for install and API examples.

```bash
pnpm add condukt-ai zod
```

## Repository Layout

- `ts/`: active runtime, tests, docs, release scripts
- `docs/`: project context (`PROJECT_COMPASS.md`, `FOUNDATIONS.md`, `LEARNINGS.md`)
- `ROADMAP.md`, `WORKLOG.md`, `DECISIONS.md`: planning and decision history

## Legacy Track Note

On 2026-02-14, legacy Python/Rust runtime tracks and their conformance harnesses were removed from this repository. The project is now intentionally TypeScript-only.
