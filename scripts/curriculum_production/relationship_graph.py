from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class RelationshipType(str, Enum):
    MATCHES = "matches"
    DEPENDS_ON = "depends_on"
    COVERS = "covers"
    MIRRORS = "mirrors"
    FEEDS = "feeds"


@dataclass
class RelationshipEdge:
    source: str
    target: str
    relationship: RelationshipType
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "relationship": self.relationship.value,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> RelationshipEdge:
        return cls(
            source=str(raw["source"]),
            target=str(raw["target"]),
            relationship=RelationshipType(str(raw["relationship"])),
            notes=str(raw.get("notes") or ""),
        )


@dataclass
class RelationshipGraph:
    lesson_id: str
    edges: list[RelationshipEdge] = field(default_factory=list)

    def add(self, source: str, target: str, relationship: RelationshipType, *, notes: str = "") -> None:
        self.edges.append(RelationshipEdge(source=source, target=target, relationship=relationship, notes=notes))

    def outgoing(self, node: str, relationship: RelationshipType | None = None) -> list[RelationshipEdge]:
        return [
            edge
            for edge in self.edges
            if edge.source == node and (relationship is None or edge.relationship == relationship)
        ]

    def has_edge(self, source: str, target: str, relationship: RelationshipType) -> bool:
        return any(
            edge.source == source and edge.target == target and edge.relationship == relationship
            for edge in self.edges
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "lesson_id": self.lesson_id,
            "edges": [edge.to_dict() for edge in self.edges],
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> RelationshipGraph:
        edges = [RelationshipEdge.from_dict(item) for item in raw.get("edges") or []]
        return cls(lesson_id=str(raw["lesson_id"]), edges=edges)

    @classmethod
    def default_lesson_graph(cls, lesson_id: str) -> RelationshipGraph:
        graph = cls(lesson_id=lesson_id)
        graph.add("presentation", "guided_notes", RelationshipType.MATCHES)
        graph.add("worksheet", "lesson_objective", RelationshipType.DEPENDS_ON)
        graph.add("assessment", "critical_content", RelationshipType.COVERS)
        graph.add("teacher_key", "student_resource", RelationshipType.MIRRORS)
        graph.add("vocabulary", "guided_notes", RelationshipType.FEEDS)
        graph.add("review", "assessment_targets", RelationshipType.COVERS)
        return graph


REQUIRED_RELATIONSHIPS: tuple[tuple[str, str, RelationshipType], ...] = (
    ("presentation", "guided_notes", RelationshipType.MATCHES),
    ("worksheet", "lesson_objective", RelationshipType.DEPENDS_ON),
    ("assessment", "critical_content", RelationshipType.COVERS),
    ("teacher_key", "student_resource", RelationshipType.MIRRORS),
    ("vocabulary", "guided_notes", RelationshipType.FEEDS),
    ("review", "assessment_targets", RelationshipType.COVERS),
)
