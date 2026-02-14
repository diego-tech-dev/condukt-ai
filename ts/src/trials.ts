import { randomUUID } from "node:crypto";

import { diagnoseFailure } from "./diagnostics.js";
import type { PipelineTrace } from "./pipeline.js";

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

export function normalizeTrialMode(mode: unknown): TrialMode {
  if (mode === "baseline") {
    return "baseline";
  }

  if (mode === "condukt-ai" || mode === "condukt") {
    return "condukt-ai";
  }

  throw new Error("mode must be one of: baseline, condukt-ai, condukt");
}

export function normalizeTrialRecord(value: unknown): TrialRecord {
  const raw = asObject(value, "record");
  const expectedRaw = asObject(raw.expected, "record.expected");
  const diagnosedRaw = asObject(raw.diagnosed, "record.diagnosed");

  const expectedTask = optionalString(expectedRaw.task, "record.expected.task");
  const expectedErrorCode = optionalString(expectedRaw.error_code, "record.expected.error_code");
  const expectedContractPaths = asStringArray(
    expectedRaw.contract_paths,
    "record.expected.contract_paths",
  );

  return {
    session_id: requiredString(raw.session_id, "record.session_id"),
    participant: requiredString(raw.participant, "record.participant"),
    scenario: requiredString(raw.scenario, "record.scenario"),
    mode: normalizeTrialMode(raw.mode),
    started_at: requiredString(raw.started_at, "record.started_at"),
    finished_at: requiredString(raw.finished_at, "record.finished_at"),
    elapsed_ms: nonNegativeNumber(raw.elapsed_ms, "record.elapsed_ms"),
    expected: {
      task: expectedTask,
      error_code: expectedErrorCode,
      contract_paths: expectedContractPaths,
    },
    diagnosed: {
      task: optionalString(diagnosedRaw.task, "record.diagnosed.task"),
      error_code: optionalString(diagnosedRaw.error_code, "record.diagnosed.error_code"),
    },
    matched_task: optionalBooleanOrNull(raw.matched_task, "record.matched_task"),
    matched_error_code: optionalBooleanOrNull(raw.matched_error_code, "record.matched_error_code"),
    diagnosis_correct: requiredBoolean(raw.diagnosis_correct, "record.diagnosis_correct"),
    notes: optionalString(raw.notes, "record.notes"),
  };
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
    "condukt-ai": [],
    baseline: [],
  };

  for (const record of records) {
    byMode[record.mode].push(record);
  }

  const conduktSummary = summarizeMode(byMode["condukt-ai"]);
  const baselineSummary = summarizeMode(byMode.baseline);
  const overall = summarizeMode(records);
  const paired = summarizePairs(records);

  return {
    ...overall,
    by_mode: {
      "condukt-ai": conduktSummary,
      baseline: baselineSummary,
    },
    condukt_ai_vs_baseline_speedup:
      baselineSummary.median_elapsed_ms !== null && conduktSummary.median_elapsed_ms !== null
        ? baselineSummary.median_elapsed_ms / conduktSummary.median_elapsed_ms
        : null,
    paired,
  };
}

export function evaluateTrialSummary(
  summary: TrialSummary,
  gate: TrialQualityGate,
): TrialQualityGateResult {
  const failures: string[] = [];

  if (typeof gate.min_records === "number" && summary.total < gate.min_records) {
    failures.push(`records ${summary.total} < required ${gate.min_records}`);
  }

  if (typeof gate.min_accuracy === "number" && summary.accuracy < gate.min_accuracy) {
    failures.push(
      `accuracy ${(summary.accuracy * 100).toFixed(1)}% < required ${(gate.min_accuracy * 100).toFixed(1)}%`,
    );
  }

  if (typeof gate.min_pairs === "number" && summary.paired.total_pairs < gate.min_pairs) {
    failures.push(`paired samples ${summary.paired.total_pairs} < required ${gate.min_pairs}`);
  }

  if (typeof gate.min_paired_speedup === "number") {
    if (summary.paired.median_speedup === null) {
      failures.push("paired median speedup unavailable");
    } else if (summary.paired.median_speedup < gate.min_paired_speedup) {
      failures.push(
        `paired median speedup ${summary.paired.median_speedup.toFixed(2)}x < required ${gate.min_paired_speedup.toFixed(2)}x`,
      );
    }
  }

  return {
    pass: failures.length === 0,
    failures,
  };
}

