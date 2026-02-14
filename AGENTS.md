# AGENTS.md

Standard agent entrypoint for this repository.

## Project Overview

Condukt AI is an intent-first orchestration language for agent systems.

Core objective:
- define goals, constraints, plans, contracts, and verification in one deterministic workflow language
- keep runtime behavior portable across implementations via versioned AST/trace contracts

Read first for deeper context:
- `docs/PROJECT_COMPASS.md`
- `docs/FOUNDATIONS.md`
- `docs/LEARNINGS.md`
- `DECISIONS.md`

## Repository Map

- `condukt/`: parser, planner, executor, CLI, specs/constants
- `ts/`: TypeScript runtime prototype (Standard Schema contracts + trace-first pipeline)
- `examples/`: runnable `.mgl` programs
- `workers/`: demo worker implementations
- `spec/`: JSON schemas for AST and trace contracts
- `tests/`: conformance and behavior tests
- `tests/golden/`: golden reference artifacts

## Key Commands

- Parse program: `python3 -m condukt parse examples/ship_release.mgl`
- Validate program: `python3 -m condukt validate examples/ship_release.mgl --capability ci --capability prod_access`
- Show plan levels: `python3 -m condukt plan examples/ship_release.mgl --capability ci --capability prod_access`
- Run program (sequential): `python3 -m condukt run examples/ship_release.mgl --capability ci --capability prod_access --sequential`
- Run program with deterministic retry seed: `python3 -m condukt run examples/ship_release.mgl --capability ci --capability prod_access --retry-seed 42 --sequential`
- Run fan-out demo: `python3 -m condukt run examples/release_fanout.mgl --capability ci --capability prod_access --max-parallel 8`
- Run resilient policy demo: `python3 -m condukt run examples/release_resilient.mgl --capability ci --capability prod_access --max-parallel 8`
- Run artifact-flow demo: `python3 -m condukt run examples/release_artifacts.mgl --capability ci --capability prod_access --sequential`
- Render graph: `python3 -m condukt graph examples/release_fanout.mgl`
- Test suite: `python3 -m unittest discover -s tests -p "test_*.py"`
- Rust bootstrap tests: `cargo test --manifest-path rust/condukt-rs/Cargo.toml`
- Rust AST contract check (JSON): `cargo run --manifest-path rust/condukt-rs/Cargo.toml -- check-ast /tmp/ship_release.ast.json --json`
- Rust single-task worker prototype: `cargo run --manifest-path rust/condukt-rs/Cargo.toml -- run-task /tmp/ship_release.ast.json --task test_suite --base-dir examples --json`
- Rust plan execution prototype: `cargo run --manifest-path rust/condukt-rs/Cargo.toml -- run-plan /tmp/ship_release.ast.json --base-dir examples --capability ci --capability prod_access --json`
- Multi-runtime conformance: `python3 scripts/conformance.py --json`
- Dual-runtime golden gate: `python3 scripts/conformance.py --json --require-goldens`
- Parity matrix: `python3 scripts/parity_matrix.py --json`
- TypeScript install/check: `cd ts && pnpm install && pnpm check`
- TypeScript lint: `cd ts && pnpm lint`
- TypeScript format: `cd ts && pnpm format`
- TypeScript typecheck: `cd ts && pnpm typecheck`
- TypeScript tests: `cd ts && pnpm test`
- TypeScript build: `cd ts && pnpm build`
- TypeScript quickstart trace demo: `cd ts && pnpm quickstart`
- TypeScript quickstart broken demo: `cd ts && pnpm quickstart:broken`

## Hard Invariants

- Only `.mgl` program files are accepted by `parse_file`.
- AST contract is versioned (`ast_version`) and defined by `spec/ast-v1.schema.json`.
- Trace contract is versioned (`trace_version`) and defined by `spec/trace-v1.schema.json`.
- Error codes in `condukt/spec.py` are stable API surface.
- Behavior changes require updating tests and golden fixtures together.

## Change Rules

- Prefer minimal, explicit changes over broad refactors.
- If language semantics change:
  - update schemas in `spec/`
  - update golden files in `tests/golden/`
  - update `DECISIONS.md`
  - update `docs/PROJECT_COMPASS.md` if direction/invariants changed
- Keep CLI output deterministic where possible.

## Coding Conventions

- JavaScript/TypeScript workflow must use `pnpm` for scripts, tests, and dependency management.
- Never use `npm` or `yarn` for JS/TS scripts/tests/dependency operations.
- Never use TypeScript `any`.
- Prefer `unknown` + explicit narrowing, or runtime validation via Standard Schema/Zod contracts.

## Completion Checklist

- Code compiles/runs locally.
- `python3 -m unittest discover -s tests -p "test_*.py"` passes.
- `python3 scripts/conformance.py --json --require-goldens` passes.
- `python3 scripts/parity_matrix.py --json` passes.
- Docs reflect the behavior you changed.
