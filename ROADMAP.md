# Condukt AI Roadmap

Last updated: 2026-02-16

## Vision

**Contract-driven agents.** The developer writes what they want (a schema), not how to get it (a prompt). The framework generates instructions for the agent from the contract, validates output against it, and when validation fails, feeds structured diagnosis back to the agent automatically. One primitive — the contract — serves three roles: developer specification, agent guidance, and runtime validation.

The tagline: **Write a schema. Get a working agent. Debug it with a trace.**

## Target API

```typescript
import { agent, pipeline } from 'condukt-ai'
import { createAnthropicProvider } from 'condukt-ai/providers'
import { z } from 'zod'

// --- Single task (the "hello world") ---

const a = agent({
  provider: createAnthropicProvider({ apiKey: process.env.ANTHROPIC_API_KEY }),
  model: 'claude-sonnet-4-5-20250929',
})

const result = await a.task({
  input: { text: 'The battery lasts forever but the screen cracks easily' },
  output: z.object({
    sentiment: z.enum(['positive', 'negative', 'mixed']),
    confidence: z.number().min(0).max(1),
    aspects: z.array(z.object({
      feature: z.string(),
      opinion: z.enum(['positive', 'negative', 'neutral']),
    })),
  }),
})
// result.data is fully typed. No prompt written. The schema WAS the instruction.
// result.trace captures every attempt, contract violation, and diagnostic retry.

// --- Reusable task ---

const extractReceipt = a.define('extract-receipt', {
  input: z.object({ imageDescription: z.string() }),
  output: z.object({
    vendor: z.string(),
    total: z.number(),
    items: z.array(z.object({ name: z.string(), price: z.number() })),
  }),
})

const receipt = await extractReceipt({ imageDescription: '...' })

// --- Multi-step pipeline ---

const research = pipeline('research')
  .agent(a)
  .task('search', {
    output: z.object({
      results: z.array(z.object({ title: z.string(), url: z.string().url(), snippet: z.string() })),
    }),
    prompt: (ctx) => `Find information about: ${ctx.input.query}`,
  })
  .task('synthesize', {
    after: ['search'],
    output: z.object({
      summary: z.string().min(100),
      keyPoints: z.array(z.string()).min(3),
      sources: z.array(z.string().url()),
    }),
  })
```

---

## Phase 0 — Strip to the Bone

**Goal:** Remove everything that doesn't serve the contract-driven agent vision. The codebase should be lean enough that every file has a clear reason to exist.

### 0.1 Remove trials system

The trials system (session management, statistical aggregation, CLI tooling) solves a measurement problem that doesn't exist yet. There are no users to measure.

**Files to delete:**
- `src/trials/` — entire directory (normalization.ts, session.ts, shared.ts, summary.ts, types.ts)
- `src/trials.ts` — re-export barrel
- `scripts/trial-metrics.ts` — CLI tool (~14K lines of script)
- `test/trials.test.ts` — trial session/summary tests
- `test/trial-metrics-cli.test.ts` — CLI tests
- `docs/TRIALS.md` — trial protocol docs

**Files to update:**
- `package.json` — remove `./trials` subpath export, remove `trial:start`/`trial:finish`/`trial:report` scripts
- `index.ts` — remove trials re-exports
- `biome.json` — remove `trials` from exclude list

### 0.2 Remove TanStack adapter

Coupling to a pre-1.0 library (`@tanstack/ai@^0.5.0`) adds dependency risk with no proven user demand.

**Files to delete:**
- `src/tanstack.ts`
- `test/tanstack.test.ts`

**Files to update:**
- `package.json` — remove `@tanstack/ai` from dependencies
- `index.ts` — remove `tanstackChatTask` export

### 0.3 Remove release identity guard

Validating that your README contains specific strings before publishing is ceremony for a one-person project.

**Files to delete:**
- `src/release_identity.ts`
- `test/release_identity.test.ts`
- `scripts/release-identity-guard.ts`

**Files to update:**
- `package.json` — remove `release:guard` script, simplify `release:check` to skip guard step
- `index.ts` — remove release identity exports (if any)

### 0.4 Simplify exports

