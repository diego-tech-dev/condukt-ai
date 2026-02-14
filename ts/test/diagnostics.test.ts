import assert from "node:assert/strict";
import test from "node:test";

import { diagnoseFailure, type PipelineTrace } from "../src/index.js";

test("diagnoseFailure returns first failing task boundary", () => {
  const trace: PipelineTrace = {
    trace_version: "ts-0.1",
    pipeline: "research-and-write",
    status: "failed",
    started_at: "2026-02-14T00:00:00.000Z",
    finished_at: "2026-02-14T00:00:02.000Z",
    execution: {
      mode: "sequential",
      levels: [["research"], ["draft"]],
    },
    task_order: ["research", "draft"],
    tasks: [
      {
        task: "research",
        status: "ok",
        started_at: "2026-02-14T00:00:00.000Z",
        finished_at: "2026-02-14T00:00:01.000Z",
        duration_ms: 1000,
        output: { topics: ["a"] },
      },
      {
        task: "draft",
        status: "error",
        started_at: "2026-02-14T00:00:01.000Z",
        finished_at: "2026-02-14T00:00:02.000Z",
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

  const diagnosis = diagnoseFailure(trace);
  assert.equal(diagnosis.failed, true);
  assert.equal(diagnosis.task, "draft");
  assert.equal(diagnosis.error_code, "CONTRACT_OUTPUT_VIOLATION");
  assert.deepEqual(diagnosis.contract_paths, ["claims"]);
});

test("diagnoseFailure handles successful traces", () => {
  const trace: PipelineTrace = {
    trace_version: "ts-0.1",
    pipeline: "research-and-write",
    status: "ok",
    started_at: "2026-02-14T00:00:00.000Z",
    finished_at: "2026-02-14T00:00:01.000Z",
    execution: {
      mode: "sequential",
      levels: [["research"]],
    },
    task_order: ["research"],
    tasks: [
      {
        task: "research",
        status: "ok",
        started_at: "2026-02-14T00:00:00.000Z",
        finished_at: "2026-02-14T00:00:01.000Z",
        duration_ms: 1000,
        output: { topics: ["a"] },
      },
    ],
    summary: {
      total: 1,
      passed: 1,
      failed: 0,
    },
  };

  const diagnosis = diagnoseFailure(trace);
  assert.equal(diagnosis.failed, false);
  assert.equal(diagnosis.task, undefined);
  assert.deepEqual(diagnosis.contract_paths, []);
});
