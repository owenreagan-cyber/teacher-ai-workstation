"""Weekly-session pacing freshness guard.

Codifies the hard rule that every new weekly Canvas workflow session must begin
with a *fresh* live read of the 2026-2027 FPK pacing guide, tab ``4B - Reagan``.
Remembered/cached pacing (earlier chats, cached plans, prior deployments,
fixtures, or project memory) may provide context but can never satisfy the
freshness requirement.

The guard is a pure, deterministic, session-scoped model:

- a session starts with no fresh pull recorded, so artifact generation is
  blocked;
- a successful live read records a :class:`PacingSessionSnapshot`;
- a refresh/verify/re-read command invalidates the snapshot and forces a new
  read;
- a failed live read blocks the build and is never silently papered over.

Standard library only. No wall-clock reads, no network, no Canvas, no writes.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date, timedelta
from typing import Any

FPK_SPREADSHEET_ID = "1I-CNb_ZPnOozY2wSMNAWF3bzuRZWDdZt9yoSBKtLWD4"
FPK_SHEET_NAME = "4B - Reagan"
WEEKDAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday")

BLOCK_FRESH_PULL_REQUIRED = "pacing:fresh_pull_required"
BLOCK_READ_FAILURE = "pacing:read_failure"
BLOCK_WRONG_SOURCE = "pacing:wrong_source"
BLOCK_MISSING_WEEK_DATES = "pacing:missing_week_dates"
BLOCK_PREVIOUS_WEEK_MISSING = "pacing:previous_week_missing"


@dataclass
class PacingSessionSnapshot:
    week_code: str = ""
    starts_on: str = ""  # Monday, ISO date
    ends_on: str = ""  # Friday, ISO date
    weekdays: dict[str, str] = field(default_factory=dict)  # weekday -> ISO date
    previous_week_starts_on: str = ""
    previous_week_ends_on: str = ""
    source_spreadsheet_id: str = FPK_SPREADSHEET_ID
    source_sheet: str = FPK_SHEET_NAME
    source_range: str = ""
    source_revision: str = ""
    pulled_at: str = ""  # ISO-8601 timestamp of the fresh pull
    fresh: bool = False
    read_failed: bool = False
    read_failure_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def weekdays_for_week(monday_iso: str) -> dict[str, str]:
    """Derive Monday-Friday ISO dates from a Monday anchor (fails closed)."""
    start = date.fromisoformat(monday_iso)
    if start.weekday() != 0:
        raise ValueError(f"week anchor must be a Monday: {monday_iso!r}")
    return {name: (start + timedelta(days=i)).isoformat() for i, name in enumerate(WEEKDAYS)}


def new_session_snapshot() -> PacingSessionSnapshot:
    """A brand-new session has no fresh pull recorded (build is blocked)."""
    return PacingSessionSnapshot()


def record_fresh_pull(
    snapshot: PacingSessionSnapshot,
    *,
    week_code: str,
    starts_on: str,
    ends_on: str,
    weekdays: dict[str, str],
    previous_week_starts_on: str,
    previous_week_ends_on: str,
    source_range: str = "",
    source_revision: str = "",
    pulled_at: str = "",
) -> PacingSessionSnapshot:
    """Record a successful fresh live read and mark the snapshot fresh."""
    snapshot.week_code = week_code
    snapshot.starts_on = starts_on
    snapshot.ends_on = ends_on
    snapshot.weekdays = dict(weekdays)
    snapshot.previous_week_starts_on = previous_week_starts_on
    snapshot.previous_week_ends_on = previous_week_ends_on
    snapshot.source_range = source_range
    snapshot.source_revision = source_revision
    snapshot.pulled_at = pulled_at
    snapshot.read_failed = False
    snapshot.read_failure_reason = ""
    snapshot.fresh = True
    return snapshot


def invalidate(snapshot: PacingSessionSnapshot) -> PacingSessionSnapshot:
    """Invalidate the current snapshot (refresh/verify/re-read forces a new pull)."""
    snapshot.fresh = False
    snapshot.pulled_at = ""
    snapshot.read_failed = False
    snapshot.read_failure_reason = ""
    return snapshot


def mark_read_failure(snapshot: PacingSessionSnapshot, reason: str) -> PacingSessionSnapshot:
    """Mark a failed live read; the build is blocked with a read-failure blocker."""
    snapshot.fresh = False
    snapshot.pulled_at = ""
    snapshot.read_failed = True
    snapshot.read_failure_reason = reason
    return snapshot


def _weekdays_complete(snapshot: PacingSessionSnapshot) -> bool:
    return all(bool(snapshot.weekdays.get(day)) for day in WEEKDAYS)


def is_fresh(snapshot: PacingSessionSnapshot) -> bool:
    return (
        snapshot.fresh
        and bool(snapshot.pulled_at)
        and not snapshot.read_failed
        and snapshot.source_spreadsheet_id == FPK_SPREADSHEET_ID
        and snapshot.source_sheet == FPK_SHEET_NAME
        and _weekdays_complete(snapshot)
    )


def covers_previous_week(snapshot: PacingSessionSnapshot) -> bool:
    """True when the snapshot includes the immediately previous school week."""
    return bool(snapshot.previous_week_starts_on) and bool(snapshot.previous_week_ends_on)


def build_blockers(snapshot: PacingSessionSnapshot) -> list[str]:
    blockers: list[str] = []
    if snapshot.read_failed:
        blockers.append(BLOCK_READ_FAILURE)
    if not snapshot.fresh or not snapshot.pulled_at:
        blockers.append(BLOCK_FRESH_PULL_REQUIRED)
    if snapshot.source_spreadsheet_id != FPK_SPREADSHEET_ID or snapshot.source_sheet != FPK_SHEET_NAME:
        blockers.append(BLOCK_WRONG_SOURCE)
    if not snapshot.starts_on or not snapshot.ends_on or not _weekdays_complete(snapshot):
        blockers.append(BLOCK_MISSING_WEEK_DATES)
    if not covers_previous_week(snapshot):
        blockers.append(BLOCK_PREVIOUS_WEEK_MISSING)
    return blockers


def can_build(snapshot: PacingSessionSnapshot) -> bool:
    """True only when a fresh, complete, correct-source pull has been recorded."""
    return not build_blockers(snapshot)


__all__ = [
    "BLOCK_FRESH_PULL_REQUIRED",
    "BLOCK_MISSING_WEEK_DATES",
    "BLOCK_PREVIOUS_WEEK_MISSING",
    "BLOCK_READ_FAILURE",
    "BLOCK_WRONG_SOURCE",
    "FPK_SHEET_NAME",
    "FPK_SPREADSHEET_ID",
    "PacingSessionSnapshot",
    "WEEKDAYS",
    "build_blockers",
    "can_build",
    "covers_previous_week",
    "invalidate",
    "is_fresh",
    "mark_read_failure",
    "new_session_snapshot",
    "record_fresh_pull",
    "weekdays_for_week",
]
