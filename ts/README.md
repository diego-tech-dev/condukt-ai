# condukt-ai (prototype)

TypeScript-first contract and trace runtime for agent workflows.

Focus of this package:
- Standard Schema task contracts (`@standard-schema/spec`) so users can bring Zod or any compliant schema library
- structured execution traces for fast failure diagnosis
- LLM task adapters for OpenAI and Anthropic JSON workflows
- provider-model-aware typing (model IDs + settings inferred per provider/model)
- typed dependency context via `pipeline.addLLMTask(...)` so `dependencyOutputs` matches declared `after` tasks
- task-level retry policies (`retries`, `backoffMs`, `jitterMs`, `retryIf`) with attempt history in traces
- Vitest-powered TypeScript test workflow

## Install

From npm:

```bash
pnpm add condukt-ai zod
```

From source:

```bash
cd ts
pnpm install
```

## Run checks

```bash
pnpm lint
pnpm format
pnpm typecheck
pnpm test
pnpm check
pnpm build
pnpm release:guard
pnpm release:check
```

## 10-minute quickstart

Run successful flow:

```bash
pnpm quickstart
```

Run intentionally broken flow:

```bash
pnpm quickstart:broken
```

Both commands write `trace.quickstart.json`. Follow `docs/TRACE_WALKTHROUGH.md` to diagnose the broken run from trace data.

## External trial instrumentation

Capture diagnosis-time metrics for external users:

```bash
pnpm trial:start --participant p1 --scenario quickstart-broken --mode condukt-ai --trace trace.quickstart.json
pnpm trial:finish --session trials/sessions/<session-id>.session.json --diagnosed-task draft --diagnosed-error-code CONTRACT_OUTPUT_VIOLATION
pnpm trial:report
pnpm trial:report -- --min-records 6 --min-accuracy 0.75 --min-pairs 3 --min-speedup 1.5
pnpm trial:report -- --markdown-out trials/report.md --title "Condukt AI Trial Report"
```

Trial protocol details: `docs/TRIALS.md`.

## Minimal usage

```ts
import { z } from "zod";
import { Pipeline, createOpenAIProvider } from "condukt-ai";

const provider = createOpenAIProvider();

const pipeline = new Pipeline("research-and-write").addLLMTask({
    id: "research",
    provider,
    model: "gpt-4.1-mini",
    modelSettings: {
      temperature: 0.2,
      maxTokens: 300,
    },
    output: z.object({ topics: z.array(z.string()) }),
    prompt: () => "Return JSON with topics.",
  });

const result = await pipeline.runDetailed();
console.log(result.trace.status);
console.log(result.outputs.research?.topics);
```

See `examples/research-write.ts` for a 3-step pipeline example.
