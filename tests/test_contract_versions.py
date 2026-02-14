from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from missiongraph.spec import AST_VERSION, TRACE_VERSION


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
        ast_golden = json.loads(
            (ROOT / "tests" / "golden" / "ship_release.ast.json").read_text(
                encoding="utf-8"
            )
        )
        trace_golden = json.loads(
            (
                ROOT / "tests" / "golden" / "ship_release.trace.normalized.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(ast_golden["ast_version"], AST_VERSION)
        self.assertEqual(trace_golden["trace_version"], TRACE_VERSION)

    def test_rust_bootstrap_constants_match_runtime_constants(self) -> None:
        lib_rs = (ROOT / "rust" / "missiongraph-rs" / "src" / "lib.rs").read_text(
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
