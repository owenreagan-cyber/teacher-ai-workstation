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
    source: str = "the pacing guide",
    already_posted: str | None = None,
    review_link: str | None = None,
) -> Notification:
    """Draft the Assessment Date Watch email (subject + body + actions)."""
    affected_lines = "\n".join(f"- {item}" for item in affected)
    posted_line = ""
    if already_posted:
        posted_line = f"\nNote: {already_posted}\n"
    review_line = f"\nReview here: {review_link}" if review_link else ""
    body = (
        f"I noticed that {assessment_name} moved from {previous_date} to "
        f"{new_date} in {source}.\n\n"
        f"This affects:\n{affected_lines}{posted_line}\n"
        f"Would you like me to update the live Canvas items and parent communications?"
        f"{review_line}"
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


def cross_source_conflict_notification(event: SourceChangeEvent) -> Notification:
    """Draft a conflict notification (delivery remains disabled)."""
    subject = event.subject.title() if event.subject else "A subject"
    observed = event.new_value or "something different"
    if event.teacher_override:
        body = (
            f"{subject}: your current plan says {event.old_value or 'as planned'}, "
            f"but Canvas currently shows {observed}. Your explicit instruction still "
            f"has higher authority. This is a read-only alert; nothing has been changed."
        )
    else:
        body = (
            f"{subject}: the current plan says {event.old_value or 'as planned'}, but "
            f"Canvas currently shows {observed}. Nothing has been changed — please review."
        )
    return Notification(
        notification_type="conflict_detected",
        subject_line=f"{subject} cross-source conflict — review",
        body=body,
        actions=["Review Changes", "Keep My Plan", "Ignore for Now"],
        requires_send=False,
    )


def friday_review_ready_notification(week_id: str, change_count: int) -> Notification:
    return Notification(
        notification_type="friday_review_ready",
        subject_line=f"{week_id} Friday review is ready",
        body=f"{change_count} item(s) changed since your last review. Review and approve when ready.",
        actions=["Open Review", "Ignore for Now"],
        requires_send=True,
    )


def friday_review_notification(
    *,
    week_id: str,
    date_range: str,
    state: str,
    change_count: int,
    conflict_count: int,
    assessment_alerts: int,
    subjects_ready: list[str],
    approved: bool,
    publish_eligible: bool,
    review_link: str,
) -> Notification:
    """The Friday approval-review email (configurable recipient, no secrets).

    Body carries only teacher-relevant fields — never Canvas tokens, raw hashes,
    credential paths, student data, or JSON payloads.
    """
    if state == "PUBLISHED_VERIFIED":
        # Suppressed by the caller; never built for an already-published week.
        return Notification(
            notification_type="friday_review_ready",
            subject_line=f"{week_id} — already published (no action needed)",
            body="Already published and verified. No approval email needed.",
            actions=[],
            requires_send=False,
        )

    if state == "BLOCKED":
        subject = "Weekly Canvas publication is blocked"
        body = (
            f"{week_id} ({date_range}) publication is blocked and will be held.\n"
            f"Reason: unresolved conflicts or source issues require your review.\n"
            f"Conflicts: {conflict_count}. Changes since last review: {change_count}.\n"
            f"Review here: {review_link}"
        )
        actions = ["Review Changes", "Keep Current Plan", "Ignore for Now"]
    else:
        # READY_FOR_REVIEW or CHANGES_AFTER_APPROVAL.
        if approved and not publish_eligible:
            subject = "Canvas plan changed after approval — review required"
        else:
            subject = "Next week's Canvas plan is ready for review"
        ready = ", ".join(subjects_ready) if subjects_ready else "none"
        body = (
            f"{week_id} ({date_range}) is ready for your Friday review.\n"
            f"Subjects ready: {ready}.\n"
            f"Changes detected: {change_count}. Unresolved conflicts: {conflict_count}.\n"
            f"Assessment-date alerts: {assessment_alerts}.\n"
            f"Publication eligible at 4:00 PM: {'yes' if publish_eligible else 'no'}.\n"
            f"Review here: {review_link}"
        )
        actions = ["Open Review", "Approve Proposed Updates", "Ignore for Now"]

    return Notification(
        notification_type="friday_review_ready",
        subject_line=subject,
        body=body,
        actions=actions,
        requires_send=True,
    )


def draft_for_event(
    event: SourceChangeEvent,
    *,
    already_posted: str | None = None,
    review_link: str | None = None,
) -> Notification | None:
    """Route a SourceChangeEvent to the right notification type."""
    if event.classification == "cross_source_conflict":
        return cross_source_conflict_notification(event)
    if event.classification == "assessment_date_changed" or event.object_type == "assessment_date":
        return assessment_date_changed_notification(
            subject=event.subject,
            assessment_name=_assessment_label(event),
            previous_date=event.old_value or "",
            new_date=event.new_value or "",
            affected=event.affected_artifacts,
            source="the pacing guide" if event.source == "pacing" else "Canvas",
            already_posted=already_posted,
            review_link=review_link,
        )
    if event.classification == "assessment_identity_changed":
        return assessment_date_changed_notification(
            subject=event.subject,
            assessment_name=event.old_value or event.subject,
            previous_date=event.old_value or "",
            new_date=event.new_value or "",
            affected=event.affected_artifacts,
            source="the pacing guide",
            already_posted=already_posted,
            review_link=review_link,
        )
    return change_event_notification(event)


def _assessment_label(event: SourceChangeEvent) -> str:
    identity = event.object_identity or ""
    parts = identity.split("|") if "|" in identity else []
    # Format: subject|day|name (or subject|day).
    if len(parts) >= 3 and parts[2]:
        return parts[2]
    if len(parts) >= 2:
        return f"{parts[0].title()} assessment on {parts[1]}"
    return f"{event.subject.title()} assessment"
