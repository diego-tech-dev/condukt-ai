import type { StandardSchemaV1 } from "@standard-schema/spec";

import { validateContract, type ContractIssue } from "./contracts.js";
import type { LLMProvider } from "./providers.js";

export const TRACE_VERSION = "ts-0.1";

export const ERROR_CODE_CONTRACT_OUTPUT_VIOLATION = "CONTRACT_OUTPUT_VIOLATION";
export const ERROR_CODE_TASK_DEPENDENCY_MISSING = "TASK_DEPENDENCY_MISSING";
export const ERROR_CODE_TASK_EXECUTION_FAILURE = "TASK_EXECUTION_FAILURE";

export interface TaskRetryPolicy {
  readonly retries?: number;
  readonly backoffMs?: number;
  readonly jitterMs?: number;
  readonly retryIf?: "error" | "execution_error" | "contract_violation";
}

type TaskOutputMap = Record<string, unknown>;
type TaskOutputKey<TOutputs extends TaskOutputMap> = Extract<keyof TOutputs, string>;
type MergeTaskOutputs<
  TOutputs extends TaskOutputMap,
  TTaskId extends string,
  TOutput,
> = Omit<TOutputs, TTaskId> & Record<TTaskId, TOutput>;
type DuplicateTaskIdConstraint<
  TOutputs extends TaskOutputMap,
  TTaskId extends string,
> = TTaskId extends TaskOutputKey<TOutputs>
  ? { readonly __duplicate_task_id__: never }
  : Record<never, never>;

export interface TaskRuntimeContext<
  TOutputs extends TaskOutputMap = TaskOutputMap,
  TDependencies extends readonly TaskOutputKey<TOutputs>[] = readonly TaskOutputKey<TOutputs>[],
> {
  readonly outputs: Readonly<TOutputs>;
  readonly taskResults: Readonly<Record<string, TaskTrace>>;
  readonly dependencyOutputs: Readonly<Pick<TOutputs, TDependencies[number]>>;
}

export interface TaskExecutionResult {
  readonly data: unknown;
  readonly input?: unknown;
  readonly rawOutput?: string;
  readonly meta?: Record<string, unknown>;
}

export interface TaskDefinition<
  TOutput = unknown,
  TOutputs extends TaskOutputMap = TaskOutputMap,
  TDependencies extends readonly TaskOutputKey<TOutputs>[] = readonly TaskOutputKey<TOutputs>[],
  TTaskId extends string = string,
> {
  readonly id: TTaskId;
  readonly description?: string;
  readonly after?: TDependencies;
  readonly retry?: TaskRetryPolicy;
  readonly output: StandardSchemaV1<unknown, TOutput>;
  run(context: TaskRuntimeContext<TOutputs, TDependencies>): Promise<TaskExecutionResult>;
}

export interface TaskAttemptTrace {
  readonly attempt: number;
  readonly status: "ok" | "error";
  readonly error_code?: string;
  readonly error?: string;
  readonly started_at: string;
  readonly finished_at: string;
  readonly duration_ms: number;
}

export interface TaskTrace {
  readonly task: string;
  readonly status: "ok" | "error";
  readonly started_at: string;
  readonly finished_at: string;
  readonly duration_ms: number;
  readonly input?: unknown;
  readonly output?: unknown;
  readonly raw_output?: string;
  readonly meta?: Record<string, unknown>;
  readonly error?: string;
  readonly error_code?: string;
  readonly contract_issues?: readonly ContractIssue[];
  readonly attempts?: readonly TaskAttemptTrace[];
}

export interface PipelineTrace {
  readonly trace_version: string;
  readonly pipeline: string;
  readonly status: "ok" | "failed";
  readonly started_at: string;
  readonly finished_at: string;
  readonly execution: {
    readonly mode: "sequential";
    readonly levels: readonly (readonly string[])[];
  };
  readonly task_order: readonly string[];
  readonly tasks: readonly TaskTrace[];
  readonly summary: {
    readonly total: number;
    readonly passed: number;
    readonly failed: number;
  };
}

