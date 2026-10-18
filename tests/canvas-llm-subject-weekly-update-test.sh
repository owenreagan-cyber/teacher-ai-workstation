#!/usr/bin/env bash
set -euo pipefail

echo "Running Canvas LLM subject Weekly Update Announcement tests..."

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

MODULE="scripts/canvas_llm_phase22/subject_weekly_update.py"
DRIVER="scripts/canvas-llm/q1w7_subject_weekly_announcements.py"
PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/teacher-ai-workstation-pycache" python3 -m py_compile "$MODULE" "$DRIVER"

python3 - <<'PY'
import json
import sys
from pathlib import Path

root = Path('.').resolve()
sys.path.insert(0, str(root))
from scripts.canvas_llm_phase22 import subject_weekly_update as swu

# 1. Canonical titles and subject labels are persisted.
assert swu.SUBJECTS["math"]["title"] == "Math Canvas Weekly Update"
assert swu.SUBJECTS["reading_spelling"]["title"] == "Reading/Spelling Canvas Weekly Update"
assert swu.SUBJECTS["language_arts"]["title"] == "Language Arts Canvas Weekly Update"
assert swu.SUBJECTS["history"]["title"] == "History Canvas Weekly Update"
assert swu.SUBJECTS["science"]["title"] == "Science Canvas Weekly Update"
print("PASS canonical subject titles are persisted")

# 2. Message shell order: greeting -> review -> ahead -> (change) -> transition -> agenda -> closing.
fake = (
    swu.CSS + "\n"
    + '<div id="kl_wrapper_3" class="kl_circle_left kl_wrapper" style="border-style: none;">'
    + '<p>Quarter 1, Week 7 | August 31\u2013September 4, 2026</p></div>\n'
    + swu.JS
)
msg = swu.build_message(
    "math",
    "We had a great week in Math!",
    "Next week, we will continue with Lessons 21\u201325.",
    fake,
)
core = swu.agenda_core(fake)
assert msg.index(swu.GREETING) < msg.index("We had a great week in Math!") < msg.index("Next week")
assert msg.index("Next week") < msg.index("The Canvas Math page has been updated")
assert msg.index("The Canvas Math page has been updated") < msg.index(core)
assert msg.index(core) < msg.index(swu.CLOSING)
print("PASS announcement shell order is enforced")

# 3. Embedded agenda is byte-identical to the front-page kl_wrapper_3 block (no regeneration).
assert core in msg
assert core.startswith('<div id="kl_wrapper_3"')
assert "canvas_global_app.css" not in core and "canvas_global_app.js" not in core
print("PASS exact agenda reuse (no drift, no regeneration)")

# 4. Schedule change (when present) precedes the transition sentence.
hist = swu.build_message(
    "history",
    "Review.",
    "Ahead.",
    fake,
    schedule_change="One schedule change to note: the test was moved.",
)
assert hist.index("One schedule change to note") < hist.index("The Canvas History page has been updated")
print("PASS schedule-change note precedes the transition sentence")

# 5. Duplicate classification: ABSENT / ALREADY_APPLIED / DRIFT.
anns = []
assert swu.classify_duplicate(anns, title="Math Canvas Weekly Update",
                              week_marker="August 31\u2013September 4, 2026",
                              expected_core=core) == ("ABSENT", None)
same = [{"id": 1, "title": "Math Canvas Weekly Update", "message": swu.CSS + core + swu.JS}]
assert swu.classify_duplicate(same, title="Math Canvas Weekly Update",
                              week_marker="August 31\u2013September 4, 2026",
                              expected_core=core) == ("ALREADY_APPLIED", 1)
drifted = [{"id": 2, "title": "Math Canvas Weekly Update",
            "message": swu.CSS + '<div id="kl_wrapper_3"><p>stale</p></div>' + swu.JS}]
assert swu.classify_duplicate(drifted, title="Math Canvas Weekly Update",
                              week_marker="August 31\u2013September 4, 2026",
                              expected_core=core) == ("DRIFT", 2)
print("PASS duplicate protection classifies ABSENT / ALREADY_APPLIED / DRIFT")

# 6. Canonical contract doc persists the rules.
contract = root / "docs/programs/canvas-llm/canonical-context-pack/subject-weekly-update-announcement-contract.md"
text = contract.read_text(encoding="utf-8")
for needle in [
    "one combined weekly update announcement",
    "Week in Review",
    "Week Ahead",
    "The Canvas [Subject] page has been updated. Please see the upcoming week ahead.",
    "Science is announced only when Science is active",
    "Never guess a lesson title, chapter title, or topic",
    "Exact agenda reuse",
    "Duplicate protection",
    "Homeroom does",
]:
    assert needle in text, f"missing contract text: {needle!r}"
print("PASS canonical contract doc persists the rules")

# 7. Curriculum enrichment map is valid JSON with source metadata and no unverified mappings.
cur = json.loads(
    (root / "config/curriculum/canvas/subject-weekly-update-curriculum-map.json").read_text(encoding="utf-8")
)
assert cur["subjects"]["math"]["lessonNumbersOnly"] is True
assert "The Wonderful Wizard of Oz" in cur["subjects"]["reading_spelling"]["verifiedTopics"]
assert cur["subjects"]["language_arts"]["lessonNumbersOnly"] is False
for key, s in cur["subjects"].items():
    assert "sources" in s and s["sources"], f"{key} missing sources"
print("PASS curriculum enrichment map persists verified mappings with sources")

# 8. Owen's Math model example asset exists and is non-empty.
example = root / "docs/programs/canvas-llm/canonical-context-pack/examples/math-canvas-weekly-update-example.html"
assert example.is_file() and example.stat().st_size > 0
body = example.read_text(encoding="utf-8")
assert "Good afternoon" in body and "The Canvas Math page has been updated" in body
print("PASS Owen's Math Canvas Weekly Update example is persisted as the model asset")

print("PASS: subject Weekly Update Announcement workflow complete")
PY

echo "PASS: Canvas LLM subject Weekly Update Announcement tests complete"
