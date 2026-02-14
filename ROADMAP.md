# MissionGraph Roadmap

Last updated: 2026-02-14

Current sprint status: completed

## Autonomy Sprint (5 milestones)

1. `M1` Planning scaffolding
- Add durable planning docs (`ROADMAP.md`, `WORKLOG.md`).
- Define scope, sequencing, and done criteria for autonomous execution.

2. `M2` Artifact contracts (`produces`/`consumes`)
- Extend `plan` task syntax with explicit artifact declarations.
- Track artifact registry during execution.
- Enforce fail-fast artifact availability checks before task execution.

3. `M3` Verify diagnostics
- Add grouped verify summary with pass/fail counts.
- Include failed-check diagnostics with source lines.
- Keep existing `verify` list stable for compatibility.

4. `M4` CLI validation workflow
- Add `mgl validate` command for parse + static validation.
- Support optional machine-readable JSON output.
- Keep non-zero exit semantics for invalid programs.

5. `M5` Conformance and docs hardening
- Add end-to-end tests for artifacts + diagnostics + validate command.
- Add example `.mgl` program that demonstrates artifact flows.
- Update docs and decision log to preserve context continuity.

## Milestone Gate

For each milestone:
- implement minimal complete feature slice
- add/update tests
- run test suite
- update `WORKLOG.md`
- atomic commit + push

## Near-Term Backlog (after sprint)

1. Artifact schema typing (typed artifact payload contracts)
2. Policy enhancements (retry jitter, retry conditions)
3. Rust runtime bootstrap against existing AST/trace contracts

## Backlog Sprint (Autonomous)

Status: completed

1. `B1` Typed artifact payload contracts: completed
2. `B2` Policy enhancements (`retry_if`, jitter): completed
3. `B3` Rust runtime bootstrap: completed

## Quality Sprint (Autonomous)

Status: completed

1. `Q1` Deterministic retry seeding: completed
2. `Q2` Multi-runtime conformance harness: completed
3. `Q3` Contract/versioning governance checks: completed

## Next Sprint (Autonomous)

Status: completed

1. `N1` Rust contract CLI parity hardening: completed
2. `N2` Rust trace semantics expansion: completed
3. `N3` Dual-runtime golden conformance gate: completed

## Follow-up Sprint (Autonomous)

Status: completed

1. `F1` Rust worker execution prototype (single task path): completed
2. `F2` Rust task-result contract shaping (error_code/provenance): completed
3. `F3` Cross-runtime parity matrix for resilient policies: completed

## Execution Sprint (Autonomous)

Status: in_progress

1. `E1` Rust multi-task sequential execution (dependency order): completed
2. `E2` Rust retry/timeout policy loop parity for task execution: pending
3. `E3` Rust trace assembly for full-plan runs (tasks + verify summary): pending
