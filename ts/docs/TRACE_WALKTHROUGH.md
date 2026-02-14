# 10-Minute Trace Walkthrough

Goal: show how quickly a broken agent step can be diagnosed from trace data.

## 1. Install and run happy path

```bash
cd ts
pnpm install
pnpm quickstart
```

This writes `trace.quickstart.json` in the `ts/` directory.

Confirm:
- `status` is `"ok"`
- all tasks are `"ok"`

## 2. Run intentionally broken path

```bash
cd ts
pnpm quickstart:broken
```

This run intentionally returns invalid `draft.claims` type (string instead of `string[]`).

Confirm in console output:
- `Status: failed`
- `Failed task: draft`
- `Error code: CONTRACT_OUTPUT_VIOLATION`

## 3. Diagnose from trace (no re-run required)

Open `trace.quickstart.json` and inspect:
- `tasks[]` entry for `task == "draft"`
- `error_code`
- `contract_issues[]` path/message
- `raw_output`

You should see:
- contract path `claims`
- a type mismatch message
- exact broken payload in `raw_output`

## Why this matters

The diagnosis path is deterministic:
1. Find first `tasks[].status == "error"`.
2. Read `error_code` and `contract_issues`.
3. Fix that task boundary contract mismatch.

This is the core MissionGraph TS value proposition: contract failures are explicit and traceable at the exact task boundary.
