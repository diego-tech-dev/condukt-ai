# AGENTS.md

Standard agent entrypoint for this repository.

## Project Overview

MissionGraph is an intent-first orchestration language for agent systems.

Core objective:
- define goals, constraints, plans, contracts, and verification in one deterministic workflow language
- keep runtime behavior portable across implementations via versioned AST/trace contracts

Read first for deeper context:
- `docs/PROJECT_COMPASS.md`
- `DECISIONS.md`

## Repository Map

- `missiongraph/`: parser, planner, executor, CLI, specs/constants
- `examples/`: runnable `.mgl` programs
- `workers/`: demo worker implementations
- `spec/`: JSON schemas for AST and trace contracts
- `tests/`: conformance and behavior tests
- `tests/golden/`: golden reference artifacts

## Key Commands

- Parse program: `python3 -m missiongraph parse examples/ship_release.mgl`
- Show plan levels: `python3 -m missiongraph plan examples/ship_release.mgl --capability ci --capability prod_access`
- Run program (sequential): `python3 -m missiongraph run examples/ship_release.mgl --capability ci --capability prod_access --sequential`
- Run fan-out demo: `python3 -m missiongraph run examples/release_fanout.mgl --capability ci --capability prod_access --max-parallel 8`
- Run resilient policy demo: `python3 -m missiongraph run examples/release_resilient.mgl --capability ci --capability prod_access --max-parallel 8`
- Render graph: `python3 -m missiongraph graph examples/release_fanout.mgl`
- Test suite: `python3 -m unittest discover -s tests -p "test_*.py"`

## Hard Invariants

- Only `.mgl` program files are accepted by `parse_file`.
- AST contract is versioned (`ast_version`) and defined by `spec/ast-v1.schema.json`.
- Trace contract is versioned (`trace_version`) and defined by `spec/trace-v1.schema.json`.
- Error codes in `missiongraph/spec.py` are stable API surface.
- Behavior changes require updating tests and golden fixtures together.

## Change Rules

- Prefer minimal, explicit changes over broad refactors.
- If language semantics change:
  - update schemas in `spec/`
  - update golden files in `tests/golden/`
  - update `DECISIONS.md`
  - update `docs/PROJECT_COMPASS.md` if direction/invariants changed
- Keep CLI output deterministic where possible.

## Completion Checklist

- Code compiles/runs locally.
- `python3 -m unittest discover -s tests -p "test_*.py"` passes.
- Docs reflect the behavior you changed.
