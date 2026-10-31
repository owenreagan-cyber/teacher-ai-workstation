"""Reusable student-facing communication policies.

Thales Academy does not provide study guides for any class. This module is the
single deterministic guard used by generated agendas, announcements, assignment
instructions, and Homeroom communication drafts. It rejects both positive
promises/references and negative disclaimers: the correct behavior is to state
only the actual preparation instructions.
"""
from __future__ import annotations

import re
from typing import Iterable

# Matches "study guide", "study guides", "review guide", and simple hyphenated
# or multi-space variants. This is intentionally broad: the policy forbids the
# concept, not one exact spelling.
_FORBIDDEN_RE = re.compile(
    r"\b(?:study|review)[\s-]*guides?\b",
    re.IGNORECASE,
)


def find_study_guide_references(text: str) -> list[str]:
    """Return every forbidden study-guide phrase found in ``text``."""
    if not text:
        return []
    return [match.group(0) for match in _FORBIDDEN_RE.finditer(str(text))]


def assert_no_study_guide_references(text: str, *, artifact: str) -> None:
    """Fail closed when a student-facing artifact references a study guide."""
    found = find_study_guide_references(text)
    if found:
        unique = sorted({item.lower() for item in found})
        raise ValueError(
            f"{artifact}: forbidden Thales study-guide reference(s): {', '.join(unique)}"
        )


def audit_student_facing_texts(texts: dict[str, str]) -> list[str]:
    """Audit named artifacts; return human-readable violations (empty = clean)."""
    violations: list[str] = []
    for name, text in texts.items():
        for found in find_study_guide_references(text):
            violations.append(f"{name}: {found}")
    return violations


def assert_clean_student_facing_texts(texts: dict[str, str]) -> None:
    violations = audit_student_facing_texts(texts)
    if violations:
        raise ValueError(
            "Thales no-study-guide policy violation(s): " + "; ".join(violations)
        )


def command_self_test() -> int:
    assert find_study_guide_references("A study guide will be provided.") == ["study guide"]
    assert find_study_guide_references("No study guide will be provided.") == ["study guide"]
    assert find_study_guide_references("Review guide attached.") == ["Review guide"]
    assert find_study_guide_references("Study-guides are not used.") == ["Study-guides"]
    assert find_study_guide_references("Review your workbook and the stories from Lessons 41-50.") == []
    assert find_study_guide_references("") == []

    try:
        assert_no_study_guide_references("See the study guide.", artifact="test")
        raise AssertionError("expected ValueError")
    except ValueError:
        pass

    try:
        assert_clean_student_facing_texts({"page": "clean", "announcement": "study guide"})
        raise AssertionError("expected ValueError")
    except ValueError:
        pass

    assert_clean_student_facing_texts({"page": "Review your workbook."})
    print("PASS student-facing communication policy self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(command_self_test())
