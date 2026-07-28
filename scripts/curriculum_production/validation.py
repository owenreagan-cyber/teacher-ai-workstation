from __future__ import annotations

from .artifact_plan import ArtifactPlan, PlannedArtifact
from .content_map import ContentMap
from .lesson_model import REQUIRED_LESSON_FIELDS, LessonModel
from .lesson_sequence import get_sequence, load_sequence_catalog
from .models import CheckStatus, ValidationReport
from .production_registry import ProductionRegistry
from .relationship_graph import REQUIRED_RELATIONSHIPS, RelationshipGraph


def validate_lesson_model(lesson: LessonModel) -> ValidationReport:
    report = ValidationReport(scope="lesson_model")
    missing = [field for field in REQUIRED_LESSON_FIELDS if not getattr(lesson, field, None)]
    if missing:
        report.add(CheckStatus.FAIL, "Lesson model missing required fields", details=", ".join(missing))
    else:
        report.add(CheckStatus.PASS, "Lesson model required fields present")
    if lesson.grade < 1 or lesson.grade > 12:
        report.add(CheckStatus.WARN, f"Grade {lesson.grade} outside typical K-12 range")
    if not lesson.required_artifacts:
        report.add(CheckStatus.WARN, "No required artifacts declared on lesson model")
    return report


def validate_content_map(content_map: ContentMap) -> ValidationReport:
    report = ValidationReport(scope="content_map")
    if not content_map.items:
        report.add(CheckStatus.WARN, "Content map has no items")
        return report
    unclassified = content_map.unclassified()
    if unclassified:
        report.add(
            CheckStatus.WARN,
            f"{len(unclassified)} content item(s) await manual prioritization",
            details="Automatic classification is intentionally disabled.",
        )
    else:
        report.add(CheckStatus.PASS, "All content items manually classified")
    report.add(CheckStatus.PASS, "Content prioritization engine is placeholder-only (no auto classification)")
    return report


def validate_instructional_sequence(sequence_id: str) -> ValidationReport:
    report = ValidationReport(scope="instructional_sequence")
    try:
        sequence = get_sequence(sequence_id)
    except KeyError:
        report.add(CheckStatus.FAIL, f"Unknown instructional sequence: {sequence_id}")
        return report
    if len(sequence.steps) < 2:
        report.add(CheckStatus.FAIL, f"Sequence {sequence_id} must define at least two steps")
    else:
        report.add(CheckStatus.PASS, f"Instructional sequence loaded: {sequence.name}")
    return report


def validate_artifact_plan(plan: ArtifactPlan) -> ValidationReport:
    report = ValidationReport(scope="artifact_plan")
    if not plan.artifacts:
        report.add(CheckStatus.FAIL, "Artifact plan is empty")
        return report
    ids = {artifact.artifact_id for artifact in plan.artifacts}
    if len(ids) != len(plan.artifacts):
        report.add(CheckStatus.FAIL, "Duplicate artifact IDs in plan")
    else:
        report.add(CheckStatus.PASS, f"Artifact plan defines {len(plan.artifacts)} artifacts")
    for artifact in plan.artifacts:
        for dep_type in artifact.dependencies:
            if not any(a.artifact_type == dep_type for a in plan.artifacts):
                report.add(
                    CheckStatus.WARN,
                    f"Artifact {artifact.artifact_id} depends on missing type {dep_type}",
                )
        if not artifact.quality_gate:
            report.add(CheckStatus.WARN, f"Artifact {artifact.artifact_id} missing quality gate profile")
    return report


def validate_relationship_graph(graph: RelationshipGraph) -> ValidationReport:
    report = ValidationReport(scope="relationship_graph")
    missing: list[str] = []
    for source, target, relationship in REQUIRED_RELATIONSHIPS:
        if not graph.has_edge(source, target, relationship):
            missing.append(f"{source} {relationship.value} {target}")
    if missing:
        report.add(
            CheckStatus.FAIL,
            "Relationship graph missing required edges",
            details="; ".join(missing),
        )
    else:
        report.add(CheckStatus.PASS, "Required lesson-package relationships present")
    return report


def validate_registry(registry: ProductionRegistry, plan: ArtifactPlan) -> ValidationReport:
    report = ValidationReport(scope="production_registry")
    record = registry.get(plan.lesson_id)
    if record is None:
        report.add(CheckStatus.FAIL, f"Lesson {plan.lesson_id} not registered")
        return report
    planned_ids = {artifact.artifact_id for artifact in plan.artifacts}
    registry_ids = set(record.artifacts.keys())
    if planned_ids != registry_ids:
        report.add(CheckStatus.FAIL, "Registry artifact set does not match artifact plan")
    else:
        report.add(CheckStatus.PASS, "Registry tracks all planned artifacts")
    return report


def validate_lesson_package(
    *,
    lesson: LessonModel,
    content_map: ContentMap,
    plan: ArtifactPlan,
    graph: RelationshipGraph,
    registry: ProductionRegistry,
) -> ValidationReport:
    report = ValidationReport(scope="lesson_package")
    sections = [
        validate_lesson_model(lesson),
        validate_content_map(content_map),
        validate_instructional_sequence(lesson.instructional_sequence_id),
        validate_artifact_plan(plan),
        validate_relationship_graph(graph),
        validate_registry(registry, plan),
    ]
    for section in sections:
        report.checks.extend(section.checks)
    if report.final_status == CheckStatus.PASS:
        report.add(CheckStatus.PASS, "Lesson package planning scaffold validates")
    return report


def validate_sequence_catalog() -> ValidationReport:
    report = ValidationReport(scope="sequence_catalog")
    catalog = load_sequence_catalog()
    expected = {"ela", "math", "history", "reading"}
    missing = sorted(expected - set(catalog.keys()))
    if missing:
        report.add(CheckStatus.FAIL, "Instructional sequence catalog missing templates", details=", ".join(missing))
    else:
        report.add(CheckStatus.PASS, f"Instructional sequence catalog loaded ({len(catalog)} templates)")
    for key, sequence in catalog.items():
        if len(sequence.steps) < 3:
            report.add(CheckStatus.WARN, f"Sequence {key} has fewer than three steps")
    return report
