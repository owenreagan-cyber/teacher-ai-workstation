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
# A scheduled run may start a few minutes after 4:00 PM. Within this grace
# window the canonical instant is still honored; beyond it the window is
# considered missed and an explicit owner-selected time is required.
PUBLICATION_GRACE_MINUTES = 30

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


def _is_instructional_day(d: date) -> bool:
    """True when ``d`` falls inside an authoritative instructional week."""
    from scripts.canvas_llm_intake import week_resolution as wr

    try:
        wr.current_week(today=d)
        return True
    except RuntimeError:
        return False


def instructional_rollover_meta(
    upcoming_week_start_date: str,
    timezone_name: str = NEW_YORK,
) -> dict[str, Any]:
    """Resolve the rollover day to the last instructional day on/before Friday.

    The canonical target is the Friday before the upcoming Monday. If that
    Friday is a holiday, track-out day, or other non-instructional day, walk
    back to the most recent weekday that is inside an instructional week. This
    keeps the Friday 4:00 PM rollover on a school day and handles quarter
    transitions (e.g. set up Q3 before winter track-out).
    """
    y, m, d = (int(x) for x in str(upcoming_week_start_date).split("-"))
    monday = date(y, m, d)
    canonical = monday + timedelta(days=-3)
    chosen = canonical
    for _ in range(31):
        if chosen.weekday() < 5 and _is_instructional_day(chosen):
            break
        chosen -= timedelta(days=1)
    local = datetime(
        chosen.year, chosen.month, chosen.day,
        ROLLOVER_HOUR, ROLLOVER_MINUTE,
        tzinfo=ZoneInfo(timezone_name),
    )
    return {
        "canonical_friday": canonical.isoformat(),
        "rollover_day": chosen.isoformat(),
        "moved": chosen != canonical,
        "scheduled_at": local.astimezone(ZoneInfo("UTC")).isoformat().replace("+00:00", "Z"),
    }


def instructional_rollover_scheduled_at(
    upcoming_week_start_date: str,
    timezone_name: str = NEW_YORK,
) -> str:
    """Instructional-day-aware Friday 4:00 PM rollover instant (UTC ISO)."""
    return instructional_rollover_meta(upcoming_week_start_date, timezone_name)["scheduled_at"]


def is_due(scheduled_at: str, now: datetime | None = None) -> bool:
    """True when ``now`` is at or past the rollover instant."""
    now = now or datetime.now(timezone.utc)
    scheduled = _parse(scheduled_at)
    if scheduled is None:
        return True  # no schedule = immediately due (fail-open for manual run)
    return now >= scheduled


