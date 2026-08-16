"""Owner-approved Canvas policies (Phase 18E). Pure, deterministic, import-safe.

The owner has explicitly approved the homework due-time policy:

    Homework assigned on a school day must appear in Canvas as due on that
    *same calendar day at 11:59 p.m.*, using the canonical school/course
    timezone.

This module is the single authority for that rule and for the still-unresolved
publish-state policy. It is pure: standard library only, no wall-clock reads,
no network, no Canvas modules, no writes.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime
from typing import Any
from zoneinfo import ZoneInfo

from scripts.canvas_llm_phase27.canonicalize import canonical_hash

DEFAULT_TIMEZONE = "America/New_York"
DEFAULT_DUE_TIME_LOCAL = "23:59"
DEFAULT_SUBMISSION_TYPE = "on_paper"


@dataclass(frozen=True)
class OwnerCanvasPolicy:
    """Immutable owner-approved Canvas policy.

    ``publish_state`` remains ``"unresolved"``: the owner has *not* approved a
    default publication decision. A future writer request must never infer one.
    """

    schema_version: int = 1
    homework_due_day: str = "assigned_day"
    homework_due_time_local: str = DEFAULT_DUE_TIME_LOCAL
    homework_submission_type: str = DEFAULT_SUBMISSION_TYPE
    publish_state: str = "unresolved"  # "resolved" | "unresolved"
    publish_decision: str = ""  # "published" | "unpublished" (only when resolved)
    timezone: str = DEFAULT_TIMEZONE

    def to_dict(self) -> dict[str, Any]:
        return {
            "schemaVersion": self.schema_version,
            "homeworkDueDay": self.homework_due_day,
            "homeworkDueTimeLocal": self.homework_due_time_local,
            "homeworkSubmissionType": self.homework_submission_type,
            "publishState": self.publish_state,
            "publishDecision": self.publish_decision,
            "timezone": self.timezone,
        }

    def publication_resolved(self) -> bool:
        return self.publish_state == "resolved" and self.publish_decision in ("published", "unpublished")


def default_policy() -> OwnerCanvasPolicy:
    return OwnerCanvasPolicy()


def policy_hash(policy: OwnerCanvasPolicy) -> str:
    """Deterministic semantic hash of the policy (no volatile timestamps)."""
    return canonical_hash(policy.to_dict())


def policy_provenance(policy: OwnerCanvasPolicy) -> list[dict[str, Any]]:
    """Provenance showing the due-time value is derived from owner policy."""
    return [
        {
            "sourceType": "owner-canvas-policy",
            "sourceRef": "owner-approved Phase 18E Canvas policy",
            "details": (
                f"homework due {policy.homework_due_time_local} local on "
                f"{policy.homework_due_day} ({policy.timezone})"
            ),
        }
    ]


def due_timestamp(
    assigned_date: str,
    timezone: str = DEFAULT_TIMEZONE,
    due_time_local: str = DEFAULT_DUE_TIME_LOCAL,
) -> str:
    """Return a Canvas-compatible timezone-aware ``due_at`` timestamp.

    Combines the canonical assignment date with the owner-approved local due
    time in the canonical IANA timezone. DST is resolved by the zone database,
    never by a hardcoded UTC offset.

    Example::

        due_timestamp("2026-08-24", "America/New_York")
        # "2026-08-24T23:59:00-04:00"  (summer, EDT)

        due_timestamp("2026-01-15", "America/New_York")
        # "2026-01-15T23:59:00-05:00"  (winter, EST)

    Raises ValueError (fails closed) if the date is blank or malformed.
    """
    if not assigned_date:
        raise ValueError("unresolved assignment date: no due timestamp")
    day = date.fromisoformat(assigned_date)
    hour_s, _, minute_s = due_time_local.partition(":")
    hour = int(hour_s or 0)
    minute = int(minute_s or 0)
    tz = ZoneInfo(timezone)
    return datetime(day.year, day.month, day.day, hour, minute, 0, tzinfo=tz).isoformat()


__all__ = [
    "DEFAULT_DUE_TIME_LOCAL",
    "DEFAULT_SUBMISSION_TYPE",
    "DEFAULT_TIMEZONE",
    "OwnerCanvasPolicy",
    "default_policy",
    "due_timestamp",
    "policy_hash",
    "policy_provenance",
]
