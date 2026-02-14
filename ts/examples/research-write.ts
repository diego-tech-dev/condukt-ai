import { z } from "zod";

import {
  Pipeline,
  createOpenAIProvider,
  llmTask,
} from "../src/index.js";

async function main(): Promise<void> {
  const provider = createOpenAIProvider();

  const pipeline = new Pipeline("research-and-write");

  pipeline.addTask(
    llmTask({
      id: "research",
      provider,
      model: "gpt-4.1-mini",
      output: z.object({
        topics: z.array(z.string()),
        sources: z.array(z.string()),
      }),
      prompt: () =>
        [
          "Return valid JSON.",
          "Research the topic: reusable launch vehicles.",
          "Output shape: {\"topics\": string[], \"sources\": string[]}",
        ].join("\n"),
    }),
  );

  pipeline.addTask(
    llmTask({
      id: "draft",
      after: ["research"],
      provider,
      model: "gpt-4.1-mini",
      output: z.object({
        article: z.string(),
        claims: z.array(z.string()),
      }),
      prompt: ({ dependencyOutputs }) => {
        const research = dependencyOutputs.research as {
          topics: string[];
          sources: string[];
        };

        return [
          "Return valid JSON.",
          `Write a short article using topics: ${research.topics.join(", ")}`,
          `Use these sources: ${research.sources.join(", ")}`,
          "Output shape: {\"article\": string, \"claims\": string[]}",
        ].join("\n");
      },
    }),
  );

  pipeline.addTask(
    llmTask({
      id: "verify",
      after: ["draft"],
      provider,
      model: "gpt-4.1-mini",
      output: z.object({
        verified: z.boolean(),
        issues: z.array(z.string()),
      }),
      prompt: ({ dependencyOutputs }) => {
        const draft = dependencyOutputs.draft as {
          claims: string[];
        };

        return [
          "Return valid JSON.",
          "Check these claims for factual support and consistency:",
          ...draft.claims.map((claim, index) => `${index + 1}. ${claim}`),
          "Output shape: {\"verified\": boolean, \"issues\": string[]}",
        ].join("\n");
      },
    }),
  );

  const trace = await pipeline.run();
  console.log(JSON.stringify(trace, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
