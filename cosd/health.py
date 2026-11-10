"""Runtime health classification for cosd.

One vocabulary, used by the authenticated API and by Chief.app:

    HEALTHY    serving, state readable, no attention needed
    DEGRADED   serving, but something needs the owner's attention
    RECOVERING startup reconciliation just repaired interrupted work
    BLOCKED    serving but refusing or unable to do useful work
    DISCONNECTED  (client side only) the app cannot reach the daemon

The HTTP server answering is not sufficient for HEALTHY; every input below is
derived from state rather than from the socket.
"""
from __future__ import annotations

from typing import Any

HEALTHY = "HEALTHY"
DEGRADED = "DEGRADED"
RECOVERING = "RECOVERING"
BLOCKED = "BLOCKED"
DISCONNECTED = "DISCONNECTED"

RECOVERING_WINDOW_S = 30


def classify(
    *,
    db_ok: bool,
    kill_switch: bool,
    queue_paused: bool,
    device_registry_available: bool,
    restart_required: bool | None,
    recovered_count: int = 0,
    recovery_age_s: float | None = None,
) -> dict[str, Any]:
    if not db_ok:
        return {"state": BLOCKED, "reasons": ["state database unavailable"]}
    if kill_switch:
        return {"state": BLOCKED, "reasons": ["kill switch engaged"]}

    recovering = (
        recovered_count > 0
        and recovery_age_s is not None
        and recovery_age_s <= RECOVERING_WINDOW_S
    )
    attention: list[str] = []
    if restart_required:
        attention.append("running code is older than the checkout; restart to update")
    if queue_paused:
        attention.append("execution queue is paused")
    if not device_registry_available:
        attention.append("device registry unavailable")

    if recovering:
        reasons = [f"{recovered_count} interrupted task(s) reconciled at startup", *attention]
        # Recovery is transient: report it as RECOVERING unless something else
        # also needs the owner, in which case DEGRADED is the honest label.
        return {"state": DEGRADED if attention else RECOVERING, "reasons": reasons}

    if attention:
        return {"state": DEGRADED, "reasons": attention}
    return {"state": HEALTHY, "reasons": []}
