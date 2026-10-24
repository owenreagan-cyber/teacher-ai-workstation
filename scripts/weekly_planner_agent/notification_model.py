"""Internal notification model + email drafting (delivery wired later if needed).

Notification types: assessment date changed, pacing changed, Canvas changed
directly, conflict detected, Friday review ready, approval needed, publish
completed, publish blocked.
"""
from __future__ import annotations

from typing import Any

from .models import Notification, SourceChangeEvent

NOTIFICATION_TYPES = (
    "assessment_date_changed",
    "pacing_changed",
    "canvas_changed_directly",
    "conflict_detected",
    "friday_review_ready",
    "approval_needed",
    "publish_completed",
    "publish_blocked",
)


def assessment_date_changed_notification(
    *,
    subject: str,
    assessment_name: str,
    previous_date: str,
    new_date: str,
    affected: list[str],
) -> Notification:
    """Draft the Assessment Date Watch email (subject + body + actions)."""
    affected_lines = "\n".join(f"- {item}" for item in affected)
    body = (
        f"I noticed that {assessment_name} moved from {previous_date} to "
        f"{new_date} in the pacing guide.\n\n"
        f"This affects:\n{affected_lines}\n\n"
        f"Would you like me to update the live Canvas items and parent communications?"
    )
    return Notification(
        notification_type="assessment_date_changed",
        subject_line=f"{subject.title()} test date changed — review Canvas updates",
        body=body,
        actions=["Approve Updates", "Review Changes", "Ignore for Now"],
        requires_send=True,
    )


def change_event_notification(event: SourceChangeEvent) -> Notification:
    return Notification(
        notification_type="pacing_changed",
        subject_line=f"{event.subject.title()} changed",
        body=f"{event.object_type} changed from {event.old_value!r} to {event.new_value!r}.",
        actions=["Review Changes"],
        requires_send=event.family_comms_affected,
    )


def friday_review_ready_notification(week_id: str, change_count: int) -> Notification:
    return Notification(
        notification_type="friday_review_ready",
        subject_line=f"{week_id} Friday review is ready",
        body=f"{change_count} item(s) changed since your last review. Review and approve when ready.",
        actions=["Open Review", "Ignore for Now"],
        requires_send=True,
    )


def draft_for_event(event: SourceChangeEvent) -> Notification | None:
    """Route a SourceChangeEvent to the right notification type."""
    if event.object_type == "assessment_date" and event.family_comms_affected:
        return assessment_date_changed_notification(
            subject=event.subject,
            assessment_name=f"{event.subject.title()} assessment",
            previous_date=event.old_value or "",
            new_date=event.new_value or "",
            affected=event.affected_artifacts,
        )
    return change_event_notification(event)
