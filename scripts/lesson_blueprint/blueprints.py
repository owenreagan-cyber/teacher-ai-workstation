from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from scripts.curriculum_production.artifact_plan import ArtifactPlan
from scripts.curriculum_production.content_map import ContentMap, ContentPriority
from scripts.curriculum_production.lesson_package import LessonPackagePlan

from .blueprint_approval import BlueprintApprovalState
from .content_budgets import ContentBudget, load_content_budgets
from .registries import LessonRegistries


@dataclass
class BlueprintSection:
    name: str
    purpose: str = ""
    expected_content: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "purpose": self.purpose,
            "expected_content": self.expected_content,
        }


@dataclass
class ArtifactBlueprint:
    artifact_type: str
    purpose: str
    sections: list[BlueprintSection] = field(default_factory=list)
    target_page_count: int | None = None
    target_slide_count: int | None = None
    content_budget: dict[str, Any] = field(default_factory=dict)
    required_vocabulary: list[str] = field(default_factory=list)
    required_diagrams: list[str] = field(default_factory=list)
    required_examples: list[str] = field(default_factory=list)
    required_assessment_links: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    quality_gate: str = ""
    approval_state: BlueprintApprovalState = BlueprintApprovalState.DRAFT

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact_type": self.artifact_type,
            "purpose": self.purpose,
            "sections": [section.to_dict() for section in self.sections],
            "target_page_count": self.target_page_count,
            "target_slide_count": self.target_slide_count,
            "content_budget": self.content_budget,
            "required_vocabulary": self.required_vocabulary,
            "required_diagrams": self.required_diagrams,
            "required_examples": self.required_examples,
            "required_assessment_links": self.required_assessment_links,
            "dependencies": self.dependencies,
            "quality_gate": self.quality_gate,
            "approval_state": self.approval_state.value,
        }


@dataclass
class LessonBlueprint:
    lesson_id: str
    review_packet: dict[str, Any]
    registries: LessonRegistries
    blueprints: dict[str, ArtifactBlueprint]
    consistency_report: Any
    blueprint_validation: Any
    approval: Any
    reports: dict[str, str] = field(default_factory=dict)
    ready_for_generation: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "lesson_id": self.lesson_id,
            "review_packet": self.review_packet,
            "registries": self.registries.to_dict(),
            "blueprints": {k: v.to_dict() for k, v in self.blueprints.items()},
            "consistency_report": self.consistency_report.to_dict(),
            "blueprint_validation": self.blueprint_validation.to_dict(),
            "approval": self.approval.to_dict(),
            "reports": self.reports,
            "ready_for_generation": self.ready_for_generation,
        }


def _load_templates(path: Path | None = None) -> dict[str, list[str]]:
    catalog_path = path or (Path(__file__).resolve().parents[2] / "configs" / "lesson-blueprint" / "blueprint-templates.yaml")
    text = catalog_path.read_text(encoding="utf-8")
    try:
        import yaml

        raw = yaml.safe_load(text)
    except ImportError:  # pragma: no cover
        raw = json.loads(text) if text.strip().startswith("{") else {}
    sections: dict[str, list[str]] = {}
    if isinstance(raw, dict):
        for key, value in raw.items():
            if isinstance(value, dict):
                sections[key] = list(value.get("sections") or [])
    return sections


def generate_artifact_blueprints(
    package: LessonPackagePlan,
    content_map: ContentMap,
    registries: LessonRegistries,
    *,
    overrides: dict[str, Any] | None = None,
) -> dict[str, ArtifactBlueprint]:
    budgets = load_content_budgets()
    templates = _load_templates()
    overrides = overrides or {}
    critical_ids = [item.content_id for item in content_map.critical()]
    assessment_targets = list(package.metadata.get("assessment_targets") or [])
    vocab = list(package.vocabulary)
    example_labels = [entry.label for entry in registries.examples.entries.values()]
    diagram_labels = [entry.label for entry in registries.diagrams.entries.values()]
    blueprints: dict[str, ArtifactBlueprint] = {}

    for planned in package.artifact_plan.artifacts:
        artifact_type = planned.artifact_type
        budget = budgets.get(artifact_type)
        section_names = list(templates.get(artifact_type) or [artifact_type.replace("_", " ").title()])
        if overrides.get("missing_section_for") == artifact_type:
            section_names = []
        if overrides.get("duplicate_sections_for") == artifact_type:
            section_names = section_names + section_names[:1]

        required_vocab = list(vocab)
        if overrides.get("vocabulary_mismatch") and artifact_type == "worksheet":
            required_vocab = list(overrides.get("worksheet_vocab") or ["nonexistent-term"])
        if overrides.get("vocabulary_mismatch") and artifact_type == "presentation":
            required_vocab = list(vocab)

        expected = [] if overrides.get("unused_critical") else critical_ids[:2]
        sections = [
            BlueprintSection(
                name=name,
                purpose=f"Cover {name.lower()} for {artifact_type}",
                expected_content=list(expected),
            )
            for name in section_names
        ]
        bp = ArtifactBlueprint(
            artifact_type=artifact_type,
            purpose=f"Specification for {artifact_type.replace('_', ' ')}",
            sections=sections,
            target_page_count=budget.pages if budget else None,
            target_slide_count=budget.max_slides if budget and artifact_type == "presentation" else None,
            content_budget=budget.to_dict() if budget else {},
            required_vocabulary=required_vocab,
            required_diagrams=list(diagram_labels),
            required_examples=list(example_labels),
            required_assessment_links=list(assessment_targets) if artifact_type in {"assessment", "worksheet", "review"} else [],
            dependencies=list(planned.dependencies),
            quality_gate=planned.quality_gate,
        )
        if overrides.get("broken_dependency_for") == artifact_type:
            bp.dependencies = ["nonexistent-artifact"]
        if overrides.get("budget_exceeded_for") == artifact_type and budget:
            if budget.max_slides:
                bp.target_slide_count = budget.max_slides + 5
            if budget.pages:
                bp.target_page_count = budget.pages + 3
            if budget.activity_sections:
                bp.content_budget["activity_sections"] = budget.activity_sections + 4
        blueprints[artifact_type] = bp
    return blueprints
