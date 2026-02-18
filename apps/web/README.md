# apps/web

`apps/web` is the Astro Starlight docs site for `condukt-ai`.

## Stack

- Astro + Starlight
- React islands (Monaco playground)
- Biome linting
- Vitest smoke/unit tests

## Commands (from repo root)

```bash
pnpm --filter @condukt-ai/web dev
pnpm --filter @condukt-ai/web lint
pnpm --filter @condukt-ai/web typecheck
pnpm --filter @condukt-ai/web test
pnpm --filter @condukt-ai/web build
pnpm --filter @condukt-ai/web linkcheck
```

## Build output

Static output is generated in `apps/web/dist` and deployed to Cloudflare Pages.

- Production domain: `https://condukt-ai.dev`
- Preview domain pattern: `*.pages.dev`
