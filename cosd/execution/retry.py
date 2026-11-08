"""Bounded exponential backoff."""
from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone

BASE_DELAY_S = 1.0
MAX_DELAY_S = 60.0
MAX_ATTEMPTS_DEFAULT = 3


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def next_retry_at(attempt_number: int, *, max_attempts: int = MAX_ATTEMPTS_DEFAULT) -> str | None:
    if attempt_number >= max_attempts:
        return None
    delay = min(MAX_DELAY_S, BASE_DELAY_S * (2 ** (attempt_number - 1)))
    delay *= 0.9 + random.random() * 0.2
    return (_utc_now() + timedelta(seconds=delay)).isoformat(timespec="milliseconds")


def retry_due(retry_after_at: str | None) -> bool:
    if not retry_after_at:
        return True
    return _utc_now() >= datetime.fromisoformat(retry_after_at.replace("Z", "+00:00"))
