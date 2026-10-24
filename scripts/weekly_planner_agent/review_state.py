"""Friday Review state machine + approval-by-exception.

Prepares the foundation so a future LaunchAgent can invoke: source sync ->
change detection -> Friday review notification -> approved publish. This phase
does NOT install or activate automatic Friday publishing.
"""
from __future__ import annotations

from typing import Any

from .models import (
    FRIDAY_APPROVED,
    FRIDAY_BLOCKED,
    FRIDAY_BUILDING,
    FRIDAY_CHANGES_DETECTED,
    FRIDAY_PUBLISHED_VERIFIED,
    FRIDAY_READY_FOR_REVIEW,
    FridayReview,
    WeeklyPlan,
)
from .change_engine import compute_changes_since


def next_state(
    *,
    change_count: int,
    unresolved_conflicts: int,
    all_approved: bool,
    published_verified: bool = False,
) -> str:
    if published_verified:
        return FRIDAY_PUBLISHED_VERIFIED
    if unresolved_conflicts > 0:
        return FRIDAY_BLOCKED
    if change_count > 0:
        return FRIDAY_CHANGES_DETECTED
    if all_approved:
        return FRIDAY_APPROVED
    return FRIDAY_READY_FOR_REVIEW


def build_review(
    plan: WeeklyPlan,
    *,
    prior: WeeklyPlan | None,
    published_verified: bool = False,
) -> FridayReview:
    """Build the one-screen Friday review summary.

    Approval-by-exception: unchanged subjects collapse, changed subjects are
    highlighted, and prior valid approvals are preserved (invalidated only for
    affected artifacts — handled by the change engine).
    """
    changes = compute_changes_since(plan, prior)
    changed_subjects = sorted({c["subject"] for c in changes if c.get("subject")})
    unresolved = [
        {"subject": s, "reason": "assessment date changed without approval"}
        for s, days in plan.subjects.items()
        for d in days
        if d.assessment is not None and d.assessment.previous_date
    ]
    approved = all(
        record.get("page") == "approved"
        for record in plan.approval_status.values()
    )
    state = next_state(
        change_count=len(changes),
        unresolved_conflicts=len(unresolved),
        all_approved=approved and not changes,
        published_verified=published_verified,
    )
    return FridayReview(
        week_id=plan.week_id,
        state=state,
        pages_count=len(plan.subjects),
        assignments_count=len(plan.assignment_candidates),
        announcements_count=len(plan.announcement_candidates),
        reminders_count=len(plan.reminder_candidates),
        changes_since_last_review=changes,
        unresolved_conflicts=unresolved,
        source_freshness=plan.freshness,
        changed_subjects=changed_subjects,
        blocking=unresolved,
    )


def approval_by_exception(
    plan: WeeklyPlan, prior: WeeklyPlan | None, changed_subjects: list[str]
) -> dict[str, Any]:
    """Preserve prior valid approvals; only changed subjects need re-review."""
    unchanged = [s for s in plan.subjects if s not in changed_subjects]
    return {
        "changed_subjects": changed_subjects,
        "unchanged_subjects": unchanged,
        "message": (
            f"{len(changed_subjects)} item(s) changed since your last review."
            if changed_subjects else "No changes since your last review."
        ),
    }
