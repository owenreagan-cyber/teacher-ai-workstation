"""Top-level reconciliation: observe → snapshot → detect → impact → events → notify.

This is the deterministic "sync + change detection" pipeline. It compares a
current observation with the previous persisted snapshot, records deduplicated
SourceChangeEvents, computes affected artifacts, invalidates only affected
approvals, and drafts notifications. It performs NO Canvas writes and NO
notification delivery.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from . import change_detection as cd
from . import freshness
from . import impact
from . import notification_model as nm
from . import snapshot as snap
from .event_store import EventStore
from .models import SourceChangeEvent, WeeklyPlan


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def pacing_cells_from_plan(plan: WeeklyPlan) -> dict[str, Any]:
    """Convert a WeeklyPlan's subject/day cells into normalized pacing cells."""
    cells: dict[str, Any] = {}
    for subject, days in plan.subjects.items():
        for day in days:
            assessment = None
            if day.assessment is not None:
                assessment = {
                    "name": day.assessment.name,
                    "date": day.assessment.date,
                    "day": day.assessment.day or day.day,
                }
            cells[f"{subject}|{day.day}"] = {
                "lesson": day.lesson,
                "chapter": (day.teacher_override or {}).get("chapter") if day.teacher_override else None,
                "classwork": list(day.classwork),
                "homework": list(day.homework),
                "assessment": assessment,
            }
    return cells


