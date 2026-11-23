#!/usr/bin/env python3
"""Canonical assignment-group routing (OWNER_POLICY).

Resolves the exact Canvas assignment group and universal settings for any
generated assignment. Reads
``config/curriculum/canvas/assignment-routing-contract-2026-2027.json``.

Future weeks must never re-derive whether a Mastery Test goes in Assessments or
a Checkout goes in Check Out. This module is the single source of truth.

Fail-closed: an unknown subject/kind returns ``None``. Auto-creation is
governed by the OWNER_APPROVED_POLICY policy in ``assignment_policy``
(2026-11-17): tests/assessments, plus pacing-derived Math/Reading homework,
classwork, workbook, and comprehension work, may auto-prepare. Generic
homework/classwork and every other subject-specific restriction still fail
closed.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from . import assignment_policy
from . import constants as C

CONTRACT_PATH = (C.REPO_ROOT / "config" / "curriculum" / "canvas"
                 / "assignment-routing-contract-2026-2027.json")

_SUBJECT_ALIASES = {
    "reading": "reading_spelling",
    "spelling": "reading_spelling",
    "ela": "language_arts",
    "shurley": "language_arts",
}

# Canonical routing key / internal generator kind -> policy kind.
_POLICY_KIND = {
    "homework": "math_homework",
    "homework_accuracy_grade": "math_homework",
    "math_homework": "math_homework",
    "classwork": "math_classwork",
    "classwork_accuracy_grade": "math_classwork",
    "math_classwork": "math_classwork",
    "workbook": "reading_classwork",
    "workbook_and_comprehension": "reading_homework",
    "reading_workbook": "reading_classwork",
    "reading_classwork": "reading_classwork",
    "comprehension": "reading_homework",
    "comprehension_questions": "reading_homework",
    "reading_homework": "reading_homework",
}


def load_contract() -> dict[str, Any]:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def _subject_key(subject: str) -> str:
    key = (subject or "").strip().lower().replace("-", "_")
    return _SUBJECT_ALIASES.get(key, key)


def _policy_kind(subject: str, kind: str) -> str:
    key = (kind or "").strip().lower().replace("-", "_")
    subject_key = _subject_key(subject)
    if subject_key == "math" and key in _POLICY_KIND:
        return _POLICY_KIND[key]
    if subject_key == "reading_spelling" and key in _POLICY_KIND:
        return _POLICY_KIND[key]
    return assignment_policy.normalize_kind(kind)


def resolve_group(subject: str, kind: str) -> str | None:
    """Resolve the canonical Canvas group for a subject/kind, or None."""
    contract = load_contract()
    subject_key = _subject_key(subject)
    course = contract["courses"].get(subject_key)
    if not course:
        return None
    key = (kind or "").strip().lower().replace("-", "_")
    policy_kind = _policy_kind(subject, kind)
    scoped = assignment_policy.scoped_kind_spec(policy_kind)
    if scoped and scoped.get("courseId") == course.get("courseId"):
        return scoped.get("group")
    routing = course.get("routing", {})
    entry = routing.get(key)
    if entry is None:
        entry = routing.get(policy_kind)
    if entry is None:
        return None
    return entry.get("group")


def auto_create_allowed(subject: str, kind: str) -> bool:
    """Return True when the owner policy plus routing contract permits creation."""
    contract = load_contract()
    subject_key = _subject_key(subject)
    course = contract["courses"].get(subject_key)
    if not course:
        return False

    key = (kind or "").strip().lower().replace("-", "_")
    routing = course.get("routing", {})
    policy_kind = _policy_kind(subject, kind)
    scoped = assignment_policy.scoped_kind_spec(policy_kind)

    # Preserve origin/main behavior outside Math and Reading.
    if subject_key not in ("math", "reading_spelling"):
        only = course.get("autoCreateOnlyFor")
        if only is not None:
            return key in only
        return key in routing

    # Apply the scoped policy to Math and Reading only.
    only = course.get("autoCreateOnlyFor")
    if only is not None:
        candidate_keys = {key, policy_kind}
        if not candidate_keys & set(only):
            return False

    if routing.get(key) is None and routing.get(policy_kind) is None and not scoped:
        return False

    group = resolve_group(subject_key, kind)
    if not group:
        return False
    return assignment_policy.auto_prepare_allowed(
        policy_kind,
        course=course.get("courseId"),
        group=group,
    )


def universal_settings() -> dict[str, Any]:
    return load_contract()["universalSettings"]


def command_self_test() -> int:
    contract = load_contract()

    # Core routing.
    assert resolve_group("math", "written_assessment") == "Written Assessments"
    assert resolve_group("math", "fact_assessment") == "Fact Assessments"
    assert resolve_group("math", "homework") == "Homework/Class Work"
    assert resolve_group("math", "classwork") == "Homework/Class Work"
    assert resolve_group("reading_spelling", "mastery_test") == "Assessments"
    assert resolve_group("reading_spelling", "fluency_checkout") == "Check Out"
    assert resolve_group("reading_spelling", "spelling_test") == "Assessments"
    assert resolve_group("reading_spelling", "reading_classwork") == "Homework"
    assert resolve_group("reading_spelling", "reading_homework") == "Homework"
    assert resolve_group("language_arts", "chapter_test") == "Assessments"
    assert resolve_group("math", "bogus") is None
    assert resolve_group("bogus", "homework") is None

    # Auto-create gating (OWNER_APPROVED_POLICY, 2026-11-17).
    assert auto_create_allowed("history", "chapter_test") is True
    assert auto_create_allowed("history", "review") is False
    assert auto_create_allowed("science", "quiz") is True
    assert auto_create_allowed("science", "chapter_test") is True
    assert auto_create_allowed("math", "homework") is True
    assert auto_create_allowed("math", "classwork") is True
    assert auto_create_allowed("math", "homework_accuracy_grade") is True
    assert auto_create_allowed("math", "classwork_accuracy_grade") is True
    assert auto_create_allowed("math", "investigation") is False
    assert auto_create_allowed("reading_spelling", "workbook") is True
    assert auto_create_allowed("reading_spelling", "reading_classwork") is True
    assert auto_create_allowed("reading_spelling", "reading_homework") is True
    assert auto_create_allowed("reading_spelling", "mastery_test") is True
    assert auto_create_allowed("reading_spelling", "spelling_test") is True
    assert auto_create_allowed("reading_spelling", "quiz") is False
    assert auto_create_allowed("language_arts", "classroom_practice") is True
    assert auto_create_allowed("language_arts", "chapter_test") is True

    # Universal settings.
    s = universal_settings()
    assert s["points_possible"] == 100
    assert s["grading_type"] == "percent"
    assert s["submission_types"] == ["on_paper"]
    assert "omit_from_final_grade=true" in s["forbiddenAnomalies"]

    print("PASS assignment routing self-test")
    return 0


if __name__ == "__main__":
    sys.exit(command_self_test())
