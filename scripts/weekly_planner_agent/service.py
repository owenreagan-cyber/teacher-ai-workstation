"""Weekly Planner Agent service: TODAY / WEEK PLAN / FRIDAY REVIEW / AGENT.

Reads the existing canonical Canvas Planner projection (``CanvasPlannerService``)
and layers the teacher-facing conversational agent on top. Local agent state
(conversation, applied plan, events) is persisted under
``.local/canvas-planner/agent/`` (gitignored). No Canvas writes, no scheduling.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.canvas_planner.state_root import planner_root

from . import teacher_instructions as ti
from . import reconciliation
from . import snapshot as snapmod
from . import freshness
from .change_engine import apply_instruction
from .event_store import EventStore
from .models import Assessment, Authority, Confidence, DayPlan, PlanStatus, WeeklyPlan
from .review_state import build_review, approval_by_exception

SCHOOL_YEAR = "2026-2027"
WEEKDAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def agent_root() -> Path:
    return planner_root() / "agent"


def _agent_dir(quarter: int, week: int) -> Path:
    return agent_root() / SCHOOL_YEAR / f"q{quarter}" / f"w{week}"


def _read_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def build_plan_from_planner(payload: dict[str, Any]) -> WeeklyPlan:
    """Convert a ``CanvasPlannerService.planner_week`` payload into a WeeklyPlan."""
    week = payload.get("week") or {}
    status = payload.get("status") or {}
    plan = WeeklyPlan(
        week_id=week.get("code") or "UNKNOWN",
        quarter=week.get("quarter") or 0,
        week=week.get("number") or 0,
        date_range=week.get("date_range") or {},
    )
    plan.freshness = {
        "pacing": payload.get("source", {}).get("synced_at"),
        "canvas": None,
    }
    plan.source_provenance = {
        "name": payload.get("source", {}).get("name"),
        "tab": payload.get("source", {}).get("tab"),
        "spreadsheet_id": payload.get("source", {}).get("spreadsheet_id"),
    }
    plan.announcement_candidates = []
    plan.assignment_candidates = []
    plan.reminder_candidates = []
    for course in payload.get("courses") or []:
        subject = course.get("id") or "unknown"
        for day in course.get("days") or []:
            in_class = day.get("in_class") or []
            at_home = day.get("at_home")
            assessment = _assessment_for(course, day)
            plan.upsert_day(DayPlan(
                subject=subject,
                day=day.get("day") or "",
                date=day.get("date"),
                lesson=in_class[0] if in_class else None,
                classwork=list(in_class),
                homework=[at_home] if at_home else [],
                assessment=assessment,
                status=(PlanStatus.PLANNED if day.get("edited") else PlanStatus.CONFIRMED_SOURCE),
                authority=Authority.OWNER_INSTRUCTION if day.get("edited") else Authority.VERIFIED_PACING,
                confidence=Confidence.CONFIRMED,
                source_value=day.get("sheet_says"),
            ))
            for a in day.get("assignments") or []:
                plan.assignment_candidates.append({"subject": subject, "day": day.get("day"), **a})
            for r in day.get("reminders") or []:
                plan.reminder_candidates.append({"subject": subject, "day": day.get("day"), **r})
        for ann in [course.get("announcement")] if course.get("announcement") else []:
            plan.announcement_candidates.append({"subject": subject, "title": ann.get("title")})
        approvals = course.get("approvals") or {}
        for artifact, record in approvals.items():
            if isinstance(record, dict) and record.get("state") == "APPROVED":
                plan.approval_status.setdefault(subject, {})[artifact] = "approved"
    return plan


def _assessment_for(course: dict[str, Any], day: dict[str, Any]) -> Assessment | None:
    """Derive a planned assessment from reminder candidates (best-effort)."""
    for reminder in day.get("reminders") or []:
        title = str(reminder.get("title") or "")
        if "Assessment" in title or "Test" in title:
            return Assessment(
                name=title,
                subject=course.get("id") or "unknown",
                day=day.get("day"),
                date=day.get("date"),
                authority=Authority.VERIFIED_PACING,
                confidence=Confidence.CONFIRMED,
            )
    return None


def load_plan(quarter: int, week: int) -> WeeklyPlan | None:
    """Load the persisted agent plan, else build from the canonical projection."""
    d = _agent_dir(quarter, week)
    data = _read_json(d / "plan.json", None)
    if isinstance(data, dict) and data.get("week_id"):
        return _from_dict(data)
    try:
        from scripts.canvas_planner.service import CanvasPlannerService
        payload = CanvasPlannerService().planner_week(quarter, week)
    except Exception:  # noqa: BLE001 — no packet yet -> empty plan
        return None
    return build_plan_from_planner(payload)


def save_plan(quarter: int, week: int, plan: WeeklyPlan) -> None:
    _write_json(_agent_dir(quarter, week) / "plan.json", plan.to_dict())


def _from_dict(data: dict[str, Any]) -> WeeklyPlan:
    plan = WeeklyPlan(
        week_id=data.get("week_id") or "UNKNOWN",
        quarter=data.get("quarter") or 0,
        week=data.get("week") or 0,
        date_range=data.get("date_range") or {},
        homeroom_items=data.get("homeroom_items") or [],
        assignment_candidates=data.get("assignment_candidates") or [],
        announcement_candidates=data.get("announcement_candidates") or [],
        reminder_candidates=data.get("reminder_candidates") or [],
        source_provenance=data.get("source_provenance") or {},
        freshness=data.get("freshness") or {},
        approval_status=data.get("approval_status") or {},
        change_history=data.get("change_history") or [],
    )
    for subject, days in (data.get("subjects") or {}).items():
        for d in days:
            assessment = None
            if d.get("assessment"):
                assessment = Assessment(
                    name=d["assessment"].get("name", ""),
                    subject=d["assessment"].get("subject", subject),
                    day=d["assessment"].get("day"),
                    date=d["assessment"].get("date"),
                    previous_date=d["assessment"].get("previous_date"),
                    authority=Authority(d["assessment"].get("authority", 2)),
                    confidence=d["assessment"].get("confidence", Confidence.CONFIRMED),
                )
            plan.upsert_day(DayPlan(
                subject=subject,
                day=d.get("day", ""),
                date=d.get("date"),
                lesson=d.get("lesson"),
                classwork=list(d.get("classwork") or []),
                homework=list(d.get("homework") or []),
                assessment=assessment,
                status=d.get("status", PlanStatus.PLANNED),
                authority=Authority(d.get("authority", 2)),
                confidence=d.get("confidence", Confidence.CONFIRMED),
                teacher_override=d.get("teacher_override"),
                source_value=d.get("source_value"),
            ))
    return plan


def instruct(quarter: int, week: int, text: str) -> dict[str, Any]:
    """Translate a teacher instruction, apply it, and persist conversation + plan."""
    plan = load_plan(quarter, week) or WeeklyPlan(
        week_id=f"Q{quarter}W{week}", quarter=quarter, week=week
    )
    parsed = ti.parse(text)
    d = _agent_dir(quarter, week)
    if not parsed.matched:
        _append_conversation(d, "teacher", text, parsed.to_dict(), None)
        return {"matched": False, "reply": parsed.reply, "plan": plan.to_dict()}

    op = parsed.ops[0]

    # Subject-less assessment-date keep binds to the focus subject (conversational).
    if op.intent == ti.KEEP_ASSESSMENT_DATE and op.subject is None:
        focus = _get_focus(quarter, week)
        op.subject = focus.get("focus_subject")

    # Conversation-level actions against the detected change events.
    if op.intent == ti.CONFIRM:
        focus = _get_focus(quarter, week)
        event_id = focus.get("focus_event_id")
        if event_id:
            resolved = resolve_event(quarter, week, event_id, action="prepare_plan")
            _append_conversation(d, "teacher", text, parsed.to_dict(), resolved)
            return {
                "matched": True,
                "reply": "Done. I've prepared the revised plan. Nothing live has changed.",
                "changes": [{"type": "confirm_prepare_plan", "event_id": event_id}],
                "affected_artifacts": [],
                "events": [],
                "plan": resolved.get("plan", plan.to_dict()),
            }
        _append_conversation(d, "teacher", text, parsed.to_dict(), None)
        return {"matched": True, "reply": "Got it. I'll apply the proposed changes.", "plan": plan.to_dict()}

    if op.intent == ti.UPDATE_WITHOUT_REMINDER:
        focus = _get_focus(quarter, week)
        event_id = focus.get("focus_event_id")
        if event_id:
            resolved = resolve_event(quarter, week, event_id, action="prepare_plan")
        else:
            resolved = {}
        _append_conversation(d, "teacher", text, parsed.to_dict(), resolved)
        return {
            "matched": True,
            "reply": "Done. I've prepared the revised plan and marked the reminder for your review. Nothing live has changed.",
            "changes": [{"type": "update_without_reminder", "event_id": event_id, "hold_reminder": True}],
            "affected_artifacts": [],
            "events": [],
            "plan": resolved.get("plan", plan.to_dict()),
        }

    if op.intent == ti.SHOW_ANNOUNCEMENT:
        _append_conversation(d, "teacher", text, parsed.to_dict(), None)
        return {
            "matched": True,
            "reply": "Here is the exact announcement parents would receive.",
            "announcement_preview": _latest_announcement_draft(quarter, week),
            "plan": plan.to_dict(),
        }

    if op.intent == ti.KEEP_ASSESSMENT_DATE:
        focus = _get_focus(quarter, week)
        event_id = focus.get("focus_event_id")
        if event_id:
            resolved = resolve_event(quarter, week, event_id, action="override_keep_current")
        else:
            resolved = {}
        _append_conversation(d, "teacher", text, parsed.to_dict(), resolved)
        return {
            "matched": True,
            "reply": (f"Recorded — I kept {op.day} as your override for "
                      f"{op.subject.title() if op.subject else 'the subject'}. "
                      f"The pacing change remains visible but won't override you."),
            "changes": [{"type": "override_keep_current", "event_id": event_id, "day": op.day}],
            "affected_artifacts": [],
            "events": [],
            "plan": resolved.get("plan", plan.to_dict()),
        }

    result = apply_instruction(plan, op) if op else None
    if result is None or not result.applied:
        _append_conversation(d, "teacher", text, parsed.to_dict(), None)
        return {"matched": False, "reply": parsed.reply, "plan": plan.to_dict()}

    save_plan(quarter, week, plan)
    _append_conversation(d, "teacher", text, parsed.to_dict(), result.to_dict())
    return {
        "matched": True,
        "reply": result.reply,
        "changes": result.changes,
        "affected_artifacts": result.affected_artifacts,
        "events": [e.to_dict() for e in result.events],
        "plan": plan.to_dict(),
    }


def _latest_announcement_draft(quarter: int, week: int) -> dict[str, Any] | None:
    from . import notification_model as nm
    store = EventStore(quarter, week)
    attention = [e for e in store.all() if e.get("family_comms_affected")]
    if not attention:
        return None
    event = attention[0]
    from .models import SourceChangeEvent
    source_event = SourceChangeEvent(
        source=event.get("source", ""), subject=event.get("subject", ""),
        object_type=event.get("object_type", ""),
        old_value=event.get("old_value"), new_value=event.get("new_value"),
        classification=event.get("classification", ""),
        affected_artifacts=event.get("affected_artifacts") or [],
        family_comms_affected=True, week_id=event.get("week_id", ""),
    )
    notification = nm.draft_for_event(source_event, review_link="#agent")
    return notification.to_dict() if notification else None


def _append_conversation(d: Path, role: str, text: str, parsed: Any, result: Any) -> None:
    d.mkdir(parents=True, exist_ok=True)
    with (d / "conversation.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({"role": role, "text": text, "parsed": parsed, "result": result, "at": _now()}) + "\n")


def conversation(quarter: int, week: int) -> list[dict[str, Any]]:
    path = _agent_dir(quarter, week) / "conversation.jsonl"
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def week_plan(quarter: int, week: int) -> dict[str, Any]:
    plan = load_plan(quarter, week)
    if plan is None:
        return {"week_id": f"Q{quarter}W{week}", "subjects": {}}
    return plan.to_dict()


def friday_review(quarter: int, week: int) -> dict[str, Any]:
    plan = load_plan(quarter, week)
    if plan is None:
        plan = WeeklyPlan(week_id=f"Q{quarter}W{week}", quarter=quarter, week=week)
    prior = None  # prior-snapshot diffing is wired to the planner in a later phase
    review = build_review(plan, prior=prior)
    payload = review.to_dict()
    # Layer on the publish gate + schedule + delivery config (concise, no hashes).
    from . import publish as pub
    from . import schedule_config
    gate = pub.build_publish_gate(quarter, week, plan=plan)
    last = pub.last_publish(quarter, week)
    payload["gate"] = {"ready": gate["ready"], "blockers": gate["blockers"]}
    payload["approval"] = (pub.load_approval(quarter, week).to_dict()
                           if pub.load_approval(quarter, week) else None)
    payload["last_publish"] = last
    payload["schedule"] = schedule_config.schedule()
    payload["delivery"] = schedule_config.delivery_config()
    # Derive a single honest review state (no false "APPROVED" when blocked).
    from .models import FRIDAY_APPROVED, FRIDAY_BLOCKED, FRIDAY_READY_FOR_REVIEW, FRIDAY_PUBLISHED_VERIFIED
    if last and last.get("review_state") == FRIDAY_PUBLISHED_VERIFIED:
        payload["state"] = FRIDAY_PUBLISHED_VERIFIED
    elif gate["ready"]:
        payload["state"] = FRIDAY_APPROVED
    else:
        needs_review = any(
            ("approv" in b) or ("changed after approval" in b) for b in gate["blockers"]
        )
        payload["state"] = FRIDAY_READY_FOR_REVIEW if needs_review else FRIDAY_BLOCKED
    return payload


def today(quarter: int, week: int) -> dict[str, Any]:
    plan = load_plan(quarter, week)
    if plan is None:
        plan = WeeklyPlan(week_id=f"Q{quarter}W{week}", quarter=quarter, week=week)
    review = build_review(plan, prior=None)
    changed = approval_by_exception(plan, None, review.changed_subjects)
    return {
        "week_id": plan.week_id,
        "changes_detected": len(review.changes_since_last_review),
        "needs_attention": review.changed_subjects,
        "source_freshness": plan.freshness,
        "friday_review_state": review.state,
        "message": changed["message"],
    }


def agent_view(quarter: int, week: int) -> dict[str, Any]:
    plan = load_plan(quarter, week)
    return {
        "week_id": f"Q{quarter}W{week}",
        "conversation": conversation(quarter, week),
        "plan": (plan or WeeklyPlan(week_id=f"Q{quarter}W{week}", quarter=quarter, week=week)).to_dict(),
        "changes": changes(quarter, week),
    }


# --------------------------------------------------------------------------- #
# Persistent change detection + reconciliation
# --------------------------------------------------------------------------- #
def _context_path(quarter: int, week: int) -> Path:
    return _agent_dir(quarter, week) / "context.json"


def _get_focus(quarter: int, week: int) -> dict[str, Any]:
    return _read_json(_context_path(quarter, week), {})


def _set_focus(quarter: int, week: int, *, event_id: str | None = None, subject: str | None = None) -> None:
    data = _get_focus(quarter, week)
    if event_id is not None:
        data["focus_event_id"] = event_id
    if subject is not None:
        data["focus_subject"] = subject
    _write_json(_context_path(quarter, week), data)


def sync(quarter: int, week: int, *, pacing: dict[str, Any] | None = None,
         canvas: dict[str, Any] | None = None) -> dict[str, Any]:
    """Run one observe→detect cycle. Persists the snapshot + events + plan."""
    plan = load_plan(quarter, week) or WeeklyPlan(
        week_id=f"Q{quarter}W{week}", quarter=quarter, week=week
    )
    report = reconciliation.sync_and_detect(
        quarter, week, week_id=plan.week_id, pacing=pacing, canvas=canvas, plan=plan
    )
    if plan is not None and report["invalidated_approvals"]:
        save_plan(quarter, week, plan)
    # Set focus to the top unresolved attention event (for conversational binding).
    attention = report.get("attention") or []
    if attention:
        top = attention[0]
        _set_focus(quarter, week, event_id=top.get("event_id"), subject=top.get("subject"))
    return report


def sync_from_plan(quarter: int, week: int) -> dict[str, Any]:
    """Convenience: sync pacing from the current agent plan (canvas unavailable)."""
    plan = load_plan(quarter, week)
    if plan is None:
        return {"baseline": True, "week_id": f"Q{quarter}W{week}", "changes": [], "events": [],
                "attention": [], "notifications": [], "affected_subjects": [],
                "invalidated_approvals": [], "freshness": {},
                "canvas_writes": 0, "notifications_delivered": 0}
    identity = {
        "name": plan.source_provenance.get("name"),
        "tab": plan.source_provenance.get("tab"),
        "spreadsheet_id": plan.source_provenance.get("spreadsheet_id"),
    }
    pacing = {"identity": identity, "cells": reconciliation.pacing_cells_from_plan(plan)}
    return sync(quarter, week, pacing=pacing, canvas=None)


def changes(quarter: int, week: int) -> dict[str, Any]:
    """Return the durable change/event history + freshness for the UI."""
    store = EventStore(quarter, week)
    events = store.all()
    unresolved = store.unresolved()
    try:
        snap_data = snapmod.load(quarter, week)
    except Exception:  # noqa: BLE001
        snap_data = None
    return {
        "week_id": f"Q{quarter}W{week}",
        "events": events,
        "unresolved": unresolved,
        "attention": [e for e in events if e.get("family_comms_affected") or e.get("requires_teacher_approval")],
        "freshness": {
            "pacing": freshness.freshness_state((snap_data or {}).get("pacing", {}).get("observed_at")),
            "canvas": freshness.freshness_state((snap_data or {}).get("canvas", {}).get("observed_at")),
        },
        "focus": _get_focus(quarter, week),
    }


def resolve_event(quarter: int, week: int, event_id: str, action: str) -> dict[str, Any]:
    """Resolve an event (durable) and apply the resulting plan change."""
    store = EventStore(quarter, week)
    event = next((e for e in store.all() if e.get("event_id") == event_id), None)
    if event is None:
        return {"error": "event not found", "event_id": event_id}
    resolved = store.resolve(event_id, action=action)
    plan = load_plan(quarter, week) or WeeklyPlan(
        week_id=f"Q{quarter}W{week}", quarter=quarter, week=week
    )
    _apply_event_to_plan(plan, event, action)
    save_plan(quarter, week, plan)
    return {"resolved": resolved, "plan": plan.to_dict()}


def _apply_event_to_plan(plan: WeeklyPlan, event: dict[str, Any], action: str) -> None:
    cls = event.get("classification")
    subject = event.get("subject")
    if cls == "assessment_date_changed" and subject:
        dp = _find_assessment_day(plan, subject)
        if dp is not None and dp.assessment is not None:
            if action in ("approve_updates", "prepare_plan"):
                dp.assessment.previous_date = dp.assessment.date
                dp.assessment.date = event.get("new_value")
                dp.assessment.authority = Authority.VERIFIED_PACING
                dp.authority = Authority.VERIFIED_PACING
            elif action == "override_keep_current":
                dp.assessment.date = event.get("old_value")
                dp.assessment.authority = Authority.OWNER_INSTRUCTION
                dp.teacher_override = {
                    "assessment_date": event.get("old_value"),
                    "kind": "override_keep_current",
                }
                dp.authority = Authority.OWNER_INSTRUCTION
    elif cls in ("lesson_changed", "homework_changed", "classwork_changed", "chapter_changed") and subject:
        dp = _find_day_by_identity(plan, subject, event.get("object_identity"))
        if dp is not None:
            if action == "override_keep_current":
                dp.teacher_override = {"kind": "override_keep_current", "keep": event.get("old_value")}
                dp.authority = Authority.OWNER_INSTRUCTION
            elif action in ("approve_updates", "prepare_plan"):
                dp.lesson = event.get("new_value") if cls == "lesson_changed" else dp.lesson
                dp.authority = Authority.VERIFIED_PACING


def _find_assessment_day(plan: WeeklyPlan, subject: str) -> DayPlan | None:
    for day in plan.subjects.get(subject, []):
        if day.assessment is not None:
            return day
    return None


def _find_day_by_identity(plan: WeeklyPlan, subject: str, identity: str | None) -> DayPlan | None:
    if identity and "|" in (identity or ""):
        day = identity.split("|", 1)[1].split("|", 1)[0]
        return plan.day(subject, day)
    return None


# --------------------------------------------------------------------------- #
# Approval -> guarded publish + notification delivery
# --------------------------------------------------------------------------- #
def approve_plan(quarter: int, week: int) -> dict[str, Any]:
    """Record a plan-version-bound approval (reuses canonical per-course approval)."""
    from . import publish as pub
    return pub.approve_plan(quarter, week)


def publish_gate(quarter: int, week: int) -> dict[str, Any]:
    """Return the agent-level publish gate (readiness + blockers)."""
    from . import publish as pub
    return pub.build_publish_gate(quarter, week)


def publish_now(quarter: int, week: int, *, client: Any,
                owner_confirmation: str | None = None) -> dict[str, Any]:
    """Delegate publication to the existing guarded rollover (agent gate first)."""
    from . import publish as pub
    return pub.publish(quarter, week, client=client, owner_confirmation=owner_confirmation)


def notifications(quarter: int, week: int) -> list[dict[str, Any]]:
    """Return the local notification outbox (delivered/queued records)."""
    from . import delivery
    return delivery.read_outbox()


def deliver_notification(quarter: int, week: int, *, event_id: str, mode: str | None = None) -> dict[str, Any]:
    """Draft + deliver a notification for one event through the chosen sink.

    ``preview`` sends nothing; ``local`` writes the outbox; ``email`` is
    disabled by default. Returns the notification record (status + error).
    """
    from . import delivery
    from . import notification_model as nm
    from .models import SourceChangeEvent

    store = EventStore(quarter, week)
    event = next((e for e in store.all() if e.get("event_id") == event_id), None)
    if event is None:
        return {"error": "event not found", "event_id": event_id}

    source_event = SourceChangeEvent(
        source=event.get("source", ""), subject=event.get("subject", ""),
        object_type=event.get("object_type", ""),
        old_value=event.get("old_value"), new_value=event.get("new_value"),
        classification=event.get("classification", ""),
        object_identity=event.get("object_identity"),
        affected_artifacts=event.get("affected_artifacts") or [],
        family_comms_affected=bool(event.get("family_comms_affected")),
        week_id=event.get("week_id", ""),
    )
    draft = nm.draft_for_event(source_event, review_link="#agent")
    if draft is None:
        return {"error": "no notification draft for this event", "event_id": event_id}

    record = delivery.make_record(
        notification_type=draft.notification_type,
        subject=draft.subject_line,
        body=draft.body,
        actions=list(draft.actions),
        review_link="#agent",
        related_event_ids=[event_id],
        plan_version=event.get("plan_version") or "",
    )
    return delivery.deliver(record, mode=mode)


def command_self_test() -> int:
    """Static no-network self-test for the agent package."""
    from pathlib import Path as _P
    pkg = _P(__file__).resolve().parent
    source = "".join(f.read_text(encoding="utf-8") for f in sorted(pkg.glob("*.py")))
    # Tokens are split so the scanner's own source never self-matches.
    tokens = [
        "request" + "s.",
        "urllib" + ".request",
        "canvas_" + "writer",
        "canvas_" + "connector",
        "gsp" + "read",
        "Phase22Live" + "CanvasClient",
        "create_" + "announcement",
        "update_" + "page",
    ]
    for tok in tokens:
        assert tok not in source, f"forbidden token {tok!r} in agent package"
    print("PASS weekly-planner-agent self-test (no network/write tokens)")
    return 0


if __name__ == "__main__":
    raise SystemExit(command_self_test())
