import { type ReactElement, useMemo, useState } from "react";
import Editor from "@monaco-editor/react";

import { getPlaygroundScenarios, runPlaygroundScenario } from "./playground/scenarios";
import type { PlaygroundRunResult } from "./playground/types";

export function Playground(): ReactElement {
  const scenarios = useMemo(() => getPlaygroundScenarios(), []);
  const [selectedId, setSelectedId] = useState<string>(scenarios[0]?.id ?? "");
  const [code, setCode] = useState<string>(scenarios[0]?.template ?? "");
  const [result, setResult] = useState<PlaygroundRunResult | null>(null);

  const selected = scenarios.find((item) => item.id === selectedId);

  function onScenarioChange(id: string): void {
    const scenario = scenarios.find((item) => item.id === id);
    if (!scenario) {
      return;
    }

    setSelectedId(id);
    setCode(scenario.template);
    setResult(null);
  }

  function onRun(): void {
    const runResult = runPlaygroundScenario(selectedId);
    setResult(runResult);
  }

  return (
    <section className="playground-root">
      <div className="playground-header">
        <div>
          <h2>Interactive simulation playground</h2>
          <p>
            Simulation mode: traces are deterministic local fixtures. No API keys, remote requests,
            or backend execution.
          </p>
        </div>
        <span className="playground-badge">Simulation mode</span>
      </div>

      <div className="playground-controls">
        <label htmlFor="scenario">Scenario</label>
        <select id="scenario" value={selectedId} onChange={(event) => onScenarioChange(event.target.value)}>
          {scenarios.map((scenario) => (
            <option key={scenario.id} value={scenario.id}>
              {scenario.name}
            </option>
          ))}
        </select>
        <button type="button" onClick={onRun}>
          Run simulation
        </button>
      </div>

      <p className="playground-description">{selected?.description}</p>

      <div className="playground-editor">
        <Editor
          language="typescript"
          value={code}
          onChange={(value) => setCode(value ?? "")}
          height="360px"
          options={{
            minimap: { enabled: false },
            fontSize: 13,
            scrollBeyondLastLine: false,
            wordWrap: "on",
          }}
          theme="vs-light"
        />
      </div>

      {result ? (
        <div className="playground-output">
          <h3>Diagnosis</h3>
          <ul>
            <li>Failed: {String(result.diagnosis.failed)}</li>
            <li>Task: {result.diagnosis.task ?? "<none>"}</li>
            <li>Error code: {result.diagnosis.error_code ?? "<none>"}</li>
            <li>
              Contract paths: {result.diagnosis.contract_paths.length > 0 ? result.diagnosis.contract_paths.join(", ") : "<none>"}
            </li>
          </ul>

          <h3>Trace output</h3>
          <pre>{JSON.stringify(result.trace, null, 2)}</pre>
        </div>
      ) : null}
    </section>
  );
}
