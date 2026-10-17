#!/usr/bin/env bash
# Deterministic Canvas Weekly Intake tests (synthetic fixture, no Canvas, no network).
set -euo pipefail

echo "Running Canvas Weekly Intake tests..."

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

MODULES=(
  "scripts/canvas_llm_intake/__init__.py"
  "scripts/canvas_llm_intake/constants.py"
  "scripts/canvas_llm_intake/manifest.py"
  "scripts/canvas_llm_intake/week_resolution.py"
  "scripts/canvas_llm_intake/questions.py"
  "scripts/canvas_llm_intake/canvas_readonly.py"
  "scripts/canvas_llm_intake/teacher_input.py"
  "scripts/canvas_llm_intake/approval.py"
  "scripts/canvas_llm_intake/reminders.py"
  "scripts/canvas_llm_intake/scheduling.py"
  "scripts/canvas_llm_intake/owner_overrides.py"
  "scripts/canvas_llm_intake/intake.py"
  "scripts/canvas_llm_intake/cycle.py"
  "scripts/canvas_llm_intake/cli.py"
  "scripts/canvas_llm_intake/status.py"
)
PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/teacher-ai-workstation-pycache" python3 -m py_compile "${MODULES[@]}"

python3 - <<'PY'
import json
import sys
import tempfile
from pathlib import Path

root = Path('.').resolve()
sys.path.insert(0, str(root))

from scripts.canvas_llm_intake import constants as C
from scripts.canvas_llm_intake import manifest as mf
from scripts.canvas_llm_intake import questions as qs
from scripts.canvas_llm_intake import intake
from scripts.canvas_llm_phase3 import pacing_extractor as pe

# ---------------------------------------------------------------------------
# 1. Course mapping + quarter rotation.
# ---------------------------------------------------------------------------
assert C.course_id_for_subject("math") == 26404
assert C.course_id_for_subject("reading") == 26442
assert C.course_id_for_subject("spelling") == 26442
assert C.course_id_for_subject("language-arts") == 28171
assert C.course_id_for_subject("science") == 28166
assert C.course_id_for_subject("history") == 28165
assert C.course_id_for_subject("homeroom") == 26429

# Q2 -> Science active; Q1 -> History active.
assert C.active_subject_keys_for_quarter(2) == ["math", "reading_spelling", "language_arts", "science"]
assert C.active_subject_keys_for_quarter(1) == ["math", "reading_spelling", "language_arts", "history"]
assert "homeroom" not in C.active_subject_keys_for_quarter(2)
print("PASS course mapping + quarter rotation")

