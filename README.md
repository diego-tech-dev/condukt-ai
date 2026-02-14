# Condukt AI Prototype

Minimal intent-first language prototype for agent orchestration.

Project context and direction:
- Agent entrypoint: `AGENTS.md`
- See `docs/PROJECT_COMPASS.md` before making design changes.
- Foundational architecture decisions: `docs/FOUNDATIONS.md`
- Implementation memory track: `docs/LEARNINGS.md`
- Decision log: `DECISIONS.md`

This MVP includes:

- A tiny DSL with `goal`, `types`, `constraints`, `plan`, `contracts`, and `verify`
- Parser + validator
- DAG planner (`after` dependencies) with level detection
- Local executor for Python/JavaScript/TypeScript workers with parallel fan-out
- Structured trace output (`status`, `confidence`, `provenance`)
- Mermaid graph rendering
- Versioned interchange contracts (`ast_version`, `trace_version`)

## TypeScript Pivot (New)

A TypeScript-first runtime prototype now lives in `ts/` with:
- Standard Schema contracts (`@standard-schema/spec`) for schema-library flexibility
- fail-fast task boundary validation
- structured trace output for fast diagnosis
- OpenAI and Anthropic JSON task adapters

Current TS package name: `condukt-ai`.

Package release runbook: `ts/docs/PUBLISHING.md`.

Quick start:

```bash
cd ts
pnpm install
pnpm test
pnpm check
pnpm quickstart
pnpm quickstart:broken
```

Walkthrough: `ts/docs/TRACE_WALKTHROUGH.md`.
External trial metrics: `ts/docs/TRIALS.md`.

Example pipeline:

```bash
cd ts
pnpm tsx examples/research-write.ts
```

## DSL Example

```mgl
goal "ship release"

types {
  type TestReport "coverage:number, tests_passed:int"
  type DeployInput "dependencies.test_suite.status:str, dependencies.test_suite.output.coverage:number"
  type DeployReport "release:str, rollback_ready:bool, risk:number"
}

constraints {
  risk <= 0.2
}

plan {
  task test_suite uses "../workers/test_suite.py" requires capability.ci
  task deploy_prod uses "../workers/deploy_prod.py" requires capability.prod_access after test_suite with timeout 30s retries 2 backoff 1s
}

contracts {
  task test_suite output @TestReport
  task deploy_prod input @DeployInput output @DeployReport
}

verify {
  test_suite.status == "ok"
  test_suite.output.coverage >= 0.9
  deploy_prod.status == "ok"
}
```

## Run the demo

```bash
python3 -m condukt run examples/ship_release.mgl \
  --capability ci \
  --capability prod_access \
  --retry-seed 42 \
  --trace-out traces/ship_release.json
```

Run fan-out demo with parallel execution:

```bash
python3 -m condukt run examples/release_fanout.mgl \
  --capability ci \
  --capability prod_access \
  --max-parallel 8
```

Run resilient policy demo (timeouts + retries + backoff):

```bash
python3 -m condukt run examples/release_resilient.mgl \
  --capability ci \
  --capability prod_access \
  --max-parallel 8
```

Run explicit artifact-flow demo (`produces`/`consumes`):

```bash
python3 -m condukt run examples/release_artifacts.mgl \
  --capability ci \
  --capability prod_access \
  --sequential
```

Parse, inspect levels, and render graph:

```bash
python3 -m condukt parse examples/ship_release.mgl
python3 -m condukt validate examples/ship_release.mgl --capability ci --capability prod_access
python3 -m condukt plan examples/ship_release.mgl --capability ci --capability prod_access
python3 -m condukt graph examples/release_fanout.mgl
```

## Worker contract

Each worker receives JSON from stdin:

```json
{
  "task": "task_name",
  "goal": "program goal",
  "constraints": [],
  "dependencies": {},
  "variables": {}
}
```

Worker paths are resolved relative to the `.mgl` file location.

Worker should print JSON to stdout:

```json
{
  "status": "ok",
  "confidence": 0.9,
  "output": {},
  "provenance": {}
}
```

`status` defaults to `error` on non-zero exit or invalid JSON.

## Types and contracts

Use `types` for reusable schemas and `contracts` for task I/O enforcement.

Type syntax:

- `type <TypeName> "<path:type, ...>"`
- Example: `type DeployReport "release:str, rollback_ready:bool, risk:number"`

Contract syntax:

- Inline: `task deploy output "release:str, risk:number"`
- Referenced: `task deploy output @DeployReport`

Schema details:

