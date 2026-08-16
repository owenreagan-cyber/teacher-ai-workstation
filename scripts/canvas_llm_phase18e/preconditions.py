"""Execution-readiness precondition evaluation (Phase 18E).

``evaluate_preconditions(...)`` turns one mutation-eligible Phase 18D
deployment intent into a deterministic ``ExecutionPreconditionReport`` that
fails closed unless *every* safety condition is satisfied: exact approval,
exact packet/policy identity, fresh canonical/preview/snapshot/config/environment,
safe ownership, complete provenance, resolved publish policy, supported
operation, and fresh live Canvas state.

No writes. No Canvas mutation. No token use. No network.
"""

from __future__ import annotations

from typing import Any

from scripts.canvas_llm_phase18d.contracts import (
    ApprovalRecord,
    CanvasSnapshot,
    DeploymentIntent,
    DryRunPacket,
)

from .contracts import ExecutionPreconditionReport, ReadinessState
from .policy import OwnerCanvasPolicy, policy_hash
from .validation import (
    approval_binds_precondition,
    approval_includes_intent,
    approval_matches_packet,
    config_hash,
    provenance_complete,
    validate_policy,
)

# Required resolved fields per object type; a blank required field blocks.
REQUIRED_RESOLVED_FIELDS: dict[str, list[str]] = {
    "agenda_page": ["title", "body", "course_id"],
    "assignment": ["title", "course_id", "assignment_group_id", "due_at"],
    "announcement": ["title", "body", "course_id"],
}

# Blocker -> readiness mapping for intent-level (Phase 18D) safety blockers.
_BLOCKER_READINESS: dict[str, str] = {
    "ownership_uncertain": ReadinessState.BLOCKED_OWNERSHIP.value,
    "wrong_course": ReadinessState.BLOCKED_OWNERSHIP.value,
    "remote_drift": ReadinessState.BLOCKED_REMOTE_DRIFT.value,
    "title_collision": ReadinessState.BLOCKED_COLLISION.value,
    "ambiguous_target": ReadinessState.BLOCKED_COLLISION.value,
    "unresolved_content": ReadinessState.BLOCKED_UNRESOLVED.value,
    "read_failure": ReadinessState.BLOCKED_STALE_CANVAS.value,
    "missing_config": ReadinessState.BLOCKED_CONFIG.value,
    "protected": ReadinessState.BLOCKED_PROTECTED.value,
    "protected_course": ReadinessState.BLOCKED_PROTECTED.value,
    "policy:publish_state_unresolved": ReadinessState.BLOCKED_PUBLISH_POLICY.value,
    "policy:due_time_unresolved": ReadinessState.BLOCKED_UNRESOLVED.value,
}

READINESS_PRIORITY = [
    ReadinessState.BLOCKED_WRITER_CONTRACT.value,
    ReadinessState.BLOCKED_APPROVAL.value,
    ReadinessState.BLOCKED_PUBLISH_POLICY.value,
    ReadinessState.BLOCKED_PROTECTED.value,
    ReadinessState.BLOCKED_OWNERSHIP.value,
    ReadinessState.BLOCKED_REMOTE_DRIFT.value,
    ReadinessState.BLOCKED_COLLISION.value,
    ReadinessState.BLOCKED_UNRESOLVED.value,
    ReadinessState.BLOCKED_PROVENANCE.value,
    ReadinessState.BLOCKED_CONFIG.value,
    ReadinessState.BLOCKED_STALE_PACKET.value,
    ReadinessState.BLOCKED_STALE_CANVAS.value,
    ReadinessState.READY_FOR_EXECUTION_REVIEW.value,
]


def logical_target_identity(intent: DeploymentIntent) -> str:
    """Deterministic logical identity of a Canvas target (never title alone)."""
    return f"{intent.course}|{intent.object_type}|{intent.target_locator}"


def record_approval_bindings(
    *,
    packet: DryRunPacket,
    policy: OwnerCanvasPolicy,
    canvas_config: dict[str, Any],
    target_environment: str | None = None,
) -> dict[str, Any]:
    """Record the exact approval-time bindings for a future approval record.

    These become the approval's ``preconditions`` and are later re-validated
    so any drift invalidates the approval (it is never transferable).
    """
    env = target_environment or packet.target_environment
    return {
        "canonical_revision": packet.canonical_revision,
        "preview_hash": packet.preview_hash,
        "snapshot_hash": packet.snapshot_hash,
        "policy_hash": policy_hash(policy),
        "target_environment": env,
        "config_hash": config_hash(canvas_config),
    }


