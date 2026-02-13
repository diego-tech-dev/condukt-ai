#!/usr/bin/env python3
from __future__ import annotations

import json
import sys


def main() -> int:
    payload = json.loads(sys.stdin.read() or "{}")
    deps = payload.get("dependencies", {})
    required = ["test_suite", "lint", "security_scan"]
    failed_gates: list[str] = []
    for name in required:
        if name not in deps:
            continue
        if deps[name].get("status") != "ok":
            failed_gates.append(name)

    if failed_gates:
        result = {
            "status": "error",
            "confidence": 0.0,
            "error": (
                "cannot deploy because dependency gate(s) failed: "
                + ", ".join(failed_gates)
            ),
            "output": {"rollback_ready": False},
            "provenance": {"source": "simulated-deploy-gate"},
        }
        print(json.dumps(result))
        return 1

    tests = deps.get("test_suite", {})
    coverage = tests.get("output", {}).get("coverage")
    risk = 0.12 if coverage is None else max(0.05, round(1.0 - float(coverage), 2))

    result = {
        "status": "ok",
        "confidence": 0.88,
        "output": {
            "release": "2026.02.0",
            "rollback_ready": True,
            "risk": risk,
        },
        "provenance": {
            "source": "simulated-deploy",
        },
    }
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
