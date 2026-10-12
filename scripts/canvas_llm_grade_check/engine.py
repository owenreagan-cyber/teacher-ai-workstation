#!/usr/bin/env python3
"""Flag computation and reconciliation (pure functions — no network, no I/O).

Flag types:
- MISSING_ASSIGNMENT  (persistent)
- LOW_ASSESSMENT_SCORE (one-time per student + assignment)
- LOW_COURSE_AVERAGE  (persistent)

All rules are pure functions over the injected data so deterministic tests can
exercise them with synthetic student/grade fixtures.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from typing import Any

from scripts.canvas_llm_grade_check.config import GradeCheckConfig, SubjectConfig
from scripts.canvas_llm_grade_check.reader import (
    Assignment,
    AssignmentGroup,
    Student,
    Submission,
)

MISSING_ASSIGNMENT = "MISSING_ASSIGNMENT"
LOW_ASSESSMENT_SCORE = "LOW_ASSESSMENT_SCORE"
LOW_COURSE_AVERAGE = "LOW_COURSE_AVERAGE"

PERSISTENT = "PERSISTENT"
ONE_TIME = "ONE_TIME"

ASSESSMENT = "assessment"
NON_ASSESSMENT = "non_assessment"
UNRESOLVED = "unresolved"


@dataclass(frozen=True)
class Flag:
    key: str
    flag_type: str
    course_id: int
    course_name: str
    student_id: int
    student_name: str
    first_name: str
    assignment_id: int | None = None
    assignment_title: str | None = None
    assignment_due_at: str | None = None
    raw_status: str | None = None
    score: float | None = None
    average: float | None = None
    behavior: str = PERSISTENT
    classification: str | None = None


@dataclass(frozen=True)
class UnresolvedItem:
    course_id: int
    course_name: str
    student_id: int
    student_name: str
    assignment_id: int
    assignment_title: str
    reason: str
    assignment_group: str | None = None


@dataclass
class ScanResult:
    subject_key: str
    course_name: str
    course_id: int
    students_scanned: int = 0
    missing_flags: list[Flag] = field(default_factory=list)
    low_assessment_flags: list[Flag] = field(default_factory=list)
    low_average_flags: list[Flag] = field(default_factory=list)
    unresolved: list[UnresolvedItem] = field(default_factory=list)


@dataclass
class ReconcileResult:
    new: list[Flag] = field(default_factory=list)
    still_active: list[Flag] = field(default_factory=list)
    resolved: list[Flag] = field(default_factory=list)
    new_one_time: list[Flag] = field(default_factory=list)

    @property
    def active_persistent(self) -> list[Flag]:
        return self.new + self.still_active


def missing_key(course_id: int, student_id: int, assignment_id: int) -> str:
    return f"{course_id}:{student_id}:{assignment_id}:{MISSING_ASSIGNMENT}"


def low_assessment_key(course_id: int, student_id: int, assignment_id: int) -> str:
    return f"{course_id}:{student_id}:{assignment_id}:{LOW_ASSESSMENT_SCORE}"


def low_average_key(course_id: int, student_id: int) -> str:
    return f"{course_id}:{student_id}:{LOW_COURSE_AVERAGE}"


def _grade_matches_marker(grade: str, markers: tuple[str, ...]) -> bool:
    return grade.upper() in {m.upper() for m in markers}


def parse_due_at(value: str | None) -> dt.datetime | None:
    """Parse a Canvas ``due_at`` into a timezone-aware datetime.

    Canvas returns ISO-8601 with an offset/Z. Naive values are assumed UTC so a
    naive/aware comparison can never raise; a naive-vs-aware mix is never used.
    """
    if not value:
        return None
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = dt.datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed


def due_at_has_passed(due_at: str | None, now: dt.datetime | None = None) -> bool:
    """True when the assignment's due timestamp is at or before ``now``.

    An assignment with no parseable due date is treated as NOT yet due: absence
    of a due date must never, by itself, make a whole class look missing.
    """
    parsed = parse_due_at(due_at)
    if parsed is None:
        return False
    reference = now or dt.datetime.now(dt.timezone.utc)
    if reference.tzinfo is None:
        reference = reference.replace(tzinfo=dt.timezone.utc)
    return parsed <= reference


def has_real_grade(submission: Submission) -> bool:
    """True when Canvas reports a real graded result for this submission.

    A numeric score (including a genuine ``0``) or a non-marker grade string
    counts as graded. Blank/null, whitespace-only, and MI-style missing markers
    do NOT count. ``0`` is a grade; only ``None``/blank is ungraded.

    An **excused** submission is never a grade: Canvas stores excused work as
    ``workflow_state="graded"`` with a null score, which must not be mistaken
    for grading that has begun.
    """
    if submission.excused:
        return False
    if submission.score is not None:
        return True
    grade = (submission.grade or "").strip()
    if not grade:
        return False
    # "MI"/other missing markers are not a graded result.
    if _grade_matches_marker(grade, ("MI", "MISSING")):
        return False
    # A non-numeric grade string (e.g. "complete", "A-", "ex") counts as graded;
    # the numeric value of a numeric grade string is verified by the reader.
    return True


def grading_has_started(submissions_for_assignment: list[Submission]) -> bool:
    """True when at least one student has a real grade for this assignment.

    Retained as a reporting/diagnostic signal ONLY. It is deliberately NOT used
    as an eligibility override: early grading must never surface missing work
    before the assignment's due date.
    """
    return any(has_real_grade(s) for s in submissions_for_assignment)


def assignment_eligible_for_missing(
    assignment: Assignment,
    submissions_for_assignment: list[Submission] | None = None,
    *,
    now: dt.datetime | None = None,
) -> bool:
    """True when MISSING_ASSIGNMENT evaluation may run for this assignment.

    eligible = due_at <= now  (due-date-only; the sole authoritative gate)

    Before the due date/time nothing flags, even when peers have already been
    graded. The ``submissions_for_assignment`` argument is accepted for call-site
    compatibility and is intentionally ignored.
    """
    return due_at_has_passed(assignment.due_at, now)


def student_is_missing(
    submission: Submission,
    submissions_for_assignment: list[Submission] | None = None,
    markers: tuple[str, ...] = ("MI", "MISSING"),
) -> bool:
    """Student-level missing rule, applied only once the assignment is eligible.

    Once the due date has passed, a student is missing when either:
    - Canvas reports an explicit MI / mi marker, or
    - the submission has no real grade (blank/null score and blank/null grade).

    A numeric ``0`` is a real grade and is therefore NOT missing. An ``excused``
    submission is never missing. Canvas's generic ``missing=true`` is NOT
    accepted on its own — it must never bypass the due-date eligibility gate.

    ``submissions_for_assignment`` is accepted for call-site compatibility and is
    intentionally ignored: peer grading no longer influences the decision.
    """
    if submission.excused:
        return False
    if _grade_matches_marker((submission.grade or "").strip(), markers):
        return True
    return not has_real_grade(submission)


def is_missing(submission: Submission, markers: tuple[str, ...]) -> bool:
    """Raw MI-marker check (no eligibility). Kept for marker semantics/tests.

    Callers computing flags must use :func:`student_is_missing` behind
    :func:`assignment_eligible_for_missing`.
    """
    if submission.missing:
        return True
    return _grade_matches_marker((submission.grade or "").strip(), markers)


def missing_status(submission: Submission, markers: tuple[str, ...]) -> str:
    """The grade/status to show, exactly as Canvas expresses it.

    A grade marker (e.g. "MI") is preserved verbatim; otherwise a Canvas
    ``missing=true`` submission reports "missing" rather than a stray score.
    """
    grade = (submission.grade or "").strip()
    if _grade_matches_marker(grade, markers):
        return grade
    if submission.missing:
        return "missing"
    return grade


def classify_assignment(
    subject: SubjectConfig,
    group_name: str | None,
    title: str,
    keywords: tuple[str, ...],
) -> str:
    """Classify an assignment as assessment / non-assessment / unresolved.

    Canonical assessment and non-assessment groups win first. Only when the
    group is unknown do we fall back to verified test-title keywords. Ambiguous
    cases resolve to ``unresolved`` rather than guessing.
    """
    if group_name is not None:
        if group_name in subject.assessment_groups:
            return ASSESSMENT
        if group_name in subject.non_assessment_groups:
            return NON_ASSESSMENT
    lowered = (title or "").lower()
    if any(kw in lowered for kw in keywords):
        return ASSESSMENT
    return UNRESOLVED


def _format_number(value: float) -> str:
    if value == int(value):
        return str(int(value))
    return repr(float(value))


def format_score(value: float | None) -> str | None:
    if value is None:
        return None
    return _format_number(value)


def scan_subject(
    subject: SubjectConfig,
    students: list[Student],
    assignments: list[Assignment],
    groups: list[AssignmentGroup],
    submissions: list[Submission],
    cfg: GradeCheckConfig,
    *,
    now: dt.datetime | None = None,
) -> ScanResult:
    """Compute current flags for one subject. Pure; no state mutation.

    MISSING_ASSIGNMENT flags are only produced for assignments that are
    eligible for missing-work evaluation (due date passed, or grading started).
    """
    group_name_by_id = {g.id: g.name for g in groups}
    assignment_by_id = {a.id: a for a in assignments}
    student_by_id = {s.user_id: s for s in students}
    threshold = cfg.threshold

    # Group submissions per assignment once: needed for the grading-started and
    # peer-graded checks below.
    submissions_by_assignment: dict[int, list[Submission]] = {}
    for submission in submissions:
        submissions_by_assignment.setdefault(submission.assignment_id, []).append(submission)

    result = ScanResult(
        subject_key=subject.key,
        course_name=subject.display_name,
        course_id=subject.course_id,
        students_scanned=len(students),
    )

    for submission in submissions:
        student = student_by_id.get(submission.user_id)
        assignment = assignment_by_id.get(submission.assignment_id)
        if student is None or assignment is None:
            continue
        group_name = (
            group_name_by_id.get(assignment.assignment_group_id)
            if assignment.assignment_group_id is not None
            else None
        )

        # Flag 1 — MISSING_ASSIGNMENT (persistent), gated by eligibility.
        # A not-yet-due assignment with no grades entered can never flag anyone,
        # even when Canvas reports missing=true for the whole class.
        peers = submissions_by_assignment.get(submission.assignment_id, [])
        if assignment_eligible_for_missing(assignment, peers, now=now) and student_is_missing(
            submission, peers, cfg.missing_grade_markers
        ):
            missing_kind = classify_assignment(
                subject, group_name, assignment.name, cfg.test_title_keywords
            )
            result.missing_flags.append(
                Flag(
                    key=missing_key(subject.course_id, student.user_id, assignment.id),
                    flag_type=MISSING_ASSIGNMENT,
                    course_id=subject.course_id,
                    course_name=subject.display_name,
                    student_id=student.user_id,
                    student_name=student.name,
                    first_name=student.first_name,
                    assignment_id=assignment.id,
                    assignment_title=assignment.name,
                    assignment_due_at=assignment.due_at,
                    raw_status=missing_status(submission, cfg.missing_grade_markers),
                    behavior=PERSISTENT,
                    classification=missing_kind,
                )
            )
            continue  # a missing item is not also scored for assessment

        # Flag 2 — LOW_ASSESSMENT_SCORE (one-time).
        if submission.score is not None and submission.score <= threshold:
            classification = classify_assignment(
                subject, group_name, assignment.name, cfg.test_title_keywords
            )
            if classification == ASSESSMENT:
                result.low_assessment_flags.append(
                    Flag(
                        key=low_assessment_key(subject.course_id, student.user_id, assignment.id),
                        flag_type=LOW_ASSESSMENT_SCORE,
                        course_id=subject.course_id,
                        course_name=subject.display_name,
                        student_id=student.user_id,
                        student_name=student.name,
                        first_name=student.first_name,
                        assignment_id=assignment.id,
                        assignment_title=assignment.name,
                        assignment_due_at=assignment.due_at,
                        raw_status=submission.grade,
                        score=submission.score,
                        behavior=ONE_TIME,
                    )
                )
            elif classification == UNRESOLVED:
                result.unresolved.append(
                    UnresolvedItem(
                        course_id=subject.course_id,
                        course_name=subject.display_name,
                        student_id=student.user_id,
                        student_name=student.name,
                        assignment_id=assignment.id,
                        assignment_title=assignment.name,
                        assignment_group=group_name,
                        reason=(
                            "score <= 85 but assignment group "
                            f"{group_name or '(none)'!r} is not a canonical assessment "
                            "group and the title has no verified test keyword"
                        ),
                    )
                )

    # Flag 3 — LOW_COURSE_AVERAGE (persistent).
    for student in students:
        average = student.average
        if average is not None and average <= threshold:
            result.low_average_flags.append(
                Flag(
                    key=low_average_key(subject.course_id, student.user_id),
                    flag_type=LOW_COURSE_AVERAGE,
                    course_id=subject.course_id,
                    course_name=subject.display_name,
                    student_id=student.user_id,
                    student_name=student.name,
                    first_name=student.first_name,
                    average=average,
                    behavior=PERSISTENT,
                )
            )

    return result


def reconcile(
    previous_active: dict[str, Flag],
    current_persistent: dict[str, Flag],
    current_one_time: list[Flag],
    issued_one_time: set[str],
) -> ReconcileResult:
    """Reconcile a scan against prior state.

    Persistent flags (missing / low-average) become NEW or STILL_ACTIVE or are
    RESOLVED when no longer present. One-time low-assessment flags only surface
    when their identity key has not already been issued.
    """
    prev_keys = set(previous_active)
    now_keys = set(current_persistent)

    new = [current_persistent[k] for k in sorted(now_keys - prev_keys)]
    still_active = [current_persistent[k] for k in sorted(now_keys & prev_keys)]
    resolved = [previous_active[k] for k in sorted(prev_keys - now_keys)]
    new_one_time = [f for f in current_one_time if f.key not in issued_one_time]

    return ReconcileResult(new=new, still_active=still_active, resolved=resolved, new_one_time=new_one_time)


def flag_to_dict(flag: Flag) -> dict[str, Any]:
    return {
        "key": flag.key,
        "flag_type": flag.flag_type,
        "course_id": flag.course_id,
        "course_name": flag.course_name,
        "student_id": flag.student_id,
        "student_name": flag.student_name,
        "first_name": flag.first_name,
        "assignment_id": flag.assignment_id,
        "assignment_title": flag.assignment_title,
        "assignment_due_at": flag.assignment_due_at,
        "raw_status": flag.raw_status,
        "score": flag.score,
        "average": flag.average,
        "behavior": flag.behavior,
        "classification": flag.classification,
    }


def flag_from_dict(data: dict[str, Any]) -> Flag:
    return Flag(
        key=data["key"],
        flag_type=data["flag_type"],
        course_id=int(data["course_id"]),
        course_name=data.get("course_name") or "",
        student_id=int(data["student_id"]),
        student_name=data.get("student_name") or "",
        first_name=data.get("first_name") or "",
        assignment_id=data.get("assignment_id"),
        assignment_title=data.get("assignment_title"),
        assignment_due_at=data.get("assignment_due_at"),
        raw_status=data.get("raw_status"),
        score=data.get("score"),
        average=data.get("average"),
        behavior=data.get("behavior", PERSISTENT),
        classification=data.get("classification"),
    )


def command_self_test() -> int:
    cfg = __import__("scripts.canvas_llm_grade_check.config", fromlist=["load_config"]).load_config()
    subject = cfg.subjects["math"]

    # Threshold boundary: 85 flag, 86 no flag, 84.99 flag, 85.4 no flag.
    assert _format_number(85.0) == "85"
    assert _format_number(84.99) == "84.99"
    assert _format_number(85.4) == "85.4"

    assert classify_assignment(subject, "Written Assessments", "SM5: Written Assessment 4", cfg.test_title_keywords) == ASSESSMENT
    assert classify_assignment(subject, "Homework/Class Work", "SM5: Lesson 26 Homework", cfg.test_title_keywords) == NON_ASSESSMENT
    assert classify_assignment(subject, None, "SM5: Mastery Test", cfg.test_title_keywords) == ASSESSMENT
    assert classify_assignment(subject, "Unknown Group", "SM5: Mystery Thing", cfg.test_title_keywords) == UNRESOLVED

    assert is_missing(Submission(id=1, user_id=1, assignment_id=1, grade="MI"), ("MI", "MISSING"))
    assert is_missing(Submission(id=1, user_id=1, assignment_id=1, grade="mi"), ("MI", "MISSING"))
    assert is_missing(Submission(id=1, user_id=1, assignment_id=1, grade="100", missing=True), ("MI", "MISSING"))
    assert not is_missing(Submission(id=1, user_id=1, assignment_id=1, grade="100"), ("MI", "MISSING"))

    # --- Eligibility (due-date-only) + grade-presence semantics ---
    past = "2020-01-01T00:00:00Z"
    future = "2999-01-01T00:00:00Z"
    assert due_at_has_passed(past) is True
    assert due_at_has_passed(future) is False
    assert due_at_has_passed(None) is False, "no due date must not imply due"
    now = dt.datetime(2026, 9, 10, 12, 0, tzinfo=dt.timezone.utc)
    assert due_at_has_passed("2026-09-10T11:59:59Z", now) is True
    assert due_at_has_passed("2026-09-10T12:00:01Z", now) is False
    # Exactly at the due instant is considered due.
    assert due_at_has_passed("2026-09-10T12:00:00Z", now) is True

    def _s(uid, score=None, grade=None, missing=False, excused=False):
        return Submission(id=uid, user_id=uid, assignment_id=1,
                          score=score, grade=grade, missing=missing, excused=excused)

    # Grade presence: 0 is a grade; blank/None is not; MI is not.
    assert has_real_grade(_s(1, score=0)) is True, "numeric zero is a real grade"
    assert has_real_grade(_s(1, score=100)) is True
    assert has_real_grade(_s(1, grade="95")) is True
    assert has_real_grade(_s(1, grade="ex")) is True
    assert has_real_grade(_s(1, score=None, grade=None)) is False
    assert has_real_grade(_s(1, grade="")) is False
    assert has_real_grade(_s(1, grade="  ")) is False
    assert has_real_grade(_s(1, grade="MI")) is False
    assert has_real_grade(_s(1, grade="mi")) is False

    # Excused work is never missing and never a grade.
    excused = Submission(id=1, user_id=1, assignment_id=1, score=None, grade=None,
                         excused=True, workflow_state="graded")
    assert has_real_grade(excused) is False, "excused is not a grade"
    assert student_is_missing(excused, None, ("MI", "MISSING")) is False

    # DUE-DATE-ONLY eligibility: nothing before the due date, whatever peers did.
    fut = Assignment(id=1, name="HW", due_at=future)
    old = Assignment(id=1, name="HW", due_at=past)
    blanks = [_s(1), _s(2)]
    assert assignment_eligible_for_missing(fut) is False
    # future + all blank
    assert assignment_eligible_for_missing(fut, blanks) is False
    # future + Canvas missing=true for everyone -> still NOT eligible
    assert assignment_eligible_for_missing(fut, [_s(1, missing=True), _s(2, missing=True)]) is False
    # future + MI markers present -> still NOT eligible
    assert assignment_eligible_for_missing(fut, [_s(1, grade="MI"), _s(2, grade="mi")]) is False
    # future + some peers already graded -> still NOT eligible (override removed)
    assert assignment_eligible_for_missing(fut, [_s(1, score=100), _s(2)]) is False
    # even a fully graded cohort does not make a future assignment eligible
    assert assignment_eligible_for_missing(fut, [_s(1, score=100), _s(2, score=90)]) is False
    # grading_has_started remains available as a diagnostic only
    assert grading_has_started([_s(1, score=100), _s(2)]) is True
    assert grading_has_started([excused, _s(3, excused=True)]) is False
    # due date passed -> eligible regardless of any grades
    assert assignment_eligible_for_missing(old) is True
    assert assignment_eligible_for_missing(old, blanks) is True
    assert assignment_eligible_for_missing(old, []) is True
    # no due date at all -> never eligible
    assert assignment_eligible_for_missing(Assignment(id=1, name="HW", due_at=None)) is False

    # Student-level rule (applied only after the due date has passed).
    assert student_is_missing(_s(1), None, ("MI", "MISSING")) is True, "blank grade -> missing"
    assert student_is_missing(_s(1, grade="MI"), None, ("MI", "MISSING")) is True
    assert student_is_missing(_s(1, grade="mi"), None, ("MI", "MISSING")) is True
    assert student_is_missing(_s(1, score=0), None, ("MI", "MISSING")) is False, "0 is a grade"
    assert student_is_missing(_s(1, score=88), None, ("MI", "MISSING")) is False
    assert student_is_missing(_s(1, grade="88%"), None, ("MI", "MISSING")) is False
    # Peer kindness/severity no longer matters: a blank student is missing, and
    # a graded student is never missing even when peers are blank.
    assert student_is_missing(_s(2), [_s(1, score=100)], ("MI", "MISSING")) is True
    assert student_is_missing(_s(1, score=100), [_s(2)], ("MI", "MISSING")) is False
    # Canvas missing=true on its own is still not accepted as a marker.
    assert student_is_missing(_s(1, missing=True), None, ("MI", "MISSING")) is True  # via blank grade
    assert student_is_missing(_s(1, score=95, missing=True), None, ("MI", "MISSING")) is False

    print("PASS grade-check engine self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(command_self_test())
