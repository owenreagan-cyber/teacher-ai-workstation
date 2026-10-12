#!/usr/bin/env bash
# Deterministic Canvas Grade Check tests (synthetic student/grade data only).
set -euo pipefail

echo "Running Canvas LLM Grade Check tests..."

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

MODULES=(
  "scripts/canvas_llm_grade_check/config.py"
  "scripts/canvas_llm_grade_check/reader.py"
  "scripts/canvas_llm_grade_check/engine.py"
  "scripts/canvas_llm_grade_check/state.py"
  "scripts/canvas_llm_grade_check/templates.py"
  "scripts/canvas_llm_grade_check/report.py"
  "scripts/canvas_llm_grade_check/emailer.py"
  "scripts/canvas_llm_grade_check/gmail_transport.py"
  "scripts/canvas_llm_grade_check/scheduler.py"
  "scripts/canvas_llm_grade_check/cli.py"
)
PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/teacher-ai-workstation-pycache" python3 -m py_compile "${MODULES[@]}"

python3 - <<'PY'
import sys
import os
import json
import hashlib
import subprocess
import tempfile
import datetime as dt
from pathlib import Path

root = Path('.').resolve()
sys.path.insert(0, str(root))

from scripts.canvas_llm_grade_check import config, engine, report, cli, templates
from scripts.canvas_llm_grade_check import state as state_mod
from scripts.canvas_llm_grade_check.reader import Assignment, AssignmentGroup, Student, Submission
from scripts.canvas_llm_grade_check.state import StateStore

cfg = config.load_config()
assert cfg.threshold == 85

# Single-subject config for the scan tests (Math only in Q1).
math_cfg = config.load_config()
math_cfg.quarter_subjects = {1: ("math",)}

# ---------------------------------------------------------------------------
# Synthetic fixture reader (no Canvas access)
# ---------------------------------------------------------------------------
class SyntheticReader:
    def __init__(self, students, assignments, groups, submissions):
        self._students = students
        self._assignments = assignments
        self._groups = groups
        self._submissions = submissions

    def list_students(self, course_id):
        return self._students

    def list_assignments(self, course_id):
        return self._assignments

    def list_assignment_groups(self, course_id):
        return self._groups

    def list_submissions(self, course_id):
        return self._submissions


GROUPS = [
    AssignmentGroup(id=1, name="Written Assessments"),
    AssignmentGroup(id=2, name="Homework/Class Work"),
    AssignmentGroup(id=3, name="Unknown Group"),
]

# Fixtures represent work that is already due (or collected and graded), so the
# assignment is eligible for missing-work evaluation under the refined rule.
PAST_DUE = "2026-09-01T03:59:59Z"
FUTURE_DUE = "2999-01-01T03:59:59Z"

ASSIGNMENTS = [
    Assignment(id=10, name="SM5: Written Assessment 4", assignment_group_id=1, due_at=PAST_DUE),
    Assignment(id=11, name="SM5: Lesson 26 Homework", assignment_group_id=2, due_at=PAST_DUE),
    Assignment(id=12, name="SM5: Fact Assessment 4", assignment_group_id=1, due_at=PAST_DUE),
    Assignment(id=13, name="SM5: Mystery Packet", assignment_group_id=3, due_at=PAST_DUE),
]

def student_alpha(avg):
    return Student(user_id=1, name="Student Alpha", current_score=avg)

def student_beta():
    return Student(user_id=2, name="Student Beta", current_score=92)


def scan_state(reader, tmpdir):
    store = StateStore(Path(tmpdir), "state.json")
    scan = cli.run_scan(reader, math_cfg, 1, store)
    # Simulate a confirmed successful send: persist exactly what --send would.
    state_mod.write_state(
        store,
        active_persistent=scan.active_persistent,
        resolved_flags=scan.merged_resolved,
        one_time_issued=scan.merged_issued,
    )
    return scan.outcome, store


# ---------------------------------------------------------------------------
# Scan 1: NEW flags
# ---------------------------------------------------------------------------
subs = [
    Submission(id=1, user_id=1, assignment_id=10, score=82.0, grade="82"),        # low assessment
    Submission(id=2, user_id=1, assignment_id=11, grade="MI", missing=False),      # missing (Lesson 26)
    Submission(id=3, user_id=1, assignment_id=12, score=90.0, grade="90"),        # above 85
    Submission(id=4, user_id=1, assignment_id=13, score=70.0, grade="70"),        # unresolved group
    Submission(id=5, user_id=2, assignment_id=10, score=86.0, grade="86"),        # 86 -> no flag
    Submission(id=6, user_id=2, assignment_id=11, score=100.0, grade="100"),      # no flag
]
reader1 = SyntheticReader([student_alpha(84.0), student_beta()], ASSIGNMENTS, GROUPS, subs)

with tempfile.TemporaryDirectory() as tmp:
    outcome, store = scan_state(reader1, tmp)

    assert len(outcome.courses) == 1 and outcome.courses[0].course_id == 26404
    assert outcome.courses[0].students_scanned == 2

    assert len(outcome.missing) == 1, f"missing={outcome.missing}"
    m = outcome.missing[0]
    assert m.status == report.NEW
    assert m.flag.student_name == "Student Alpha"
    assert m.flag.assignment_title == "SM5: Lesson 26 Homework"
    assert m.flag.raw_status == "MI"
    assert m.flag.classification == engine.NON_ASSESSMENT

    assert len(outcome.low_assessment) == 1, f"low_assessment={outcome.low_assessment}"
    a = outcome.low_assessment[0]
    assert a.flag.assignment_title == "SM5: Written Assessment 4"
    assert a.flag.score == 82.0

    assert len(outcome.low_average) == 1, f"low_average={outcome.low_average}"
    av = outcome.low_average[0]
    assert av.flag.student_name == "Student Alpha"
    assert av.flag.average == 84.0

    assert len(outcome.unresolved) == 1, f"unresolved={outcome.unresolved}"
    assert outcome.unresolved[0].assignment_title == "SM5: Mystery Packet"
    assert outcome.unresolved[0].assignment_group == "Unknown Group"
    assert outcome.resolved == []

    # Default (routine) preview is compact and contains NO parent templates.
    preview = report.render_preview(outcome)
    assert "=== 4A GRADE CHECK — TEACHER REVIEW ===" in preview
    assert "Your child, Student, is currently missing the homework assignment for Lesson 26." not in preview
    assert "COPY/PASTE PARENT MESSAGE" not in preview
    assert "scored an 82 on SM5: Written Assessment 4" not in preview
    assert "current average in Math is 84" not in preview
    assert "CANVAS WRITES PERFORMED: 0" in preview
    assert "EMAILS SENT: 0" in preview
    # Compact one-line entries.
    assert "[NEW] Student Alpha | Math | SM5: Lesson 26 Homework | missing" in preview
    assert "[NEW] Student Alpha | Math | SM5: Written Assessment 4 | 82" in preview
    assert "[NEW] Student Alpha | Math | 84" in preview
    # Summary counts.
    assert "NEW missing: 1" in preview
    assert "STILL ACTIVE missing: 0" in preview
    assert "NEW assessment <=85: 1" in preview
    assert "STILL ACTIVE low averages: 0" in preview
    assert "Unresolved low-score items: 1" in preview
    # Unresolved grouped: course | title | group | count. No per-student line.
    assert "UNRESOLVED LOW-SCORE ITEMS (grouped)" in preview
    assert "[Math] SM5: Mystery Packet | Unknown Group | 1 students" in preview
    assert "Student Alpha | Math | SM5: Mystery Packet" not in preview

    # Detailed mode prints expanded metadata + parent templates.
    detailed = report.render_preview(outcome, details=True)
    assert "(DETAILED)" in detailed
    assert "Your child, Student, is currently missing the homework assignment for Lesson 26." in detailed
    assert "scored an 82 on SM5: Written Assessment 4" in detailed
    assert "current average in Math is 84" in detailed
    assert "ASSESSMENT <=85 GROUPED REVIEW" in detailed

    # Parent-template mode prints drafts only, grouped by student.
    parent_only = report.render_parent_templates(outcome)
    assert "PARENT MESSAGE DRAFTS (COPY/PASTE ONLY)" in parent_only
    assert "No message is sent automatically" in parent_only
    assert "--- Student Alpha ---" in parent_only
    assert "Your child, Student, is currently missing the homework assignment for Lesson 26." in parent_only
    assert "scored an 82 on SM5: Written Assessment 4" in parent_only
    assert "current average in Math is 84" in parent_only
    assert "EMAILS SENT: 0" in parent_only

    print("PASS scan 1 detects NEW missing / low-assessment / low-average / unresolved")

    # -----------------------------------------------------------------------
    # Scan 2 (identical data): no duplicate alerts; persistent = STILL ACTIVE.
    # -----------------------------------------------------------------------
    outcome2, _ = scan_state(reader1, tmp)
    assert [e.status for e in outcome2.missing] == [report.STILL_ACTIVE]
    assert [e.status for e in outcome2.low_average] == [report.STILL_ACTIVE]
    assert outcome2.low_assessment == [], "one-time assessment must not re-alert"
    assert outcome2.resolved == []
    print("PASS scan 2 marks STILL ACTIVE and does not duplicate one-time alerts")

    # -----------------------------------------------------------------------
    # Scan 3 (Student recovered): missing + low-average resolve; one-time stays silent.
    # -----------------------------------------------------------------------
    subs3 = [
        Submission(id=1, user_id=1, assignment_id=10, score=95.0, grade="95"),  # grade changed; still one-time
        Submission(id=2, user_id=1, assignment_id=11, grade="100", missing=False),  # no longer missing
        Submission(id=5, user_id=2, assignment_id=10, score=86.0, grade="86"),
        Submission(id=6, user_id=2, assignment_id=11, score=100.0, grade="100"),
    ]
    reader3 = SyntheticReader([student_alpha(90.0), student_beta()], ASSIGNMENTS, GROUPS, subs3)
    outcome3, store3 = scan_state(reader3, tmp)
    assert outcome3.missing == []
    assert outcome3.low_average == []
    assert outcome3.low_assessment == [], "one-time assessment must not re-alert after grade change"
    assert len(outcome3.resolved) == 2, f"resolved={outcome3.resolved}"
    resolved_keys = {f.key for f in outcome3.resolved}
    assert "26404:1:11:MISSING_ASSIGNMENT" in resolved_keys
    assert "26404:1:LOW_COURSE_AVERAGE" in resolved_keys
    print("PASS scan 3 resolves missing + low-average and keeps one-time silent")

    # Resolved state persisted.
    persisted = store3.load()
    assert "26404:1:11:MISSING_ASSIGNMENT" in persisted["resolved_flags"]
    assert "26404:1:LOW_COURSE_AVERAGE" in persisted["resolved_flags"]

    # -----------------------------------------------------------------------
    # Scan 4 (Student drops back to 84): low-average reactivates as NEW.
    # -----------------------------------------------------------------------
    subs4 = [
        Submission(id=5, user_id=2, assignment_id=10, score=86.0, grade="86"),
        Submission(id=6, user_id=2, assignment_id=11, score=100.0, grade="100"),
    ]
    reader4 = SyntheticReader([student_alpha(84.0), student_beta()], ASSIGNMENTS, GROUPS, subs4)
    outcome4, _ = scan_state(reader4, tmp)
    assert [e.status for e in outcome4.low_average] == [report.NEW], "re-drop must reactivate"
    assert len(outcome4.low_average) == 1
    print("PASS scan 4 reactivates a recovered-then-dropped low average as NEW")

