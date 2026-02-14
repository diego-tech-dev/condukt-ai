import { randomUUID } from "node:crypto";

import { diagnoseFailure } from "./diagnostics.js";
import type { PipelineTrace } from "./pipeline.js";

export type TrialMode = "condukt" | "baseline";

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
  readonly condukt_vs_baseline_speedup: number | null;
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
  readonly condukt_elapsed_ms: number;
  readonly speedup: number;
  readonly baseline_correct: boolean;
  readonly condukt_correct: boolean;
}

export interface TrialPairSummary {
  readonly total_pairs: number;
  readonly median_speedup: number | null;
  readonly p90_speedup: number | null;
  readonly pairs: readonly TrialPair[];
}

export function createTrialSession(input: CreateTrialSessionInput): TrialSession {
  const expectedFromTrace = input.trace ? expectationFromTrace(input.trace) : undefined;
  const expected: TrialExpectation = {
    task: normalizeString(input.expected?.task ?? expectedFromTrace?.task),
    error_code: normalizeString(input.expected?.error_code ?? expectedFromTrace?.error_code),
    contract_paths: normalizeStringArray(
      input.expected?.contract_paths ?? expectedFromTrace?.contract_paths ?? [],
    ),
  };

  if (!expected.task && !expected.error_code) {
    throw new Error("trial expectation must include task or error_code");
  }

  return {
    session_id: input.sessionId ?? randomUUID(),
    participant: normalizeRequiredString(input.participant, "participant"),
    scenario: normalizeRequiredString(input.scenario, "scenario"),
    mode: input.mode,
    started_at: input.startedAt ?? nowIso(),
    expected,
    pipeline: input.trace?.pipeline,
  };
}

export function completeTrialSession(input: CompleteTrialSessionInput): TrialRecord {
  const finishedAt = input.finishedAt ?? nowIso();
  const elapsedMs = Math.max(
    0,
    new Date(finishedAt).getTime() - new Date(input.session.started_at).getTime(),
  );

  const diagnosedTask = normalizeString(input.diagnosed.task);
  const diagnosedErrorCode = normalizeString(input.diagnosed.error_code);
  const matchedTask = matchField(input.session.expected.task, diagnosedTask);
  const matchedErrorCode = matchField(input.session.expected.error_code, diagnosedErrorCode);
  const diagnosisCorrect = [matchedTask, matchedErrorCode].every((value) => value !== false);

  return {
    session_id: input.session.session_id,
    participant: input.session.participant,
    scenario: input.session.scenario,
    mode: input.session.mode,
    started_at: input.session.started_at,
    finished_at: finishedAt,
    elapsed_ms: elapsedMs,
    expected: input.session.expected,
    diagnosed: {
      task: diagnosedTask,
      error_code: diagnosedErrorCode,
    },
    matched_task: matchedTask,
    matched_error_code: matchedErrorCode,
    diagnosis_correct: diagnosisCorrect,
    notes: normalizeString(input.notes),
  };
}

export function summarizeTrialRecords(records: readonly TrialRecord[]): TrialSummary {
  const byMode: Record<TrialMode, TrialRecord[]> = {
    condukt: [],
    baseline: [],
  };

  for (const record of records) {
    byMode[record.mode].push(record);
  }

  const conduktSummary = summarizeMode(byMode.condukt);
  const baselineSummary = summarizeMode(byMode.baseline);
  const overall = summarizeMode(records);
  const paired = summarizePairs(records);

  return {
    ...overall,
    by_mode: {
      condukt: conduktSummary,
      baseline: baselineSummary,
    },
    condukt_vs_baseline_speedup:
      baselineSummary.median_elapsed_ms !== null && conduktSummary.median_elapsed_ms !== null
        ? baselineSummary.median_elapsed_ms / conduktSummary.median_elapsed_ms
        : null,
    paired,
  };
}

function expectationFromTrace(trace: PipelineTrace): TrialExpectation {
  const diagnosis = diagnoseFailure(trace);
  if (!diagnosis.failed) {
    throw new Error("trace has no failure; cannot derive diagnosis expectation");
  }

  return {
    task: diagnosis.task,
    error_code: diagnosis.error_code,
    contract_paths: diagnosis.contract_paths,
  };
}

