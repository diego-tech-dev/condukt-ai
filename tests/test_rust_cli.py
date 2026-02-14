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


if __name__ == "__main__":
    unittest.main()
