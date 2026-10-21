"""Shared constants for the Canvas Weekly Intake workspace.

Reuses the Phase 3 pacing constants (spreadsheet identity, sheet name, weekday
order, instructional-weeks path) so the intake layer never re-declares source
authority that already lives in ``scripts.canvas_llm_phase3.constants``.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from scripts.canvas_llm_phase3 import constants as P3
from scripts.canvas_planner.state_root import intake_root

REPO_ROOT = P3.REPO_ROOT

# --------------------------------------------------------------------------- #
# Staging workspace
# --------------------------------------------------------------------------- #
INTAKE_ROOT = intake_root()

# Lifecycle states (intake/staging specific; PUBLISHED_VERIFIED is never reached
# by this package — publishing belongs to the guarded deployment workflow).
LIFECYCLE_STATES = (
    "SOURCE_FETCHED",
    "NORMALIZED",
    "DRAFTED",
    "NEEDS_INPUT",
    "READY_FOR_REVIEW",
    "TEACHER_APPROVED",
    "READY_TO_PUBLISH",
    "PUBLISHED_VERIFIED",
)

# Approval granularities + states.
APPROVAL_STATES = ("PENDING", "NEEDS_CHANGES", "APPROVED", "BLOCKED")

# Academic subject keys (Homeroom is a separate family/newsletter workflow).
SUBJECT_KEYS = ("math", "reading_spelling", "language_arts", "science", "history")

# Course mapping (single source of truth: canvas-course-mappings.json).
_COURSE_MAPPINGS_PATH = REPO_ROOT / "config" / "curriculum" / "canvas-course-mappings.json"


def load_course_mappings() -> dict[str, Any]:
    return json.loads(_COURSE_MAPPINGS_PATH.read_text(encoding="utf-8"))


def production_courses() -> list[dict[str, Any]]:
    data = load_course_mappings()
    return data.get("currentProduction", {}).get("courses", [])


def course_id_for_subject(subject_id: str) -> int | None:
    """Resolve the production Canvas course id for a subject id.

    ``reading`` and ``spelling`` both map to course 26442.
    """
    for course in production_courses():
        if course.get("subjectId") == subject_id:
            return int(course["courseId"])
    return None


def subject_display(subject_id: str) -> str:
    for course in production_courses():
        if course.get("subjectId") == subject_id:
            return course.get("displayName", subject_id)
    return subject_id


# Quarter activation (History vs Science rotation).
QUARTER_ACTIVATION_PATH = P3.QUARTER_ACTIVATION_PATH


def load_quarter_activation() -> dict[str, Any]:
    return json.loads(QUARTER_ACTIVATION_PATH.read_text(encoding="utf-8"))


def active_rotating_subject(quarter: int) -> str:
    """Return 'history' or 'science' for a quarter."""
    activation = load_quarter_activation()
    q = activation.get("quarters", {}).get(f"Q{quarter}", {})
    return q.get("activeSubject", "")


def active_subject_keys_for_quarter(quarter: int) -> list[str]:
    """Academic subjects active for a quarter.

    Math / Reading+Spelling / Language Arts are always active. History is active
    in Q1/Q3; Science in Q2/Q4. Homeroom is excluded (separate workflow).
    """
    rotating = active_rotating_subject(quarter)
    keys = ["math", "reading_spelling", "language_arts"]
    if rotating == "history":
        keys.append("history")
    elif rotating == "science":
        keys.append("science")
    return keys


# Canonical assignment defaults (OWNER_POLICY).
ASSIGNMENT_DEFAULTS = {
    "points_possible": 100,
    "grading_type": "percent",
    "submission_types": ["on_paper"],
    "omit_from_final_grade": False,
    "due_time": "11:59 PM",
    "timezone": "America/New_York",
}

# Weekdays (reuse Phase 3).
WEEKDAYS = P3.WEEKDAYS