- Paths use dot notation (for example `dependencies.test_suite.status`)
- Type names: `str`, `int`, `float`, `number`, `bool`, `dict`, `list`, `any`, `none`
- Aliases: `string`, `integer`, `boolean`, `object`, `array`
- Optional fields: suffix type with `?` (for example `risk:number?`)

Contract checks are fail-fast:

- Input schema is checked before worker execution.
- Output schema is checked immediately after worker response.
- First contract violation halts the remaining plan and returns a failed trace.

## Artifact contracts

Use task-level artifact contracts in `plan` to make dataflow explicit:

- `produces <artifact[, ...]>`: task must emit matching keys in `output`.
- `consumes <artifact[, ...]>`: task requires artifacts from dependency producers.
- Optional typed form: `<artifact>:<type>` where `<type>` is primitive (`number`, `str`, etc.) or a named type from `types`.

Example:

```mgl
task test_suite uses "../workers/test_suite.py" requires capability.ci produces test_report
task deploy_prod uses "../workers/deploy_prod.py" requires capability.prod_access after test_suite consumes test_report
```

Typed example:

```mgl
task lint uses "../workers/lint.py" requires capability.ci produces report:number
task deploy_prod uses "../workers/deploy_prod.py" requires capability.prod_access after lint consumes report:number
```

Runtime behavior:

- Consumers fail fast if required artifacts are unavailable.
- Producers fail if declared artifacts are missing from worker `output`.
- Typed consumers/producers fail on artifact type contract violations.

## Parallel execution

- Tasks run by dependency levels.
- Independent tasks in the same level can run concurrently.
- Use `--sequential` to disable concurrency.
- Use `--max-parallel N` to cap level concurrency.

## Task execution policies

`plan` tasks support retry and timeout policies through a `with` clause:

- `timeout <duration>`: per-attempt timeout (for example `30s`, `250ms`).
- `retries <int>`: number of retries after the first attempt.
- `retry_if <mode>`: retry strategy (`error`, `timeout`, `worker_failure`).
- `backoff <duration>`: exponential retry base delay (`delay * 2^(attempt-1)`).
- `jitter <duration>`: random delay added per retry (`0..jitter`).
- CLI `--retry-seed <int>`: deterministic retry+jitter behavior for reproducible runs.

Example:

```mgl
task deploy_prod uses "../workers/deploy_prod.py" requires capability.prod_access after test_suite with timeout 30s retries 2 retry_if timeout backoff 1s jitter 250ms
```

Notes:

- `with` keys can be ordered freely.
- `backoff` requires `retries > 0`.
- `jitter` requires `retries > 0`.

Plan output includes both flattened `task_order` and per-level structure.

## Portability contracts

- Primary language name: `Condukt`
- Primary extension: `.mgl`
- Preferred CLI: `mgl` (when installed) or `python3 -m condukt`
- `parse_file` rejects non-`.mgl` extensions.
- `parse` output includes `ast_version` for stable AST interoperability.
- `run` output includes `trace_version` and normalized `error_code` fields.
- `run` output includes `verify_summary` for grouped verify diagnostics.
- JSON schemas are versioned in `spec/ast-v1.schema.json` and `spec/trace-v1.schema.json`.
- Conformance goldens live in `tests/golden/` to validate future runtimes.

## Rust Bootstrap

Rust bootstrap runtime is available at `rust/condukt-rs`.

```bash
python3 -m condukt parse examples/ship_release.mgl > /tmp/ship_release.ast.json
cargo run --manifest-path rust/condukt-rs/Cargo.toml -- check-ast /tmp/ship_release.ast.json --json
cargo run --manifest-path rust/condukt-rs/Cargo.toml -- trace-skeleton /tmp/ship_release.ast.json
cargo run --manifest-path rust/condukt-rs/Cargo.toml -- run-task /tmp/ship_release.ast.json --task test_suite --base-dir examples --json
cargo run --manifest-path rust/condukt-rs/Cargo.toml -- run-plan /tmp/ship_release.ast.json --base-dir examples --capability ci --capability prod_access --json
```

## Multi-Runtime Conformance

Run Python vs Rust contract conformance checks:

```bash
python3 scripts/conformance.py --json
python3 scripts/conformance.py --json --require-goldens
```

This validates AST/trace versions, task order, dependency-level execution metadata, and optionally golden parity.

Cross-runtime parity matrix (including resilient-policy coverage):

```bash
python3 scripts/parity_matrix.py --json
```

## Tests

```bash
python3 -m unittest discover -s tests -p "test_*.py"
```

## License

Apache-2.0. See `LICENSE`.