export function renderTrialSummaryMarkdown(
  summary: TrialSummary,
  options: TrialSummaryMarkdownOptions = {},
): string {
  const title = options.title ?? "Condukt AI Trial Report";
  const maxPairs = Math.max(1, Math.floor(options.max_pairs ?? 20));
  const visiblePairs = summary.paired.pairs.slice(0, maxPairs);

  const lines: string[] = [
    `# ${title}`,
    "",
    "## Overview",
    "",
    `- Records: ${summary.total}`,
    `- Accuracy: ${formatPercent(summary.accuracy)}`,
    `- Median elapsed: ${formatMilliseconds(summary.median_elapsed_ms)}`,
    `- P90 elapsed: ${formatMilliseconds(summary.p90_elapsed_ms)}`,
    `- Global speedup (mode medians): ${formatSpeedup(summary.condukt_ai_vs_baseline_speedup)}`,
    `- Paired samples: ${summary.paired.total_pairs}`,
    `- Paired median speedup: ${formatSpeedup(summary.paired.median_speedup)}`,
    `- Paired p90 speedup: ${formatSpeedup(summary.paired.p90_speedup)}`,
    "",
    "## By Mode",
    "",
    "| Mode | Records | Accuracy | Median elapsed | P90 elapsed |",
    "| --- | ---: | ---: | ---: | ---: |",
    modeRow("condukt-ai", summary.by_mode["condukt-ai"]),
    modeRow("baseline", summary.by_mode.baseline),
  ];

  if (visiblePairs.length > 0) {
    lines.push(
      "",
      "## Paired Samples",
      "",
      "| Participant | Scenario | Baseline elapsed | Condukt AI elapsed | Speedup |",
      "| --- | --- | ---: | ---: | ---: |",
      ...visiblePairs.map((pair) =>
        `| ${pair.participant} | ${pair.scenario} | ${pair.baseline_elapsed_ms} ms | ${pair.condukt_ai_elapsed_ms} ms | ${pair.speedup.toFixed(2)}x |`
      ),
    );

    if (summary.paired.pairs.length > visiblePairs.length) {
      lines.push(
        "",
        `... ${summary.paired.pairs.length - visiblePairs.length} more pair(s) omitted.`,
      );
    }
  } else {
    lines.push("", "## Paired Samples", "", "_No paired samples available._");
  }

  lines.push("");
  return lines.join("\n");
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
    conduktAi?: TrialRecord;
  }

  const buckets = new Map<string, PairBucket>();
  for (const record of records) {
    const key = `${record.participant}::${record.scenario}`;
    const bucket = buckets.get(key) ?? {};

    if (record.mode === "baseline") {
      bucket.baseline = pickLatestRecord(bucket.baseline, record);
    } else {
      bucket.conduktAi = pickLatestRecord(bucket.conduktAi, record);
    }

    buckets.set(key, bucket);
  }

  const pairs: TrialPair[] = [];
  for (const [key, bucket] of buckets.entries()) {
    if (!bucket.baseline || !bucket.conduktAi) {
      continue;
    }

    if (bucket.conduktAi.elapsed_ms <= 0) {
      continue;
    }

    const [participant, scenario] = splitPairKey(key);
    pairs.push({
      participant,
      scenario,
      baseline_elapsed_ms: bucket.baseline.elapsed_ms,
      condukt_ai_elapsed_ms: bucket.conduktAi.elapsed_ms,
      speedup: bucket.baseline.elapsed_ms / bucket.conduktAi.elapsed_ms,
      baseline_correct: bucket.baseline.diagnosis_correct,
      condukt_ai_correct: bucket.conduktAi.diagnosis_correct,
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

function modeRow(mode: TrialMode, summary: TrialModeSummary): string {
  return `| ${mode} | ${summary.total} | ${formatPercent(summary.accuracy)} | ${formatMilliseconds(summary.median_elapsed_ms)} | ${formatMilliseconds(summary.p90_elapsed_ms)} |`;
}

function formatPercent(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

function formatMilliseconds(value: number | null): string {
  if (value === null) {
    return "n/a";
  }
  return `${value} ms`;
}

function formatSpeedup(value: number | null): string {
  if (value === null) {
    return "n/a";
  }
  return `${value.toFixed(2)}x`;
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

function asObject(value: unknown, field: string): Record<string, unknown> {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new Error(`${field} must be an object`);
  }
  return value as Record<string, unknown>;
}

function requiredString(value: unknown, field: string): string {
  if (typeof value !== "string") {
    throw new Error(`${field} must be a string`);
  }
  return normalizeRequiredString(value, field);
}

function optionalString(value: unknown, field: string): string | undefined {
  if (typeof value === "undefined" || value === null) {
    return undefined;
  }

  if (typeof value !== "string") {
    throw new Error(`${field} must be a string when provided`);
  }

  return normalizeString(value);
}

function asStringArray(value: unknown, field: string): readonly string[] {
  if (!Array.isArray(value)) {
    throw new Error(`${field} must be an array`);
  }

  return value.map((entry, index) => requiredString(entry, `${field}[${index}]`));
}

function requiredBoolean(value: unknown, field: string): boolean {
  if (typeof value !== "boolean") {
    throw new Error(`${field} must be a boolean`);
  }
  return value;
}

function optionalBooleanOrNull(value: unknown, field: string): boolean | null {
  if (value === null || typeof value === "boolean") {
    return value;
  }

  throw new Error(`${field} must be boolean or null`);
}

function nonNegativeNumber(value: unknown, field: string): number {
  if (typeof value !== "number" || !Number.isFinite(value) || value < 0) {
    throw new Error(`${field} must be a non-negative number`);
  }
  return value;
}
