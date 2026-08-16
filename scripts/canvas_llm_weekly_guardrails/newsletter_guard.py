"""Homeroom newsletter guardrails.

Three rules are codified here:

1. The live Homeroom newsletter/front page must be read from Canvas before any
   edit (never an old local copy, project memory, or last week's version).
2. "Dates to Remember" cleanup removes only clearly-expired dates, preserves all
   future dates, and surfaces ambiguous dates instead of guessing.
3. The teacher must be shown the updated newsletter and asked the mandatory
   "anything to add?" question before it can move to final Canvas review.

Standard library only. No network, no Canvas, no writes.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from typing import Any

BLOCK_LIVE_READ_REQUIRED = "newsletter:live_read_required"
BLOCK_QUESTION_REQUIRED = "newsletter:question_required"


@dataclass
class NewsletterGuardState:
    live_read: bool = False
    live_page_verified: bool = False
    question_asked: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _as_date(value: Any) -> date:
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def prune_expired_dates(
    important_dates: list[dict[str, Any]],
    today: Any,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Partition ``important_dates`` into ``(kept, removed, ambiguous)``.

    - A date strictly before ``today`` is removed.
    - A date today or in the future is kept.
    - A missing or unparseable date is kept *and* surfaced as ambiguous.
    """
    cutoff = _as_date(today)
    kept: list[dict[str, Any]] = []
    removed: list[dict[str, Any]] = []
    ambiguous: list[dict[str, Any]] = []
    for item in important_dates:
        if not isinstance(item, dict):
            ambiguous.append(item)
            kept.append(item)
            continue
        value = str(item.get("date") or "").strip()
        if not value:
            ambiguous.append(item)
            kept.append(item)
            continue
        try:
            item_date = date.fromisoformat(value)
        except ValueError:
            ambiguous.append(item)
            kept.append(item)
            continue
        if item_date < cutoff:
            removed.append(item)
        else:
            kept.append(item)
    return kept, removed, ambiguous


def newsletter_blockers(state: NewsletterGuardState) -> list[str]:
    blockers: list[str] = []
    if not state.live_read:
        blockers.append(BLOCK_LIVE_READ_REQUIRED)
    if not state.question_asked:
        blockers.append(BLOCK_QUESTION_REQUIRED)
    return blockers


def can_finalize_newsletter(state: NewsletterGuardState) -> bool:
    return not newsletter_blockers(state)


__all__ = [
    "BLOCK_LIVE_READ_REQUIRED",
    "BLOCK_QUESTION_REQUIRED",
    "NewsletterGuardState",
    "can_finalize_newsletter",
    "newsletter_blockers",
    "prune_expired_dates",
]
