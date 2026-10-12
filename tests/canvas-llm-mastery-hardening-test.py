#!/usr/bin/env python3
"""Deterministic mastery + grade-check + absence + privacy fixtures (synthetic only).

Covers: absence override lifecycle (ABSENT/CLEAR), GET-count instrumentation,
submission-content data minimization, email preview payload, no-send default,
and manual-aggregate no-student-flags. No real student data.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.canvas_llm_grade_check import config, engine as gc_engine, reader  # noqa: E402
from scripts.canvas_llm_mastery import absence, counting, engine as mastery  # noqa: E402


def check(name: str, cond: bool) -> None:
    print(f"{'PASS' if cond else 'FAIL'}  {name}")
    if not cond:
        raise SystemExit(f"FAILED: {name}")


def main() -> int:
    # --- Absence override lifecycle ---
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "abs.json"

        # ABSENT + missing score -> provisional mastery.
        absence.add_absence(course_id=26442, student_id=12345, assignment_id=1045694,
                            effective_date="2026-10-16", path=p)
        check("ABSENT override recorded", absence.absence_user_ids_for_assignment(1045694, path=p) == {12345})

        # duplicate ABSENT is idempotent.
        absence.add_absence(course_id=26442, student_id=12345, assignment_id=1045694,
                            effective_date="2026-10-16", path=p)
        check("duplicate ABSENT idempotent", len(absence.list_absences(path=p)) == 1)

        # audit history preserved.
        hist_before = len(absence.load_store(p)["history"])
        check("audit history recorded", hist_before >= 2)

        # CLEAR removes active override, retains history.
        clr = absence.clear_absence(course_id=26442, student_id=12345, assignment_id=1045694, path=p)
        check("CLEAR resolves override", clr["cleared"] is True)
        check("CLEAR removes from active", absence.absence_user_ids_for_assignment(1045694, path=p) == set())
        check("CLEAR retains audit history", len(absence.load_store(p)["history"]) == hist_before + 1)

        # CLEAR on non-existent -> no-op.
        check("CLEAR non-existent is no-op", absence.clear_absence(course_id=26442, student_id=99999, assignment_id=1, path=p)["cleared"] is False)

    # --- GET-count instrumentation ---
    class Stub(reader.GradeReader):
        def list_students(self, c): return []
        def list_assignments(self, c): return []
        def list_assignment_groups(self, c): return []
        def list_submissions(self, c): return []

    cr = counting.CountingReader(Stub())
    cr.list_students(1); cr.list_assignments(1); cr.list_assignment_groups(1); cr.list_submissions(1)
    check("GET counter increments", cr.network.get == 4)
    check("zero-write network summary", cr.network.post == 0 and cr.network.put == 0 and cr.network.patch == 0 and cr.network.delete == 0)
    check("endpoint families recorded", len(cr.network.endpoint_families) == 4)

    # --- Data minimization: forbidden fields never persisted ---
    # The reader's Submission dataclass holds only minimal fields. Verify by
    # constructing from a rich raw dict and confirming body/comments/url are absent.
    rich_raw = {
        "id": 1, "user_id": 1, "assignment_id": 1, "score": 88.0, "grade": "88",
        "missing": False, "late": False, "excused": False, "workflow_state": "graded",
        "preview_url": "https://school/canvas/preview/1",
        "body": "student essay text",
        "submission_comments": [{"comment": "nice work"}],
        "attachments": [{"url": "https://school/files/1"}],
        "rubric_assessment": {"points": 10},
        "user": {"name": "Real Student"},
    }
    sub = reader.Submission(
        id=rich_raw["id"], user_id=rich_raw["user_id"], assignment_id=rich_raw["assignment_id"],
        score=rich_raw["score"], grade=rich_raw["grade"], missing=rich_raw["missing"],
        late=rich_raw["late"], excused=rich_raw["excused"], workflow_state=rich_raw["workflow_state"],
    )
    serialized = json.dumps(sub.__dict__)
    for forbidden in ("body", "essay", "comment", "attachment", "preview_url", "rubric", "file"):
        check(f"forbidden field '{forbidden}' not retained", forbidden not in serialized.lower())

    # --- Email preview payload exact ---
    from scripts.canvas_llm_mastery import cli as mastery_cli
    subject = config.SubjectConfig(key="math", display_name="Math", course_id=26404,
                                   assessment_groups=("Written Assessments",), non_assessment_groups=("Homework/Class Work",))
    assignment = reader.Assignment(id=1, name="SM5: Written Assessment 6")
    students = [reader.Student(user_id=i, name=f"S{i}") for i in range(1, 4)]
    subs = [reader.Submission(id=1, user_id=1, assignment_id=1, score=92),
            reader.Submission(id=2, user_id=2, assignment_id=1, score=70),
            reader.Submission(id=3, user_id=3, assignment_id=1, score=None, grade="")]
    rollup = mastery.evaluate_assessment_mastery(subject=subject, assignment=assignment,
                                                group_name="Written Assessments", students=students,
                                                submissions=subs, absence_user_ids={3}, keywords=("test",))
    rep = mastery_cli.MasteryReport(quarter=1, assessment_rows=[rollup])
    body = mastery_cli.render_email_body(rep)
    check("email body has teacher-only subject", "4A Grade Check - Student Flags" in body)
    check("email body separates confirmed vs provisional", "Confirmed mastery: 1" in body and "Provisional absence mastery: 1" in body)
    check("email body has all 7 sections", all(f"{i}. " in body for i in range(1, 8)))

    # --- Manual aggregate produces no student-level flags ---
    manual = mastery.ManualAssessmentResult("Language Arts", "Shurley Chapter 5 Test", "2026-10-01", 20, 20)
    check("manual aggregate has no student identities", "student_id" not in manual.to_dict())
    check("manual aggregate marked manual_teacher_entry", manual.to_dict()["source"] == "manual_teacher_entry")

    print("\nSummary: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
