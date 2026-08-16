"""Pure validation helpers for Phase 18E execution preconditions.

These functions are deterministic and side-effect free. They validate owner
policy, approval binding, configuration freshness, live-state freshness, and
ownership/provenance invariants. Every check fails closed.
"""

from __future__ import annotations

from typing import Any

from scripts.canvas_llm_phase27.canonicalize import canonical_hash

from .contracts import FieldClassification
from .policy import OwnerCanvasPolicy, policy_hash


def validate_policy(policy: OwnerCanvasPolicy) -> list[str]:
    """Return policy structural errors (empty list means valid)."""
    errors: list[str] = []
    if policy.homework_due_day != "assigned_day":
        errors.append("homework_due_day must be 'assigned_day'")
    if policy.homework_due_time_local not in ("23:59", "23:59:00"):
        # The owner-approved rule is 23:59 local; anything else is unapproved.
        errors.append("homework_due_time_local must be '23:59'")
    if policy.homework_submission_type != "on_paper":
        errors.append("homework_submission_type must be 'on_paper'")
    if policy.publish_state not in ("resolved", "unresolved"):
        errors.append("publish_state must be 'resolved' or 'unresolved'")
    if policy.publish_state == "resolved" and policy.publish_decision not in ("published", "unpublished"):
        errors.append("resolved publish_state requires publish_decision 'published' or 'unpublished'")
    if not policy.timezone:
        errors.append("timezone must be set")
    return errors


def config_hash(config: dict[str, Any]) -> str:
    """Deterministic identity of a verified Canvas configuration bundle."""
    return canonical_hash(config)


def validate_config(config: dict[str, Any], expected_config_hash: str) -> tuple[bool, list[str]]:
    """Return (valid, errors). Config differs from approved packet -> block."""
    if not expected_config_hash:
        return False, ["config:missing_expected_hash"]
    if config_hash(config) != expected_config_hash:
        return False, ["config:drift"]
    return True, []


def approval_matches_packet(approval: Any, packet_hash: str) -> bool:
    """Approval must bind to the exact packet hash."""
    if approval is None:
        return False
    return getattr(approval, "packet_hash", "") == packet_hash


def approval_includes_intent(approval: Any, intent_id: str) -> bool:
    """The specific intent must be listed in the approval's approved IDs."""
    if approval is None:
        return False
    approved = getattr(approval, "approved_intent_ids", []) or []
    return intent_id in approved


def approval_binds_precondition(approval: Any, key: str, value: str) -> bool:
    """Check a recorded approval-time precondition value."""
    if approval is None:
        return False
    preconditions = getattr(approval, "preconditions", {}) or {}
    return preconditions.get(key) == value


def validate_live_state(
    *,
    expected_current_hash: str,
    current_live_hash: str,
    expected_last_updated: str = "",
    current_last_updated: str = "",
) -> tuple[bool, list[str]]:
    """Validate fresh live Canvas state against approval-time expectations."""
    errors: list[str] = []
    if not expected_current_hash:
        errors.append("live_state:missing_expected_hash")
    elif current_live_hash != expected_current_hash:
        errors.append("live_state:stale_canvas")
    if expected_last_updated and current_last_updated and current_last_updated != expected_last_updated:
        errors.append("live_state:updated_at_drift")
    return (not errors), errors


def provenance_complete(intent: Any) -> bool:
    """Provenance must trace back to canonical source; empty -> fail closed."""
    if intent is None:
        return False
    provenance = getattr(intent, "provenance", []) or []
    return bool(provenance)


# Writer-default audit: every future writer-request field is classified by its
# authority. Implementation defaults must never become canonical.
WRITER_DEFAULT_AUDIT: dict[str, str] = {
    "operation": FieldClassification.CANONICAL.value,  # trusts Phase 18D resolved op
    "target_type": FieldClassification.CANONICAL.value,
    "course_id": FieldClassification.CONFIGURED.value,
    "target_canvas_id": FieldClassification.CONFIGURED.value,
    "title": FieldClassification.CANONICAL.value,
    "body": FieldClassification.CANONICAL.value,
    "due_at": FieldClassification.POLICY_DERIVED.value,
    "submission_type": FieldClassification.POLICY_DERIVED.value,
    "assignment_group_id": FieldClassification.CONFIGURED.value,
    "published": FieldClassification.UNRESOLVED.value,  # owner has not decided
    "expected_current_hash": FieldClassification.OPERATIONAL.value,
    "expected_last_updated": FieldClassification.OPERATIONAL.value,
    "provenance": FieldClassification.CANONICAL.value,
}


__all__ = [
    "WRITER_DEFAULT_AUDIT",
    "approval_binds_precondition",
    "approval_includes_intent",
    "approval_matches_packet",
    "config_hash",
    "provenance_complete",
    "validate_config",
    "validate_live_state",
    "validate_policy",
]
