import type { PipelineTrace } from "../pipeline.js";

export type TrialMode = "condukt-ai" | "baseline";

export interface TrialExpectation {
  readonly task?: string;
  readonly error_code?: string;
  readonly contract_paths: readonly string[];
}

export interface TrialSession {
  readonly session_id: string;
  readonly participant: string;
  readonly scenario: string;
  readonly mode: TrialMode;
  readonly started_at: string;
  readonly expected: TrialExpectation;
  readonly pipeline?: string;
}

export interface TrialRecord {
  readonly session_id: string;
  readonly participant: string;
  readonly scenario: string;
  readonly mode: TrialMode;
  readonly started_at: string;
  readonly finished_at: string;
  readonly elapsed_ms: number;
  readonly expected: TrialExpectation;
  readonly diagnosed: {
    readonly task?: string;
    readonly error_code?: string;
  };
  readonly matched_task: boolean | null;
  readonly matched_error_code: boolean | null;
  readonly diagnosis_correct: boolean;
  readonly notes?: string;
}

export interface CreateTrialSessionInput {
  readonly participant: string;
  readonly scenario: string;
  readonly mode: TrialMode;
  readonly trace?: PipelineTrace;
  readonly expected?: {
    readonly task?: string;
    readonly error_code?: string;
    readonly contract_paths?: readonly string[];
  };
  readonly sessionId?: string;
  readonly startedAt?: string;
}

export interface CompleteTrialSessionInput {
  readonly session: TrialSession;
  readonly diagnosed: {
    readonly task?: string;
    readonly error_code?: string;
  };
  readonly notes?: string;
  readonly finishedAt?: string;
}

export interface TrialSummary {
  readonly total: number;
  readonly correct: number;
  readonly accuracy: number;
  readonly median_elapsed_ms: number | null;
  readonly p90_elapsed_ms: number | null;
  readonly by_mode: Record<TrialMode, TrialModeSummary>;
  readonly condukt_ai_vs_baseline_speedup: number | null;
  readonly paired: TrialPairSummary;
}

export interface TrialModeSummary {
  readonly total: number;
  readonly correct: number;
  readonly accuracy: number;
  readonly median_elapsed_ms: number | null;
  readonly p90_elapsed_ms: number | null;
}

export interface TrialPair {
  readonly participant: string;
  readonly scenario: string;
  readonly baseline_elapsed_ms: number;
  readonly condukt_ai_elapsed_ms: number;
  readonly speedup: number;
  readonly baseline_correct: boolean;
  readonly condukt_ai_correct: boolean;
}

export interface TrialPairSummary {
  readonly total_pairs: number;
  readonly median_speedup: number | null;
  readonly p90_speedup: number | null;
  readonly pairs: readonly TrialPair[];
}

export interface TrialQualityGate {
  readonly min_records?: number;
  readonly min_accuracy?: number;
  readonly min_pairs?: number;
  readonly min_paired_speedup?: number;
}

export interface TrialQualityGateResult {
  readonly pass: boolean;
  readonly failures: readonly string[];
}

export interface TrialSummaryMarkdownOptions {
  readonly title?: string;
  readonly max_pairs?: number;
}
