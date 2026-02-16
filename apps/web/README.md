# apps/web

This folder hosts the Condukt AI website application (docs + marketing + product web surface).

Constraints:
- Framework-agnostic placeholder for now.
- No Next.js assumptions in repository tooling.
- Consume workspace packages with `workspace:*` dependencies where needed.

Quality commands (from repo root):
- `pnpm --filter @condukt-ai/web lint`
- `pnpm --filter @condukt-ai/web typecheck`
- `pnpm --filter @condukt-ai/web test`
- `pnpm --filter @condukt-ai/web build`
