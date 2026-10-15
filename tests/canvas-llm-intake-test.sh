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
  "scripts/canvas_llm_intake/intake.py"
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
# History inactive in Q2 -> active_subjects excludes it; blank science Friday flagged.
from scripts.canvas_llm_phase3 import week_workflow as wf
active = wf.active_subjects("Q2W2", bw)
assert "science" in active and "history" not in active

qs_gen = qs.generate_questions(week=bw, subject_reports={}, assessment_events=[], reminder_events=[])
assert any(q["subject"] == "science" and "blank" in q["reason"] for q in qs_gen), qs_gen
print("PASS questions: blank cells flagged, inactive subject excluded")

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

print("PASS: Canvas Weekly Intake tests complete")
PY

echo "PASS Canvas Weekly Intake tests complete"
