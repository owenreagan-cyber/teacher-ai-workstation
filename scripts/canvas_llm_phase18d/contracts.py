"""Phase 18D pure write-intent contracts (import-safe).

These are pure data structures only. Importing this module must never import
Canvas execution code, writers, connectors, mutation clients, or token/network
modules. Phase 18D is a pure pre-execution layer: it describes *intent*, never
execution.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class OperationType(str, Enum):
    """Explicit operation classes. No execution methods live here."""

    CREATE = "CREATE"
    UPDATE = "UPDATE"
    NO_CHANGE = "NO_CHANGE"
    BLOCKED = "BLOCKED"
    SKIP = "SKIP"


class ObjectType(str, Enum):
    AGENDA_PAGE = "agenda_page"
    ASSIGNMENT = "assignment"
    ANNOUNCEMENT = "announcement"


class PacketReadiness(str, Enum):
    """Global dry-run packet readiness. Fail-closed by default."""

    READY_FOR_OWNER_REVIEW = "READY_FOR_OWNER_REVIEW"
    BLOCKED_UNRESOLVED = "BLOCKED_UNRESOLVED"
    BLOCKED_POLICY = "BLOCKED_POLICY"
    BLOCKED_MISSING_CONFIG = "BLOCKED_MISSING_CONFIG"
    BLOCKED_REMOTE_DRIFT = "BLOCKED_REMOTE_DRIFT"
    BLOCKED_OWNERSHIP = "BLOCKED_OWNERSHIP"
    BLOCKED_COLLISION = "BLOCKED_COLLISION"
    BLOCKED_PROTECTED = "BLOCKED_PROTECTED"
    BLOCKED_STALE = "BLOCKED_STALE"
    BLOCKED_READ_FAILURE = "BLOCKED_READ_FAILURE"


class RiskTier(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ChangeKind(str, Enum):
    NO_CHANGE = "NO_CHANGE"
    ADD = "ADD"
    REMOVE = "REMOVE"
    UPDATE = "UPDATE"


class DiffClassification(str, Enum):
    """Safety-diff classification of a single intent."""

    NO_CHANGE = "NO_CHANGE"
    SAFE_CREATE = "SAFE_CREATE"
    SAFE_UPDATE = "SAFE_UPDATE"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    BLOCKED = "BLOCKED"
    SKIP = "SKIP"


def _ser(value: Any) -> Any:
    """Deterministic serialization helper: enums -> value, nested dataclasses -> dict."""
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(k): _ser(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_ser(v) for v in value]
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return value.to_dict()
    return value


@dataclass
class SnapshotObject:
    """A single live Canvas object captured read-only for dry-run comparison."""

    object_id: str
    object_type: str
    course: str
    locator: str
    title: str
    current_state: dict[str, Any] = field(default_factory=dict)
    content_hash: str = ""
    managed: bool = False
    baseline_hash: str = ""

    def to_dict(self) -> dict[str, Any]:
        return _ser(asdict(self))


@dataclass
class CanvasSnapshot:
    """Read-only live Canvas state snapshot (pure data; no fetch lives here)."""

    week_code: str
    snapshot_id: str
    captured_at: str = ""
    objects: list[SnapshotObject] = field(default_factory=list)
    fetch_errors: list[str] = field(default_factory=list)
    read_failure: bool = False
    read_failure_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return _ser(asdict(self))

    def index(self) -> dict[tuple[str, str, str], list[SnapshotObject]]:
        index: dict[tuple[str, str, str], list[SnapshotObject]] = {}
        for obj in self.objects:
            index.setdefault((obj.course, obj.object_type, obj.locator), []).append(obj)
        return index


@dataclass
class FieldDiff:
    field: str
    current: Any
    desired: Any
    change: str


@dataclass
class SafetyDiffItem:
    intent_id: str
    object_type: str
    course: str
    locator: str
    operation: str
    classification: str
    risk: str
    source: str
    blockers: list[str] = field(default_factory=list)
    field_diffs: list[FieldDiff] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return _ser(asdict(self))


@dataclass
class DeploymentIntent:
    """A proposed (never executed) Canvas mutation, fully traceable to canonical source."""

    id: str
    operation: str
    object_type: str
    course: str
    canonical_source: str
    target_locator: str
    desired_state: dict[str, Any] = field(default_factory=dict)
    current_state: dict[str, Any] = field(default_factory=dict)
    provenance: list[dict[str, Any]] = field(default_factory=list)
    preconditions: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    risk: str = RiskTier.LOW.value
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return _ser(asdict(self))


@dataclass
class DryRunPacket:
    """Deterministic dry-run deployment packet. Never executable by this package."""

    week_code: str
    canonical_plan_identity: str
    canonical_revision: str
    preview_identity: str
    preview_hash: str
    snapshot_identity: str
    snapshot_hash: str
    target_environment: str
    intents: list[DeploymentIntent] = field(default_factory=list)
    blocked: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    no_change: list[str] = field(default_factory=list)
    provenance: list[dict[str, Any]] = field(default_factory=list)
    readiness: str = PacketReadiness.BLOCKED_STALE.value
    packet_hash: str = ""

    def to_dict(self) -> dict[str, Any]:
        return _ser(asdict(self))

    def intent_by_id(self) -> dict[str, DeploymentIntent]:
        return {intent.id: intent for intent in self.intents}


@dataclass
class ApprovalRecord:
    """Owner-approval contract for a *future* write-enabled phase. Not executed here."""

    packet_hash: str
    reviewer: str
    approved_at: str
    scope: str
    approved_intent_ids: list[str] = field(default_factory=list)
    preconditions: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return _ser(asdict(self))


@dataclass
class DryRunContext:
    """Read-only runtime state for dry-run assembly. Never carries credentials."""

    canvas_config: dict[str, Any] = field(default_factory=dict)
    due_time_policy: str = "unresolved"  # "resolved" | "unresolved"
    due_time_reason: str = "Canvas assignment due-time convention remains owner-unresolved"
    resolved_due_time: str = ""  # explicit; only honored when due_time_policy == "resolved"
    publish_policy: str = "unresolved"  # "resolved" | "unresolved"
    resolved_publish_state: str = ""  # "published" | "unpublished" when publish_policy == "resolved"
    target_environment: str = "sandbox"
    legacy_fixtures: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return _ser(asdict(self))


__all__ = [
    "ApprovalRecord",
    "CanvasSnapshot",
    "ChangeKind",
    "DeploymentIntent",
    "DiffClassification",
    "DryRunContext",
    "DryRunPacket",
    "FieldDiff",
    "ObjectType",
    "OperationType",
    "PacketReadiness",
    "RiskTier",
    "SafetyDiffItem",
    "SnapshotObject",
]