export interface PipelineRunResult<TOutputs extends TaskOutputMap> {
  readonly trace: PipelineTrace;
  readonly outputs: Readonly<Partial<TOutputs>>;
  readonly taskResults: Readonly<Record<string, TaskTrace>>;
}

type RequiredKeys<TValue extends object> = {
  [TKey in keyof TValue]-?: object extends Pick<TValue, TKey> ? never : TKey;
}[keyof TValue];

type LLMTaskModelSettingsField<TSettings extends object> =
  keyof TSettings extends never
    ? { readonly modelSettings?: undefined }
    : RequiredKeys<TSettings> extends never
      ? { readonly modelSettings?: TSettings }
      : { readonly modelSettings: TSettings };

export type LLMTaskDefinition<
  TOutput = unknown,
  TModel extends string = string,
  TSettingsByModel extends Record<TModel, object> = Record<TModel, Record<string, never>>,
  TSelectedModel extends TModel = TModel,
  TOutputs extends TaskOutputMap = TaskOutputMap,
  TDependencies extends readonly TaskOutputKey<TOutputs>[] = readonly TaskOutputKey<TOutputs>[],
  TTaskId extends string = string,
> = {
  readonly id: TTaskId;
  readonly description?: string;
  readonly after?: TDependencies;
  readonly retry?: TaskRetryPolicy;
  readonly output: StandardSchemaV1<unknown, TOutput>;
  readonly provider: LLMProvider<TModel, TSettingsByModel>;
  readonly model: TSelectedModel;
  readonly prompt: (context: TaskRuntimeContext<TOutputs, TDependencies>) => string | Promise<string>;
  readonly system?:
    | string
    | ((context: TaskRuntimeContext<TOutputs, TDependencies>) => string | Promise<string>);
} & LLMTaskModelSettingsField<TSettingsByModel[TSelectedModel]>;

export function llmTask<
  TOutput,
  TModel extends string,
  TSettingsByModel extends Record<TModel, object>,
  TSelectedModel extends TModel,
  TOutputs extends TaskOutputMap,
  TDependencies extends readonly TaskOutputKey<TOutputs>[],
  TTaskId extends string,
>(
  definition: LLMTaskDefinition<
    TOutput,
    TModel,
    TSettingsByModel,
    TSelectedModel,
    TOutputs,
    TDependencies,
    TTaskId
  >,
): TaskDefinition<TOutput, TOutputs, TDependencies, TTaskId> {
  return {
    id: definition.id,
    description: definition.description,
    after: definition.after,
    retry: definition.retry,
    output: definition.output,
    async run(context) {
      const prompt = await definition.prompt(context);
      const system =
        typeof definition.system === "function"
          ? await definition.system(context)
          : definition.system;

      const response = await definition.provider.generateJSON({
        model: definition.model,
        prompt,
        system,
        settings: definition.modelSettings,
      });

      return {
        data: response.data,
        rawOutput: response.rawText,
        input: {
          provider: definition.provider.name,
          model: definition.model,
          prompt,
          ...(system ? { system } : {}),
          ...(definition.modelSettings ? { model_settings: definition.modelSettings } : {}),
        },
        meta: {
          provider: response.provider,
          model: response.model,
          response_id: response.responseId,
          usage: response.usage,
        },
      };
    },
  };
}

type RuntimeTaskDefinition = TaskDefinition<unknown, TaskOutputMap, readonly string[], string>;

export class Pipeline<TOutputs extends TaskOutputMap = Record<never, never>> {
  private readonly tasksById = new Map<string, RuntimeTaskDefinition>();

  constructor(public readonly name: string) {}

  addTask<
    TOutput,
    TDependencies extends readonly TaskOutputKey<TOutputs>[],
    const TTaskId extends string,
  >(
    task: TaskDefinition<TOutput, TOutputs, TDependencies, TTaskId> &
      DuplicateTaskIdConstraint<TOutputs, TTaskId>,
  ): Pipeline<MergeTaskOutputs<TOutputs, TTaskId, TOutput>> {
    if (this.tasksById.has(task.id)) {
      throw new Error(`duplicate task id '${task.id}'`);
    }
    this.tasksById.set(task.id, task as unknown as RuntimeTaskDefinition);
    return this as unknown as Pipeline<MergeTaskOutputs<TOutputs, TTaskId, TOutput>>;
  }

