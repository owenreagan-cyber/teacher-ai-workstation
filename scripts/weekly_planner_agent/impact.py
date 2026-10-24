"""Impact analysis and approval invalidation.

For each detected source change, compute the dependent artifacts and invalidate
ONLY the affected subject approvals. Unaffected subjects/artifacts keep their
exact approved content and provenance. The existing approval/hash contracts are
not weakened: invalidation only flips an approval to "stale" so the guarded
publisher re-requires review, it never fabricates a new approval.
"""
from __future__ import annotations

from typing import Any

from . import change_detection as cd
from .models import SourceChangeEvent, WeeklyPlan

# Artifacts that an assessment date/identity change demonstrably depends on.
ASSESSMENT_ARTIFACTS = [
    "weekly page",
    "assessment assignment",
    "first parent announcement",
    "day-before reminder",
    "weekly update",
]


def affected_artifacts(event: SourceChangeEvent) -> list[str]:
    """Return the affected-artifact list (subject-scoped) for an event."""
    if event.affected_artifacts:
        return list(event.affected_artifacts)
    subject = event.subject.title() if event.subject else "Subject"
    if event.classification in (cd.CHANGE_ASSESSMENT_DATE, cd.CHANGE_ASSESSMENT_IDENTITY):
        return [f"{subject} {a}" for a in ASSESSMENT_ARTIFACTS]
    if event.classification in (cd.CHANGE_LESSON, cd.CHANGE_CHAPTER, cd.CHANGE_HOMEWORK, cd.CHANGE_CLASSWORK):
        return [f"{subject} weekly page"]
    if event.classification in (cd.CHANGE_ASSIGNMENT_DUE, cd.CHANGE_ASSIGNMENT_MISSING, cd.CHANGE_ASSIGNMENT_PRESENT):
        return [f"{subject} assignments"]
    if event.classification == cd.CHANGE_ANNOUNCEMENT:
        return [f"{subject} announcement"]
    if event.classification in (cd.CHANGE_REMINDER_MISSING, cd.CHANGE_REMINDER_DUPLICATED, cd.CHANGE_REMINDER_OBSOLETE):
        return [f"{subject} day-before reminder"]
    if event.classification in (cd.CHANGE_PAGE_BODY, cd.CHANGE_CANVAS_CONFLICT, cd.CHANGE_FRONT_PAGE):
        return [f"{subject} weekly page"]
    return [f"{subject} weekly page"]


def affected_subjects(events: list[SourceChangeEvent]) -> set[str]:
    subjects = {e.subject for e in events if e.subject and e.subject != "*"}
    return subjects


def invalidate_affected_approvals(plan: WeeklyPlan, events: list[SourceChangeEvent]) -> list[str]:
    """Flip affected subject/artifact approvals to "stale" (approval-by-exception).

    Returns the list of invalidated "subject:artifact" keys. Unaffected approvals
    are preserved.
    """
    invalidated: list[str] = []
    for event in events:
        subject = event.subject
        if not subject or subject == "*":
            continue
        record = plan.approval_status.setdefault(subject, {})
        artifacts = _artifacts_for_classification(event.classification)
        for artifact in artifacts:
            if record.get(artifact) == "approved":
                record[artifact] = "stale"
                invalidated.append(f"{subject}:{artifact}")
    return invalidated


def _artifacts_for_classification(classification: str) -> list[str]:
    if classification in (cd.CHANGE_ASSESSMENT_DATE, cd.CHANGE_ASSESSMENT_IDENTITY):
        return ["page", "assignments", "announcement", "assessment_reminder"]
    if classification in (cd.CHANGE_LESSON, cd.CHANGE_CHAPTER, cd.CHANGE_HOMEWORK, cd.CHANGE_CLASSWORK):
        return ["page"]
    if classification in (cd.CHANGE_ASSIGNMENT_DUE, cd.CHANGE_ASSIGNMENT_MISSING, cd.CHANGE_ASSIGNMENT_PRESENT):
        return ["assignments"]
    if classification == cd.CHANGE_ANNOUNCEMENT:
        return ["announcement"]
    if classification in (cd.CHANGE_REMINDER_MISSING, cd.CHANGE_REMINDER_DUPLICATED, cd.CHANGE_REMINDER_OBSOLETE):
        return ["assessment_reminder"]
    if classification in (cd.CHANGE_PAGE_BODY, cd.CHANGE_CANVAS_CONFLICT, cd.CHANGE_FRONT_PAGE):
        return ["page"]
    return ["page"]


def command_self_test() -> int:
    ev = SourceChangeEvent(
        source="pacing", subject="math", object_type="assessment_date",
        old_value="2026-11-05", new_value="2026-11-06",
        classification=cd.CHANGE_ASSESSMENT_DATE, affected_artifacts=[],
    )
    affected = affected_artifacts(ev)
    assert "Math weekly page" in affected and "Math day-before reminder" in affected, affected
    # Approval invalidation is subject-scoped.
    plan = WeeklyPlan(week_id="Q2W3", quarter=2, week=3)
    plan.approval_status = {
        "math": {"page": "approved", "assignments": "approved"},
        "science": {"page": "approved"},
    }
    invalidated = invalidate_affected_approvals(plan, [ev])
    assert "math:page" in invalidated and "math:assignments" in invalidated
    assert plan.approval_status["science"]["page"] == "approved"  # unaffected preserved
    print("PASS weekly-planner-agent impact self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(command_self_test())
