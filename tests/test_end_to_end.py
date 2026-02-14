from __future__ import annotations

import copy
import io
import json
import random
import subprocess
import threading
import time
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from condukt.cli import main as cli_main
from condukt.executor import ExecutionError, execute_program
from condukt.parser import ParseError, parse_file, parse_program
from condukt.planner import build_mermaid_graph
from condukt.serialization import program_to_ast
from condukt.spec import (
    ERROR_CODE_ARTIFACT_CONSUME_MISSING,
    ERROR_CODE_ARTIFACT_CONTRACT_CONSUME_VIOLATION,
    ERROR_CODE_ARTIFACT_CONTRACT_OUTPUT_VIOLATION,
    ERROR_CODE_ARTIFACT_OUTPUT_MISSING,
    ERROR_CODE_CONTRACT_INPUT_VIOLATION,
    ERROR_CODE_CONTRACT_OUTPUT_VIOLATION,
    ERROR_CODE_WORKER_EXIT_NONZERO,
    ERROR_CODE_WORKER_TIMEOUT,
)


ROOT = Path(__file__).resolve().parent.parent
GOLDEN_DIR = ROOT / "tests" / "golden"
GOLDEN_CASES = [
    {
        "name": "ship_release",
        "program": ROOT / "examples" / "ship_release.mgl",
        "capabilities": {"ci", "prod_access"},
        "parallel": False,
        "max_parallel": 1,
    },
    {
        "name": "release_artifacts",
        "program": ROOT / "examples" / "release_artifacts.mgl",
        "capabilities": {"ci", "prod_access"},
        "parallel": False,
        "max_parallel": 1,
    },
    {
        "name": "release_fanout",
        "program": ROOT / "examples" / "release_fanout.mgl",
        "capabilities": {"ci", "prod_access"},
        "parallel": True,
        "max_parallel": 3,
    },
    {
        "name": "release_resilient",
        "program": ROOT / "examples" / "release_resilient.mgl",
        "capabilities": {"ci", "prod_access"},
        "parallel": True,
        "max_parallel": 3,
    },
]


