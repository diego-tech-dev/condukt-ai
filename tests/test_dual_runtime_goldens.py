from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Any

from missiongraph.spec import AST_VERSION, TRACE_VERSION


ROOT = Path(__file__).resolve().parent.parent
GOLDEN_DIR = ROOT / "tests" / "golden"
RUST_MANIFEST = ROOT / "rust" / "missiongraph-rs" / "Cargo.toml"
GOLDEN_CASES = ["ship_release", "release_artifacts"]


@unittest.skipUnless(shutil.which("cargo"), "cargo is required for dual-runtime tests")
class DualRuntimeGoldenTests(unittest.TestCase):
    def test_rust_matches_python_golden_contract_surface(self) -> None:
        for case_name in GOLDEN_CASES:
            with self.subTest(case=case_name):
                ast_golden = _read_json(GOLDEN_DIR / f"{case_name}.ast.json")
                trace_golden = _read_json(
                    GOLDEN_DIR / f"{case_name}.trace.normalized.json"
                )
                self.assertEqual(ast_golden["ast_version"], AST_VERSION)
                self.assertEqual(trace_golden["trace_version"], TRACE_VERSION)

                with tempfile.NamedTemporaryFile(
                    mode="w",
                    suffix=".ast.json",
                    encoding="utf-8",
                    delete=False,
                ) as handle:
                    ast_path = Path(handle.name)
                    handle.write(json.dumps(ast_golden))

                try:
                    check_proc = _run_rust("check-ast", str(ast_path), "--json")
                    self.assertEqual(
                        check_proc.returncode, 0, msg=check_proc.stderr or check_proc.stdout
                    )
                    check_payload = json.loads(check_proc.stdout)
                    self.assertTrue(check_payload["ok"])
                    self.assertEqual(check_payload["ast_version"], AST_VERSION)

                    trace_proc = _run_rust("trace-skeleton", str(ast_path))
                    self.assertEqual(
                        trace_proc.returncode, 0, msg=trace_proc.stderr or trace_proc.stdout
                    )
                    rust_trace = json.loads(trace_proc.stdout)
                finally:
                    ast_path.unlink(missing_ok=True)

                self.assertEqual(
                    _trace_contract_projection(rust_trace),
                    _trace_contract_projection(trace_golden),
                )


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _run_rust(*args: str) -> subprocess.CompletedProcess[str]:
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


def _trace_contract_projection(trace: dict[str, Any]) -> dict[str, Any]:
    return {
        "trace_version": trace.get("trace_version"),
        "goal": trace.get("goal"),
        "execution": trace.get("execution"),
        "task_order": trace.get("task_order"),
    }


if __name__ == "__main__":
    unittest.main()
