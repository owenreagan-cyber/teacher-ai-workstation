from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .artifact_plan import ArtifactPlan, PlannedArtifact
from .lesson_model import LessonModel, ProductionStatus


class TeacherReviewStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_REVIEW = "in_review"
    CHANGES_REQUESTED = "changes_requested"
    APPROVED = "approved"


class QualityStatus(str, Enum):
    NOT_RUN = "not_run"
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


@dataclass
class RegistryArtifactRecord:
    artifact_id: str
    artifact_type: str
    planned: bool = True
    completed: bool = False
    validated: bool = False
    approved: bool = False
    quality_status: QualityStatus = QualityStatus.NOT_RUN

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "artifact_type": self.artifact_type,
            "planned": self.planned,
            "completed": self.completed,
            "validated": self.validated,
            "approved": self.approved,
            "quality_status": self.quality_status.value,
        }


@dataclass
class LessonRegistryRecord:
    lesson_id: str
    production_status: ProductionStatus = ProductionStatus.PLANNED
    teacher_review_status: TeacherReviewStatus = TeacherReviewStatus.NOT_STARTED
    artifacts: dict[str, RegistryArtifactRecord] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "lesson_id": self.lesson_id,
            "production_status": self.production_status.value,
            "teacher_review_status": self.teacher_review_status.value,
            "artifacts": {key: value.to_dict() for key, value in self.artifacts.items()},
        }


@dataclass
class ProductionRegistry:
    """In-memory registry — no database, no real curriculum ingestion."""

    lessons: dict[str, LessonRegistryRecord] = field(default_factory=dict)

    def register_lesson(self, lesson: LessonModel, plan: ArtifactPlan) -> LessonRegistryRecord:
        record = LessonRegistryRecord(
            lesson_id=lesson.lesson_id,
            production_status=lesson.production_status,
        )
        for artifact in plan.artifacts:
            record.artifacts[artifact.artifact_id] = RegistryArtifactRecord(
                artifact_id=artifact.artifact_id,
                artifact_type=artifact.artifact_type,
                planned=True,
            )
        self.lessons[lesson.lesson_id] = record
        return record

    def get(self, lesson_id: str) -> LessonRegistryRecord | None:
        return self.lessons.get(lesson_id)

    def mark_completed(self, lesson_id: str, artifact_id: str) -> None:
        record = self._require(lesson_id)
        artifact = record.artifacts[artifact_id]
        artifact.completed = True

    def mark_validated(self, lesson_id: str, artifact_id: str, quality_status: QualityStatus) -> None:
        record = self._require(lesson_id)
        artifact = record.artifacts[artifact_id]
        artifact.validated = True
        artifact.quality_status = quality_status

    def mark_approved(self, lesson_id: str, artifact_id: str) -> None:
        record = self._require(lesson_id)
        artifact = record.artifacts[artifact_id]
        artifact.approved = True

    def summary(self) -> dict[str, Any]:
        return {
            "lesson_count": len(self.lessons),
            "lessons": {lesson_id: record.to_dict() for lesson_id, record in self.lessons.items()},
        }

    def _require(self, lesson_id: str) -> LessonRegistryRecord:
        record = self.lessons.get(lesson_id)
        if record is None:
            raise KeyError(f"Lesson not registered: {lesson_id}")
        return record

    @classmethod
    def from_plan(cls, lesson: LessonModel, plan: ArtifactPlan) -> ProductionRegistry:
        registry = cls()
        registry.register_lesson(lesson, plan)
        return registry
