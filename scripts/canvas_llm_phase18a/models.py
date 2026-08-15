"""Canonical WeeklyPlan model (Phase 18A).

The WeeklyPlan is the sole normalized input for future preview and publishing
phases. It describes instructional/publishing intent only.

It must NOT embed permanent assumptions that belong in live Canvas
configuration. For example, a current assignment-group numeric ID is never
stored here as eternal truth; registry IDs are referenced/resolved separately
and verified during later preflight.

Serialization is JSON with camelCase keys to match repo convention.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

SCHEMA = "canonical-weekly-plan"
VERSION = 1

WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

KNOWN_COURSES = ["Reading/Spelling", "Math", "Language Arts", "History", "Science"]

REQUESTED_ARTIFACT_TYPES = ["page", "assignment", "announcement", "newsletter-front-page"]

DEFAULT_TIMEZONE = "America/New_York"


@dataclass
class Evidence:
    """Provenance for a single material decision."""

    source_class: str = ""  # one of SOURCE_PRECEDENCE
    reference: str = ""  # file path, tab name, instruction quote, etc.
    note: str = ""
    precedent_class: str = ""  # required when source_class == "precedent"

    def to_dict(self) -> dict[str, Any]:
        return {
            "sourceClass": self.source_class,
            "reference": self.reference,
            "note": self.note,
            "precedentClass": self.precedent_class,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Evidence":
        return cls(
            source_class=data.get("sourceClass", data.get("source_class", "")),
            reference=data.get("reference", ""),
            note=data.get("note", ""),
            precedent_class=data.get("precedentClass", data.get("precedent_class", "")),
        )


@dataclass
class DayEntry:
    """One weekday for one course."""

    weekday: str = ""  # "Monday" .. "Friday"
    date: str = ""  # "YYYY-MM-DD"
    in_class: str = ""  # normalized student-facing "In Class" text
    homework: str = ""  # normalized "Homework"/"At Home" text; empty = omit At Home
    raw: str = ""  # preserved raw pacing/instruction value (verbatim)
    blank: bool = False  # intentionally blank day; never guess content
    decided_source: str = ""  # source class that determined in_class/homework
    evidence: list[Evidence] = field(default_factory=list)
    ambiguity: str = ""  # non-empty = unresolved; must not be guessed

    def to_dict(self) -> dict[str, Any]:
        return {
            "weekday": self.weekday,
            "date": self.date,
            "inClass": self.in_class,
            "homework": self.homework,
            "raw": self.raw,
            "blank": self.blank,
            "decidedSource": self.decided_source,
            "evidence": [e.to_dict() for e in self.evidence],
            "ambiguity": self.ambiguity,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DayEntry":
        return cls(
            weekday=data.get("weekday", ""),
            date=data.get("date", ""),
            in_class=data.get("inClass", data.get("in_class", "")),
            homework=data.get("homework", ""),
            raw=data.get("raw", ""),
            blank=bool(data.get("blank", False)),
            decided_source=data.get("decidedSource", data.get("decided_source", "")),
            evidence=[Evidence.from_dict(e) for e in data.get("evidence", [])],
            ambiguity=data.get("ambiguity", ""),
        )


@dataclass
class CoursePlan:
    """Instructional/publishing intent for one course across the week."""

    course: str = ""  # one of KNOWN_COURSES
    days: list[DayEntry] = field(default_factory=list)  # exactly 5, Monday-Friday
    requested_artifacts: list[str] = field(default_factory=list)  # page, assignment, announcement
    protected: bool = False
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "course": self.course,
            "days": [d.to_dict() for d in self.days],
            "requestedArtifacts": list(self.requested_artifacts),
            "protected": self.protected,
            "notes": list(self.notes),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CoursePlan":
        return cls(
            course=data.get("course", ""),
            days=[DayEntry.from_dict(d) for d in data.get("days", [])],
            requested_artifacts=list(data.get("requestedArtifacts", data.get("requested_artifacts", []))),
            protected=bool(data.get("protected", False)),
            notes=list(data.get("notes", [])),
        )


@dataclass
class RequestedArtifacts:
    """Plan-level summary of requested artifact types."""

    pages: bool = False
    assignments: bool = False
    announcements: bool = False
    newsletter_front_page: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "pages": self.pages,
            "assignments": self.assignments,
            "announcements": self.announcements,
            "newsletterFrontPage": self.newsletter_front_page,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RequestedArtifacts":
        return cls(
            pages=bool(data.get("pages", False)),
            assignments=bool(data.get("assignments", False)),
            announcements=bool(data.get("announcements", False)),
            newsletter_front_page=bool(data.get("newsletterFrontPage", data.get("newsletter_front_page", False))),
        )


@dataclass
class WeeklyPlan:
    """Canonical normalized weekly instructional/publishing intent."""

    schema: str = SCHEMA
    version: int = VERSION
    school_year: str = ""
    quarter: int = 0
    week_number: int = 0
    week_code: str = ""
    monday_date: str = ""
    friday_date: str = ""
    timezone: str = DEFAULT_TIMEZONE
    source_metadata: list[Evidence] = field(default_factory=list)
    teacher_instructions: list[str] = field(default_factory=list)
    teacher_overrides: list[dict[str, Any]] = field(default_factory=list)
    courses: dict[str, CoursePlan] = field(default_factory=dict)
    assessments_reminders: list[dict[str, Any]] = field(default_factory=list)
    requested_artifacts: RequestedArtifacts = field(default_factory=RequestedArtifacts)
    protected_courses: list[str] = field(default_factory=list)
    unresolved_ambiguities: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    provenance: list[Evidence] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "version": self.version,
            "schoolYear": self.school_year,
            "quarter": self.quarter,
            "weekNumber": self.week_number,
            "weekCode": self.week_code,
            "mondayDate": self.monday_date,
            "fridayDate": self.friday_date,
            "timezone": self.timezone,
            "sourceMetadata": [e.to_dict() for e in self.source_metadata],
            "teacherInstructions": list(self.teacher_instructions),
            "teacherOverrides": [dict(o) for o in self.teacher_overrides],
            "courses": {name: course.to_dict() for name, course in self.courses.items()},
            "assessmentsReminders": [dict(a) for a in self.assessments_reminders],
            "requestedArtifacts": self.requested_artifacts.to_dict(),
            "protectedCourses": list(self.protected_courses),
            "unresolvedAmbiguities": [dict(a) for a in self.unresolved_ambiguities],
            "warnings": list(self.warnings),
            "provenance": [e.to_dict() for e in self.provenance],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WeeklyPlan":
        courses_raw = data.get("courses", {})
        courses = {name: CoursePlan.from_dict(c) for name, c in courses_raw.items()}
        return cls(
            schema=data.get("schema", SCHEMA),
            version=int(data.get("version", VERSION)),
            school_year=data.get("schoolYear", data.get("school_year", "")),
            quarter=int(data.get("quarter", 0)),
            week_number=int(data.get("weekNumber", data.get("week_number", 0))),
            week_code=data.get("weekCode", data.get("week_code", "")),
            monday_date=data.get("mondayDate", data.get("monday_date", "")),
            friday_date=data.get("fridayDate", data.get("friday_date", "")),
            timezone=data.get("timezone", DEFAULT_TIMEZONE),
            source_metadata=[Evidence.from_dict(e) for e in data.get("sourceMetadata", data.get("source_metadata", []))],
            teacher_instructions=list(data.get("teacherInstructions", data.get("teacher_instructions", []))),
            teacher_overrides=[dict(o) for o in data.get("teacherOverrides", data.get("teacher_overrides", []))],
            courses=courses,
            assessments_reminders=[dict(a) for a in data.get("assessmentsReminders", data.get("assessments_reminders", []))],
            requested_artifacts=RequestedArtifacts.from_dict(data.get("requestedArtifacts", data.get("requested_artifacts", {}))),
            protected_courses=list(data.get("protectedCourses", data.get("protected_courses", []))),
            unresolved_ambiguities=[dict(a) for a in data.get("unresolvedAmbiguities", data.get("unresolved_ambiguities", []))],
            warnings=list(data.get("warnings", [])),
            provenance=[Evidence.from_dict(e) for e in data.get("provenance", [])],
        )

    def to_json(self, *, indent: int | None = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True)

    @classmethod
    def from_json(cls, text: str) -> "WeeklyPlan":
        return cls.from_dict(json.loads(text))
