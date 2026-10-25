"""Canonical Weekly Planner Agent models.

Pure data model (no network, no Canvas, no file I/O). The WeeklyPlan is the
single source for downstream generated artifacts; Canvas and the pacing sheet
are inputs, not the source of truth.

Authority hierarchy (lower number = higher priority):
    OWNER_INSTRUCTION > VERIFIED_PACING > VERIFIED_CANVAS > SUBJECT_RULES > INFERENCE
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import IntEnum
from typing import Any


class Authority(IntEnum):
    """Source authority. Lower value wins; conflicts are surfaced, never guessed."""

    OWNER_INSTRUCTION = 1
    VERIFIED_PACING = 2
    VERIFIED_CANVAS = 3
    SUBJECT_RULES = 4
    INFERENCE = 5


class Confidence(str):
    """Confidence/status of a plan element."""

    CONFIRMED = "confirmed"
    INFERRED = "inferred"
    PREDICTED = "predicted"


class PlanStatus(str):
    """State boundary of a plan element or artifact."""

    CONFIRMED_SOURCE = "confirmed_source"
    PLANNED = "planned"
    APPROVED = "approved"
    LIVE = "live"
    VERIFIED = "verified"


# Friday Review lifecycle (mirrors the contract language without the scheduler).
FRIDAY_BUILDING = "BUILDING"
FRIDAY_NEEDS_OWEN = "NEEDS_OWEN"
FRIDAY_READY_FOR_REVIEW = "READY_FOR_REVIEW"
FRIDAY_CHANGES_DETECTED = "CHANGES_DETECTED"
FRIDAY_APPROVED = "APPROVED"
FRIDAY_PUBLISHING = "PUBLISHING"
FRIDAY_PUBLISHED_VERIFIED = "PUBLISHED_VERIFIED"
FRIDAY_BLOCKED = "BLOCKED"
FRIDAY_STATES = (
    FRIDAY_BUILDING,
    FRIDAY_NEEDS_OWEN,
    FRIDAY_READY_FOR_REVIEW,
    FRIDAY_CHANGES_DETECTED,
    FRIDAY_APPROVED,
    FRIDAY_PUBLISHING,
    FRIDAY_PUBLISHED_VERIFIED,
    FRIDAY_BLOCKED,
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# SourceChangeEvent lifecycle states (durable, persisted).
EVENT_DETECTED = "DETECTED"
EVENT_ANALYZING = "ANALYZING"
EVENT_NEEDS_OWEN = "NEEDS_OWEN"
EVENT_PLAN_UPDATED = "PLAN_UPDATED"
EVENT_APPROVED = "APPROVED"
EVENT_IGNORED = "IGNORED"
EVENT_RESOLVED = "RESOLVED"
EVENT_BLOCKED = "BLOCKED"
EVENT_LIFECYCLE_STATES = (
    EVENT_DETECTED,
    EVENT_ANALYZING,
    EVENT_NEEDS_OWEN,
    EVENT_PLAN_UPDATED,
    EVENT_APPROVED,
    EVENT_IGNORED,
    EVENT_RESOLVED,
    EVENT_BLOCKED,
)

# Notification status (delivery is not enabled this phase; drafts are validated
# against fake/local sinks only).
NOTIFICATION_PENDING = "pending"
NOTIFICATION_DRAFTED = "drafted"
NOTIFICATION_QUEUED = "queued"
NOTIFICATION_DELIVERED = "delivered"
NOTIFICATION_FAILED = "failed"
NOTIFICATION_SUPPRESSED = "suppressed"
NOTIFICATION_STATUSES = (
    NOTIFICATION_PENDING,
    NOTIFICATION_DRAFTED,
    NOTIFICATION_QUEUED,
    NOTIFICATION_DELIVERED,
    NOTIFICATION_FAILED,
    NOTIFICATION_SUPPRESSED,
)


@dataclass
class Assessment:
    """A planned assessment/test."""

    name: str
    subject: str
    day: str | None = None
    date: str | None = None
    previous_date: str | None = None
    authority: Authority = Authority.VERIFIED_PACING
    confidence: str = Confidence.CONFIRMED

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "subject": self.subject,
            "day": self.day,
            "date": self.date,
            "previous_date": self.previous_date,
            "authority": int(self.authority),
            "confidence": self.confidence,
        }


@dataclass
class DayPlan:
    """One subject/day plan cell."""

    subject: str
    day: str
    date: str | None = None
    lesson: str | None = None
    classwork: list[str] = field(default_factory=list)
    homework: list[str] = field(default_factory=list)
    assessment: Assessment | None = None
    status: str = PlanStatus.PLANNED
    authority: Authority = Authority.VERIFIED_PACING
    confidence: str = Confidence.CONFIRMED
    teacher_override: dict[str, Any] | None = None
    source_value: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "subject": self.subject,
            "day": self.day,
            "date": self.date,
            "lesson": self.lesson,
            "classwork": list(self.classwork),
            "homework": list(self.homework),
            "assessment": self.assessment.to_dict() if self.assessment else None,
            "status": self.status,
            "authority": int(self.authority),
            "confidence": self.confidence,
            "teacher_override": self.teacher_override,
            "source_value": self.source_value,
        }


@dataclass
class WeeklyPlan:
    """Canonical weekly plan for one instructional week."""

    week_id: str
    quarter: int
    week: int
    date_range: dict[str, str] = field(default_factory=dict)
    subjects: dict[str, list[DayPlan]] = field(default_factory=dict)
    homeroom_items: list[dict[str, Any]] = field(default_factory=list)
    assignment_candidates: list[dict[str, Any]] = field(default_factory=list)
    announcement_candidates: list[dict[str, Any]] = field(default_factory=list)
    reminder_candidates: list[dict[str, Any]] = field(default_factory=list)
    source_provenance: dict[str, Any] = field(default_factory=dict)
    freshness: dict[str, Any] = field(default_factory=dict)
    approval_status: dict[str, Any] = field(default_factory=dict)
    change_history: list[dict[str, Any]] = field(default_factory=list)

    def day(self, subject: str, day: str) -> DayPlan | None:
        for item in self.subjects.get(subject, []):
            if item.day == day:
                return item
        return None

    def upsert_day(self, item: DayPlan) -> None:
        days = self.subjects.setdefault(item.subject, [])
        for index, existing in enumerate(days):
            if existing.day == item.day:
                days[index] = item
                return
        days.append(item)

    def assessments(self) -> list[tuple[str, Assessment]]:
        out: list[tuple[str, Assessment]] = []
        for subject, days in self.subjects.items():
            for day in days:
                if day.assessment is not None:
                    out.append((subject, day.assessment))
        return out

    def to_dict(self) -> dict[str, Any]:
        return {
            "week_id": self.week_id,
            "quarter": self.quarter,
            "week": self.week,
            "date_range": self.date_range,
            "subjects": {s: [d.to_dict() for d in days] for s, days in self.subjects.items()},
            "homeroom_items": self.homeroom_items,
            "assignment_candidates": self.assignment_candidates,
            "announcement_candidates": self.announcement_candidates,
            "reminder_candidates": self.reminder_candidates,
            "source_provenance": self.source_provenance,
            "freshness": self.freshness,
            "approval_status": self.approval_status,
            "change_history": self.change_history,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)


@dataclass
class SourceChangeEvent:
    """A structured, auditable source/plan change (powers later notifications).

    ``event_id`` is a stable, dedup-able identity (hash of the underlying
    identity + old/new values). ``resolution_status`` tracks the durable
    lifecycle; ``notification_status`` tracks draft/delivery (delivery is not
    enabled this phase).
    """

    source: str
    subject: str
    object_type: str
    old_value: str | None
    new_value: str | None
    timestamp: str = field(default_factory=_now)
    confidence: str = Confidence.CONFIRMED
    severity: str = "info"
    affected_artifacts: list[str] = field(default_factory=list)
    requires_teacher_approval: bool = True
    live_canvas_stale: bool = False
    family_comms_affected: bool = False
    approved: bool = False
    event_id: str = ""
    week_id: str = ""
    object_identity: str | None = None
    classification: str = ""
    source_identity: str = ""
    notification_status: str = NOTIFICATION_PENDING
    resolution_status: str = EVENT_DETECTED
    # Cross-source conflict fields (empty for temporal events). ``authority_winner``
    # is the higher-authority source name; ``pacing_value``/``canvas_value`` carry
    # the explicit normalized values so the UI never guesses which side disagreed.
    authority_winner: str = ""
    teacher_override: dict[str, Any] | None = None
    pacing_value: str | None = None
    canvas_value: str | None = None
    source_timestamps: dict[str, Any] = field(default_factory=dict)
    source_freshness: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Notification:
    """Internal notification model (email delivery may be wired in a later phase)."""

    notification_type: str
    subject_line: str
    body: str
    actions: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=_now)
    requires_send: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class FridayReview:
    """One-screen Friday review summary + state machine state."""

    week_id: str
    state: str = FRIDAY_BUILDING
    pages_count: int = 0
    assignments_count: int = 0
    announcements_count: int = 0
    reminders_count: int = 0
    changes_since_last_review: list[dict[str, Any]] = field(default_factory=list)
    unresolved_conflicts: list[dict[str, Any]] = field(default_factory=list)
    source_freshness: dict[str, Any] = field(default_factory=dict)
    changed_subjects: list[str] = field(default_factory=list)
    blocking: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PlanApproval:
    """A plan-version-bound approval record (thin; not a duplicate of the
    canonical per-artifact approval store — it binds one teacher approval to
    the exact plan/source versions that were reviewed)."""

    week_id: str
    plan_version: str
    source_fingerprint: str
    canvas_fingerprint: str = ""
    approved_at: str = field(default_factory=_now)
    approved_by: str = "OWNER_UI"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
