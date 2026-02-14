import assert from "node:assert/strict";
import test from "node:test";

import {
  completeTrialSession,
  createTrialSession,
  summarizeTrialRecords,
  type PipelineTrace,
} from "../src/index.js";

function buildBrokenTrace(): PipelineTrace {
  return {
    trace_version: "ts-0.1",
    pipeline: "quickstart-research-write",
    status: "failed",
    started_at: "2026-02-14T10:00:00.000Z",
    finished_at: "2026-02-14T10:00:02.000Z",
    execution: {
      mode: "sequential",
      levels: [["research"], ["draft"]],
    },
    task_order: ["research", "draft"],
    tasks: [
      {
        task: "research",
        status: "ok",
        started_at: "2026-02-14T10:00:00.000Z",
        finished_at: "2026-02-14T10:00:01.000Z",
        duration_ms: 1000,
        output: { topics: ["a"], sources: ["b"] },
      },
      {
        task: "draft",
        status: "error",
        started_at: "2026-02-14T10:00:01.000Z",
        finished_at: "2026-02-14T10:00:02.000Z",
        duration_ms: 1000,
        error_code: "CONTRACT_OUTPUT_VIOLATION",
        error: "task output contract violation",
        contract_issues: [{ path: "claims", message: "expected array" }],
      },
    ],
    summary: {
      total: 2,
      passed: 1,
      failed: 1,
    },
  };
}

test("createTrialSession derives expected diagnosis from trace", () => {
  const session = createTrialSession({
    participant: "p1",
    scenario: "quickstart-broken",
    mode: "condukt",
    trace: buildBrokenTrace(),
    sessionId: "session-1",
    startedAt: "2026-02-14T10:00:00.000Z",
  });

  assert.equal(session.session_id, "session-1");
  assert.equal(session.expected.task, "draft");
  assert.equal(session.expected.error_code, "CONTRACT_OUTPUT_VIOLATION");
  assert.deepEqual(session.expected.contract_paths, ["claims"]);
});

test("completeTrialSession marks diagnosis accuracy", () => {
  const session = createTrialSession({
    participant: "p1",
    scenario: "quickstart-broken",
    mode: "condukt",
    trace: buildBrokenTrace(),
    sessionId: "session-1",
    startedAt: "2026-02-14T10:00:00.000Z",
  });

  const record = completeTrialSession({
    session,
    diagnosed: {
      task: "draft",
      error_code: "CONTRACT_OUTPUT_VIOLATION",
    },
    finishedAt: "2026-02-14T10:00:30.000Z",
  });

  assert.equal(record.elapsed_ms, 30_000);
  assert.equal(record.diagnosis_correct, true);
  assert.equal(record.matched_task, true);
  assert.equal(record.matched_error_code, true);
});

test("summarizeTrialRecords computes per-mode aggregates and speedup", () => {
  const records = [
    {
      session_id: "s1",
      participant: "p1",
      scenario: "quickstart-broken",
      mode: "condukt",
      started_at: "2026-02-14T10:00:00.000Z",
      finished_at: "2026-02-14T10:00:20.000Z",
      elapsed_ms: 20_000,
      expected: {
        task: "draft",
        error_code: "CONTRACT_OUTPUT_VIOLATION",
        contract_paths: ["claims"],
      },
      diagnosed: {
        task: "draft",
        error_code: "CONTRACT_OUTPUT_VIOLATION",
      },
      matched_task: true,
      matched_error_code: true,
      diagnosis_correct: true,
    },
    {
      session_id: "s2",
      participant: "p2",
      scenario: "quickstart-broken",
      mode: "baseline",
      started_at: "2026-02-14T10:00:00.000Z",
      finished_at: "2026-02-14T10:01:20.000Z",
      elapsed_ms: 80_000,
      expected: {
        task: "draft",
        error_code: "CONTRACT_OUTPUT_VIOLATION",
        contract_paths: ["claims"],
      },
      diagnosed: {
        task: "draft",
        error_code: "CONTRACT_OUTPUT_VIOLATION",
      },
      matched_task: true,
      matched_error_code: true,
      diagnosis_correct: true,
    },
  ];

  const summary = summarizeTrialRecords(records);
  assert.equal(summary.total, 2);
  assert.equal(summary.by_mode.condukt.total, 1);
  assert.equal(summary.by_mode.baseline.total, 1);
  assert.equal(summary.condukt_vs_baseline_speedup, 4);
});
