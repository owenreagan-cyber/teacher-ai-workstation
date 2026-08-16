"""Phase 18E pure pre-execution policy and validation layer (import-safe).

Only pure contracts, owner policy, preconditions, validation, and the pure
writer-request adapter are re-exported here. The read-only snapshot adapter
(``snapshot_adapter``) is intentionally *not* imported: it may load the read
connector and must never be pulled into the pure import graph.
"""

from __future__ import annotations

from .adapter import (
    build_writer_requests,
    build_writer_requests_with_reports,
    detect_request_collisions,
    stable_request_id,
)
from .contracts import (
    ExecutionPreconditionReport,
    FieldClassification,
    ReadinessState,
    WriterRequest,
)
from .policy import (
    OwnerCanvasPolicy,
    default_policy,
    due_timestamp,
    policy_hash,
    policy_provenance,
)
from .preconditions import evaluate_preconditions, logical_target_identity, record_approval_bindings
from .validation import WRITER_DEFAULT_AUDIT, config_hash

__all__ = [
    "ExecutionPreconditionReport",
    "FieldClassification",
    "OwnerCanvasPolicy",
    "ReadinessState",
    "WRITER_DEFAULT_AUDIT",
    "WriterRequest",
    "build_writer_requests",
    "build_writer_requests_with_reports",
    "config_hash",
    "default_policy",
    "detect_request_collisions",
    "due_timestamp",
    "evaluate_preconditions",
    "logical_target_identity",
    "policy_hash",
    "policy_provenance",
    "record_approval_bindings",
    "stable_request_id",
]
