from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .approval_workflow import ApprovalWorkflow, WorkflowState
from .artifact_plan import ArtifactPlan, STANDARD_ARTIFACT_TYPES
from .content_map import ContentMap, ContentPriority
from .curriculum_intake import REQUIRED_INTAKE_FIELDS, CurriculumIntake
from .lesson_model import LessonModel
from .lesson_sequence import InstructionalSequence
from .models import CheckStatus, ValidationReport
from .relationship_graph import RelationshipGraph, REQUIRED_RELATIONSHIPS
from .validation import (
    validate_artifact_plan,
    validate_instructional_sequence,
    validate_lesson_model,
    validate_relationship_graph,
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_priority_limits() -> dict[str, Any]:
    path = _repo_root() / "configs" / "curriculum-production" / "priority-limits.yaml"
    text = path.read_text(encoding="utf-8")
    try:
        import yaml

        data = yaml.safe_load(text)
    except ImportError:  # pragma: no cover
        data = {}
        for line in text.splitlines():
            if ":" in line and not line.strip().startswith("#"):
                key, val = line.split(":", 1)
                val = val.strip()
                if val.lower() in {"true", "false"}:
                    data[key.strip()] = val.lower() == "true"
                else:
                    try:
                        data[key.strip()] = int(val)
                    except ValueError:
                        try:
                            data[key.strip()] = float(val)
                        except ValueError:
                            data[key.strip()] = val
    return data if isinstance(data, dict) else {}


def validate_intake(intake: CurriculumIntake) -> ValidationReport:
    report = ValidationReport(scope="curriculum_intake")
    missing = [field for field in REQUIRED_INTAKE_FIELDS if not getattr(intake, field, None)]
    if missing:
        report.add(CheckStatus.FAIL, "Intake missing required fields", details=", ".join(missing))
    else:
        report.add(CheckStatus.PASS, "Manual curriculum intake fields present")
    if not intake.objective.strip():
        report.add(CheckStatus.FAIL, "Missing lesson objective")
    return report


def validate_objectives(intake: CurriculumIntake, content_map: ContentMap) -> ValidationReport:
    report = ValidationReport(scope="objectives")
    objective = intake.objective.strip()
    if not objective:
        report.add(CheckStatus.FAIL, "Missing lesson objective")
        return report
    if ";" in objective or objective.lower().count(" and ") > 2:
        report.add(CheckStatus.WARN, "Multiple objectives may conflict in one statement")
    critical = content_map.critical()
    linked = [item for item in critical if item.supports_objective]
    if not linked:
        report.add(CheckStatus.WARN, "No Critical content explicitly supports lesson objective")
    else:
        report.add(CheckStatus.PASS, "Critical content supports lesson objective")
    if objective and not intake.standards:
        report.add(CheckStatus.WARN, "Objective present without referenced standards")
    return report


def validate_assessment_targets(intake: CurriculumIntake, content_map: ContentMap) -> ValidationReport:
    report = ValidationReport(scope="assessment_targets")
    if not intake.assessment_targets:
        report.add(CheckStatus.WARN, "No assessment targets declared")
        return report
    report.add(CheckStatus.PASS, f"{len(intake.assessment_targets)} assessment target(s) declared")
    for target in intake.assessment_targets:
        supporters = [
            item
            for item in content_map.critical()
            if item.supports_assessment_target == target or target in item.title
        ]
        if not supporters:
            report.add(
                CheckStatus.WARN,
                f"Assessment target lacks supporting Critical content",
                details=target,
            )
    return report


def validate_content_priorities(intake: CurriculumIntake, content_map: ContentMap) -> ValidationReport:
    report = ValidationReport(scope="content_priorities")
    limits = load_priority_limits()
    unclassified = content_map.unclassified()
    if unclassified:
        report.add(CheckStatus.WARN, f"{len(unclassified)} content item(s) await manual priority")

    for item in content_map.critical():
        if not (item.supports_objective or item.supports_assessment_target):
            report.add(
                CheckStatus.FAIL,
                "Critical item must support lesson objective or assessment target",
                details=item.content_id,
            )

    high = content_map.by_priority(ContentPriority.HIGH_PRIORITY)
    if limits.get("require_source_ref_for_high_priority", True):
        for item in high:
            if not item.source_ref.strip():
                report.add(CheckStatus.WARN, "High Priority item lacks source reference", details=item.content_id)

    supporting = content_map.by_priority(ContentPriority.SUPPORTING)
    max_supporting = int(limits.get("max_supporting_items", 12))
    if len(supporting) > max_supporting:
        report.add(
            CheckStatus.WARN,
            f"Supporting items exceed configured limit ({len(supporting)} > {max_supporting})",
        )

    total = max(len(content_map.items), 1)
    background = len(content_map.by_priority(ContentPriority.TEACHER_BACKGROUND))
    ratio = background / total
    max_ratio = float(limits.get("max_teacher_background_ratio", 0.40))
    if ratio > max_ratio:
        report.add(CheckStatus.WARN, "Teacher Background content dominates lesson map")

    omit_in_plan = content_map.omit_in_plan()
    if omit_in_plan:
        report.add(
            CheckStatus.WARN,
            "Omit items referenced in artifact planning",
            details=", ".join(item.content_id for item in omit_in_plan),
        )

    if not report.checks:
        report.add(CheckStatus.PASS, "Content priority workflow validated")
    return report


def validate_sequence_alignment(
    content_map: ContentMap,
    sequence: InstructionalSequence,
) -> ValidationReport:
    report = ValidationReport(scope="instructional_sequence")
    if len(sequence.steps) < 3:
        report.add(CheckStatus.WARN, "Instructional sequence appears incomplete")
    critical = content_map.critical()
    linked = [item for item in critical if item.linked_sequence_step]
    if critical and not linked:
        report.add(CheckStatus.WARN, "Critical content not linked to instructional sequence steps")
    elif linked:
        invalid = [item for item in linked if item.linked_sequence_step not in sequence.steps]
        for item in invalid:
            report.add(
                CheckStatus.WARN,
                "Critical content linked to unknown sequence step",
                details=f"{item.content_id} → {item.linked_sequence_step}",
            )
        if not invalid:
            report.add(CheckStatus.PASS, "Critical content aligned to instructional sequence")
    else:
        report.add(CheckStatus.PASS, f"Instructional sequence loaded: {sequence.name}")
    return report


def validate_artifact_plan_references(plan: ArtifactPlan, intake: CurriculumIntake) -> ValidationReport:
    report = ValidationReport(scope="artifact_plan")
    base = validate_artifact_plan(plan)
    report.checks.extend(base.checks)
    missing_types = [t for t in STANDARD_ARTIFACT_TYPES if not plan.by_type(t)]
    if missing_types:
        report.add(CheckStatus.WARN, "Artifact plan missing standard artifact types", details=", ".join(missing_types))
    for artifact in plan.artifacts:
        if not artifact.linked_objective:
            report.add(CheckStatus.WARN, f"Artifact {artifact.artifact_type} missing objective reference")
        if not artifact.linked_critical_content_ids and intake.objective:
            report.add(CheckStatus.WARN, f"Artifact {artifact.artifact_type} missing critical content reference")
        if not artifact.linked_sequence_steps:
            report.add(CheckStatus.WARN, f"Artifact {artifact.artifact_type} missing sequence reference")
    return report


def validate_approval_workflow(workflow: ApprovalWorkflow) -> ValidationReport:
    report = ValidationReport(scope="teacher_approval")
    if workflow.state == WorkflowState.DRAFT:
        report.add(CheckStatus.WARN, "Teacher approval still Draft")
    elif workflow.state == WorkflowState.IN_REVIEW:
        report.add(CheckStatus.WARN, "Teacher approval In Review")
    elif workflow.state == WorkflowState.APPROVED:
        report.add(CheckStatus.PASS, "Teacher approval recorded as Approved")
    else:
        report.add(CheckStatus.WARN, "Lesson package archived")
    return report


def validate_lesson_package_plan(
    *,
    intake: CurriculumIntake,
    content_map: ContentMap,
    lesson: LessonModel,
    plan: ArtifactPlan,
    graph: RelationshipGraph,
    workflow: ApprovalWorkflow,
    sequence: InstructionalSequence,
) -> ValidationReport:
    report = ValidationReport(scope="lesson_package_plan")
    sections = [
        validate_intake(intake),
        validate_lesson_model(lesson),
        validate_objectives(intake, content_map),
        validate_assessment_targets(intake, content_map),
        validate_content_priorities(intake, content_map),
        validate_instructional_sequence(sequence.sequence_id),
        validate_sequence_alignment(content_map, sequence),
        validate_artifact_plan_references(plan, intake),
        validate_relationship_graph(graph),
        validate_approval_workflow(workflow),
    ]
    for section in sections:
        report.checks.extend(section.checks)
    if report.final_status == CheckStatus.PASS:
        report.add(CheckStatus.PASS, "Lesson package plan ready for teacher review")
    return report
