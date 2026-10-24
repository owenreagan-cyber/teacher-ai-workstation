"""Assessment Date Watch.

When the pacing source or verified Canvas state indicates a test/assessment date
changed and the change was not already explicitly approved by Owen, the agent
must create a teacher-attention event and recompute the proposed plan and
affected drafts. It must NOT silently rewrite live family-facing communications.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .authority import Conflict
from .models import Assessment, Authority, SourceChangeEvent, WeeklyPlan


@dataclass
class WatchResult:
    attention_needed: bool
    subject: str
    assessment_name: str
    previous_date: str | None
    new_date: str | None
    affected: list[str]
    message: str
    ask: str
    event: SourceChangeEvent | None = None
    plan: WeeklyPlan | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "attention_needed": self.attention_needed,
            "subject": self.subject,
            "assessment_name": self.assessment_name,
            "previous_date": self.previous_date,
            "new_date": self.new_date,
            "affected": self.affected,
            "message": self.message,
            "ask": self.ask,
            "event": self.event.to_dict() if self.event else None,
        }


def watch_assessment_date(
    plan: WeeklyPlan,
    *,
    subject: str,
    assessment_name: str,
    previous_date: str | None,
    new_date: str | None,
    approved: bool = False,
) -> WatchResult:
    """Detect an unapproved assessment date change and surface it.

    Returns a WatchResult with ``attention_needed=True`` when the date changed
    and Owen has not already approved it. The caller keeps ownership of live
    Canvas/family communication writes (this function never writes).
    """
    changed = previous_date is not None and new_date is not None and previous_date != new_date
    if not changed:
        return WatchResult(
            attention_needed=False, subject=subject, assessment_name=assessment_name,
            previous_date=previous_date, new_date=new_date, affected=[],
            message="", ask="",
        )

    affected = [
        f"{subject.title()} weekly page",
        f"{subject.title()} assessment assignment",
        f"{subject.title()} first parent announcement",
        f"{subject.title()} day-before reminder",
    ]

    if approved:
        return WatchResult(
            attention_needed=False, subject=subject, assessment_name=assessment_name,
            previous_date=previous_date, new_date=new_date, affected=affected,
            message=f"{assessment_name} date change was already approved by Owen.",
            ask="",
        )

    # Recompute the proposed plan: update the assessment's planned date locally.
    recomputed = plan
    day_plan = next(
        (d for days in plan.subjects.values() for d in days if d.assessment is not None),
        None,
    )
    if day_plan is not None and day_plan.assessment is not None:
        day_plan.assessment.previous_date = previous_date
        day_plan.assessment.date = new_date
        day_plan.assessment.authority = Authority.VERIFIED_PACING

    event = SourceChangeEvent(
        source="pacing_or_canvas",
        subject=subject,
        object_type="assessment_date",
        old_value=previous_date,
        new_value=new_date,
        severity="high",
        affected_artifacts=affected,
        requires_teacher_approval=True,
        live_canvas_stale=True,
        family_comms_affected=True,
    )

    message = (
        f"I noticed a test date changed: {assessment_name} moved from "
        f"{previous_date} to {new_date}."
    )
    ask = "Would you like me to update the live Canvas items and parent communications?"

    return WatchResult(
        attention_needed=True,
        subject=subject,
        assessment_name=assessment_name,
        previous_date=previous_date,
        new_date=new_date,
        affected=affected,
        message=message,
        ask=ask,
        event=event,
        plan=recomputed,
    )


def conflict_to_watch(conflict: Conflict, assessment_name: str) -> WatchResult:
    """Bridge: surface an authority Conflict about an assessment date as a watch event."""
    return watch_assessment_date(
        WeeklyPlan(week_id="", quarter=0, week=0),
        subject=conflict.subject,
        assessment_name=assessment_name,
        previous_date=conflict.current,
        new_date=conflict.incoming,
    )
