from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from condukt.spec import AST_VERSION, TRACE_VERSION


ROOT = Path(__file__).resolve().parent.parent


class ContractVersionTests(unittest.TestCase):
    def test_schema_const_versions_match_runtime_constants(self) -> None:
        ast_schema = json.loads(
            (ROOT / "spec" / "ast-v1.schema.json").read_text(encoding="utf-8")
        )
        trace_schema = json.loads(
            (ROOT / "spec" / "trace-v1.schema.json").read_text(encoding="utf-8")
        )
        self.assertEqual(ast_schema["properties"]["ast_version"]["const"], AST_VERSION)
        self.assertEqual(
            trace_schema["properties"]["trace_version"]["const"],
            TRACE_VERSION,
        )

    def test_golden_contract_versions_match_runtime_constants(self) -> None:
        golden_dir = ROOT / "tests" / "golden"
        ast_files = sorted(golden_dir.glob("*.ast.json"))
        trace_files = sorted(golden_dir.glob("*.trace.normalized.json"))
        self.assertGreaterEqual(len(ast_files), 1)
        self.assertGreaterEqual(len(trace_files), 1)

        for ast_path in ast_files:
            ast_golden = json.loads(ast_path.read_text(encoding="utf-8"))
            self.assertEqual(ast_golden["ast_version"], AST_VERSION, msg=str(ast_path))

        for trace_path in trace_files:
            trace_golden = json.loads(trace_path.read_text(encoding="utf-8"))
            self.assertEqual(
                trace_golden["trace_version"],
                TRACE_VERSION,
                msg=str(trace_path),
            )

    def test_rust_bootstrap_constants_match_runtime_constants(self) -> None:
        lib_rs = (ROOT / "rust" / "condukt-rs" / "src" / "lib.rs").read_text(
            encoding="utf-8"
        )
        ast_match = re.search(r'pub const AST_VERSION: &str = "([^"]+)";', lib_rs)
        trace_match = re.search(r'pub const TRACE_VERSION: &str = "([^"]+)";', lib_rs)
        self.assertIsNotNone(ast_match)
        self.assertIsNotNone(trace_match)
        self.assertEqual(ast_match.group(1), AST_VERSION)  # type: ignore[union-attr]
        self.assertEqual(trace_match.group(1), TRACE_VERSION)  # type: ignore[union-attr]

    def test_versioning_doc_mentions_current_versions(self) -> None:
        doc = (ROOT / "spec" / "VERSIONING.md").read_text(encoding="utf-8")
        self.assertIn(f"`ast_version`: `{AST_VERSION}`", doc)
        self.assertIn(f"`trace_version`: `{TRACE_VERSION}`", doc)


if __name__ == "__main__":
    unittest.main()