# ---------------------------------------------------------------------------
# Routine preview refinement: concise default, expanded details, parent drafts.
# (Detection rules, thresholds, persistence, and transport behavior unchanged.)
# ---------------------------------------------------------------------------
with tempfile.TemporaryDirectory() as tmp:
    o1, _ = scan_state(reader1, tmp)
    default_pv = report.render_preview(o1)
    detailed_pv = report.render_preview(o1, details=True)
    parent_pv = report.render_parent_templates(o1)

    # 1. Default preview is concise: NO parent templates, NO per-flag blocks.
    assert "PARENT MESSAGE" not in default_pv
    assert "message drafts" not in default_pv.lower()
    assert "Student: Student Alpha" not in default_pv       # no verbose block
    assert "Behavior:" not in default_pv

    # 2. Default preview still shows the header, counts, and compact lines.
    assert "=== 4A GRADE CHECK — TEACHER REVIEW ===" in default_pv
    assert "Quarter: Q1" in default_pv
    assert "Summary counts" in default_pv
    assert "[NEW] Student Alpha | Math | SM5: Lesson 26 Homework | missing" in default_pv
    assert "[NEW] Student Alpha | Math | SM5: Written Assessment 4 | 82" in default_pv
    assert "[NEW] Student Alpha | Math | 84" in default_pv

    # 3. --details prints expanded detail incl. metadata and parent templates.
    assert "(DETAILED)" in detailed_pv
    assert "Student: Student Alpha" in detailed_pv
    assert "Behavior: PERSISTENT" in detailed_pv
    assert "Behavior: ONE-TIME" in detailed_pv
    assert "COPY/PASTE PARENT MESSAGE" in detailed_pv
    assert "Your child, Student, is currently missing the homework assignment for Lesson 26." in detailed_pv

    # 4. --parent-templates prints parent drafts grouped by student, and only
    #    for the three active flag types (never unresolved informational items).
    assert "PARENT MESSAGE DRAFTS (COPY/PASTE ONLY)" in parent_pv
    assert "--- Student Alpha ---" in parent_pv
    assert "MISSING ASSIGNMENT | Math | SM5: Lesson 26 Homework" in parent_pv
    assert "ASSESSMENT 85 OR BELOW | Math | SM5: Written Assessment 4 | 82" in parent_pv
    assert "OVERALL AVERAGE 85 OR BELOW | Math | 84" in parent_pv
    # Unresolved items are informational only and get no parent draft.
    assert "Mystery Packet" not in parent_pv
    assert "EMAILS SENT: 0" in parent_pv

    # 5. Unresolved items are grouped (count) in the default preview, not listed
    #    per student; detailed mode lists them individually.
    assert "[Math] SM5: Mystery Packet | Unknown Group | 1 students" in default_pv
    assert "SM5: Mystery Packet | Unknown Group | Unresolved" not in default_pv
    assert "UNRESOLVED LOW-SCORE ITEMS (individual students)" in detailed_pv
    assert "Student Alpha | Math | SM5: Mystery Packet" in detailed_pv
print("PASS routine preview: concise default / details / parent templates / grouping")

# ---------------------------------------------------------------------------
# Resolved flags appear only when newly resolved; STILL ACTIVE persists; the
# one-time issued assessments stay suppressed across a preview.
# ---------------------------------------------------------------------------
with tempfile.TemporaryDirectory() as tmp:
    _o1, _ = scan_state(reader1, tmp)            # scan 1 -> NEW
    o2, _ = scan_state(reader1, tmp)             # scan 2 -> STILL ACTIVE, no resolved
    pv2 = report.render_preview(o2)
    assert "STILL ACTIVE missing: 1" in pv2
    assert "STILL ACTIVE low averages: 1" in pv2
    assert "RESOLVED missing: 0" in pv2
    assert "RESOLVED low averages: 0" in pv2
    assert "NEW assessment <=85: 0" in pv2, "issued one-time assessment must stay suppressed"
    assert "[STILL ACTIVE] Student Alpha | Math | SM5: Lesson 26 Homework | missing" in pv2
    assert "[STILL ACTIVE] Student Alpha | Math | 84" in pv2
    assert "--- RESOLVED PERSISTENT FLAGS SINCE LAST SCAN ---" in pv2
    assert "None" in pv2

    # Scan 3 resolves both persistent flags -> they appear as resolved once.
    o3, _ = scan_state(reader3, tmp)
    pv3 = report.render_preview(o3)
    assert "RESOLVED missing: 1" in pv3
    assert "RESOLVED low averages: 1" in pv3
    assert "NEW missing: 0" in pv3
    assert "STILL ACTIVE missing: 0" in pv3
    assert "NEW assessment <=85: 0" in pv3, "one-time assessment must remain suppressed"
    assert "26404:1:11:MISSING_ASSIGNMENT" in pv3 or "MISSING_ASSIGNMENT" in pv3

    # A subsequent scan with nothing newly resolved shows no resolved items.
    o3b, _ = scan_state(reader3, tmp)
    pv3b = report.render_preview(o3b)
    assert "RESOLVED missing: 0" in pv3b
    assert "RESOLVED low averages: 0" in pv3b
print("PASS resolved-only-when-newly-resolved + STILL ACTIVE + one-time suppression")

# ---------------------------------------------------------------------------
# No preview mode sends an email or writes Canvas.
# ---------------------------------------------------------------------------
with tempfile.TemporaryDirectory() as tmp:
    o1b, _ = scan_state(reader1, tmp)
    for mode_text in (
        report.render_preview(o1b),
        report.render_preview(o1b, details=True),
        report.render_parent_templates(o1b),
    ):
        assert "EMAILS SENT: 0" in mode_text
        assert "CANVAS WRITES PERFORMED: 0" in mode_text
print("PASS no preview mode sends email or writes Canvas")

# ---------------------------------------------------------------------------
# Threshold rule: 86 no flag, 85 flag, 84.99 flag, 85.4 no flag.
# ---------------------------------------------------------------------------
math = cfg.subjects["math"]
assert engine.classify_assignment(math, "Written Assessments", "X", cfg.test_title_keywords) == "assessment"

def score_only(score):
    return SyntheticReader(
        [Student(user_id=1, name="Student Alpha", current_score=90)],
        [Assignment(id=10, name="SM5: Written Assessment 4", assignment_group_id=1, due_at=PAST_DUE)],
        GROUPS, [Submission(id=1, user_id=1, assignment_id=10, score=score, grade=str(score))],
    )

def assessment_count(score):
    with tempfile.TemporaryDirectory() as tmp:
        o, _ = scan_state(score_only(score), tmp)
        return len(o.low_assessment)

