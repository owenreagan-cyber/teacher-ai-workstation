from __future__ import annotations

from .approval_workflow import WorkflowState
from .lesson_package import LessonPackagePlan
from .models import CheckStatus


def _category_status(checks: list[tuple[str, CheckStatus]]) -> str:
    statuses = [status for _, status in checks]
    if any(s == CheckStatus.FAIL for s in statuses):
        return "FAIL"
    if any(s == CheckStatus.WARN for s in statuses):
        return "WARN"
    return "PASS"


def format_lesson_package_status(package: LessonPackagePlan) -> str:
    validation = package.validation_summary
    categories = {
        "Lesson": CheckStatus.PASS if package.metadata.get("title") else CheckStatus.WARN,
        "Objectives": _scope_status(validation, ("objective", "objectives")),
        "Critical Content": _scope_status(validation, ("critical", "content")),
        "Vocabulary": CheckStatus.PASS if package.vocabulary else CheckStatus.WARN,
        "Instructional Sequence": _scope_status(validation, ("sequence", "instructional")),
        "Artifact Plan": _scope_status(validation, ("artifact", "plan")),
        "Teacher Approval": _approval_label(package.approval_status),
    }
    overall = validation.final_status.value
    lines = ["Lesson Package Status", "---------------------", ""]
    for name, status in categories.items():
        label = status.value if isinstance(status, CheckStatus) else status
        lines.append(f"{name}: {label}")
    lines.extend(["", f"Overall: {overall}"])
    return "\n".join(lines)


def _scope_status(validation, keywords: tuple[str, ...]) -> CheckStatus:
    scoped = [
        check
        for check in validation.checks
        if any(keyword in check.message.lower() for keyword in keywords)
    ]
    if not scoped:
        return CheckStatus.PASS
    if any(check.status == CheckStatus.FAIL for check in scoped):
        return CheckStatus.FAIL
    if any(check.status == CheckStatus.WARN for check in scoped):
        return CheckStatus.WARN
    return CheckStatus.PASS


def _approval_label(state: WorkflowState) -> str:
    if state == WorkflowState.APPROVED:
        return "Approved"
    if state == WorkflowState.IN_REVIEW:
        return "In Review"
    if state == WorkflowState.ARCHIVED:
        return "Archived"
    return "Draft"
