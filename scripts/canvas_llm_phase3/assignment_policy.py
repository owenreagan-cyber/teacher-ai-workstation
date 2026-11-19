#!/usr/bin/env python3
"""Canonical gradebook-assignment policy gate (OWNER_APPROVED_POLICY).

Source of truth:
``docs/programs/canvas-llm/weekly-canvas-production-workflow-2026-2027.json``

Owner policy (2026-11-17, superseding the 2026-11-14 tests-only restriction):
  * automatically prepare gradebook assignments for tests/assessments that the
    approved pacing and teacher-reviewed WeeklyPlan explicitly identify;
  * also automatically prepare legitimate pacing-derived Math homework, Math
    classwork, Reading workbook classwork, and Reading comprehension work;
  * every eligible assignment is 100 points, percent grading, on-paper
    submission, same instructional day 11:59 PM America/New_York, with the
    established ``omit_from_final_grade`` setting;
  * quizzes, chapter activities, worksheets, investigations, projects,
    ordinary practice, and every other subject remain agenda-only unless a
    complete structured owner approval matches the exact object;
  * preparation is not publication; teacher approval and live readback remain
    mandatory;
  * spelling keeps its fixed dual-course target set;
  * unknown or ambiguous objects fail closed.

Generic ``homework`` and ``classwork`` are still forbidden. Only the four
subject-scoped policy kinds (``math_homework``, ``math_classwork``,
``reading_homework``, ``reading_classwork``) may auto-prepare, and only in
their verified course/group.

This module never calls Canvas and performs no writes.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_PATH = (REPO_ROOT / "docs" / "programs" / "canvas-llm"
                 / "weekly-canvas-production-workflow-2026-2027.json")

AUTHORITY = "OWNER_APPROVED_POLICY"
OWNER_IDENTITY = "Owen Reagan"

# Canonical kind aliases -> policy kind.
_ALIASES = {
    "written_assessment": "written_assessment",
    "written assessment": "written_assessment",
    "writtenassessment": "written_assessment",
    "math_test": "written_assessment",
    "math test": "written_assessment",
    "fact_assessment": "fact_assessment",
    "fact assessment": "fact_assessment",
    "factassessment": "fact_assessment",
    "mastery_test": "mastery_test",
    "mastery test": "mastery_test",
    "masterytest": "mastery_test",
    "fluency_checkout": "fluency_checkout",
    "fluency checkout": "fluency_checkout",
    "fluencycheckout": "fluency_checkout",
    "spelling_test": "spelling_test",
    "spelling test": "spelling_test",
    "spellingtest": "spelling_test",
    "chapter_test": "chapter_test",
    "chapter test": "chapter_test",
    "chaptertest": "chapter_test",
    "unit_test": "unit_test",
    "unit test": "unit_test",
    "unittest": "unit_test",
    "quiz": "quiz",
    "chapter_activity": "chapter_activity",
    "chapter activity": "chapter_activity",
    "activity": "chapter_activity",
    "worksheet": "worksheet",
    "classwork": "classwork",
    "classroompractice": "classwork",
    "homework": "homework",
    "practice": "practice",
    "ordinary_practice": "practice",
    "investigation": "investigation",
    "project": "project",
    "review": "review",
    "checkup": "checkup",
    "worksheet_packet": "worksheet",
    # Internal generator kinds -> subject-scoped policy kinds.
    "homework_accuracy_grade": "math_homework",
    "math_homework": "math_homework",
    "math homework": "math_homework",
    "classwork_accuracy_grade": "math_classwork",
    "math_classwork": "math_classwork",
    "math classwork": "math_classwork",
    "reading_homework": "reading_homework",
    "reading homework": "reading_homework",
    "reading_classwork": "reading_classwork",
    "reading classwork": "reading_classwork",
}

_SCOPED_KINDS = ("math_homework", "math_classwork",
                 "reading_homework", "reading_classwork")

APPROVAL_FIELDS = (
    "owner_identity",
    "request_id",
    "course",
    "assignment_type",
    "assignment_title",
    "approval_status",
    "timestamp",
)


def normalize_kind(kind: str) -> str:
    key = (kind or "").strip().lower().replace("-", "_")
    return _ALIASES.get(key, key)


def load_workflow() -> dict[str, Any]:
    return json.loads(WORKFLOW_PATH.read_text(encoding="utf-8"))


def auto_prepare_policy() -> dict[str, Any]:
    return load_workflow()["assignmentStandard"]["autoPrepare"]


def allowed_kinds() -> list[str]:
    return list(auto_prepare_policy()["allowedKinds"])


def forbidden_kinds() -> list[str]:
    return list(auto_prepare_policy()["forbiddenKinds"])


def scoped_kinds() -> dict[str, Any]:
    return dict(auto_prepare_policy().get("scopedKinds") or {})


def scoped_kind_spec(kind: str) -> dict[str, Any] | None:
    """Return the verified course/group/archetype for a scoped kind."""
    return scoped_kinds().get(normalize_kind(kind))


def is_scoped_kind(kind: str) -> bool:
    return normalize_kind(kind) in _SCOPED_KINDS


def default_group(kind: str) -> str | None:
    """Canonical assignment group for a policy kind, when unambiguous."""
    normalized = normalize_kind(kind)
    spec = scoped_kind_spec(normalized)
    if spec:
        return spec.get("group")
    return {
        "written_assessment": "Written Assessments",
        "fact_assessment": "Fact Assessments",
        "mastery_test": "Assessments",
        "fluency_checkout": "Check Out",
        "spelling_test": "Assessments",
        "chapter_test": "Assessments",
        "unit_test": "Assignments",
    }.get(normalized)


def default_course(kind: str) -> int | None:
    spec = scoped_kind_spec(kind)
    return spec.get("courseId") if spec else None


def classify_assignment(
    *,
    kind: str | None = None,
    title: str | None = None,
    group: str | None = None,
    source_rule: str | None = None,
) -> str:
    """Classify an assignment-like object into a policy kind.

    Explicit ``kind`` wins. Otherwise the title/source rule is inspected.
    Generic homework/classwork stays generic (and therefore forbidden). Only a
    canonical subject prefix (SM5/RM4) upgrades work to a scoped kind.
    Anything unrecognized returns ``unknown`` and fails closed.
    """
    if kind:
        normalized = normalize_kind(kind)
        if normalized and normalized != "assignment":
            return normalized

    raw_title = (title or "").strip()
    title_l = raw_title.lower()
    blob = " ".join(x for x in (title or "", source_rule or "") if x).lower()

    # Tests and assessments always classify first.
    if "written assessment" in blob or "math test" in blob:
        return "written_assessment"
    if "fact assessment" in blob or "power up test" in blob:
        return "fact_assessment"
    if "mastery test" in blob or "reading test" in blob:
        return "mastery_test"
    if "fluency checkout" in blob or "fluency check" in blob or "check out" in blob:
        return "fluency_checkout"
    if "spelling test" in blob:
        return "spelling_test"
    if "unit test" in blob:
        return "unit_test"
    if "chapter" in blob and "test" in blob:
        return "chapter_test"
    if "quiz" in blob:
        return "quiz"
    if "investigation" in blob:
        return "investigation"
    if "project" in blob:
        return "project"

    # Subject-scoped pacing work requires the canonical course prefix.
    if re.match(r"^sm5\s*:", title_l):
        if "classwork" in title_l:
            return "math_classwork"
        if "homework" in title_l:
            return "math_homework"
    if re.match(r"^rm4\s*:", title_l):
        if "comprehension" in title_l:
            return "reading_homework"
        if "workbook" in title_l:
            return "reading_classwork"

    # Generic work stays generic and remains forbidden.
    if "worksheet" in blob:
        return "worksheet"
    if "classwork" in blob or "workbook" in blob or "comprehension" in blob \
            or "classroom practice" in blob or "practice" in blob:
        return "classwork"
    if "homework" in blob or (group or "").lower() in {"homework", "homework/class work"}:
        return "homework"
    if "review" in blob:
        return "review"
    if "checkup" in blob:
        return "checkup"
    if "activity" in blob:
        return "chapter_activity"
    return "unknown"


_READING_LESSON_RE = re.compile(
    r"^rm4:\s*(?:(?P<weekday>monday|tuesday|wednesday|thursday|friday)\s+)?"
    r"(?P<role>workbook classwork|workbook and comprehension|workbook|comprehension questions)"
    r"(?:\s*[-\u2014]\s*lesson\s+(?P<n1>\d+)|\s+lesson\s+(?P<n2>\d+))?$",
    re.IGNORECASE,
)
_READING_LEGACY_LESSON_RE = re.compile(
    r"^rm4:\s*lesson\s+(?P<n>\d+)\s+(?P<role>workbook and comprehension|workbook)$",
    re.IGNORECASE,
)
_MATH_LESSON_RE = re.compile(
    r"^sm5:\s*(?:(?P<weekday>monday|tuesday|wednesday|thursday|friday)\s+)?"
    r"(?P<role>homework|classwork)"
    r"(?:\s*[-\u2014]\s*lesson\s+(?P<n1>\d+)|\s+lesson\s+(?P<n2>\d+))?$",
    re.IGNORECASE,
)
_MATH_CANONICAL_LESSON_RE = re.compile(
    r"^sm5:\s*lesson\s+(?P<n>\d+)\s+(?P<role>homework|classwork)$",
    re.IGNORECASE,
)
_MATH_WRITTEN_RE = re.compile(
    r"^sm5:\s*(?:written assessment|math test)\s+(?P<n>\d+)$", re.IGNORECASE)
_MATH_FACT_RE = re.compile(
    r"^sm5:\s*fact assessment\s+(?P<n>\d+)$", re.IGNORECASE)
_READING_MASTERY_RE = re.compile(
    r"^rm4:\s*(?:reading\s+)?mastery test\s+(?P<n>\d+)$", re.IGNORECASE)
_READING_CHECKOUT_RE = re.compile(
    r"^rm4:\s*(?:fluency\s+)?(?:checkout|check out)\s+(?P<n>\d+)$", re.IGNORECASE)
_SPELLING_RE = re.compile(
    r"^(?P<prefix>rm4|ela4a):\s*spelling test\s+(?P<n>\d+)"
    r"(?:\s*[-\u2014]\s*(?P<suffix>assessment|announcement))?$",
    re.IGNORECASE,
)


def semantic_identity(title: str | None) -> tuple[str, int] | None:
    """Return ``(family, number)`` for safe duplicate-candidate matching.

    The family deliberately groups legacy and canonical title forms of the same
    assignment so reconciliation can surface a semantic duplicate instead of
    silently POSTing a second object or renaming an existing one.
    """
    text = " ".join((title or "").strip().split())
    match = _READING_LEGACY_LESSON_RE.match(text)
    if match:
        role = match.group("role").lower()
        family = "reading_homework" if "comprehension" in role else "reading_classwork"
        return family, int(match.group("n"))
    match = _READING_LESSON_RE.match(text)
    if match and (match.group("n1") or match.group("n2")):
        role = match.group("role").lower()
        family = "reading_homework" if "comprehension" in role else "reading_classwork"
        return family, int(match.group("n1") or match.group("n2"))
    match = _MATH_CANONICAL_LESSON_RE.match(text) or _MATH_LESSON_RE.match(text)
    if match and (match.groupdict().get("n1") or match.groupdict().get("n2")
                  or match.groupdict().get("n")):
        family = ("math_classwork" if match.group("role").lower() == "classwork"
                  else "math_homework")
        number = (match.groupdict().get("n") or match.groupdict().get("n1")
                  or match.groupdict().get("n2"))
        return family, int(number)
    for pattern, family in (
        (_MATH_WRITTEN_RE, "written_assessment"),
        (_MATH_FACT_RE, "fact_assessment"),
        (_READING_MASTERY_RE, "mastery_test"),
        (_READING_CHECKOUT_RE, "fluency_checkout"),
    ):
        match = pattern.match(text)
        if match:
            return family, int(match.group("n"))
    match = _SPELLING_RE.match(text)
    if match:
        suffix = (match.group("suffix") or "assessment").lower()
        family = ("spelling_announcement" if suffix == "announcement"
                  else "spelling_test")
        return family, int(match.group("n"))
    return None


def semantic_match(
    proposed_title: str | None,
    existing_titles: Iterable[str],
) -> list[str]:
    """Return existing titles that share a semantic identity with the proposal."""
    identity = semantic_identity(proposed_title)
    if identity is None:
        return []
    return [title for title in existing_titles if semantic_identity(title) == identity]


def _norm_course(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def _parse_timestamp(value: Any) -> datetime | None:
    if not value or not isinstance(value, str):
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def validate_owner_override(
    approval: dict[str, Any] | None,
    proposed: dict[str, Any] | None,
) -> tuple[bool, list[str]]:
    """Validate a structured owner approval against the proposed assignment.

    Fails closed on missing fields, wrong owner, wrong course, wrong title or
    type, revoked status, and expiry.
    """
    errors: list[str] = []
    if not isinstance(approval, dict):
        return False, ["approval record missing"]
    for field in APPROVAL_FIELDS:
        if not str(approval.get(field) or "").strip():
            errors.append(f"missing field: {field}")

    if str(approval.get("approval_status") or "").strip().upper() != "APPROVED":
        errors.append("approval_status is not APPROVED")
    if str(approval.get("owner_identity") or "").strip() != OWNER_IDENTITY:
        errors.append("owner_identity mismatch")

    proposed = proposed or {}
    if _norm_course(approval.get("course")) != _norm_course(proposed.get("course")):
        errors.append("course mismatch")
    if str(approval.get("assignment_title") or "").strip() != str(proposed.get("title") or "").strip():
        errors.append("assignment_title mismatch")

    proposed_kind = normalize_kind(proposed.get("kind") or "")
    approval_type = normalize_kind(approval.get("assignment_type") or "")
    if proposed_kind and approval_type != proposed_kind:
        errors.append("assignment_type mismatch")

    approved_at = _parse_timestamp(approval.get("timestamp"))
    if approved_at is None:
        errors.append("timestamp is not a valid ISO timestamp")
    elif approved_at > datetime.now(timezone.utc):
        errors.append("timestamp is in the future")

    revoked_at = _parse_timestamp(approval.get("revoked_at"))
    if approval.get("revoked_at") and revoked_at is None:
        errors.append("revoked_at is not a valid ISO timestamp")
    if revoked_at is not None:
        errors.append("approval revoked")

    expires_at = _parse_timestamp(approval.get("expires_at"))
    if approval.get("expires_at") and expires_at is None:
        errors.append("expires_at is not a valid ISO timestamp")
    if expires_at is not None and expires_at <= datetime.now(timezone.utc):
        errors.append("approval expired")

    return (not errors), errors


def auto_prepare_allowed(
    kind: str,
    *,
    course: Any = None,
    group: str | None = None,
    approval: dict[str, Any] | None = None,
    proposed: dict[str, Any] | None = None,
) -> bool:
    """Return True for an auto-prepare kind or a valid owner override.

    Scoped kinds are verified against the canonical course and assignment
    group when the caller supplies them. A mismatched course or group fails
    closed even when the kind name is allowed.
    """
    normalized = normalize_kind(kind)
    if normalized in _SCOPED_KINDS:
        spec = scoped_kind_spec(normalized)
        if not spec:
            return False
        if course is not None and _norm_course(course) != _norm_course(spec.get("courseId")):
            return False
        if group not in (None, "") and str(group) != str(spec.get("group")):
            return False
        return True
    if normalized in allowed_kinds():
        return True
    if approval is None:
        return False
    ok, _errors = validate_owner_override(approval, proposed or {"kind": normalized})
    return ok


def _submission_types(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    return list(value or [])


def validate_assignment_settings(item: dict[str, Any]) -> list[str]:
    """Return violations of the universal assignment invariants.

    Missing optional fields are tolerated so planning objects can be filtered
    before normalization. Any present field must match exactly.
    """
    violations: list[str] = []
    if "points_possible" in item and item.get("points_possible") not in (100, 100.0):
        violations.append("points_possible must be 100")
    if "grading_type" in item and str(item.get("grading_type") or "").lower() != "percent":
        violations.append("grading_type must be percent")
    if "submission_types" in item and "on_paper" not in _submission_types(item.get("submission_types")):
        violations.append("submission_types must include on_paper")
    if "omit_from_final_grade" in item and bool(item.get("omit_from_final_grade")) is not False:
        violations.append("omit_from_final_grade must be false")
    if "due_time" in item and str(item.get("due_time") or "") not in ("23:59", "11:59 PM"):
        violations.append("due_time must be 23:59 / 11:59 PM")
    if "timezone" in item and str(item.get("timezone") or "") != "America/New_York":
        violations.append("timezone must be America/New_York")
    if "due_date" in item and not str(item.get("due_date") or "").strip():
        violations.append("due_date is required")
    return violations


def plan_gradebook_assignments(items: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Filter WeeklyPlan items down to the gradebook objects policy permits.

    Each item may carry ``kind``/``assignment_type``, a ``title``, and its
    verified ``course``/``course_id`` + ``assignment_group``/``group``. A
    forbidden or unknown item is kept only when a complete matching approval
    record is present under ``approval``. Fully specified items must also pass
    the universal 100-point/percent/on-paper invariants.
    """
    planned: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        kind = (item.get("kind") or item.get("assignment_type")
                or classify_assignment(title=item.get("title"), group=item.get("group")))
        course = item.get("course") if item.get("course") is not None else item.get("course_id")
        group = item.get("assignment_group") or item.get("group")
        if not auto_prepare_allowed(kind, course=course, group=group,
                                    approval=item.get("approval"), proposed=item):
            continue
        if validate_assignment_settings(item):
            continue
        planned.append(item)
    return planned


