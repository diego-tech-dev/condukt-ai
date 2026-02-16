import type { StandardSchemaV1 } from "@standard-schema/spec";

import type { ContractIssue } from "../contracts.js";

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

export type TaskOutputMap = Record<string, unknown>;
export type TaskOutputKey<TOutputs extends TaskOutputMap> = Extract<keyof TOutputs, string>;

export type MergeTaskOutputs<
  TOutputs extends TaskOutputMap,
  TTaskId extends string,
  TOutput,
> = Omit<TOutputs, TTaskId> & Record<TTaskId, TOutput>;

export type DuplicateTaskIdConstraint<TOutputs extends TaskOutputMap, TTaskId extends string> =
  TTaskId extends TaskOutputKey<TOutputs>
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

export type TaskCondition<
  TOutputs extends TaskOutputMap = TaskOutputMap,
  TDependencies extends readonly TaskOutputKey<TOutputs>[] = readonly TaskOutputKey<TOutputs>[],
> = {
  bivarianceHack(context: TaskRuntimeContext<TOutputs, TDependencies>): boolean | Promise<boolean>;
}["bivarianceHack"];

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
  readonly when?: TaskCondition<TOutputs, TDependencies>;
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
  readonly status: "ok" | "error" | "skipped";
  readonly started_at: string;
  readonly finished_at: string;
  readonly duration_ms: number;
  readonly input?: unknown;
  readonly output?: unknown;
  readonly raw_output?: string;
  readonly meta?: Record<string, unknown>;
  readonly error?: string;
  readonly error_code?: string;
  readonly skip_reason?: string;
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
    readonly mode: "level_parallel";
    readonly levels: readonly (readonly string[])[];
  };
  readonly task_order: readonly string[];
  readonly tasks: readonly TaskTrace[];
  readonly summary: {
    readonly total: number;
    readonly passed: number;
    readonly failed: number;
    readonly skipped: number;
  };
}

export interface PipelineRunResult<TOutputs extends TaskOutputMap> {
  readonly trace: PipelineTrace;
  readonly outputs: Readonly<Partial<TOutputs>>;
  readonly taskResults: Readonly<Record<string, TaskTrace>>;
}