class ConduktEndToEndTests(unittest.TestCase):
    def test_demo_program_executes(self) -> None:
        program = parse_file(ROOT / "examples" / "ship_release.mgl")
        trace = execute_program(
            program,
            capabilities={"ci", "prod_access"},
        )
        self.assertEqual(trace["status"], "ok")
        self.assertEqual(trace["task_order"], ["test_suite", "deploy_prod"])
        self.assertTrue(all(item["passed"] for item in trace["verify"]))

    def test_artifact_demo_program_executes(self) -> None:
        program = parse_file(ROOT / "examples" / "release_artifacts.mgl")
        trace = execute_program(
            program,
            capabilities={"ci", "prod_access"},
            parallel=False,
        )
        self.assertEqual(trace["status"], "ok")
        self.assertEqual(trace["task_order"], ["test_suite", "publish_release"])
        self.assertEqual(trace["tasks"][1]["output"]["quality_gate"], "high")

    def test_missing_capability_fails_validation(self) -> None:
        program = parse_file(ROOT / "examples" / "ship_release.mgl")
        with self.assertRaises(ExecutionError):
            execute_program(program, capabilities={"ci"})

    def test_validate_command_json_success(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = cli_main(
                [
                    "validate",
                    str(ROOT / "examples" / "ship_release.mgl"),
                    "--capability",
                    "ci",
                    "--capability",
                    "prod_access",
                    "--json",
                ]
            )
        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertTrue(payload["valid"])
        self.assertEqual(payload["errors"], [])
        self.assertEqual(stderr.getvalue(), "")

    def test_validate_command_json_failure(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = cli_main(
                [
                    "validate",
                    str(ROOT / "examples" / "ship_release.mgl"),
                    "--capability",
                    "ci",
                    "--json",
                ]
            )
        self.assertEqual(exit_code, 1)
        payload = json.loads(stdout.getvalue())
        self.assertFalse(payload["valid"])
        self.assertGreaterEqual(len(payload["errors"]), 1)
        self.assertEqual(stderr.getvalue(), "")

    def test_verify_summary_reports_failed_checks_with_lines(self) -> None:
        program = parse_program(
            f"""
goal "verify diagnostics demo"

plan {{
  task test_suite uses "{(ROOT / 'workers' / 'test_suite.py').as_posix()}" requires capability.ci
}}

verify {{
  test_suite.status == "ok"
  test_suite.output.coverage > 0.99
}}
""".strip()
        )
        trace = execute_program(program, capabilities={"ci"})
        self.assertEqual(trace["status"], "failed")
        summary = trace["verify_summary"]
        self.assertEqual(summary["total"], 2)
        self.assertEqual(summary["passed"], 1)
        self.assertEqual(summary["failed"], 1)
        self.assertEqual(len(summary["failures"]), 1)
        self.assertEqual(summary["failures"][0]["line"], 9)
        self.assertIn("coverage > 0.99", summary["failures"][0]["expression"])

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

        def fake_run_task(task, payload, base_dir, *args, **kwargs):  # type: ignore[no-untyped-def]
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

        with patch("condukt.executor._run_task", side_effect=fake_run_task):
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
        with patch("condukt.executor._run_task", side_effect=fake_run_task):
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
  task deploy_prod uses "{(ROOT / 'workers' / 'deploy_prod.py').as_posix()}" with timeout 250ms retries 2 retry_if timeout backoff 1s jitter 250ms requires capability.prod_access after lint consumes test_report produces release_ticket
  task lint uses "{(ROOT / 'workers' / 'lint.py').as_posix()}" requires capability.ci
}}
""".strip()
        )
        deploy = program.tasks[0]
        lint = program.tasks[1]
        self.assertAlmostEqual(deploy.timeout_seconds or 0.0, 0.25)
        self.assertEqual(deploy.retries, 2)
        self.assertEqual(deploy.retry_if, "timeout")
        self.assertAlmostEqual(deploy.backoff_seconds, 1.0)
        self.assertAlmostEqual(deploy.jitter_seconds, 0.25)
        self.assertEqual(deploy.requires, {"prod_access"})
        self.assertEqual(deploy.after, ["lint"])
        self.assertEqual(deploy.consumes, ["test_report"])
        self.assertEqual(deploy.produces, ["release_ticket"])
        self.assertIsNone(lint.timeout_seconds)
        self.assertEqual(lint.retries, 0)
        self.assertEqual(lint.retry_if, "error")
        self.assertEqual(lint.backoff_seconds, 0.0)
        self.assertEqual(lint.jitter_seconds, 0.0)
        self.assertEqual(lint.consumes, [])
        self.assertEqual(lint.produces, [])

        ast = program_to_ast(program)
        deploy_ast = ast["tasks"][0]
        lint_ast = ast["tasks"][1]
        self.assertAlmostEqual(deploy_ast["timeout_seconds"], 0.25)
        self.assertEqual(deploy_ast["retries"], 2)
        self.assertEqual(deploy_ast["retry_if"], "timeout")
        self.assertAlmostEqual(deploy_ast["backoff_seconds"], 1.0)
        self.assertAlmostEqual(deploy_ast["jitter_seconds"], 0.25)
        self.assertEqual(deploy_ast["consumes"], ["test_report"])
        self.assertEqual(deploy_ast["produces"], ["release_ticket"])
        self.assertNotIn("timeout_seconds", lint_ast)
        self.assertNotIn("retries", lint_ast)
        self.assertNotIn("retry_if", lint_ast)
        self.assertNotIn("backoff_seconds", lint_ast)
        self.assertNotIn("jitter_seconds", lint_ast)
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

        def fake_run_task(task, payload, base_dir, *args, **kwargs):  # type: ignore[no-untyped-def]
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

        with patch("condukt.executor._run_task", side_effect=fake_run_task):
            trace = execute_program(
                program,
                capabilities={"ci", "prod_access"},
                parallel=False,
            )

        self.assertEqual(trace["status"], "ok")

    def test_typed_artifact_contract_is_parsed_and_serialized(self) -> None:
        program = parse_program(
            f"""
goal "typed artifact parse demo"

