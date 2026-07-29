from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .approval_workflow import WorkflowState
from .lesson_model import LessonModel, ProductionStatus


REQUIRED_INTAKE_FIELDS = (
    "lesson_id",
    "subject",
    "grade",
    "unit",
    "chapter",
    "lesson_number",
    "title",
    "objective",
)


@dataclass
class SourceReference:
    ref_id: str
    label: str
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> SourceReference:
        return cls(
            ref_id=str(raw["ref_id"]),
            label=str(raw["label"]),
            note=str(raw.get("note") or ""),
        )


@dataclass
class CurriculumIntake:
    """Teacher-entered curriculum metadata — no extraction, OCR, or file parsing."""

    lesson_id: str
    subject: str
    grade: int
    unit: str
    chapter: str
    lesson_number: int
    title: str
    objective: str
    standards: list[str] = field(default_factory=list)
    vocabulary: list[str] = field(default_factory=list)
    assessment_targets: list[str] = field(default_factory=list)
    teacher_notes: str = ""
    source_references: list[SourceReference] = field(default_factory=list)
    approval_status: WorkflowState = WorkflowState.DRAFT
    instructional_sequence_id: str = ""
    prerequisite_knowledge: list[str] = field(default_factory=list)
    required_artifacts: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["approval_status"] = self.approval_status.value
        payload["source_references"] = [ref.to_dict() for ref in self.source_references]
        return payload

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> CurriculumIntake:
        status = raw.get("approval_status", WorkflowState.DRAFT.value)
        if isinstance(status, WorkflowState):
            approval_status = status
        else:
            approval_status = WorkflowState(str(status))
        refs = [SourceReference.from_dict(item) for item in raw.get("source_references") or []]
        return cls(
            lesson_id=str(raw.get("lesson_id") or ""),
            subject=str(raw.get("subject") or ""),
            grade=int(raw.get("grade") or 0),
            unit=str(raw.get("unit") or ""),
            chapter=str(raw.get("chapter") or ""),
            lesson_number=int(raw.get("lesson_number") or 0),
            title=str(raw.get("title") or ""),
            objective=str(raw.get("objective") or ""),
            standards=list(raw.get("standards") or []),
            vocabulary=list(raw.get("vocabulary") or []),
            assessment_targets=list(raw.get("assessment_targets") or []),
            teacher_notes=str(raw.get("teacher_notes") or ""),
            source_references=refs,
            approval_status=approval_status,
            instructional_sequence_id=str(raw.get("instructional_sequence_id") or ""),
            prerequisite_knowledge=list(raw.get("prerequisite_knowledge") or []),
            required_artifacts=list(raw.get("required_artifacts") or []),
        )

    def to_lesson_model(self) -> LessonModel:
        status_map = {
            WorkflowState.DRAFT: ProductionStatus.DRAFT,
            WorkflowState.IN_REVIEW: ProductionStatus.TEACHER_REVIEW,
            WorkflowState.APPROVED: ProductionStatus.APPROVED,
            WorkflowState.ARCHIVED: ProductionStatus.BLOCKED,
        }
        return LessonModel(
            lesson_id=self.lesson_id,
            subject=self.subject,
            grade=self.grade,
            unit=self.unit,
            chapter=self.chapter,
            lesson_number=self.lesson_number,
            title=self.title,
            objective=self.objective,
            standards=list(self.standards),
            vocabulary=list(self.vocabulary),
            prerequisite_knowledge=list(self.prerequisite_knowledge),
            assessment_targets=list(self.assessment_targets),
            instructional_sequence_id=self.instructional_sequence_id,
            required_artifacts=list(self.required_artifacts),
            production_status=status_map.get(self.approval_status, ProductionStatus.DRAFT),
        )
