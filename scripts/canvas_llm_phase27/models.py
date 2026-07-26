from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

VALID_OBJECT_TYPES = {
    "page",
    "assignment",
    "module",
    "module_item",
    "announcement",
    "file",
    "course_target",
}

COMPARISON_STATUSES = {
    "CREATE",
    "UPDATE",
    "UNCHANGED",
    "BLOCKED",
    "CONFLICT",
    "OMIT",
    "DELETE_CANDIDATE",
}

_CREDENTIAL_MARKERS = (
    "authorization",
    "bearer ",
    "access_token",
    "api_key",
    "apikey",
    "password",
    "set-cookie",
    "sessiontoken",
)

_UNSAFE_URL_QUERY_MARKERS = ("token=", "access_token=", "api_key=", "password=")


class ModelValidationError(ValueError):
    pass


def reject_credential_content(value: str, where: str) -> None:
    lowered = value.lower()
    for marker in _CREDENTIAL_MARKERS:
        if marker in lowered:
            raise ModelValidationError(
                f"{where} appears to contain credential-like content ({marker!r})"
            )


def reject_unsafe_url(url: str, where: str) -> None:
    if not url:
        return
    lowered = url.lower()
    if not (lowered.startswith("https://") or lowered.startswith("http://")):
        raise ModelValidationError(f"{where} is not an http(s) URL: {url!r}")
    for marker in _UNSAFE_URL_QUERY_MARKERS:
        if marker in lowered:
            raise ModelValidationError(
                f"{where} embeds a credential-like query parameter ({marker!r})"
            )


def reject_executable_mutation_flags(provenance: list[dict[str, Any]], where: str) -> None:
    for entry in provenance:
        if not isinstance(entry, dict):
            continue
        if entry.get("executable") is True or entry.get("mutation") is True:
            raise ModelValidationError(
                f"{where} contains an executable mutation flag, which Phase 27 forbids"
            )


@dataclass
class DeployableObject:
    localObjectId: str
    objectType: str
    weekCode: str
    subject: str
    courseRef: str
    canonicalTitle: str
    canonicalBody: str
    contentHash: str
    bodyHash: str = ""
    metadataHash: str = ""
    placementHash: str = ""
    fullOperationHash: str = ""
    sourceRevision: int = 0
    approvalRevision: int = 0
    targetCanvasId: str = ""
    targetCanvasUrl: str = ""
    targetModuleId: str = ""
    targetModuleName: str = ""
    currentModulePosition: int | None = None
    desiredModulePosition: int | None = None
    desiredState: str = ""
    existingState: str = ""
    comparisonStatus: str = ""
    deploymentStatus: str = ""
    blockedReasons: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    provenance: list[dict[str, Any]] = field(default_factory=list)
    createdAt: str = ""
    updatedAt: str = ""

    def __post_init__(self) -> None:
        if self.objectType not in VALID_OBJECT_TYPES:
            raise ModelValidationError(f"invalid objectType: {self.objectType!r}")
        if not self.localObjectId or not self.localObjectId.strip():
            raise ModelValidationError("localObjectId is required")
        if not self.courseRef or not self.courseRef.strip():
            raise ModelValidationError("courseRef is required")
        if self.comparisonStatus and self.comparisonStatus not in COMPARISON_STATUSES:
            raise ModelValidationError(f"invalid comparisonStatus: {self.comparisonStatus!r}")
        reject_credential_content(self.canonicalTitle, "canonicalTitle")
        reject_credential_content(self.canonicalBody, "canonicalBody")
        reject_unsafe_url(self.targetCanvasUrl, "targetCanvasUrl")
        reject_executable_mutation_flags(self.provenance, "provenance")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SafetyDiffItem:
    objectId: str
    objectType: str
    localTitle: str
    targetCourse: str
    matchedCanvasId: str | None
    matchReason: str | None
    matchConfidence: float
    comparisonStatus: str
    fieldDiffs: list[dict[str, Any]]
    contentHashBefore: str
    contentHashAfter: str
    metadataHashBefore: str
    metadataHashAfter: str
    placementHashBefore: str
    placementHashAfter: str
    sourceRevision: int
    approvalState: str
    blockers: list[str]
    dependencies: list[str]
    driftCategory: str
    recommendedAction: str
    executable: bool = False

    def __post_init__(self) -> None:
        if self.objectType not in VALID_OBJECT_TYPES:
            raise ModelValidationError(f"invalid objectType: {self.objectType!r}")
        if self.comparisonStatus not in COMPARISON_STATUSES:
            raise ModelValidationError(f"invalid comparisonStatus: {self.comparisonStatus!r}")
        if not (0.0 <= self.matchConfidence <= 1.0):
            raise ModelValidationError("matchConfidence must be between 0 and 1")
        if self.executable is not False:
            raise ModelValidationError("Phase 27 SafetyDiffItem must never be executable")
        reject_credential_content(self.localTitle, "localTitle")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Dependency:
    fromObjectId: str
    toObjectId: str
    kind: str

    def __post_init__(self) -> None:
        if not self.fromObjectId or not self.toObjectId:
            raise ModelValidationError("dependency requires fromObjectId and toObjectId")
        if self.fromObjectId == self.toObjectId:
            raise ModelValidationError("dependency cannot reference itself")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Approval:
    objectId: str
    manifestRevision: int
    snapshotId: str
    approvedAt: str
    approvedBy: str
    state: str = "approved"

    def __post_init__(self) -> None:
        if self.state not in {"approved", "revoked", "invalidated"}:
            raise ModelValidationError(f"invalid approval state: {self.state!r}")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
