"""Structured, non-authoritative AI review records for Canvas Planner."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Protocol

from scripts.canvas_llm_intake import manifest
from scripts.canvas_llm_intake import constants

from .events import append_event

CHECKS = (
    "plan_matches_sheet",
    "owner_edits_kept",
    "no_missing_assignments",
    "no_assignments_without_lesson",
    "assessments_and_reminders",
    "course_subject_isolation",
    "page_announcement_agree",
    "shorthand_interpretation",
)
VALID_STATES = ("PASS", "WARN", "NEEDS_OWEN", "FAIL", "UNAVAILABLE", "PENDING", "STALE")


class Reviewer(Protocol):
    model: str

    def review(self, packet: dict[str, Any]) -> dict[str, Any]: ...


def _now() -> datetime:
    return datetime.now(timezone.utc)


def review_path(quarter: int, week: int) -> Path:
    return manifest.staging_dir(quarter, week) / "planner" / "ai-review.json"


def _packet_hash(packet: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(packet, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def schedule(quarter: int, week: int, *, reason: str, delay_seconds: int = 2) -> dict[str, Any]:
    """Mark review pending after an edit; no model is invoked by this call."""
    now = _now()
    record = {
        "schemaVersion": 1,
        "state": "PENDING",
        "reason": reason,
        "scheduled_at": now.isoformat(),
        "not_before": (now + timedelta(seconds=delay_seconds)).isoformat(),
        "model": None,
        "courses": {},
    }
    _save(quarter, week, record)
    return record


def run(quarter: int, week: int, *, reviewer: Reviewer, packet: dict[str, Any]) -> dict[str, Any]:
    """Run a supplied eligible reviewer and persist only structured findings.

    The reviewer receives a plain data copy and has no state paths or mutation
    functions. Its output is validated before it becomes review evidence.
    """
    raw = reviewer.review(json.loads(json.dumps(packet)))
    courses = raw.get("courses") if isinstance(raw, dict) else None
    if not isinstance(courses, dict):
        raise ValueError("reviewer output must contain courses")
    for course, result in courses.items():
        if result.get("state") not in VALID_STATES:
            raise ValueError(f"invalid AI review state for {course}")
        for finding in result.get("findings") or []:
            if not finding.get("evidence"):
                raise ValueError("every AI finding requires evidence")
            if finding.get("status") not in ("PASS", "WARN", "NEEDS_OWEN", "FAIL"):
                raise ValueError("invalid AI finding status")
    now = _now().isoformat()
    record = {
        "schemaVersion": 1,
        "state": "COMPLETE",
        "created_at": now,
        "updated_at": now,
        "model": reviewer.model,
        "packet_hash": _packet_hash(packet),
        "checks": raw.get("checks") or [],
        "courses": courses,
    }
    _save(quarter, week, record)
    append_event(
        manifest.staging_dir(quarter, week), action="ai_review_completed", actor="ai_reviewer",
        reason=f"Structured review completed with {reviewer.model}.",
        after={"model": reviewer.model, "packet_hash": record["packet_hash"]},
    )
    return record


def unavailable(quarter: int, week: int, *, reason: str) -> dict[str, Any]:
    """Record an explicit unavailable state; never converts it to PASS."""
    now = _now().isoformat()
    record = {
        "schemaVersion": 1,
        "state": "UNAVAILABLE",
        "created_at": now,
        "updated_at": now,
        "model": None,
        "reason": reason,
        "checks": [{"id": check, "state": "UNAVAILABLE"} for check in CHECKS],
        "courses": {
            course: {"state": "UNAVAILABLE", "findings": []}
            for course in (*constants.active_subject_keys_for_quarter(quarter), "homeroom")
        },
    }
    _save(quarter, week, record)
    append_event(
        manifest.staging_dir(quarter, week), action="ai_review_unavailable", actor="system",
        reason=reason, after={"state": "UNAVAILABLE"},
    )
    return record


def answer_finding(
    quarter: int, week: int, *, finding_id: str, answer: str
) -> dict[str, Any]:
    """Record Owen's answer. This never edits plans or artifacts."""
    record = load(quarter, week)
    if not record:
        raise ValueError("no AI review")
    if answer not in ("ACCEPT", "DECLINE"):
        raise ValueError("answer must be ACCEPT or DECLINE")
    found = None
    for result in (record.get("courses") or {}).values():
        for finding in result.get("findings") or []:
            if finding.get("id") == finding_id:
                found = finding
                break
    if found is None:
        raise ValueError("unknown AI finding")
    before = dict(found)
    found["resolution"] = answer
    found["resolved_at"] = _now().isoformat()
    found["status"] = "WARN" if answer == "DECLINE" else "PASS"
    record["updated_at"] = _now().isoformat()
    _save(quarter, week, record)
    append_event(
        manifest.staging_dir(quarter, week), action="ai_finding_answered", actor="owner",
        reason=f"Owen chose {answer.lower()} for {finding_id}.", before=before, after=found,
        undo={"action": "restore_ai_finding", "finding_id": finding_id, "value": before},
    )
    return found


def load(quarter: int, week: int) -> dict[str, Any] | None:
    try:
        value = json.loads(review_path(quarter, week).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _save(quarter: int, week: int, record: dict[str, Any]) -> None:
    path = review_path(quarter, week)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
