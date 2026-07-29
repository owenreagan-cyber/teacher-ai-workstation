from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from scripts.curriculum_production.content_map import ContentMap, ContentPriority
from scripts.curriculum_production.lesson_package import LessonPackagePlan


@dataclass
class LessonReviewPacket:
    lesson_id: str
    metadata: dict[str, Any]
    objectives: list[str]
    standards: list[str]
    vocabulary: list[str]
    critical_content: list[dict[str, Any]]
    high_priority_content: list[dict[str, Any]]
    supporting_content: list[dict[str, Any]]
    teacher_background: list[dict[str, Any]]
    omitted_content: list[dict[str, Any]]
    assessment_targets: list[str]
    instructional_sequence: dict[str, Any]
    artifact_plan: dict[str, Any]
    validation_summary: dict[str, Any]
    approval_history: list[dict[str, Any]]
    teacher_notes: str
    production_status: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "lesson_id": self.lesson_id,
            "metadata": self.metadata,
            "objectives": self.objectives,
            "standards": self.standards,
            "vocabulary": self.vocabulary,
            "critical_content": self.critical_content,
            "high_priority_content": self.high_priority_content,
            "supporting_content": self.supporting_content,
            "teacher_background": self.teacher_background,
            "omitted_content": self.omitted_content,
            "assessment_targets": self.assessment_targets,
            "instructional_sequence": self.instructional_sequence,
            "artifact_plan": self.artifact_plan,
            "validation_summary": self.validation_summary,
            "approval_history": self.approval_history,
            "teacher_notes": self.teacher_notes,
            "production_status": self.production_status,
        }


def build_review_packet(package: LessonPackagePlan, content_map: ContentMap) -> LessonReviewPacket:
    record = package.registry.get(package.lesson_id)
    production_status = record.production_status.value if record else "unknown"
    approval_history: list[dict[str, Any]] = []
    if record and record.approval_record:
        approval_history = [record.approval_record.to_dict()]
    return LessonReviewPacket(
        lesson_id=package.lesson_id,
        metadata=package.metadata,
        objectives=package.objectives,
        standards=list(package.metadata.get("standards") or []),
        vocabulary=package.vocabulary,
        critical_content=[item.to_dict() for item in content_map.by_priority(ContentPriority.CRITICAL)],
        high_priority_content=[item.to_dict() for item in content_map.by_priority(ContentPriority.HIGH_PRIORITY)],
        supporting_content=[item.to_dict() for item in content_map.by_priority(ContentPriority.SUPPORTING)],
        teacher_background=[item.to_dict() for item in content_map.by_priority(ContentPriority.TEACHER_BACKGROUND)],
        omitted_content=[item.to_dict() for item in content_map.by_priority(ContentPriority.OMIT)],
        assessment_targets=list(package.metadata.get("assessment_targets") or []),
        instructional_sequence=package.instructional_sequence.to_dict(),
        artifact_plan=package.artifact_plan.to_dict(),
        validation_summary=package.validation_summary.to_dict(),
        approval_history=approval_history,
        teacher_notes=package.teacher_notes,
        production_status=production_status,
    )


def render_review_packet_markdown(packet: LessonReviewPacket) -> str:
    lines = [
        "# Lesson Review Packet",
        "",
        f"**Lesson ID:** {packet.lesson_id}",
        f"**Title:** {packet.metadata.get('title', '')}",
        f"**Production Status:** {packet.production_status}",
        "",
        "## Objective",
        "",
    ]
    lines.extend(f"- {obj}" for obj in packet.objectives or ["(none)"])
    lines.extend(["", "## Standards", ""])
    lines.extend(f"- {std}" for std in packet.standards or ["(none)"])
    lines.extend(["", "## Vocabulary", ""])
    lines.extend(f"- {term}" for term in packet.vocabulary or ["(none)"])
    for heading, bucket in (
        ("Critical Content", packet.critical_content),
        ("High Priority Content", packet.high_priority_content),
        ("Supporting Content", packet.supporting_content),
        ("Teacher Background", packet.teacher_background),
        ("Omitted Content", packet.omitted_content),
    ):
        lines.extend(["", f"## {heading}", ""])
        if bucket:
            for item in bucket:
                lines.append(f"- {item.get('title', item.get('content_id', 'item'))}")
        else:
            lines.append("- (none)")
    lines.extend(["", "## Assessment Targets", ""])
    lines.extend(f"- {target}" for target in packet.assessment_targets or ["(none)"])
    lines.extend(["", "## Instructional Sequence", ""])
    for step in packet.instructional_sequence.get("steps") or []:
        lines.append(f"- {step}")
    lines.extend(["", "## Validation Summary", "", f"Status: {packet.validation_summary.get('final_status', 'unknown')}", ""])
    lines.extend(["", "## Teacher Notes", "", packet.teacher_notes or "(none)", ""])
    return "\n".join(lines)


def render_review_packet_yaml(packet: LessonReviewPacket) -> str:
    try:
        import yaml

        return yaml.safe_dump(packet.to_dict(), sort_keys=False, allow_unicode=True)
    except ImportError:  # pragma: no cover
        return "# YAML output requires PyYAML\n"