After removals, `index.ts` should export only what matters for the new API. Keep existing pipeline/provider/contract/diagnostics exports — they'll be refactored in later phases but shouldn't break.

**Done criteria:**
- `pnpm build` succeeds
- `pnpm test` passes (remaining tests)
- `pnpm typecheck` passes
- No dead imports, no orphaned files
- Every remaining source file has a clear purpose in the contract-driven agent story

---

## Phase 1 — Schema-to-Instruction Engine

**Goal:** Build the core innovation. A function that takes any StandardSchema-compatible schema (Zod, ArkType, Valibot) and generates clear, structured natural language instructions that an LLM can follow to produce conforming output.

This is the piece that makes "write a schema, get a working agent" possible.

### 1.1 Schema introspection layer

**New file:** `src/schema.ts`

Build a function that walks a StandardSchema and extracts structural metadata:

```typescript
interface SchemaField {
  readonly path: string            // e.g. "aspects[].feature"
  readonly type: string            // "string" | "number" | "boolean" | "array" | "object" | "enum"
  readonly required: boolean
  readonly constraints: readonly SchemaConstraint[]
  readonly description?: string    // from .describe() in Zod
  readonly children?: readonly SchemaField[]
}

interface SchemaConstraint {
  readonly kind: string            // "min" | "max" | "minLength" | "maxLength" | "enum" | "pattern" | "url" | "email" | etc.
  readonly value: unknown          // the constraint value (e.g. 0 for min(0), ['a','b'] for enum)
}

interface SchemaIntrospection {
  readonly fields: readonly SchemaField[]
  readonly rootType: string
}

function introspectSchema(schema: StandardSchemaV1): SchemaIntrospection
```

**How it works:** StandardSchema v1 doesn't expose metadata directly, but the `~standard` property includes a `vendor` field and the `types` generic. For Zod specifically, the underlying `_def` structure is inspectable. The introspection layer should:

1. First try Zod-specific introspection (check if `schema._def` exists, walk the Zod AST)
2. Fall back to a "black box" mode that generates a basic instruction from the schema's TypeScript type signature
3. Be extensible — other schema libraries can add their own introspector later

**Implementation strategy for Zod introspection:**
- Zod schemas have a `_def` property with a `typeName` field (e.g. `ZodString`, `ZodNumber`, `ZodObject`, `ZodArray`, `ZodEnum`)
- Each type has specific fields: `ZodString._def.checks` contains `{ kind: 'min', value: 5 }` etc.
- `ZodObject._def.shape()` returns the child schemas
- `ZodEnum._def.values` contains the allowed values
- `ZodOptional` wraps an inner schema
- `.describe()` sets `_def.description`

**Key Zod types to handle:**
- `z.string()` — with `.min()`, `.max()`, `.url()`, `.email()`, `.regex()`, `.describe()`
- `z.number()` — with `.min()`, `.max()`, `.int()`, `.positive()`, `.nonnegative()`
- `z.boolean()`
- `z.enum()` — extract allowed values
- `z.array()` — with `.min()`, `.max()`, inner element schema
- `z.object()` — recurse into shape, track required vs optional keys
- `z.union()` / `z.discriminatedUnion()` — list variants
- `z.literal()` — exact value
- `z.nullable()` / `z.optional()` — mark as optional

**Tests (`test/schema.test.ts`):**
- Flat object with string/number/boolean fields
- Nested object (object containing objects)
- Array of objects with constraints (`z.array(z.object({...})).min(3)`)
- Enum fields
- Optional vs required fields
- Fields with `.describe()` annotations
- Number ranges (`z.number().min(0).max(1)`)
- String constraints (`z.string().min(100).url()`)
- Black-box fallback for non-Zod schemas

### 1.2 Instruction generator

**New file:** `src/instructions.ts`

Build a function that takes a `SchemaIntrospection` (or directly a `StandardSchemaV1`) and produces a clear text block the LLM will receive as part of its prompt.

```typescript
function generateInstructions(schema: StandardSchemaV1, options?: InstructionOptions): string

interface InstructionOptions {
  readonly style?: 'concise' | 'detailed'   // default: 'concise'
  readonly includeExampleShape?: boolean     // default: true
}
```

