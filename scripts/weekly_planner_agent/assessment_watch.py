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


# --------------------------------------------------------------------------- #
# Cross-source Assessment Date Watch (live pacing vs verified Canvas)
# --------------------------------------------------------------------------- #

_ANNOUNCEMENT_HINTS = ("reminder", "assessment", "test")
_CORRECTION_SOURCES = ("canvas", "pacing")


def _assessment_identity_token(name: str | None) -> str:
    """A stable, minimal token used to match a pacing assessment to Canvas.

    Extracts the trailing numeric/identity fragment (e.g. "Assessment 8" -> "8",
    "Written Assessment 8" -> "8"). Returns the lowercased full name as a
    fallback so matching never silently drops an assessment.
    """
    text = (name or "").strip()
    if not text:
        return ""
    import re
    nums = re.findall(r"\d+", text)
    return nums[-1] if nums else text.lower()


def _matching_assignment(course: dict[str, Any], assessment_name: str | None) -> dict[str, Any] | None:
    token = _assessment_identity_token(assessment_name)
    for a in (course.get("assignments") or []):
        a_name = a.get("name") or a.get("title") or ""
        if not token:
            continue
        if token in _assessment_identity_token(a_name):
            return a
        # Whole-name fallback (e.g. exact canonical title match).
        if assessment_name and assessment_name.lower() in a_name.lower():
            return a
    return None


def _matching_reminder(course: dict[str, Any]) -> dict[str, Any] | None:
    for a in (course.get("announcements") or []):
        title = (a.get("title") or "").lower()
        if any(hint in title for hint in _ANNOUNCEMENT_HINTS):
            return a
    return None


def _first_announcement(course: dict[str, Any]) -> dict[str, Any] | None:
    for a in (course.get("announcements") or []):
        title = (a.get("title") or "").lower()
        if not any(hint in title for hint in _ANNOUNCEMENT_HINTS):
            return a
    return None


def _posted_state(announcement: dict[str, Any] | None) -> bool:
    """True when an announcement is already posted (not merely scheduled)."""
    if not announcement:
        return False
    from .canvas_observation import posted_vs_scheduled
    return posted_vs_scheduled(announcement) == "POSTED"


def build_watch(
    events: list[Any],
    canvas_observation: dict[str, Any] | None,
    *,
    plan: WeeklyPlan | None = None,
) -> list[dict[str, Any]]:
    """Enrich assessment-date change events into exactly ONE watch entry each.

    For every ``assessment_date_changed`` / ``assessment_identity_changed``
    event, produce a single teacher-attention record carrying the full detail
    Owen needs to decide: old/new dates, the source that changed, the current
    Canvas state (assignment, first announcement, day-before reminder), whether
    anything already posted, the recommended communication action, and the ask.

    No live Canvas write happens here; this is read-only enrichment.
    """
    from . import communication_rules as cr

    courses = (canvas_observation or {}).get("courses") or {}
    watch: list[dict[str, Any]] = []

    def _val(item: Any, key: str, default: Any = None) -> Any:
        if isinstance(item, dict):
            return item.get(key, default)
        return getattr(item, key, default)

    for event in events:
        classification = _val(event, "classification")
        if classification not in ("assessment_date_changed", "assessment_identity_changed"):
            continue

        subject = _val(event, "subject")
        old_value = _val(event, "old_value")
        new_value = _val(event, "new_value")
        event_id = _val(event, "event_id")
        affected = list(_val(event, "affected_artifacts") or [])
        object_identity = _val(event, "object_identity") or ""

        # Assessment label from the event identity (subject|day|name).
        parts = object_identity.split("|") if "|" in object_identity else []
        assessment_name = parts[2] if len(parts) >= 3 and parts[2] else (
            f"{str(subject).title()} assessment"
        )

        course = courses.get(subject) or {}
        assignment = _matching_assignment(course, assessment_name)
        reminder = _matching_reminder(course)
        first = _first_announcement(course)

        reminder_posted = _posted_state(reminder)
        first_posted = _posted_state(first)
        action = cr.handle_date_change(
            first_announcement_posted=first_posted,
            reminder_posted=reminder_posted,
        )

        canvas_state: dict[str, Any] = {
            "assignment": {
                "name": (assignment or {}).get("name") or (assignment or {}).get("title"),
                "due_at": (assignment or {}).get("due_at"),
            } if assignment else None,
            "first_announcement": {
                "title": first.get("title"),
                "posted": first_posted,
                "delayed_post_at": first.get("delayed_post_at"),
            } if first else None,
            "day_before_reminder": {
                "title": reminder.get("title"),
                "posted": reminder_posted,
                "delayed_post_at": reminder.get("delayed_post_at"),
            } if reminder else None,
            "front_page": (course.get("front_page") or {}).get("title")
            or (course.get("front_page") or {}).get("page_id"),
        }

        watch.append({
            "assessment_name": assessment_name,
            "subject": subject,
            "old_date": old_value,
            "new_date": new_value,
            "source_changed": "the pacing guide" if _val(event, "source") == "pacing" else "Canvas",
            "affected": affected,
            "canvas_state": canvas_state,
            "already_posted": {"first_announcement": first_posted, "reminder": reminder_posted},
            "recommended_action": action.to_dict(),
            "ask": "Would you like me to prepare the updated Canvas items and parent communications?",
            "event_id": event_id,
            "requires_teacher_approval": bool(_val(event, "requires_teacher_approval", True)),
        })

    return watch
