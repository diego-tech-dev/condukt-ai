#!/usr/bin/env python3
from __future__ import annotations

import json
import sys


def main() -> int:
    payload = json.loads(sys.stdin.read() or "{}")
    artifacts = payload.get("artifacts", {})
    coverage = float(artifacts.get("coverage", 0.0))
    quality_gate = "high" if coverage >= 0.9 else "low"

    result = {
        "status": "ok",
        "confidence": 0.9,
        "output": {
            "release_id": "rel-2026-02",
            "quality_gate": quality_gate,
        },
        "provenance": {
            "source": "simulated-release-publisher",
        },
    }
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
