import { expect, test } from "vitest";

import { z } from "zod";

import {
  ERROR_CODE_CONTRACT_OUTPUT_VIOLATION,
  type LLMJsonRequest,
  type LLMJsonResponse,
  Pipeline,
  type LLMProvider,
  llmTask,
} from "../src/index.js";

type FakeModel = "fake-model";
type FakeModelSettingsByModel = {
  readonly "fake-model": Record<string, never>;
};

class FakeProvider implements LLMProvider<FakeModel, FakeModelSettingsByModel> {
  readonly name = "fake";
  readonly models = ["fake-model"] as const;

  constructor(private readonly responses: Record<string, unknown>) {}

  async generateJSON<TSelectedModel extends FakeModel>(
    request: LLMJsonRequest<TSelectedModel, FakeModelSettingsByModel[TSelectedModel]>,
  ): Promise<LLMJsonResponse<TSelectedModel>> {
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

  expect(trace.status).toBe("ok");
  expect(trace.task_order).toEqual(["research", "draft", "verify"]);
  expect(trace.summary.failed).toBe(0);
  expect(trace.tasks.length).toBe(3);
  expect(trace.tasks[2]?.status).toBe("ok");
  expect(trace.tasks[2]?.output).toEqual({ verified: true, issues: [] });
  expect(trace.tasks[1]?.input?.provider).toBe("fake");
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

  expect(trace.status).toBe("failed");
  expect(trace.tasks.length).toBe(2);
  expect(trace.summary.failed).toBe(1);

  const failedTask = trace.tasks[1];
  expect(failedTask?.task).toBe("draft");
  expect(failedTask?.status).toBe("error");
  expect(failedTask?.error_code).toBe(ERROR_CODE_CONTRACT_OUTPUT_VIOLATION);
  expect(failedTask?.error).toBe("task output contract violation");
  expect(Array.isArray(failedTask?.contract_issues)).toBe(true);
  expect(failedTask?.contract_issues?.[0]?.path).toBe("claims");
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

  await expect(pipeline.run()).rejects.toThrow(/depends on unknown task 'missing_task'/);
});

test("retries execution failures and succeeds on later attempt", async () => {
  let attempts = 0;
  const provider = new FakeProvider({
    recover: { ok: true },
  });

  const pipeline = new Pipeline("retry-success");
  pipeline.addTask(
    llmTask({
      id: "recoverable",
      provider,
      model: "fake-model",
      retry: {
        retries: 2,
        backoffMs: 0,
        retryIf: "execution_error",
      },
      output: z.object({ ok: z.boolean() }),
      prompt: () => {
        attempts += 1;
        if (attempts === 1) {
          throw new Error("transient failure");
        }
        return "recover";
      },
    }),
  );

  const trace = await pipeline.run();
  expect(trace.status).toBe("ok");
  expect(trace.tasks.length).toBe(1);
  expect(trace.tasks[0]?.status).toBe("ok");
  expect(trace.tasks[0]?.attempts?.length).toBe(2);
  expect(trace.tasks[0]?.attempts?.[0]?.status).toBe("error");
  expect(trace.tasks[0]?.attempts?.[1]?.status).toBe("ok");
});
