"""Friday 4:00 PM America/New_York weekly rollover schedule + lifecycle.

The canonical rollover instant is the Friday immediately before the upcoming
instructional week, at 4:00 PM America/New_York. This is the *same* instant the
existing weekly-update announcements are scheduled for
(``scripts.canvas_llm_deploy.plan.weekly_update_delayed_post_at``); we reuse
that derivation so there is a single canonical "Friday 4 PM" clock.

All time math is timezone-aware (``zoneinfo.ZoneInfo``). We never hard-code a
UTC offset: DST is resolved from the America/New_York zone.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo

NEW_YORK = "America/New_York"
ROLLOVER_HOUR = 16  # 4:00 PM
ROLLOVER_MINUTE = 0

# Canonical FRIDAY ROLLOVER lifecycle states.
NOT_DUE = "NOT_DUE"
PREPARING = "PREPARING"
NEEDS_OWEN = "NEEDS_OWEN"
READY = "READY"
HELD_UNTIL_4PM = "HELD_UNTIL_4PM"
EXECUTING = "EXECUTING"
PUBLISHED_VERIFIED = "PUBLISHED_VERIFIED"
BLOCKED = "BLOCKED"

ROLLOVER_STATES = (
    NOT_DUE, PREPARING, NEEDS_OWEN, READY,
    HELD_UNTIL_4PM, EXECUTING, PUBLISHED_VERIFIED, BLOCKED,
)


def friday_rollover_scheduled_at(
    upcoming_week_start_date: str,
    timezone_name: str = NEW_YORK,
) -> str:
    """Return the Friday 4:00 PM local rollover instant as a UTC ISO string.

    ``upcoming_week_start_date`` is the upcoming week's Monday (``YYYY-MM-DD``).
    The rollover fires the Friday immediately before that Monday.
    """
    y, m, d = (int(x) for x in str(upcoming_week_start_date).split("-"))
    start = date(y, m, d)
    friday = start + timedelta(days=-3)  # Monday - 3 days == the prior Friday
    local = datetime(
        friday.year, friday.month, friday.day,
        ROLLOVER_HOUR, ROLLOVER_MINUTE,
        tzinfo=ZoneInfo(timezone_name),
    )
    return local.astimezone(ZoneInfo("UTC")).isoformat().replace("+00:00", "Z")


def _parse(ts: str | None) -> datetime | None:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    except ValueError:
        return None


def is_due(scheduled_at: str, now: datetime | None = None) -> bool:
    """True when ``now`` is at or past the rollover instant."""
    now = now or datetime.now(timezone.utc)
    scheduled = _parse(scheduled_at)
    if scheduled is None:
        return True  # no schedule = immediately due (fail-open for manual run)
    return now >= scheduled


def classify_state(
    *,
    scheduled_at: str,
    now: datetime | None,
    ready: bool,
    needs_owen: bool,
    blockers: list[str],
    ledger_state: str | None,
    preparing: bool,
) -> str:
    """Deterministic FRIDAY ROLLOVER lifecycle classification.

    Order of precedence (highest first):

    1. ``PUBLISHED_VERIFIED`` — ledger says the rollover already verified.
    2. ``EXECUTING`` — ledger says a rollover is in flight.
    3. ``BLOCKED`` — a hard blocker exists (even if some artifacts are ready).
    4. ``NEEDS_OWEN`` — no hard blocker, but owner input is required.
    5. ``PREPARING`` — not ready yet, still being prepared.
    6. ``NOT_DUE`` — ready but the upcoming week is more than one rollover
       window away (nothing due yet).
    7. ``HELD_UNTIL_4PM`` — ready and within the window, but before 4 PM.
    8. ``READY`` — ready and due (or ready on/after 4 PM).
    """
    if ledger_state == PUBLISHED_VERIFIED:
        return PUBLISHED_VERIFIED
    if ledger_state == EXECUTING:
        return EXECUTING
    if blockers:
        return BLOCKED
    if needs_owen:
        return NEEDS_OWEN
    if not ready:
        return PREPARING if preparing else NOT_DUE
    if not is_due(scheduled_at, now):
        return HELD_UNTIL_4PM
    return READY


def command_self_test() -> int:
    # Friday 4 PM ET for Q2W3 (Monday 2026-10-26) == Friday 2026-10-23 20:00Z.
    assert friday_rollover_scheduled_at("2026-10-26") == "2026-10-23T20:00:00Z", \
        friday_rollover_scheduled_at("2026-10-26")
    # A different week is not hard-coded: Q2W4 (2026-11-02) -> 2026-10-30 20:00Z.
    assert friday_rollover_scheduled_at("2026-11-02") == "2026-10-30T20:00:00Z", \
        friday_rollover_scheduled_at("2026-11-02")

    now = datetime(2026, 10, 19, 12, 0, tzinfo=timezone.utc)  # Monday, before Friday
    sched = friday_rollover_scheduled_at("2026-10-26")

    # Held until 4 PM when ready but not yet due.
    assert classify_state(scheduled_at=sched, now=now, ready=True, needs_owen=False,
                          blockers=[], ledger_state=None, preparing=False) == HELD_UNTIL_4PM
    # READY once due.
    due_now = datetime(2026, 10, 23, 20, 0, tzinfo=timezone.utc)
    assert classify_state(scheduled_at=sched, now=due_now, ready=True, needs_owen=False,
                          blockers=[], ledger_state=None, preparing=False) == READY
    # Needs Owen outranks preparing.
    assert classify_state(scheduled_at=sched, now=now, ready=False, needs_owen=True,
                          blockers=[], ledger_state=None, preparing=True) == NEEDS_OWEN
    # Blocked outranks needs_owen.
    assert classify_state(scheduled_at=sched, now=now, ready=False, needs_owen=True,
                          blockers=["x"], ledger_state=None, preparing=True) == BLOCKED
    # Verified is terminal.
    assert classify_state(scheduled_at=sched, now=now, ready=True, needs_owen=False,
                          blockers=[], ledger_state=PUBLISHED_VERIFIED,
                          preparing=False) == PUBLISHED_VERIFIED
    print("PASS canvas-rollover schedule self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(command_self_test())
