from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from scripts.curriculum_production.content_map import ContentItem, ContentMap, ContentPriority
from scripts.curriculum_production.lesson_package import LessonPackagePlan
from scripts.curriculum_production.models import CheckStatus, ValidationReport


class RegistryEntryState(str, Enum):
    ACTIVE = "active"
    OMITTED = "omitted"


@dataclass
class RegistryEntry:
    entry_id: str
    label: str
    artifact_refs: list[str] = field(default_factory=list)
    state: RegistryEntryState = RegistryEntryState.ACTIVE

    def to_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "label": self.label,
            "artifact_refs": self.artifact_refs,
            "state": self.state.value,
        }


@dataclass
class NamedRegistry:
    name: str
    entries: dict[str, RegistryEntry] = field(default_factory=dict)

    def add(self, entry: RegistryEntry) -> None:
        if entry.entry_id in self.entries:
            raise ValueError(f"Duplicate {self.name} entry: {entry.entry_id}")
        self.entries[entry.entry_id] = entry

    def validate(self, valid_refs: set[str] | None = None) -> ValidationReport:
        report = ValidationReport(scope=self.name)
        if not self.entries:
            report.add(CheckStatus.WARN, f"{self.name} registry is empty")
            return report
        duplicates = _find_duplicate_labels(self.entries.values())
        if duplicates:
            report.add(CheckStatus.WARN, f"{self.name} duplicate labels detected", details=", ".join(duplicates))
        if valid_refs is not None:
            for entry in self.entries.values():
                for ref in entry.artifact_refs:
                    if ref not in valid_refs:
                        report.add(
                            CheckStatus.FAIL,
                            f"{self.name} broken artifact reference",
                            details=f"{entry.entry_id} → {ref}",
                        )
        broken = [e.entry_id for e in self.entries.values() if e.state == RegistryEntryState.ACTIVE and not e.artifact_refs]
        if broken and self.name in {"Vocabulary", "Objective", "Assessment"}:
            report.add(CheckStatus.WARN, f"{self.name} entries missing artifact references", details=", ".join(broken))
        if report.final_status == CheckStatus.PASS:
            report.add(CheckStatus.PASS, f"{self.name} registry validated ({len(self.entries)} entries)")
        return report


@dataclass
class LessonRegistries:
    vocabulary: NamedRegistry
    objectives: NamedRegistry
    examples: NamedRegistry
    diagrams: NamedRegistry
    questions: NamedRegistry
    assessments: NamedRegistry
    artifacts: NamedRegistry

    def validate_all(self, valid_refs: set[str] | None = None) -> ValidationReport:
        report = ValidationReport(scope="registries")
        for registry in (
            self.vocabulary,
            self.objectives,
            self.examples,
            self.diagrams,
            self.questions,
            self.assessments,
            self.artifacts,
        ):
            section = registry.validate(valid_refs=valid_refs)
            report.checks.extend(section.checks)
        if report.final_status == CheckStatus.PASS:
            report.add(CheckStatus.PASS, "All shared registries validated")
        return report

    def to_dict(self) -> dict[str, Any]:
        return {
            "vocabulary": {k: v.to_dict() for k, v in self.vocabulary.entries.items()},
            "objectives": {k: v.to_dict() for k, v in self.objectives.entries.items()},
            "examples": {k: v.to_dict() for k, v in self.examples.entries.items()},
            "diagrams": {k: v.to_dict() for k, v in self.diagrams.entries.items()},
            "questions": {k: v.to_dict() for k, v in self.questions.entries.items()},
            "assessments": {k: v.to_dict() for k, v in self.assessments.entries.items()},
            "artifacts": {k: v.to_dict() for k, v in self.artifacts.entries.items()},
        }


def build_registries(package: LessonPackagePlan, content_map: ContentMap) -> LessonRegistries:
    registries = LessonRegistries(
        vocabulary=NamedRegistry("Vocabulary"),
        objectives=NamedRegistry("Objective"),
        examples=NamedRegistry("Example"),
        diagrams=NamedRegistry("Diagram"),
        questions=NamedRegistry("Question"),
        assessments=NamedRegistry("Assessment"),
        artifacts=NamedRegistry("Artifact"),
    )
    artifact_types = [a.artifact_type for a in package.artifact_plan.artifacts]
    for artifact_type in artifact_types:
        registries.artifacts.add(
            RegistryEntry(entry_id=artifact_type, label=artifact_type, artifact_refs=[artifact_type])
        )
    for index, objective in enumerate(package.objectives, start=1):
        registries.objectives.add(
            RegistryEntry(
                entry_id=f"objective-{index}",
                label=objective,
                artifact_refs=artifact_types,
            )
        )
    for index, term in enumerate(package.vocabulary, start=1):
        refs = _default_vocab_refs(artifact_types)
        registries.vocabulary.add(
            RegistryEntry(entry_id=f"vocab-{index}", label=term, artifact_refs=refs)
        )
    for index, target in enumerate(package.metadata.get("assessment_targets") or [], start=1):
        registries.assessments.add(
            RegistryEntry(
                entry_id=f"assessment-{index}",
                label=target,
                artifact_refs=["assessment", "worksheet", "teacher_key"],
            )
        )
    for item in content_map.items:
        if item.priority == ContentPriority.OMIT:
            continue
        if "example" in item.tags or "worked" in item.title.lower():
            registries.examples.add(
                RegistryEntry(
                    entry_id=item.content_id,
                    label=item.title,
                    artifact_refs=["presentation", "guided_notes", "worksheet"],
                )
            )
        if "diagram" in item.tags or "chart" in item.title.lower():
            registries.diagrams.add(
                RegistryEntry(
                    entry_id=item.content_id,
                    label=item.title,
                    artifact_refs=["presentation", "worksheet"],
                )
            )
        if item.priority == ContentPriority.CRITICAL and "question" in item.tags:
            registries.questions.add(
                RegistryEntry(entry_id=item.content_id, label=item.title, artifact_refs=["worksheet", "assessment"])
            )
    return registries


def _default_vocab_refs(artifact_types: list[str]) -> list[str]:
    preferred = ["presentation", "guided_notes", "worksheet", "vocabulary", "assessment", "teacher_key"]
    return [t for t in preferred if t in artifact_types] or list(artifact_types)


def _find_duplicate_labels(entries: Any) -> list[str]:
    seen: dict[str, int] = {}
    for entry in entries:
        key = entry.label.strip().lower()
        seen[key] = seen.get(key, 0) + 1
    return [label for label, count in seen.items() if count > 1]
