import { describe, expect, test } from "vitest";

import { getPlaygroundScenarios, runPlaygroundScenario } from "../src/components/playground/scenarios";

describe("playground scenarios", () => {
  test("exposes deterministic scenario catalog", () => {
    const scenarios = getPlaygroundScenarios();
    expect(scenarios.map((scenario) => scenario.id)).toEqual([
      "success",
      "contract-violation",
      "retry-recovery",
      "conditional-skip",
    ]);
  });

  test("returns diagnosis data for failing scenario", () => {
    const result = runPlaygroundScenario("contract-violation");

    expect(result.trace.status).toBe("failed");
    expect(result.diagnosis.failed).toBe(true);
    expect(result.diagnosis.task).toBe("draft");
    expect(result.diagnosis.error_code).toBe("CONTRACT_OUTPUT_VIOLATION");
    expect(result.diagnosis.contract_paths).toEqual(["claims"]);
  });

  test("throws for unknown scenario ids", () => {
    expect(() => runPlaygroundScenario("missing")).toThrow(/unknown scenario/);
  });
});
