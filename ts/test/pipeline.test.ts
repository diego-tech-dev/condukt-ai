import assert from "node:assert/strict";
import test from "node:test";

import { z } from "zod";

import {
  ERROR_CODE_CONTRACT_OUTPUT_VIOLATION,
  Pipeline,
  type LLMProvider,
  llmTask,
} from "../src/index.js";

class FakeProvider implements LLMProvider {
  readonly name = "fake";

  constructor(private readonly responses: Record<string, unknown>) {}

  async generateJSON(request: { readonly prompt: string; readonly model: string }): Promise<{
    readonly provider: string;
    readonly model: string;
    readonly rawText: string;
    readonly data: unknown;
  }> {
    const data = this.responses[request.prompt];
    if (typeof data === "undefined") {
      throw new Error(`no fake response for prompt '${request.prompt}'`);
    }

    return {
      provider: this.name,
      model: request.model,
      rawText: JSON.stringify(data),
      data,
    };
  }
}

test("runs an LLM pipeline with typed contracts and trace output", async () => {
  const provider = new FakeProvider({
    "research:space elevators": {
      topics: ["history", "materials"],
      sources: ["nasa", "ieee"],
    },
    "draft from history,materials": {
      article: "Space elevators are hypothetical transport systems.",
      claims: ["Carbon nanotubes are a candidate material."],
    },
    "verify claims count=1": {
      verified: true,
      issues: [],
    },
  });

  const pipeline = new Pipeline("research-and-write");

  pipeline.addTask(
    llmTask({
      id: "research",
      provider,
      model: "fake-model",
      output: z.object({
        topics: z.array(z.string()),
        sources: z.array(z.string()),
      }),
      prompt: () => "research:space elevators",
    }),
  );

  pipeline.addTask(
    llmTask({
      id: "draft",
      after: ["research"],
      provider,
      model: "fake-model",
      output: z.object({
        article: z.string(),
        claims: z.array(z.string()),
      }),
      prompt: ({ dependencyOutputs }) => {
        const research = dependencyOutputs.research as { topics: string[] };
        return `draft from ${research.topics.join(",")}`;
      },
    }),
  );

  pipeline.addTask(
    llmTask({
      id: "verify",
      after: ["draft"],
      provider,
      model: "fake-model",
      output: z.object({
        verified: z.boolean(),
        issues: z.array(z.string()),
      }),
      prompt: ({ dependencyOutputs }) => {
        const draft = dependencyOutputs.draft as { claims: string[] };
        return `verify claims count=${draft.claims.length}`;
      },
    }),
  );

  const trace = await pipeline.run();

  assert.equal(trace.status, "ok");
  assert.deepEqual(trace.task_order, ["research", "draft", "verify"]);
  assert.equal(trace.summary.failed, 0);
  assert.equal(trace.tasks.length, 3);
  assert.equal(trace.tasks[2]?.status, "ok");
  assert.deepEqual(trace.tasks[2]?.output, { verified: true, issues: [] });
  assert.equal(trace.tasks[1]?.input?.provider, "fake");
});

test("fails fast with contract diagnostics when a task returns invalid shape", async () => {
  const provider = new FakeProvider({
    "research": {
      topics: ["a"],
      sources: ["s"],
    },
    "draft": {
      article: "hello",
      claims: "not-a-list",
    },
  });

  const pipeline = new Pipeline("contract-failure");

  pipeline.addTask(
    llmTask({
      id: "research",
      provider,
      model: "fake-model",
      output: z.object({
        topics: z.array(z.string()),
        sources: z.array(z.string()),
      }),
      prompt: () => "research",
    }),
  );

  pipeline.addTask(
    llmTask({
      id: "draft",
      after: ["research"],
      provider,
      model: "fake-model",
      output: z.object({
        article: z.string(),
        claims: z.array(z.string()),
      }),
      prompt: () => "draft",
    }),
  );

  const trace = await pipeline.run();

  assert.equal(trace.status, "failed");
  assert.equal(trace.tasks.length, 2);
  assert.equal(trace.summary.failed, 1);

  const failedTask = trace.tasks[1];
  assert.equal(failedTask?.task, "draft");
  assert.equal(failedTask?.status, "error");
  assert.equal(failedTask?.error_code, ERROR_CODE_CONTRACT_OUTPUT_VIOLATION);
  assert.equal(failedTask?.error, "task output contract violation");
  assert.ok(Array.isArray(failedTask?.contract_issues));
  assert.equal(failedTask?.contract_issues?.[0]?.path, "claims");
});

test("rejects unknown dependencies", async () => {
  const provider = new FakeProvider({
    ok: { value: true },
  });

  const pipeline = new Pipeline("bad-deps");
  pipeline.addTask(
    llmTask({
      id: "only_task",
      after: ["missing_task"],
      provider,
      model: "fake-model",
      output: z.object({ value: z.boolean() }),
      prompt: () => "ok",
    }),
  );

  await assert.rejects(
    async () => pipeline.run(),
    /depends on unknown task 'missing_task'/,
  );
});