  addLLMTask<
    TOutput,
    TModel extends string,
    TSettingsByModel extends Record<TModel, object>,
    TSelectedModel extends TModel,
    TDependencies extends readonly TaskOutputKey<TOutputs>[],
    const TTaskId extends string,
  >(
    definition: LLMTaskDefinition<
      TOutput,
      TModel,
      TSettingsByModel,
      TSelectedModel,
      TOutputs,
      TDependencies,
      TTaskId
    > &
      DuplicateTaskIdConstraint<TOutputs, TTaskId>,
  ): Pipeline<MergeTaskOutputs<TOutputs, TTaskId, TOutput>> {
    const task = llmTask(definition) as TaskDefinition<TOutput, TOutputs, TDependencies, TTaskId> &
      DuplicateTaskIdConstraint<TOutputs, TTaskId>;
    return this.addTask(task);
  }

  async runDetailed(): Promise<PipelineRunResult<TOutputs>> {
    const levels = buildDependencyLevels(Array.from(this.tasksById.values()));
    const taskOrder = levels.flat();

    const startedAt = nowIso();
    const outputs: Record<string, unknown> = {};
    const taskResults: Record<string, TaskTrace> = {};
    const taskTrace: TaskTrace[] = [];

    let failed = false;

    for (const level of levels) {
      for (const taskId of level) {
        const task = this.tasksById.get(taskId);
        if (!task) {
          throw new Error(`internal error: task '${taskId}' missing from registry`);
        }

        const dependencyOutputs: Record<string, unknown> = {};
        for (const dependency of task.after ?? []) {
          if (!(dependency in outputs)) {
            const trace = buildTaskErrorTrace({
              task,
              startedAt: nowIso(),
              finishedAt: nowIso(),
              durationMs: 0,
              errorCode: ERROR_CODE_TASK_DEPENDENCY_MISSING,
              error: `dependency output missing: ${dependency}`,
            });
            taskTrace.push(trace);
            taskResults[task.id] = trace;
            failed = true;
            break;
          }
          dependencyOutputs[dependency] = outputs[dependency];
        }

        if (failed) {
          break;
        }

        const trace = await executeTaskWithRetry(task, {
          outputs,
          taskResults,
          dependencyOutputs,
        });

        taskTrace.push(trace);
        taskResults[task.id] = trace;

        if (trace.status === "ok") {
          outputs[task.id] = trace.output;
          continue;
        }

        failed = true;
        break;
      }

      if (failed) {
        break;
      }
    }

    const finishedAt = nowIso();
    const summary = summarize(taskTrace);

    const trace: PipelineTrace = {
      trace_version: TRACE_VERSION,
      pipeline: this.name,
      status: failed ? "failed" : "ok",
      started_at: startedAt,
      finished_at: finishedAt,
      execution: {
        mode: "sequential",
        levels,
      },
      task_order: taskOrder,
      tasks: taskTrace,
      summary,
    };

    return {
      trace,
      outputs: outputs as Partial<TOutputs>,
      taskResults,
    };
  }

  async run(): Promise<PipelineTrace> {
    const result = await this.runDetailed();
    return result.trace;
  }
}

interface NormalizedTaskRetryPolicy {
  readonly retries: number;
  readonly backoffMs: number;
  readonly jitterMs: number;
  readonly retryIf: "error" | "execution_error" | "contract_violation";
}

