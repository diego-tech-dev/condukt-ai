import { appendFile, mkdir, readFile, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";

import type { PipelineTrace } from "../src/pipeline.js";
import {
  completeTrialSession,
  createTrialSession,
  evaluateTrialSummary,
  normalizeTrialMode,
  normalizeTrialRecord,
  renderTrialSummaryMarkdown,
  summarizeTrialRecords,
  type TrialMode,
  type TrialQualityGate,
  type TrialQualityGateResult,
  type TrialRecord,
  type TrialSession,
} from "../src/trials.js";

const DEFAULT_TRIAL_DATA = "trials/diagnosis-metrics.jsonl";
const DEFAULT_SESSION_DIR = "trials/sessions";

async function main(): Promise<void> {
  const [, , command, ...rest] = process.argv;
  const args = parseArgs(rest);

  if (command === "start") {
    await runStart(args);
    return;
  }

  if (command === "finish") {
    await runFinish(args);
    return;
  }

  if (command === "report") {
    await runReport(args);
    return;
  }

  printUsage();
  process.exitCode = 1;
}

async function runStart(args: Map<string, string>): Promise<void> {
  const participant = requiredArg(args, "participant");
  const scenario = requiredArg(args, "scenario");
  const rawMode = requiredArg(args, "mode");
  const mode = normalizeTrialMode(rawMode) as TrialMode;
  if (rawMode === "condukt") {
    console.log("Mode alias 'condukt' is deprecated; normalized to 'condukt-ai'.");
  }

  const tracePath = args.get("trace");
  const trace = tracePath ? await readJson<PipelineTrace>(tracePath) : undefined;

  const session = createTrialSession({
    participant,
    scenario,
    mode,
    trace,
    expected: {
      task: args.get("expected-task"),
      error_code: args.get("expected-error-code"),
      contract_paths: splitList(args.get("expected-contract-paths")),
    },
  });

  const explicitOut = args.get("session-out");
  const outputPath = explicitOut
    ? resolve(process.cwd(), explicitOut)
    : resolve(
        process.cwd(),
        DEFAULT_SESSION_DIR,
        `${session.session_id}.session.json`,
      );
  await mkdir(dirname(outputPath), { recursive: true });
  await writeFile(outputPath, `${JSON.stringify(session, null, 2)}\n`, "utf-8");

  console.log(`Session started: ${session.session_id}`);
  console.log(`Session file: ${outputPath}`);
  console.log(`Expected task: ${session.expected.task ?? "<unspecified>"}`);
  console.log(`Expected error code: ${session.expected.error_code ?? "<unspecified>"}`);
}

async function runFinish(args: Map<string, string>): Promise<void> {
  const sessionPath = requiredArg(args, "session");
  const outputPath = resolve(process.cwd(), args.get("out") ?? DEFAULT_TRIAL_DATA);

  const session = await readJson<TrialSession>(sessionPath);
  const record = completeTrialSession({
    session,
    diagnosed: {
      task: args.get("diagnosed-task"),
      error_code: args.get("diagnosed-error-code"),
    },
    notes: args.get("notes"),
  });

  await mkdir(dirname(outputPath), { recursive: true });
  await appendFile(outputPath, `${JSON.stringify(record)}\n`, "utf-8");

  console.log(`Session finished: ${record.session_id}`);
  console.log(`Elapsed ms: ${record.elapsed_ms}`);
  console.log(`Diagnosis correct: ${record.diagnosis_correct}`);
  console.log(`Metrics file: ${outputPath}`);
}

async function runReport(args: Map<string, string>): Promise<void> {
  const inputPath = resolve(process.cwd(), args.get("input") ?? DEFAULT_TRIAL_DATA);
  const records = await readAndNormalizeTrialRecords(inputPath);
  const summary = summarizeTrialRecords(records);
  const gate = parseTrialQualityGate(args);
  const hasGate = hasGateConfiguration(gate);
  const gateResult = hasGate ? evaluateTrialSummary(summary, gate) : undefined;

  await maybeWriteMarkdownReport(args, summary, gateResult);

  if (args.has("json")) {
    if (hasGate) {
      console.log(
        JSON.stringify(
          {
            summary,
            gate: {
              config: gate,
              result: gateResult ?? { pass: true, failures: [] },
            },
          },
          null,
          2,
        ),
      );
      if (gateResult && !gateResult.pass) {
        process.exitCode = 1;
      }
      return;
    }

    console.log(JSON.stringify(summary, null, 2));
    return;
  }

  console.log(`Records: ${summary.total}`);
  console.log(`Correct: ${summary.correct}`);
  console.log(`Accuracy: ${(summary.accuracy * 100).toFixed(1)}%`);
  console.log(`Median elapsed ms: ${summary.median_elapsed_ms ?? "n/a"}`);
  console.log(`P90 elapsed ms: ${summary.p90_elapsed_ms ?? "n/a"}`);
  console.log(
    `Condukt AI vs baseline speedup (median): ${
      summary.condukt_ai_vs_baseline_speedup
        ? `${summary.condukt_ai_vs_baseline_speedup.toFixed(2)}x`
        : "n/a"
    }`,
  );
  console.log(`Paired samples: ${summary.paired.total_pairs}`);
  console.log(
    `Paired speedup (median): ${
      summary.paired.median_speedup ? `${summary.paired.median_speedup.toFixed(2)}x` : "n/a"
    }`,
  );

  if (hasGate) {
    console.log(`Gate status: ${gateResult?.pass ? "PASS" : "FAIL"}`);
    for (const failure of gateResult?.failures ?? []) {
      console.log(`- ${failure}`);
    }
    if (gateResult && !gateResult.pass) {
      process.exitCode = 1;
    }
  }
}

function parseArgs(args: readonly string[]): Map<string, string> {
  const parsed = new Map<string, string>();
  for (let index = 0; index < args.length; index += 1) {
    const token = args[index];
    if (!token?.startsWith("--")) {
      continue;
    }

    const key = token.slice(2);
    const value = args[index + 1];
    if (!value || value.startsWith("--")) {
      parsed.set(key, "true");
      continue;
    }

    parsed.set(key, value);
    index += 1;
  }
  return parsed;
}

function requiredArg(args: Map<string, string>, key: string): string {
  const value = args.get(key);
  if (!value) {
    throw new Error(`missing --${key}`);
  }
  return value;
}

function parseTrialQualityGate(args: Map<string, string>): TrialQualityGate {
  return {
    min_records: parseOptionalInt(args.get("min-records"), "min-records"),
    min_accuracy: parseOptionalRatio(args.get("min-accuracy"), "min-accuracy"),
    min_pairs: parseOptionalInt(args.get("min-pairs"), "min-pairs"),
    min_paired_speedup: parseOptionalFloat(args.get("min-speedup"), "min-speedup"),
  };
}

function hasGateConfiguration(gate: TrialQualityGate): boolean {
  return (
    typeof gate.min_records === "number" ||
    typeof gate.min_accuracy === "number" ||
    typeof gate.min_pairs === "number" ||
    typeof gate.min_paired_speedup === "number"
  );
}

function parseOptionalInt(value: string | undefined, field: string): number | undefined {
  if (!value) {
    return undefined;
  }
  const parsed = Number.parseInt(value, 10);
  if (!Number.isInteger(parsed) || parsed < 0) {
    throw new Error(`invalid --${field}, expected non-negative integer`);
  }
  return parsed;
}

function parseOptionalFloat(value: string | undefined, field: string): number | undefined {
  if (!value) {
    return undefined;
  }
  const parsed = Number.parseFloat(value);
  if (!Number.isFinite(parsed) || parsed < 0) {
    throw new Error(`invalid --${field}, expected non-negative number`);
  }
  return parsed;
}

function parseOptionalRatio(value: string | undefined, field: string): number | undefined {
  if (!value) {
    return undefined;
  }
  const parsed = Number.parseFloat(value);
  if (!Number.isFinite(parsed) || parsed < 0 || parsed > 1) {
    throw new Error(`invalid --${field}, expected number between 0 and 1`);
  }
  return parsed;
}

function splitList(value: string | undefined): readonly string[] {
  if (!value) {
    return [];
  }

  return value
    .split(",")
    .map((entry) => entry.trim())
    .filter((entry) => entry.length > 0);
}

async function readJson<T>(path: string): Promise<T> {
  const content = await readFile(resolve(process.cwd(), path), "utf-8");
  return JSON.parse(content) as T;
}

async function readJsonLines<T>(path: string): Promise<T[]> {
  const content = await readFile(path, "utf-8");
  return content
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter((line) => line.length > 0)
    .map((line) => JSON.parse(line) as T);
}

async function readAndNormalizeTrialRecords(path: string): Promise<TrialRecord[]> {
  const records = await readJsonLines<unknown>(path);
  return records.map((record, index) => {
    try {
      return normalizeTrialRecord(record);
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      throw new Error(`invalid trial record at line ${index + 1}: ${message}`);
    }
  });
}

async function maybeWriteMarkdownReport(
  args: Map<string, string>,
  summary: ReturnType<typeof summarizeTrialRecords>,
  gateResult: TrialQualityGateResult | undefined,
): Promise<void> {
  const markdownOut = args.get("markdown-out");
  if (!markdownOut) {
    return;
  }

  const maxPairs = parseOptionalInt(args.get("max-pairs"), "max-pairs");
  const title = args.get("title")?.trim();

  let markdown = renderTrialSummaryMarkdown(summary, {
    ...(title ? { title } : {}),
    ...(typeof maxPairs === "number" ? { max_pairs: maxPairs } : {}),
  });

  if (gateResult) {
    markdown += "\n## Gate\n\n";
    markdown += `- Status: ${gateResult.pass ? "PASS" : "FAIL"}\n`;
    if (gateResult.failures.length > 0) {
      markdown += "\n";
      for (const failure of gateResult.failures) {
        markdown += `- ${failure}\n`;
      }
    }
  }

  const outputPath = resolve(process.cwd(), markdownOut);
  await mkdir(dirname(outputPath), { recursive: true });
  await writeFile(outputPath, markdown, "utf-8");
  console.log(`Markdown report: ${outputPath}`);
}

function printUsage(): void {
  console.log(
      "Usage:\n" +
      "  trial-metrics.ts start --participant <id> --scenario <name> --mode <condukt-ai|condukt|baseline> [--trace <trace.json>]\n" +
      "  trial-metrics.ts finish --session <session.json> [--diagnosed-task <id>] [--diagnosed-error-code <code>] [--out <metrics.jsonl>]\n" +
      "  trial-metrics.ts report [--input <metrics.jsonl>] [--json] [--markdown-out <file.md>] [--title <text>] [--max-pairs <int>] [--min-records <int>] [--min-accuracy <0..1>] [--min-pairs <int>] [--min-speedup <number>]",
  );
}

main().catch((error) => {
  console.error(error instanceof Error ? error.message : String(error));
  process.exitCode = 1;
});