# ---------------------------------------------------------------------------
# 2. Synthetic pacing fixture -> normalized week (blank preservation).
# ---------------------------------------------------------------------------
rows = [
    ["Subject:", "", "", "10/19/26", "10/20/26", "10/21/26", "10/22/26", "10/23/26"],
    ["", "", "", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
    ["Saxon Math", "5", "", "L41", "WA 5", "L42", "L43", "INV 4"],
    ["Reading Mastery", "4", "", "45", "46", "47", "48", "RMT+FCO"],
    ["Spelling", "4", "", "41", "42", "43", "Test", "review"],
    ["Shurley English", "4", "", "6.1", "6.1", "6.2", "6.2, CP22", "6.3"],
    ["History", "4", "", "", "", "", "", ""],
    ["Science", "4", "", "Ch. 3", "Ch. 3", "Ch. 4", "Ch. 4 Check", "Ch. 3-4 Review"],
    ["", "", "", "Science: Force and Motion", "", "", "", "", ""],
]
source = {"workbook": "test", "sheet": "4A - Reagan", "freshRead": False, "status": "SYNTHETIC"}
week = pe.extract_week(rows, "Q2W2", source)

assert week["week"]["startDate"] == "2026-10-19", week["week"]
assert week["week"]["endDate"] == "2026-10-23"
# Blanks remain blank.
assert week["days"]["Monday"]["subjects"]["history"]["raw"] == ""
assert week["days"]["Monday"]["subjects"]["history"]["blank"] is True
# Raw values preserved verbatim.
assert week["days"]["Tuesday"]["subjects"]["math"]["raw"] == "WA 5"
assert week["days"]["Thursday"]["subjects"]["language_arts"]["raw"] == "6.2, CP22"
print("PASS synthetic fixture normalizes + preserves blanks")

# ---------------------------------------------------------------------------
# 3. Subject translation produces assignments (Math WA, LA CP, Science none).
# ---------------------------------------------------------------------------
from scripts.canvas_llm_phase3 import pacing_math as pm
from scripts.canvas_llm_phase3 import pacing_translation as pt

math_report = pm.translate_math_week(week)
assert math_report["deterministic"] is True
# WA 5 on Tuesday -> a Written Assessment assignment.
assert any(a.get("title", "").startswith("SM5") or "Written Assessment" in a.get("title", "") for a in math_report["assignments"]), math_report["assignments"]

la_report = pt.translate_subject_week(week, "language_arts")
assert any(a.get("title") == "Classroom Practice 22" for a in la_report["assignments"]), la_report["assignments"]

sci_report = pt.translate_subject_week(week, "science")
assert sci_report["assignments"] == [], "Science must not auto-propose assignments for Check/Review"
print("PASS subject translation + assignment proposals")

# ---------------------------------------------------------------------------
# 4. Questions: blank History -> no History questions (History inactive Q2);
#    blank Science on a day -> question; unresolved token -> question.
# ---------------------------------------------------------------------------
def _blank_week():
    w = json.loads(json.dumps(week))
    w["days"]["Friday"]["subjects"]["science"]["raw"] = ""
    return w

bw = _blank_week()
# History inactive in Q2 -> active_subjects excludes it.
from scripts.canvas_llm_phase3 import week_workflow as wf
active = wf.active_subjects("Q2W2", bw)
assert "science" in active and "history" not in active

# Partial blank (only Friday blank) -> NO per-day blank question (collapse rule).
qs_partial = qs.generate_questions(week=bw, subject_reports={}, assessment_events=[], reminder_events=[])
assert not any(q["subject"] == "science" and "blank" in q["reason"] for q in qs_partial), qs_partial

# Full-week blank active subject -> exactly ONE subject-level question.
full_blank = json.loads(json.dumps(bw))
for d in full_blank["days"].values():
    d["subjects"]["science"]["raw"] = ""
qs_full = qs.generate_questions(week=full_blank, subject_reports={}, assessment_events=[], reminder_events=[])
sci_q = [q for q in qs_full if q["subject"] == "science"]
assert len(sci_q) == 1, sci_q
assert sci_q[0]["question_id"].endswith("all-blank"), sci_q
assert "completely blank" in sci_q[0]["reason"]
print("PASS questions: full-week blank collapses to one subject-level question; inactive subject excluded")

# ---------------------------------------------------------------------------
# 5. Manifest lifecycle: no auto-approval; monotonic; backward rejected.
# ---------------------------------------------------------------------------
m = mf.new_manifest(quarter=2, week=2, week_code="Q2W2",
                    date_range={"start": "2026-10-19", "end": "2026-10-23"})
mf.advance_status(m, "NORMALIZED")
mf.advance_status(m, "DRAFTED")
assert m["status"] == "DRAFTED"
assert m["approval_state"] == "PENDING"
try:
    mf.advance_status(m, "NORMALIZED")
    raise AssertionError("backward transition must be rejected")
except ValueError:
    pass
assert m["status"] != "TEACHER_APPROVED"
print("PASS manifest lifecycle: monotonic, no auto-approval")

# ---------------------------------------------------------------------------
# 6. Zero-write proof: intake package has no Canvas write verbs.
# ---------------------------------------------------------------------------
from scripts.canvas_llm_intake import status as status_mod
zw = status_mod._zero_write_proof()
assert zw["write_free"] is True, zw
print("PASS zero-write proof: no Canvas write verbs in intake package")

# ---------------------------------------------------------------------------
# 7. Page HTML render (kl_wrapper_3) + combined reading/spelling.
# ---------------------------------------------------------------------------
from scripts.canvas_llm_phase3 import canvas_preview as cp
days = {
    "Monday": {"in_class": ["Lesson 41", "Problems 1-10"], "at_home": ["Problems 12-30 Evens"]},
    "Tuesday": {"in_class": ["Written Assessment 5"], "at_home": None},
    "Wednesday": {"in_class": ["Lesson 42"], "at_home": ["Problems 11-29 Odds"]},
    "Thursday": {"in_class": ["Lesson 43"], "at_home": None},
    "Friday": {"in_class": ["Investigation 4"], "at_home": None},
}
html = cp.build_agenda_html("Q2W2", days, reminders=["Written Assessment 5 — Thursday, October 20"])
assert 'id="kl_wrapper_3"' in html
assert "Written Assessment 5" in html
print("PASS page HTML render (kl_wrapper_3)")

# ---------------------------------------------------------------------------
# 8. Reading bare-number + prefixed + Lesson forms + blank + unknown.
# ---------------------------------------------------------------------------
from scripts.canvas_llm_phase3 import pacing_reading as prd2
assert prd2.parse_reading_token("41")["translation"] == "Lesson 41"
assert prd2.parse_reading_token("L41")["translation"] == "Lesson 41"
assert prd2.parse_reading_token("Lesson 41")["translation"] == "Lesson 41"
assert prd2.parse_reading_token("")["kind"] == "blank"
assert prd2.parse_reading_token("Rotations")["kind"] == "unknown"
# Ambiguous numeric-looking content that must NOT be coerced: "RMT+FCO" is rmt_fco.
assert prd2.parse_reading_token("RMT+FCO")["kind"] == "rmt_fco"
print("PASS reading bare-number + prefixed + Lesson forms + blank + unknown")

# ---------------------------------------------------------------------------
# 9. Math FA6* marker preservation (identifier parsed, marker UNKNOWN).
# ---------------------------------------------------------------------------
from scripts.canvas_llm_phase3 import pacing_math as pm2
combined = pm2.parse_math_tokens("WA6/ FA6*")
kinds = [t["kind"] for t in combined["tokens"]]
assert kinds == ["written_assessment", "fact_assessment"], kinds
assert combined["tokens"][1]["number"] == 6
assert combined["markers"] and combined["markers"][0]["meaning"] == "UNKNOWN"
print("PASS math FA6* marker preservation (identifier parsed, marker UNKNOWN)")

# ---------------------------------------------------------------------------
# 10. Teacher input: answer question, reject assignment, source untouched,
#     deterministic regeneration.
# ---------------------------------------------------------------------------
import scripts.canvas_llm_intake.manifest as mf2
import scripts.canvas_llm_intake.teacher_input as ti2
import scripts.canvas_llm_intake.questions as qs2
import tempfile

_mf_orig = mf2.staging_dir
try:
    _tmp = tempfile.mkdtemp()
    def _tmp_dir(q, w):
        return Path(_tmp) / f"q{q}w{w}"
    mf2.staging_dir = _tmp_dir

    ti2.answer_question(2, 2, 1, "Interpret as Lesson 41")
    ti2.apply_input(quarter=2, week=2, subject="math", op="reject_assignment", value="SM5: Lesson 36 Homework")
    data = ti2.load_input(2, 2)
    assert data["question_answers"]["1"]["answer"] == "Interpret as Lesson 41"
    assert "SM5: Lesson 36 Homework" in data["subjects"]["math"]["reject_assignments"]
    print("PASS teacher input: answer + reject + deterministic store")
finally:
    mf2.staging_dir = _mf_orig

# ---------------------------------------------------------------------------
# 10b. Owner overrides: create / edit / restore / mark blank+ pending, with
#      audit history and fail-closed status validation.
# ---------------------------------------------------------------------------
import scripts.canvas_llm_intake.owner_overrides as oo2
_oo_orig = mf2.staging_dir
try:
    _oo_tmp = tempfile.mkdtemp()
    mf2.staging_dir = lambda q, w: Path(_oo_tmp) / f"q{q}w{w}"
    oo2.upsert_override(2, 3, subject="math", day="Wednesday", source_value="Review",
                        in_class=["Review"], at_home="Study for tomorrow's test.", status="PLANNED")
    rec = oo2.day_override(2, 3, "math", "Wednesday")
    assert rec["at_home"] == "Study for tomorrow's test." and rec["source"] == "OWNER_INPUT"
    assert len(rec["history"]) == 1
    # edit (not duplicate)
    oo2.upsert_override(2, 3, subject="math", day="Wednesday", at_home="Study harder.")
    assert oo2.day_override(2, 3, "math", "Wednesday")["at_home"] == "Study harder."
    # mark blank / pending
    oo2.mark_blank(2, 3, "science", "Monday")
    oo2.mark_pending(2, 3, "language_arts", "Wednesday")
    assert oo2.day_override(2, 3, "science", "Monday")["status"] == "OWNER_CONFIRMED_BLANK"
    assert oo2.day_override(2, 3, "language_arts", "Wednesday")["status"] == "PENDING_SOURCE"
    # restore source deactivates
    assert oo2.restore_source(2, 3, "math", "Wednesday") is True
    assert oo2.day_override(2, 3, "math", "Wednesday") is None
    # invalid status fails closed
    try:
        oo2.upsert_override(2, 3, subject="math", day="Monday", status="BOGUS")
        raise AssertionError("expected ValueError")
    except ValueError:
        pass
    print("PASS owner overrides: create/edit/restore/blank/pending + history + fail-closed")
finally:
    mf2.staging_dir = _oo_orig

# ---------------------------------------------------------------------------
# 11. Approval: explicit approval, hash binding, invalidation, gate.
# ---------------------------------------------------------------------------
import scripts.canvas_llm_intake.approval as ap2
_ap_orig = mf2.staging_dir
try:
    mf2.staging_dir = _tmp_dir
    subjects = ["math", "reading_spelling", "language_arts", "science"]
    ap2.set_state(2, 2, "math", "page", "APPROVED", draft_hash="h_page", subjects=subjects)
    data = ap2.load_approvals(2, 2, subjects)
    assert data["subjects"]["math"]["page"]["state"] == "APPROVED"
    # Stale hash invalidates.
    assert ap2.invalidate_if_stale(data, subject="math", draft_hashes={"page": "changed"}) is True
    assert data["subjects"]["math"]["page"]["state"] == "PENDING"
    # Partial approval -> NOT ready.
    artifacts = {s: {"page", "assignments", "announcement"} for s in subjects}
    ready, blockers = ap2.ready_to_publish(data, subjects=subjects, has_blocking_questions=False, artifacts=artifacts)
    assert ready is False
    # assessment_reminder granularity exists.
    assert "assessment_reminder" in ap2.GRANULARITIES
    print("PASS approval: hash binding + invalidation + gate + assessment_reminder granularity")
finally:
    mf2.staging_dir = _ap_orig

# ---------------------------------------------------------------------------
# 11b. Approval Phase 3: OWNER_UI provenance, source-hash binding, revoke,
#      history, NOT_REQUIRED, targeted invalidation, gate recalculation.
# ---------------------------------------------------------------------------
import scripts.canvas_llm_intake.approval as ap3
_ap3_orig = mf2.staging_dir
try:
    _ap3_tmp = tempfile.mkdtemp()
    mf2.staging_dir = lambda q, w: Path(_ap3_tmp) / f"q{q}w{w}"
    subjects = ["math", "reading_spelling", "language_arts", "science"]

    # approve_artifact records OWNER_UI + draft hash + source hash + history.
    ap3.approve_artifact(2, 3, "math", "page", draft_hash="h_page", source_hash="s1", subjects=subjects)
    data = ap3.load_approvals(2, 3, subjects)
    rec = data["subjects"]["math"]["page"]
    assert rec["state"] == "APPROVED" and rec["approved_by"] == "OWNER_UI"
    assert rec["draft_hash"] == "h_page" and rec["source_hash"] == "s1"
    assert len(rec["history"]) == 1 and rec["history"][0]["action"] == "set_approved"

    # Targeted invalidation: unrelated subject approval preserved when math changes.
    ap3.approve_artifact(2, 3, "reading_spelling", "announcement", draft_hash="h_r", source_hash="s1", subjects=subjects)
    data = ap3.load_approvals(2, 3, subjects)
    assert ap3.invalidate_if_stale(data, subject="math", draft_hashes={"page": "changed"}) is True
    assert data["subjects"]["math"]["page"]["state"] == "PENDING"
    assert data["subjects"]["reading_spelling"]["announcement"]["state"] == "APPROVED"
    assert data["subjects"]["math"]["page"]["history"][-1]["action"] == "invalidated"

    # Source-hash change invalidates (even when draft hash unchanged).
    ap3.approve_artifact(2, 3, "math", "page", draft_hash="h_page", source_hash="s1", subjects=subjects)
    data = ap3.load_approvals(2, 3, subjects)
    assert ap3.invalidate_if_stale(data, subject="math", draft_hashes={"page": "h_page"}, source_hash="s2") is True
    assert data["subjects"]["math"]["page"]["state"] == "PENDING"

    # Revoke: removes active approval, preserves history.
    ap3.approve_artifact(2, 3, "math", "announcement", draft_hash="h_a", source_hash="s1", subjects=subjects)
    ap3.revoke_approval(2, 3, "math", "announcement", subjects=subjects)
    data = ap3.load_approvals(2, 3, subjects)
    assert data["subjects"]["math"]["announcement"]["state"] == "PENDING"
    assert data["subjects"]["math"]["announcement"]["history"][-1]["action"] == "revoke"

    # NOT_REQUIRED satisfies the gate (owner-confirmed blank).
    ap3.mark_not_required(2, 3, "science", "page", subjects=subjects)
    ap3.mark_not_required(2, 3, "science", "announcement", subjects=subjects)
    data = ap3.load_approvals(2, 3, subjects)
    assert data["subjects"]["science"]["page"]["state"] == "NOT_REQUIRED"
    artifacts = {s: {"page", "announcement"} for s in subjects}
    ready, blockers = ap3.ready_to_publish(data, subjects=subjects,
                                           has_blocking_questions=False, artifacts=artifacts)
    assert "science:page" not in blockers and "science:announcement" not in blockers

    # Approval history is non-empty and newest-first.
    hist = ap3.approval_history(2, 3, subjects)
    assert len(hist) > 0
    assert hist[0]["at"] >= hist[-1]["at"]

    print("PASS approval Phase 3: OWNER_UI provenance, source binding, revoke, history, NOT_REQUIRED, targeted invalidation")
finally:
    mf2.staging_dir = _ap3_orig

# ---------------------------------------------------------------------------
# 11c. Draft-hash coupling: assignment bundle hash + announcement/page coupling.
# ---------------------------------------------------------------------------
import scripts.canvas_llm_intake.intake as inth
_active = ["math", "science"]
_assn_a = [{"course": "math", "title": "SM5: Lesson 41 Homework", "due_date": "2026-10-19"}]
_assn_b = _assn_a + [{"course": "math", "title": "SM5: Lesson 42 Homework", "due_date": "2026-10-20"}]
_ann = [{"course": "Math", "title": "Math Canvas Weekly Update", "agenda_hash": "pagehash-1"}]
_pages = {"math": {"agenda_hash": "pagehash-1"}}
_rem = []

# Assignment bundle hash: adding an assignment changes the bundle hash.
h1 = inth._draft_hashes(_active, {}, _assn_a, _ann, _pages, _rem)["math"]["assignments"]
h2 = inth._draft_hashes(_active, {}, _assn_b, _ann, _pages, _rem)["math"]["assignments"]
assert h1 != h2, "assignment bundle hash must change when a member is added"
# Unrelated subject unaffected: science page hash independent of math assignments.
s1 = inth._draft_hashes(_active, {}, _assn_a, _ann, _pages, _rem)["science"]["page"]
s2 = inth._draft_hashes(_active, {}, _assn_b, _ann, _pages, _rem)["science"]["page"]
assert s1 == s2, "unrelated subject hash must not change"
# Page/announcement coupling: page body change changes both page + announcement hash.
pages_v2 = {"math": {"agenda_hash": "pagehash-2"}}
ann_v2 = [{"course": "Math", "title": "Math Canvas Weekly Update", "agenda_hash": "pagehash-2"}]
m_page1 = inth._draft_hashes(_active, {}, _assn_a, _ann, _pages, _rem)["math"]["page"]
m_page2 = inth._draft_hashes(_active, {}, _assn_a, ann_v2, pages_v2, _rem)["math"]["page"]
m_ann1 = inth._draft_hashes(_active, {}, _assn_a, _ann, _pages, _rem)["math"]["announcement"]
m_ann2 = inth._draft_hashes(_active, {}, _assn_a, ann_v2, pages_v2, _rem)["math"]["announcement"]
assert m_page1 != m_page2, "page hash must change when page body changes"
assert m_ann1 != m_ann2, "announcement hash must change when embedded page body changes"
print("PASS draft-hash coupling: assignment bundle + page/announcement coupling")


# ---------------------------------------------------------------------------
# 12. Scheduling semantics (active-feed based — the verified Q2W2 finding).
# ---------------------------------------------------------------------------
import scripts.canvas_llm_intake.scheduling as sched2
from datetime import datetime, timezone
_now = datetime(2026, 10, 16, 12, 0, tzinfo=timezone.utc)
_future = "2026-10-16T20:00:00Z"
_past = "2026-10-15T20:00:00Z"
# A. published=true + future delayed + NOT active -> HELD (not a failure).
assert sched2.classify_announcement(delayed_post_at=_future, posted_at="2026-10-16T01:09:48Z",
                                    published=True, in_active_feed=False, now=_now) == sched2.HELD_SCHEDULED
# posted_at == created_at is NOT early publication.
assert sched2.classify_announcement(delayed_post_at=_future, posted_at="2026-10-16T01:09:48Z",
                                    published=True, in_active_feed=False, now=_now) == sched2.HELD_SCHEDULED
# B. future delayed + active -> PREMATURE (FAIL).
assert sched2.classify_announcement(delayed_post_at=_future, posted_at=None,
                                    published=True, in_active_feed=True, now=_now) == sched2.PREMATURE_LIVE
# C. past delayed + active -> POSTED (PASS).
assert sched2.classify_announcement(delayed_post_at=_past, posted_at=_past,
                                    published=True, in_active_feed=True, now=_now) == sched2.POSTED
# D. published=false + not active + no schedule -> DRAFT_UNPUBLISHED (not a failure).
assert sched2.classify_announcement(delayed_post_at=None, posted_at=None,
                                    published=False, in_active_feed=False, now=_now) == sched2.DRAFT_UNPUBLISHED
print("PASS scheduling semantics: active-feed hold/early/posted/draft classification")

# ---------------------------------------------------------------------------
# 13. Assessment reminder generation + Fact Assessment -> Power Up.
# ---------------------------------------------------------------------------
import scripts.canvas_llm_intake.reminders as rem2
r = rem2.resolve_fact_test(6)
assert r["powerUpCode"] == "B", r
assert rem2.resolve_fact_test(999) is None, "missing map entry must fail closed"
week_spelling = {
    "week": {"code": "Q2W2"},
    "days": {"Friday": {"date": "2026-10-23", "subjects": {"spelling": {"raw": "Test 40"}}}},
}
s_rem = rem2.draft_spelling_reminders(week_spelling)
assert len(s_rem) == 1 and s_rem[0]["test_number"] == 40
assert "Lists 1\u201340" in s_rem[0]["body"]
# No spelling test -> no reminder.
assert rem2.draft_spelling_reminders({"week": {"code": "Q2W3"}, "days": {}}) == []
print("PASS assessment reminders: Fact Assessment Power Up + Spelling reminder + fail-closed")

# ---------------------------------------------------------------------------
# 14. Cycle delta detection (NEW / UNCHANGED / CHANGED).
# ---------------------------------------------------------------------------
import scripts.canvas_llm_intake.cycle as cyc
import scripts.canvas_llm_intake.manifest as mfcyc
_cyc_orig = mfcyc.staging_dir
try:
    _cyc_tmp = tempfile.mkdtemp()
    mfcyc.staging_dir = lambda q, w: Path(_cyc_tmp) / f"q{q}w{w}"
    week3 = {
        "week": {"code": "Q2W3"},
        "days": {"Monday": {"date": "2026-10-26", "subjects": {"math": {"raw": "L41"}}}},
    }
    assert cyc.detect_delta(2, 3, week3)["delta"] == "NEW"
    m3 = mfcyc.new_manifest(quarter=2, week=3, week_code="Q2W3", date_range={"start": "x", "end": "y"})
    m3["source_hash"] = "beef"
    mfcyc.save_manifest(2, 3, m3)
    assert cyc.detect_delta(2, 3, week3)["delta"] == "CHANGED"
    fresh_hash = cyc.detect_delta(2, 3, week3)["fresh_hash"]
    m3["source_hash"] = fresh_hash
    mfcyc.save_manifest(2, 3, m3)
    assert cyc.detect_delta(2, 3, week3)["delta"] == "UNCHANGED"
    print("PASS cycle: NEW/UNCHANGED/CHANGED delta detection")
finally:
    mfcyc.staging_dir = _cyc_orig

print("PASS: Canvas Weekly Intake tests complete")
PY

echo "PASS Canvas Weekly Intake tests complete"