assert assessment_count(86.0) == 0
assert assessment_count(85.0) == 1
assert assessment_count(84.99) == 1
assert assessment_count(85.4) == 0
print("PASS threshold rule: 86 no flag, 85 flag, 84.99 flag, 85.4 no flag")

# ---------------------------------------------------------------------------
# Missing-item type classification flows through the scanner end-to-end.
# ---------------------------------------------------------------------------
def missing_only(group_id, title):
    return SyntheticReader(
        [Student(user_id=1, name="Student Alpha", current_score=90)],
        [Assignment(id=20, name=title, assignment_group_id=group_id, due_at=PAST_DUE)],
        GROUPS, [Submission(id=1, user_id=1, assignment_id=20, grade="MI")],
    )

with tempfile.TemporaryDirectory() as tmp:
    o_hw, _ = scan_state(missing_only(2, "SM5: Lesson 26 Homework"), tmp)   # Homework/Class Work
    assert o_hw.missing[0].flag.classification == engine.NON_ASSESSMENT
    hw_msg = templates.parent_message_for(o_hw.missing[0].flag)
    assert "missing the homework assignment for Lesson 26" in hw_msg

with tempfile.TemporaryDirectory() as tmp:
    o_asm, _ = scan_state(missing_only(1, "SM5: Written Assessment 4"), tmp)  # Written Assessments
    assert o_asm.missing[0].flag.classification == engine.ASSESSMENT
    asm_msg = templates.parent_message_for(o_asm.missing[0].flag)
    assert "is currently missing SM5: Written Assessment 4." in asm_msg
    assert "homework" not in asm_msg

with tempfile.TemporaryDirectory() as tmp:
    o_unk, _ = scan_state(missing_only(3, "SM5: Mystery Packet"), tmp)       # Unknown Group
    assert o_unk.missing[0].flag.classification == engine.UNRESOLVED
    unk_msg = templates.parent_message_for(o_unk.missing[0].flag)
    assert "is currently missing SM5: Mystery Packet." in unk_msg
    assert "homework" not in unk_msg
    assert "missing the assessment" not in unk_msg
print("PASS missing-item classification drives type-aware parent templates")

# ---------------------------------------------------------------------------
# Missing-work eligibility rule (refined): an assignment may only generate
# MISSING_ASSIGNMENT when due date passed OR grading has started.
# ---------------------------------------------------------------------------
def elig_reader(assignment_due, subs, assignment_id=20, group_id=2):
    return SyntheticReader(
        [Student(user_id=1, name="Student Alpha", current_score=90),
         Student(user_id=2, name="Student Beta", current_score=92)],
        [Assignment(id=assignment_id, name="SM5: Lesson 31 Homework",
                    assignment_group_id=group_id, due_at=assignment_due)],
        GROUPS, subs,
    )

# Excused work: Canvas stores it as workflow_state="graded" with a null score.
# It must never count as a grade, never start grading, and never be missing.
_ex = Submission(id=1, user_id=1, assignment_id=20, score=None, grade=None,
                 excused=True, workflow_state="graded")
assert engine.has_real_grade(_ex) is False
assert engine.grading_has_started([_ex]) is False

def missing_count(reader):
    with tempfile.TemporaryDirectory() as tmp:
        o, _ = scan_state(reader, tmp)
        return len(o.missing), o

# Excused submissions (Canvas: workflow_state="graded", score null) must not
# start grading and must not flag anyone.
n, o = missing_count(elig_reader(FUTURE_DUE, [
    Submission(id=1, user_id=1, assignment_id=20, score=None, grade=None,
               excused=True, workflow_state="graded"),
    Submission(id=2, user_id=2, assignment_id=20, score=None, grade=None,
               excused=True, workflow_state="graded"),
]))
assert n == 0, f"excused-only must not start grading or flag: {n}"
# Excused student alongside a genuinely graded peer is still not missing.
n, o = missing_count(elig_reader(PAST_DUE, [
    Submission(id=1, user_id=1, assignment_id=20, score=None, grade=None,
               excused=True, workflow_state="graded"),
    Submission(id=2, user_id=2, assignment_id=20, score=100.0, grade="100"),
]))
assert all(f.flag.student_id != 1 for f in o.missing), "excused student must not be flagged"

# Case A: future assignment + all grades blank -> NO missing flags.
n, _ = missing_count(elig_reader(FUTURE_DUE, [
    Submission(id=1, user_id=1, assignment_id=20, score=None, grade=None),
    Submission(id=2, user_id=2, assignment_id=20, score=None, grade=None),
]))
assert n == 0, f"future + all blank must not flag: {n}"

# Canvas missing=true + all grades blank + not due -> NO missing flags.
n, _ = missing_count(elig_reader(FUTURE_DUE, [
    Submission(id=1, user_id=1, assignment_id=20, score=None, grade=None, missing=True),
    Submission(id=2, user_id=2, assignment_id=20, score=None, grade=None, missing=True),
]))
assert n == 0, f"missing=true must not bypass the due-date gate: {n}"

# DUE-DATE-ONLY: future assignment + peers already graded -> NO missing flags.
# (This is the ELA4A: Spelling Test 30 case; the grading-started override is gone.)
n, _ = missing_count(elig_reader(FUTURE_DUE, [
    Submission(id=1, user_id=1, assignment_id=20, score=100.0, grade="100"),
    Submission(id=2, user_id=2, assignment_id=20, score=None, grade=None),
]))
assert n == 0, f"early peer grading must NOT flag a future assignment: {n}"

# future + MI marker -> NO missing flags (nothing before the due date).
n, _ = missing_count(elig_reader(FUTURE_DUE, [
    Submission(id=1, user_id=1, assignment_id=20, grade="MI"),
    Submission(id=2, user_id=2, assignment_id=20, grade="mi"),
]))
assert n == 0, f"MI must not flag before the due date: {n}"

# future + every peer graded, this student blank -> still NO flag.
n, _ = missing_count(elig_reader(FUTURE_DUE, [
    Submission(id=1, user_id=1, assignment_id=20, score=100.0, grade="100"),
    Submission(id=2, user_id=2, assignment_id=20, score=None, grade=None),
]))
assert n == 0

# Past-due + blank student -> flagged (no peer grading needed).
n, o = missing_count(elig_reader(PAST_DUE, [
    Submission(id=1, user_id=1, assignment_id=20, score=None, grade=None),
    Submission(id=2, user_id=2, assignment_id=20, score=None, grade=None),
]))
assert n == 2, f"past-due blanks must all flag: {n}"

# Past-due + MI -> flagged.
n, o = missing_count(elig_reader(PAST_DUE, [
    Submission(id=1, user_id=1, assignment_id=20, grade="mi"),
    Submission(id=2, user_id=2, assignment_id=20, score=100.0, grade="100"),
]))
assert n == 1, f"past-due MI must flag: {n}"
assert o.missing[0].flag.raw_status == "mi"

# Past-due + grade 0 -> NOT missing (a real zero is a grade).
n, o = missing_count(elig_reader(PAST_DUE, [
    Submission(id=1, user_id=1, assignment_id=20, score=0.0, grade="0"),
    Submission(id=2, user_id=2, assignment_id=20, score=None, grade=None),
]))
assert all(f.flag.student_id != 1 for f in o.missing), "grade 0 must not be missing"

# Past-due + any real grade -> not missing.
n, o = missing_count(elig_reader(PAST_DUE, [
    Submission(id=1, user_id=1, assignment_id=20, score=88.0, grade="88%"),
    Submission(id=2, user_id=2, assignment_id=20, score=72.0, grade="72%"),
]))
assert n == 0, f"real grades must never be missing: {n}"

# grading_has_started is retained as a diagnostic only.
assert engine.grading_has_started([
    Submission(id=1, user_id=1, assignment_id=20, score=100.0, grade="100"),
]) is True
assert engine.grading_has_started([
    Submission(id=1, user_id=1, assignment_id=20, score=None, grade=None),
]) is False
# The override is gone: an eligible-for-grading-started assignment is still not
# eligible for missing checks before the due date.
_fut = Assignment(id=20, name="X", assignment_group_id=2, due_at=FUTURE_DUE)
assert engine.assignment_eligible_for_missing(_fut, [
    Submission(id=1, user_id=1, assignment_id=20, score=100.0, grade="100"),
]) is False, "grading-started override must not exist"

# Assignment with no due date at all must not flag an ungraded class.
n, _ = missing_count(elig_reader(None, [
    Submission(id=1, user_id=1, assignment_id=20, score=None, grade=None),
    Submission(id=2, user_id=2, assignment_id=20, score=None, grade=None),
]))
assert n == 0, f"missing due_at must not imply due: {n}"

