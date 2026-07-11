from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class DeployableObject:
    localObjectId: str
    objectType: str
    weekCode: str
    subject: str
    canonicalTitle: str
    canonicalBody: str
    contentHash: str
    sourceRevision: int = 0
    approvalRevision: int = 0
    targetCanvasId: str = ""
    targetCanvasUrl: str = ""
    moduleRef: str = ""
    modulePosition: int = 0
    desiredState: str = ""
    existingState: str = ""
    comparisonStatus: str = ""
    deploymentStatus: str = ""
    blockedReasons: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    provenance: list[dict[str, Any]] = field(default_factory=list)
    createdAt: str = ""
    updatedAt: str = ""
    courseRef: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SafetyDiffItem:
    objectId: str
    objectType: str
    localTitle: str
    targetCourse: str
    comparisonStatus: str
    fieldDiffs: list[dict[str, Any]]
    contentHashBefore: str
    contentHashAfter: str
    sourceRevision: int
    approvalState: str
    blockers: list[str]
    dependencies: list[str]
    confidence: float
    recommendedAction: str
    targetCanvasId: str = ""
    targetCanvasUrl: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

