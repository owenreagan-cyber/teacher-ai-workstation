#!/usr/bin/env bash
set -euo pipefail
echo "Running Canvas LLM Phase 22 predictive weekly planning workstation tests..."
M=scripts/canvas_llm_phase22/phase22_workstation.py
T=$(mktemp -d "${TMPDIR:-/tmp}/phase22.XXXXXX")
trap 'rm -rf "$T"' EXIT
PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/teacher-ai-workstation-pycache" python3 -m py_compile "$M"
DEMO="$T/phase22-demo.json"
python3 "$M" build-demo --out "$DEMO"
python3 - "$DEMO" apps/predictive-weekly-planning/data/phase22-demo.json <<'PY'
import json
import sys
from pathlib import Path

def scrub(path):
    obj = json.loads(Path(path).read_text())
    obj['importReport']['generatedAt'] = '__normalized__'
    return obj

temp = scrub(sys.argv[1])
committed = scrub(sys.argv[2])
assert temp == committed
assert temp['artifactClassification'] == 'synthetic-curriculum'
assert temp['containsStudentData'] is False
assert temp['importReport']['artifactClassification'] == 'teacher-planning'
print('PASS demo artifact matches committed fixture shape')
PY
python3 "$M" validate-no-sensitive "$DEMO" fixtures/canvas-llm/phase-22/synthetic-pacing-guide.manifest.json .local/canvas-llm/approved-course-metadata | grep -q '^PASS quarantine report: classification=public-resource-metadata'
python3 "$M" --db "$T/w.sqlite3" self-test
python3 "$M" --db "$T/runtime.sqlite3" runtime-proof --port 18766
python3 "$M" --db "$T/browser.sqlite3" browser-proof --port 18767
python3 - <<'PY' "$T/w.sqlite3"
import sys
from datetime import date
from pathlib import Path
sys.path.insert(0, str(Path('.').resolve()))
from scripts.canvas_llm_phase22 import phase22_workstation as p

db = p.WorkstationDB(Path(sys.argv[1]))
db.migrate()
db.seed_from_fixture()
weeks = p.load_instructional_weeks()
assert len(weeks) == 37
assert weeks[0]['code'] == 'Q1W1' and weeks[0]['startsOn'] == '2026-07-20'
assert p.instructional_week_by_code('Q1W5')['startsOn'] == '2026-08-17'
assert p.instructional_week_for_date(date(2026, 8, 17))['code'] == 'Q1W5'
assert p.select_startup_week(db, date(2026, 7, 1))['mode'] == 'chooser'
assert p.select_startup_week(db, date(2027, 7, 1))['mode'] == 'chooser'
assert p.select_startup_week(db, date(2026, 7, 21))['week']['code'] == 'Q1W1'
assert p.resolve_reading_test(2)['lessonRange'] == {'start': 11, 'end': 20}
assert p.resolve_reading_test(10)['lessonRange'] == {'start': 91, 'end': 100}
assert p.resolve_checkout(1)['fluency'] == {'wpm': 100, 'maxErrors': 2}
assert p.resolve_checkout(7)['fluency'] == {'wpm': 100, 'maxErrors': 2}
assert p.resolve_checkout(8)['fluency'] == {'wpm': 115, 'maxErrors': 2}
assert p.resolve_checkout(10)['fluency'] == {'wpm': 115, 'maxErrors': 2}
assert p.resolve_checkout(11)['fluency'] == {'wpm': 130, 'maxErrors': 2}
assert p.resolve_checkout(13)['fluency'] == {'wpm': 130, 'maxErrors': 2}
assert p.resolve_checkout(1)['passage'] == 'The Cyclone, Chapter 2'
assert p.resolve_checkout(13)['passage'] == 'The Prince with the Peasants'
assert p.resolve_checkout(2)['title'] == 'RM4: Fluency Checkout 2'
fam = p.reading_assessment_family(2, '2026-07-21')
assert fam['sourceCheckoutKey'] == 'Check out 20'
fam14 = p.reading_assessment_family(14, '2026-08-01')
assert fam14['checkout'] is None
assert fam14['warnings'] == []
assert p.reading_checkout_number(14) is None
assert 'Checkout 14' not in p.reading_announcement_body(fam14)
w = db.current_week()['week']
d = w['subjects'][0]['days'][0]
up = db.patch_table('daily_subject_entries', d['id'], {'lesson': '1', 'title': 'Lesson 1'}, d['version'])
assert up['version'] == d['version'] + 1
assert db.patch_table('daily_subject_entries', d['id'], {'title': 'stale'}, d['version'])['status'] == 409
db2 = p.WorkstationDB(Path(sys.argv[1]))
assert db2.get_week(w['id'])['subjects'][0]['days'][0]['title'] == 'Lesson 1'
db.seed_from_fixture()
assert db.get_week(w['id'])['subjects'][0]['days'][0]['title'] == 'Lesson 1'
db.generate_week(w['id'])
week_after = db.get_week(w['id'])
deploy = week_after['deploymentPreview']
deploy_payload = deploy['payload']
assert deploy_payload['previewOnly'] is True
assert deploy_payload['canvasWritesAllowed'] is False
assert deploy_payload['emailSendsAllowed'] is False
assert deploy_payload['scheduleIntent'] == 'Friday 4:00 PM America/New_York'
for op in deploy_payload['operations']:
    low = op.lower()
    assert 'resource' not in low
    assert 'url' not in low
    assert 'publish' not in low
    assert 'front page' not in low
    assert 'create/update' not in low