def _fresh_object(
    snapshot: CanvasSnapshot | None, intent: DeploymentIntent
) -> tuple[bool, Any | None]:
    """Return (found, object) for the intent's logical target in a fresh snapshot."""
    if snapshot is None:
        return False, None
    for obj in snapshot.objects:
        if obj.course == intent.course and obj.object_type == intent.object_type and obj.locator == intent.target_locator:
            return True, obj
    return False, None


def _evaluate_live_state(
    intent: DeploymentIntent, snapshot: CanvasSnapshot | None
) -> tuple[bool, list[str]]:
    """Fresh live-state validation. Fails closed when a fresh snapshot is absent."""
    errors: list[str] = []
    expected_hash = (intent.preconditions or {}).get("expected_current_hash", "")
    expected_updated = (intent.preconditions or {}).get("expected_last_updated", "")

    if snapshot is None:
        errors.append("live_state:missing_fresh_snapshot")
        return False, errors
    if snapshot.read_failure:
        errors.append("live_state:read_failure")
        return False, errors
    if intent.course in (snapshot.fetch_errors or []):
        errors.append("live_state:partial_fetch")
        return False, errors

    found, obj = _fresh_object(snapshot, intent)
    if intent.operation == "CREATE":
        # Object must still be absent at freshness check.
        if found:
            errors.append("live_state:create_target_appeared")
        return (not errors), errors

    # UPDATE: exact Canvas ID, correct course, matching current hash, no drift.
    if not found:
        errors.append("live_state:update_target_disappeared")
        return False, errors
    if obj.object_id and (intent.preconditions or {}).get("expected_object_id") and obj.object_id != (intent.preconditions or {}).get("expected_object_id"):
        errors.append("live_state:canvas_id_mismatch")
    if not expected_hash:
        errors.append("live_state:missing_expected_hash")
    elif obj.content_hash != expected_hash:
        errors.append("live_state:stale_canvas")
    if expected_updated and obj.current_state.get("updated_at") and obj.current_state.get("updated_at") != expected_updated:
        errors.append("live_state:updated_at_drift")
    return (not errors), errors


def evaluate_preconditions(
    packet: DryRunPacket,
    intent: DeploymentIntent,
    approval: ApprovalRecord | None,
    policy: OwnerCanvasPolicy,
    *,
    canvas_config: dict[str, Any],
    snapshot: CanvasSnapshot | None = None,
    target_environment: str | None = None,
) -> ExecutionPreconditionReport:
    """Evaluate execution readiness for a single mutation-eligible intent."""
    env = target_environment or packet.target_environment
    ph = policy_hash(policy)
    pre = intent.preconditions or {}

    report = ExecutionPreconditionReport(
        packet_hash=packet.packet_hash,
        intent_id=intent.id,
        policy_hash=ph,
        canonical_revision=packet.canonical_revision,
        preview_hash=packet.preview_hash,
        snapshot_hash=packet.snapshot_hash,
        approval_identity=getattr(approval, "reviewer", "") or "",
        target_environment=env,
        object_identity=logical_target_identity(intent),
        target_canvas_id=pre.get("expected_object_id", ""),
        expected_course_id=str((intent.desired_state or {}).get("course_id", "")),
        expected_current_hash=pre.get("expected_current_hash", ""),
        expected_last_updated=pre.get("expected_last_updated", ""),
        operation=intent.operation,
        object_type=intent.object_type,
        course=intent.course,
    )

    blockers: list[str] = []

    # 1. Operation support (Phase 18E never exposes DELETE or unknown ops).
    if intent.operation not in ("CREATE", "UPDATE"):
        blockers.append("writer:unsupported_operation")
    if intent.object_type not in REQUIRED_RESOLVED_FIELDS:
        blockers.append("writer:unsupported_object_type")

    # 2. Exact approval binding.
    if not approval_matches_packet(approval, packet.packet_hash):
        blockers.append("approval:packet_hash_mismatch")
    if not approval_includes_intent(approval, intent.id):
        blockers.append("approval:intent_not_approved")

    # 3. Policy binding: owner policy change invalidates old approval.
    if validate_policy(policy):
        blockers.append("policy:invalid")
    if not approval_binds_precondition(approval, "policy_hash", ph):
        blockers.append("policy:hash_mismatch")

    # 4. Canonical / preview / snapshot freshness.
    if not approval_binds_precondition(approval, "canonical_revision", packet.canonical_revision):
        blockers.append("stale:canonical_revision")
    if not approval_binds_precondition(approval, "preview_hash", packet.preview_hash):
        blockers.append("stale:preview_hash")
    if not approval_binds_precondition(approval, "snapshot_hash", packet.snapshot_hash):
        blockers.append("stale:snapshot_hash")

    # 5. Config freshness + environment identity.
    expected_cfg_hash = (getattr(approval, "preconditions", {}) or {}).get("config_hash", "")
    if not expected_cfg_hash or config_hash(canvas_config) != expected_cfg_hash:
        blockers.append("config:drift")
    if env != packet.target_environment:
        blockers.append("config:environment_mismatch")
    if not approval_binds_precondition(approval, "target_environment", env):
        blockers.append("config:cross_environment")

    # 6. Publish policy must be explicit for any publishable write.
    if not policy.publication_resolved():
        blockers.append("publish:policy_unresolved")

    # 7. Intent-level safety blockers (ownership/drift/collision/protected/...).
    for b in intent.blockers:
        blockers.append(f"intent:{b}")

    # 8. Required fields resolved (no blank overwrites).
    for field in REQUIRED_RESOLVED_FIELDS.get(intent.object_type, []):
        value = (intent.desired_state or {}).get(field)
        if value in (None, "", "unresolved"):
            blockers.append(f"unresolved:{field}")

    # 9. UPDATE requires an exact Canvas ID (never target by title alone).
    if intent.operation == "UPDATE" and not report.target_canvas_id:
        blockers.append("writer:update_missing_canvas_id")

    # 10. Provenance continuity.
    report.provenance_valid = provenance_complete(intent)
    if not report.provenance_valid:
        blockers.append("provenance:missing")

    # 11. Fresh live Canvas state.
    live_ok, live_errors = _evaluate_live_state(intent, snapshot)
    blockers.extend(live_errors)
    report.live_state_valid = live_ok

    # Populate boolean gates.
    report.approval_valid = approval_matches_packet(approval, packet.packet_hash) and approval_includes_intent(approval, intent.id)
    report.policy_valid = not validate_policy(policy) and approval_binds_precondition(approval, "policy_hash", ph)
    report.config_valid = bool(expected_cfg_hash) and config_hash(canvas_config) == expected_cfg_hash
    report.ownership_valid = not any(b.startswith(("intent:ownership_uncertain", "intent:wrong_course")) for b in blockers)
    report.blockers = list(dict.fromkeys(blockers))

    report.readiness = _resolve_readiness(intent, blockers)
    return report


