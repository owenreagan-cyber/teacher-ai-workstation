"""Course-scoped identity for weekly Canvas artifacts.

Title equality is not identity. A Math item cannot satisfy Reading/Spelling,
a Q2W4 item cannot satisfy Q2W5, and a reminder cannot satisfy the assessment
or its first notice. This module does not invent Canvas IDs and does not
choose among multiple candidates.
"""
from __future__ import annotations

from typing import Any

from scripts.canvas_llm_deploy.preflight import (
    classify_assessment_reminder,
    classify_weekly_announcement,
)

FIELDS = (
    "school_year", "quarter", "week", "course_id", "artifact_type",
    "canonical_identity", "canvas_id", "title", "content_hash",
    "assessment_identity", "assessment_date", "due_at",
    "delayed_post_at", "approval_identity", "plan_fingerprint",
)


def identity_record(artifact: dict[str, Any], *, artifact_type: str) -> dict[str, Any]:
    """Copy the identity fields that are actually present. Missing fields stay absent."""
    record = {
        "school_year": artifact.get("school_year") or "2026-2027",
        "quarter": artifact.get("quarter"),
        "week": artifact.get("week") or artifact.get("week_code"),
        "course_id": artifact.get("course_id"),
        "artifact_type": artifact_type,
        "canonical_identity": artifact.get("canonical_identity") or artifact.get("assessment_identity"),
        "canvas_id": artifact.get("canvas_id") or artifact.get("assignment_id") or artifact.get("page_id") or artifact.get("announcement_id"),
        "title": artifact.get("title"),
        "content_hash": artifact.get("content_hash") or artifact.get("agenda_hash") or artifact.get("to_page_hash"),
        "assessment_identity": artifact.get("assessment_identity"),
        "assessment_date": artifact.get("assessment_date"),
        "due_at": artifact.get("due_utc") or artifact.get("due_at"),
        "delayed_post_at": artifact.get("delayed_post_at"),
        "approval_identity": artifact.get("approval_identity") or artifact.get("draft_hash"),
        "plan_fingerprint": artifact.get("plan_fingerprint"),
    }
    return {key: value for key, value in record.items() if value not in (None, "")}


def same_course_and_week(proposed: dict[str, Any], live: dict[str, Any]) -> bool:
    if proposed.get("course_id") is not None and live.get("course_id") not in (None, proposed.get("course_id")):
        return False
    proposed_week = proposed.get("week_code") or proposed.get("week")
    live_week = live.get("week_code") or live.get("week")
    if proposed_week and live_week and proposed_week != live_week:
        return False
    return True


def reconcile_weekly_announcement(proposed: dict[str, Any], live: list[dict[str, Any]]) -> str:
    return classify_weekly_announcement(proposed, live)


def reconcile_reminder(proposed: dict[str, Any], live: list[dict[str, Any]]) -> str:
    return classify_assessment_reminder(proposed, live)
