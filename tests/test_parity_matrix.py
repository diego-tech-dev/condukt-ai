from __future__ import annotations

import json
import shutil
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


@unittest.skipUnless(shutil.which("cargo"), "cargo is required for parity matrix")
class ParityMatrixTests(unittest.TestCase):
    def test_parity_matrix_script_reports_resilient_policy_row(self) -> None:
        proc = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "parity_matrix.py"),
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
        rows = payload["rows"]

        features = {row["feature"] for row in rows}
        self.assertEqual(
            features,
            {
                "core-sequential",
                "artifact-flow",
                "parallel-fanout",
                "resilient-policies",
            },
        )

        resilient = next(row for row in rows if row["feature"] == "resilient-policies")
        self.assertTrue(resilient["ok"])
        self.assertTrue(resilient["golden_ast_match"])
        self.assertTrue(resilient["golden_trace_contract_match"])
        self.assertEqual(resilient["rust_execution_mode"], "parallel")


if __name__ == "__main__":
    unittest.main()
