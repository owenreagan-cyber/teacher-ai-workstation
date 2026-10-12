"""Phase 3.5A — assignment routing resolver (OWNER_POLICY).

Deterministic resolution of the canonical assignment group + universal settings
for any generated assignment. Reads
``config/curriculum/canvas/assignment-routing-contract-2026-2027.json``.

Future weeks must never re-derive whether a Mastery Test goes in Assessments or
a Checkout goes in Check Out. This module is the single source of truth.

Fail-closed: an unknown subject/kind or a kind not in ``autoCreateOnlyFor``
(for History/Science) returns ``None`` (do not create).
"""
from __future__ import annotations

import json
import sys
from typing import Any

from . import constants as C


def load_contract() -> dict[str, Any]:
    return json.loads(C.ASSIGNMENT_ROUTING_CONTRACT_PATH.read_text(encoding="utf-8"))


def resolve_group(subject: str, kind: str) -> str | None:
    """Return the canonical assignment-group name for (subject, kind), else None."""
    contract = load_contract()
    course = contract["courses"].get(subject)
    if not course:
        return None
    routing = course.get("routing", {}).get(kind)
    if not routing:
        return None
    return routing.get("group")


def auto_create_allowed(subject: str, kind: str) -> bool:
    """Return True if OWNER_POLICY permits auto-creating this assignment kind."""
    contract = load_contract()
    course = contract["courses"].get(subject)
    if not course:
        return False
    only = course.get("autoCreateOnlyFor")
    if only is not None:
        return kind in only
    # No restriction list means all routed kinds are allowed (math/reading/LA).
    return kind in course.get("routing", {})


def universal_settings() -> dict[str, Any]:
    return load_contract()["universalSettings"]


def command_self_test() -> int:
    assert resolve_group("math", "written_assessment") == "Written Assessments"
    assert resolve_group("math", "fact_assessment") == "Fact Assessments"
    assert resolve_group("math", "homework") == "Homework/Class Work"
    assert resolve_group("math", "classwork") == "Homework/Class Work"
    assert resolve_group("reading_spelling", "workbook") == "Homework"
    assert resolve_group("reading_spelling", "workbook_and_comprehension") == "Homework"
    assert resolve_group("reading_spelling", "mastery_test") == "Assessments"
    assert resolve_group("reading_spelling", "fluency_checkout") == "Check Out"
    assert resolve_group("reading_spelling", "spelling_test") == "Assessments"
    assert resolve_group("language_arts", "classroom_practice") == "Classwork"
    assert resolve_group("language_arts", "chapter_test") == "Assessments"
    assert resolve_group("history", "chapter_test") == "Assignments"
    assert resolve_group("history", "quiz") == "Assignments"
    assert resolve_group("science", "chapter_test") == "Assignments"
    assert resolve_group("science", "quiz") == "Assignments"

    # Fail-closed: unknown subject/kind.
    assert resolve_group("math", "bogus") is None
    assert resolve_group("bogus", "homework") is None

    # Auto-create gating: History/Science only test/quiz.
    assert auto_create_allowed("history", "chapter_test") is True
    assert auto_create_allowed("history", "review") is False
    assert auto_create_allowed("science", "lab") is False
    assert auto_create_allowed("science", "quiz") is True
    assert auto_create_allowed("math", "homework") is True

    # Universal settings.
    s = universal_settings()
    assert s["points_possible"] == 100
    assert s["grading_type"] == "percent"
    assert s["submission_types"] == ["on_paper"]

    print("PASS assignment routing resolver self-test")
    return 0


if __name__ == "__main__":
    sys.exit(command_self_test())
