from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from missiongraph.spec import AST_VERSION


ROOT = Path(__file__).resolve().parent.parent
RUST_MANIFEST = ROOT / "rust" / "missiongraph-rs" / "Cargo.toml"


@unittest.skipUnless(shutil.which("cargo"), "cargo is required for rust CLI tests")
class RustCliTests(unittest.TestCase):
    def _run(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                "cargo",
                "run",
                "--quiet",
                "--manifest-path",
                str(RUST_MANIFEST),
                "--",
                *args,
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_check_ast_json_success(self) -> None:
        ast_path = ROOT / "tests" / "golden" / "ship_release.ast.json"
        proc = self._run("check-ast", str(ast_path), "--json")
        self.assertEqual(proc.returncode, 0, msg=proc.stderr or proc.stdout)

        payload = json.loads(proc.stdout)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["ast_version"], AST_VERSION)
        self.assertEqual(payload["goal"], "ship release")
        self.assertEqual(payload["task_count"], 2)
        self.assertEqual(payload["errors"], [])

    def test_check_ast_json_reports_cycle_error(self) -> None:
        ast_payload = {
            "ast_version": AST_VERSION,
            "goal": "cycle",
            "tasks": [
                {"name": "a", "after": ["b"]},
                {"name": "b", "after": ["a"]},
            ],
        }
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".json",
            encoding="utf-8",
            delete=False,
        ) as handle:
            ast_path = Path(handle.name)
            handle.write(json.dumps(ast_payload))

        try:
            proc = self._run("check-ast", str(ast_path), "--json")
        finally:
            ast_path.unlink(missing_ok=True)

        self.assertNotEqual(proc.returncode, 0)
        payload = json.loads(proc.stdout)
        self.assertFalse(payload["ok"])
        self.assertIn("cycle detected in plan", " ".join(payload["errors"]))

    def test_run_task_executes_dependency_free_worker(self) -> None:
        ast_path = ROOT / "tests" / "golden" / "ship_release.ast.json"
        proc = self._run(
            "run-task",
            str(ast_path),
            "--task",
            "test_suite",
            "--base-dir",
            str(ROOT / "examples"),
            "--json",
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr or proc.stdout)
        payload = json.loads(proc.stdout)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["task"], "test_suite")
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["output"]["tests_passed"], 128)
        self.assertIsNone(payload["error_code"])
        self.assertIsNone(payload["error"])
        self.assertIsNotNone(payload["started_at"])
        self.assertIsNotNone(payload["finished_at"])
        self.assertEqual(payload["provenance"]["return_code"], 0)
        self.assertIn("worker", payload["provenance"])
        self.assertIn("command", payload["provenance"])

    def test_run_task_rejects_tasks_with_dependencies(self) -> None:
        ast_path = ROOT / "tests" / "golden" / "ship_release.ast.json"
        proc = self._run(
            "run-task",
            str(ast_path),
            "--task",
            "deploy_prod",
            "--base-dir",
            str(ROOT / "examples"),
            "--json",
        )
        self.assertNotEqual(proc.returncode, 0)
        payload = json.loads(proc.stdout)
        self.assertFalse(payload["ok"])
        self.assertIn("dependency-free tasks", payload["error"])
        self.assertEqual(payload["error_code"], "RUNTIME_EXECUTION_FAILURE")

    def test_run_task_maps_nonzero_exit_to_error_code(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_root = Path(tmp_dir)
            worker_path = temp_root / "fail_worker.py"
            worker_path.write_text(
                (
                    "import json\n"
                    "print(json.dumps({'status':'ok','confidence':1.0,'output':{}}))\n"
                    "raise SystemExit(1)\n"
                ),
                encoding="utf-8",
            )
            ast_path = temp_root / "fail.ast.json"
            ast_path.write_text(
                json.dumps(
                    {
                        "ast_version": AST_VERSION,
                        "goal": "failing worker",
                        "tasks": [
                            {
                                "name": "fail_task",
                                "worker": str(worker_path),
                                "after": [],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            proc = self._run(
                "run-task",
                str(ast_path),
                "--task",
                "fail_task",
                "--json",
            )

        self.assertNotEqual(proc.returncode, 0)
        payload = json.loads(proc.stdout)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["error_code"], "WORKER_EXIT_NONZERO")
        self.assertEqual(payload["provenance"]["return_code"], 1)

    def test_run_plan_executes_in_dependency_order(self) -> None:
        ast_path = ROOT / "tests" / "golden" / "ship_release.ast.json"
        proc = self._run(
            "run-plan",
            str(ast_path),
            "--base-dir",
            str(ROOT / "examples"),
            "--capability",
            "ci",
            "--capability",
            "prod_access",
            "--json",
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr or proc.stdout)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["execution"]["mode"], "sequential")
        self.assertEqual(payload["execution"]["max_parallel"], 1)
        self.assertEqual(payload["task_order"], ["test_suite", "deploy_prod"])
        self.assertEqual([item["task"] for item in payload["tasks"]], payload["task_order"])
        self.assertEqual(payload["tasks"][1]["output"]["rollback_ready"], True)

    def test_run_plan_stops_on_first_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_root = Path(tmp_dir)
            worker_fail = temp_root / "fail_worker.py"
            worker_should_not_run = temp_root / "should_not_run.py"
            marker = temp_root / "ran.txt"
            worker_fail.write_text(
                (
                    "import json\n"
                    "print(json.dumps({'status':'error','confidence':0.0,'error':'boom','output':{}}))\n"
                    "raise SystemExit(1)\n"
                ),
                encoding="utf-8",
            )
            worker_should_not_run.write_text(
                (
                    "from pathlib import Path\n"
                    "Path(r'" + str(marker) + "').write_text('ran', encoding='utf-8')\n"
                    "print('{\"status\":\"ok\",\"confidence\":1.0,\"output\":{}}')\n"
                ),
                encoding="utf-8",
            )
            ast_path = temp_root / "plan.ast.json"
            ast_path.write_text(
                json.dumps(
                    {
                        "ast_version": AST_VERSION,
                        "goal": "fail fast",
                        "tasks": [
                            {"name": "first", "worker": str(worker_fail), "after": []},
                            {
                                "name": "second",
                                "worker": str(worker_should_not_run),
                                "after": ["first"],
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )
            proc = self._run(
                "run-plan",
                str(ast_path),
                "--json",
            )

        self.assertNotEqual(proc.returncode, 0)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["status"], "failed")
        self.assertEqual(payload["task_order"], ["first", "second"])
        self.assertEqual(len(payload["tasks"]), 1)
        self.assertEqual(payload["tasks"][0]["task"], "first")
        self.assertFalse(marker.exists())

    def test_run_task_retries_and_succeeds(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_root = Path(tmp_dir)
            counter_path = temp_root / "counter.txt"
            worker_path = temp_root / "flaky_worker.py"
            worker_path.write_text(
                (
                    "import json\n"
                    "from pathlib import Path\n"
                    f"counter = Path(r'{counter_path}')\n"
                    "attempt = int(counter.read_text(encoding='utf-8')) if counter.exists() else 0\n"
                    "attempt += 1\n"
                    "counter.write_text(str(attempt), encoding='utf-8')\n"
                    "payload = {'status':'ok','confidence':1.0,'output':{'attempt': attempt}}\n"
                    "print(json.dumps(payload))\n"
                    "raise SystemExit(1 if attempt == 1 else 0)\n"
                ),
                encoding="utf-8",
            )
            ast_path = temp_root / "retry.ast.json"
            ast_path.write_text(
                json.dumps(
                    {
                        "ast_version": AST_VERSION,
                        "goal": "retry success",
                        "tasks": [
                            {
                                "name": "flaky",
                                "worker": str(worker_path),
                                "after": [],
                                "retries": 1,
                                "backoff_seconds": 0.0,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            proc = self._run(
                "run-task",
                str(ast_path),
                "--task",
                "flaky",
                "--json",
            )

        self.assertEqual(proc.returncode, 0, msg=proc.stderr or proc.stdout)
        payload = json.loads(proc.stdout)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["output"]["attempt"], 2)
        self.assertEqual(payload["provenance"]["attempt"], 2)
        self.assertEqual(payload["provenance"]["max_attempts"], 2)
        self.assertEqual(payload["provenance"]["retries"], 1)
        self.assertEqual(len(payload["provenance"]["attempts"]), 2)
        self.assertEqual(payload["provenance"]["attempts"][0]["status"], "error")
        self.assertEqual(payload["provenance"]["attempts"][1]["status"], "ok")

    def test_run_task_retry_if_timeout_retries_timeout_failures(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_root = Path(tmp_dir)
            worker_path = temp_root / "slow_worker.py"
            worker_path.write_text(
                (
                    "import json\n"
                    "import time\n"
                    "time.sleep(0.20)\n"
                    "print(json.dumps({'status':'ok','confidence':1.0,'output':{}}))\n"
                ),
                encoding="utf-8",
            )
            ast_path = temp_root / "timeout_retry.ast.json"
            ast_path.write_text(
                json.dumps(
                    {
                        "ast_version": AST_VERSION,
                        "goal": "timeout retries",
                        "tasks": [
                            {
                                "name": "slow",
                                "worker": str(worker_path),
                                "after": [],
                                "timeout_seconds": 0.05,
                                "retries": 1,
                                "retry_if": "timeout",
                                "backoff_seconds": 0.0,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            proc = self._run(
                "run-task",
                str(ast_path),
                "--task",
                "slow",
                "--json",
            )

        self.assertNotEqual(proc.returncode, 0)
        payload = json.loads(proc.stdout)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["error_code"], "WORKER_TIMEOUT")
        self.assertEqual(payload["provenance"]["attempt"], 2)
        self.assertEqual(len(payload["provenance"]["attempts"]), 2)
        self.assertTrue(payload["error"].startswith("worker timed out after"))

    def test_run_task_retry_if_timeout_does_not_retry_other_failures(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_root = Path(tmp_dir)
            worker_path = temp_root / "fast_fail_worker.py"
            worker_path.write_text(
                (
                    "import json\n"
                    "print(json.dumps({'status':'error','confidence':0.0,'error_code':'WORKER_OUTPUT_JSON_INVALID','error':'bad output','output':{}}))\n"
                    "raise SystemExit(1)\n"
                ),
                encoding="utf-8",
            )
            ast_path = temp_root / "timeout_filter.ast.json"
            ast_path.write_text(
                json.dumps(
                    {
                        "ast_version": AST_VERSION,
                        "goal": "timeout filter",
                        "tasks": [
                            {
                                "name": "fast_fail",
                                "worker": str(worker_path),
                                "after": [],
                                "retries": 2,
                                "retry_if": "timeout",
                                "backoff_seconds": 0.0,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            proc = self._run(
                "run-task",
                str(ast_path),
                "--task",
                "fast_fail",
                "--json",
            )

        self.assertNotEqual(proc.returncode, 0)
        payload = json.loads(proc.stdout)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["error_code"], "WORKER_OUTPUT_JSON_INVALID")
        self.assertEqual(payload["provenance"]["attempt"], 1)
        self.assertEqual(payload["provenance"]["max_attempts"], 3)
        self.assertEqual(len(payload["provenance"]["attempts"]), 1)

    def test_run_plan_honors_retry_policy_before_dependent_task(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_root = Path(tmp_dir)
            counter_path = temp_root / "counter.txt"
            flaky_worker = temp_root / "flaky_worker.py"
            downstream_worker = temp_root / "downstream_worker.py"
            flaky_worker.write_text(
                (
                    "import json\n"
                    "from pathlib import Path\n"
                    f"counter = Path(r'{counter_path}')\n"
                    "attempt = int(counter.read_text(encoding='utf-8')) if counter.exists() else 0\n"
                    "attempt += 1\n"
                    "counter.write_text(str(attempt), encoding='utf-8')\n"
                    "print(json.dumps({'status':'ok','confidence':1.0,'output':{'attempt': attempt}}))\n"
                    "raise SystemExit(1 if attempt == 1 else 0)\n"
                ),
                encoding="utf-8",
            )
            downstream_worker.write_text(
                (
                    "import json\n"
                    "import sys\n"
                    "payload = json.loads(sys.stdin.read() or '{}')\n"
                    "attempt = payload['dependencies']['flaky']['output']['attempt']\n"
                    "print(json.dumps({'status':'ok','confidence':1.0,'output':{'from_first': attempt}}))\n"
                ),
                encoding="utf-8",
            )
            ast_path = temp_root / "plan_retry.ast.json"
            ast_path.write_text(
                json.dumps(
                    {
                        "ast_version": AST_VERSION,
                        "goal": "plan retries",
                        "tasks": [
                            {
                                "name": "flaky",
                                "worker": str(flaky_worker),
                                "after": [],
                                "retries": 1,
                                "backoff_seconds": 0.0,
                            },
                            {
                                "name": "downstream",
                                "worker": str(downstream_worker),
                                "after": ["flaky"],
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )

            proc = self._run(
                "run-plan",
                str(ast_path),
                "--json",
            )

        self.assertEqual(proc.returncode, 0, msg=proc.stderr or proc.stdout)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual([item["task"] for item in payload["tasks"]], ["flaky", "downstream"])
        self.assertEqual(payload["tasks"][0]["provenance"]["attempt"], 2)
        self.assertEqual(len(payload["tasks"][0]["provenance"]["attempts"]), 2)
        self.assertEqual(payload["tasks"][1]["output"]["from_first"], 2)

    def test_run_plan_emits_constraints_and_verify_summary(self) -> None:
        ast_path = ROOT / "tests" / "golden" / "ship_release.ast.json"
        proc = self._run(
            "run-plan",
            str(ast_path),
            "--base-dir",
            str(ROOT / "examples"),
            "--json",
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr or proc.stdout)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(len(payload["constraints"]), 1)
        self.assertTrue(payload["constraints"][0]["passed"])
        self.assertEqual(payload["verify_summary"]["total"], 4)
        self.assertEqual(payload["verify_summary"]["passed"], 4)
        self.assertEqual(payload["verify_summary"]["failed"], 0)
        self.assertEqual(payload["verify_summary"]["failures"], [])

    def test_run_plan_reports_constraint_and_verify_failures(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_root = Path(tmp_dir)
            worker_path = temp_root / "worker.py"
            worker_path.write_text(
                (
                    "import json\n"
                    "print(json.dumps({'status':'ok','confidence':1.0,'output':{'risk':0.5}}))\n"
                ),
                encoding="utf-8",
            )
            ast_path = temp_root / "constraint_verify.ast.json"
            ast_path.write_text(
                json.dumps(
                    {
                        "ast_version": AST_VERSION,
                        "goal": "verify failure",
                        "constraints": [
                            {"key": "risk", "op": "<=", "value": 0.2, "line": 10}
                        ],
                        "verify": [
                            {"line": 20, "expression": "producer.output.risk <= 0.2"},
                            {"line": 21, "expression": "producer.status == \"ok\""},
                        ],
                        "tasks": [
                            {
                                "name": "producer",
                                "worker": str(worker_path),
                                "after": [],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            proc = self._run(
                "run-plan",
                str(ast_path),
                "--json",
            )

        self.assertNotEqual(proc.returncode, 0)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["status"], "failed")
        self.assertFalse(payload["constraints"][0]["passed"])
        self.assertEqual(payload["verify_summary"]["total"], 2)
        self.assertEqual(payload["verify_summary"]["passed"], 1)
        self.assertEqual(payload["verify_summary"]["failed"], 1)
        self.assertEqual(payload["verify_summary"]["failures"][0]["line"], 20)
        self.assertEqual(
            payload["verify_summary"]["failures"][0]["expression"],
            "producer.output.risk <= 0.2",
        )

    def test_run_plan_unresolved_constraint_is_reported_with_null_passed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_root = Path(tmp_dir)
            worker_path = temp_root / "worker.py"
            worker_path.write_text(
                (
                    "import json\n"
                    "print(json.dumps({'status':'ok','confidence':1.0,'output':{}}))\n"
                ),
                encoding="utf-8",
            )
            ast_path = temp_root / "unresolved_constraint.ast.json"
            ast_path.write_text(
                json.dumps(
                    {
                        "ast_version": AST_VERSION,
                        "goal": "unresolved constraint",
                        "constraints": [
                            {"key": "risk", "op": "<=", "value": 0.2, "line": 10}
                        ],
                        "verify": [],
                        "tasks": [
                            {
                                "name": "producer",
                                "worker": str(worker_path),
                                "after": [],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            proc = self._run(
                "run-plan",
                str(ast_path),
                "--json",
            )

        self.assertEqual(proc.returncode, 0, msg=proc.stderr or proc.stdout)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["status"], "ok")
        self.assertIsNone(payload["constraints"][0]["passed"])
        self.assertIn("unresolved key", payload["constraints"][0]["reason"])


if __name__ == "__main__":
    unittest.main()
