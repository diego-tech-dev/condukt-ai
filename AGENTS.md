# AGENTS.md

Standard agent entrypoint for this repository.

## Project Overview

Condukt AI is a TypeScript-first orchestration runtime focused on:
- typed task handoffs using Standard Schema-compatible contracts
- structured traces for fast failure diagnosis across multi-step agent flows

Read first:
- `docs/PROJECT_COMPASS.md`
- `docs/FOUNDATIONS.md`
- `docs/LEARNINGS.md`
- `DECISIONS.md`

## Repository Map

- `packages/core/`: published npm library (`condukt-ai`)
- `apps/web/`: website/docs app location (framework-neutral placeholder)
- `docs/`: project context and design records
- `.github/workflows/`: CI quality and publish workflows

## Workspace Commands (Run From Repository Root)

- Install dependencies: `pnpm install`
- Lint all workspaces: `pnpm lint`
- Typecheck all workspaces: `pnpm typecheck`
- Test all workspaces: `pnpm test`
- Build all workspaces: `pnpm build`
- Run full root checks: `pnpm check`
- Core release gate: `pnpm --filter condukt-ai release:check`

Core package-specific:
- Quickstart (healthy): `pnpm --filter condukt-ai quickstart`
- Quickstart (broken): `pnpm --filter condukt-ai quickstart:broken`
- Trials report: `pnpm --filter condukt-ai trial:report`

## Coding Conventions

- Always use `pnpm` for scripts, tests, and dependency management.
- Never use `npm` or `yarn`.
- Never use TypeScript `any`.
- Prefer `unknown` plus explicit narrowing, or runtime validation via Standard Schema/Zod.

## Change Rules

- Keep changes minimal, explicit, and test-backed.
- Preserve public package API stability unless a breaking change is intentional and documented.
- Update docs and `DECISIONS.md` when behavior or architectural direction changes.

## Completion Checklist

- `pnpm lint` passes.
- `pnpm typecheck` passes.
- `pnpm test` passes.
- `pnpm build` passes.
- `pnpm --filter condukt-ai release:check` passes.
- Docs match current workspace layout (`packages/core`, `apps/web`).

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