**Output format example** for the sentiment analysis schema:

```
Respond with a JSON object matching this exact structure:

{
  "sentiment": "<one of: positive, negative, mixed>",
  "confidence": "<number between 0 and 1>",
  "aspects": [
    {
      "feature": "<string>",
      "opinion": "<one of: positive, negative, neutral>"
    }
  ]
}

Requirements:
- sentiment: Must be one of: "positive", "negative", "mixed"
- confidence: Must be a number >= 0 and <= 1
- aspects: Must be an array of objects
  - aspects[].feature: Must be a string
  - aspects[].opinion: Must be one of: "positive", "negative", "neutral"
```

**Design rules:**
- Always include a JSON shape example at the top (LLMs follow examples better than rules)
- List constraints as bullet points after the example
- Use plain English, not schema jargon ("Must be a number >= 0 and <= 1", not "z.number().min(0).max(1)")
- Include `.describe()` annotations inline ("sentiment: The overall emotional tone of the text. Must be one of...")
- For optional fields, mark them explicitly: "(optional, omit if not applicable)"
- Output valid JSON in the example shape (use placeholder strings, not actual values)

**Tests (`test/instructions.test.ts`):**
- Simple flat schema generates expected instruction text
- Nested schema produces hierarchical requirements
- Enum constraints list all values
- Number ranges show bounds
- `.describe()` annotations appear in output
- Array min/max constraints
- Optional fields marked correctly
- The generated instruction, when fed to an LLM with a simple input, produces output that passes the schema (integration test, can be skipped in CI)

### 1.3 Wire into existing LLM task path

Update `src/pipeline/llm.ts` to automatically prepend schema-generated instructions to the user's prompt when an `llmTask` is executed.

**Changes to `llmTask()`:**
- Before calling `provider.generateJSON()`, call `generateInstructions(definition.output)` to get the instruction block
- Prepend it to the system prompt (or create one if none exists)
- The user's `prompt` function still runs and provides the actual task context
- The combined prompt becomes: `[schema instructions]\n\n[user prompt]`

**The user's existing prompt is augmented, not replaced.** If the developer provides a prompt, it's appended after the schema instructions. If they don't (in the new `agent.task()` API), the schema instructions alone are the prompt.

**Tests:**
- Existing pipeline tests still pass (instructions are additive)
- New test: an LLM task with a schema produces a prompt that includes instruction text
- New test: mock provider receives the combined prompt

**Done criteria:**
- `introspectSchema()` handles all common Zod types
- `generateInstructions()` produces clear, LLM-readable text for any supported schema
- Instructions are automatically injected into LLM task prompts
- All tests pass

---

## Phase 2 — Diagnostic Retry Loop

**Goal:** When a task's output fails contract validation, format the violation as structured, agent-readable feedback and inject it into the next retry attempt. This closes the loop: contract failure becomes agent guidance, not just a gate.

### 2.1 Diagnostic message formatter

**New file:** `src/diagnosis.ts` (replaces current `diagnostics.ts`)

Build a function that takes contract validation issues and the raw LLM output, and produces a clear retry prompt:

```typescript
interface DiagnosticRetryContext {
  readonly issues: readonly ContractIssue[]
  readonly rawOutput: string
  readonly attempt: number
  readonly schema: StandardSchemaV1
}

function formatDiagnosticRetry(context: DiagnosticRetryContext): string
```

**Output example:**

```
Your previous response did not match the required format. Here are the specific issues:

1. Field "confidence": Must be a number between 0 and 1, but you returned 1.5
2. Field "aspects[2].opinion": Must be one of "positive", "negative", "neutral", but you returned "great"

Your previous output was:
{"sentiment":"mixed","confidence":1.5,"aspects":[...]}

Please correct these specific fields and return the complete JSON object again.
```

**Design rules:**
- List each issue with the field path and what went wrong
- Include the raw output so the agent can see what it produced
- Be specific about what's expected vs what was received
- Don't repeat the full schema instructions (the agent already has them from the first attempt)
- Keep it concise — one paragraph context, numbered issues, the raw output, one-line ask

