#!/usr/bin/env bash
set -euo pipefail

echo "Running Canvas LLM pacing translation and weekly reminders tests..."

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

ENGINE="scripts/canvas_llm_phase23/phase23_content_engine.py"
PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/teacher-ai-workstation-pycache" python3 -m py_compile "$ENGINE"

python3 - <<'PY'
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path('.').resolve()))
from scripts.canvas_llm_phase23 import phase23_content_engine as p23

# 1. Known Shurley shorthand is translated before student-facing rendering.
assert p23.translate_student_facing_pacing("CP6") == ("Classroom Practice 6", True)
assert p23.translate_student_facing_pacing("2.3") == ("Chapter 2, Lesson 3", True)
assert p23.translate_student_facing_pacing("Ch.2.3") == ("Chapter 2, Lesson 3", True)
assert p23.translate_student_facing_pacing("CP6 / 2.3") == (
    "Classroom Practice 6 / Chapter 2, Lesson 3",
    True,
)
assert p23.student_facing_subject_title("language-arts", "CP6") == "ELA4: Classroom Practice 6"
assert p23.student_facing_subject_title("language-arts", "Ch.2.3") == "ELA4: Chapter 2, Lesson 3"
print("PASS known Shurley shorthand is translated before student-facing rendering")

# 2. MTS renders as Mountains.
assert p23.translate_student_facing_pacing("MTS Ch1") == ("Mountains Chapter 1", True)
assert p23.student_facing_subject_title("history", "MTS Ch1") == "Mountains Chapter 1"
assert p23.translate_student_facing_pacing("MTS Ch2") == ("Mountains Chapter 2", True)
print("PASS MTS renders as Mountains")

# 3. Unknown shorthand is not guessed.
unknown_text, unknown_resolved = p23.translate_student_facing_pacing("XYZ9")
assert unknown_resolved is False
assert unknown_text == "XYZ9"
assert p23.translate_student_facing_pacing("QRS")[1] is False
assert p23.translate_student_facing_pacing("CP6 / QRS")[1] is False
print("PASS unknown shorthand is not guessed")

# 4. Active weekly pages cannot render with an empty Reminders section.
packet = p23.build_packet("Q1W5")
assert packet["validation"]["failCount"] == 0
for page in packet["pages"]:
    reminder_block = re.search(r"Reminders</h3>(.*?)</div>", page["body_html"], re.DOTALL)
    assert reminder_block is not None, f"{page['title']} missing Reminders heading"
    assert "<li>" in reminder_block.group(1), f"{page['title']} rendered an empty Reminders section"
print("PASS active weekly pages cannot render with an empty Reminders section")

# 5. No-assessment weeks receive a supported instructional-focus reminder.
week = p23.canonical_week("Q1W5")
no_assessment_rows = [
    {"subject": "math", "weekday": "Monday", "entry_date": "2026-08-17", "lesson": "18", "tests": "", "title": "Lesson 18", "in_class": "Lesson 18", "at_home": "Evens"},
    {"subject": "math", "weekday": "Tuesday", "entry_date": "2026-08-18", "lesson": "19", "tests": "", "title": "Lesson 19", "in_class": "Lesson 19", "at_home": "Odds"},
]
html = p23.render_page_html(week, no_assessment_rows, "math")
assert "This week we will continue working through Lessons 18" in html
assert "<li>" in html
print("PASS no-assessment weeks receive a supported instructional-focus reminder")

# 6. Inactive/blank Science remains untouched.
assert p23.subject_active_for_week("science", week) is False
assert all(page["subject_group"] != "science" for page in packet["pages"])
print("PASS inactive/blank Science remains untouched")

# Demo packet validation confirms every page passes the reminders-present check.
demo = p23.build_packet("Q1W5")
reminder_findings = [
    item for item in demo["validation"]["findings"]
    if item["code"] == "page.reminders-present"
]
assert reminder_findings and all(item["severity"] == "pass" for item in reminder_findings)
print("PASS packet validation enforces non-empty Reminders")
PY

echo "PASS: Canvas LLM pacing translation and weekly reminders tests complete"
