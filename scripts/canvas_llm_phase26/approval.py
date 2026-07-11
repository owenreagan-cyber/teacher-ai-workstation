from __future__ import annotations

from typing import Any


REQUIRED_SUBJECTS = [
    "math",
    "reading-spelling",
    "language-arts",
    "homeroom",
]


def subject_approval_state(subject: dict[str, Any], approval_rows: list[dict[str, Any]], unresolved_count: int, blocked_count: int) -> dict[str, Any]:
    active = [row for row in approval_rows if int(row.get("active", 0)) == 1 and row.get("scope") == subject["subject"]]
    approved = bool(active)
    if blocked_count:
        status = "Blocked"
    elif unresolved_count:
        status = "Needs Review"
    elif approved:
        status = "Approved"
    else:
        status = "Ready"
    return {
        "subject": subject["subject"],
        "status": status,
        "approved": approved,
        "activeApproval": active[-1] if active else None,
    }


def can_approve_subject(subject: dict[str, Any]) -> bool:
    return subject.get("readinessState") != "Blocked"


def can_approve_full_week(subjects: list[dict[str, Any]]) -> bool:
    return all(subject.get("approvalState") == "Approved" for subject in subjects if subject.get("assignmentPolicy", "enabled") != "disabled")


def build_approval_panel(subjects: list[dict[str, Any]], approval_rows: list[dict[str, Any]]) -> dict[str, Any]:
    subject_approvals: list[dict[str, Any]] = []
    for subject in subjects:
        unresolved_count = len(subject.get("unresolvedResources", []))
        blocked_count = len(subject.get("blockedResources", []))
        subject_approvals.append(
            {
                **subject_approval_state(subject, approval_rows, unresolved_count, blocked_count),
                "canApprove": can_approve_subject(subject),
                "unresolvedCount": unresolved_count,
                "blockedCount": blocked_count,
            }
        )
    return {
        "subjectApprovals": subject_approvals,
        "fullWeekApprovalReady": can_approve_full_week(subjects),
        "fullWeekApprovalState": "Approved" if can_approve_full_week(subjects) else "Not approved",
    }

