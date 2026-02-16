import { runPipeline } from "./execution.js";
import { llmTask, type LLMTaskDefinition } from "./llm.js";
import {
  createPipelineRuntimeEnvironment,
  type PipelineRuntimeEnvironment,
  type PipelineRuntimeEnvironmentOverrides,
} from "./runtime.js";
import type {
  DuplicateTaskIdConstraint,
  MergeTaskOutputs,
  PipelineRunResult,
  PipelineTrace,
  TaskDefinition,
  TaskOutputKey,
  TaskOutputMap,
} from "./types.js";

interface PipelineState {
  readonly runtime: PipelineRuntimeEnvironment;
  readonly tasksById: Map<string, TaskDefinition>;
}

export interface PipelineOptions {
  readonly runtime?: PipelineRuntimeEnvironmentOverrides;
}

export class Pipeline<TOutputs extends TaskOutputMap = Record<never, never>> {
  private readonly state: PipelineState;

  constructor(
    public readonly name: string,
    options: PipelineOptions = {},
    state?: PipelineState,
  ) {
    this.state = state ?? {
      runtime: createPipelineRuntimeEnvironment(options.runtime),
      tasksById: new Map(),
    };
  }

  addTask<
    TOutput,
    TDependencies extends readonly TaskOutputKey<TOutputs>[],
    const TTaskId extends string,
  >(
    task: TaskDefinition<TOutput, TOutputs, TDependencies, TTaskId> &
      DuplicateTaskIdConstraint<TOutputs, TTaskId>,
  ): Pipeline<MergeTaskOutputs<TOutputs, TTaskId, TOutput>> {
    return this.addTaskInternal(task);
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
    return this.addTaskInternal(llmTask(definition));
  }

  async runDetailed(): Promise<PipelineRunResult<TOutputs>> {
    return runPipeline<TOutputs>({
      pipelineName: this.name,
      tasksById: this.state.tasksById,
      runtime: this.state.runtime,
    });
  }

  async run(): Promise<PipelineTrace> {
    const result = await this.runDetailed();
    return result.trace;
  }

  private addTaskInternal<
    TOutput,
    TDependencies extends readonly TaskOutputKey<TOutputs>[],
    TTaskId extends string,
  >(
    task: TaskDefinition<TOutput, TOutputs, TDependencies, TTaskId>,
  ): Pipeline<MergeTaskOutputs<TOutputs, TTaskId, TOutput>> {
    if (this.state.tasksById.has(task.id)) {
      throw new Error(`duplicate task id '${task.id}'`);
    }

    this.state.tasksById.set(task.id, task);
    return new Pipeline<MergeTaskOutputs<TOutputs, TTaskId, TOutput>>(this.name, {}, this.state);
  }
}
