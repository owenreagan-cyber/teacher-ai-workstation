from __future__ import annotations

from typing import Any

from scripts.curriculum_production.content_map import ContentMap
from scripts.curriculum_production.lesson_package import LessonPackagePlan
from scripts.curriculum_production.models import CheckStatus

from .blueprint_approval import BlueprintApprovalWorkflow
from .blueprint_validation import validate_blueprints
from .blueprints import LessonBlueprint, generate_artifact_blueprints
from .consistency import validate_consistency
from .registries import RegistryEntry, build_registries
from .reporting import build_lesson_blueprint_reports
from .review_packet import build_review_packet


def build_lesson_blueprint(
    package: LessonPackagePlan,
    content_map: ContentMap,
    *,
    overrides: dict[str, Any] | None = None,
    approval: BlueprintApprovalWorkflow | None = None,
) -> LessonBlueprint:
    """Transform an approved Lesson Package Plan into a fully specified Lesson Blueprint."""
    overrides = overrides or {}
    review = build_review_packet(package, content_map)
    registries = build_registries(package, content_map)
    if overrides.get("broken_registry_duplicate") and registries.vocabulary.entries:
        first = next(iter(registries.vocabulary.entries.values()))
        registries.vocabulary.entries["dup-vocab"] = RegistryEntry(
            entry_id="dup-vocab",
            label=first.label,
            artifact_refs=list(first.artifact_refs),
        )
    if overrides.get("broken_registry_reference") and registries.vocabulary.entries:
        first = next(iter(registries.vocabulary.entries.values()))
        first.artifact_refs = ["nonexistent-artifact"]
    blueprints = generate_artifact_blueprints(package, content_map, registries, overrides=overrides)
    if overrides.get("missing_blueprint_for"):
        blueprints.pop(overrides["missing_blueprint_for"], None)

    consistency = validate_consistency(package, content_map, registries, blueprints)
    validation = validate_blueprints(package, content_map, registries, blueprints)
    workflow = approval or BlueprintApprovalWorkflow()

    from .blueprint_approval import BlueprintApprovalState

    ready = (
        consistency.final_status != CheckStatus.FAIL
        and validation.final_status != CheckStatus.FAIL
        and workflow.state in {BlueprintApprovalState.APPROVED, BlueprintApprovalState.LOCKED}
    )

    blueprint = LessonBlueprint(
        lesson_id=package.lesson_id,
        review_packet=review.to_dict(),
        registries=registries,
        blueprints=blueprints,
        consistency_report=consistency,
        blueprint_validation=validation,
        approval=workflow,
        ready_for_generation=ready,
    )
    blueprint.reports = build_lesson_blueprint_reports(blueprint)
    return blueprint
