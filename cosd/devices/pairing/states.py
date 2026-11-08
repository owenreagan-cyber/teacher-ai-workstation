"""Pairing state machine. Only service methods may change state."""

from __future__ import annotations

from enum import Enum

from ..models import DeviceError


class PairingState(str, Enum):
    PENDING = "PENDING"
    AWAITING_OWNER_APPROVAL = "AWAITING_OWNER_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


STATES = tuple(state.value for state in PairingState)
TERMINAL = frozenset(
    {
        PairingState.REJECTED.value,
        PairingState.EXPIRED.value,
        PairingState.COMPLETED.value,
        PairingState.CANCELLED.value,
    }
)
PENDING_STATES = frozenset({PairingState.PENDING.value, PairingState.AWAITING_OWNER_APPROVAL.value})

# Central transition table. There is no path back from a terminal state.
ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
    PairingState.PENDING.value: frozenset(
        {
            PairingState.AWAITING_OWNER_APPROVAL.value,
            PairingState.REJECTED.value,
            PairingState.EXPIRED.value,
            PairingState.CANCELLED.value,
        }
    ),
    PairingState.AWAITING_OWNER_APPROVAL.value: frozenset(
        {
            PairingState.APPROVED.value,
            PairingState.REJECTED.value,
            PairingState.EXPIRED.value,
            PairingState.CANCELLED.value,
        }
    ),
    PairingState.APPROVED.value: frozenset(
        {PairingState.COMPLETED.value, PairingState.EXPIRED.value, PairingState.CANCELLED.value}
    ),
    PairingState.REJECTED.value: frozenset(),
    PairingState.EXPIRED.value: frozenset(),
    PairingState.COMPLETED.value: frozenset(),
    PairingState.CANCELLED.value: frozenset(),
}


def ensure_transition(current: str, new: str) -> None:
    if new not in ALLOWED_TRANSITIONS.get(current, frozenset()):
        raise DeviceError(
            f"pairing state cannot move from {current} to {new}",
            kind="conflict",
            http_status=409,
        )


def is_terminal(state: str) -> bool:
    return state in TERMINAL