async function executeTaskWithRetry(task: TaskDefinition, context: TaskRuntimeContext): Promise<TaskTrace> {
  const retryPolicy = normalizeRetryPolicy(task.retry);
  const maxAttempts = retryPolicy.retries + 1;
  const attemptHistory: TaskAttemptTrace[] = [];

  for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
    const taskStartedAt = nowIso();
    const startedMs = Date.now();

    try {
      const result = await task.run(context);
      const validation = await validateContract(task.output, result.data);
      const taskFinishedAt = nowIso();
      const durationMs = Date.now() - startedMs;

      if (!validation.ok) {
        const trace = buildTaskErrorTrace({
          task,
          startedAt: taskStartedAt,
          finishedAt: taskFinishedAt,
          durationMs,
          input: result.input,
          rawOutput: result.rawOutput,
          meta: result.meta,
          errorCode: ERROR_CODE_CONTRACT_OUTPUT_VIOLATION,
          error: "task output contract violation",
          contractIssues: validation.issues,
          attempts: recordAttempt(attemptHistory, {
            attempt,
            status: "error",
            error_code: ERROR_CODE_CONTRACT_OUTPUT_VIOLATION,
            error: "task output contract violation",
            started_at: taskStartedAt,
            finished_at: taskFinishedAt,
            duration_ms: durationMs,
          }),
        });

        if (!shouldRetry(retryPolicy, trace.error_code, attempt, maxAttempts)) {
          return trace;
        }
      } else {
        return {
          task: task.id,
          status: "ok",
          started_at: taskStartedAt,
          finished_at: taskFinishedAt,
          duration_ms: durationMs,
          input: result.input,
          output: validation.value,
          raw_output: result.rawOutput,
          meta: result.meta,
          attempts: maxAttempts > 1
            ? recordAttempt(attemptHistory, {
                attempt,
                status: "ok",
                started_at: taskStartedAt,
                finished_at: taskFinishedAt,
                duration_ms: durationMs,
              })
            : undefined,
        };
      }
    } catch (error) {
      const taskFinishedAt = nowIso();
      const durationMs = Date.now() - startedMs;
      const trace = buildTaskErrorTrace({
        task,
        startedAt: taskStartedAt,
        finishedAt: taskFinishedAt,
        durationMs,
        errorCode: ERROR_CODE_TASK_EXECUTION_FAILURE,
        error: asErrorMessage(error),
        attempts: recordAttempt(attemptHistory, {
          attempt,
          status: "error",
          error_code: ERROR_CODE_TASK_EXECUTION_FAILURE,
          error: asErrorMessage(error),
          started_at: taskStartedAt,
          finished_at: taskFinishedAt,
          duration_ms: durationMs,
        }),
      });
      if (!shouldRetry(retryPolicy, trace.error_code, attempt, maxAttempts)) {
        return trace;
      }
    }

    const delayMs = retryDelayMs(retryPolicy, attempt);
    if (delayMs > 0) {
      await sleepMs(delayMs);
    }
  }

  return buildTaskErrorTrace({
    task,
    startedAt: nowIso(),
    finishedAt: nowIso(),
    durationMs: 0,
    errorCode: ERROR_CODE_TASK_EXECUTION_FAILURE,
    error: "task attempts exhausted",
    attempts: attemptHistory,
  });
}

function normalizeRetryPolicy(policy: TaskRetryPolicy | undefined): NormalizedTaskRetryPolicy {
  return {
    retries: Math.max(0, Math.floor(policy?.retries ?? 0)),
    backoffMs: Math.max(0, policy?.backoffMs ?? 0),
    jitterMs: Math.max(0, policy?.jitterMs ?? 0),
    retryIf: policy?.retryIf ?? "error",
  };
}

function shouldRetry(
  policy: NormalizedTaskRetryPolicy,
  errorCode: string | undefined,
  attempt: number,
  maxAttempts: number,
): boolean {
  if (attempt >= maxAttempts) {
    return false;
  }

  if (policy.retryIf === "error") {
    return true;
  }

  if (policy.retryIf === "contract_violation") {
    return errorCode === ERROR_CODE_CONTRACT_OUTPUT_VIOLATION;
  }

  if (policy.retryIf === "execution_error") {
    return errorCode === ERROR_CODE_TASK_EXECUTION_FAILURE;
  }

  return false;
}

