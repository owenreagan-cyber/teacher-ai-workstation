#!/usr/bin/env python3
"""Copy/paste parent message templates.

These are produced for the teacher to review and copy. They are NEVER sent
automatically. Wording follows the owner-approved template exactly; the child's
first name, actual assignment/assessment name, and actual score/average are
substituted. No material is invented.
"""
from __future__ import annotations

import re

from scripts.canvas_llm_grade_check.engine import (
    ASSESSMENT,
    NON_ASSESSMENT,
    format_score,
)

_LESSON_RE = re.compile(r"\bLesson\s+(\d+)\b", re.IGNORECASE)


def extract_lesson(assignment_title: str | None) -> str | None:
    """Return 'Lesson N' only when a single lesson number is reliably present."""
    if not assignment_title:
        return None
    matches = _LESSON_RE.findall(assignment_title)
    if len(matches) == 1:
        return f"Lesson {matches[0]}"
    return None


def _missing_homework_message(first_name: str, assignment_title: str | None) -> str:
    lesson = extract_lesson(assignment_title)
    if lesson:
        return (
            "Good afternoon,\n\n"
            f"Your child, {first_name}, is currently missing the homework assignment "
            f"for {lesson}.\n\n"
            f"Please have {first_name} complete the missing assignment and return it "
            "to school as soon as possible.\n\n"
            "Thank you for your help and support!\n\n"
            "Best,\n"
            "Owen Reagan"
        )
    return (
        "Good afternoon,\n\n"
        f"I wanted to let you know that {first_name} is currently missing the homework "
        f"assignment for {assignment_title or 'the current assignment'}.\n\n"
        f"Please have {first_name} complete the missing assignment and return it "
        "to school as soon as possible.\n\n"
        "Thank you for your help and support!\n\n"
        "Best,\n"
        "Owen Reagan"
    )


def _missing_assessment_message(first_name: str, assessment_name: str | None) -> str:
    return (
        "Good afternoon,\n\n"
        f"I wanted to let you know that {first_name} is currently missing "
        f"{assessment_name or 'the assessment'}.\n\n"
        f"Please have {first_name} complete the missing assessment as soon as "
        "possible.\n\n"
        "Thank you for your help and support!\n\n"
        "Best,\n"
        "Owen Reagan"
    )


def _missing_neutral_message(first_name: str, assignment_name: str | None) -> str:
    return (
        "Good afternoon,\n\n"
        f"I wanted to let you know that {first_name} is currently missing "
        f"{assignment_name or 'the assignment'}.\n\n"
        f"Please have {first_name} complete the missing assignment as soon as "
        "possible.\n\n"
        "Thank you for your help and support!\n\n"
        "Best,\n"
        "Owen Reagan"
    )


def missing_parent_message(
    first_name: str,
    assignment_title: str | None,
    classification: str | None = None,
) -> str:
    """Type-aware missing-item template.

    - homework/classwork (NON_ASSESSMENT) -> homework wording
    - test/assessment/checkout (ASSESSMENT) -> assessment wording
    - unresolved/unknown -> neutral fallback (no guessed type)
    """
    if classification == NON_ASSESSMENT:
        return _missing_homework_message(first_name, assignment_title)
    if classification == ASSESSMENT:
        return _missing_assessment_message(first_name, assignment_title)
    return _missing_neutral_message(first_name, assignment_title)


def low_assessment_parent_message(
    first_name: str, assessment_name: str | None, score: float | None
) -> str:
    score_label = format_score(score) or "the recorded score"
    return (
        "Good afternoon,\n\n"
        f"I wanted to let you know that {first_name} scored an {score_label} on "
        f"{assessment_name or 'the assessment'}.\n\n"
        "Showing mastery is receiving above an 85 on the assessment. Please review "
        f"the material with {first_name} so they can continue strengthening their "
        "understanding of the skills and concepts covered.\n\n"
        "Thank you for your continued support!\n\n"
        "Best,\n"
        "Owen Reagan"
    )


def low_average_parent_message(
    first_name: str, course_name: str, average: float | None
) -> str:
    average_label = format_score(average) or "the recorded average"
    return (
        "Good afternoon,\n\n"
        f"I wanted to make you aware that {first_name}'s current average in "
        f"{course_name} is {average_label}.\n\n"
        "An average above 85 demonstrates the level of mastery we are working toward. "
        f"Please continue reviewing classwork, homework, and assessment material with "
        f"{first_name} and encourage them to ask for help whenever something is "
        "unclear.\n\n"
        "Thank you for your continued support!\n\n"
        "Best,\n"
        "Owen Reagan"
    )


def parent_message_for(flag) -> str:
    """Dispatch to the correct template based on flag type."""
    from scripts.canvas_llm_grade_check import engine

    if flag.flag_type == engine.MISSING_ASSIGNMENT:
        return missing_parent_message(
            flag.first_name, flag.assignment_title, flag.classification
        )
    if flag.flag_type == engine.LOW_ASSESSMENT_SCORE:
        return low_assessment_parent_message(flag.first_name, flag.assignment_title, flag.score)
    if flag.flag_type == engine.LOW_COURSE_AVERAGE:
        return low_average_parent_message(flag.first_name, flag.course_name, flag.average)
    return ""


def command_self_test() -> int:
    from scripts.canvas_llm_grade_check import engine

    assert extract_lesson("SM5: Lesson 26 Homework") == "Lesson 26"
    assert extract_lesson("RM4: Lesson 31 Workbook and Comprehension") == "Lesson 31"
    assert extract_lesson("Reading Test & Fluency Checkout") is None
    assert extract_lesson("Lessons 21-30 Review") is None  # range is not a single lesson

    # Homework/classwork -> homework wording (with lesson extraction).
    msg = missing_parent_message("Student", "SM5: Lesson 26 Homework", engine.NON_ASSESSMENT)
    assert "Your child, Student, is currently missing the homework assignment for Lesson 26." in msg
    assert "Owen Reagan" in msg

    msg2 = missing_parent_message("Student", "Map Project", engine.NON_ASSESSMENT)
    assert "Map Project" in msg2 and "Lesson" not in msg2
    assert "homework assignment" in msg2

    # Assessment/test/checkout -> assessment wording, never "homework".
    msg3 = missing_parent_message("Student", "RM4: Fluency Checkout 2", engine.ASSESSMENT)
    assert "is currently missing RM4: Fluency Checkout 2." in msg3
    assert "homework" not in msg3
    msg4 = missing_parent_message("Student", "Math Test 3", engine.ASSESSMENT)
    assert "is currently missing Math Test 3." in msg4
    assert "homework" not in msg4

    # Neutral fallback -> no guessed type.
    msg5 = missing_parent_message("Student", "Mystery Packet", engine.UNRESOLVED)
    assert "is currently missing Mystery Packet." in msg5
    assert "homework" not in msg5 and "assessment" not in msg5

    la = low_assessment_parent_message("Student", "SM5: Written Assessment 4", 82)
    assert "scored an 82 on SM5: Written Assessment 4" in la
    assert "failed" not in la

    la2 = low_assessment_parent_message("Student", "SM5: Fact Assessment 4", 84.99)
    assert "scored an 84.99" in la2

    avg = low_average_parent_message("Student", "Math", 80)
    assert "current average in Math is 80" in avg
    assert "missing" not in avg

    print("PASS grade-check templates self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(command_self_test())