def _resolve_readiness(intent: DeploymentIntent, blockers: list[str]) -> str:
    """Map blockers to the highest-priority (most severe) readiness state."""
    if intent.operation == "NO_CHANGE":
        return ReadinessState.NO_CHANGE.value
    if not blockers:
        return ReadinessState.READY_FOR_EXECUTION_REVIEW.value

    mapped: set[str] = set()
    for b in blockers:
        if b == "writer:unsupported_operation" or b == "writer:unsupported_object_type" or b == "writer:update_missing_canvas_id":
            mapped.add(ReadinessState.BLOCKED_WRITER_CONTRACT.value)
        elif b.startswith("approval:") or b == "policy:hash_mismatch" or b == "policy:invalid":
            mapped.add(ReadinessState.BLOCKED_APPROVAL.value)
        elif b.startswith("publish:"):
            mapped.add(ReadinessState.BLOCKED_PUBLISH_POLICY.value)
        elif b.startswith("stale:"):
            mapped.add(ReadinessState.BLOCKED_STALE_PACKET.value)
        elif b.startswith("config:"):
            mapped.add(ReadinessState.BLOCKED_CONFIG.value)
        elif b.startswith("live_state:"):
            mapped.add(ReadinessState.BLOCKED_STALE_CANVAS.value)
        elif b == "provenance:missing":
            mapped.add(ReadinessState.BLOCKED_PROVENANCE.value)
        elif b.startswith("unresolved:"):
            mapped.add(ReadinessState.BLOCKED_UNRESOLVED.value)
        elif b.startswith("intent:"):
            mapped.add(_BLOCKER_READINESS.get(b[len("intent:"):], ReadinessState.BLOCKED_WRITER_CONTRACT.value))
        else:
            mapped.add(ReadinessState.BLOCKED_WRITER_CONTRACT.value)

    for state in READINESS_PRIORITY:
        if state in mapped:
            return state
    return ReadinessState.BLOCKED_WRITER_CONTRACT.value


__all__ = [
    "REQUIRED_RESOLVED_FIELDS",
    "evaluate_preconditions",
    "logical_target_identity",
    "record_approval_bindings",
]