**Tests (`test/diagnosis.test.ts`):**
- Single field violation produces readable message
- Multiple violations listed as numbered items
- Long raw output is truncated in the message
- Path formatting is human-readable ("aspects[2].opinion", not "aspects.2.opinion")

### 2.2 Integrate into retry loop

**Changes to `src/pipeline/execution.ts`:**

The current `executeTaskWithRetry` function retries by calling `task.run(context)` again with the same context. The agent gets zero feedback about what went wrong.

Modify the retry path for `CONTRACT_OUTPUT_VIOLATION` errors:

1. When contract validation fails and retry is allowed, call `formatDiagnosticRetry()` to build the diagnostic message
2. Store the diagnostic message in the task's runtime context so the next `task.run()` call can access it
3. For LLM tasks specifically: the `llmTask` adapter appends the diagnostic message to the prompt on retry attempts

**Changes to types:**

```typescript
// Add to TaskRuntimeContext
interface TaskRuntimeContext<...> {
  readonly outputs: ...
  readonly taskResults: ...
  readonly dependencyOutputs: ...
  readonly previousAttempt?: {           // NEW
    readonly rawOutput: string
    readonly issues: readonly ContractIssue[]
    readonly diagnosticMessage: string
  }
}
```

**Changes to `llmTask()` in `src/pipeline/llm.ts`:**

```typescript
// Inside the run function:
async run(context) {
  const prompt = await definition.prompt(context)
  const system = ...

  // If this is a retry with diagnostic feedback, append it
  let fullPrompt = prompt
  if (context.previousAttempt) {
    fullPrompt = `${prompt}\n\n${context.previousAttempt.diagnosticMessage}`
  }

  const response = await definition.provider.generateJSON({
    model: definition.model,
    prompt: fullPrompt,
    system,
    settings: definition.modelSettings,
  })
  ...
}
```

**Changes to `executeTaskWithRetry()` in `src/pipeline/execution.ts`:**

When a contract violation occurs and retry is permitted:
1. Build the diagnostic message via `formatDiagnosticRetry()`
2. Create a new context with `previousAttempt` populated
3. Pass this enriched context to the next `task.run()` call

**Trace additions:**

Each attempt trace should include the diagnostic message that was sent (if any), so developers can see exactly what guidance the agent received:

```typescript
// Add to TaskAttemptTrace
interface TaskAttemptTrace {
  readonly attempt: number
  readonly status: 'ok' | 'error'
  readonly error_code?: string
  readonly error?: string
  readonly started_at: string
  readonly finished_at: string
  readonly duration_ms: number
  readonly diagnostic_prompt?: string    // NEW: the retry guidance sent to the agent
}
```

**Tests:**
- Contract violation on attempt 1 → diagnostic message injected into attempt 2 prompt
- Diagnostic message includes the specific field paths and constraint descriptions
- Trace records the diagnostic prompt for each retry attempt
- Agent that fails once but succeeds on guided retry produces a passing trace
- Multiple violations formatted correctly across retries
- Non-contract errors (execution failures) do NOT get diagnostic retry (behavior unchanged)

**Done criteria:**
- Contract violations produce structured, agent-readable feedback
- Feedback is automatically injected into retry prompts for LLM tasks
- Traces capture the full diagnostic retry story
- Existing retry behavior for non-contract errors is unchanged
- All existing tests still pass

---

## Phase 3 — The `agent()` Primitive

**Goal:** Build the simplest possible entry point for structured LLM output. One function, fully typed, no prompt required for simple cases, diagnostic retries built in.

### 3.1 Agent constructor

**New file:** `src/agent.ts`

