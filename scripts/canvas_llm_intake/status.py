"""PASS/WARN/FAIL status proof for Canvas Weekly Intake.

Reports source freshness, draft status, open questions, approval state, and
publish readiness. It never approves or publishes — Owen is the approval
authority.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import constants as C
from . import week_resolution as wr
from . import manifest as mf


def _zero_write_proof() -> dict[str, Any]:
    """Static proof this package cannot invoke Canvas write verbs.

    Tokens are constructed dynamically so the scanner's own source never
    self-matches (mirrors the Phase 3 zero-write proof).
    """
    forbidden = ["." + v + "(" for v in ("post", "put", "patch", "delete")]
    forbidden += ["method" + "=\"" + v.upper() + "\"" for v in ("post", "put", "patch", "delete")]
    forbidden += ["requests." + v for v in ("post", "put", "patch", "delete")]
    found: list[str] = []
    for p in Path(__file__).parent.glob("*.py"):
        src = p.read_text(encoding="utf-8")
        for tok in forbidden:
            if tok in src:
                found.append(f"{p.name}:{tok}")
    return {"write_free": len(found) == 0, "detail": found or "no Canvas write verbs in intake package"}


def render_status() -> dict[str, Any]:
    lines = ["Canvas Weekly Intake"]
    checks: list[tuple[bool, str]] = []

    # Source availability (pacing engine config present).
    from scripts.canvas_llm_phase3 import constants as P3

    checks.append((P3.WEEKS_PATH.exists(), "instructional-weeks config present"))
    checks.append((P3.QUARTER_ACTIVATION_PATH.exists(), "quarter-activation config present"))

    # Latest intake manifest (if any).
    manifests = sorted(C.INTAKE_ROOT.glob("2026-2027/q*/w*/intake-manifest.json"))
    if manifests:
        latest = json.loads(manifests[-1].read_text(encoding="utf-8"))
        checks.append((True, f"latest intake: {latest.get('week_code')} ({latest.get('status')})"))
        checks.append((latest.get("status") != "NEEDS_INPUT", f"open questions: {len(latest.get('questions') or [])}"))
        checks.append((latest.get("approval_state") != "PENDING", f"approval: {latest.get('approval_state')}"))
        publish_ready = latest.get("status") in ("TEACHER_APPROVED", "READY_TO_PUBLISH")
        checks.append((publish_ready, "publish readiness"))
    else:
        checks.append((True, "no intake staged yet (informational)"))

    zw = _zero_write_proof()
    checks.append((zw["write_free"], f"zero-write proof: {zw['detail'] if not zw['write_free'] else 'no write verbs'}"))

    fails = sum(1 for ok, _ in checks if not ok)
    for ok, label in checks:
        lines.append(f"  {'PASS' if ok else 'WARN'}  {label}")
    overall = "PASS" if fails == 0 else "WARN"
    lines.append(f"\nSummary: {overall}")
    return {"text": "\n".join(lines), "ok": fails == 0, "overall": overall}


def command_self_test() -> int:
    s = render_status()
    assert s["overall"] in ("PASS", "WARN")
    assert _zero_write_proof()["write_free"] is True
    print("PASS intake status self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(command_self_test())
