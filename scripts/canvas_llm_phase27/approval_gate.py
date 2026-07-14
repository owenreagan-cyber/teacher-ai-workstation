from __future__ import annotations

from typing import Any

from .ledger import DeploymentLedger

NON_APPROVABLE_STATUSES = {"CONFLICT", "BLOCKED", "OMIT", "DELETE_CANDIDATE"}
BLOCKING_FRESHNESS_STATES = {"stale", "expired", "unknown"}


class ApprovalRejectedError(ValueError):
    pass


def approve_operation(
    ledger: DeploymentLedger,
    safety_diff_item: dict[str, Any],
    manifest_revision: int,
    snapshot_id: str,
    snapshot_freshness: str,
    approved_by: str,
) -> None:
    """Approve a single Safety Diff item. Approval is stored keyed on
    (objectId, manifestRevision, snapshotId): this is what makes invalidation
    real rather than simulated -- if the packet revision or snapshot changes,
    no approval row matches the new key, so `is_approved` reads back False
    without any separate "invalidate" bookkeeping being required.

    Explicitly non-approvable by comparisonStatus alone (not merely by
    whether `blockers` happens to be non-empty): CONFLICT (ambiguous match),
    BLOCKED (covers archived-course targets and unresolved-due-time
    assignments, both of which set this status), OMIT (policy-disabled
    subjects), and DELETE_CANDIDATE (informational only, never actionable).
    Previously DELETE_CANDIDATE items carried no blockers and were not in
    this set, so they were approvable -- a real bug, fixed here."""
    object_id = safety_diff_item["objectId"]
    status = safety_diff_item["comparisonStatus"]
    if status in NON_APPROVABLE_STATUSES:
        raise ApprovalRejectedError(f"{object_id} is {status} and cannot be approved")
    if safety_diff_item.get("blockers"):
        raise ApprovalRejectedError(
            f"{object_id} has unresolved blockers and cannot be approved: "
            f"{safety_diff_item['blockers']}"
        )
    if snapshot_freshness in BLOCKING_FRESHNESS_STATES:
        raise ApprovalRejectedError(
            f"snapshot freshness is {snapshot_freshness!r}; cannot approve "
            "an operation against a non-fresh snapshot"
        )
    ledger.record_approval(object_id, manifest_revision, snapshot_id, approved_by)


def revoke_operation(
    ledger: DeploymentLedger, object_id: str, manifest_revision: int, snapshot_id: str
) -> None:
    ledger.revoke_approval(object_id, manifest_revision, snapshot_id)


def is_approved(
    ledger: DeploymentLedger, object_id: str, manifest_revision: int, snapshot_id: str
) -> bool:
    return (
        ledger.current_approval_state(object_id, manifest_revision, snapshot_id) == "approved"
    )
