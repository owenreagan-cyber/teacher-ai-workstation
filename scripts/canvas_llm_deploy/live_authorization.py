"""Quarter/week live-transport authorization.

The Q1W2 environment flag does not authorize any other week. A weekly live
client must present a record bound to that week, the current source hash, the
current plan fingerprint, and the course being written. The record contains no
credentials.
"""
from __future__ import annotations

import json
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any

from scripts.canvas_llm_intake import manifest as imf
from scripts.canvas_llm_phase22.canvas_connection import (
    ELA_COURSE_ID,
    HOMEROOM_COURSE_ID,
    MATH_COURSE_ID,
    READING_COURSE_ID,
    SCIENCE_COURSE_ID,
)

SCHOOL_YEAR = "2026-2027"
FILE_NAME = "live-transport-authorization.json"
KNOWN_COURSE_IDS = {
    HOMEROOM_COURSE_ID,
    MATH_COURSE_ID,
    READING_COURSE_ID,
    ELA_COURSE_ID,
    SCIENCE_COURSE_ID,
}
_SCOPE: ContextVar[dict[str, Any] | None] = ContextVar("live_authorization_scope", default=None)


class LiveAuthorizationError(RuntimeError):
    """The live transport is not authorized for this quarter and week."""


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse(value: str | None) -> datetime:
    if not value:
        raise LiveAuthorizationError("authorization timestamp is missing")
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError as exc:
        raise LiveAuthorizationError("authorization timestamp is invalid") from exc
    if parsed.tzinfo is None:
        raise LiveAuthorizationError("authorization timestamp must include a timezone")
    return parsed.astimezone(timezone.utc)


def authorization_path(quarter: int, week: int):
    return imf.staging_dir(quarter, week) / "planner" / FILE_NAME


def load_authorization(quarter: int, week: int) -> dict[str, Any] | None:
    path = authorization_path(quarter, week)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def authorize_live_transport(
    *,
    school_year: str,
    quarter: int,
    week: int,
    source_hash: str,
    plan_fingerprint: str,
    publication_time: str,
    course_ids: list[int],
    authorized_by: str,
    reason: str,
    expires_at: str,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Record owner authorization for one week. Timestamps are supplied or taken from the clock."""
    if school_year != SCHOOL_YEAR:
        raise LiveAuthorizationError("academic year is not authorized")
    if not source_hash or not plan_fingerprint:
        raise LiveAuthorizationError("source hash and plan fingerprint are required")
    if not course_ids or any(int(course_id) not in KNOWN_COURSE_IDS for course_id in course_ids):
        raise LiveAuthorizationError("authorization names an unknown course")
    publication = _parse(publication_time)
    expiry = _parse(expires_at)
    now = now or _now()
    if publication <= now or expiry <= now:
        raise LiveAuthorizationError("authorization publication time must be in the future")
    record = {
        "school_year": school_year,
        "quarter": int(quarter),
        "week": int(week),
        "state": "ACTIVE",
        "source_hash": source_hash,
        "plan_fingerprint": plan_fingerprint,
        "publication_time": publication.isoformat().replace("+00:00", "Z"),
        "course_ids": [int(course_id) for course_id in course_ids],
        "authorized_by": authorized_by,
        "authorized_at": now.isoformat().replace("+00:00", "Z"),
        "expires_at": expiry.isoformat().replace("+00:00", "Z"),
        "reason": reason,
    }
    path = authorization_path(quarter, week)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return record


def clear_scope() -> None:
    _SCOPE.set(None)


def require_scoped_live_transport(*, quarter: int, week: int, now: datetime | None = None) -> dict[str, Any]:
    """Validate the week record against the current manifest. No network."""
    clear_scope()
    clock = now or _now()
    record = load_authorization(quarter, week)
    if not record:
        raise LiveAuthorizationError(
            f"missing live authorization for {SCHOOL_YEAR} Q{quarter}W{week}"
        )
    if record.get("school_year") != SCHOOL_YEAR:
        raise LiveAuthorizationError("authorization academic year does not match")
    if int(record.get("quarter") or 0) != int(quarter) or int(record.get("week") or 0) != int(week):
        raise LiveAuthorizationError("authorization quarter or week does not match")
    if record.get("state") != "ACTIVE":
        raise LiveAuthorizationError("authorization is not active")
    if _parse(record.get("expires_at")) <= clock:
        raise LiveAuthorizationError("authorization has expired")
    manifest = imf.load_manifest(quarter, week) or {}
    if not manifest.get("source_hash") or record.get("source_hash") != manifest.get("source_hash"):
        raise LiveAuthorizationError("authorization source hash does not match the current manifest")
    if not manifest.get("plan_fingerprint") or record.get("plan_fingerprint") != manifest.get("plan_fingerprint"):
        raise LiveAuthorizationError("authorization plan fingerprint does not match the current manifest")
    courses = [int(course_id) for course_id in record.get("course_ids") or []]
    if not courses or any(course_id not in KNOWN_COURSE_IDS for course_id in courses):
        raise LiveAuthorizationError("authorization course list is invalid")
    _SCOPE.set(record)
    return record


def require_authorized_course(course_id: int) -> None:
    """Reject a course that the active week authorization did not name."""
    record = _SCOPE.get()
    if record is None:
        return
    if int(course_id) not in {int(item) for item in record.get("course_ids") or []}:
        raise LiveAuthorizationError(f"course {course_id} is not authorized for this week")
