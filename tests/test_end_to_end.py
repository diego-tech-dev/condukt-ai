from __future__ import annotations

import copy
import json
import subprocess
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from missiongraph.executor import ExecutionError, execute_program
from missiongraph.parser import ParseError, parse_file, parse_program
from missiongraph.planner import build_mermaid_graph
from missiongraph.serialization import program_to_ast
from missiongraph.spec import (
    ERROR_CODE_ARTIFACT_CONSUME_MISSING,
    ERROR_CODE_ARTIFACT_OUTPUT_MISSING,
    ERROR_CODE_CONTRACT_INPUT_VIOLATION,
    ERROR_CODE_CONTRACT_OUTPUT_VIOLATION,
    ERROR_CODE_WORKER_TIMEOUT,
)


ROOT = Path(__file__).resolve().parent.parent
GOLDEN_DIR = ROOT / "tests" / "golden"


class MissionGraphEndToEndTests(unittest.TestCase):
    def test_demo_program_executes(self) -> None:
        program = parse_file(ROOT / "examples" / "ship_release.mgl")
        trace = execute_program(
            program,
            capabilities={"ci", "prod_access"},
        )
        self.assertEqual(trace["status"], "ok")
        self.assertEqual(trace["task_order"], ["test_suite", "deploy_prod"])
        self.assertTrue(all(item["passed"] for item in trace["verify"]))

    def test_missing_capability_fails_validation(self) -> None:
        program = parse_file(ROOT / "examples" / "ship_release.mgl")
        with self.assertRaises(ExecutionError):
            execute_program(program, capabilities={"ci"})

    def test_output_contract_violation_halts_plan(self) -> None:
        program = parse_program(
            f"""
goal "contract failure demo"

plan {{
  task test_suite uses "{(ROOT / 'workers' / 'test_suite.py').as_posix()}" requires capability.ci
  task deploy_prod uses "{(ROOT / 'workers' / 'deploy_prod.py').as_posix()}" requires capability.prod_access after test_suite
}}

contracts {{
  task test_suite output "coverage:str"
}}
""".strip()
        )
        trace = execute_program(
            program,
            capabilities={"ci", "prod_access"},
        )
        self.assertEqual(trace["status"], "failed")
        self.assertEqual(len(trace["tasks"]), 1)
        self.assertIn("output contract violation", trace["tasks"][0]["error"])
        self.assertEqual(
            trace["tasks"][0]["error_code"],
            ERROR_CODE_CONTRACT_OUTPUT_VIOLATION,
        )

    def test_input_contract_violation_blocks_worker_execution(self) -> None:
        program = parse_program(
            f"""
goal "input contract failure demo"

plan {{
  task test_suite uses "{(ROOT / 'workers' / 'test_suite.py').as_posix()}" requires capability.ci
}}

contracts {{
  task test_suite input "variables.release_id:str"
}}
""".strip()
        )
        trace = execute_program(program, capabilities={"ci"})
        self.assertEqual(trace["status"], "failed")
        self.assertEqual(len(trace["tasks"]), 1)
        self.assertIn("input contract violation", trace["tasks"][0]["error"])
        self.assertEqual(
            trace["tasks"][0]["error_code"],
            ERROR_CODE_CONTRACT_INPUT_VIOLATION,
        )
        self.assertTrue(trace["tasks"][0]["provenance"].get("contract_only"))

    def test_type_reference_contract_is_resolved(self) -> None:
        program = parse_program(
            f"""
goal "type ref demo"

types {{
  type WorkerResult "coverage:number, tests_passed:int"
}}

plan {{
  task test_suite uses "{(ROOT / 'workers' / 'test_suite.py').as_posix()}" requires capability.ci
}}

contracts {{
  task test_suite output @WorkerResult
}}
""".strip()
        )
        task = program.tasks[0]
        self.assertEqual(task.output_schema[0].path, "coverage")
        self.assertEqual(task.output_schema[0].expected_type, "number")
        self.assertEqual(task.output_schema[1].path, "tests_passed")
        self.assertEqual(task.output_schema[1].expected_type, "int")

    def test_parallel_execution_runs_same_level_concurrently(self) -> None:
        program = parse_program(
            f"""
goal "parallel demo"

plan {{
  task lint uses "{(ROOT / 'workers' / 'lint.py').as_posix()}" requires capability.ci
  task test_suite uses "{(ROOT / 'workers' / 'test_suite.py').as_posix()}" requires capability.ci
}}
""".strip()
        )

        active = 0
        max_active = 0
        lock = threading.Lock()

        def fake_run_task(task, payload, base_dir):  # type: ignore[no-untyped-def]
            nonlocal active, max_active
            with lock:
                active += 1
                max_active = max(max_active, active)
            time.sleep(0.05)
            with lock:
                active -= 1
            return {
                "task": task.name,
                "worker": task.worker,
                "status": "ok",
                "confidence": 1.0,
                "output": {},
                "error": None,
                "started_at": "t0",
                "finished_at": "t1",
                "provenance": {},
            }

        with patch("missiongraph.executor._run_task", side_effect=fake_run_task):
            trace_parallel = execute_program(
                program,
                capabilities={"ci"},
                parallel=True,
                max_parallel=4,
            )

        self.assertEqual(trace_parallel["status"], "ok")
        self.assertGreaterEqual(max_active, 2)
        self.assertEqual(trace_parallel["execution"]["levels"], [["lint", "test_suite"]])

        active = 0
        max_active = 0
        with patch("missiongraph.executor._run_task", side_effect=fake_run_task):
            trace_sequential = execute_program(
                program,
                capabilities={"ci"},
                parallel=False,
                max_parallel=4,
            )

        self.assertEqual(trace_sequential["status"], "ok")
        self.assertEqual(max_active, 1)
        self.assertEqual(trace_sequential["execution"]["mode"], "sequential")

    def test_task_policy_is_parsed_and_serialized(self) -> None:
        program = parse_program(
            f"""
goal "policy parse demo"

plan {{
  task deploy_prod uses "{(ROOT / 'workers' / 'deploy_prod.py').as_posix()}" with timeout 250ms retries 2 backoff 1s requires capability.prod_access after lint consumes test_report produces release_ticket
  task lint uses "{(ROOT / 'workers' / 'lint.py').as_posix()}" requires capability.ci
}}
""".strip()
        )
        deploy = program.tasks[0]
        lint = program.tasks[1]
        self.assertAlmostEqual(deploy.timeout_seconds or 0.0, 0.25)
        self.assertEqual(deploy.retries, 2)
        self.assertAlmostEqual(deploy.backoff_seconds, 1.0)
        self.assertEqual(deploy.requires, {"prod_access"})
        self.assertEqual(deploy.after, ["lint"])
        self.assertEqual(deploy.consumes, ["test_report"])
        self.assertEqual(deploy.produces, ["release_ticket"])
        self.assertIsNone(lint.timeout_seconds)
        self.assertEqual(lint.retries, 0)
        self.assertEqual(lint.backoff_seconds, 0.0)
        self.assertEqual(lint.consumes, [])
        self.assertEqual(lint.produces, [])

        ast = program_to_ast(program)
        deploy_ast = ast["tasks"][0]
        lint_ast = ast["tasks"][1]
        self.assertAlmostEqual(deploy_ast["timeout_seconds"], 0.25)
        self.assertEqual(deploy_ast["retries"], 2)
        self.assertAlmostEqual(deploy_ast["backoff_seconds"], 1.0)
        self.assertEqual(deploy_ast["consumes"], ["test_report"])
        self.assertEqual(deploy_ast["produces"], ["release_ticket"])
        self.assertNotIn("timeout_seconds", lint_ast)
        self.assertNotIn("retries", lint_ast)
        self.assertNotIn("backoff_seconds", lint_ast)
        self.assertNotIn("consumes", lint_ast)
        self.assertNotIn("produces", lint_ast)

    def test_artifact_consumption_is_passed_to_worker_payload(self) -> None:
        program = parse_program(
            f"""
goal "artifact payload demo"

plan {{
  task test_suite uses "{(ROOT / 'workers' / 'test_suite.py').as_posix()}" requires capability.ci produces test_report
  task deploy_prod uses "{(ROOT / 'workers' / 'deploy_prod.py').as_posix()}" requires capability.prod_access after test_suite consumes test_report
}}
""".strip()
        )

        def fake_run_task(task, payload, base_dir):  # type: ignore[no-untyped-def]
            if task.name == "test_suite":
                return {
                    "task": task.name,
                    "worker": task.worker,
                    "status": "ok",
                    "confidence": 1.0,
                    "output": {"test_report": {"coverage": 0.95}},
                    "error": None,
                    "started_at": "t0",
                    "finished_at": "t1",
                    "provenance": {},
                }
            self.assertIn("artifacts", payload)
            self.assertEqual(payload["artifacts"]["test_report"]["coverage"], 0.95)
            return {
                "task": task.name,
                "worker": task.worker,
                "status": "ok",
                "confidence": 1.0,
                "output": {},
                "error": None,
                "started_at": "t0",
                "finished_at": "t1",
                "provenance": {},
            }

        with patch("missiongraph.executor._run_task", side_effect=fake_run_task):
            trace = execute_program(
                program,
                capabilities={"ci", "prod_access"},
                parallel=False,
            )

        self.assertEqual(trace["status"], "ok")

    def test_missing_consumed_artifact_fails_fast(self) -> None:
        program = parse_program(
            f"""
goal "missing artifact demo"

plan {{
  task test_suite uses "{(ROOT / 'workers' / 'test_suite.py').as_posix()}" requires capability.ci
  task deploy_prod uses "{(ROOT / 'workers' / 'deploy_prod.py').as_posix()}" requires capability.prod_access after test_suite consumes test_report
}}
""".strip()
        )
        with self.assertRaises(ExecutionError):
            execute_program(program, capabilities={"ci", "prod_access"})

    def test_declared_produced_artifact_must_exist_in_output(self) -> None:
        program = parse_program(
            f"""
goal "missing produced artifact demo"

plan {{
  task test_suite uses "{(ROOT / 'workers' / 'test_suite.py').as_posix()}" requires capability.ci produces test_report
}}
""".strip()
        )
        trace = execute_program(program, capabilities={"ci"})
        self.assertEqual(trace["status"], "failed")
        self.assertEqual(trace["tasks"][0]["error_code"], ERROR_CODE_ARTIFACT_OUTPUT_MISSING)

    def test_missing_artifact_error_code_when_runtime_path_not_statically_valid(self) -> None:
        program = parse_program(
            f"""
goal "runtime artifact fail demo"

plan {{
  task build uses "{(ROOT / 'workers' / 'test_suite.py').as_posix()}" requires capability.ci produces coverage
  task deploy uses "{(ROOT / 'workers' / 'deploy_prod.py').as_posix()}" requires capability.prod_access after build consumes release_ticket
}}
""".strip()
        )
        with patch("missiongraph.executor.validate_program", return_value=[]):
            trace = execute_program(
                program,
                capabilities={"ci", "prod_access"},
                parallel=False,
            )
        self.assertEqual(trace["status"], "failed")
        self.assertEqual(trace["tasks"][-1]["error_code"], ERROR_CODE_ARTIFACT_CONSUME_MISSING)

    def test_retry_policy_recovers_from_transient_failure(self) -> None:
        program = parse_program(
            f"""
goal "retry demo"

plan {{
  task test_suite uses "{(ROOT / 'workers' / 'test_suite.py').as_posix()}" with retries 2 backoff 0s requires capability.ci
}}
""".strip()
        )

        attempts_seen: list[int] = []

        def fake_run_task_attempt(**kwargs):  # type: ignore[no-untyped-def]
            attempt = kwargs["attempt"]
            attempts_seen.append(attempt)
            if attempt < 2:
                return {
                    "task": "test_suite",
                    "worker": program.tasks[0].worker,
                    "status": "error",
                    "confidence": 0.0,
                    "output": {},
                    "error_code": "TRANSIENT",
                    "error": "transient failure",
                    "started_at": "t0",
                    "finished_at": "t1",
                    "provenance": {},
                }
            return {
                "task": "test_suite",
                "worker": program.tasks[0].worker,
                "status": "ok",
                "confidence": 1.0,
                "output": {"attempt": attempt},
                "error_code": None,
                "error": None,
                "started_at": "t0",
                "finished_at": "t1",
                "provenance": {},
            }

        with patch(
            "missiongraph.executor._run_task_attempt",
            side_effect=fake_run_task_attempt,
        ):
            trace = execute_program(program, capabilities={"ci"}, parallel=False)

        self.assertEqual(trace["status"], "ok")
        self.assertEqual(attempts_seen, [1, 2])
        self.assertEqual(trace["tasks"][0]["output"]["attempt"], 2)
        attempts = trace["tasks"][0]["provenance"].get("attempts", [])
        self.assertEqual(len(attempts), 2)
        self.assertEqual(attempts[0]["status"], "error")
        self.assertEqual(attempts[1]["status"], "ok")

    def test_timeout_policy_returns_worker_timeout_error(self) -> None:
        program = parse_program(
            f"""
goal "timeout demo"

plan {{
  task test_suite uses "{(ROOT / 'workers' / 'test_suite.py').as_posix()}" with timeout 1ms retries 1 backoff 0s requires capability.ci
}}
""".strip()
        )

        timeout_1 = subprocess.TimeoutExpired(
            cmd=["python3", "worker.py"],
            timeout=0.001,
            output="",
            stderr="timed out",
        )
        timeout_2 = subprocess.TimeoutExpired(
            cmd=["python3", "worker.py"],
            timeout=0.001,
            output="",
            stderr="timed out",
        )
        with patch(
            "missiongraph.executor.subprocess.run",
            side_effect=[timeout_1, timeout_2],
        ):
            trace = execute_program(program, capabilities={"ci"}, parallel=False)

        self.assertEqual(trace["status"], "failed")
        task_result = trace["tasks"][0]
        self.assertEqual(task_result["status"], "error")
        self.assertEqual(task_result["error_code"], ERROR_CODE_WORKER_TIMEOUT)
        self.assertIn("timed out", task_result.get("error", ""))
        self.assertEqual(task_result["provenance"]["max_attempts"], 2)
        self.assertEqual(len(task_result["provenance"]["attempts"]), 2)

    def test_invalid_task_policy_is_rejected(self) -> None:
        with self.assertRaises(ParseError):
            parse_program(
                f"""
goal "invalid policy"

plan {{
  task test_suite uses "{(ROOT / 'workers' / 'test_suite.py').as_posix()}" with jitter 1s requires capability.ci
}}
""".strip()
            )

    def test_backoff_without_retries_fails_validation(self) -> None:
        program = parse_program(
            f"""
goal "invalid backoff"

plan {{
  task test_suite uses "{(ROOT / 'workers' / 'test_suite.py').as_posix()}" with backoff 1s requires capability.ci
}}
""".strip()
        )
        with self.assertRaises(ExecutionError):
            execute_program(program, capabilities={"ci"})

    def test_mermaid_graph_output_contains_expected_edges(self) -> None:
        program = parse_program(
            f"""
goal "graph demo"

plan {{
  task lint uses "{(ROOT / 'workers' / 'lint.py').as_posix()}" requires capability.ci
  task deploy_prod uses "{(ROOT / 'workers' / 'deploy_prod.py').as_posix()}" requires capability.prod_access after lint
}}
""".strip()
        )
        graph = build_mermaid_graph(program.tasks)
        self.assertIn("graph TD", graph)
        self.assertIn("T1", graph)
        self.assertIn("T2", graph)
        self.assertIn("T1 --> T2", graph)

    def test_non_mgl_extension_is_rejected(self) -> None:
        source = (ROOT / "examples" / "ship_release.mgl").read_text(encoding="utf-8")
        temp_path = ROOT / "examples" / "_invalid_extension.apl"
        temp_path.write_text(source, encoding="utf-8")

        try:
            with self.assertRaises(ParseError):
                parse_file(temp_path)
        finally:
            temp_path.unlink(missing_ok=True)

    def test_ast_golden_conformance(self) -> None:
        program = parse_file(ROOT / "examples" / "ship_release.mgl")
        actual = program_to_ast(program)
        expected = _read_json(GOLDEN_DIR / "ship_release.ast.json")
        self.assertEqual(actual, expected)

    def test_trace_golden_conformance(self) -> None:
        program = parse_file(ROOT / "examples" / "ship_release.mgl")
        trace = execute_program(
            program,
            capabilities={"ci", "prod_access"},
            parallel=False,
        )
        actual = _normalize_trace(trace)
        expected = _read_json(GOLDEN_DIR / "ship_release.trace.normalized.json")
        self.assertEqual(actual, expected)


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _normalize_trace(trace: dict) -> dict:
    normalized = copy.deepcopy(trace)
    normalized["started_at"] = "<ts>"
    normalized["finished_at"] = "<ts>"
    for task in normalized.get("tasks", []):
        task["started_at"] = "<ts>"
        task["finished_at"] = "<ts>"
        provenance = task.get("provenance", {})
        if isinstance(provenance, dict):
            if "command" in provenance:
                provenance["command"] = "<cmd>"
            if "stdout_sha256" in provenance:
                provenance["stdout_sha256"] = "<sha256>"
    return normalized


if __name__ == "__main__":
    unittest.main()
