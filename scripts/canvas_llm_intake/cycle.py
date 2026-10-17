"""Recurring weekly intake cycle (prepare-next orchestration).

Resolves the next instructional week, fetches authoritative pacing, detects
source delta vs any existing packet, preserves owner overrides, and delegates
the full draft to ``intake.build_intake``. Stops at READY_TO_PUBLISH — never
deploys.

Delta classification:
    NEW       — no existing packet for this week
    UNCHANGED — source hash identical to existing packet
    CHANGED   — source hash differs; per-cell diff surfaced

Owner override precedence: a local teacher-input / owner override is surfaced as
``SOURCE_CHANGED_AFTER_OWNER_OVERRIDE`` when refreshed pacing conflicts, and
Owen review is required (never silently pick one side).
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.canvas_llm_phase3 import constants as P3
from scripts.canvas_llm_phase3 import pacing_extractor as pe

from . import constants as C
from . import intake
from . import manifest as mf
from . import teacher_input as ti
from . import week_resolution as wr


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _week_hash(week_norm: dict[str, Any]) -> str:
    """Stable content hash (excludes timestamp-bearing ``source`` metadata)."""
    from .intake import _content_hash
    return _content_hash(week_norm)


def next_unprepared_week() -> tuple[int, int]:
    """Resolve the next instructional week that is NOT already PUBLISHED_VERIFIED.

    Walks the canonical calendar from the current week forward, skipping any
    week whose local intake packet is already PUBLISHED_VERIFIED. This is the
    recurring-cycle target (prepare the next not-yet-published week).
    """
    import datetime as dt

    today = dt.datetime.now(dt.timezone(dt.timedelta(hours=-4))).date()
    weeks = sorted(
        (w for w in wr.load_weeks() if wr._week_start(w) is not None),
        key=lambda w: wr._week_start(w),
    )
    for w in weeks:
        start = wr._week_start(w)
        if start is None or start < today:
            continue
        q, wk = int(w["quarter"]), int(w["week"])
        m = mf.load_manifest(q, wk)
        if m is not None and m.get("status") == "PUBLISHED_VERIFIED":
            continue  # already done; skip
        return q, wk
    raise RuntimeError("no unprepared instructional week ahead")


def detect_delta(quarter: int, week: int, fresh_week_norm: dict[str, Any]) -> dict[str, Any]:
    """Classify NEW / UNCHANGED / CHANGED against an existing packet.

    Also computes a per-cell diff (subject/day -> {before, after}) when CHANGED.
    """
    manifest = mf.load_manifest(quarter, week)
    existing_hash = manifest.get("source_hash") if manifest else None
    fresh_hash = _week_hash(fresh_week_norm)

    if manifest is None:
        return {"delta": "NEW", "fresh_hash": fresh_hash, "changes": []}

    if existing_hash == fresh_hash:
        return {"delta": "UNCHANGED", "fresh_hash": fresh_hash, "existing_hash": existing_hash, "changes": []}

    # CHANGED: diff normalized cells against the stored snapshot.
    prev_norm = None
    snap = mf.staging_dir(quarter, week) / "source" / "pacing-snapshot.json"
    if snap.exists():
        try:
            prev_norm = json.loads(snap.read_text(encoding="utf-8")).get("normalized")
        except (json.JSONDecodeError, OSError):
            prev_norm = None

    changes: list[dict[str, Any]] = []
    if prev_norm:
        for wd in C.WEEKDAYS:
            cur_day = (fresh_week_norm.get("days") or {}).get(wd, {})
            prev_day = (prev_norm.get("days") or {}).get(wd, {})
            for subject in C.SUBJECT_KEYS:
                cur = cur_day.get("subjects", {}).get(subject, {}).get("raw", "")
                prev = prev_day.get("subjects", {}).get(subject, {}).get("raw", "")
                if cur != prev:
                    changes.append({"weekday": wd, "subject": subject, "before": prev, "after": cur})

    return {
        "delta": "CHANGED",
        "fresh_hash": fresh_hash,
        "existing_hash": existing_hash,
        "changes": changes,
    }


def detect_owner_override_conflict(
    quarter: int, week: int, fresh_week_norm: dict[str, Any]
) -> list[dict[str, Any]]:
    """Surface conflicts between local owner input and refreshed pacing.

    Returns a list of conflicts; empty means no conflict. This never silently
    picks a side — the caller must require Owen review.
    """
    conflicts: list[dict[str, Any]] = []
    data = ti.load_input(quarter, week)
    subjects_block = data.get("subjects", {})
    # An owner override is represented by reject_assignments / replace_announcement
    # / notes. If refreshed pacing would re-propose a rejected assignment, that
    # is a conflict to surface.
    for subject, block in subjects_block.items():
        for rej in block.get("reject_assignments", []):
            conflicts.append({
                "kind": "SOURCE_CHANGED_AFTER_OWNER_OVERRIDE",
                "subject": subject,
                "detail": f"owner rejected assignment {rej!r}; refreshed pacing may re-propose it",
            })
        for _n in block.get("add_reminder", []):
            conflicts.append({
                "kind": "OWNER_OVERRIDE_PRESERVED",
                "subject": subject,
                "detail": "owner-added reminder will be preserved",
            })
    return conflicts


def prepare_week(
    *,
    quarter: int,
    week: int,
    fresh: bool = True,
    canvas=None,
    include_canvas_context: bool = True,
) -> dict[str, Any]:
    """Full recurring prepare: fetch -> delta -> build. Never deploys.

    Refuses to re-prepare a week already marked PUBLISHED_VERIFIED (the
    recurring cycle must skip completed weeks, not clobber their lifecycle).
    """
    week_code = wr.week_code_for(quarter, week)
    existing = mf.load_manifest(quarter, week)
    if existing is not None and existing.get("status") == "PUBLISHED_VERIFIED":
        return {
            "week_code": week_code,
            "quarter": quarter,
            "week": week,
            "skipped": True,
            "reason": "already PUBLISHED_VERIFIED; no re-prepare",
            "canvas_writes": 0,
        }

    # Fetch fresh normalized week for delta detection (build_intake re-fetches,
    # but we want the delta against the EXISTING packet before regenerating).
    rows, meta = pe.fetch_pacing(fresh=fresh)
    fresh_norm = pe.extract_week(rows, week_code, meta)

    delta = detect_delta(quarter, week, fresh_norm)
    conflicts = detect_owner_override_conflict(quarter, week, fresh_norm)

    summary = intake.build_intake(
        quarter=quarter,
        week=week,
        fresh=fresh,
        canvas=canvas,
        include_canvas_context=include_canvas_context,
    )

    # Record delta + conflicts into the manifest + a local changes file.
    d = mf.staging_dir(quarter, week)
    (d / "changes.json").write_text(
        json.dumps({"delta": delta, "conflicts": conflicts}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8"
    )

    manifest = mf.load_manifest(quarter, week) or {}
    manifest["source_delta"] = delta["delta"]
    manifest["owner_override_conflicts"] = conflicts
    mf.save_manifest(quarter, week, manifest)

    summary["source_delta"] = delta
    summary["owner_override_conflicts"] = conflicts
    return summary


def command_self_test() -> int:
    import tempfile
    from pathlib import Path

    # delta detection with synthetic packets.
    with tempfile.TemporaryDirectory() as tmp:
        import scripts.canvas_llm_intake.manifest as mfmod
        orig = mfmod.staging_dir
        mfmod.staging_dir = lambda q, w: Path(tmp) / f"q{q}w{w}"
        try:
            week = {
                "week": {"code": "Q2W3", "startDate": "2026-10-26", "endDate": "2026-10-30"},
                "days": {
                    "Monday": {"date": "2026-10-26", "subjects": {"math": {"raw": "L41"}, "reading": {"raw": "46"}, "spelling": {"raw": "41"}, "language_arts": {"raw": "7.1"}, "science": {"raw": "Ch. 4"}, "history": {"raw": ""}}},
                },
            }
            # NEW: no manifest.
            d = detect_delta(2, 3, week)
            assert d["delta"] == "NEW", d

            # Write a manifest with a DIFFERENT hash -> CHANGED.
            m = mfmod.new_manifest(quarter=2, week=3, week_code="Q2W3",
                                   date_range={"start": "2026-10-26", "end": "2026-10-30"})
            m["source_hash"] = "deadbeef"
            mfmod.save_manifest(2, 3, m)
            d2 = detect_delta(2, 3, week)
            assert d2["delta"] == "CHANGED", d2

            # Same hash -> UNCHANGED.
            m2 = mfmod.load_manifest(2, 3)
            m2["source_hash"] = d2["fresh_hash"]
            mfmod.save_manifest(2, 3, m2)
            d3 = detect_delta(2, 3, week)
            assert d3["delta"] == "UNCHANGED", d3
        finally:
            mfmod.staging_dir = orig

    print("PASS intake cycle self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(command_self_test())
