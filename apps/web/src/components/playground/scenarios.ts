import type {
  PlaygroundRunResult,
  PlaygroundScenario,
  SimulatedPipelineTrace,
} from "./types";

const baseTemplate = `import { Pipeline, createOpenAIProvider } from "condukt-ai";
import { z } from "zod";

const provider = createOpenAIProvider();

const pipeline = new Pipeline("release-workflow");
// Add tasks here
`;

function createResult(scenarioId: string, trace: SimulatedPipelineTrace): PlaygroundRunResult {
  const firstFailure = trace.tasks.find((task) => task.status === "error");

  return {
    scenarioId,
    trace,
    diagnosis: {
      failed: trace.status === "failed",
      task: firstFailure?.task,
      error_code: firstFailure?.error_code,
      contract_paths: (firstFailure?.contract_issues ?? []).map((issue) => issue.path),
    },
  };
}

const scenarios: readonly PlaygroundScenario[] = [
  {
    id: "success",
    name: "Success path",
    description: "All tasks satisfy contracts and the pipeline finishes successfully.",
    language: "typescript",
    template: `${baseTemplate}// Scenario: success path`,
    run: () =>
      createResult("success", {
        trace_version: "ts-0.1",
        pipeline: "release-workflow",
        status: "ok",
        execution: {
          mode: "level_parallel",
          levels: [["research", "draft"], ["verify"]],
        },
        task_order: ["research", "draft", "verify"],
        tasks: [
          { task: "research", status: "ok" },
          { task: "draft", status: "ok" },
          { task: "verify", status: "ok" },
        ],
        summary: {
          total: 3,
          passed: 3,
          failed: 0,
          skipped: 0,
        },
      }),
  },
  {
    id: "contract-violation",
    name: "Contract violation",
    description: "A task returns invalid JSON shape and fails with contract diagnostics.",
    language: "typescript",
    template: `${baseTemplate}// Scenario: contract violation on draft.claims`,
    run: () =>
      createResult("contract-violation", {
        trace_version: "ts-0.1",
        pipeline: "release-workflow",
        status: "failed",
        execution: {
          mode: "level_parallel",
          levels: [["research"], ["draft"]],
        },
        task_order: ["research", "draft"],
        tasks: [
          { task: "research", status: "ok" },
          {
            task: "draft",
            status: "error",
            error_code: "CONTRACT_OUTPUT_VIOLATION",
            error: "task output contract violation",
            contract_issues: [{ path: "claims", message: "expected array" }],
          },
        ],
        summary: {
          total: 2,
          passed: 1,
          failed: 1,
          skipped: 0,
        },
      }),
  },
  {
    id: "retry-recovery",
    name: "Execution retry recovery",
    description: "First attempt fails with execution error, second attempt succeeds.",
    language: "typescript",
    template: `${baseTemplate}// Scenario: execution_error with retry recovery`,
    run: () =>
      createResult("retry-recovery", {
        trace_version: "ts-0.1",
        pipeline: "release-workflow",
        status: "ok",
        execution: {
          mode: "level_parallel",
          levels: [["deploy"]],
        },
        task_order: ["deploy"],
        tasks: [{ task: "deploy", status: "ok" }],
        summary: {
          total: 1,
          passed: 1,
          failed: 0,
          skipped: 0,
        },
      }),
  },
  {
    id: "conditional-skip",
    name: "Conditional skip",
    description: "A gated task is skipped when `when(context)` returns false.",
    language: "typescript",
    template: `${baseTemplate}// Scenario: conditional skip`,
    run: () =>
      createResult("conditional-skip", {
        trace_version: "ts-0.1",
        pipeline: "release-workflow",
        status: "ok",
        execution: {
          mode: "level_parallel",
          levels: [["risk-check"], ["deploy"]],
        },
        task_order: ["risk-check", "deploy"],
        tasks: [
          { task: "risk-check", status: "ok" },
          { task: "deploy", status: "skipped", skip_reason: "condition returned false" },
        ],
        summary: {
          total: 2,
          passed: 1,
          failed: 0,
          skipped: 1,
        },
      }),
  },
];

export function getPlaygroundScenarios(): readonly PlaygroundScenario[] {
  return scenarios;
}

export function runPlaygroundScenario(id: string): PlaygroundRunResult {
  const scenario = scenarios.find((item) => item.id === id);
  if (!scenario) {
    throw new Error(`unknown scenario '${id}'`);
  }

  return structuredClone(scenario.run());
}
