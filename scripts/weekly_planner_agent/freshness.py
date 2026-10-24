"""Source freshness tracking and outage handling.

Freshness is tracked separately for Google pacing and Canvas. A source outage is
NEVER interpreted as an empty source or as evidence that Canvas objects were
deleted: the last successful snapshot is preserved, marked stale, and
destructive/publication conclusions that depend on the missing source are
suppressed.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

STALE_THRESHOLD_SECONDS = 8 * 3600  # 8 hours


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse(ts: str | None) -> datetime | None:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    except ValueError:
        return None


def freshness_state(observed_at: str | None, *, now: datetime | None = None) -> dict[str, Any]:
    """Human-readable + machine freshness for one source observation."""
    now = now or _now()
    observed = _parse(observed_at)
    if observed is None:
        return {"label": "not checked yet", "minutes_ago": None, "stale": False}
    minutes = max(0, int((now - observed).total_seconds() // 60))
    stale = (now - observed).total_seconds() > STALE_THRESHOLD_SECONDS
    if minutes < 1:
        label = "checked just now"
    elif minutes < 60:
        label = f"checked {minutes} minute{'s' if minutes != 1 else ''} ago"
    else:
        hours = minutes // 60
        label = f"checked {hours} hour{'s' if hours != 1 else ''} ago"
    if stale:
        label += " (stale)"
    return {"label": label, "minutes_ago": minutes, "stale": stale, "observed_at": observed_at}


def mark_unavailable(
    snapshot: dict[str, Any],
    section: str,
    *,
    reason: str = "source unavailable",
    observed_at: str | None = None,
) -> dict[str, Any]:
    """Mark a section unavailable while PRESERVING the last successful data.

    The caller keeps the prior snapshot's cells/objects; this only flips the
    status so downstream detection reports an outage instead of a deletion.
    """
    section_data = dict(snapshot.get(section) or {})
    section_data["status"] = "UNAVAILABLE"
    section_data["unavailable_reason"] = reason
    if observed_at:
        section_data["last_success_at"] = section_data.get("observed_at") or observed_at
    snapshot[section] = section_data
    return snapshot


def suppress_destructive(events: list[Any], *, source: str) -> list[Any]:
    """Drop destructive conclusions (missing/deleted/conflict) when a source was unavailable.

    Accepts either ``SourceChangeEvent`` objects or event dicts.
    """
    destructive = {"assignment_missing", "reminder_missing", "canvas_conflict",
                   "page_body_changed", "front_page_changed", "assessment_removed"}

    def _src(e: Any) -> str:
        return e.source if hasattr(e, "source") else e.get("source")

    def _cls(e: Any) -> str:
        return e.classification if hasattr(e, "classification") else e.get("classification")

    return [
        e for e in events
        if not (_src(e) == source and _cls(e) in destructive)
    ]


def command_self_test() -> int:
    now = datetime(2026, 10, 24, 12, 0, tzinfo=timezone.utc)
    fresh = freshness_state("2026-10-24T11:53:00Z", now=now)
    assert fresh["label"] == "checked 7 minutes ago" and not fresh["stale"]
    old = freshness_state("2026-10-24T01:00:00Z", now=now)
    assert old["stale"] and "stale" in old["label"]
    snap = {"pacing": {"status": "OK", "cells": {"a": 1}}, "canvas": {}}
    mark_unavailable(snap, "pacing", reason="network down")
    assert snap["pacing"]["status"] == "UNAVAILABLE"
    assert snap["pacing"]["cells"] == {"a": 1}  # data preserved, not deleted
    print("PASS weekly-planner-agent freshness self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(command_self_test())
