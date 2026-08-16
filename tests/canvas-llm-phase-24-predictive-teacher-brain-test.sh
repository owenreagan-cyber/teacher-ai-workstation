#!/usr/bin/env bash
set -euo pipefail

echo "Running Canvas LLM Phase 24 predictive teacher brain tests..."
M=scripts/canvas_llm_phase24/predict_week.py
V=scripts/canvas_llm_phase24/validate_prediction.py
T=$(mktemp -d "${TMPDIR:-/tmp}/phase24.XXXXXX")
trap 'rm -rf "$T"' EXIT

PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/teacher-ai-workstation-pycache" python3 -m py_compile \
  "$M" "$V" \
  scripts/canvas_llm_phase24/models.py \
  scripts/canvas_llm_phase24/pacing_knowledge.py \
  scripts/canvas_llm_phase24/correction_memory.py \
  scripts/canvas_llm_phase24/rule_engine.py

DEMO="$T/phase24-demo.json"
python3 "$M" --week Q1W5 --input fixtures/canvas-llm/phase-24/predictive-teacher-brain.json --output "$DEMO"

python3 - "$DEMO" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["weekCode"] == "Q1W5"
assert payload["validation"]["failCount"] == 0
assert payload["validation"]["warnCount"] == 1
assert payload["reviewState"] == "needs_review"
assert "Study Guide" not in json.dumps(payload)
print("PASS predicted week payload shape")
PY

python3 "$V" "$DEMO" | grep -q '^PASS: due-time.resolved Canvas assignment due-time resolved by owner policy (same-day 11:59 p.m. local)$'
python3 "$V" "$DEMO" | grep -q '^WARN: math-test-cadence.unresolved Math test cadence remains owner-unresolved$'
python3 "$V" "$DEMO" | grep -q '^PASS: reading.checkout14 Checkout 14 is absent without warning$'
python3 "$V" "$DEMO" | grep -q '^FAIL: 0$'

python3 - "$DEMO" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))

def find(subject, weekday, event_type, lesson=None, assessment=None):
    for item in payload["predictions"]:
        if item["subject"] == subject and item["weekday"] == weekday and item["event_type"] == event_type:
            if lesson is not None and item.get("lesson_number") != lesson:
                continue
            if assessment is not None and item.get("assessment_number") != assessment:
                continue
            return item
    raise AssertionError((subject, weekday, event_type, lesson, assessment))

math18 = find("math", "Monday", "lesson", lesson=18)
assert math18["in_class_title"] == "SM5: Lesson 18"
assert math18["at_home_title"] == "#12-30 evens"
assert math18["decision_layer"] == "owner-confirmed hard rules"
assert math18["confidence"]["level"] == "high"

math7 = find("math", "Tuesday", "lesson", lesson=7)
assert math7["at_home_title"] == "No Homework"

math8 = find("math", "Wednesday", "lesson", lesson=8)
assert math8["at_home_title"] == "#11-29 odds"

inv10 = find("math", "Thursday", "lesson", lesson=10)
assert inv10["in_class_title"] == "SM5: Investigation 1"
assert "Study Guide" not in inv10["at_home_title"]

inv20 = find("math", "Friday", "lesson", lesson=20)
assert inv20["in_class_title"] == "SM5: Investigation 2"
assert inv20["at_home_title"] == "No Homework"

math_assessment = find("math", "Tuesday", "assessment", assessment=18)
assert math_assessment["requires_review"] is True
assert "Written Assessment" in math_assessment["in_class_title"]

reading1 = find("reading", "Tuesday", "assessment", assessment=1)
assert reading1["at_home_title"] == "RM4: Fluency Checkout 1"

reading7 = find("reading", "Wednesday", "assessment", assessment=7)
assert reading7["at_home_title"] == "RM4: Fluency Checkout 7"

reading14 = find("reading", "Thursday", "assessment", assessment=14)
assert reading14["at_home_title"] == ""
assert "Checkout 14" not in json.dumps(reading14)

spell = find("spelling", "Friday", "assessment", assessment=5)
assert spell["in_class_title"] == "RM4: Spelling Test 5"

spell_override = find("spelling", "Thursday", "assessment", assessment=15)
assert spell_override["manual_override_state"] == "applied"
assert spell_override["decision_layer"] == "approved teacher correction"

shurley = find("shurley", "Tuesday", "lesson")
assert shurley["decision_layer"] == "explicit current-year pacing-guide entry"

history = find("history", "Thursday", "lesson")
assert history["requires_review"] is False

science_predictions = [item for item in payload["predictions"] if item["subject"] == "science"]
assert science_predictions == []
assert any("Science is inactive this quarter" in warning for warning in payload["warnings"])

print("PASS prediction rules")
PY

PHASE24_LOCAL_ROOT="$T/local-root" python3 - <<'PY'
import json
import os
from pathlib import Path
from scripts.canvas_llm_phase24.correction_memory import load_correction_state, save_teacher_correction, load_teacher_corrections, state_path

