from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


def compact(value: Any) -> str:
    return " ".join(str(value or "").replace("\xa0", " ").split())


@dataclass
class ResourceIdentity:
    resource_id: str
    canonical_name: str
    subject: str
    program: str | None = None
    grade: str | None = None
    resource_type: str = ""
    lesson_ref: str | None = None
    lesson_number: int | None = None
    assessment_number: int | None = None
    unit: str | None = None
    chapter: str | None = None
    applicability: dict[str, Any] = field(default_factory=dict)
    source_provider: str | None = None
    source_reference: str | None = None
    content_hash: str | None = None
    filename: str | None = None
    file_size: int | None = None
    modified_at: str | None = None
    verification_status: str = "verified"
    availability_status: str = "available"
    visibility: str = "student-facing"
    deployment_policy: str = "approved-for-canvas-link"
    canvas_status: str = "unknown"
    notes: str = ""
    provenance: list[dict[str, Any]] = field(default_factory=list)
    revision: int = 1
    aliases: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["resourceId"] = payload.pop("resource_id")
        payload["canonicalName"] = payload.pop("canonical_name")
        payload["resourceType"] = payload.pop("resource_type")
        payload["lessonRef"] = payload.pop("lesson_ref")
        payload["lessonNumber"] = payload.pop("lesson_number")
        payload["assessmentNumber"] = payload.pop("assessment_number")
        payload["sourceProvider"] = payload.pop("source_provider")
        payload["sourceReference"] = payload.pop("source_reference")
        payload["contentHash"] = payload.pop("content_hash")
        payload["modifiedAt"] = payload.pop("modified_at")
        payload["verificationStatus"] = payload.pop("verification_status")
        payload["availabilityStatus"] = payload.pop("availability_status")
        payload["deploymentPolicy"] = payload.pop("deployment_policy")
        payload["canvasStatus"] = payload.pop("canvas_status")
        return payload


@dataclass
class ResourceRequirement:
    resource_type: str
    subject: str
    event_id: str
    week_code: str | None = None
    day: str | None = None
    lesson_ref: str | None = None
    lesson_number: int | None = None
    assessment_number: int | None = None
    variant: str | None = None
    assessment_family: str | None = None
    required_visibility: str = "student-facing"
    preferred_verification_status: str = "verified"
    required_deployment_policy: str = "approved-for-canvas-link"
    canvas_status: str = "unknown"
    title_hint: str = ""
    review_state: str = "needs_review"

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["resourceType"] = payload.pop("resource_type")
        payload["eventId"] = payload.pop("event_id")
        payload["weekCode"] = payload.pop("week_code")
        payload["day"] = payload.pop("day")
        payload["lessonRef"] = payload.pop("lesson_ref")
        payload["lessonNumber"] = payload.pop("lesson_number")
        payload["assessmentNumber"] = payload.pop("assessment_number")
        payload["assessmentFamily"] = payload.pop("assessment_family")
        payload["requiredVisibility"] = payload.pop("required_visibility")
        payload["preferredVerificationStatus"] = payload.pop("preferred_verification_status")
        payload["requiredDeploymentPolicy"] = payload.pop("required_deployment_policy")
        payload["canvasStatus"] = payload.pop("canvas_status")
        payload["titleHint"] = payload.pop("title_hint")
        payload["reviewState"] = payload.pop("review_state")
        return payload


@dataclass
class ResolutionEvidence:
    source_type: str
    source_ref: str
    details: str


@dataclass
class ResolvedResource:
    requirement: ResourceRequirement
    resolution_method: str
    confidence: float
    review_state: str
    explanation: list[str] = field(default_factory=list)
    source_evidence: list[ResolutionEvidence] = field(default_factory=list)
    ignored_candidates: list[dict[str, Any]] = field(default_factory=list)
    conflicts: list[dict[str, Any]] = field(default_factory=list)
    blocked_reason: str | None = None
    resource: ResourceIdentity | None = None
    linked: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "requirement": self.requirement.to_dict(),
            "resolutionMethod": self.resolution_method,
            "confidence": self.confidence,
            "reviewState": self.review_state,
            "explanation": list(self.explanation),
            "sourceEvidence": [asdict(item) for item in self.source_evidence],
            "ignoredCandidates": list(self.ignored_candidates),
            "conflicts": list(self.conflicts),
            "blockedReason": self.blocked_reason,
            "linked": self.linked,
            "resource": self.resource.to_dict() if self.resource else None,
        }


@dataclass
class ReviewQueueItem:
    event_id: str
    subject: str
    event_label: str
    required_resource_class: str
    status: str
    candidate_resources: list[dict[str, Any]] = field(default_factory=list)
    resolver_explanation: list[str] = field(default_factory=list)
    confidence: float = 0.0
    recommended_teacher_action: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["eventId"] = payload.pop("event_id")
        payload["eventLabel"] = payload.pop("event_label")
        payload["requiredResourceClass"] = payload.pop("required_resource_class")
        payload["candidateResources"] = payload.pop("candidate_resources")
        payload["resolverExplanation"] = payload.pop("resolver_explanation")
        payload["recommendedTeacherAction"] = payload.pop("recommended_teacher_action")
        payload["status"] = payload["status"].title()
        return payload


@dataclass
class RiskFinding:
    severity: str
    code: str
    message: str
    mitigation: str


@dataclass
class Phase25Packet:
    schema_version: int
    packet_id: str
    week_code: str
    generated_at: str
    source_kind: str
    source_hierarchy: list[str]
    contains_student_data: bool
    upstream_warnings: list[str]
    predictions: list[dict[str, Any]]
    resource_requirements: list[dict[str, Any]]
    resolved_resources: list[ResolvedResource]
    review_queue: list[ReviewQueueItem]
    phase23_preview: dict[str, Any]
    validation: dict[str, Any]
    risks: list[RiskFinding]
    provenance: list[dict[str, Any]]
    approval_state: str
    deployment_state: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "schemaVersion": self.schema_version,
            "packetId": self.packet_id,
            "weekCode": self.week_code,
            "generatedAt": self.generated_at,
            "sourceKind": self.source_kind,
            "sourceHierarchy": list(self.source_hierarchy),
            "containsStudentData": self.contains_student_data,
            "upstreamWarnings": list(self.upstream_warnings),
            "predictions": list(self.predictions),
            "resourceRequirements": list(self.resource_requirements),
            "resolvedResources": [item.to_dict() for item in self.resolved_resources],
            "reviewQueue": [item.to_dict() for item in self.review_queue],
            "phase23Preview": self.phase23_preview,
            "validation": self.validation,
            "risks": [asdict(item) for item in self.risks],
            "provenance": list(self.provenance),
            "approvalState": self.approval_state,
            "deploymentState": self.deployment_state,
        }
