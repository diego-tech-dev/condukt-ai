# Publishing Condukt

## Preconditions

- npm account authenticated (`npm whoami`)
- package name availability checked (`npm view condukt`)
- clean git state

## 1) Validate release locally

```bash
cd ts
pnpm install
pnpm release:check
```

This runs:
- typecheck
- tests
- build
- npm pack dry-run

## 2) Bump version

```bash
cd ts
npm version patch
```

Use `minor`/`major` when needed.

## 3) Publish

```bash
cd ts
npm publish --access public
```

## 4) Verify install

```bash
pnpm dlx tsx -e "import('condukt').then(m => console.log(Object.keys(m).slice(0,8)))"
```

## Release notes template

- Added:
- Changed:
- Fixed:
- Breaking:
