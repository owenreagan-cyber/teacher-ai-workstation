from __future__ import annotations

from .approval_workflow import WorkflowState
from .artifact_plan import ArtifactPlan, populate_artifact_plan_references
from .content_map import ContentPriority
from .curriculum_intake import CurriculumIntake
from .lesson_package import LessonPackageInput, LessonPackagePlan
from .lesson_sequence import get_sequence
from .production_registry import ProductionRegistry
from .relationship_graph import RelationshipGraph
from .reporting import format_lesson_package_status
from .intake_validation import validate_lesson_package_plan


def build_lesson_package(package_input: LessonPackageInput) -> LessonPackagePlan:
    """Manual workflow: intake → content → plan → validation → package (no generation)."""
    intake = package_input.intake
    content_map = package_input.content_map
    if content_map.lesson_id != intake.lesson_id:
        raise ValueError("Content map lesson_id must match intake lesson_id")

    lesson = intake.to_lesson_model()
    sequence = get_sequence(intake.instructional_sequence_id or _default_sequence(intake.subject))
    plan = ArtifactPlan.default_lesson_plan(intake.lesson_id, intake.subject)
    critical_ids = [item.content_id for item in content_map.critical()]
    populate_artifact_plan_references(
        plan,
        critical_content_ids=critical_ids,
        sequence_steps=sequence.steps,
    )
    graph = RelationshipGraph.default_lesson_graph(intake.lesson_id)
    workflow = package_input.approval or _workflow_from_intake(intake)

    validation = validate_lesson_package_plan(
        intake=intake,
        content_map=content_map,
        lesson=lesson,
        plan=plan,
        graph=graph,
        workflow=workflow,
        sequence=sequence,
    )
    registry = ProductionRegistry.from_plan(
        lesson,
        plan,
        workflow=workflow,
        validation_report=validation,
    )

    objectives = [intake.objective] if intake.objective.strip() else []
    package = LessonPackagePlan(
        lesson_id=intake.lesson_id,
        metadata={
            "title": intake.title,
            "subject": intake.subject,
            "grade": intake.grade,
            "unit": intake.unit,
            "chapter": intake.chapter,
            "lesson_number": intake.lesson_number,
            "standards": intake.standards,
            "assessment_targets": intake.assessment_targets,
            "source_references": [ref.to_dict() for ref in intake.source_references],
        },
        objectives=objectives,
        vocabulary=list(intake.vocabulary),
        critical_content=content_map.critical(),
        instructional_sequence=sequence,
        artifact_plan=plan,
        relationship_graph=graph,
        validation_summary=validation,
        approval_status=workflow.state,
        teacher_notes=intake.teacher_notes,
        registry=registry,
    )
    package.status_report = format_lesson_package_status(package)
    return package


def _default_sequence(subject: str) -> str:
    normalized = subject.lower().replace("_", "-")
    if normalized in {"math", "ela", "reading", "history", "shurley"}:
        if normalized == "shurley":
            return "ela"
        return normalized if normalized != "reading" else "reading"
    return "math"


def _workflow_from_intake(intake: CurriculumIntake):
    from .approval_workflow import ApprovalWorkflow

    return ApprovalWorkflow(state=intake.approval_status)