def resolve_publication_time(
    upcoming_week_start_date: str,
    *,
    now: datetime | None = None,
    owner_selected_at: str | None = None,
    timezone_name: str = NEW_YORK,
) -> dict[str, Any]:
    """Resolve the publication instant without silently reusing an expired one.

    The canonical instant is the Friday before the upcoming week at 4:00 PM
    America/New_York. If that window has already passed, the caller MUST supply
    an explicit future ``owner_selected_at``. Returning ``None`` (with
    ``requires_owner_time=True``) is the fail-closed behavior.

    ``owner_selected_at`` must be a timezone-aware ISO-8601 timestamp strictly
    after ``now``. Naive timestamps are rejected rather than guessed.
    """
    now = now or datetime.now(timezone.utc)
    meta = instructional_rollover_meta(upcoming_week_start_date, timezone_name)
    canonical = meta["scheduled_at"]
    canonical_dt = _parse(canonical)

    if owner_selected_at:
        selected = _parse(owner_selected_at)
        if selected is None:
            raise ValueError("owner_selected_at must be an ISO-8601 timestamp")
        if selected.tzinfo is None:
            raise ValueError("owner_selected_at must include a timezone")
        if selected <= now:
            raise ValueError("owner_selected_at must be in the future")
        return {
            "canonical_scheduled_at": canonical,
            "canonical_friday": meta["canonical_friday"],
            "rollover_day": meta["rollover_day"],
            "rollover_day_moved": meta["moved"],
            "scheduled_at": selected.astimezone(ZoneInfo("UTC")).isoformat().replace("+00:00", "Z"),
            "source": "OWNER_SELECTED",
            "requires_owner_time": False,
            "reason": "Owner explicitly selected a new publication time.",
        }

    if canonical_dt is not None and canonical_dt > now:
        return {
            "canonical_scheduled_at": canonical,
            "canonical_friday": meta["canonical_friday"],
            "rollover_day": meta["rollover_day"],
            "rollover_day_moved": meta["moved"],
            "scheduled_at": canonical,
            "source": "CANONICAL_FRIDAY_4PM",
            "requires_owner_time": False,
            "reason": "Canonical Friday 4:00 PM America/New_York window is still in the future.",
        }

    # The scheduled LaunchAgent run can begin a few minutes late. Honor the
    # canonical instant inside the grace window instead of forcing the owner to
    # pick a new time on every slightly-delayed Friday run.
    if canonical_dt is not None and now <= canonical_dt + timedelta(minutes=PUBLICATION_GRACE_MINUTES):
        return {
            "canonical_scheduled_at": canonical,
            "canonical_friday": meta["canonical_friday"],
            "rollover_day": meta["rollover_day"],
            "rollover_day_moved": meta["moved"],
            "scheduled_at": canonical,
            "source": "CANONICAL_FRIDAY_4PM_GRACE",
            "requires_owner_time": False,
            "reason": "Canonical Friday 4:00 PM window is due within the publication grace period.",
        }

    return {
        "canonical_scheduled_at": canonical,
        "canonical_friday": meta["canonical_friday"],
        "rollover_day": meta["rollover_day"],
        "rollover_day_moved": meta["moved"],
        "scheduled_at": None,
        "source": "OWNER_SELECTED_REQUIRED",
        "requires_owner_time": True,
        "reason": "Canonical Friday 4:00 PM window has passed; an explicit owner-selected publication time is required.",
    }


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

    # Publication-time resolution: expired canonical window requires an owner.
    expired_now = datetime(2026, 10, 30, 21, 0, tzinfo=timezone.utc)
    res = resolve_publication_time("2026-11-02", now=expired_now)
    assert res["requires_owner_time"] is True, res
    assert res["scheduled_at"] is None, res
    assert res["canonical_scheduled_at"] == "2026-10-30T20:00:00Z", res

    # A future canonical window still resolves without owner input.
    future_now = datetime(2026, 10, 30, 12, 0, tzinfo=timezone.utc)
    res2 = resolve_publication_time("2026-11-02", now=future_now)
    assert res2["requires_owner_time"] is False
    assert res2["scheduled_at"] == "2026-10-30T20:00:00Z", res2

    # A slightly-delayed scheduler run (within grace) still honors the window.
    grace_now = datetime(2026, 10, 30, 20, 15, tzinfo=timezone.utc)
    res_grace = resolve_publication_time("2026-11-02", now=grace_now)
    assert res_grace["requires_owner_time"] is False, res_grace
    assert res_grace["source"] == "CANONICAL_FRIDAY_4PM_GRACE", res_grace
    assert res_grace["scheduled_at"] == "2026-10-30T20:00:00Z", res_grace

    # Beyond grace, the window is missed and owner input is required.
    late_now = datetime(2026, 10, 30, 20, 31, tzinfo=timezone.utc)
    res_late = resolve_publication_time("2026-11-02", now=late_now)
    assert res_late["requires_owner_time"] is True, res_late

    # Explicit future owner time wins (DST-aware conversion).
    res3 = resolve_publication_time(
        "2026-11-02", now=expired_now, owner_selected_at="2026-11-01T09:00:00-05:00",
    )
    assert res3["source"] == "OWNER_SELECTED"
    assert res3["scheduled_at"] == "2026-11-01T14:00:00Z", res3

    # Past/naive owner times fail closed.
    for bad in ("2026-10-30T12:00:00-04:00", "2026-11-01T09:00:00"):
        try:
            resolve_publication_time("2026-11-02", now=expired_now, owner_selected_at=bad)
            raise AssertionError("expected ValueError")
        except ValueError:
            pass

    # Instructional calendar: never roll over on Thanksgiving break (Nov 27).
    # Q2W7 starts Monday Nov 30, so the last instructional rollover day is
    # Friday Nov 20 at 4:00 PM EST (21:00Z).
    q2w7 = instructional_rollover_meta("2026-11-30")
    assert q2w7["canonical_friday"] == "2026-11-27", q2w7
    assert q2w7["rollover_day"] == "2026-11-20", q2w7
    assert q2w7["moved"] is True
    assert q2w7["scheduled_at"] == "2026-11-20T21:00:00Z", q2w7

    # Quarter transition: Q3W1 starts Monday Jan 11, 2027. Winter track-out
    # covers Dec 21-Jan 8, so the rollover is the last instructional Friday
    # (Dec 18, 2026) at 4:00 PM EST.
    q3w1 = instructional_rollover_meta("2027-01-11")
    assert q3w1["canonical_friday"] == "2027-01-08", q3w1
    assert q3w1["rollover_day"] == "2026-12-18", q3w1
    assert q3w1["moved"] is True
    assert q3w1["scheduled_at"] == "2026-12-18T21:00:00Z", q3w1

    # Ordinary weeks are unchanged.
    assert instructional_rollover_scheduled_at("2026-11-02") == "2026-10-30T20:00:00Z"
    assert instructional_rollover_scheduled_at("2026-11-09") == "2026-11-06T21:00:00Z"

    print("PASS canvas-rollover schedule self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(command_self_test())
