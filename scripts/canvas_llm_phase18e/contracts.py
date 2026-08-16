"""Phase 18E pure execution-precondition contracts (import-safe).

These are pure data structures only. Importing this module must never import
Canvas execution code, writers, connectors, mutation clients, or token/network
modules. Phase 18E is a pure pre-execution policy and validation layer: it
describes *readiness* and a future writer *request*, never execution.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class ReadinessState(str, Enum):
    """Execution-readiness states for a single intent (fail closed by default)."""

    READY_FOR_EXECUTION_REVIEW = "READY_FOR_EXECUTION_REVIEW"
    NO_CHANGE = "NO_CHANGE"
    BLOCKED_APPROVAL = "BLOCKED_APPROVAL"
    BLOCKED_STALE_PACKET = "BLOCKED_STALE_PACKET"
    BLOCKED_STALE_CANVAS = "BLOCKED_STALE_CANVAS"
    BLOCKED_CONFIG = "BLOCKED_CONFIG"
    BLOCKED_OWNERSHIP = "BLOCKED_OWNERSHIP"
    BLOCKED_REMOTE_DRIFT = "BLOCKED_REMOTE_DRIFT"
    BLOCKED_UNRESOLVED = "BLOCKED_UNRESOLVED"
    BLOCKED_PUBLISH_POLICY = "BLOCKED_PUBLISH_POLICY"
    BLOCKED_PROTECTED = "BLOCKED_PROTECTED"
    BLOCKED_PROVENANCE = "BLOCKED_PROVENANCE"
    BLOCKED_COLLISION = "BLOCKED_COLLISION"
    BLOCKED_WRITER_CONTRACT = "BLOCKED_WRITER_CONTRACT"


class FieldClassification(str, Enum):
    """Writer-default audit classification for a future writer-request field.

    Implementation defaults must never silently become canonical educational
    decisions; this enum forces each field to be labelled with its authority.
    """

    CANONICAL = "canonical"
    POLICY_DERIVED = "policy_derived"
    CONFIGURED = "configured"
    OPERATIONAL = "operational"
    UNRESOLVED = "unresolved"
    IMPLEMENTATION_DEFAULT = "implementation_default"


def _ser(value: Any) -> Any:
    """Deterministic serialization helper (enums -> value, nested -> dict)."""
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
class ExecutionPreconditionReport:
    """Machine-checkable execution-readiness report for one deployment intent.

    Every boolean gate defaults to ``False`` so an unpopulated report fails
    closed. ``blockers`` carries the reasons; ``readiness`` is the single
    authoritative status.
    """

    packet_hash: str = ""
    intent_id: str = ""
    policy_hash: str = ""
    canonical_revision: str = ""
    preview_hash: str = ""
    snapshot_hash: str = ""
    approval_identity: str = ""
    target_environment: str = ""
    object_identity: str = ""
    target_canvas_id: str = ""
    expected_course_id: str = ""
    expected_current_hash: str = ""
    expected_last_updated: str = ""
    operation: str = ""
    object_type: str = ""
    course: str = ""
    provenance_valid: bool = False
    ownership_valid: bool = False
    approval_valid: bool = False
    policy_valid: bool = False
    config_valid: bool = False
    live_state_valid: bool = False
    blockers: list[str] = field(default_factory=list)
    readiness: str = ReadinessState.BLOCKED_WRITER_CONTRACT.value

    def to_dict(self) -> dict[str, Any]:
        return _ser(asdict(self))


@dataclass
class WriterRequest:
    """Pure data-only description of what a future Phase 22 writer call needs.

    No writer import. No execution function. Explicit optionality: fields not
    relevant to a given object type are left blank.
    """

    request_id: str = ""
    packet_hash: str = ""
    intent_id: str = ""
    policy_hash: str = ""
    operation: str = ""
    target_type: str = ""
    course_id: str = ""
    target_canvas_id: str = ""
    title: str = ""
    body: str = ""
    due_at: str = ""
    submission_type: str = ""
    assignment_group_id: str = ""
    published: str = ""  # "published" | "unpublished" | "" (unresolved)
    expected_current_hash: str = ""
    expected_last_updated: str = ""
    provenance: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return _ser(asdict(self))


__all__ = [
    "ExecutionPreconditionReport",
    "FieldClassification",
    "ReadinessState",
    "WriterRequest",
]
