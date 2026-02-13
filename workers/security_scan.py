#!/usr/bin/env python3
from __future__ import annotations

import json
import sys


def main() -> int:
    _payload = json.loads(sys.stdin.read() or "{}")
    result = {
        "status": "ok",
        "confidence": 0.89,
        "output": {
            "critical": 0,
            "high": 0,
            "status": "clear",
        },
        "provenance": {
            "source": "simulated-security-scan",
        },
    }
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
