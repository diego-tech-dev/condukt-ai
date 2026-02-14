# Publishing Condukt

## Preconditions

- npm account authenticated (`pnpm npm whoami`)
- package name availability checked (`pnpm npm view condukt-ai`)
- clean git state

## 1) Validate release locally

```bash
cd ts
pnpm install
pnpm release:check
```

This runs:
- lint
- typecheck
- tests
- build
- `pnpm pack` artifact check

## 2) Bump version

```bash
cd ts
pnpm version patch
```

Use `minor`/`major` when needed.

## 3) Publish

```bash
cd ts
pnpm publish --access public --no-git-checks
```

Or use GitHub Actions manual workflow:
- run `ts-publish`
- ensure repo secret `NPM_TOKEN` is configured

## 4) Verify install

```bash
pnpm dlx tsx -e "import('condukt-ai').then(m => console.log(Object.keys(m).slice(0,8)))"
```

## Release notes template

- Added:
- Changed:
- Fixed:
- Breaking:
