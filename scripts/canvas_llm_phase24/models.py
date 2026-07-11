from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class SourceEvidence:
    source_type: str
    source_ref: str
    details: str
    owner_confirmed: bool = False


@dataclass
class RuleExplanation:
    rule_id: str
    decision_layer: str
    explanation: str


@dataclass
class Confidence:
    level: str
    score: float
    rationale: str = ""


@dataclass
class TeacherOverride:
    subject: str
    week_code: str
    day: str
    field: str
    value: str
    scope: str
    timestamp: str
    reason: str = ""
    revision: int = 1


@dataclass
class TeacherCorrection:
    subject: str
    week_code: str
    day: str
    predicted_value: str
    approved_value: str
    correction_scope: str
    timestamp: str
    reason: str = ""
    source_rule: str = ""
    revision: int = 1


@dataclass
class UnresolvedDecision:
    decision_id: str
    subject: str
    week_code: str
    day: str
    reason: str
    candidates: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class PredictedResourceRequirement:
    resource_type: str
    lesson_ref: str | None = None
    variant: str | None = None
    resolution_status: str = "unresolved"
    requires_review: bool = True
    verified_url: str | None = None


@dataclass
class PredictedInstructionalEvent:
    week_code: str
    subject: str
    weekday: str
    event_type: str
    lesson_number: int | None = None
    assessment_number: int | None = None
    in_class_title: str = ""
    at_home_title: str = ""
    resource_requirements: list[PredictedResourceRequirement] = field(default_factory=list)
    source_pacing_reference: str = ""
    previous_instructional_state: dict[str, Any] = field(default_factory=dict)
    rules_applied: list[str] = field(default_factory=list)
    explanation: list[str] = field(default_factory=list)
    confidence: Confidence = field(default_factory=lambda: Confidence("medium", 0.5))
    requires_review: bool = False
    manual_override_state: str = "none"
    review_state: str = "needs_review"
    source_evidence: list[SourceEvidence] = field(default_factory=list)
    rule_explanations: list[RuleExplanation] = field(default_factory=list)
    decision_layer: str = ""
    canonical_week_code: str = ""
    teacher_override: TeacherOverride | None = None
    teacher_correction: TeacherCorrection | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["confidence"] = asdict(self.confidence)
        return payload


@dataclass
class PredictedLesson(PredictedInstructionalEvent):
    pass


@dataclass
class PredictedHomework(PredictedInstructionalEvent):
    pass


@dataclass
class PredictedAssessment(PredictedInstructionalEvent):
    pass


@dataclass
class WeekPrediction:
    week_code: str
    source_hierarchy: list[str]
    predictions: list[PredictedInstructionalEvent]
    unresolved_decisions: list[UnresolvedDecision]
    teacher_overrides: list[TeacherOverride]
    teacher_corrections: list[TeacherCorrection]
    pattern_records: list[dict[str, Any]]
    warnings: list[str]
    review_state: str
    provenance: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "weekCode": self.week_code,
            "sourceHierarchy": self.source_hierarchy,
            "predictions": [item.to_dict() for item in self.predictions],
            "unresolvedDecisions": [asdict(item) for item in self.unresolved_decisions],
            "teacherOverrides": [asdict(item) for item in self.teacher_overrides],
            "teacherCorrections": [asdict(item) for item in self.teacher_corrections],
            "patternRecords": self.pattern_records,
            "warnings": list(self.warnings),
            "reviewState": self.review_state,
            "provenance": list(self.provenance),
        }
