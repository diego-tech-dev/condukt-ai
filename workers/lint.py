#!/usr/bin/env python3
from __future__ import annotations

import json
import sys


def main() -> int:
    _payload = json.loads(sys.stdin.read() or "{}")
    result = {
        "status": "ok",
        "confidence": 0.91,
        "output": {
            "warnings": 2,
            "status": "clean-enough",
        },
        "provenance": {
            "source": "simulated-lint",
        },
    }
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