plan {{
  task lint uses "{(ROOT / 'workers' / 'lint.py').as_posix()}" requires capability.ci produces report:number
  task deploy_prod uses "{(ROOT / 'workers' / 'deploy_prod.py').as_posix()}" requires capability.prod_access after lint consumes report:number
}}
""".strip()
        )
        lint = program.tasks[0]
        deploy = program.tasks[1]
        self.assertEqual(lint.produces, ["report"])
        self.assertEqual(lint.produces_types, {"report": "number"})
        self.assertEqual(deploy.consumes, ["report"])
        self.assertEqual(deploy.consumes_types, {"report": "number"})
        ast = program_to_ast(program)
        self.assertEqual(ast["tasks"][0]["produces_types"]["report"], "number")
        self.assertEqual(ast["tasks"][1]["consumes_types"]["report"], "number")

    def test_unknown_typed_artifact_type_fails_validation(self) -> None:
        program = parse_program(
            f"""
goal "unknown typed artifact"

plan {{
  task lint uses "{(ROOT / 'workers' / 'lint.py').as_posix()}" requires capability.ci produces report:UnknownType
}}
""".strip()
        )
        with self.assertRaises(ExecutionError):
            execute_program(program, capabilities={"ci"})

    def test_incompatible_typed_artifact_contract_fails_validation(self) -> None:
        program = parse_program(
            f"""
goal "typed incompatibility"

plan {{
  task lint uses "{(ROOT / 'workers' / 'lint.py').as_posix()}" requires capability.ci produces report:number
  task deploy_prod uses "{(ROOT / 'workers' / 'deploy_prod.py').as_posix()}" requires capability.prod_access after lint consumes report:str
}}
""".strip()
        )
        with self.assertRaises(ExecutionError):
            execute_program(program, capabilities={"ci", "prod_access"})

    def test_produced_typed_artifact_violation_fails_runtime(self) -> None:
        program = parse_program(
            f"""
goal "produce typed violation"

plan {{
  task test_suite uses "{(ROOT / 'workers' / 'test_suite.py').as_posix()}" requires capability.ci produces coverage:dict
}}
""".strip()
        )
        trace = execute_program(program, capabilities={"ci"})
        self.assertEqual(trace["status"], "failed")
        self.assertEqual(
            trace["tasks"][0]["error_code"],
            ERROR_CODE_ARTIFACT_CONTRACT_OUTPUT_VIOLATION,
        )

    def test_consumed_typed_artifact_violation_fails_runtime(self) -> None:
        program = parse_program(
            f"""
goal "consume typed violation"

plan {{
  task test_suite uses "{(ROOT / 'workers' / 'test_suite.py').as_posix()}" requires capability.ci produces coverage
  task deploy_prod uses "{(ROOT / 'workers' / 'deploy_prod.py').as_posix()}" requires capability.prod_access after test_suite consumes coverage:dict
}}
""".strip()
        )
        trace = execute_program(program, capabilities={"ci", "prod_access"}, parallel=False)
        self.assertEqual(trace["status"], "failed")
        self.assertEqual(
            trace["tasks"][1]["error_code"],
            ERROR_CODE_ARTIFACT_CONTRACT_CONSUME_VIOLATION,
        )

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
        with patch("condukt.executor.validate_program", return_value=[]):
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
            "condukt.executor._run_task_attempt",
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

    def test_retry_if_timeout_skips_non_timeout_errors(self) -> None:
        program = parse_program(
            f"""
goal "retry-if timeout skip"

plan {{
  task test_suite uses "{(ROOT / 'workers' / 'test_suite.py').as_posix()}" with retries 3 retry_if timeout requires capability.ci
}}
""".strip()
        )
        attempts_seen: list[int] = []

        def fake_run_task_attempt(**kwargs):  # type: ignore[no-untyped-def]
            attempt = kwargs["attempt"]
            attempts_seen.append(attempt)
            return {
                "task": "test_suite",
                "worker": program.tasks[0].worker,
                "status": "error",
                "confidence": 0.0,
                "output": {},
                "error_code": ERROR_CODE_WORKER_EXIT_NONZERO,
                "error": "worker exited with return code 1",
                "started_at": "t0",
                "finished_at": "t1",
                "provenance": {},
            }

        with patch(
            "condukt.executor._run_task_attempt",
            side_effect=fake_run_task_attempt,
        ):
            trace = execute_program(program, capabilities={"ci"}, parallel=False)

        self.assertEqual(trace["status"], "failed")
        self.assertEqual(attempts_seen, [1])

    def test_retry_if_timeout_retries_timeouts_only(self) -> None:
        program = parse_program(
            f"""
