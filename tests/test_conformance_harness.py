from __future__ import annotations

import json
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

from missiongraph.spec import AST_VERSION, TRACE_VERSION


ROOT = Path(__file__).resolve().parent.parent


@unittest.skipUnless(shutil.which("cargo"), "cargo is required for conformance harness")
class ConformanceHarnessTests(unittest.TestCase):
    def test_conformance_script_succeeds_for_ship_release(self) -> None:
        proc = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "conformance.py"),
                "--program",
                "examples/ship_release.mgl",
                "--json",
                "--require-goldens",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr or proc.stdout)
        payload = json.loads(proc.stdout)
        self.assertTrue(payload["ok"])
        self.assertEqual(len(payload["cases"]), 1)
        case = payload["cases"][0]
        self.assertTrue(case["ok"])
        self.assertEqual(case["python_ast_version"], AST_VERSION)
        self.assertTrue(case["rust_check_ok"])
        self.assertEqual(case["rust_ast_version"], AST_VERSION)
        self.assertEqual(case["rust_trace_version"], TRACE_VERSION)
        self.assertEqual(case["rust_execution_mode"], "sequential")
        self.assertEqual(
            case["rust_execution_levels"],
            [["test_suite"], ["deploy_prod"]],
        )
        self.assertTrue(case["golden_ast_match"])
        self.assertTrue(case["golden_trace_contract_match"])


if __name__ == "__main__":
    unittest.main()
