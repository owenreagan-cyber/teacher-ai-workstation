#!/usr/bin/env python3
"""Execute Phase G from the three approved existing evidence artifacts."""

from __future__ import annotations

import json
import sys

from pilot import PilotBoundaryError
from relationship_pilot import execute_relationship_pilot


def main() -> int:
    try:
        result = execute_relationship_pilot()
    except (OSError, ValueError, PilotBoundaryError) as exc:
        print(f"FAIL: relationship.pilot: {exc}")
        return 1
    print(json.dumps(result.__dict__, indent=2))
    return 0 if result.status == "completed" else 1


if __name__ == "__main__":
    sys.exit(main())