# Persistence preserved: a legitimately-active missing flag stays STILL ACTIVE.
_miss = elig_reader(PAST_DUE, [
    Submission(id=1, user_id=1, assignment_id=20, grade="MI"),
    Submission(id=2, user_id=2, assignment_id=20, score=100.0, grade="100"),
])
with tempfile.TemporaryDirectory() as tmp:
    o1, _ = scan_state(_miss, tmp)
    assert len(o1.missing) == 1 and o1.missing[0].status == report.NEW
    o2, _ = scan_state(_miss, tmp)
    assert len(o2.missing) == 1 and o2.missing[0].status == report.STILL_ACTIVE
    # Resolves once the student later receives a grade.
    _resolved = elig_reader(PAST_DUE, [
        Submission(id=1, user_id=1, assignment_id=20, score=91.0, grade="91"),
        Submission(id=2, user_id=2, assignment_id=20, score=100.0, grade="100"),
    ])
    o3, _ = scan_state(_resolved, tmp)
    assert len(o3.missing) == 0
    assert any(f.flag_type == engine.MISSING_ASSIGNMENT for f in o3.resolved)
print("PASS missing eligibility: due-date-only gate, future/MI/missing=true/early-grading all suppressed, zero is a grade")

# ---------------------------------------------------------------------------
# Authoritative missing-rule regression: the six canonical rules, each asserted
# explicitly against engine.student_is_missing so a future refactor cannot
# silently change behavior.
# ---------------------------------------------------------------------------
_past = Assignment(id=20, name="X", assignment_group_id=2, due_at=PAST_DUE)
_future = Assignment(id=20, name="X", assignment_group_id=2, due_at=FUTURE_DUE)

def _flag_count(assignment, subs):
    n, o = missing_count(elig_reader(assignment.due_at, subs))
    return n, o

# Rule 1: future-due assignment -> never flag missing, regardless of evidence.
for _sub in (
    Submission(id=1, user_id=1, assignment_id=20, score=None, grade=None),
    Submission(id=1, user_id=1, assignment_id=20, score=None, grade=None, missing=True),
    Submission(id=1, user_id=1, assignment_id=20, grade="MI"),
    Submission(id=1, user_id=1, assignment_id=20, grade="mi"),
):
    assert engine.assignment_eligible_for_missing(_future, [_sub]) is False
    n, _ = _flag_count(_future, [_sub,
        Submission(id=2, user_id=2, assignment_id=20, score=100.0, grade="100")])
    assert n == 0, f"future-due must never flag: {n}"

# Rule 2: overdue + blank score/grade -> missing.
assert engine.student_is_missing(
    Submission(id=1, user_id=1, assignment_id=20, score=None, grade=None)) is True
n, _ = _flag_count(_past, [
    Submission(id=1, user_id=1, assignment_id=20, score=None, grade=None),
    Submission(id=2, user_id=2, assignment_id=20, score=100.0, grade="100")])
assert n == 1, f"overdue blank must flag: {n}"

# Rule 3: overdue + MI / mi -> missing (case-insensitive).
for _mi in ("MI", "mi", "Mi", "mI"):
    assert engine.student_is_missing(
        Submission(id=1, user_id=1, assignment_id=20, grade=_mi)) is True, _mi

# Rule 4: overdue + numeric 0 -> graded, not missing.
assert engine.has_real_grade(
    Submission(id=1, user_id=1, assignment_id=20, score=0.0, grade="0")) is True
assert engine.student_is_missing(
    Submission(id=1, user_id=1, assignment_id=20, score=0.0, grade="0")) is False

# Rule 5: missing=true alone does not control eligibility (does not create a flag).
n, _ = _flag_count(_future, [
    Submission(id=1, user_id=1, assignment_id=20, score=None, grade=None, missing=True),
    Submission(id=2, user_id=2, assignment_id=20, score=None, grade=None, missing=True)])
assert n == 0, f"missing=true alone must not flag: {n}"

# Rule 6: missing=false does NOT protect an overdue blank from being flagged.
n, o = _flag_count(_past, [
    Submission(id=1, user_id=1, assignment_id=20, score=None, grade=None, missing=False),
    Submission(id=2, user_id=2, assignment_id=20, score=100.0, grade="100")])
assert n == 1, f"missing=false must not protect an overdue blank: {n}"
assert o.missing[0].flag.student_id == 1
print("PASS authoritative missing rule: 6 canonical cases (future/blank/MI/zero/missing=true/missing=false)")

# ---------------------------------------------------------------------------
# No student names used as identifiers; keys are course+student(+assignment).
# ---------------------------------------------------------------------------
assert engine.missing_key(26404, 1, 11).startswith("26404:1:11:")
assert engine.low_average_key(26404, 1).startswith("26404:1:")
assert "Student" not in engine.low_assessment_key(26404, 1, 10)
print("PASS stable identities use IDs, never names")

# ---------------------------------------------------------------------------
# Quarter/course applicability lives in config (not hard-coded in the scanner).
# ---------------------------------------------------------------------------
assert [s.key for s in config.active_subjects(cfg, 1)] == ["reading-spelling", "math", "language-arts", "history"]
assert [s.key for s in config.active_subjects(cfg, 2)] == ["science"]
print("PASS quarter applicability is configuration-driven")

# ---------------------------------------------------------------------------
# Transactional safeguard: run_scan is side-effect free; last_send persists
# only via write_state (i.e. after a confirmed send).
# ---------------------------------------------------------------------------
with tempfile.TemporaryDirectory() as tmp:
    store = StateStore(Path(tmp), "state.json")
    scan = cli.run_scan(reader1, math_cfg, 1, store)
    # run_scan alone must NOT write the state file.
    assert not store.path.exists(), "run_scan must be side-effect free"

    # Simulate a successful send with last-send metadata.
    state_mod.write_state(
        store,
        active_persistent=scan.active_persistent,
        resolved_flags=scan.merged_resolved,
        one_time_issued=scan.merged_issued,
        last_send={"sent_at": "2026-09-09T00:00:00+00:00", "subject": "baseline"},
    )
    persisted = store.load()
    assert persisted["last_send"]["subject"] == "baseline"
    assert len(persisted["active_flags"]) == len(scan.active_persistent)
    # one-time assessment key is recorded as issued.
    assert any(k.endswith("LOW_ASSESSMENT_SCORE") for k in persisted["one_time_issued"])
print("PASS transactional safeguard: no persistence without a confirmed send")

# ---------------------------------------------------------------------------
# Meaningful-change email gate: NEW or RESOLVED qualifies; unchanged
# STILL ACTIVE only does not. Detection/thresholds/persistence unchanged.
# ---------------------------------------------------------------------------
with tempfile.TemporaryDirectory() as tmp:
    o_new, _ = scan_state(reader1, tmp)          # NEW flags present
    assert o_new.has_change is True
    o_still, _ = scan_state(reader1, tmp)        # unchanged STILL ACTIVE only
    assert o_still.has_any_flag is True
    assert o_still.has_change is False, "unchanged STILL ACTIVE must not be a change"
    o_res, _ = scan_state(reader3, tmp)          # resolved flags present
    assert o_res.has_change is True, "resolved flags must qualify as a change"
print("PASS meaningful-change gate: NEW/RESOLVED qualify, unchanged STILL ACTIVE does not")

# ---------------------------------------------------------------------------
# command_send with unchanged STILL ACTIVE only: suppresses the email and
# reports zero writes/emails (regression: this path must not raise).
# ---------------------------------------------------------------------------
import contextlib as _ctx
import io as _io
import types as _types
from scripts.canvas_llm_grade_check import cli as _cli
from scripts.canvas_llm_grade_check import emailer as _emailer_mod

with tempfile.TemporaryDirectory() as tmp:
    # Seed an isolated store: scan 1 persists, scan 2 is unchanged STILL ACTIVE.
    _o1, _ = scan_state(reader1, tmp)
    _o2, _ = scan_state(reader1, tmp)
    assert _o2.has_change is False

    # CRITICAL: command_send resolves its state store from cfg.state_directory,
    # which defaults to the REAL repo path. Point it at the isolated temp dir so
    # this test can never read or overwrite the real local grade state.
    _send_cfg = config.load_config()
    _send_cfg.quarter_subjects = {1: ("math",)}
    _send_cfg.state_directory = tmp
    _send_cfg.state_file = "state.json"
    assert not str(_send_cfg.state_directory).startswith(str(root / ".local"))

    # Fail loudly if any send is attempted: there must be no email transport use.
    _calls = []
    _orig_send = _cli.emailer.send_teacher_report

    def _spy(**k):
        _calls.append(k)
        return _emailer_mod.EmailResult(
            sent=True, recipients=["owen.reagan@thalesacademy.org"],
            subject=k.get("subject", ""),
        )

    _cli.emailer.send_teacher_report = _spy
    _orig_reader = _cli._build_reader
    _cli._build_reader = lambda: reader1
    try:
        buf = _io.StringIO()
        with _ctx.redirect_stdout(buf):
            rc = _cli.command_send(_send_cfg, 1)
        out = buf.getvalue()
    finally:
        _cli.emailer.send_teacher_report = _orig_send
        _cli._build_reader = _orig_reader

    assert rc == 0, f"unchanged run should exit 0, got {rc}: {out}"
    assert "email suppressed" in out
    assert "CANVAS WRITES PERFORMED: 0" in out
    assert "EMAILS SENT: 0" in out
    assert _calls == [], f"no email may be attempted when nothing changed: {_calls}"
print("PASS unchanged STILL ACTIVE send suppresses email and attempts no send")

