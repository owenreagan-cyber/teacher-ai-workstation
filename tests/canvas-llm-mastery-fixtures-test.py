#!/usr/bin/env python3
"""Deterministic mastery + grade-check fixtures (synthetic only, no real data).

Covers the OWNER_POLICY boundary cases for the mastery threshold, provisional
absence, missing grades, flag one-time/persistent behavior, and ambiguous
classification. No real student data.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.canvas_llm_grade_check import config, engine as gc_engine, reader  # noqa: E402
from scripts.canvas_llm_mastery import engine as mastery  # noqa: E402


def check(name: str, cond: bool) -> None:
    print(f"{'PASS' if cond else 'FAIL'}  {name}")
    if not cond:
        raise SystemExit(f"FAILED: {name}")


def main() -> int:
    # --- Mastery threshold (exclusive > 85) ---
    check("score 100 -> mastery", mastery.is_mastery(100) is True)
    check("score 90 -> mastery", mastery.is_mastery(90) is True)
    check("score 85.4 -> mastery", mastery.is_mastery(85.4) is True)
    check("score 85 -> NOT mastery", mastery.is_mastery(85) is False)
    check("score 84.99 -> NOT mastery", mastery.is_mastery(84.99) is False)

    # --- Missing grade vs absence ---
    subject = config.SubjectConfig(key="math", display_name="Math", course_id=26404,
                                   assessment_groups=("Written Assessments",),
                                   non_assessment_groups=("Homework/Class Work",))
    assignment = mastery.Assignment(id=1, name="SM5: Written Assessment 6")
    students = [reader.Student(user_id=i, name=f"S{i}") for i in range(1, 4)]

    # missing grade + no absence -> MISSING_GRADES
    subs_missing = [reader.Submission(id=1, user_id=1, assignment_id=1, score=88),
                    reader.Submission(id=2, user_id=2, assignment_id=1, score=None, grade=""),
                    reader.Submission(id=3, user_id=3, assignment_id=1, score=None, grade="")]
    r = mastery.evaluate_assessment_mastery(subject=subject, assignment=assignment,
                                            group_name="Written Assessments", students=students,
                                            submissions=subs_missing, absence_user_ids=set(),
                                            keywords=("test",))
    check("missing grade + no absence -> MISSING_GRADES", r.missing_grades == 2 and r.status == mastery.MISSING_GRADES)

    # missing grade + explicit absence -> PROVISIONAL_ABSENCE
    r2 = mastery.evaluate_assessment_mastery(subject=subject, assignment=assignment,
                                             group_name="Written Assessments", students=students,
                                             submissions=subs_missing, absence_user_ids={3},
                                             keywords=("test",))
    st_absent = next(s for s in r2.student_states if s.student_id == 3)
    check("missing grade + absence -> PROVISIONAL_ABSENCE (per student)", st_absent.status == mastery.PROVISIONAL_ABSENCE and st_absent.mastery is True)
    check("rollup reflects provisional absence", r2.provisional_absences == 1 and r2.status == mastery.PROVISIONAL_ABSENCE)

    # provisional absence later receives 92 -> CONFIRMED mastery
    subs_update = [reader.Submission(id=1, user_id=1, assignment_id=1, score=88),
                   reader.Submission(id=2, user_id=2, assignment_id=1, score=None, grade=""),
                   reader.Submission(id=3, user_id=3, assignment_id=1, score=92)]
    r3 = mastery.evaluate_assessment_mastery(subject=subject, assignment=assignment,
                                             group_name="Written Assessments", students=students,
                                             submissions=subs_update, absence_user_ids=set(),
                                             keywords=("test",))
    st3 = next(s for s in r3.student_states if s.student_id == 3)
    check("provisional absence later 92 -> CONFIRMED mastery", st3.status == mastery.CONFIRMED and st3.mastery is True)

    # provisional absence later receives 70 -> CONFIRMED non-mastery
    subs_update2 = [reader.Submission(id=1, user_id=1, assignment_id=1, score=88),
                    reader.Submission(id=2, user_id=2, assignment_id=1, score=None, grade=""),
                    reader.Submission(id=3, user_id=3, assignment_id=1, score=70)]
    r4 = mastery.evaluate_assessment_mastery(subject=subject, assignment=assignment,
                                             group_name="Written Assessments", students=students,
                                             submissions=subs_update2, absence_user_ids=set(),
                                             keywords=("test",))
    st4 = next(s for s in r4.student_states if s.student_id == 3)
    check("provisional absence later 70 -> CONFIRMED non-mastery", st4.status == mastery.CONFIRMED and st4.mastery is False)

    # --- Flag identity: low assessment one-time ---
    k1 = gc_engine.low_assessment_key(26404, 1, 10)
    k2 = gc_engine.low_assessment_key(26404, 1, 10)
    check("low assessment flag stable identity", k1 == k2)

    # --- Missing assignment persists then resolves/reactivates (reconcile) ---
    mk = gc_engine.missing_key(26404, 1, 20)
    prev_active = {mk: gc_engine.Flag(key=mk, flag_type=gc_engine.MISSING_ASSIGNMENT, course_id=26404,
                                      course_name="Math", student_id=1, student_name="S1", first_name="S1")}
    # present -> still active
    rec = gc_engine.reconcile(prev_active, {mk: prev_active[mk]}, [], set())
    check("missing assignment persists", len(rec.still_active) == 1)
    # absent -> resolved
    rec2 = gc_engine.reconcile(prev_active, {}, [], set())
    check("missing assignment resolves", len(rec2.resolved) == 1)
    # reappears -> new
    rec3 = gc_engine.reconcile({}, {mk: prev_active[mk]}, [], set())
    check("missing assignment reactivates", len(rec3.new) == 1)

    # --- Low average persists then resolves (reconcile) ---
    ak = gc_engine.low_average_key(26404, 1)
    f_avg = gc_engine.Flag(key=ak, flag_type=gc_engine.LOW_COURSE_AVERAGE, course_id=26404,
                           course_name="Math", student_id=1, student_name="S1", first_name="S1")
    rec4 = gc_engine.reconcile({ak: f_avg}, {}, [], set())
    check("low average resolves", len(rec4.resolved) == 1)
    rec5 = gc_engine.reconcile({}, {ak: f_avg}, [], set())
    check("low average reactivates", len(rec5.new) == 1)

    # --- Ambiguous classification -> unresolved ---
    subj_unknown = config.SubjectConfig(key="science", display_name="Science", course_id=28166,
                                        assessment_groups=(), non_assessment_groups=())
    cls = mastery.classify_mastery_eligible(subj_unknown, "Assignments", "Ramp Lab", ("test",))
    check("ambiguous assignment -> UNRESOLVED", cls == "unresolved")

    # --- Homework low score -> no LOW_ASSESSMENT_SCORE ---
    cls_hw = gc_engine.classify_assignment(subject, "Homework/Class Work", "SM5: Lesson 26 Homework", ("test",))
    check("homework 70 -> NON_ASSESSMENT (no low-assessment flag)", cls_hw == gc_engine.NON_ASSESSMENT)

    print("\nSummary: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