goal "retry-if timeout only"

plan {{
  task test_suite uses "{(ROOT / 'workers' / 'test_suite.py').as_posix()}" with retries 2 retry_if timeout requires capability.ci
}}
""".strip()
        )
        attempts_seen: list[int] = []

        def fake_run_task_attempt(**kwargs):  # type: ignore[no-untyped-def]
            attempt = kwargs["attempt"]
            attempts_seen.append(attempt)
            if attempt == 1:
                return {
                    "task": "test_suite",
                    "worker": program.tasks[0].worker,
                    "status": "error",
                    "confidence": 0.0,
                    "output": {},
                    "error_code": ERROR_CODE_WORKER_TIMEOUT,
                    "error": "worker timed out",
                    "started_at": "t0",
                    "finished_at": "t1",
                    "provenance": {},
                }
            return {
                "task": "test_suite",
                "worker": program.tasks[0].worker,
                "status": "ok",
                "confidence": 1.0,
                "output": {},
                "error_code": None,
                "error": None,
                "started_at": "t0",
                "finished_at": "t1",
                "provenance": {},
            }

        with patch(
            "condukt.executor._run_task_attempt",
            side_effect=fake_run_task_attempt,
        ):
            trace = execute_program(program, capabilities={"ci"}, parallel=False)

        self.assertEqual(trace["status"], "ok")
        self.assertEqual(attempts_seen, [1, 2])

    def test_retry_jitter_contributes_to_sleep_delay(self) -> None:
        program = parse_program(
            f"""
goal "retry jitter"

plan {{
  task test_suite uses "{(ROOT / 'workers' / 'test_suite.py').as_posix()}" with retries 1 backoff 1s jitter 500ms requires capability.ci
}}
""".strip()
        )

        def fake_run_task_attempt(**kwargs):  # type: ignore[no-untyped-def]
            if kwargs["attempt"] == 1:
                return {
                    "task": "test_suite",
                    "worker": program.tasks[0].worker,
                    "status": "error",
                    "confidence": 0.0,
                    "output": {},
                    "error_code": ERROR_CODE_WORKER_TIMEOUT,
                    "error": "worker timed out",
                    "started_at": "t0",
                    "finished_at": "t1",
                    "provenance": {},
                }
            return {
                "task": "test_suite",
                "worker": program.tasks[0].worker,
                "status": "ok",
                "confidence": 1.0,
                "output": {},
                "error_code": None,
                "error": None,
                "started_at": "t0",
                "finished_at": "t1",
                "provenance": {},
            }

        with patch(
            "condukt.executor._run_task_attempt",
            side_effect=fake_run_task_attempt,
        ), patch("condukt.executor.random.uniform", return_value=0.25), patch(
            "condukt.executor.time.sleep"
        ) as sleep_mock:
            trace = execute_program(program, capabilities={"ci"}, parallel=False)

        self.assertEqual(trace["status"], "ok")
        sleep_mock.assert_called_once_with(1.25)

    def test_retry_seed_makes_jitter_deterministic(self) -> None:
        program = parse_program(
            f"""
goal "retry seed deterministic"