def spelling_targets(n: int) -> dict[str, Any]:
    """Return the canonical dual-course Spelling Test object set."""
    if not isinstance(n, int) or n <= 0:
        raise ValueError("spelling test number must be a positive integer")
    policy = auto_prepare_policy()["spellingDualCourse"]
    rs = policy["readingSpelling"]
    la = policy["languageArts"]
    return {
        "readingSpelling": {
            "courseId": rs["courseId"],
            "assessment": {
                "title": rs["assessmentTitle"].format(N=n),
                "group": rs["assessmentGroup"],
                "gradebook": True,
            },
            "announcement": {
                "title": rs["announcementTitle"].format(N=n),
                "gradebook": False,
            },
        },
        "languageArts": {
            "courseId": la["courseId"],
            "assessment": {
                "title": la["assessmentTitle"].format(N=n),
                "group": la["assessmentGroup"],
                "gradebook": True,
            },
            "announcement": None,
        },
        "authority": AUTHORITY,
    }


def _self_test_approval(**overrides: Any) -> dict[str, Any]:
    base = {
        "owner_identity": OWNER_IDENTITY,
        "request_id": "REQ-TEST-1",
        "course": 26404,
        "assignment_type": "project",
        "assignment_title": "SM5: Lesson 99 Project",
        "approval_status": "APPROVED",
        "timestamp": "2026-11-17T12:00:00Z",
    }
    base.update(overrides)
    return base


