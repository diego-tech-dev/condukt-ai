export type { StandardSchemaV1 } from "@standard-schema/spec";

export {
  ERROR_CODE_CONTRACT_OUTPUT_VIOLATION,
  ERROR_CODE_TASK_DEPENDENCY_MISSING,
  ERROR_CODE_TASK_EXECUTION_FAILURE,
  Pipeline,
  TRACE_VERSION,
  llmTask,
} from "./pipeline.js";

export type {
  LLMTaskDefinition,
  PipelineTrace,
  TaskDefinition,
  TaskExecutionResult,
  TaskRuntimeContext,
  TaskTrace,
} from "./pipeline.js";

export {
  createAnthropicProvider,
  createOpenAIProvider,
} from "./providers.js";

export type {
  AnthropicProviderOptions,
  LLMJsonRequest,
  LLMJsonResponse,
  LLMProvider,
  OpenAIProviderOptions,
} from "./providers.js";

export { validateContract } from "./contracts.js";
export type { ContractIssue, ContractValidationResult } from "./contracts.js";

export { diagnoseFailure } from "./diagnostics.js";
export type { FailureDiagnosis } from "./diagnostics.js";

export {
  completeTrialSession,
  createTrialSession,
  evaluateTrialSummary,
  summarizeTrialRecords,
} from "./trials.js";
export type {
  CompleteTrialSessionInput,
  CreateTrialSessionInput,
  TrialExpectation,
  TrialMode,
  TrialPair,
  TrialPairSummary,
  TrialQualityGate,
  TrialQualityGateResult,
  TrialModeSummary,
  TrialRecord,
  TrialSession,
  TrialSummary,
} from "./trials.js";
