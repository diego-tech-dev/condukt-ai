import type { PipelineTrace, TaskTrace } from "./pipeline.js";

export interface FailureDiagnosis {
  readonly pipeline: string;
  readonly failed: boolean;
  readonly task?: string;
  readonly task_index?: number;
  readonly error_code?: string;
  readonly error?: string;
  readonly contract_paths: readonly string[];
  readonly failed_at?: string;
}

export function diagnoseFailure(trace: PipelineTrace): FailureDiagnosis {
  const taskIndex = trace.tasks.findIndex((task) => task.status === "error");
  if (taskIndex < 0) {
    return {
      pipeline: trace.pipeline,
      failed: false,
      contract_paths: [],
    };
  }

  const failedTask = trace.tasks[taskIndex] as TaskTrace;
  return {
    pipeline: trace.pipeline,
    failed: true,
    task: failedTask.task,
    task_index: taskIndex,
    error_code: failedTask.error_code,
    error: failedTask.error,
    contract_paths: (failedTask.contract_issues ?? []).map((issue) => issue.path),
    failed_at: failedTask.finished_at,
  };
}
