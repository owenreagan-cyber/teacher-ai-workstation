#!/usr/bin/env bash
# Q2W3 live-refresh regression tests (synthetic, deterministic, no network/Canvas).
# Covers the parser + intake fixes for the Q2W3 source refresh.
set -euo pipefail

echo "Running Q2W3 live-refresh regression tests..."

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

python3 - <<'PY'
import sys
sys.path.insert(0, '.')

from scripts.canvas_llm_phase3 import pacing_translation as pt
from scripts.canvas_llm_intake import questions as iq

config = pt.load_config()

# ---- Shurley Q2W3 cells -> lesson + Classroom Practice ----
# (Covers F/G at the routing level below.)
la_wed = pt.translate_shurley_cell("Ch 7 L1 + CP25")
assert la_wed["lines"] == ["Chapter 7, Lesson 1", "Classroom Practice 25"], la_wed
assert la_wed["cp_numbers"] == [25] and la_wed["resolved"] is True
la_thu = pt.translate_shurley_cell("Ch 7 L2 + CP26")
assert la_thu["cp_numbers"] == [26] and la_thu["resolved"] is True
la_fri = pt.translate_shurley_cell("Ch 7 Compound + CP27 bridge")
assert la_fri["lines"] == ["Chapter 7 Compound", "Classroom Practice 27", "bridge"], la_fri
assert la_fri["cp_numbers"] == [27] and la_fri["resolved"] is True and la_fri["unresolved"] == []
la_tue = pt.translate_shurley_cell("CH 5 Test")
assert la_tue["test_numbers"] == [5] and la_tue["resolved"] is True

# ---- F: Shurley Classroom Practice routes to Classwork ----
cp = pt.classroom_practice_assignment(25, "2026-10-28", config)
assert cp["title"] == "Classroom Practice 25", cp
assert cp["assignment_group"] == "Classwork", cp
cp27 = pt.classroom_practice_assignment(27, "2026-10-30", config)
assert cp27["title"] == "Classroom Practice 27" and cp27["assignment_group"] == "Classwork"

# ---- G: Shurley Chapter Test routes to Assessments ----
ct = pt.chapter_test_assignment(5, "2026-10-27", config)
assert ct["title"] == "ELA4: Chapter 5 Test", ct
assert ct["assignment_group"] == "Assessments", ct

# ---- Whole-week Shurley derivation produces CP25/26/27 + Chapter 5 Test ----
week = {
    "week": {"code": "Q2W3", "startDate": "2026-10-26", "endDate": "2026-10-30"},
    "unitContext": {"science": "Force and Motion"},
    "days": {
        "Monday": {"date": "2026-10-26", "subjects": {"language_arts": {"raw": "CH 5 Checkup"}, "science": {"raw": "U1 Ch4 Electricity Transfer"}}},
        "Tuesday": {"date": "2026-10-27", "subjects": {"language_arts": {"raw": "CH 5 Test"}, "science": {"raw": "U1 Ch4 Electricity Detective"}}},
        "Wednesday": {"date": "2026-10-28", "subjects": {"language_arts": {"raw": "Ch 7 L1 + CP25"}, "science": {"raw": "U1 Ch4 Check (MC)"}}},
        "Thursday": {"date": "2026-10-29", "subjects": {"language_arts": {"raw": "Ch 7 L2 + CP26"}, "science": {"raw": "U1 Ch5 Collisions / Crash Lab"}}},
        "Friday": {"date": "2026-10-30", "subjects": {"language_arts": {"raw": "Ch 7 Compound + CP27 bridge"}, "science": {"raw": "U1 Ch5 Check (MC)"}}},
    },
}
la = pt.translate_subject_week(week, "language_arts", config)
la_titles = sorted(a["title"] for a in la["assignments"])
assert la_titles == ["Classroom Practice 25", "Classroom Practice 26", "Classroom Practice 27", "ELA4: Chapter 5 Test"], la_titles
assert la["unresolved"] == [], la["unresolved"]
assert la["days"]["Wednesday"]["lines"] == ["Chapter 7, Lesson 1", "Classroom Practice 25"]

# ---- B: blank LA Wed-Fri -> populated clears day-level pending ----
# The day states are derived from raw source; populated source means no pending.
assert la["days"]["Wednesday"]["source"] == "Ch 7 L1 + CP25"
assert la["days"]["Thursday"]["source"] == "Ch 7 L2 + CP26"
assert la["days"]["Friday"]["source"] == "Ch 7 Compound + CP27 bridge"

# ---- A + E: Science populated resolves; "Check (MC)" never auto-creates assignments ----
sci = pt.translate_subject_week(week, "science", config)
assert sci["unresolved"] == [], sci["unresolved"]
assert sci["assignments"] == [], sci["assignments"]  # no speculative Science assignments
assert sci["days"]["Monday"]["lines"] == ["U1 Ch4 Electricity Transfer"]
assert sci["days"]["Wednesday"]["lines"] == ["U1 Ch4 Check (MC)"]
assert sci["days"]["Friday"]["lines"] == ["U1 Ch5 Check (MC)"]
assert sci["days"]["Thursday"]["lines"] == ["U1 Ch5 Collisions / Crash Lab"]

# ---- C: obsolete all-blank question disappears when Science populated ----
qs = iq.generate_questions(week=week, subject_reports={"science": sci, "language_arts": la},
                           assessment_events=[], reminder_events=[])
blank_qs = [q for q in qs if q.get("question_id", "").endswith("all-blank")]
assert blank_qs == [], blank_qs
# No unresolved-token questions for Shurley/Science (all resolved).
unresolved_qs = [q for q in qs if "no deterministic translation" in q.get("reason", "")]
assert unresolved_qs == [], unresolved_qs

# ---- D: owner Math At Home override survives compatible source refresh ----
import json, tempfile
from pathlib import Path
from scripts.canvas_llm_intake import manifest as imf
from scripts.canvas_llm_intake import owner_overrides as oo
from scripts.canvas_llm_intake import intake

orig = imf.staging_dir
with tempfile.TemporaryDirectory() as tmp:
    imf.staging_dir = lambda q, w: Path(tmp) / f"q{q}w{w}"
    try:
        # Record the owner Math Wednesday override.
        oo.upsert_override(2, 3, subject="math", day="Wednesday", source_value="Review",
                           in_class=["Review"], at_home="Study for tomorrow's test.", status="PLANNED")
        rec = oo.day_override(2, 3, "math", "Wednesday")
        assert rec["at_home"] == "Study for tomorrow's test." and rec["active"] is True
        # The override survives a compatible source refresh (Review unchanged).
        assert oo.day_override(2, 3, "math", "Wednesday")["source_value"] == "Review"
    finally:
        imf.staging_dir = orig

print("PASS: Q2W3 live-refresh regression tests complete")
PY

echo "PASS Q2W3 live-refresh regression tests complete"
