# AGENTS.md

Standard agent entrypoint for this repository.

## What This Is

Condukt AI is a TypeScript contract-driven agent framework. The core idea: developers write a schema (Zod/StandardSchema), the framework generates LLM instructions from it, validates output against it, and feeds structured diagnostic feedback back to the agent on retry. One primitive — the contract — serves as developer specification, agent guidance, and runtime validation.

Published as `condukt-ai` on npm. Monorepo with pnpm workspaces + Turborepo.

Read first for deeper context:
- `docs/PROJECT_COMPASS.md` — purpose, scope, non-goals
- `docs/FOUNDATIONS.md` — core design choices and tradeoffs
- `docs/LEARNINGS.md` — implementation guardrails
- `DECISIONS.md` — architectural decision log

## Repository Map

- `packages/core/` — published npm library (`condukt-ai`)
- `apps/web/` — Astro Starlight docs site (`condukt-ai.dev`)
- `docs/` — project context and design records
- `.github/workflows/` — CI quality and publish workflows

## Commands

All commands run from repository root. Always use `pnpm`, never `npm` or `yarn`.

```bash
# Full workspace
pnpm install                        # install all dependencies
pnpm build                          # build all workspaces (turbo)
pnpm lint                           # biome lint all workspaces
pnpm typecheck                      # tsc --noEmit all workspaces
pnpm test                           # vitest run all workspaces
pnpm check                          # lint + typecheck

# Core package only
pnpm --filter condukt-ai test              # run core tests
pnpm --filter condukt-ai test -- -t "name" # run single test by name
pnpm --filter condukt-ai test:watch        # vitest watch mode
pnpm --filter condukt-ai build             # tsc compile to dist/
pnpm --filter condukt-ai lint              # biome lint core only
pnpm --filter condukt-ai typecheck         # typecheck core only
pnpm --filter condukt-ai quickstart        # run example with FakeProvider
pnpm --filter condukt-ai release:check     # full release gate (clean+check+test+build+guard+pack)

# Docs site
pnpm --filter @condukt-ai/web dev          # local dev server
pnpm --filter @condukt-ai/web check        # lint + typecheck docs
pnpm --filter @condukt-ai/web linkcheck    # verify internal/external links
pnpm docs:api                              # regenerate TypeDoc API docs
```

## Architecture

```
packages/core/src/
├── index.ts                  # Public API barrel — all user-facing exports
├── pipeline.ts               # Re-exports from pipeline/ submodule
├── agent.ts                  # (planned) Agent primitive: schema → LLM → validate → retry
├── schema.ts                 # (planned) Schema introspection: Zod AST → structural metadata
├── instructions.ts           # (planned) Schema → LLM-readable instruction text
├── contracts.ts              # StandardSchema validation, ContractIssue normalization
├── diagnostics.ts            # Extract first-failure diagnosis from a PipelineTrace
├── providers.ts              # OpenAI + Anthropic provider adapters (raw fetch, JSON mode)
├── json.ts                   # JSON parse/preview utilities
├── pipeline/
│   ├── class.ts              # Pipeline builder (immutable, generic accumulator for typed outputs)
│   ├── execution.ts          # DAG runner: topological levels, retry loop, contract enforcement
│   ├── graph.ts              # Kahn's algorithm for dependency resolution + cycle detection
│   ├── llm.ts                # llmTask() adapter: LLMTaskDefinition → TaskDefinition
│   ├── runtime.ts            # Injectable runtime env (now, random, sleep) for deterministic tests
│   ├── trace.ts              # Trace assembly helpers
│   └── types.ts              # Core types: TaskDefinition, TaskTrace, PipelineTrace, etc.
```

### Key design patterns

**Contract-first validation:** Every task declares a `StandardSchemaV1` output contract. Outputs are validated at task boundaries via `validateContract()`. Failures produce `ContractIssue[]` with dotted field paths — these drive both developer diagnostics and (planned) agent retry feedback.

**Typed pipeline builder:** `Pipeline` uses generic type accumulation — each `.addTask()` call merges the task's output type into `TOutputs`. This gives compile-time safety for dependency references (`after: ['taskA']`) and typed access to outputs via `runDetailed().outputs`.

**Duplicate task ID prevention:** Enforced at both compile time (`DuplicateTaskIdConstraint` conditional type) and runtime (Map lookup in `addTaskInternal`).

**Provider-model typing:** `LLMProvider<TModel, TSettingsByModel>` uses a settings map keyed by model ID, so `modelSettings` is conditionally required based on which model is selected. `llmTask()` infers this automatically.

**Runtime injection:** `PipelineRuntimeEnvironment` abstracts `Date.now()`, `Math.random()`, and `setTimeout` so tests are fully deterministic without mocking globals.

**DAG execution:** `buildDependencyLevels()` (Kahn's algorithm) produces execution levels. Tasks within a level run in parallel via `Promise.all`. Levels execute sequentially. If any task in a level fails, remaining levels are skipped.

## Conventions

- Never use TypeScript `any` — use `unknown` + narrowing or StandardSchema validation
- All source is ESM (`"type": "module"`, NodeNext resolution) — use `.js` extensions in imports
- `readonly` on all type properties and function parameters
- Biome for lint/format (2-space indent, 100 char line width)
- Vitest for tests, located in `packages/core/test/`

## Documentation & Comments

- Add JSDoc to public APIs; include `@remarks` or `@example` when helpful.
- Write comments that capture intent, and remove stale notes during refactors.
- Update architecture or design docs when introducing significant patterns.

## Code Organization

- **Imports at the top** — NEVER inside functions or mid-file
- **Type hints always** — function parameters and return types
- **Comments for intent only** — DO NOT comment what code does (should be self-explanatory), unless they are public APIs
- **Kebab-case filenames**: `user-session.ts`, `data-service.ts`
- **PascalCase** for components, classes, interfaces, enums; **camelCase** for everything else

## Change Rules

- Keep changes minimal, explicit, and test-backed.
- Preserve public package API stability unless a breaking change is intentional and documented.
- Update docs and `DECISIONS.md` when behavior or architectural direction changes.

## Completion Checklist

After every change, all of these must pass:

- `pnpm lint`
- `pnpm typecheck`
- `pnpm test`
- `pnpm build`
- `pnpm --filter condukt-ai release:check`

## Current Direction

See `ROADMAP.md` for the active plan. The project is pivoting from a pipeline-only library to a contract-driven agent framework with five phases: strip dead code → schema-to-instruction engine → diagnostic retry loop → agent() primitive → pipeline integration + polish.
