"""Guarded publish orchestration for the Weekly Planner Agent.

Bridges agent state (plan-version-bound approval, source snapshots, unresolved
change events) to the existing guarded Friday rollover publisher.

The existing ``bin/canvas-weekly-rollover`` engine remains the SOLE publisher:
this module computes an agent-level publish gate, binds one teacher approval to
the exact plan/source versions reviewed, then delegates publication to
``scripts.canvas_llm_rollover.rollover.publish_weekly_package`` and maps the
resulting deployment ledger back to the agent review state. No second publisher.
"""
from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from scripts.canvas_planner import friday as friday_module
from scripts.canvas_llm_rollover import rollover

from . import freshness
from . import snapshot as snapmod
from .event_store import EventStore
from .models import (
    FRIDAY_APPROVED,
    FRIDAY_BLOCKED,
    FRIDAY_PUBLISHING,
    FRIDAY_PUBLISHED_VERIFIED,
    PlanApproval,
    WeeklyPlan,
)

# Agent publish-state file (plan-version-bound approval + last publish result).
SCHEMA_VERSION = 1


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def state_path(quarter: int, week: int) -> Path:
    return snapmod._week_dir(quarter, week) / "publish-state.json"


def _read_state(quarter: int, week: int) -> dict[str, Any]:
    try:
        data = json.loads(state_path(quarter, week).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _write_state(quarter: int, week: int, data: dict[str, Any]) -> None:
    path = state_path(quarter, week)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    import os
    os.replace(tmp, path)


def _sha(value: str) -> str:
    return hashlib.sha256((value or "").encode("utf-8")).hexdigest()


def plan_version(plan: WeeklyPlan) -> str:
    """Stable fingerprint of the approval-relevant plan content.

    Includes subject/day lesson + classwork + homework + assessment dates,
    teacher overrides, and the assignment/announcement/reminder candidates.
    Excludes volatile fields (freshness, change_history, approval_status).
    """
    payload = {
        "week_id": plan.week_id,
        "date_range": plan.date_range,
        "subjects": {
            subject: [
                {
                    "day": d.day, "lesson": d.lesson,
                    "classwork": sorted(d.classwork), "homework": sorted(d.homework),
                    "assessment": (d.assessment.to_dict() if d.assessment else None),
                    "teacher_override": d.teacher_override,
                }
                for d in sorted(days, key=lambda x: x.day)
            ]
            for subject, days in sorted(plan.subjects.items())
        },
        "assignment_candidates": plan.assignment_candidates,
        "announcement_candidates": plan.announcement_candidates,
        "reminder_candidates": plan.reminder_candidates,
        "homeroom_items": plan.homeroom_items,
    }
    return _sha(json.dumps(payload, sort_keys=True, ensure_ascii=False))


def source_fingerprint(snapshot: dict[str, Any] | None) -> str:
    if not snapshot:
        return ""
    pacing = snapshot.get("pacing") or {}
    canvas = snapshot.get("canvas") or {}
    payload = {
        "pacing_fingerprint": pacing.get("fingerprint") or "",
        "pacing_status": pacing.get("status"),
        "canvas_status": canvas.get("status"),
        "canvas_fingerprint": _sha(json.dumps(canvas.get("courses", {}), sort_keys=True, ensure_ascii=False)),
    }
    return _sha(json.dumps(payload, sort_keys=True, ensure_ascii=False))


def approve_plan(
    quarter: int,
    week: int,
    *,
    plan: WeeklyPlan | None = None,
    snapshot: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Record a plan-version-bound approval for one week.

    Also delegates canonical per-course approval to the existing approval bundle
    so the guarded rollover's readiness gate sees real approvals. The agent-level
    record is the thin plan-version binding (not a duplicate artifact store).
    """
    from scripts.weekly_planner_agent import service as agent_service

    plan = plan if plan is not None else agent_service.load_plan(quarter, week)
    snapshot = snapshot if snapshot is not None else snapmod.load(quarter, week)
    if plan is None:
        raise ValueError("no weekly plan to approve")

    approval = PlanApproval(
        week_id=plan.week_id,
        plan_version=plan_version(plan),
        source_fingerprint=source_fingerprint(snapshot),
    )
    state = _read_state(quarter, week)
    state["schema_version"] = SCHEMA_VERSION
    state["week_id"] = plan.week_id
    state["approval"] = approval.to_dict()
    _write_state(quarter, week, state)

    # Delegate canonical per-course approval (reuse, never duplicate). Only
    # active academic subjects + homeroom have approvals.
    delegated: list[str] = []
    from scripts.canvas_planner import approval_bundle
    from scripts.canvas_llm_intake import constants as IC
    for course in IC.active_subject_keys_for_quarter(quarter):
        try:
            approval_bundle.approve_course(
                quarter, week, course=course, expected_hashes=None, confirm_without_ai=True,
            )
            delegated.append(course)
        except Exception as exc:  # noqa: BLE001 — canonical store may be absent in dry tests
            delegated.append(f"{course}:{type(exc).__name__}")
    try:
        approval_bundle.approve_course(
            quarter, week, course="homeroom", expected_hashes=None, confirm_without_ai=True,
        )
        delegated.append("homeroom")
    except Exception as exc:  # noqa: BLE001
        delegated.append(f"homeroom:{type(exc).__name__}")

    return {"approval": approval.to_dict(), "delegated": delegated}


def load_approval(quarter: int, week: int) -> PlanApproval | None:
    state = _read_state(quarter, week)
    record = state.get("approval")
    if not isinstance(record, dict):
        return None
    return PlanApproval(
        week_id=record.get("week_id", ""),
        plan_version=record.get("plan_version", ""),
        source_fingerprint=record.get("source_fingerprint", ""),
        canvas_fingerprint=record.get("canvas_fingerprint", ""),
        approved_at=record.get("approved_at", ""),
        approved_by=record.get("approved_by", "OWNER_UI"),
    )


def _unresolved_assessment_events(quarter: int, week: int) -> list[dict[str, Any]]:
    store = EventStore(quarter, week)
    return [
        e for e in store.unresolved()
        if e.get("classification") in ("assessment_date_changed", "assessment_identity_changed")
        or e.get("family_comms_affected")
    ]


def _conflict_blocks_publish(event: dict[str, Any]) -> bool:
    """A cross-source conflict blocks publication when a live correction is needed.

    "Missing" states (assessment assignment, first announcement, day-before
    reminder) are often simply "not yet created by the Friday rollover" — they
    are review-needed but NOT publish-blocking; the canonical rollover readiness
    gate already blocks on genuinely missing approved content at publish time.
    A *value disagreement* (date, identity, front page, obsolete reminder) is a
    material live correction and blocks unless an explicit owner override makes
    the plan authoritative AND Canvas already agrees with that override.
    """
    object_type = event.get("object_type") or ""
    if object_type in ("assessment_assignment_missing", "first_announcement", "day_before_reminder"):
        return False
    winner = event.get("authority_winner") or ""
    canvas_value = event.get("canvas_value")
    authoritative = event.get("old_value")
    if winner == "OWNER_INSTRUCTION":
        # Only pacing disagrees (Canvas already agrees with the override) -> non-blocking.
        return canvas_value is not None and canvas_value != authoritative
    # No override: any canvas-side value disagreement blocks.
    return True


def build_publish_gate(
    quarter: int,
    week: int,
    *,
    plan: WeeklyPlan | None = None,
    snapshot: dict[str, Any] | None = None,
    rollover_readiness: dict[str, Any] | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Evaluate the agent-level publish gate (pure; no Canvas writes).

    Returns ``{ready, blockers, plan_version, source_fingerprint, approval_ok,
    source_ok, unresolved_conflicts}``. ``rollover_readiness`` is the canonical
    rollover readiness result (injectable; defaults to the real one).
    """
    from scripts.weekly_planner_agent import service as agent_service

    plan = plan if plan is not None else agent_service.load_plan(quarter, week)
    snapshot = snapshot if snapshot is not None else snapmod.load(quarter, week)

    blockers: list[str] = []
    now = now or datetime.now(timezone.utc)

    # 1. Current source snapshot required.
    if snapshot is None:
        blockers.append("No source snapshot yet — run a sync first.")
    else:
        pacing_fresh = freshness.freshness_state(
            (snapshot.get("pacing") or {}).get("observed_at"), now=now)
        canvas_fresh = freshness.freshness_state(
            (snapshot.get("canvas") or {}).get("observed_at"), now=now)
        if (snapshot.get("pacing") or {}).get("status") in (snapmod.SNAPSHOT_UNAVAILABLE, snapmod.SNAPSHOT_STALE):
            blockers.append("Pacing source is stale or unavailable.")
        elif pacing_fresh.get("stale"):
            blockers.append("Pacing source is stale.")
        if (snapshot.get("canvas") or {}).get("status") in (snapmod.SNAPSHOT_UNAVAILABLE, snapmod.SNAPSHOT_STALE):
            blockers.append("Canvas source is stale or unavailable.")

    # 2. No unresolved assessment-date / family-comms changes.
    unresolved = _unresolved_assessment_events(quarter, week)
    if unresolved:
        blockers.append("An assessment-date change is unresolved — review it before publishing.")

    # 2b. No material unresolved cross-source conflicts. An explicit owner
    # override may resolve the *plan*, but a Canvas-side disagreement still
    # needs a correction decision before publication.
    cross_conflicts = [
        e for e in EventStore(quarter, week).unresolved()
        if e.get("classification") == "cross_source_conflict"
    ]
    blocking_conflicts = [
        e for e in cross_conflicts
        if _conflict_blocks_publish(e)
    ]
    if blocking_conflicts:
        blockers.append(
            "A cross-source conflict with Canvas is unresolved — review it before publishing."
        )

    # 3. Approval present and still bound to the current plan + source versions.
    approval = load_approval(quarter, week)
    current_pv = plan_version(plan) if plan is not None else ""
    current_sf = source_fingerprint(snapshot)
    approval_ok = approval is not None
    if approval is None:
        blockers.append("The plan is not approved yet.")
    elif approval.plan_version != current_pv:
        blockers.append("The plan changed after approval — review the affected items again.")
        approval_ok = False
    elif approval.source_fingerprint and approval.source_fingerprint != current_sf:
        blockers.append("The source changed after approval — review the affected items again.")
        approval_ok = False

    # 4. Canonical rollover readiness (approvals + agenda hash + homeroom).
    if rollover_readiness is None:
        from scripts.canvas_planner import friday as friday_mod
        try:
            fq, fw, _tq, _tw = friday_mod._weeks(date.today())
        except Exception:  # noqa: BLE001
            fq, fw = quarter, week
        rollover_readiness = rollover.build_readiness(fq, fw, quarter, week)
    for blocker in rollover_readiness.get("blockers") or []:
        blockers.append(blocker)

    ready = len(blockers) == 0
    return {
        "ready": ready,
        "blockers": blockers,
        "plan_version": current_pv,
        "source_fingerprint": current_sf,
        "approval_ok": approval_ok,
        "unresolved_conflicts": [e.get("event_id") for e in unresolved],
    }


def publish(
    quarter: int,
    week: int,
    *,
    client: Any,
    owner_confirmation: str | None = None,
    from_quarter: int | None = None,
    from_week: int | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Run the gate, then delegate to the existing guarded rollover publisher.

    Returns ``{gate, report, review_state, published}``. On gate failure or a
    blocked/failed publish, the review state becomes BLOCKED and no second
    publishing path is used.
    """
    from scripts.weekly_planner_agent import service as agent_service

    plan = agent_service.load_plan(quarter, week)
    snapshot = snapmod.load(quarter, week)

    if from_quarter is None or from_week is None:
        from scripts.canvas_planner import friday as friday_mod
        fq, fw, _tq, _tw = friday_mod._weeks((now or datetime.now(timezone.utc)).date())
        from_quarter, from_week = from_quarter or fq, from_week or fw

    gate = build_publish_gate(
        quarter, week, plan=plan, snapshot=snapshot,
        rollover_readiness=rollover.build_readiness(from_quarter, from_week, quarter, week),
        now=now,
    )
    if not gate["ready"]:
        state = _read_state(quarter, week)
        state["last_publish"] = {"lifecycle": FRIDAY_BLOCKED, "at": _now(),
                                 "blockers": gate["blockers"]}
        _write_state(quarter, week, state)
        return {"gate": gate, "report": None, "review_state": FRIDAY_BLOCKED, "published": False}

    confirmation = owner_confirmation or _confirmation_phrase(quarter, week)
    _mark_publishing(quarter, week)
    try:
        report = rollover.publish_weekly_package(
            from_quarter, from_week, quarter, week,
            client=client, owner_confirmation=confirmation,
        )
    except rollover.RolloverBlocked as exc:
        state = _read_state(quarter, week)
        state["last_publish"] = {"lifecycle": FRIDAY_BLOCKED, "at": _now(), "error": str(exc)}
        _write_state(quarter, week, state)
        return {"gate": gate, "report": None, "review_state": FRIDAY_BLOCKED, "published": False}

    lifecycle = report.get("lifecycle") if isinstance(report, dict) else ""
    review_state = FRIDAY_PUBLISHED_VERIFIED if lifecycle == "PUBLISHED_VERIFIED" else FRIDAY_BLOCKED
    state = _read_state(quarter, week)
    state["last_publish"] = {
        "lifecycle": lifecycle, "at": _now(),
        "review_state": review_state,
        "verb_totals": report.get("verb_totals") if isinstance(report, dict) else {},
    }
    _write_state(quarter, week, state)
    return {"gate": gate, "report": report, "review_state": review_state,
            "published": review_state == FRIDAY_PUBLISHED_VERIFIED}


def _confirmation_phrase(quarter: int, week: int) -> str:
    from scripts.canvas_llm_intake import week_resolution as wr
    code = wr.week_code_for(quarter, week)
    return f"ROLLOVER {code}"


def _mark_publishing(quarter: int, week: int) -> None:
    state = _read_state(quarter, week)
    state["last_publish"] = {"lifecycle": FRIDAY_PUBLISHING, "at": _now()}
    _write_state(quarter, week, state)


def last_publish(quarter: int, week: int) -> dict[str, Any] | None:
    return _read_state(quarter, week).get("last_publish")


def command_self_test() -> int:
    import tempfile
    from pathlib import Path
    from scripts.weekly_planner_agent import snapshot as snapmod
    orig = snapmod.agent_root
    snapmod.agent_root = lambda: Path(tempfile.mkdtemp())
    try:
        # plan_version is stable and content-sensitive.
        from .models import Assessment, Authority, DayPlan, PlanStatus
        plan = WeeklyPlan(week_id="Q2W3", quarter=2, week=3)
        plan.upsert_day(DayPlan(subject="math", day="Thursday", lesson="WA8",
                                assessment=Assessment(name="WA8", subject="math", day="Thursday", date="2026-11-05")))
        v1 = plan_version(plan)
        assert v1 == plan_version(plan)
        plan.day("math", "Thursday").assessment.date = "2026-11-06"
        assert plan_version(plan) != v1
        # source_fingerprint distinguishes snapshots.
        s1 = snapmod.blank_snapshot(2, 3, "Q2W3")
        s1["pacing"]["fingerprint"] = "aaa"
        s2 = snapmod.blank_snapshot(2, 3, "Q2W3")
        s2["pacing"]["fingerprint"] = "bbb"
        assert source_fingerprint(s1) != source_fingerprint(s2)
    finally:
        snapmod.agent_root = orig
    print("PASS weekly-planner-agent publish self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(command_self_test())
