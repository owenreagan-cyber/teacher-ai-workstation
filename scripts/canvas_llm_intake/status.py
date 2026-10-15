"""PASS/WARN/FAIL status proof for Canvas Weekly Intake.

Reports source freshness, open/answered question counts, approval state,
blocked count, current lifecycle, and publish readiness. Pending teacher
approval is a WARN (not a technical FAIL); broken source/artifact or a failed
safety gate is a FAIL.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from . import constants as C
from . import manifest as mf
from . import questions as qs
from . import week_resolution as wr


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
    checks: list[tuple[str, bool, bool]] = []  # (label, ok, is_technical_fail)
    technical_fail = False

    from scripts.canvas_llm_phase3 import constants as P3

    # Technical prerequisites.
    checks.append(("instructional-weeks config present", P3.WEEKS_PATH.exists(), True))
    checks.append(("quarter-activation config present", P3.QUARTER_ACTIVATION_PATH.exists(), True))

    # Zero-write proof (safety gate — a FAIL here is a hard technical failure).
    zw = _zero_write_proof()
    checks.append(("zero-write proof", zw["write_free"], True))
    if not zw["write_free"]:
        technical_fail = True

    manifests = sorted(C.INTAKE_ROOT.glob("2026-2027/q*/w*/intake-manifest.json"))
    if manifests:
        latest = json.loads(manifests[-1].read_text(encoding="utf-8"))
        week_code = latest.get("week_code", "?")
        status = latest.get("status", "?")
        lines.append("")
        lines.append(f"Latest packet: {week_code}")
        lines.append(f"  lifecycle: {status}")
        checks.append((f"source freshness ({week_code})", bool(latest.get("source_hash")), True))

        # Questions: load from the latest packet's own quarter/week (not the
        # current week — the staged packet may be for next week).
        q = latest.get("quarter", 1)
        w = latest.get("week", 1)
        all_questions = qs.load_questions(q, w)
        open_q = qs.unresolved_questions(all_questions)
        answered_q = len(all_questions) - len(open_q)
        lines.append(f"  questions: {len(open_q)} open, {answered_q} answered")
        checks.append((f"open questions ({len(open_q)})", len(open_q) == 0, False))

        approval_summary = latest.get("approval_summary") or {}
        approved = 0
        blocked = 0
        total = 0
        for s, gran in approval_summary.items():
            for g, st in gran.items():
                total += 1
                if st == "APPROVED":
                    approved += 1
                elif st == "BLOCKED":
                    blocked += 1
        lines.append(f"  approvals: {approved}/{total} approved, {blocked} blocked")
        checks.append((f"approvals ({approved}/{total})", approved >= total, False))
        checks.append(("no blocked artifacts", blocked == 0, False))

        ready = bool(latest.get("ready_to_publish"))
        lines.append(f"  ready to publish: {'YES' if ready else 'NO'}")
        checks.append(("ready to publish", ready, False))

        # A packet with a broken artifact is FAIL; pending approval is WARN.
        if status in ("SOURCE_FETCHED", "NORMALIZED", "DRAFTED", "NEEDS_INPUT"):
            # Incomplete lifecycle is informational/WARN (not a defect).
            checks.append((f"lifecycle complete ({status})", False, False))
        else:
            checks.append((f"lifecycle complete ({status})", True, False))
    else:
        lines.append("")
        lines.append("No intake staged yet (informational).")

    # Render.
    for label, ok, _technical in checks:
        mark = "PASS" if ok else "WARN"
        lines.append(f"  {mark}  {label}")

    # Technical failures are the only FAIL.
    fails = sum(1 for _, ok, technical in checks if (not ok and technical))
    any_warn = any(not ok for _, ok, _ in checks)
    if fails:
        overall = "FAIL"
    elif any_warn:
        overall = "WARN"
    else:
        overall = "PASS"
    lines.append(f"\nSummary: {overall}")
    return {"text": "\n".join(lines), "ok": fails == 0, "overall": overall}


def command_self_test() -> int:
    s = render_status()
    assert s["overall"] in ("PASS", "WARN", "FAIL")
    assert _zero_write_proof()["write_free"] is True
    print("PASS intake status self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(command_self_test())