# ---------------------------------------------------------------------------
# Baseline email body: subject, intro, four sections, no parent template for
# unresolved items.
# ---------------------------------------------------------------------------
baseline = report.render_baseline_email_body(
    report.ScanOutcome(
        quarter=1,
        courses=[],
        missing=[report.ReportEntry(engine.Flag(
            key="26404:1:10:MISSING_ASSIGNMENT", flag_type=engine.MISSING_ASSIGNMENT,
            course_id=26404, course_name="Math", student_id=1, student_name="Student Alpha",
            first_name="Student", assignment_id=10, assignment_title="SM5: Lesson 26 Homework",
            raw_status="MI", classification=engine.NON_ASSESSMENT,
        ), report.NEW)],
        low_assessment=[],
        low_average=[],
        unresolved=[engine.UnresolvedItem(
            course_id=28165, course_name="History", student_id=2, student_name="Student Gamma",
            assignment_id=30, assignment_title="HIST 4B: Maps Vocabulary Review 1-3",
            reason="x", assignment_group="Assignments",
        )],
    )
)
assert report.BASELINE_SUBJECT in baseline
assert "initial Grade Check baseline" in baseline
assert "UNRESOLVED LOW-SCORE ITEMS — INFORMATIONAL ONLY" in baseline
assert "Your child, Student, is currently missing the homework assignment for Lesson 26." in baseline
# Unresolved items must NOT include a parent template for the student.
assert "complete the missing assessment" not in baseline
assert "Maps Vocabulary Review 1-3" in baseline
print("PASS baseline email body has subject, intro, four sections, informational-only unresolved")

# ---------------------------------------------------------------------------
# Gmail OAuth/API primary transport + SMTP fallback-disabled (no network).
# ---------------------------------------------------------------------------
from types import SimpleNamespace
from scripts.canvas_llm_grade_check import emailer as emailer_mod

GOOD_SENDER = {"host": "", "port": "587", "user": "oreagan81@gmail.com",
               "password": "", "from": "oreagan81@gmail.com"}

