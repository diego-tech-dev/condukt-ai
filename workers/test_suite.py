#!/usr/bin/env python3
from __future__ import annotations

import json
import sys


def main() -> int:
    _payload = json.loads(sys.stdin.read() or "{}")
    result = {
        "status": "ok",
        "confidence": 0.93,
        "output": {
            "coverage": 0.94,
            "tests_passed": 128,
        },
        "provenance": {
            "source": "simulated-local-ci",
        },
    }
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
