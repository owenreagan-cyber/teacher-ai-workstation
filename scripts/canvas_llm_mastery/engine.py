#!/usr/bin/env python3
"""Mastery computation (pure functions — no network, no I/O).

Implements the OWNER_POLICY mastery threshold (score > 85%) and the provisional
absence / status model on top of the read-only grade data already modeled by
``scripts.canvas_llm_grade_check.reader`` and classified by
``scripts.canvas_llm_grade_check.config``.

Key rules (OWNER_POLICY, locked):
- mastery = score > 85 (exclusive); 85 and below is NOT mastery; use exact value.
- Missing grade alone is NOT absence. Absence requires an authoritative source.
- Provisional absence temporarily counts as mastery until a score appears.
- Once a score appears for a provisional student: NEEDS_UPDATE -> CONFIRMED.
- Normal homework/classwork is never treated as an assessment just because the
  score is low. Ambiguous classification -> UNRESOLVED (no mastery call).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from scripts.canvas_llm_grade_check.config import (
    GradeCheckConfig,
    SubjectConfig,
)
from scripts.canvas_llm_grade_check.engine import (
    ASSESSMENT,
    NON_ASSESSMENT,
    UNRESOLVED,
    classify_assignment,
)
from scripts.canvas_llm_grade_check.reader import (
    Assignment,
    AssignmentGroup,
    Student,
    Submission,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = REPO_ROOT / "config" / "curriculum" / "canvas" / "mastery-tracker-policy-2026-2027.json"

MASTERY_THRESHOLD = 85.0  # exclusive

# Status vocabulary (OWNER_POLICY)
CONFIRMED = "CONFIRMED"
PROVISIONAL_ABSENCE = "PROVISIONAL_ABSENCE"
MISSING_GRADES = "MISSING_GRADES"
NEEDS_UPDATE = "NEEDS_UPDATE"
UNRESOLVED = "UNRESOLVED"


def load_policy() -> dict[str, Any]:
    return json.loads(POLICY_PATH.read_text(encoding="utf-8"))


def is_mastery(score: float) -> bool:
    """mastery = score > 85 (exclusive). Exact Canvas value; no rounding."""
    return score > MASTERY_THRESHOLD


def classify_mastery_eligible(
    subject: SubjectConfig,
    group_name: str | None,
    title: str,
    keywords: tuple[str, ...],
) -> str:
    """Whether an assignment participates in mastery assessment.

    Reuses the grade-check classification: canonical assessment groups win;
    title keywords only when the group is unknown. Returns 'assessment' /
    'non_assessment' / 'unresolved'.
    """
    return classify_assignment(subject, group_name, title, keywords)


@dataclass(frozen=True)
class ManualAssessmentResult:
    """A teacher-entered aggregate assessment summary (OWNER_POLICY).

    Never fabricate per-student data from these aggregate counts.
    """
    subject: str
    assessment_title: str
    date: str
    mastered_count: int
    tested_count: int
    provisional_absence_count: int = 0
    source: str = "manual_teacher_entry"
    authority: str = "OWNER_POLICY"
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "subject": self.subject,
            "assessment_title": self.assessment_title,
            "date": self.date,
            "mastered_count": self.mastered_count,
            "tested_count": self.tested_count,
            "provisional_absence_count": self.provisional_absence_count,
            "source": self.source,
            "authority": self.authority,
            "notes": self.notes,
        }

    @property
    def mastery_rate(self) -> float | None:
        denom = self.tested_count + self.provisional_absence_count
        if denom <= 0:
            return None
        return round((self.mastered_count + self.provisional_absence_count) / denom * 100, 2)


@dataclass
class StudentMasteryState:
    """Per-student mastery result for one assessment."""
    student_id: int
    score: float | None = None
    has_grade: bool = False
    absent: bool = False
    status: str = CONFIRMED
    mastery: bool | None = None


@dataclass
class AssessmentMastery:
    """Mastery roll-up for one assessment."""
    course_name: str
    course_id: int
    assessment_title: str
    assessment_group: str | None
    due_at: str | None
    total_expected: int
    scores_present: int
    mastery_count: int = 0
    non_mastery_count: int = 0
    provisional_absences: int = 0
    missing_grades: int = 0
    unresolved: int = 0
    status: str = CONFIRMED
    student_states: list[StudentMasteryState] = field(default_factory=list)

    @property
    def tested_or_provisional_denominator(self) -> int:
        """Denominator = scores_present + provisional_absences (explicit)."""
        return self.scores_present + self.provisional_absences

    @property
    def mastery_rate(self) -> float | None:
        denom = self.tested_or_provisional_denominator
        if denom <= 0:
            return None
        return round((self.mastery_count + self.provisional_absences) / denom * 100, 2)


def evaluate_assessment_mastery(
    *,
    subject: SubjectConfig,
    assignment: Assignment,
    group_name: str | None,
    students: list[Student],
    submissions: list[Submission],
    absence_user_ids: set[int],
    keywords: tuple[str, ...],
) -> AssessmentMastery:
    """Compute the mastery roll-up for one verified assessment assignment.

    Only classified-assessment assignments should be passed here (caller gates).
    Absence is supplied as an authoritative set of user IDs (never inferred).
    """
    student_by_id = {s.user_id: s for s in students}
    sub_by_user = {s.user_id: s for s in submissions if s.assignment_id == assignment.id}

    states: list[StudentMasteryState] = []
    mastery = 0
    non_mastery = 0
    provisional = 0
    missing = 0
    unresolved = 0
    scores_present = 0

    # Students with submissions or authoritative absence.
    involved_ids = set(sub_by_user.keys()) | (absence_user_ids & set(student_by_id.keys()))

    for uid in sorted(involved_ids):
        student = student_by_id.get(uid)
        if student is None:
            continue
        sub = sub_by_user.get(uid)
        absent = uid in absence_user_ids

        if sub is not None and sub.score is not None:
            scores_present += 1
            st = StudentMasteryState(
                student_id=uid, score=sub.score, has_grade=True, absent=absent,
                status=CONFIRMED, mastery=is_mastery(sub.score),
            )
            if st.mastery:
                mastery += 1
            else:
                non_mastery += 1
        elif absent:
            # Authoritative absence, no score yet: provisional mastery.
            provisional += 1
            st = StudentMasteryState(
                student_id=uid, score=None, has_grade=False, absent=True,
                status=PROVISIONAL_ABSENCE, mastery=True,
            )
        else:
            # No score and no authoritative absence: missing grade.
            missing += 1
            st = StudentMasteryState(
                student_id=uid, score=None, has_grade=False, absent=False,
                status=MISSING_GRADES, mastery=None,
            )
        states.append(st)

    if unresolved > 0:
        status = UNRESOLVED
    elif provisional > 0:
        status = PROVISIONAL_ABSENCE
    elif missing > 0:
        status = MISSING_GRADES
    else:
        status = CONFIRMED

    return AssessmentMastery(
        course_name=subject.display_name,
        course_id=subject.course_id,
        assessment_title=assignment.name,
        assessment_group=group_name,
        due_at=assignment.due_at,
        total_expected=len(involved_ids),
        scores_present=scores_present,
        mastery_count=mastery,
        non_mastery_count=non_mastery,
        provisional_absences=provisional,
        missing_grades=missing,
        unresolved=unresolved,
        status=status,
        student_states=states,
    )


def command_self_test() -> int:
    # Threshold boundary (exclusive > 85).
    assert is_mastery(100) is True
    assert is_mastery(90) is True
    assert is_mastery(85.4) is True
    assert is_mastery(85) is False
    assert is_mastery(84.99) is False
    assert is_mastery(70) is False

    # Manual result mastery_rate.
    m = ManualAssessmentResult("language-arts", "Shurley Chapter 5 Test", "2026-10-01",
                               mastered_count=20, tested_count=20)
    assert m.mastery_rate == 100.0
    m2 = ManualAssessmentResult("math", "Written Assessment 6", "2026-10-20",
                                mastered_count=16, tested_count=20, provisional_absence_count=2)
    assert m2.mastery_rate == round((16 + 2) / 22 * 100, 2)

    policy = load_policy()
    assert policy["masteryThresholdExclusive"] == 85
    assert policy["provisionalAbsenceCountsAsMastery"] is True
    assert policy["missingGradeDoesNotEqualAbsence"] is True
    assert policy["emailRecipient"] == "owen.reagan@thalesacademy.org"
    assert policy["teacherOnly"] is True

    # evaluate_assessment_mastery with synthetic data.
    subject = SubjectConfig(key="math", display_name="Math", course_id=26404,
                            assessment_groups=("Written Assessments",), non_assessment_groups=("Homework/Class Work",))
    assignment = Assignment(id=1, name="SM5: Written Assessment 6", due_at="2026-10-20T03:59:00Z")
    students = [Student(user_id=1, name="A"), Student(user_id=2, name="B"),
                Student(user_id=3, name="C"), Student(user_id=4, name="D")]
    submissions = [
        Submission(id=1, user_id=1, assignment_id=1, score=92),
        Submission(id=2, user_id=2, assignment_id=1, score=70),
        Submission(id=3, user_id=3, assignment_id=1, score=None, grade=""),
    ]
    # Student 4 absent (authoritative), student 3 missing grade.
    rollup = evaluate_assessment_mastery(
        subject=subject, assignment=assignment, group_name="Written Assessments",
        students=students, submissions=submissions, absence_user_ids={4},
        keywords=("test",),
    )
    assert rollup.scores_present == 2
    assert rollup.mastery_count == 1  # student 1 (92)
    assert rollup.non_mastery_count == 1  # student 2 (70)
    assert rollup.provisional_absences == 1  # student 4
    assert rollup.missing_grades == 1  # student 3
    assert rollup.tested_or_provisional_denominator == 3  # 2 scored + 1 provisional
    assert rollup.mastery_rate == round((1 + 1) / 3 * 100, 2)  # (mastery + provisional)/3

    print("PASS mastery engine self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(command_self_test())