```typescript
import type { LLMProvider } from './providers.js'
import type { StandardSchemaV1 } from '@standard-schema/spec'

interface AgentOptions<TModel extends string> {
  readonly provider: LLMProvider<TModel, any>
  readonly model: TModel
  readonly defaultRetries?: number          // default: 2 (for contract violations)
  readonly system?: string                  // default system prompt prefix
}

interface TaskOptions<TOutput, TInput = unknown> {
  readonly input?: TInput
  readonly output: StandardSchemaV1<unknown, TOutput>
  readonly prompt?: string                  // optional — if omitted, the schema IS the prompt
  readonly system?: string                  // overrides agent-level system
  readonly retry?: TaskRetryPolicy
}

interface TaskResult<TOutput> {
  readonly data: TOutput
  readonly trace: TaskTrace
}

interface Agent<TModel extends string> {
  task<TOutput>(options: TaskOptions<TOutput>): Promise<TaskResult<TOutput>>
  define<TOutput, TInput>(
    name: string,
    schema: { input: StandardSchemaV1<unknown, TInput>, output: StandardSchemaV1<unknown, TOutput> },
  ): (input: TInput) => Promise<TaskResult<TOutput>>
}

function agent<TModel extends string>(options: AgentOptions<TModel>): Agent<TModel>
```

**How `agent.task()` works internally:**

1. Call `generateInstructions(options.output)` to build schema instructions
2. Build the full prompt:
   - If `options.prompt` is provided: `[schema instructions]\n\n[user prompt]\n\nInput:\n[JSON.stringify(options.input)]`
   - If no prompt: `[schema instructions]\n\nInput:\n[JSON.stringify(options.input)]`
3. Call `provider.generateJSON()` with the combined prompt
4. Validate output against `options.output` contract
5. If validation fails and retries remain: build diagnostic message, retry with feedback
6. Return `{ data, trace }` on success, throw on exhausted retries

**How `agent.define()` works internally:**

1. Validates the input against the input schema
2. Calls `agent.task()` with the input serialized and the output schema
3. Returns the typed result

The implementation reuses:
- `generateInstructions()` from Phase 1
- `validateContract()` from existing `contracts.ts`
- `formatDiagnosticRetry()` from Phase 2
- Provider `generateJSON()` from existing `providers.ts`

But it does NOT go through the full pipeline execution engine. It's a direct, lightweight path for single-task execution. No DAG, no dependency resolution, no level-parallel execution. Just: prompt → LLM → validate → maybe retry → result.

### 3.2 Default retry policy for agents

Agents should retry contract violations by default (2 retries), because the diagnostic retry loop is the whole point. This is different from the pipeline default (0 retries) to keep pipelines explicit.

```typescript
// Agent-level defaults
const AGENT_DEFAULT_RETRIES = 2
const AGENT_DEFAULT_RETRY_IF = 'contract_violation'
```

The developer can override per-task:

```typescript
a.task({
  output: z.object({ ... }),
  retry: { retries: 0 },  // disable retries for this specific task
})
```

### 3.3 Trace output for agent tasks

Every `agent.task()` call produces a `TaskTrace` with the same structure as pipeline task traces. This means the same trace viewer, the same `diagnoseFailure()` function, and the same debugging workflow applies to both agent tasks and pipeline tasks.