assert deploy_payload['operations'] == [
    'validate local weekly inputs',
    'generate local assignment previews',
    'render academic agenda previews',
    'generate minimal assessment reminder previews',
    'await teacher approval',
]
assert all(item['status'] == 'blocked_preview' for item in deploy['items'])
assert all('Teacher approval required' in item['unresolved_dependencies'] for item in deploy['items'])
html = ''.join(x['body_html'] for x in week_after['drafts'])
assert 'kl_wrapper_3' in html
assert 'Reminders</h3>' in html and 'Homework</h4>' in html
assert 'display: flex' in html and 'width: 49%' in html
assert 'In Class' in html
assert 'Reminders &amp; Resources' not in html and '>At Home<' not in html and 'Study Guide' not in html
assert 'href="#"' not in html
assert p.resolve_math_lesson(1)['suggestedHomework'] == 'Odds'
assert p.resolve_course('2026-2027', 'production', 'reading')['courseId'] == p.resolve_course('2026-2027', 'production', 'spelling')['courseId']
assert p.phase22_validate_artifact_payload(p.build_payload(Path('fixtures/canvas-llm/phase-22/synthetic-pacing-guide.csv'), 'synthetic-fixture'))['safe']

def rows(*items):
    return [dict(x) for x in items]

week_meta={'quarter':1,'code':'Q1W5'}
normal_math=rows(
    {'subject':'math','weekday':'Monday','lesson':'18','tests':'','entry_date':'2026-08-17'},
    {'subject':'math','weekday':'Tuesday','lesson':'19','tests':'','entry_date':'2026-08-18'},
    {'subject':'math','weekday':'Wednesday','lesson':'20','tests':'','entry_date':'2026-08-19'},
    {'subject':'math','weekday':'Thursday','lesson':'21','tests':'','entry_date':'2026-08-20'},
    {'subject':'math','weekday':'Friday','lesson':'22','tests':'','entry_date':'2026-08-21'},
)
specs=p.selected_graded_assignment_specs(normal_math, week_meta)
math_instructional=[s for s in specs if s['subject']=='math' and s['payload']['metadata']['gradeCategory']=='instructional']
assert len(math_instructional)==3
assert any(s['title']==p.math_homework_assignment_title('Monday',18) for s in math_instructional)
assert any(s['title']==p.math_homework_assignment_title('Wednesday',20) for s in math_instructional)
assert any(s['title']==p.math_classwork_assignment_title('Tuesday',19) for s in math_instructional)
assert not any(s['title']==p.math_classwork_assignment_title('Thursday',21) for s in math_instructional)

displaced_math=rows(
    {'subject':'math','weekday':'Monday','lesson':'18','tests':'','entry_date':'2026-08-17'},
    {'subject':'math','weekday':'Tuesday','lesson':'','tests':'4','entry_date':'2026-08-18'},
    {'subject':'math','weekday':'Wednesday','lesson':'20','tests':'','entry_date':'2026-08-19'},
    {'subject':'math','weekday':'Thursday','lesson':'21','tests':'','entry_date':'2026-08-20'},
)
specs=p.selected_graded_assignment_specs(displaced_math, week_meta)
math_instructional=[s for s in specs if s['subject']=='math' and s['payload']['metadata']['gradeCategory']=='instructional']
assert len(math_instructional)==3
assert any(s['title']==p.math_classwork_assignment_title('Thursday',21) for s in math_instructional)
assert not any(s['title']==p.math_classwork_assignment_title('Tuesday',19) for s in math_instructional)
assert any(s['title']=='SM5: Written Assessment 4' for s in specs)

override_math=rows(
    {'subject':'math','weekday':'Monday','lesson':'18','tests':'','entry_date':'2026-08-17','resolver_output':'{"gradedSelectionOverride":{"classworkDay":"Thursday"}}'},
    {'subject':'math','weekday':'Tuesday','lesson':'19','tests':'','entry_date':'2026-08-18'},
    {'subject':'math','weekday':'Wednesday','lesson':'20','tests':'','entry_date':'2026-08-19'},
    {'subject':'math','weekday':'Thursday','lesson':'21','tests':'','entry_date':'2026-08-20'},
)
specs=p.selected_graded_assignment_specs(override_math, week_meta)
assert any(s['title']==p.math_classwork_assignment_title('Thursday',21) and s['payload']['metadata']['teacherOverrideApplied'] for s in specs)