function retryDelayMs(policy: NormalizedTaskRetryPolicy, attempt: number): number {
  const backoff = policy.backoffMs > 0 ? policy.backoffMs * 2 ** (attempt - 1) : 0;
  const jitter = policy.jitterMs > 0 ? Math.random() * policy.jitterMs : 0;
  return Math.max(0, backoff + jitter);
}

function recordAttempt(
  attemptHistory: TaskAttemptTrace[],
  attempt: TaskAttemptTrace,
): readonly TaskAttemptTrace[] {
  attemptHistory.push(attempt);
  return [...attemptHistory];
}

async function sleepMs(delayMs: number): Promise<void> {
  await new Promise((resolve) => {
    setTimeout(resolve, delayMs);
  });
}

interface BuildTaskErrorInput {
  readonly task: TaskDefinition;
  readonly startedAt: string;
  readonly finishedAt: string;
  readonly durationMs: number;
  readonly errorCode: string;
  readonly error: string;
  readonly input?: unknown;
  readonly rawOutput?: string;
  readonly meta?: Record<string, unknown>;
  readonly contractIssues?: readonly ContractIssue[];
  readonly attempts?: readonly TaskAttemptTrace[];
}

function buildTaskErrorTrace(args: BuildTaskErrorInput): TaskTrace {
  return {
    task: args.task.id,
    status: "error",
    started_at: args.startedAt,
    finished_at: args.finishedAt,
    duration_ms: args.durationMs,
    input: args.input,
    raw_output: args.rawOutput,
    meta: args.meta,
    error_code: args.errorCode,
    error: args.error,
    contract_issues: args.contractIssues,
    attempts: args.attempts,
  };
}

function buildDependencyLevels(tasks: readonly TaskDefinition[]): string[][] {
  const byId = new Map<string, TaskDefinition>();
  const order = new Map<string, number>();

  for (let index = 0; index < tasks.length; index += 1) {
    const task = tasks[index];
    if (byId.has(task.id)) {
      throw new Error(`duplicate task id '${task.id}'`);
    }
    byId.set(task.id, task);
    order.set(task.id, index);
  }

  const outgoing = new Map<string, string[]>();
  const inDegree = new Map<string, number>();

  for (const task of tasks) {
    outgoing.set(task.id, []);
    inDegree.set(task.id, 0);
  }

  for (const task of tasks) {
    for (const dependency of task.after ?? []) {
      if (!byId.has(dependency)) {
        throw new Error(`task '${task.id}' depends on unknown task '${dependency}'`);
      }

      outgoing.get(dependency)?.push(task.id);
      inDegree.set(task.id, (inDegree.get(task.id) ?? 0) + 1);
    }
  }

  for (const children of outgoing.values()) {
    children.sort((left, right) => (order.get(left) ?? 0) - (order.get(right) ?? 0));
  }

  let ready = tasks
    .filter((task) => (inDegree.get(task.id) ?? 0) === 0)
    .map((task) => task.id);

  const levels: string[][] = [];
  let seenCount = 0;

  while (ready.length > 0) {
    const current = ready;
    levels.push(current);
    seenCount += current.length;

    const next: string[] = [];
    for (const taskId of current) {
      const children = outgoing.get(taskId) ?? [];
      for (const child of children) {
        const degree = (inDegree.get(child) ?? 0) - 1;
        inDegree.set(child, degree);
        if (degree === 0) {
          next.push(child);
        }
      }
    }

    ready = next;
  }

  if (seenCount !== tasks.length) {
    const unresolved = tasks
      .filter((task) => (inDegree.get(task.id) ?? 0) > 0)
      .map((task) => task.id);
    throw new Error(`cycle detected in pipeline: ${unresolved.join(", ")}`);
  }

  return levels;
}

function summarize(tasks: readonly TaskTrace[]): {
  readonly total: number;
  readonly passed: number;
  readonly failed: number;
} {
  const total = tasks.length;
  const failed = tasks.filter((task) => task.status === "error").length;
  return {
    total,
    passed: total - failed,
    failed,
  };
}

function asErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }
  return String(error);
}

function nowIso(): string {
  return new Date().toISOString();
}
