from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.canvas_llm_phase26.pipeline import validate_workstation_packet  # noqa: E402


def main() -> int:
    failures = 0
    for raw in sys.argv[1:]:
        path = Path(raw)
        payload = json.loads(path.read_text(encoding="utf-8"))
        validation = validate_workstation_packet(payload)
        for finding in validation["findings"]:
            print(f"{finding['severity'].upper()}: {finding['code']} {finding['message']}")
        print(f"PASS: {validation['passCount']}")
        print(f"WARN: {validation['warnCount']}")
        print(f"FAIL: {validation['failCount']}")
        failures += validation["failCount"]
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

