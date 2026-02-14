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


if __name__ == "__main__":
    unittest.main()