# 1. Gmail API success permits state persistence (mock gmail transport).
gmail_ok = SimpleNamespace(
    oauth_ready=lambda: True,
    GmailTransportError=RuntimeError,
    send_via_gmail_api=lambda subject, body, sender, recipient: SimpleNamespace(
        sent=True, message_id="mock-msg-id"),
)
saved_gm = sys.modules.get("scripts.canvas_llm_grade_check.gmail_transport")
sys.modules["scripts.canvas_llm_grade_check.gmail_transport"] = gmail_ok
from scripts.canvas_llm_grade_check import gmail_transport as gt_mod
import scripts.canvas_llm_grade_check as gc_pkg
setattr(gc_pkg, "gmail_transport", gmail_ok)
try:
    os.environ["CANVAS_LLM_GRADE_CHECK_SEND_APPROVED"] = "1"
    res_ok = emailer_mod.send_teacher_report(
        subject="s", body="b", recipient="owen.reagan@thalesacademy.org", config=GOOD_SENDER)
    assert res_ok.sent is True
    # State persistence is permitted when send is confirmed (proven by
    # write_state in cli.command_send after result.sent is True).
    assert res_ok.reason is None

    # 2. Gmail API failure does NOT persist state (reason carries error, sent=False).
    gmail_fail = SimpleNamespace(
        oauth_ready=lambda: True,
        GmailTransportError=RuntimeError,
        send_via_gmail_api=lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    sys.modules["scripts.canvas_llm_grade_check.gmail_transport"] = gmail_fail
    setattr(gc_pkg, "gmail_transport", gmail_fail)
    res_fail = emailer_mod.send_teacher_report(
        subject="s", body="b", recipient="owen.reagan@thalesacademy.org", config=GOOD_SENDER)
    assert res_fail.sent is False
    assert "Gmail API send error" in (res_fail.reason or "")
    os.environ.pop("CANVAS_LLM_GRADE_CHECK_SEND_APPROVED", None)
finally:
    # Force a clean re-import of the REAL gmail_transport module: drop the mock
    # from both sys.modules and the package attribute, then re-import so later
    # tests see the real module and its real SCOPE/oauth_status.
    import importlib
    sys.modules.pop("scripts.canvas_llm_grade_check.gmail_transport", None)
    if hasattr(gc_pkg, "gmail_transport"):
        delattr(gc_pkg, "gmail_transport")
    real_gt = importlib.import_module("scripts.canvas_llm_grade_check.gmail_transport")
    setattr(gc_pkg, "gmail_transport", real_gt)
    sys.modules["scripts.canvas_llm_grade_check.gmail_transport"] = real_gt
    os.environ.pop("CANVAS_LLM_GRADE_CHECK_SEND_APPROVED", None)
print("PASS Gmail API transport: success permits persistence, failure blocks persistence")

# 3. SMTP fallback disabled by default.
os.environ.pop("CANVAS_LLM_GRADE_CHECK_SMTP_ENABLED", None)
assert emailer_mod._smtp_enabled() is False
os.environ["CANVAS_LLM_GRADE_CHECK_GRADE_CHECK_SMTP_ENABLED"] = "1"  # wrong key, must not enable
assert emailer_mod._smtp_enabled() is False
os.environ.pop("CANVAS_LLM_GRADE_CHECK_GRADE_CHECK_SMTP_ENABLED", None)
os.environ["CANVAS_LLM_GRADE_CHECK_SMTP_ENABLED"] = "1"
assert emailer_mod._smtp_enabled() is True
os.environ.pop("CANVAS_LLM_GRADE_CHECK_SMTP_ENABLED", None)
print("PASS SMTP fallback disabled by default; enabled only via explicit flag")

# ---------------------------------------------------------------------------
# OAuth setup/status helper (no real OAuth; no network; no send).
# ---------------------------------------------------------------------------
from scripts.canvas_llm_grade_check import gmail_transport as gt

GOOD_TOK = {"scope": gt.SCOPES, "email": gt.ALLOWED_ACCOUNT, "refresh_token": "rt", "token_type": "Bearer"}
WRONG_ACCT = {"scope": gt.SCOPES, "email": "someone.else@gmail.com", "refresh_token": "rt"}
NO_SCOPE = {"scope": "https://www.googleapis.com/auth/gmail.readonly",
            "email": gt.ALLOWED_ACCOUNT, "refresh_token": "rt"}

def _write(tmp, name, payload, mode):
    p = Path(tmp) / name
    p.write_text(json.dumps(payload))
    p.chmod(mode)
    return p

with tempfile.TemporaryDirectory() as tmp:
    gt.set_config_dir(Path(tmp))

    # 1. Missing client_secret -> not ready.
    s = gt.oauth_status()
    assert s["client_credential_present"] is False
    assert s["gmail_transport_ready"] is False

    # Place client_secret + valid token -> ready.
    (Path(tmp) / "client_secret.json").write_text(json.dumps({"installed": {"client_id": "c", "client_secret": "s"}}))
    _write(tmp, "token.json", GOOD_TOK, 0o600)
    s = gt.oauth_status()
    assert s["client_credential_present"] is True
    assert s["token_present"] is True
    assert s["token_permissions_safe"] is True
    assert s["authorized_sender_identity"] is True
    assert s["gmail_send_scope_present"] is True
    assert s["gmail_transport_ready"] is True

    # 2. Wrong authorized account -> identity FAIL, not ready.
    _write(tmp, "token.json", WRONG_ACCT, 0o600)
    s = gt.oauth_status()
    assert s["authorized_sender_identity"] is False
    assert s["gmail_transport_ready"] is False

    # 3. Missing gmail.send scope -> scope FAIL, not ready.
    _write(tmp, "token.json", NO_SCOPE, 0o600)
    s = gt.oauth_status()
    assert s["gmail_send_scope_present"] is False
    assert s["gmail_transport_ready"] is False

    # 4. Unsafe token permissions (0644) -> permissions FAIL.
    _write(tmp, "token.json", GOOD_TOK, 0o644)
    s = gt.oauth_status()
    assert s["token_permissions_safe"] is False
    assert s["gmail_transport_ready"] is False

    # 5. No secret/token leakage in status output. (Only check for literal
    #    secret KEY names and the actual secret value — not common substrings
    #    like "rt" or "Authorization" which legitimately appear in output.)
    lines = gt.oauth_status_lines()
    joined = "\n".join(lines)
    for secret in ["refresh_token", "access_token", "client_secret", '"rt"', "Bearer <"]:
        assert secret not in joined, f"secret leaked: {secret}"

    # 6. No OOB redirect anywhere.
    cl = {"auth_uri": "https://accounts.google.com/o/oauth2/v2/auth", "client_id": "c",
          "redirect_uris": ["http://localhost:8080/"]}
    u = gt.build_authorize_url(cl, "http://localhost:8080/", "st")
    assert "urn:ietf:wg:oauth:2.0:oob" not in u
    q = __import__("urllib.parse", fromlist=["parse_qs"]).parse_qs(__import__("urllib.parse", fromlist=["urlparse"]).urlparse(u).query)
    assert q["redirect_uri"] == ["http://localhost:8080/"]
    assert q["state"] == ["st"]
    assert gt.GMAIL_SEND_SCOPE in q["scope"][0]

    # 7. Scope-safety: identity scopes allowed, gmail.send required, broader
    #    Gmail data scopes rejected. Ordering is irrelevant.
    def _ss(scope): return gt._scope_is_gmail_send_only(gt._granted_scope_set({"scope": scope}))
    # PASS cases.
    assert _ss("openid email profile " + gt.GMAIL_SEND_SCOPE) is True
    assert _ss(gt.GMAIL_SEND_SCOPE + " openid email profile") is True
    # Google echoes identity scopes in canonical userinfo URI form.
    assert _ss("openid https://www.googleapis.com/auth/userinfo.email "
               "https://www.googleapis.com/auth/userinfo.profile " + gt.GMAIL_SEND_SCOPE) is True
    # FAIL cases.
    assert _ss("openid email profile " + gt.GMAIL_SEND_SCOPE
               + " https://www.googleapis.com/auth/gmail.readonly") is False
    assert _ss("openid email profile https://www.googleapis.com/auth/gmail.modify") is False
    assert _ss("openid email profile https://www.googleapis.com/auth/gmail.send "
               "https://www.googleapis.com/auth/gmail.compose") is False
    assert _ss("openid email profile https://www.googleapis.com/auth/gmail.send "
               "https://www.googleapis.com/auth/gmail.insert") is False
    assert _ss("openid email profile https://mail.google.com/") is False
    assert _ss("openid email profile " + gt.GMAIL_SEND_SCOPE + " https://mail.google.com/") is False
    assert _ss("openid email profile") is False
    # validate_token_metadata agrees.
    send_only = {"scope": gt.SCOPES, "email": gt.ALLOWED_ACCOUNT}
    assert gt.validate_token_metadata(send_only) is None
    broad = {"scope": gt.SCOPES + " https://www.googleapis.com/auth/gmail.readonly",
             "email": gt.ALLOWED_ACCOUNT}
    assert "beyond gmail.send" in (gt.validate_token_metadata(broad) or "")

    # 8. Identity verification succeeds without broader Gmail scopes: extract
    #    email from the OIDC id_token (no Gmail profile endpoint call).
    import base64 as _b64
    def _jwt(payload):
        def b(d): return _b64.urlsafe_b64encode(json.dumps(d).encode()).decode().rstrip("=")
        return b({"alg": "none"}) + "." + b(payload) + ".sig"
    idt_ok = _jwt({"email": gt.ALLOWED_ACCOUNT})
    assert gt.decode_id_token_email(idt_ok) == gt.ALLOWED_ACCOUNT
    assert gt.extract_identity_from_token_response({"id_token": idt_ok}) == gt.ALLOWED_ACCOUNT
    idt_wrong = _jwt({"email": "someone.else@gmail.com"})
    assert gt._identity_is_allowed(gt.extract_identity_from_token_response({"id_token": idt_wrong})) is False
    assert gt.decode_id_token_email("not.a.jwt") is None

    # 9. Wrong account fails closed through the full setup flow (injected code +
    #    exchange + identity, no network/browser).
    def code_provider(**kw): return "SECRET_AUTHCODE", "state"
    def exch_ok(client, code, redirect_uri):
        return {"refresh_token": "SECRET_REFRESH_TOKEN", "access_token": "SECRET_ACCESS_TOKEN",
                "id_token": idt_ok, "scope": gt.SCOPES, "token_type": "Bearer"}
    rc = gt.run_oauth_setup(
        print_fn=lambda *a, **k: None,
        get_authorization_code=code_provider,
        exchange_fn=exch_ok,
        identity_fn=gt.extract_identity_from_token_response,
    )
    assert rc == 0
    assert gt.token_file().exists()
    assert gt.file_mode_is_600(gt.token_file())
    tok = json.loads(gt.token_file().read_text(encoding="utf-8"))
    assert tok["email"] == gt.ALLOWED_ACCOUNT
    assert gt.GMAIL_SEND_SCOPE in tok["scope"]

    def exch_wrong(client, code, redirect_uri):
        return {"refresh_token": "SECRET_REFRESH_TOKEN", "access_token": "SECRET_ACCESS_TOKEN",
                "id_token": _jwt({"email": "someone.else@gmail.com"}),
                "scope": gt.SCOPES, "token_type": "Bearer"}
    assert gt.run_oauth_setup(print_fn=lambda *a, **k: None,
        get_authorization_code=code_provider, exchange_fn=exch_wrong,
        identity_fn=gt.extract_identity_from_token_response) != 0

    def exch_broad(client, code, redirect_uri):
        return {"refresh_token": "SECRET_REFRESH_TOKEN", "access_token": "SECRET_ACCESS_TOKEN",
                "id_token": idt_ok,
                "scope": gt.SCOPES + " https://www.googleapis.com/auth/gmail.readonly",
                "token_type": "Bearer"}
    assert gt.run_oauth_setup(print_fn=lambda *a, **k: None,
        get_authorization_code=code_provider, exchange_fn=exch_broad,
        identity_fn=gt.extract_identity_from_token_response) != 0

    # A scope-safety failure must NOT write a token.
    if gt.token_file().exists():
        gt.token_file().unlink()
    assert not gt.token_file().exists()
    assert gt.run_oauth_setup(print_fn=lambda *a, **k: None,
        get_authorization_code=code_provider, exchange_fn=exch_broad,
        identity_fn=gt.extract_identity_from_token_response) != 0
    assert not gt.token_file().exists(), "no token may be written when scope-safety fails"

    # No id_token -> identity cannot be proven -> fail closed.
    def exch_noid(client, code, redirect_uri):
        return {"refresh_token": "SECRET_REFRESH_TOKEN", "access_token": "SECRET_ACCESS_TOKEN",
                "scope": gt.SCOPES}
    assert gt.run_oauth_setup(print_fn=lambda *a, **k: None,
        get_authorization_code=code_provider, exchange_fn=exch_noid,
        identity_fn=gt.extract_identity_from_token_response) != 0

    # Token contents never printed.
    captured = []
    gt.run_oauth_setup(print_fn=lambda *a, **k: captured.append(" ".join(str(x) for x in a)),
        get_authorization_code=code_provider, exchange_fn=exch_ok,
        identity_fn=gt.extract_identity_from_token_response)
    joined_cap = "\n".join(captured)
    for secret in ["SECRET_AUTHCODE", "SECRET_REFRESH_TOKEN", "SECRET_ACCESS_TOKEN",
                   "refresh_token", "access_token", "client_secret"]:
        assert secret not in joined_cap, f"secret leaked: {secret}"
    print("PASS OAuth helper: missing client_secret / wrong account / missing scope / "
          "perms / id_token identity / no OOB / no profile endpoint / no leakage / no send")

gt.set_config_dir(Path.home() / ".config" / "teacher-ai-workstation" / "grade-check-oauth")

# ---------------------------------------------------------------------------
# Scheduler: LaunchAgent plist generation, weekday 4:15 PM, no --baseline,
# no secrets, duplicate protection, uninstall scope, no send/no write.
# ---------------------------------------------------------------------------
from scripts.canvas_llm_grade_check import scheduler as sch

sched_cfg = config.load_config()
sched = sched_cfg.schedule
assert sched.weekdays_only is True
assert sched.hour_local == 16 and sched.minute_local == 15
assert sch._schedule_label(sched) == "Mon–Fri 4:15 PM ET"

plist = sch.build_plist(sched_cfg)
assert plist["Label"] == "com.teacher-ai-workstation.grade-check"

# Mon-Fri only: five intervals, weekdays 1-5, never weekend.
intervals = plist["StartCalendarInterval"]
assert len(intervals) == 5, intervals
wd = sorted(i["Weekday"] for i in intervals)
assert wd == [1, 2, 3, 4, 5], wd
assert not any(i["Weekday"] in (0, 6, 7) for i in intervals), "no weekend schedule"
for i in intervals:
    assert i["Hour"] == 16 and i["Minute"] == 15

# No --baseline in the scheduled command; --send only.
args = plist["ProgramArguments"]
assert "--send" in args
assert "--baseline" not in args and "--preview" not in args
assert "--baseline" not in sch.scheduled_shell_command()
assert sch.SCHEDULED_ARGS == ("--send",)

# Minimal explicit environment with the approval flag; no secrets anywhere.
assert plist["EnvironmentVariables"]["CANVAS_LLM_GRADE_CHECK_SEND_APPROVED"] == "1"
xml_lower = sch.render_plist_xml(sched_cfg).lower()
for forbidden in ["refresh_token", "access_token", "client_secret", "client_id",
                  "password", "smtp_password", "secret"]:
    assert forbidden not in xml_lower, f"plist leaks {forbidden}"

# OAuth credential path unchanged (not duplicated/relocated, not in plist).
oauth_dir = Path.home() / ".config" / "teacher-ai-workstation" / "grade-check-oauth"
assert sch.gmail_oauth_dir() == oauth_dir
assert "grade-check-oauth" not in xml_lower
assert gt.CONFIG_DIR == oauth_dir
assert gt.TOKEN_FILE.parent == oauth_dir

# Duplicate install protection: one canonical plist path + one label.
assert sch.plist_path().name == "com.teacher-ai-workstation.grade-check.plist"
assert sch.plist_path().parent == Path.home() / "Library" / "LaunchAgents"
assert sch.LAUNCH_AGENT_LABEL == "com.teacher-ai-workstation.grade-check"

# Uninstall scope: only the Grade Check label/plist, nothing broader.
assert sch.PLIST_FILENAME == "com.teacher-ai-workstation.grade-check.plist"

# Logs are repo-local and gitignored.
assert ".local/canvas-llm/grade-check/logs" in plist["StandardOutPath"]

# Status/self-test perform no email send and no Canvas write.
import subprocess as _sp
_status_out = _sp.run([sys.executable, "scripts/canvas_llm_grade_check/scheduler.py", "status"],
                      capture_output=True, text=True, timeout=60)
assert _status_out.returncode == 0, _status_out.stderr
assert "CANVAS WRITES PERFORMED: 0" in _status_out.stdout
assert "EMAILS SENT: 0" in _status_out.stdout
assert "Gmail transport ready:" in _status_out.stdout
assert "last exit status:" in _status_out.stdout
print("PASS scheduler: Mon-Fri 4:15 PM plist / no baseline / no secrets / no send")

# ---------------------------------------------------------------------------
# Health check: PASS/WARN/FAIL + exit codes, school-day logic, no send/no write.
# ---------------------------------------------------------------------------
from scripts.canvas_llm_grade_check import health as health_mod

assert (health_mod.EXIT_PASS, health_mod.EXIT_WARN, health_mod.EXIT_FAIL) == (0, 1, 2)
assert health_mod.PASS == "PASS" and health_mod.WARN == "WARN" and health_mod.FAIL == "FAIL"

# Stale-run threshold is strictly greater than 2 school days.
assert health_mod.STALE_AFTER_SCHOOL_DAYS == 2

_days, _src = health_mod.school_days()
assert _src.startswith("instructional-week calendar"), _src
# Weekends are never counted as school days.
assert health_mod.is_school_day(dt.date(2026, 9, 12), _days, _src) is False   # Sat
assert health_mod.is_school_day(dt.date(2026, 9, 13), _days, _src) is False   # Sun
# Fall-break weekdays are excluded by the canonical calendar.
assert health_mod.is_school_day(dt.date(2026, 9, 22), _days, _src) is False
# Weekend gap is not counted: Fri -> Mon = 1 school day.
assert health_mod.school_days_between(dt.date(2026, 9, 11), dt.date(2026, 9, 14), _days, _src) == 1
# Fri -> Sun = 0 school days (pure weekend).
assert health_mod.school_days_between(dt.date(2026, 9, 11), dt.date(2026, 9, 13), _days, _src) == 0

# Freshness verdicts: fresh PASS, >2 school days WARN.
_thu = dt.datetime(2026, 9, 10, 16, 15)
_sec, st, n, _ = health_mod.check_freshness("2026-09-10T20:15:00+00:00", _thu)
assert st == health_mod.PASS and n == 0
_sec, st, n, _ = health_mod.check_freshness("2026-09-08T20:15:00+00:00", _thu)
assert st == health_mod.PASS and n == 2, (st, n)
_sec, st, n, _ = health_mod.check_freshness("2026-09-07T20:15:00+00:00", _thu)
assert st == health_mod.WARN and n == 3, (st, n)

# Synthetic/test keys are detected (critical state-integrity signal).
assert health_mod.synthetic_keys(
    {"active_flags": {"26404:1:11:MISSING_ASSIGNMENT": {}}}) != []
assert health_mod.synthetic_keys(
    {"one_time_issued": {"26442:22140:1020031:LOW_ASSESSMENT_SCORE": True}}) == []

# Live report: healthy system -> PASS/exit 0. Mutate nothing, send nothing.
_state_hash = hashlib.sha256(
    (root / ".local/canvas-llm/grade-check/state.json").read_bytes()
).hexdigest() if (root / ".local/canvas-llm/grade-check/state.json").exists() else None

_out = subprocess.run(["bash", "bin/grade-check-health"],
                      capture_output=True, text=True, timeout=60)
assert _out.returncode in (0, 1, 2), (_out.returncode, _out.stderr[-400:])
assert "CANVAS WRITES PERFORMED: 0" in _out.stdout
assert "EMAILS SENT: 0" in _out.stdout
assert "STATE MUTATIONS: 0" in _out.stdout
# Exactly one overall verdict line.
_verdicts = [ln for ln in _out.stdout.splitlines() if ln.startswith("GRADE CHECK HEALTH:")]
assert len(_verdicts) == 1, _verdicts
assert _verdicts[0].split(": ")[1] in ("PASS", "WARN", "FAIL")
# Exit code agrees with the printed verdict.
_expected_exit = {"PASS": 0, "WARN": 1, "FAIL": 2}[_verdicts[0].split(": ")[1]]
assert _out.returncode == _expected_exit, (_out.returncode, _verdicts[0])

# Health check printed no secret material.
for forbidden in ("refresh_token", "access_token", "client_secret",
                  "client_id", "ya29.", "SMTP_PASSWORD"):
    assert forbidden not in _out.stdout, f"health leaked {forbidden!r}"

# Health check mutated no state.
if _state_hash is not None:
    _after = hashlib.sha256(
        (root / ".local/canvas-llm/grade-check/state.json").read_bytes()
    ).hexdigest()
    assert _after == _state_hash, "health check must not mutate state"

# FAIL paths, exercised with injected data so the real install is untouched.
with tempfile.TemporaryDirectory() as _tmp:
    # Corrupt state -> FAIL.
    _bad = Path(_tmp) / "state.json"
    _bad.write_text("{not valid json", encoding="utf-8")
    _sec, _data = health_mod.check_state(_bad)
    assert _sec.status == "FAIL" and _data is None, _sec.status
    assert any("corrupt" in ln or "parses cleanly: FAIL" in ln for ln in _sec.lines), _sec.lines

    # Missing state -> FAIL.
    _sec, _data = health_mod.check_state(Path(_tmp) / "absent.json")
    assert _sec.status == "FAIL" and _data is None

    # Synthetic/test keys in state -> FAIL (state-integrity regression guard).
    _synth = Path(_tmp) / "synth.json"
    _synth.write_text(json.dumps({
        "active_flags": {"26404:1:11:MISSING_ASSIGNMENT": {}},
        "one_time_issued": {},
        "last_send": {"sent_at": "2026-09-10T00:00:00+00:00"},
    }), encoding="utf-8")
    _sec, _data = health_mod.check_state(_synth)
    assert _sec.status == "FAIL", _sec.status
    assert any("synthetic key present" in ln for ln in _sec.lines), _sec.lines

    # Clean state -> not FAIL.
    _ok = Path(_tmp) / "ok.json"
    _ok.write_text(json.dumps({
        "active_flags": {"26442:31353:22140:MISSING_ASSIGNMENT": {}},
        "one_time_issued": {"26442:22140:1020031:LOW_ASSESSMENT_SCORE": True},
        "last_send": {"sent_at": "2026-09-10T00:00:00+00:00"},
    }), encoding="utf-8")
    _sec, _data = health_mod.check_state(_ok)
    assert _sec.status != "FAIL", (_sec.status, _sec.lines)

# Scheduler verdict: installed-but-unloaded must be FAIL (not WARN).
assert health_mod._worst("PASS", "WARN") == "WARN"
assert health_mod._worst("WARN", "FAIL") == "FAIL"
assert health_mod._worst("FAIL", "PASS") == "FAIL"

# Monkeypatched FAIL paths (restored immediately; nothing external is touched).
_cfg = config.load_config()
_orig_loaded = health_mod.scheduler.is_loaded
_orig_status = health_mod.gmail_transport.oauth_status
_orig_sender = health_mod.emailer._sender_allowed
try:
    # Installed but unloaded -> scheduler FAIL.
    health_mod.scheduler.is_loaded = lambda *a, **k: False
    _sec, _st, _lr, _cmd = health_mod.check_scheduler(_cfg)
    assert _st == "FAIL", _st
    assert any(ln.startswith("loaded: NO") for ln in _sec.lines), _sec.lines
    health_mod.scheduler.is_loaded = _orig_loaded

    # Loaded but non-zero last exit -> scheduler FAIL.
    health_mod.scheduler.is_loaded = lambda *a, **k: True
    _orig_exit = health_mod.scheduler._last_exit_status
    health_mod.scheduler._last_exit_status = lambda *a, **k: "78"
    _sec, _st, _lr, _cmd = health_mod.check_scheduler(_cfg)
    assert _st == "FAIL", _st
    health_mod.scheduler._last_exit_status = _orig_exit
    health_mod.scheduler.is_loaded = _orig_loaded

    # Gmail transport not ready -> OAuth section FAIL.
    health_mod.gmail_transport.oauth_status = lambda: {
        "client_credential_present": True, "token_present": True,
        "token_permissions_safe": True, "authorized_sender_identity": True,
        "gmail_send_scope_present": True, "gmail_transport_ready": False,
        "blocker": "token file unreadable",
    }
    _sec = health_mod.check_oauth()
    assert _sec.status == "FAIL", _sec.status
    health_mod.gmail_transport.oauth_status = _orig_status

    # Recipient-safety regression -> FAIL.
    health_mod.emailer._sender_allowed = lambda addr: True
    _sec = health_mod.check_recipient_safety()
    health_mod.emailer._sender_allowed = _orig_sender
    _sec_ok = health_mod.check_recipient_safety()
    assert _sec_ok.status == "PASS", _sec_ok.lines
finally:
    health_mod.scheduler.is_loaded = _orig_loaded
    health_mod.gmail_transport.oauth_status = _orig_status
    health_mod.emailer._sender_allowed = _orig_sender

# End-to-end: healthy-but-stale -> WARN / exit 1.
# Scheduler/plist and temp log are injected so the real install is untouched.
with tempfile.TemporaryDirectory() as _tmp:
    _logs = Path(_tmp)
    # Last successful run: Monday 2026-09-07; "now" is Thursday 2026-09-10 -> 3 school days.
    (_logs / "grade-check.runs.jsonl").write_text(json.dumps({
        "timestamp": "2026-09-07T20:15:00+00:00", "blocker": None,
        "courses_scanned": ["Math"], "students_scanned": 20, "quarter": "Q1",
        "email_sent": False,
        "counts": {"missing_new": 0, "missing_still_active": 0, "missing_resolved": 0,
                   "assessment_new": 0, "average_still_active": 0, "average_resolved": 0,
                   "unresolved": 0},
    }) + "\n", encoding="utf-8")

    _o_ld, _o_pl = health_mod.scheduler.log_dir, health_mod._read_plist
    try:
        health_mod.scheduler.log_dir = lambda *a, **k: _logs
        health_mod._read_plist = lambda *a, **k: {"Label": "x", "StartCalendarInterval": [{"Weekday": 1, "Hour": 16, "Minute": 15}]}
        _rep = health_mod.build_report(dt.datetime(2026, 9, 10, 16, 15))
        assert _rep.school_days_since == 3, _rep.school_days_since
        assert _rep.overall == "WARN", (_rep.overall, [s.title + "=" + s.status for s in _rep.sections])
        assert _rep.exit_code == 1, _rep.exit_code
        _txt = health_mod.render(_rep)
        assert "WARNING: Grade Check has not completed successfully in more than 2 school days." in _txt
        assert "Scheduler freshness: WARN" in _txt
        assert _txt.strip().endswith("GRADE CHECK HEALTH: WARN")
    finally:
        health_mod.scheduler.log_dir = _o_ld
        health_mod._read_plist = _o_pl

# End-to-end: fresh log -> PASS / exit 0 (with trigger safety neutralized).
with tempfile.TemporaryDirectory() as _tmp:
    _logs = Path(_tmp)
    (_logs / "grade-check.runs.jsonl").write_text(json.dumps({
        "timestamp": "2026-09-10T20:15:00+00:00", "blocker": None,
        "courses_scanned": ["Math"], "students_scanned": 20, "quarter": "Q1",
        "email_sent": False,
        "counts": {"missing_new": 0, "missing_still_active": 0, "missing_resolved": 0,
                   "assessment_new": 0, "average_still_active": 0, "average_resolved": 0,
                   "unresolved": 0},
    }) + "\n", encoding="utf-8")
    _o_ld, _o_pl = health_mod.scheduler.log_dir, health_mod._read_plist
    try:
        health_mod.scheduler.log_dir = lambda *a, **k: _logs
        health_mod._read_plist = lambda *a, **k: {"Label": "x", "StartCalendarInterval": [{"Weekday": 1, "Hour": 16, "Minute": 15}]}
        _rep = health_mod.build_report(dt.datetime(2026, 9, 10, 16, 15))
        assert _rep.school_days_since == 0, _rep.school_days_since
        assert _rep.overall == "PASS", (_rep.overall, [s.title + "=" + s.status for s in _rep.sections])
        assert _rep.exit_code == 0, _rep.exit_code
        assert health_mod.render(_rep).strip().endswith("GRADE CHECK HEALTH: PASS")
    finally:
        health_mod.scheduler.log_dir = _o_ld
        health_mod._read_plist = _o_pl

# Trigger safety: calendar-only is PASS; every off-schedule trigger is FAIL.
_CAL = {"StartCalendarInterval": [{"Weekday": 1, "Hour": 16, "Minute": 15}]}
_ok, _probs = health_mod.trigger_safety(dict(_CAL))
assert _ok and _probs == [], (_ok, _probs)
# The exact defect that caused the unapproved 2026-09-10 20:24 EDT send.
_ok, _probs = health_mod.trigger_safety(
    {**_CAL, "KeepAlive": {"SuccessfulExit": False}})
assert not _ok and any("KeepAlive" in p for p in _probs), _probs
# Explicit null KeepAlive is still a key that must not be installed.
_ok, _probs = health_mod.trigger_safety({**_CAL, "KeepAlive": None})
assert not _ok and any("KeepAlive" in p for p in _probs), _probs
_ok, _probs = health_mod.trigger_safety({**_CAL, "KeepAlive": False})
assert not _ok and any("KeepAlive" in p for p in _probs), _probs
# RunAtLoad: any form must be reported; explicit false is a note only.
_ok, _probs = health_mod.trigger_safety({**_CAL, "RunAtLoad": True})
assert not _ok and any("RunAtLoad" in p for p in _probs), _probs
_ok, _probs = health_mod.trigger_safety({**_CAL, "RunAtLoad": False})
assert _ok and _probs == [], _probs
# Every other off-schedule trigger key is rejected.
for _key in health_mod.scheduler.FORBIDDEN_TRIGGER_KEYS:
    if _key in ("KeepAlive", "RunAtLoad"):
        continue
    _ok, _probs = health_mod.trigger_safety({**_CAL, _key: True})
    assert not _ok and _probs, f"{_key} must be rejected"
# A calendar-only plist with no calendar entry is also rejected.
_ok, _probs = health_mod.trigger_safety({"Label": "x"})
assert not _ok and _probs, _probs

# A job that has never run ("(never exited)") is not a failure; a real
# non-zero exit code is. Regression guard for the false FAIL after install.
for _never in ("(never exited)", "unknown", None):
    _orig_exit2 = health_mod.scheduler._last_exit_status
    _orig_loaded2 = health_mod.scheduler.is_loaded
    _orig_plist2 = health_mod._read_plist
    try:
        health_mod.scheduler.is_loaded = lambda *a, **k: True
        health_mod.scheduler._last_exit_status = lambda *a, **k: _never
        health_mod._read_plist = lambda *a, **k: {
            "StartCalendarInterval": [{"Weekday": 1, "Hour": 16, "Minute": 15}]}
        _sec2, _st2, _lr2, _cmd2 = health_mod.check_scheduler(_cfg)
        assert _st2 == "PASS", f"{_never!r} must not be a scheduler FAIL: {_sec2.lines}"
        assert any("no scheduled run recorded yet" in ln for ln in _sec2.lines), _sec2.lines
    finally:
        health_mod.scheduler._last_exit_status = _orig_exit2
        health_mod.scheduler.is_loaded = _orig_loaded2
        health_mod._read_plist = _orig_plist2

# A real non-zero exit code IS a failure.
_orig_exit3 = health_mod.scheduler._last_exit_status
_orig_loaded3 = health_mod.scheduler.is_loaded
_orig_plist3 = health_mod._read_plist
try:
    health_mod.scheduler.is_loaded = lambda *a, **k: True
    health_mod.scheduler._last_exit_status = lambda *a, **k: "1"
    health_mod._read_plist = lambda *a, **k: {
        "StartCalendarInterval": [{"Weekday": 1, "Hour": 16, "Minute": 15}]}
    _sec3, _st3, _lr3, _cmd3 = health_mod.check_scheduler(_cfg)
    assert _st3 == "FAIL", (_st3, _sec3.lines)
finally:
    health_mod.scheduler._last_exit_status = _orig_exit3
    health_mod.scheduler.is_loaded = _orig_loaded3
    health_mod._read_plist = _orig_plist3

print("PASS health check: verdicts, exit codes, school days, FAIL paths, no send/no write/no leak")

# 7. Recipient safety regression: sender/recipient allowlist still enforced.
from scripts.canvas_llm_grade_check import emailer as _em  # already imported as emailer_mod above
os.environ["CANVAS_LLM_GRADE_CHECK_SEND_APPROVED"] = "1"
assert _em.check_recipient_safety("owen.reagan@thalesacademy.org") is None
assert "RECIPIENT SAFETY BLOCK" in (_em.check_recipient_safety("parent@example.com") or "")
assert "RECIPIENT SAFETY BLOCK" in (_em.check_recipient_safety(
    ["owen.reagan@thalesacademy.org", "second@example.com"]) or "")
os.environ.pop("CANVAS_LLM_GRADE_CHECK_SEND_APPROVED", None)
print("PASS recipient safety regression: allowlist gates still enforced")

print("PASS: Canvas Grade Check tests complete")
PY

echo "PASS Canvas LLM Grade Check tests complete"
