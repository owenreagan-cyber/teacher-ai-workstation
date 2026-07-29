from __future__ import annotations

from scripts.curriculum_production.content_map import ContentMap
from scripts.curriculum_production.lesson_package import LessonPackagePlan
from scripts.curriculum_production.models import CheckStatus, ValidationReport

from .blueprints import ArtifactBlueprint
from .content_budgets import load_content_budgets
from .registries import LessonRegistries


def validate_blueprints(
    package: LessonPackagePlan,
    content_map: ContentMap,
    registries: LessonRegistries,
    blueprints: dict[str, ArtifactBlueprint],
) -> ValidationReport:
    report = ValidationReport(scope="blueprint_validation")
    budgets = load_content_budgets()

    if not blueprints:
        report.add(CheckStatus.FAIL, "Missing artifact blueprints")
        return report

    for artifact_type, blueprint in blueprints.items():
        if not blueprint.sections:
            report.add(CheckStatus.FAIL, f"Missing required sections in blueprint", details=artifact_type)
        section_names = [section.name for section in blueprint.sections]
        if len(section_names) != len(set(section_names)):
            report.add(CheckStatus.WARN, f"Duplicate sections in blueprint", details=artifact_type)
        if not blueprint.required_vocabulary and package.vocabulary:
            report.add(CheckStatus.WARN, f"Blueprint missing required vocabulary", details=artifact_type)
        budget = budgets.get(artifact_type)
        if budget and blueprint.target_slide_count and budget.max_slides:
            if blueprint.target_slide_count > budget.max_slides:
                report.add(CheckStatus.WARN, "Presentation slide budget exceeded", details=str(blueprint.target_slide_count))
        if budget and blueprint.target_page_count and budget.pages:
            if blueprint.target_page_count > budget.pages:
                report.add(CheckStatus.WARN, "Page budget exceeded", details=f"{artifact_type}: {blueprint.target_page_count}")
        if budget and budget.activity_sections:
            declared = blueprint.content_budget.get("activity_sections")
            if isinstance(declared, int) and declared > budget.activity_sections:
                report.add(CheckStatus.WARN, "Worksheet activity section budget exceeded", details=str(declared))

    critical_ids = {item.content_id for item in content_map.critical()}
    assigned: set[str] = set()
    for blueprint in blueprints.values():
        for section in blueprint.sections:
            assigned.update(section.expected_content)
    unused = critical_ids - assigned
    if unused:
        report.add(CheckStatus.WARN, "Unused Critical content in blueprint assignments", details=", ".join(sorted(unused)))

    assessment_targets = package.metadata.get("assessment_targets") or []
    linked = set()
    for blueprint in blueprints.values():
        linked.update(blueprint.required_assessment_links)
    for target in assessment_targets:
        if target not in linked:
            report.add(CheckStatus.WARN, "Unused assessment target in blueprints", details=target)

    for planned in package.artifact_plan.artifacts:
        if planned.artifact_type not in blueprints:
            report.add(CheckStatus.FAIL, "Artifact plan entry missing blueprint", details=planned.artifact_type)

    if report.final_status == CheckStatus.PASS:
        report.add(CheckStatus.PASS, "Artifact blueprints validated")
    return report
