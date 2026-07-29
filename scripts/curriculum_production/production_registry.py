from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .approval_workflow import ApprovalRecord, ApprovalWorkflow, WorkflowState
from .artifact_plan import ArtifactPlan, PlannedArtifact
from .lesson_model import LessonModel, ProductionStatus
from .models import CheckStatus, ValidationReport


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
    readiness: str = "planned"

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "artifact_type": self.artifact_type,
            "planned": self.planned,
            "completed": self.completed,
            "validated": self.validated,
            "approved": self.approved,
            "quality_status": self.quality_status.value,
            "readiness": self.readiness,
        }


@dataclass
class LessonRegistryRecord:
    lesson_id: str
    production_status: ProductionStatus = ProductionStatus.PLANNED
    teacher_review_status: TeacherReviewStatus = TeacherReviewStatus.NOT_STARTED
    workflow_state: WorkflowState = WorkflowState.DRAFT
    validation_status: QualityStatus = QualityStatus.NOT_RUN
    completion_percent: float = 0.0
    approval_record: ApprovalRecord | None = None
    artifacts: dict[str, RegistryArtifactRecord] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "lesson_id": self.lesson_id,
            "production_status": self.production_status.value,
            "teacher_review_status": self.teacher_review_status.value,
            "workflow_state": self.workflow_state.value,
            "validation_status": self.validation_status.value,
            "completion_percent": round(self.completion_percent, 1),
            "artifacts": {key: value.to_dict() for key, value in self.artifacts.items()},
        }
        if self.approval_record is not None:
            payload["approval_record"] = self.approval_record.to_dict()
        return payload


@dataclass
class ProductionRegistry:
    """In-memory registry — no database, no real curriculum ingestion."""

    lessons: dict[str, LessonRegistryRecord] = field(default_factory=dict)

    def register_lesson(
        self,
        lesson: LessonModel,
        plan: ArtifactPlan,
        *,
        workflow: ApprovalWorkflow | None = None,
        validation_report: ValidationReport | None = None,
    ) -> LessonRegistryRecord:
        workflow_state = workflow.state if workflow else WorkflowState.DRAFT
        record = LessonRegistryRecord(
            lesson_id=lesson.lesson_id,
            production_status=lesson.production_status,
            workflow_state=workflow_state,
            teacher_review_status=_review_status(workflow_state),
        )
        for artifact in plan.artifacts:
            record.artifacts[artifact.artifact_id] = RegistryArtifactRecord(
                artifact_id=artifact.artifact_id,
                artifact_type=artifact.artifact_type,
                planned=True,
                readiness="planned",
            )
        if workflow and workflow.history:
            record.approval_record = workflow.history[-1]
        if validation_report is not None:
            record.validation_status = _quality_from_report(validation_report)
            record.completion_percent = compute_completion_percent(validation_report, plan)
        self.lessons[lesson.lesson_id] = record
        return record

    def get(self, lesson_id: str) -> LessonRegistryRecord | None:
        return self.lessons.get(lesson_id)

    def update_progress(self, lesson_id: str, validation_report: ValidationReport, plan: ArtifactPlan) -> None:
        record = self._require(lesson_id)
        record.validation_status = _quality_from_report(validation_report)
        record.completion_percent = compute_completion_percent(validation_report, plan)

    def mark_completed(self, lesson_id: str, artifact_id: str) -> None:
        record = self._require(lesson_id)
        artifact = record.artifacts[artifact_id]
        artifact.completed = True
        artifact.readiness = "completed"

    def mark_validated(self, lesson_id: str, artifact_id: str, quality_status: QualityStatus) -> None:
        record = self._require(lesson_id)
        artifact = record.artifacts[artifact_id]
        artifact.validated = True
        artifact.quality_status = quality_status
        artifact.readiness = "validated"

    def mark_approved(self, lesson_id: str, artifact_id: str) -> None:
        record = self._require(lesson_id)
        artifact = record.artifacts[artifact_id]
        artifact.approved = True
        artifact.readiness = "approved"

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
    def from_plan(
        cls,
        lesson: LessonModel,
        plan: ArtifactPlan,
        *,
        workflow: ApprovalWorkflow | None = None,
        validation_report: ValidationReport | None = None,
    ) -> ProductionRegistry:
        registry = cls()
        registry.register_lesson(lesson, plan, workflow=workflow, validation_report=validation_report)
        return registry


def compute_completion_percent(validation_report: ValidationReport, plan: ArtifactPlan) -> float:
    checkpoints = max(len(validation_report.checks), 1)
    passed = sum(1 for check in validation_report.checks if check.status == CheckStatus.PASS)
    artifact_bonus = sum(1 for artifact in plan.artifacts if artifact.linked_objective) / max(len(plan.artifacts), 1)
    base = (passed / checkpoints) * 85.0
    return min(100.0, round(base + artifact_bonus * 15.0, 1))


def _quality_from_report(report: ValidationReport) -> QualityStatus:
    if report.final_status == CheckStatus.FAIL:
        return QualityStatus.FAIL
    if report.final_status == CheckStatus.WARN:
        return QualityStatus.WARN
    return QualityStatus.PASS


def _review_status(state: WorkflowState) -> TeacherReviewStatus:
    mapping = {
        WorkflowState.DRAFT: TeacherReviewStatus.NOT_STARTED,
        WorkflowState.IN_REVIEW: TeacherReviewStatus.IN_REVIEW,
        WorkflowState.APPROVED: TeacherReviewStatus.APPROVED,
        WorkflowState.ARCHIVED: TeacherReviewStatus.CHANGES_REQUESTED,
    }
    return mapping.get(state, TeacherReviewStatus.NOT_STARTED)
