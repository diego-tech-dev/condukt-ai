# External Trial Instrumentation

Goal: capture a measurable `time-to-diagnose` metric for broken agent workflows.

This workflow records:
- participant
- mode (`baseline` or `condukt`)
- expected failure boundary (task + error code)
- participant diagnosis
- elapsed diagnosis time
- accuracy

## 1) Prepare a broken trace

```bash
cd ts
pnpm quickstart:broken
```

This writes `trace.quickstart.json`.

## 2) Start a timed trial session

```bash
cd ts
pnpm trial:start \
  --participant p1 \
  --scenario quickstart-broken \
  --mode condukt \
  --trace trace.quickstart.json
```

Output includes a session file path (stored under `ts/trials/sessions/` by default).

For baseline runs without a trace-driven expectation:

```bash
cd ts
pnpm trial:start \
  --participant p1 \
  --scenario quickstart-broken \
  --mode baseline \
  --expected-task draft \
  --expected-error-code CONTRACT_OUTPUT_VIOLATION
```

## 3) Finish session after participant gives diagnosis

```bash
cd ts
pnpm trial:finish \
  --session trials/sessions/<session-id>.session.json \
  --diagnosed-task draft \
  --diagnosed-error-code CONTRACT_OUTPUT_VIOLATION
```

This appends one record to `ts/trials/diagnosis-metrics.jsonl`.

## 4) Generate summary report

```bash
cd ts
pnpm trial:report
pnpm trial:report -- --json
```

Report includes:
- total records
- accuracy
- median and p90 elapsed diagnosis times
- median speedup ratio (`baseline / condukt`)

## Suggested 2-week target

- collect at least 3 external participants
- run one baseline + one condukt diagnosis per participant
- success criterion: at least one participant repeats usage unprompted
