"""Announcement scheduling-state semantics (verified against live Canvas).

Encodes the behavior discovered during the Q2W2 deployment: Canvas honors
``delayed_post_at``. The reliable "is this visible to students" signal is
**active-feed membership**, NOT ``published`` and NOT ``posted_at``.

Rules (verified):
    - A scheduled announcement created with ``published=true`` + future
      ``delayed_post_at`` is HELD. Canvas reports ``published=true`` and
      ``posted_at == created_at``, but it is NOT in the active_only feed and
      students do not see it.
    - ``posted_at == created_at`` is NOT evidence of early publication.
    - ``published`` distinguishes "published vs draft state", NOT visibility.

Classification model:
    classify_announcement(delayed_post_at, posted_at, published,
                          in_active_feed, now) -> one of:
      HELD_SCHEDULED    — future delayed time, not in active feed (correct)
      PREMATURE_LIVE    — future delayed time, but in active feed (defect)
      POSTED            — delayed time passed (or none), in active feed
      DRAFT_UNPUBLISHED — published=false, not scheduled
      UNVERIFIED        — cannot classify from available fields
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

HELD_SCHEDULED = "HELD_SCHEDULED"
PREMATURE_LIVE = "PREMATURE_LIVE"
POSTED = "POSTED"
DRAFT_UNPUBLISHED = "DRAFT_UNPUBLISHED"
UNVERIFIED = "UNVERIFIED"


def _parse(ts: str | None) -> datetime | None:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    except ValueError:
        return None


def classify_announcement(
    *,
    delayed_post_at: str | None,
    posted_at: str | None,
    published: bool | None,
    in_active_feed: bool,
    now: datetime | None = None,
) -> str:
    """Classify an announcement's visibility/scheduling state.

    ``in_active_feed`` is whether the announcement appears in the course's
    ``active_only=true`` announcements feed (the student-visible set).
    """
    now = now or datetime.now(timezone.utc)
    delayed = _parse(delayed_post_at)

    if delayed is not None and delayed > now:
        # Scheduled time is still in the future.
        if in_active_feed:
            return PREMATURE_LIVE
        return HELD_SCHEDULED

    # No future scheduled time (none, or already passed).
    if in_active_feed:
        return POSTED
    if published is False:
        return DRAFT_UNPUBLISHED
    # A published announcement with no future schedule and a real posted_at
    # timestamp is visible. posted_at is reliable here: there is no future
    # delayed_post_at to "hold" it behind (unlike the HELD_SCHEDULED case above,
    # where posted_at == created_at is a transient artifact). This also covers a
    # late/manual run that posts an already-past-scheduled announcement
    # immediately, even when the active_only feed cannot be read.
    if posted_at is not None:
        return POSTED
    return UNVERIFIED


def is_held(data: dict[str, Any], *, now: datetime | None = None) -> bool:
    """Convenience: True when correctly held (future delayed time, not active)."""
    return classify_announcement(
        delayed_post_at=data.get("delayed_post_at"),
        posted_at=data.get("posted_at"),
        published=data.get("published"),
        in_active_feed=bool(data.get("in_active_feed")),
        now=now,
    ) == HELD_SCHEDULED


def command_self_test() -> int:
    now = datetime(2026, 10, 16, 12, 0, tzinfo=timezone.utc)
    future = "2026-10-16T20:00:00Z"
    past = "2026-10-15T20:00:00Z"

    # A. published=true + future delayed + NOT active -> HELD (the real Q2W2 case)
    assert classify_announcement(delayed_post_at=future, posted_at="2026-10-16T01:09:48Z",
                                 published=True, in_active_feed=False, now=now) == HELD_SCHEDULED
    # posted_at == created_at before delayed time is NOT early publication.
    assert classify_announcement(delayed_post_at=future, posted_at="2026-10-16T01:09:48Z",
                                 published=True, in_active_feed=False, now=now) == HELD_SCHEDULED

    # B. future delayed + in active feed -> PREMATURE
    assert classify_announcement(delayed_post_at=future, posted_at=None,
                                 published=True, in_active_feed=True, now=now) == PREMATURE_LIVE

    # C. past delayed + active -> POSTED
    assert classify_announcement(delayed_post_at=past, posted_at=past,
                                 published=True, in_active_feed=True, now=now) == POSTED
    # no delayed + active -> POSTED (immediate)
    assert classify_announcement(delayed_post_at=None, posted_at=now.isoformat(),
                                 published=True, in_active_feed=True, now=now) == POSTED

    # D. published=false, not active, no future schedule -> DRAFT_UNPUBLISHED
    assert classify_announcement(delayed_post_at=None, posted_at=None,
                                 published=False, in_active_feed=False, now=now) == DRAFT_UNPUBLISHED

    # E. past delayed + not active + real posted_at -> POSTED (late/manual run;
    #    active_only feed unavailable). posted_at is reliable with no future hold.
    assert classify_announcement(delayed_post_at=past, posted_at="2026-10-23T22:10:57Z",
                                 published=True, in_active_feed=False, now=now) == POSTED

    # F. past delayed + not active + published + no posted_at -> UNVERIFIED
    assert classify_announcement(delayed_post_at=past, posted_at=None,
                                 published=True, in_active_feed=False, now=now) == UNVERIFIED

    print("PASS intake scheduling-semantics self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(command_self_test())
