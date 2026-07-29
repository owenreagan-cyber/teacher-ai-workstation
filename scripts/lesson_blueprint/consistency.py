from __future__ import annotations

from scripts.curriculum_production.content_map import ContentMap, ContentPriority
from scripts.curriculum_production.lesson_package import LessonPackagePlan
from scripts.curriculum_production.models import CheckStatus, ValidationReport

from .blueprints import ArtifactBlueprint
from .registries import LessonRegistries


def validate_consistency(
    package: LessonPackagePlan,
    content_map: ContentMap,
    registries: LessonRegistries,
    blueprints: dict[str, ArtifactBlueprint],
) -> ValidationReport:
    report = ValidationReport(scope="consistency_engine")
    valid_refs = {a.artifact_type for a in package.artifact_plan.artifacts}
    registry_report = registries.validate_all(valid_refs=valid_refs)
    report.checks.extend(registry_report.checks)

    vocab_terms = {term.lower() for term in package.vocabulary}
    for artifact_type, blueprint in blueprints.items():
        for term in blueprint.required_vocabulary:
            if term.lower() not in vocab_terms:
                report.add(
                    CheckStatus.WARN,
                    f"Vocabulary term missing from lesson vocabulary list",
                    details=f"{artifact_type}: {term}",
                )

    presentation = blueprints.get("presentation")
    worksheet = blueprints.get("worksheet")
    if presentation and worksheet:
        p_vocab = {t.lower() for t in presentation.required_vocabulary}
        w_vocab = {t.lower() for t in worksheet.required_vocabulary}
        if p_vocab != w_vocab and (p_vocab or w_vocab):
            report.add(CheckStatus.WARN, "Vocabulary mismatch between presentation and worksheet")

    for item in content_map.critical():
        covered = any(item.content_id in section.expected_content for bp in blueprints.values() for section in bp.sections)
        if not covered:
            report.add(CheckStatus.WARN, "Unused Critical content in blueprints", details=item.content_id)

    if package.objectives:
        seq_steps = package.instructional_sequence.steps
        uncovered = [obj for obj in package.objectives if obj and not seq_steps]
        if uncovered:
            report.add(CheckStatus.WARN, "Objective may not be covered by instructional sequence")

    assessment_targets = package.metadata.get("assessment_targets") or []
    assessment_bp = blueprints.get("assessment")
    if assessment_targets and assessment_bp:
        for target in assessment_targets:
            if target not in assessment_bp.required_assessment_links:
                report.add(CheckStatus.WARN, "Assessment target not linked in assessment blueprint", details=target)
    elif assessment_targets and not assessment_bp:
        report.add(CheckStatus.WARN, "Assessment targets exist but assessment blueprint missing")

    teacher_key = blueprints.get("teacher_key")
    if teacher_key:
        budget = teacher_key.content_budget
        if not budget.get("mirrored"):
            report.add(CheckStatus.WARN, "Teacher key blueprint should mirror student artifacts")

    for artifact_type, blueprint in blueprints.items():
        for dep in blueprint.dependencies:
            if dep not in blueprints and dep not in {a.artifact_type for a in package.artifact_plan.artifacts}:
                report.add(CheckStatus.FAIL, "Broken artifact dependency", details=f"{artifact_type} → {dep}")

    critical_in_notes = content_map.by_priority(ContentPriority.CRITICAL)
    guided = blueprints.get("guided_notes")
    if guided and critical_in_notes:
        if not guided.sections:
            report.add(CheckStatus.FAIL, "Guided notes blueprint missing required sections")

    if report.final_status == CheckStatus.PASS:
        report.add(CheckStatus.PASS, "Cross-artifact consistency checks passed")
    return report
