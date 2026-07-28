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
    priority: ContentPriority | None = None
    source_ref: str = ""
    notes: str = ""
    manual_classification_required: bool = True

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        if self.priority is not None:
            payload["priority"] = self.priority.value
        else:
            payload["priority"] = None
        return payload

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> ContentItem:
        priority_raw = raw.get("priority")
        priority = ContentPriority(priority_raw) if priority_raw else None
        return cls(
            content_id=str(raw["content_id"]),
            title=str(raw["title"]),
            priority=priority,
            source_ref=str(raw.get("source_ref") or ""),
            notes=str(raw.get("notes") or ""),
            manual_classification_required=bool(raw.get("manual_classification_required", True)),
        )


@dataclass
class ContentMap:
    lesson_id: str
    items: list[ContentItem] = field(default_factory=list)

    def unclassified(self) -> list[ContentItem]:
        return [item for item in self.items if item.priority is None]

    def by_priority(self, priority: ContentPriority) -> list[ContentItem]:
        return [item for item in self.items if item.priority == priority]

    def to_dict(self) -> dict[str, Any]:
        return {
            "lesson_id": self.lesson_id,
            "items": [item.to_dict() for item in self.items],
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> ContentMap:
        items = [ContentItem.from_dict(item) for item in raw.get("items") or []]
        return cls(lesson_id=str(raw["lesson_id"]), items=items)