normal_reading=rows(
    {'subject':'reading','weekday':'Monday','lesson':'50','tests':'','entry_date':'2026-08-17'},
    {'subject':'reading','weekday':'Tuesday','lesson':'51','tests':'','entry_date':'2026-08-18'},
    {'subject':'reading','weekday':'Wednesday','lesson':'52','tests':'','entry_date':'2026-08-19'},
    {'subject':'reading','weekday':'Thursday','lesson':'53','tests':'','entry_date':'2026-08-20'},
)
specs=p.selected_graded_assignment_specs(normal_reading, week_meta)
reading_instructional=[s for s in specs if s['subject']=='reading' and s['payload']['metadata']['gradeCategory']=='instructional']
assert len(reading_instructional)==3
assert any(s['title']==p.reading_classwork_assignment_title('Monday',50) for s in reading_instructional)
assert not any(s['title']==p.reading_classwork_assignment_title('Wednesday',52) for s in reading_instructional)

reading_override=rows(
    {'subject':'reading','weekday':'Monday','lesson':'50','tests':'','entry_date':'2026-08-17'},
    {'subject':'reading','weekday':'Tuesday','lesson':'51','tests':'','entry_date':'2026-08-18'},
    {'subject':'reading','weekday':'Wednesday','lesson':'52','tests':'','entry_date':'2026-08-19','resolver_output':'{"gradedSelectionOverride":{"classworkDay":"Wednesday"}}'},
    {'subject':'reading','weekday':'Thursday','lesson':'53','tests':'','entry_date':'2026-08-20'},
)
specs=p.selected_graded_assignment_specs(reading_override, week_meta)
assert any(s['title']==p.reading_classwork_assignment_title('Wednesday',52) and s['payload']['metadata']['teacherOverrideApplied'] for s in specs)
assert not any(s['title']==p.reading_classwork_assignment_title('Monday',50) for s in specs)

other=rows(
    {'subject':'spelling','weekday':'Tuesday','lesson':'5','tests':'','entry_date':'2026-08-18'},
    {'subject':'language-arts','weekday':'Wednesday','lesson':'3','tests':'','entry_date':'2026-08-19','title':'ELA4: Chapter 3 Practice'},
    {'subject':'history','weekday':'Thursday','lesson':'4','tests':'','entry_date':'2026-08-20','title':'HIST4: Ancient Rome, Lesson 4'},
    {'subject':'science','weekday':'Friday','lesson':'2','tests':'','entry_date':'2026-08-21','title':'SCI4: Life Cycles, Lesson 2'},
)
specs=p.selected_graded_assignment_specs(other, week_meta)
assert not any(s['subject'] in {'spelling','language-arts','history','science'} and s['payload']['metadata']['gradeRole'] in {'homework','classwork'} for s in specs)

window_rows=rows(
    {'subject':'math','weekday':'Tuesday','lesson':'','tests':'4','entry_date':'2026-08-18'},
    {'subject':'reading','weekday':'Wednesday','lesson':'','tests':'7','entry_date':'2026-08-19'},
    {'subject':'spelling','weekday':'Friday','lesson':'','tests':'5','entry_date':'2026-08-21'},
)
findings=p.validate_assessment_schedule_windows(window_rows, week_meta)
assert any(f['code']=='math-written.window' and f['severity']=='pass' for f in findings)
assert any(f['code']=='reading-mastery.window' and f['severity']=='pass' for f in findings)
assert any(f['code']=='spelling-test.window' and f['severity']=='pass' for f in findings)

due=p.same_day_due_fields('2026-08-17')
assert due['dueTime']=='11:59 PM' and due['points']==100 and due['gradeDisplay']=='Percentage'
print('PASS C0M graded-item selection')
print('PASS python behavior')
PY
bash scripts/canvas-llm-phase-22-predictive-weekly-planning-workstation-status.sh >"$T/status.txt" 2>&1 || { cat "$T/status.txt"; exit 1; }
grep -q '^FAIL: 0$' "$T/status.txt" || { cat "$T/status.txt"; exit 1; }
bin/chief-of-staff --canvas-llm-phase-22-predictive-weekly-planning-workstation-status >"$T/cli.txt" 2>&1 || { cat "$T/cli.txt"; exit 1; }
grep -q '^FAIL: 0$' "$T/cli.txt" || { cat "$T/cli.txt"; exit 1; }
if git ls-files .local | grep -q .; then echo "FAIL: .local artifacts tracked"; exit 1; fi
echo "PASS: Canvas LLM Phase 22 predictive weekly planning workstation tests complete"
