# missiongraph-ts (prototype)

TypeScript-first contract and trace runtime for agent workflows.

Focus of this package:
- Standard Schema task contracts (`@standard-schema/spec`) so users can bring Zod or any compliant schema library
- structured execution traces for fast failure diagnosis
- LLM task adapters for OpenAI and Anthropic JSON workflows

## Install

```bash
cd ts
pnpm install
```

## Run checks

```bash
pnpm test
pnpm check
pnpm build
```

## Minimal usage

```ts
import { z } from "zod";
import { Pipeline, llmTask, createOpenAIProvider } from "missiongraph-ts";

const provider = createOpenAIProvider();
const pipeline = new Pipeline("research-and-write");

pipeline.addTask(
  llmTask({
    id: "research",
    provider,
    model: "gpt-4.1-mini",
    output: z.object({ topics: z.array(z.string()) }),
    prompt: () => "Return JSON with topics.",
  }),
);

const trace = await pipeline.run();
console.log(trace);
```

See `examples/research-write.ts` for a 3-step pipeline example.
