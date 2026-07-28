from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class ProductionStatus(str, Enum):
    DRAFT = "draft"
    PLANNED = "planned"
    IN_PRODUCTION = "in_production"
    VALIDATED = "validated"
    TEACHER_REVIEW = "teacher_review"
    APPROVED = "approved"
    BLOCKED = "blocked"


REQUIRED_LESSON_FIELDS = (
    "lesson_id",
    "subject",
    "grade",
    "unit",
    "chapter",
    "lesson_number",
    "title",
    "objective",
    "instructional_sequence_id",
    "production_status",
)


@dataclass
class LessonModel:
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
    prerequisite_knowledge: list[str] = field(default_factory=list)
    assessment_targets: list[str] = field(default_factory=list)
    instructional_sequence_id: str = ""
    required_artifacts: list[str] = field(default_factory=list)
    production_status: ProductionStatus = ProductionStatus.DRAFT

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["production_status"] = self.production_status.value
        return payload

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> LessonModel:
        status = raw.get("production_status", ProductionStatus.DRAFT.value)
        if isinstance(status, ProductionStatus):
            production_status = status
        else:
            production_status = ProductionStatus(str(status))
        return cls(
            lesson_id=str(raw["lesson_id"]),
            subject=str(raw["subject"]),
            grade=int(raw["grade"]),
            unit=str(raw["unit"]),
            chapter=str(raw["chapter"]),
            lesson_number=int(raw["lesson_number"]),
            title=str(raw["title"]),
            objective=str(raw["objective"]),
            standards=list(raw.get("standards") or []),
            vocabulary=list(raw.get("vocabulary") or []),
            prerequisite_knowledge=list(raw.get("prerequisite_knowledge") or []),
            assessment_targets=list(raw.get("assessment_targets") or []),
            instructional_sequence_id=str(raw.get("instructional_sequence_id") or ""),
            required_artifacts=list(raw.get("required_artifacts") or []),
            production_status=production_status,
        )