function summarizeMode(records: readonly TrialRecord[]): TrialModeSummary {
  if (records.length === 0) {
    return {
      total: 0,
      correct: 0,
      accuracy: 0,
      median_elapsed_ms: null,
      p90_elapsed_ms: null,
    };
  }

  const correct = records.filter((record) => record.diagnosis_correct).length;
  const elapsed = records.map((record) => record.elapsed_ms).sort((left, right) => left - right);

  return {
    total: records.length,
    correct,
    accuracy: correct / records.length,
    median_elapsed_ms: quantile(elapsed, 0.5),
    p90_elapsed_ms: quantile(elapsed, 0.9),
  };
}

function summarizePairs(records: readonly TrialRecord[]): TrialPairSummary {
  const pairs = buildPairs(records);
  const speedups = pairs.map((pair) => pair.speedup).sort((left, right) => left - right);

  return {
    total_pairs: pairs.length,
    median_speedup: quantile(speedups, 0.5),
    p90_speedup: quantile(speedups, 0.9),
    pairs,
  };
}

function buildPairs(records: readonly TrialRecord[]): TrialPair[] {
  interface PairBucket {
    baseline?: TrialRecord;
    condukt?: TrialRecord;
  }

  const buckets = new Map<string, PairBucket>();
  for (const record of records) {
    const key = `${record.participant}::${record.scenario}`;
    const bucket = buckets.get(key) ?? {};

    if (record.mode === "baseline") {
      bucket.baseline = pickLatestRecord(bucket.baseline, record);
    } else {
      bucket.condukt = pickLatestRecord(bucket.condukt, record);
    }

    buckets.set(key, bucket);
  }

  const pairs: TrialPair[] = [];
  for (const [key, bucket] of buckets.entries()) {
    if (!bucket.baseline || !bucket.condukt) {
      continue;
    }

    if (bucket.condukt.elapsed_ms <= 0) {
      continue;
    }

    const [participant, scenario] = splitPairKey(key);
    pairs.push({
      participant,
      scenario,
      baseline_elapsed_ms: bucket.baseline.elapsed_ms,
      condukt_elapsed_ms: bucket.condukt.elapsed_ms,
      speedup: bucket.baseline.elapsed_ms / bucket.condukt.elapsed_ms,
      baseline_correct: bucket.baseline.diagnosis_correct,
      condukt_correct: bucket.condukt.diagnosis_correct,
    });
  }

  return pairs.sort((left, right) => {
    if (left.participant !== right.participant) {
      return left.participant.localeCompare(right.participant);
    }
    return left.scenario.localeCompare(right.scenario);
  });
}

function pickLatestRecord(current: TrialRecord | undefined, next: TrialRecord): TrialRecord {
  if (!current) {
    return next;
  }

  const currentMs = new Date(current.finished_at).getTime();
  const nextMs = new Date(next.finished_at).getTime();
  return nextMs >= currentMs ? next : current;
}

function splitPairKey(key: string): [string, string] {
  const separator = key.indexOf("::");
  if (separator < 0) {
    return [key, ""];
  }

  return [key.slice(0, separator), key.slice(separator + 2)];
}

function quantile(sortedValues: readonly number[], q: number): number | null {
  if (sortedValues.length === 0) {
    return null;
  }

  const index = Math.ceil(q * sortedValues.length) - 1;
  const clamped = Math.min(sortedValues.length - 1, Math.max(0, index));
  return sortedValues[clamped] ?? null;
}

function normalizeRequiredString(value: string, field: string): string {
  const normalized = normalizeString(value);
  if (!normalized) {
    throw new Error(`${field} is required`);
  }
  return normalized;
}

function normalizeString(value: string | undefined): string | undefined {
  if (!value) {
    return undefined;
  }

  const normalized = value.trim();
  return normalized.length > 0 ? normalized : undefined;
}

function normalizeStringArray(values: readonly string[]): readonly string[] {
  return values
    .map((value) => value.trim())
    .filter((value) => value.length > 0);
}

function matchField(expected: string | undefined, actual: string | undefined): boolean | null {
  if (!expected) {
    return null;
  }

  return expected === actual;
}

function nowIso(): string {
  return new Date().toISOString();
}