def build_snapshot(
    *,
    quarter: int,
    week: int,
    week_id: str,
    pacing: dict[str, Any] | None = None,
    canvas: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Assemble a versioned snapshot from pacing/canvas observations."""
    snapshot = snap.blank_snapshot(quarter, week, week_id)
    if pacing:
        snapshot["pacing"] = {
            "status": pacing.get("status", snap.SNAPSHOT_OK),
            "observed_at": pacing.get("observed_at") or _now(),
            "identity": pacing.get("identity") or {},
            "fingerprint": snap.fingerprint(pacing.get("cells") or {}),
            "cells": pacing.get("cells") or {},
        }
    if canvas:
        snapshot["canvas"] = canvas
    return snapshot


def sync_and_detect(
    quarter: int,
    week: int,
    *,
    week_id: str | None = None,
    pacing: dict[str, Any] | None = None,
    canvas: dict[str, Any] | None = None,
    plan: WeeklyPlan | None = None,
) -> dict[str, Any]:
    """Run one observe→detect cycle. Returns a reconciliation report dict."""
    week_id = week_id or f"Q{quarter}W{week}"
    store = EventStore(quarter, week)

    curr = build_snapshot(quarter=quarter, week=week, week_id=week_id,
                          pacing=pacing, canvas=canvas)
    prev = snap.load(quarter, week)

    # Source outages are NEVER treated as an empty source. When a live read
    # fails, carry the last successful cells/objects forward and only flip the
    # status to STALE/UNAVAILABLE, so detection reports an outage instead of a
    # phantom deletion or an all-cells-cleared diff.
    if prev is not None:
        if (curr.get("pacing") or {}).get("status") in (snap.SNAPSHOT_STALE, snap.SNAPSHOT_UNAVAILABLE):
            prev_pacing = prev.get("pacing") or {}
            curr["pacing"]["cells"] = prev_pacing.get("cells") or {}
            curr["pacing"]["fingerprint"] = prev_pacing.get("fingerprint") or ""
            curr["pacing"]["identity"] = prev_pacing.get("identity") or {}
        if (curr.get("canvas") or {}).get("status") in (snap.SNAPSHOT_STALE, snap.SNAPSHOT_UNAVAILABLE):
            prev_canvas = prev.get("canvas") or {}
            curr["canvas"]["courses"] = prev_canvas.get("courses") or {}

    # Temporal change detection (previous ↔ current). Only when a prior
    # snapshot exists; a first observation produces NO false historical change.
    temporal_events: list[SourceChangeEvent] = []
    if prev is not None:
        temporal_events = cd.detect_changes(prev, curr)
        # Outage handling: never treat a missing source as deletion/conflict.
        if (curr.get("pacing") or {}).get("status") in (snap.SNAPSHOT_UNAVAILABLE, snap.SNAPSHOT_STALE):
            temporal_events = freshness.suppress_destructive(temporal_events, source="pacing")
        if (curr.get("canvas") or {}).get("status") in (snap.SNAPSHOT_UNAVAILABLE, snap.SNAPSHOT_STALE):
            temporal_events = freshness.suppress_destructive(temporal_events, source="canvas")

    # Baseline cross-source consistency (current pacing ↔ current Canvas).
    # Runs on EVERY observation — including the first — so a disagreement that
    # exists right now is surfaced even with no prior history. An outage
    # (either source unavailable) yields no conflicts.
    from . import cross_source
    cross_events: list[SourceChangeEvent] = cross_source.scan(curr, plan=plan)

    # Preserve historical false-positive records but close them as system-
    # superseded ONLY when the fresh sources confirm the preceding week's
    # front page and exactly one staged upcoming-week page.
    _, expected_transitions = cross_source.front_page_transition_state(curr)
    if expected_transitions:
        store.supersede(
            classification=cd.CROSS_SOURCE_CONFLICT,
            object_identities={
                f"{subject}:front_page"
                for subject in expected_transitions
            },
            except_ids=set(),
        )

    if cross_events:
        store.supersede(
            classification=cd.CROSS_SOURCE_CONFLICT,
            object_identities={e.object_identity for e in cross_events},
            except_ids={e.event_id for e in cross_events},
        )

    events = list(temporal_events) + list(cross_events)
    recorded = store.record(events)
    snap.save(quarter, week, curr)

    # Impact: affected subjects + approval invalidation (approval-by-exception).
    affected_subjects = sorted(impact.affected_subjects(events))
    invalidated: list[str] = []
    if plan is not None:
        invalidated = impact.invalidate_affected_approvals(plan, events)

    # Attention events (teacher decision) + notification drafts.
    attention = [
        e for e in store.unresolved()
        if e.get("family_comms_affected") or e.get("requires_teacher_approval")
    ]
    notifications = [_draft_notification(e) for e in attention if _needs_notification(e)]

    return {
        "baseline": prev is None,
        "week_id": week_id,
        "changes": [e for e in store.all() if e["event_id"] in {x.event_id for x in events}],
        "new_events_added": recorded["added"],
        "events": store.all(),
        "cross_source_conflicts": [
            e for e in store.unresolved()
            if e.get("classification") == cd.CROSS_SOURCE_CONFLICT
        ],
        "attention": attention,
        "notifications": notifications,
        "affected_subjects": affected_subjects,
        "invalidated_approvals": invalidated,
        "freshness": _freshness_report(curr),
        "canvas_writes": 0,
        "notifications_delivered": 0,
    }


def _freshness_report(snapshot: dict[str, Any]) -> dict[str, Any]:
    pacing = freshness.freshness_state((snapshot.get("pacing") or {}).get("observed_at"))
    canvas = freshness.freshness_state((snapshot.get("canvas") or {}).get("observed_at"))
    pacing["status"] = (snapshot.get("pacing") or {}).get("status")
    canvas["status"] = (snapshot.get("canvas") or {}).get("status")
    return {"pacing": pacing, "canvas": canvas}


def _needs_notification(event: dict[str, Any]) -> bool:
    return bool(event.get("family_comms_affected"))


def _draft_notification(event: dict[str, Any]) -> dict[str, Any]:
    source_event = SourceChangeEvent(
        source=event.get("source", ""),
        subject=event.get("subject", ""),
        object_type=event.get("object_type", ""),
        old_value=event.get("old_value"),
        new_value=event.get("new_value"),
        classification=event.get("classification", ""),
        object_identity=event.get("object_identity"),
        affected_artifacts=event.get("affected_artifacts") or [],
        family_comms_affected=bool(event.get("family_comms_affected")),
        week_id=event.get("week_id", ""),
    )
    notification = nm.draft_for_event(source_event)
    if notification is None:
        return {}
    data = notification.to_dict()
    data["event_id"] = event.get("event_id")
    data["review_link"] = "#agent"
    data["already_posted"] = event.get("already_posted")
    return data


def command_self_test() -> int:
    import tempfile
    from pathlib import Path as _P
    import scripts.weekly_planner_agent.snapshot as snapmod
    tmp = _P(tempfile.mkdtemp())
    orig = snapmod.agent_root
    snapmod.agent_root = lambda: tmp
    try:
        plan = WeeklyPlan(week_id="Q2W3", quarter=2, week=3)
        from .models import Assessment, Authority, DayPlan
        plan.upsert_day(DayPlan(subject="math", day="Thursday", lesson="WA8",
                                assessment=Assessment(name="Written Assessment 8", subject="math",
                                                      day="Thursday", date="2026-11-05")))
        pacing = {"identity": {"name": "FPK"}, "cells": pacing_cells_from_plan(plan)}
        r1 = sync_and_detect(2, 3, week_id="Q2W3", pacing=pacing, plan=plan)
        assert r1["baseline"] is True
        # Change date.
        plan.day("math", "Thursday").assessment.date = "2026-11-06"
        pacing2 = {"identity": {"name": "FPK"}, "cells": pacing_cells_from_plan(plan)}
        r2 = sync_and_detect(2, 3, week_id="Q2W3", pacing=pacing2, plan=plan)
        assert r2["baseline"] is False
        assert any(e["classification"] == "assessment_date_changed" for e in r2["events"])
        assert r2["notifications"], r2["notifications"]
    finally:
        snapmod.agent_root = orig
    print("PASS weekly-planner-agent reconciliation self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(command_self_test())
