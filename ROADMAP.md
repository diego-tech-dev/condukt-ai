# MissionGraph Roadmap

Last updated: 2026-02-13

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
