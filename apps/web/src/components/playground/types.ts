export interface SimulatedTaskTrace {
  readonly task: string;
  readonly status: "ok" | "error" | "skipped";
  readonly error_code?: string;
  readonly error?: string;
  readonly contract_issues?: readonly {
    readonly path: string;
    readonly message: string;
  }[];
  readonly skip_reason?: string;
}

export interface SimulatedPipelineTrace {
  readonly trace_version: string;
  readonly pipeline: string;
  readonly status: "ok" | "failed";
  readonly execution: {
    readonly mode: "level_parallel";
    readonly levels: readonly (readonly string[])[];
  };
  readonly task_order: readonly string[];
  readonly tasks: readonly SimulatedTaskTrace[];
  readonly summary: {
    readonly total: number;
    readonly passed: number;
    readonly failed: number;
    readonly skipped: number;
  };
}

export interface PlaygroundRunResult {
  readonly scenarioId: string;
  readonly trace: SimulatedPipelineTrace;
  readonly diagnosis: {
    readonly failed: boolean;
    readonly task?: string;
    readonly error_code?: string;
    readonly contract_paths: readonly string[];
  };
}

export interface PlaygroundScenario {
  readonly id: string;
  readonly name: string;
  readonly description: string;
  readonly language: "typescript";
  readonly template: string;
  run(): PlaygroundRunResult;
}
