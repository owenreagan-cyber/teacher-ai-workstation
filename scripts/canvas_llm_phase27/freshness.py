from __future__ import annotations

from datetime import datetime, timezone

# Local policy defaults, not universal facts: how old a snapshot may be
# before it is considered aging/stale/expired. A different program could
# choose different thresholds.
DEFAULT_AGING_THRESHOLD_HOURS = 24
DEFAULT_STALE_THRESHOLD_HOURS = 72
DEFAULT_EXPIRED_THRESHOLD_HOURS = 168  # 7 days

FRESHNESS_STATES = {"fresh", "aging", "stale", "expired", "unknown"}


def _parse(timestamp: str) -> datetime | None:
    try:
        value = timestamp.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed
    except (ValueError, AttributeError):
        return None


def classify_freshness(
    generated_at: str,
    now: datetime | None = None,
    aging_hours: float = DEFAULT_AGING_THRESHOLD_HOURS,
    stale_hours: float = DEFAULT_STALE_THRESHOLD_HOURS,
    expired_hours: float = DEFAULT_EXPIRED_THRESHOLD_HOURS,
) -> str:
    """Classify a snapshot's freshness from its generatedAt timestamp.
    Unknown/unparseable timestamps are never silently treated as fresh --
    they require review, matching the Phase 27 safety requirement that
    unknown freshness cannot silently pass."""
    parsed = _parse(generated_at)
    if parsed is None:
        return "unknown"
    reference = now or datetime.now(timezone.utc)
    if reference.tzinfo is None:
        reference = reference.replace(tzinfo=timezone.utc)
    age_hours = (reference - parsed).total_seconds() / 3600.0
    if age_hours < 0:
        return "unknown"
    if age_hours <= aging_hours:
        return "fresh"
    if age_hours <= stale_hours:
        return "aging"
    if age_hours <= expired_hours:
        return "stale"
    return "expired"


def blocks_readiness(freshness_state: str) -> bool:
    return freshness_state in {"stale", "expired", "unknown"}
