from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .approval_workflow import ApprovalWorkflow, WorkflowState
from .artifact_plan import ArtifactPlan
from .content_map import ContentItem, ContentMap
from .curriculum_intake import CurriculumIntake
from .lesson_model import LessonModel
from .lesson_sequence import InstructionalSequence
from .models import ValidationReport
from .production_registry import ProductionRegistry
from .relationship_graph import RelationshipGraph


@dataclass
class LessonPackagePlan:
    """Canonical planning output — no generated instructional artifacts."""

    lesson_id: str
    metadata: dict[str, Any]
    objectives: list[str]
    vocabulary: list[str]
    critical_content: list[ContentItem]
    instructional_sequence: InstructionalSequence
    artifact_plan: ArtifactPlan
    relationship_graph: RelationshipGraph
    validation_summary: ValidationReport
    approval_status: WorkflowState
    teacher_notes: str
    registry: ProductionRegistry
    status_report: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "lesson_id": self.lesson_id,
            "metadata": self.metadata,
            "objectives": self.objectives,
            "vocabulary": self.vocabulary,
            "critical_content": [item.to_dict() for item in self.critical_content],
            "instructional_sequence": self.instructional_sequence.to_dict(),
            "artifact_plan": self.artifact_plan.to_dict(),
            "relationship_graph": self.relationship_graph.to_dict(),
            "validation_summary": self.validation_summary.to_dict(),
            "approval_status": self.approval_status.value,
            "teacher_notes": self.teacher_notes,
            "registry": self.registry.summary(),
            "status_report": self.status_report,
        }


@dataclass
class LessonPackageInput:
    intake: CurriculumIntake
    content_map: ContentMap
    approval: ApprovalWorkflow | None = None
    broken_graph: bool = False

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> LessonPackageInput:
        intake = CurriculumIntake.from_dict(raw["intake"])
        content_map = ContentMap.from_dict(raw["content_map"])
        approval = ApprovalWorkflow.from_dict(raw["approval"]) if raw.get("approval") else None
        return cls(
            intake=intake,
            content_map=content_map,
            approval=approval,
            broken_graph=bool(raw.get("broken_graph")),
        )