def command_self_test() -> int:
    policy = auto_prepare_policy()
    assert policy["authority"] == AUTHORITY
    assert policy["decidedAt"] == "2026-11-17"
    for kind in allowed_kinds():
        assert auto_prepare_allowed(kind) is True, kind
    for kind in forbidden_kinds():
        assert auto_prepare_allowed(kind) is False, kind
    assert auto_prepare_allowed("bogus_kind") is False

    # Scoped kinds verify course and group when supplied.
    assert auto_prepare_allowed("math_homework", course=26404, group="Homework/Class Work") is True
    assert auto_prepare_allowed("math_homework", course=26442, group="Homework/Class Work") is False
    assert auto_prepare_allowed("math_homework", course=26404, group="Homework") is False
    assert auto_prepare_allowed("reading_classwork", course=26442, group="Homework") is True
    assert auto_prepare_allowed("reading_classwork", course=26404, group="Homework") is False
    assert auto_prepare_allowed("homework", course=26404, group="Homework/Class Work") is False
    assert auto_prepare_allowed("classwork", course=26442, group="Homework") is False

    # Classification of canonical and internal kinds.
    assert classify_assignment(title="SM5: Lesson 49 Homework") == "math_homework"
    assert classify_assignment(title="SM5: Lesson 50 Classwork") == "math_classwork"
    assert classify_assignment(kind="homework_accuracy_grade") == "math_homework"
    assert classify_assignment(kind="classwork_accuracy_grade") == "math_classwork"
    assert classify_assignment(title="RM4: Monday Workbook Classwork — Lesson 59") == "reading_classwork"
    assert classify_assignment(title="RM4: Tuesday Comprehension Questions — Lesson 60") == "reading_homework"
    assert classify_assignment(kind="reading_homework") == "reading_homework"
    assert classify_assignment(kind="reading_classwork") == "reading_classwork"
    assert classify_assignment(title="Classroom Practice 27") == "classwork"
    assert classify_assignment(title="SCI4: Chapter 4 Quiz") == "quiz"
    assert classify_assignment(title="Investigation 5") == "investigation"
    assert classify_assignment(title="MATH THNK") == "unknown"

    # Semantic identity groups weekday variants without guessing meaning.
    assert semantic_identity("RM4: Tuesday Comprehension Questions — Lesson 60") == \
        ("reading_homework", 60)
    assert semantic_identity("RM4: Thursday Comprehension Questions — Lesson 60") == \
        ("reading_homework", 60)
    assert semantic_identity("RM4: Lesson 60 Workbook and Comprehension") == \
        ("reading_homework", 60)
    assert semantic_identity("RM4: Mastery Test 6") == ("mastery_test", 6)
    assert semantic_identity("MATH THNK") is None
    assert semantic_match("RM4: Tuesday Comprehension Questions — Lesson 60",
                          ["RM4: Thursday Comprehension Questions — Lesson 60"]) == \
        ["RM4: Thursday Comprehension Questions — Lesson 60"]

    proposed = {"course": 26404, "kind": "project",
                "title": "SM5: Lesson 99 Project"}
    assert auto_prepare_allowed("project") is False
    assert auto_prepare_allowed("project", approval=_self_test_approval(), proposed=proposed) is True
    assert auto_prepare_allowed("project", approval=_self_test_approval(course=99999),
                                proposed=proposed) is False
    assert auto_prepare_allowed("project", approval=_self_test_approval(assignment_title="Other"),
                                proposed=proposed) is False
    assert auto_prepare_allowed("project", approval=_self_test_approval(approval_status="PENDING"),
                                proposed=proposed) is False
    assert auto_prepare_allowed("project", approval=_self_test_approval(revoked_at="2026-11-17T13:00:00Z"),
                                proposed=proposed) is False
    assert auto_prepare_allowed("project", approval=_self_test_approval(expires_at="2020-01-01T00:00:00Z"),
                                proposed=proposed) is False

    planned = plan_gradebook_assignments([
        {"kind": "homework"},
        {"kind": "classwork"},
        {"kind": "quiz"},
        {"kind": "investigation"},
        {"kind": "project"},
        {"kind": "worksheet"},
        {"kind": "chapter_activity"},
        {"kind": "written_assessment"},
        {"kind": "mastery_test"},
        {"kind": "math_homework"},
        {"kind": "math_classwork"},
        {"kind": "reading_homework"},
        {"kind": "reading_classwork"},
    ])
    assert [p["kind"] for p in planned] == [
        "written_assessment", "mastery_test", "math_homework", "math_classwork",
        "reading_homework", "reading_classwork",
    ]

    # Settings invariants fail closed when specified.
    assert validate_assignment_settings({"points_possible": 100, "grading_type": "percent",
                                        "submission_types": "on_paper",
                                        "omit_from_final_grade": False,
                                        "due_time": "23:59",
                                        "timezone": "America/New_York",
                                        "due_date": "2026-11-16"}) == []
    assert validate_assignment_settings({"points_possible": 50})
    assert validate_assignment_settings({"grading_type": "pass_fail"})
    assert validate_assignment_settings({"submission_types": ["none"]})
    assert validate_assignment_settings({"omit_from_final_grade": True})

    targets = spelling_targets(9)
    assert targets["readingSpelling"]["assessment"]["title"] == \
        "RM4: Spelling Test 9 - Assessment"
    assert targets["readingSpelling"]["announcement"]["title"] == \
        "RM4: Spelling Test 9 - Announcement"
    assert targets["languageArts"]["assessment"]["title"] == \
        "ELA4A Spelling Test 9 - Assessment"
    assert targets["languageArts"]["announcement"] is None

    print("PASS assignment policy gate self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(command_self_test())