plan {{
  task test_suite uses "{(ROOT / 'workers' / 'test_suite.py').as_posix()}" with retries 1 backoff 1s jitter 500ms requires capability.ci
}}
""".strip()
        )

        def fake_run_task_attempt(**kwargs):  # type: ignore[no-untyped-def]
            if kwargs["attempt"] == 1:
                return {
                    "task": "test_suite",
                    "worker": program.tasks[0].worker,
                    "status": "error",
                    "confidence": 0.0,
                    "output": {},
                    "error_code": ERROR_CODE_WORKER_TIMEOUT,
                    "error": "worker timed out",
                    "started_at": "t0",
                    "finished_at": "t1",
                    "provenance": {},
                }
            return {
                "task": "test_suite",
                "worker": program.tasks[0].worker,
                "status": "ok",
                "confidence": 1.0,
                "output": {},
                "error_code": None,
                "error": None,
                "started_at": "t0",
                "finished_at": "t1",
                "provenance": {},
            }

        with patch(
            "condukt.executor._run_task_attempt",
            side_effect=fake_run_task_attempt,
        ), patch("condukt.executor.time.sleep") as sleep_mock_1:
            trace_1 = execute_program(
                program,
                capabilities={"ci"},
                parallel=False,
                retry_seed=7,
            )
        with patch(
            "condukt.executor._run_task_attempt",
            side_effect=fake_run_task_attempt,
        ), patch("condukt.executor.time.sleep") as sleep_mock_2:
            trace_2 = execute_program(
                program,
                capabilities={"ci"},
                parallel=False,
                retry_seed=7,
            )

        self.assertEqual(trace_1["status"], "ok")
        self.assertEqual(trace_2["status"], "ok")
        delay_1 = sleep_mock_1.call_args_list[0][0][0]
        delay_2 = sleep_mock_2.call_args_list[0][0][0]
        self.assertAlmostEqual(delay_1, delay_2)
        expected_delay = 1.0 + random.Random("7:test_suite").uniform(0.0, 0.5)
        self.assertAlmostEqual(delay_1, expected_delay)

    def test_cli_run_accepts_retry_seed(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = cli_main(
                [
                    "run",
                    str(ROOT / "examples" / "ship_release.mgl"),
                    "--capability",
                    "ci",
                    "--capability",
                    "prod_access",
                    "--sequential",
                    "--retry-seed",
                    "42",
                ]
            )
        self.assertEqual(exit_code, 0)
        trace = json.loads(stdout.getvalue())
        self.assertTrue(all(task["provenance"]["retry_seed"] == 42 for task in trace["tasks"]))
        self.assertEqual(stderr.getvalue(), "")

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
            "condukt.executor.subprocess.run",
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
  task test_suite uses "{(ROOT / 'workers' / 'test_suite.py').as_posix()}" with foobar 1s requires capability.ci
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
        for case in GOLDEN_CASES:
            case_name = case["name"]
            with self.subTest(case=case_name):
                program = parse_file(case["program"])
                actual = program_to_ast(program)
                expected = _read_json(GOLDEN_DIR / f"{case_name}.ast.json")
                self.assertEqual(actual, expected)

    def test_trace_golden_conformance(self) -> None:
        for case in GOLDEN_CASES:
            case_name = case["name"]
            with self.subTest(case=case_name):
                program = parse_file(case["program"])
                trace = execute_program(
                    program,
                    capabilities=case["capabilities"],
                    parallel=case["parallel"],
                    max_parallel=case["max_parallel"],
                )
                actual = _normalize_trace(trace)
                expected = _read_json(
                    GOLDEN_DIR / f"{case_name}.trace.normalized.json"
                )
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
            worker = provenance.get("worker")
            if isinstance(worker, str):
                provenance["worker"] = _normalize_worker_path(worker)
            if "command" in provenance:
                provenance["command"] = "<cmd>"
            if "stdout_sha256" in provenance:
                provenance["stdout_sha256"] = "<sha256>"
            attempts = provenance.get("attempts")
            if isinstance(attempts, list):
                for attempt in attempts:
                    if isinstance(attempt, dict):
                        if "started_at" in attempt:
                            attempt["started_at"] = "<ts>"
                        if "finished_at" in attempt:
                            attempt["finished_at"] = "<ts>"
    return normalized


def _normalize_worker_path(worker_path: str) -> str:
    normalized = worker_path.replace("\\", "/")
    marker = "/workers/"
    marker_index = normalized.rfind(marker)
    if marker_index >= 0:
        return normalized[marker_index + 1 :]
    return Path(normalized).name


if __name__ == "__main__":
    unittest.main()
