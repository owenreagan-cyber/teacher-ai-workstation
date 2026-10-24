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
from .change_engine import apply_instruction
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

    result = apply_instruction(plan, parsed.ops[0]) if parsed.ops else None
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
    return review.to_dict()


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
    }


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
