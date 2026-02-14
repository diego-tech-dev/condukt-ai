from __future__ import annotations

import json
import shutil
import subprocess
import sys
import unittest
from pathlib import Path


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
        self.assertEqual(case["python_ast_version"], "1.0")
        self.assertEqual(case["rust_trace_version"], "1.0")


if __name__ == "__main__":
    unittest.main()
