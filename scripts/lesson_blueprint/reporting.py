from __future__ import annotations

from scripts.curriculum_production.models import CheckStatus, ValidationReport

from .blueprint_approval import BlueprintApprovalWorkflow
from .blueprints import ArtifactBlueprint, LessonBlueprint
from .content_budgets import load_content_budgets
from .registries import LessonRegistries


def build_lesson_blueprint_reports(blueprint: LessonBlueprint) -> dict[str, str]:
    return {
        "lesson_blueprint_status": format_lesson_blueprint_status(blueprint),
        "artifact_blueprint_status": format_artifact_blueprint_status(blueprint),
        "consistency_report": _format_validation_report("Consistency Report", blueprint.consistency_report),
        "vocabulary_report": format_vocabulary_report(blueprint.registries),
        "assessment_coverage_report": format_assessment_coverage_report(blueprint),
        "dependency_report": format_dependency_report(blueprint),
        "content_budget_report": format_content_budget_report(blueprint),
    }


def format_lesson_blueprint_status(blueprint: LessonBlueprint) -> str:
    overall = _overall_status(blueprint.consistency_report, blueprint.blueprint_validation)
    lines = [
        "Lesson Blueprint Status",
        "-----------------------",
        "",
        f"Lesson: {blueprint.lesson_id}",
        f"Approval: {blueprint.approval.state.value}",
        f"Ready for Generation: {'yes' if blueprint.ready_for_generation else 'no'}",
        f"Consistency: {blueprint.consistency_report.final_status.value}",
        f"Blueprint Validation: {blueprint.blueprint_validation.final_status.value}",
        "",
        f"Overall: {overall}",
    ]
    return "\n".join(lines)


def format_artifact_blueprint_status(blueprint: LessonBlueprint) -> str:
    lines = ["Artifact Blueprint Status", "-------------------------", ""]
    for artifact_type, bp in sorted(blueprint.blueprints.items()):
        sections = len(bp.sections)
        lines.append(f"{artifact_type}: {sections} sections | gate={bp.quality_gate}")
    lines.append("")
    lines.append(f"Overall: {blueprint.blueprint_validation.final_status.value}")
    return "\n".join(lines)


def format_vocabulary_report(registries: LessonRegistries) -> str:
    lines = ["Vocabulary Report", "-----------------", ""]
    for entry in registries.vocabulary.entries.values():
        lines.append(f"- {entry.label} → {', '.join(entry.artifact_refs)}")
    lines.append("")
    lines.append(f"Overall: {registries.vocabulary.validate().final_status.value}")
    return "\n".join(lines)


def format_assessment_coverage_report(blueprint: LessonBlueprint) -> str:
    targets = blueprint.review_packet.get("assessment_targets") or []
    lines = ["Assessment Coverage Report", "----------------------------", ""]
    for target in targets:
        lines.append(f"- {target}")
    assessment = blueprint.blueprints.get("assessment")
    if assessment:
        lines.append("")
        lines.append(f"Assessment blueprint links: {', '.join(assessment.required_assessment_links) or '(none)'}")
    lines.extend(["", f"Overall: {blueprint.consistency_report.final_status.value}"])
    return "\n".join(lines)


def format_dependency_report(blueprint: LessonBlueprint) -> str:
    lines = ["Dependency Report", "-----------------", ""]
    for artifact_type, bp in sorted(blueprint.blueprints.items()):
        if bp.dependencies:
            lines.append(f"{artifact_type} → {', '.join(bp.dependencies)}")
    dep_fails = [c for c in blueprint.consistency_report.checks if "dependency" in c.message.lower()]
    overall = CheckStatus.FAIL if dep_fails else CheckStatus.PASS
    lines.extend(["", f"Overall: {overall.value}"])
    return "\n".join(lines)


def format_content_budget_report(blueprint: LessonBlueprint) -> str:
    budgets = load_content_budgets()
    lines = ["Content Budget Report", "---------------------", ""]
    for artifact_type, bp in sorted(blueprint.blueprints.items()):
        budget = budgets.get(artifact_type)
        label = budget.label if budget else "n/a"
        lines.append(f"{artifact_type}: {label}")
    budget_warns = [c for c in blueprint.blueprint_validation.checks if "budget" in c.message.lower()]
    overall = CheckStatus.WARN if budget_warns else CheckStatus.PASS
    lines.extend(["", f"Overall: {overall.value}"])
    return "\n".join(lines)


def _format_validation_report(title: str, report: ValidationReport) -> str:
    lines = [title, "-" * len(title), ""]
    for check in report.checks[:12]:
        lines.append(f"{check.status.value}: {check.message}")
    lines.extend(["", f"Overall: {report.final_status.value}"])
    return "\n".join(lines)


def _overall_status(*reports: ValidationReport) -> str:
    statuses = [report.final_status for report in reports]
    if any(status == CheckStatus.FAIL for status in statuses):
        return CheckStatus.FAIL.value
    if any(status == CheckStatus.WARN for status in statuses):
        return CheckStatus.WARN.value
    approval = CheckStatus.PASS
    return approval.value
