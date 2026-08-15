"""Packet readiness evaluation and approval validation (Phase 18D).

Fail-closed: any blocker makes the packet not globally write-ready. Readiness is
a pure function over blocker kinds; approval validity is a pure function over
packet hashes and preconditions (no identity infrastructure, no network).
"""

from __future__ import annotations

from .contracts import ApprovalRecord, DryRunPacket, PacketReadiness

# Most-severe-first blocker kind -> readiness state. Ordering is deterministic so
# mixed blockers resolve to a single stable state.
BLOCKER_PRIORITY: list[tuple[str, str]] = [
    ("stale", PacketReadiness.BLOCKED_STALE.value),
    ("read_failure", PacketReadiness.BLOCKED_READ_FAILURE.value),
    ("protected", PacketReadiness.BLOCKED_PROTECTED.value),
    ("ownership", PacketReadiness.BLOCKED_OWNERSHIP.value),
    ("remote_drift", PacketReadiness.BLOCKED_REMOTE_DRIFT.value),
    ("collision", PacketReadiness.BLOCKED_COLLISION.value),
    ("missing_config", PacketReadiness.BLOCKED_MISSING_CONFIG.value),
    ("policy", PacketReadiness.BLOCKED_POLICY.value),
    ("unresolved", PacketReadiness.BLOCKED_UNRESOLVED.value),
]

_BLOCKER_KIND_INDEX = {kind: i for i, (kind, _) in enumerate(BLOCKER_PRIORITY)}


def evaluate_packet_readiness(blocker_kinds: set[str]) -> str:
    """Return the global readiness for a set of blocker kinds (fail-closed)."""
    ordered = sorted(blocker_kinds, key=lambda k: _BLOCKER_KIND_INDEX.get(k, 999))
    for kind in ordered:
        state = dict(BLOCKER_PRIORITY).get(kind)
        if state is not None:
            return state
    return PacketReadiness.READY_FOR_OWNER_REVIEW.value


def packet_is_stale(
    packet: DryRunPacket,
    *,
    canonical_revision: str | None = None,
    preview_hash: str | None = None,
    snapshot_hash: str | None = None,
) -> tuple[bool, list[str]]:
    """Return (stale, reasons) if any identity the packet is bound to changed."""
    reasons: list[str] = []
    if canonical_revision is not None and canonical_revision != packet.canonical_revision:
        reasons.append("canonical plan changed")
    if preview_hash is not None and preview_hash != packet.preview_hash:
        reasons.append("teacher preview changed")
    if snapshot_hash is not None and snapshot_hash != packet.snapshot_hash:
        reasons.append("canvas snapshot changed")
    return bool(reasons), reasons


def approval_is_valid(record: ApprovalRecord, packet: DryRunPacket) -> tuple[bool, list[str]]:
    """An approval is valid only if the exact packet it approved is unchanged."""
    reasons: list[str] = []
    if record.packet_hash != packet.packet_hash:
        reasons.append("packet hash mismatch")
        return False, reasons
    for key in ("canonical_revision", "preview_hash", "snapshot_hash"):
        expected = record.preconditions.get(key)
        actual = getattr(packet, key, None)
        if expected is not None and expected != actual:
            reasons.append(f"{key} changed")
    return (not reasons), reasons