The trace includes:
- `attempts` array with each attempt's timing, status, and diagnostic prompt (if any)
- `contract_issues` for the final attempt (if it failed)
- `input` (the constructed prompt)
- `output` (the validated data)
- `raw_output` (the LLM's raw text response)
- `meta` (provider, model, response_id, usage)

**Tests (`test/agent.test.ts`):**
- `agent.task()` with simple schema returns typed, validated data (mock provider)
- `agent.task()` without prompt succeeds using schema instructions alone
- `agent.task()` with prompt includes both schema instructions and user prompt
- `agent.task()` with input serializes it into the prompt
- Contract violation triggers diagnostic retry with feedback
- Second attempt receives diagnostic message from first failure
- Retries exhausted throws with trace attached
- `agent.define()` validates input and returns typed output
- `agent.define()` rejects invalid input before calling the LLM
- Trace structure matches existing `TaskTrace` interface
- Custom retry policy overrides agent defaults

**Done criteria:**
- `agent()` is a working, fully typed entry point
- `agent.task()` produces structured output from a schema alone (no prompt needed)
- Diagnostic retries work end-to-end
- Traces capture the full agent execution story
- The API is genuinely 5 lines for a simple case

---

## Phase 4 — Pipeline Integration

**Goal:** Make the existing pipeline builder speak the same contract-driven language as the agent primitive, so multi-step workflows get the same benefits (schema instructions, diagnostic retries).

### 4.1 Simplify pipeline task definitions for agent-backed tasks

Add a new method to the Pipeline builder that accepts an agent + schema-driven task:

```typescript
class Pipeline<TOutputs extends TaskOutputMap> {
  // Existing methods stay
  addTask(...): Pipeline<...>
  addLLMTask(...): Pipeline<...>

  // New: agent-backed task with contract-driven defaults
  addAgentTask<TOutput, TDependencies, TTaskId>(definition: {
    readonly id: TTaskId
    readonly agent: Agent
    readonly output: StandardSchemaV1<unknown, TOutput>
    readonly after?: TDependencies
    readonly when?: TaskCondition
    readonly prompt?: (context: TaskRuntimeContext) => string | Promise<string>
    readonly retry?: TaskRetryPolicy    // defaults to agent's retry policy
  }): Pipeline<MergeTaskOutputs<TOutputs, TTaskId, TOutput>>
}
```

**How `addAgentTask` works internally:**
- Wraps the agent's task execution into a `TaskDefinition`
- The `run()` method calls the agent's internal task path (schema instructions + diagnostic retry)
- Dependencies and conditions work exactly like existing tasks
- If no `prompt` is provided, the task runs on schema instructions + serialized dependency outputs

### 4.2 Pipeline-level agent binding

Allow setting a default agent for the pipeline so you don't repeat it on every task:

```typescript
const p = pipeline('research')
  .agent(myAgent)                    // sets default agent for all subsequent tasks
  .addAgentTask({ id: 'search', output: searchSchema })
  .addAgentTask({ id: 'synthesize', output: synthesisSchema, after: ['search'] })
```

This is sugar — each task still gets its own agent instance internally, but the developer doesn't have to pass it every time.

### 4.3 Keep backward compatibility

`addTask()` and `addLLMTask()` continue to work exactly as before. The new `addAgentTask()` is additive. You can mix agent tasks and manual tasks in the same pipeline.

**Tests:**
- Pipeline with `addAgentTask()` runs and produces typed outputs
- Agent task in pipeline receives dependency outputs from prior tasks
- Diagnostic retry works within pipeline context
- Mixed pipeline: `addTask()` + `addAgentTask()` in same pipeline
- Existing pipeline tests unchanged

**Done criteria:**
- Pipelines can use agent-backed tasks with contract-driven defaults
- Diagnostic retries work within pipeline execution
- Zero breaking changes to existing API
- Pipeline trace includes agent task traces with diagnostic information

---

## Phase 5 — Real-World Demo and Polish

**Goal:** Make the library showable. One real example that works with a real API, a rewritten README, and a clean first impression.

### 5.1 Real-world example

**New file:** `examples/real-world.ts`

A single file that:
1. Creates an Anthropic agent with a real API key (from env)
2. Runs a structured extraction task (e.g., extract structured data from a product review)
3. Prints the typed result
4. Prints the trace showing what happened

```bash
ANTHROPIC_API_KEY=sk-... npx tsx examples/real-world.ts
```

This should be copy-pasteable and produce impressive output in < 10 seconds.

**Second example:** `examples/pipeline-demo.ts`

A multi-step pipeline that:
1. Takes a topic as input
2. Step 1: Generates research questions (schema: array of strings, min 3)
3. Step 2: Answers each question (depends on step 1, schema: array of Q&A objects)
4. Step 3: Synthesizes a summary (depends on step 2, schema: object with summary + key findings)
5. Prints the final output and trace

### 5.2 README rewrite

Rewrite `packages/core/README.md` to lead with the new API:

**Structure:**
1. One-sentence pitch: "Contract-driven agents for TypeScript. Write a schema, get structured output."
2. Install: `pnpm add condukt-ai zod`
3. Quickstart (5 lines that actually work):
   ```typescript
   const a = agent({ provider: createAnthropicProvider(), model: 'claude-sonnet-4-5-20250929' })
   const { data } = await a.task({
     input: { text: 'Great product, terrible shipping' },
     output: z.object({
       sentiment: z.enum(['positive', 'negative', 'mixed']),
       confidence: z.number().min(0).max(1),
     }),
   })
   ```
4. "What just happened?" — explain the three roles of the contract
5. Pipeline example for multi-step
6. How diagnostic retries work
7. API reference (brief)

### 5.3 Update existing quickstart example

Replace `examples/quickstart-debug.ts` with an example that uses the new `agent()` API with a `FakeProvider` (for running without API keys). This is the `pnpm quickstart` command.

### 5.4 Root README alignment

Update the root `README.md` to reflect the new vision and API, pointing to the core package README for details.

### 5.5 Update exports

Final `index.ts` should export:

```typescript
// Primary API
export { agent } from './agent.js'
export type { Agent, AgentOptions, TaskOptions, TaskResult } from './agent.js'

// Pipeline API
export { Pipeline } from './pipeline.js'
export type { PipelineOptions, PipelineRunResult, PipelineTrace, TaskTrace, ... } from './pipeline.js'
export { llmTask } from './pipeline.js'

// Providers (from condukt-ai/providers or inline)
export { createAnthropicProvider, createOpenAIProvider } from './providers.js'
export type { LLMProvider, ... } from './providers.js'

// Contracts & Diagnostics
export { validateContract } from './contracts.js'
export { diagnoseFailure } from './diagnostics.js'

// Schema utilities (for advanced users)
export { introspectSchema, generateInstructions } from './schema.js'
```

**Done criteria:**
- `examples/real-world.ts` runs with a real API key and produces correct, validated output
- `examples/pipeline-demo.ts` runs a multi-step pipeline with real LLM calls
- README quickstart is copy-pasteable
- Someone seeing this for the first time understands the value proposition in 30 seconds
- `pnpm quickstart` runs without an API key (fake provider)

---

## What's Explicitly Out of Scope

These are real features that real users will eventually want. They are not part of this roadmap.

| Feature | Why not now |
|---|---|
| Streaming | Adds complexity to every layer. Ship request/response first. |
| Tool use / function calling | Important for agents, but contracts + structured output is the differentiator. Tools come after the core loop is proven. |
| Multi-agent orchestration | Premature. One agent doing tasks well is the foundation. |
| Memory / persistence | Requires understanding usage patterns that don't exist yet. |
| Cost tracking | Nice-to-have. Add after real users ask for it. |
| More providers (Gemini, Mistral, etc.) | Two providers (OpenAI + Anthropic) cover 90% of users. |
| Plugin / hook system | Extensibility before product-market fit is over-engineering. |
| Web UI / playground | The trace JSON is the debugging tool for now. |
| Trials / measurement | Bring back when there are users to measure. |

---

## Execution Order and Dependencies

```
Phase 0 (Strip)
  └─> Phase 1 (Schema Engine)
        ├─> Phase 2 (Diagnostic Retry)  ← depends on schema introspection for rich diagnostics
        │     └─> Phase 3 (Agent Primitive)  ← depends on both schema engine + diagnostic retry
        │           └─> Phase 4 (Pipeline Integration)  ← depends on agent primitive
        └─────────────────────────────────────────────> Phase 5 (Demo & Polish)  ← depends on all above
```

Phase 0 is prerequisite for everything.
Phase 1 is prerequisite for Phase 2 and Phase 3.
Phase 2 is prerequisite for Phase 3.
Phase 3 is prerequisite for Phase 4.
Phase 5 is the final pass after everything works.

---

## Definition of "Showable"

The product is ready to show someone when ALL of these are true:

1. `pnpm add condukt-ai zod` installs cleanly
2. The README quickstart is 5 lines and produces typed, validated output
3. A real example (`examples/real-world.ts`) works with an actual API key
4. When the LLM returns bad output, the framework automatically retries with structured feedback and succeeds
5. The trace JSON tells the full story of what happened, including diagnostic retries
6. Someone can go from "never heard of this" to "this is working" in under 5 minutes
7. The pitch is explainable in one sentence: "Write a schema, get a working agent, debug it with a trace"
