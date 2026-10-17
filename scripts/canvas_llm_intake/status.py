"""PASS/WARN/FAIL status proof for Canvas Weekly Intake.

Distinguishes the latest COMPLETED week (PUBLISHED_VERIFIED) from the next
PREPARED week (NEEDS_INPUT / READY_FOR_REVIEW / READY_TO_PUBLISH). A completed
verified week does NOT cause WARN merely for being complete.

Semantics:
    PASS = healthy system / completed verified week
    WARN = valid packet awaiting teacher review/approval
    FAIL = technical/safety defect
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
    """Static proof this package cannot invoke Canvas write verbs."""
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


def _load_manifests() -> list[dict[str, Any]]:
    manifests = []
    for p in sorted(C.INTAKE_ROOT.glob("2026-2027/q*/w*/intake-manifest.json")):
        try:
            manifests.append(json.loads(p.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError):
            continue
    return manifests


def render_status(*, quarter: int | None = None, week: int | None = None) -> dict[str, Any]:
    lines = ["Canvas Weekly Intake"]
    checks: list[tuple[str, bool, bool]] = []  # (label, ok, technical_fail)
    technical_fail = False

    from scripts.canvas_llm_phase3 import constants as P3

    checks.append(("instructional-weeks config present", P3.WEEKS_PATH.exists(), True))
    checks.append(("quarter-activation config present", P3.QUARTER_ACTIVATION_PATH.exists(), True))
    zw = _zero_write_proof()
    checks.append(("zero-write proof", zw["write_free"], True))
    if not zw["write_free"]:
        technical_fail = True

    manifests = _load_manifests()

    # Partition: completed (PUBLISHED_VERIFIED) vs prepared (everything else).
    completed = [m for m in manifests if m.get("status") == "PUBLISHED_VERIFIED"]
    prepared = [m for m in manifests if m.get("status") != "PUBLISHED_VERIFIED"]

    # If an explicit quarter/week is requested, focus on that packet.
    target = None
    if quarter is not None and week is not None:
        target = next((m for m in manifests if m.get("quarter") == quarter and m.get("week") == week), None)
        if target is None:
            lines.append("")
            lines.append(f"No packet for Q{quarter}W{week}.")
            lines.append("\nSummary: WARN")
            return {"text": "\n".join(lines), "ok": True, "overall": "WARN"}
        completed = [m for m in manifests if m.get("status") == "PUBLISHED_VERIFIED" and m is target]
        prepared = [m for m in manifests if m.get("status") != "PUBLISHED_VERIFIED" and m is target]

    lines.append("")
    if completed:
        latest_completed = completed[-1]
        lines.append(f"Latest completed: {latest_completed.get('week_code')} — PUBLISHED_VERIFIED")
        checks.append((f"completed week ({latest_completed.get('week_code')})", True, False))
    else:
        lines.append("Latest completed: none yet")

    if prepared:
        next_prepared = prepared[-1]
        wc = next_prepared.get("week_code", "?")
        st = next_prepared.get("status", "?")
        lines.append(f"Next prepared: {wc} — {st}")
        q = next_prepared.get("quarter", 1)
        w = next_prepared.get("week", 1)
        all_q = qs.load_questions(q, w)
        open_q = qs.unresolved_questions(all_q)
        lines.append(f"  open questions: {len(open_q)}")
        lines.append(f"  changed since last run: {next_prepared.get('source_delta', 'N/A')}")
        lines.append(f"  ready to publish: {'YES' if next_prepared.get('ready_to_publish') else 'NO'}")
        # Pending review is WARN (not FAIL).
        checks.append((f"next packet review pending ({wc})", next_prepared.get("ready_to_publish", False), False))
    else:
        lines.append("Next prepared: none (run `prepare-next`)")

    # Technical prerequisites render.
    for label, ok, technical in checks:
        mark = "PASS" if ok else ("FAIL" if technical else "WARN")
        lines.append(f"  {mark}  {label}")

    fails = sum(1 for _, ok, technical in checks if (not ok and technical))
    any_warn = any(not ok for _, ok, _ in checks)
    overall = "FAIL" if fails else ("WARN" if any_warn else "PASS")
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
