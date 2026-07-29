from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class ContentPriority(str, Enum):
    """Manual classification tiers — never auto-assigned by the engine."""

    CRITICAL = "critical"
    HIGH_PRIORITY = "high_priority"
    SUPPORTING = "supporting"
    TEACHER_BACKGROUND = "teacher_background"
    OMIT = "omit"


class ContentApprovalState(str, Enum):
    DRAFT = "draft"
    APPROVED = "approved"


class ItemValidationState(str, Enum):
    NOT_STARTED = "not_started"
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


PRIORITY_ORDER = (
    ContentPriority.CRITICAL,
    ContentPriority.HIGH_PRIORITY,
    ContentPriority.SUPPORTING,
    ContentPriority.TEACHER_BACKGROUND,
    ContentPriority.OMIT,
)


@dataclass
class ContentItem:
    content_id: str
    title: str
    description: str = ""
    source_ref: str = ""
    priority: ContentPriority | None = None
    subject: str = ""
    tags: list[str] = field(default_factory=list)
    teacher_notes: str = ""
    approval_state: ContentApprovalState = ContentApprovalState.DRAFT
    validation_state: ItemValidationState = ItemValidationState.NOT_STARTED
    supports_objective: bool = False
    supports_assessment_target: str = ""
    linked_sequence_step: str = ""
    notes: str = ""
    manual_classification_required: bool = True
    artifact_plan_refs: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["priority"] = self.priority.value if self.priority else None
        payload["approval_state"] = self.approval_state.value
        payload["validation_state"] = self.validation_state.value
        return payload

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> ContentItem:
        priority_raw = raw.get("priority")
        priority = ContentPriority(priority_raw) if priority_raw else None
        return cls(
            content_id=str(raw["content_id"]),
            title=str(raw["title"]),
            description=str(raw.get("description") or ""),
            source_ref=str(raw.get("source_ref") or ""),
            priority=priority,
            subject=str(raw.get("subject") or ""),
            tags=list(raw.get("tags") or []),
            teacher_notes=str(raw.get("teacher_notes") or raw.get("notes") or ""),
            approval_state=ContentApprovalState(str(raw.get("approval_state", ContentApprovalState.DRAFT.value))),
            validation_state=ItemValidationState(str(raw.get("validation_state", ItemValidationState.NOT_STARTED.value))),
            supports_objective=bool(raw.get("supports_objective", False)),
            supports_assessment_target=str(raw.get("supports_assessment_target") or ""),
            linked_sequence_step=str(raw.get("linked_sequence_step") or ""),
            notes=str(raw.get("notes") or ""),
            manual_classification_required=bool(raw.get("manual_classification_required", True)),
            artifact_plan_refs=list(raw.get("artifact_plan_refs") or []),
        )


@dataclass
class ContentMap:
    lesson_id: str
    items: list[ContentItem] = field(default_factory=list)

    def unclassified(self) -> list[ContentItem]:
        return [item for item in self.items if item.priority is None]

    def by_priority(self, priority: ContentPriority) -> list[ContentItem]:
        return [item for item in self.items if item.priority == priority]

    def critical(self) -> list[ContentItem]:
        return self.by_priority(ContentPriority.CRITICAL)

    def omit_in_plan(self) -> list[ContentItem]:
        return [item for item in self.items if item.priority == ContentPriority.OMIT and item.artifact_plan_refs]

    def to_dict(self) -> dict[str, Any]:
        return {
            "lesson_id": self.lesson_id,
            "items": [item.to_dict() for item in self.items],
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> ContentMap:
        items = [ContentItem.from_dict(item) for item in raw.get("items") or []]
        return cls(lesson_id=str(raw["lesson_id"]), items=items)
