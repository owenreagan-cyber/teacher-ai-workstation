from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class ArtifactStatus(str, Enum):
    PLANNED = "planned"
    OUTLINED = "outlined"
    DRAFTED = "drafted"
    VALIDATED = "validated"
    APPROVED = "approved"
    BLOCKED = "blocked"


class ValidationState(str, Enum):
    NOT_STARTED = "not_started"
    PENDING = "pending"
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


STANDARD_ARTIFACT_TYPES = (
    "presentation",
    "guided_notes",
    "worksheet",
    "teacher_script",
    "vocabulary",
    "assessment",
    "teacher_key",
    "review",
)


@dataclass
class PlannedArtifact:
    artifact_id: str
    artifact_type: str
    status: ArtifactStatus = ArtifactStatus.PLANNED
    dependencies: list[str] = field(default_factory=list)
    validation_state: ValidationState = ValidationState.NOT_STARTED
    required_subject: str | None = None
    quality_gate: str = ""
    approved: bool = False
    linked_objective: bool = False
    linked_critical_content_ids: list[str] = field(default_factory=list)
    linked_sequence_steps: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["status"] = self.status.value
        payload["validation_state"] = self.validation_state.value
        return payload

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> PlannedArtifact:
        status = ArtifactStatus(str(raw.get("status", ArtifactStatus.PLANNED.value)))
        validation = ValidationState(str(raw.get("validation_state", ValidationState.NOT_STARTED.value)))
        return cls(
            artifact_id=str(raw["artifact_id"]),
            artifact_type=str(raw["artifact_type"]),
            status=status,
            dependencies=list(raw.get("dependencies") or []),
            validation_state=validation,
            required_subject=raw.get("required_subject"),
            quality_gate=str(raw.get("quality_gate") or ""),
            approved=bool(raw.get("approved", False)),
            linked_objective=bool(raw.get("linked_objective", False)),
            linked_critical_content_ids=list(raw.get("linked_critical_content_ids") or []),
            linked_sequence_steps=list(raw.get("linked_sequence_steps") or []),
        )


@dataclass
class ArtifactPlan:
    lesson_id: str
    artifacts: list[PlannedArtifact] = field(default_factory=list)

    def by_type(self, artifact_type: str) -> list[PlannedArtifact]:
        return [a for a in self.artifacts if a.artifact_type == artifact_type]

    def get(self, artifact_id: str) -> PlannedArtifact | None:
        for artifact in self.artifacts:
            if artifact.artifact_id == artifact_id:
                return artifact
        return None

    def to_dict(self) -> dict[str, Any]:
        return {
            "lesson_id": self.lesson_id,
            "artifacts": [artifact.to_dict() for artifact in self.artifacts],
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> ArtifactPlan:
        artifacts = [PlannedArtifact.from_dict(item) for item in raw.get("artifacts") or []]
        return cls(lesson_id=str(raw["lesson_id"]), artifacts=artifacts)

    @classmethod
    def default_lesson_plan(cls, lesson_id: str, subject: str) -> ArtifactPlan:
        """Planning scaffold only — no generated content."""
        gates = {
            "presentation": "projector-slides",
            "guided_notes": "guided-notes-letter",
            "worksheet": "worksheet-letter",
            "teacher_script": "worksheet-letter",
            "vocabulary": "worksheet-letter",
            "assessment": "quiz-letter",
            "teacher_key": "teacher-key-letter",
            "review": "quiz-letter",
        }
        artifacts: list[PlannedArtifact] = []
        for artifact_type in STANDARD_ARTIFACT_TYPES:
            artifacts.append(
                PlannedArtifact(
                    artifact_id=f"{lesson_id}-{artifact_type}",
                    artifact_type=artifact_type,
                    dependencies=_default_dependencies(artifact_type),
                    required_subject=subject,
                    quality_gate=gates.get(artifact_type, "worksheet-letter"),
                )
            )
        return cls(lesson_id=lesson_id, artifacts=artifacts)


def populate_artifact_plan_references(
    plan: ArtifactPlan,
    *,
    critical_content_ids: list[str],
    sequence_steps: list[str],
) -> None:
    """Attach objective/critical/sequence references — planning metadata only."""
    for artifact in plan.artifacts:
        artifact.linked_objective = True
        artifact.linked_critical_content_ids = list(critical_content_ids)
        artifact.linked_sequence_steps = list(sequence_steps)


def _default_dependencies(artifact_type: str) -> list[str]:
    mapping = {
        "guided_notes": ["presentation"],
        "worksheet": ["guided_notes"],
        "teacher_script": ["presentation"],
        "vocabulary": ["guided_notes"],
        "assessment": ["worksheet"],
        "teacher_key": ["worksheet", "assessment"],
        "review": ["assessment"],
    }
    return mapping.get(artifact_type, [])