root = Path(os.environ['PHASE24_LOCAL_ROOT'])
state = load_correction_state('Q1W5')
assert state['status'] == 'saved'
assert state['version'] == 0

saved = save_teacher_correction(
    {
        'subject': 'math',
        'weekCode': 'Q1W5',
        'day': 'Wednesday',
        'predictedValue': 'SM5: Lesson 8 Evens',
        'approvedValue': 'SM5: Lesson 8 Odds',
        'correctionScope': 'this occurrence only',
        'timestamp': '2026-07-11T00:00:00Z',
        'reason': 'teacher preference',
        'sourceRule': 'teacher.override',
        'revision': 1,
    },
    0,
)
assert saved['version'] == 1
assert load_teacher_corrections('Q1W5')[0]['approvedValue'] == 'SM5: Lesson 8 Odds'
assert state_path('Q1W5').exists()

conflict = save_teacher_correction(
    {
        'subject': 'math',
        'weekCode': 'Q1W5',
        'day': 'Wednesday',
        'predictedValue': 'SM5: Lesson 8 Evens',
        'approvedValue': 'SM5: Lesson 8 Odds',
        'correctionScope': 'this lesson permanently',
        'timestamp': '2026-07-11T00:00:00Z',
        'reason': 'teacher preference',
        'sourceRule': 'teacher.override',
        'revision': 2,
    },
    0,
)
assert conflict['status'] == 'conflict'

bad = root / 'corrections' / 'Q1W5.json'
bad.parent.mkdir(parents=True, exist_ok=True)
bad.write_text('{broken-json', encoding='utf-8')
quarantined = load_correction_state('Q1W5')
assert quarantined['status'] == 'error'
assert any(path.name == 'Q1W5.json' for path in (root / 'quarantine').rglob('Q1W5.json'))
print('PASS correction memory')
PY

python3 - <<'PY'
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path('.').resolve()))
from scripts.canvas_llm_phase24.rule_engine import predict_week_data, annotate_graded_selection
from scripts.canvas_llm_phase24.pacing_knowledge import load_pacing_knowledge

fixture = Path('fixtures/canvas-llm/phase-24/predictive-teacher-brain.json')
knowledge = load_pacing_knowledge(fixture)
prediction = predict_week_data('Q1W5', fixture, {'records': []})
selected = [item for item in prediction.predictions if 'graded.selected' in item.rules_applied]
non_selected = [item for item in prediction.predictions if 'graded.non-selected-instructional' in item.rules_applied]
assert any('graded.selected' in item.rules_applied for item in prediction.predictions)
assert any('graded.non-selected-instructional' in item.rules_applied for item in prediction.predictions)
assert any('Math test cadence remains owner-unresolved' in warning for warning in prediction.warnings)
assert not any(item.field == 'homeworkParity' for item in prediction.teacher_overrides)
assert prediction.announcement_drafts
assert not any(item.get('title') == 'RM4: Fluency Checkout 14' for item in prediction.announcement_drafts)
assert all(item.get('teacherApprovalRequired') is not False for item in prediction.announcement_drafts)
assert all((item.get('schedule_metadata') or {}).get('scheduleIntent') == '1-2 days before assessment date America/New_York' for item in prediction.announcement_drafts)
assert all((item.get('schedule_metadata') or {}).get('assessmentDate') == item.get('assessment_date') for item in prediction.announcement_drafts)
assert all((item.get('schedule_metadata') or {}).get('announcementDate') < item.get('assessment_date') for item in prediction.announcement_drafts if item.get('assessment_date'))
print('PASS C0N announcement prediction metadata')
assert prediction.newsletter_draft and prediction.newsletter_update_announcement
assert prediction.newsletter_draft['title']=='Homeroom Newsletter — August 2026'
assert prediction.newsletter_draft['course_id']==26427 and prediction.newsletter_draft['cadence']=='monthly'
assert prediction.newsletter_update_announcement['body_text']=='The newsletter has been updated for August 2026.'
assert prediction.newsletter_update_announcement['depends_on']==prediction.newsletter_draft['local_object_id']
assert prediction.newsletter_update_announcement['page_url'] is None
assert prediction.newsletter_update_announcement['schedule_metadata'] is None
print('PASS C0O newsletter prediction metadata')
assert prediction.daily_teacher_briefs and len(prediction.daily_teacher_briefs)==5
monday=next(item for item in prediction.daily_teacher_briefs if item.get('entry_date')=='2026-08-17')
assert monday['title']=='Daily Teacher Brief — Monday, August 17, 2026'
assert monday.get('recipientConfigured') and monday.get('recipientDisplay')=='Teacher'
assert monday.get('delivery_status')=='blocked_preview'
assert (monday.get('schedule_metadata') or {}).get('intendedForUtc')=='2026-08-17T10:15:00Z'
print('PASS C0P daily teacher brief prediction metadata')
print('PASS C0M graded-item selection metadata')
PY

echo "PASS: Canvas LLM Phase 24 predictive teacher brain tests complete"
