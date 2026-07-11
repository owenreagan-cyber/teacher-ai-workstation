from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


def compact(value: Any) -> str:
    return " ".join(str(value or "").replace("\xa0", " ").split())


def stable_id(*parts: Any) -> str:
    import hashlib

    payload = "|".join(map(str, parts)).encode("utf-8")
    return "p26-" + hashlib.sha256(payload).hexdigest()[:18]


@dataclass
class WeekSelection:
    code: str
    quarter: int
    starts_on: str
    ends_on: str
    display_subtitle: str
    shortened_week: bool = False
    no_school_days: list[str] = field(default_factory=list)
    quarter_boundary: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["startsOn"] = payload.pop("starts_on")
        payload["endsOn"] = payload.pop("ends_on")
        payload["displaySubtitle"] = payload.pop("display_subtitle")
        payload["shortenedWeek"] = payload.pop("shortened_week")
        payload["noSchoolDays"] = payload.pop("no_school_days")
        payload["quarterBoundary"] = payload.pop("quarter_boundary")
        return payload


@dataclass
class SubjectSnapshot:
    subject: str
    title: str
    readiness_state: str
    approval_state: str
    confidence: float
    source_hierarchy: list[str]
    predicted_instruction: list[dict[str, Any]]
    resolved_resources: list[dict[str, Any]]
    unresolved_resources: list[dict[str, Any]]
    blocked_resources: list[dict[str, Any]]
    teacher_edits: list[dict[str, Any]]
    production_preview_status: str
    assignment_policy: str = "enabled"
    why: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["readinessState"] = payload.pop("readiness_state")
        payload["approvalState"] = payload.pop("approval_state")
        payload["sourceHierarchy"] = payload.pop("source_hierarchy")
        payload["predictedInstruction"] = payload.pop("predicted_instruction")
        payload["resolvedResources"] = payload.pop("resolved_resources")
        payload["unresolvedResources"] = payload.pop("unresolved_resources")
        payload["blockedResources"] = payload.pop("blocked_resources")
        payload["teacherEdits"] = payload.pop("teacher_edits")
        payload["productionPreviewStatus"] = payload.pop("production_preview_status")
        payload["assignmentPolicy"] = payload.pop("assignment_policy")
        return payload


@dataclass
class ManifestOperation:
    type: str
    subject: str
    status: str
    reason: str = ""


@dataclass
class WorkstationPacket:
    schema_version: int
    packet_id: str
    week_code: str
    generated_at: str
    source_mode: str
    week_selection: dict[str, Any]
    source_pacing: dict[str, Any]
    teacher_brain: dict[str, Any]
    resource_resolution: dict[str, Any]
    production_packet: dict[str, Any]
    subject_workspaces: list[SubjectSnapshot]
    exception_inbox: list[dict[str, Any]]
    revision_history: list[dict[str, Any]]
    local_diff: list[dict[str, Any]]
    approval_panel: dict[str, Any]
    readiness: dict[str, Any]
    export_package_preview: dict[str, Any]
    deployment_manifest_preview: dict[str, Any]
    validation: dict[str, Any]
    provenance: list[dict[str, Any]]
    local_state: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        def as_payload(item: Any) -> Any:
            return item.to_dict() if hasattr(item, "to_dict") else item

        return {
            "schemaVersion": self.schema_version,
            "packetId": self.packet_id,
            "weekCode": self.week_code,
            "generatedAt": self.generated_at,
            "sourceMode": self.source_mode,
            "weekSelection": self.week_selection,
            "sourcePacing": self.source_pacing,
            "teacherBrain": self.teacher_brain,
            "resourceResolution": self.resource_resolution,
            "productionPacket": self.production_packet,
            "subjectWorkspaces": [as_payload(item) for item in self.subject_workspaces],
            "exceptionInbox": self.exception_inbox,
            "revisionHistory": self.revision_history,
            "localDiff": self.local_diff,
            "approvalPanel": self.approval_panel,
            "readiness": self.readiness,
            "exportPackagePreview": self.export_package_preview,
            "deploymentManifestPreview": self.deployment_manifest_preview,
            "validation": self.validation,
            "provenance": list(self.provenance),
            "localState": self.local_state,
        }
