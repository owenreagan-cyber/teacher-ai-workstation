#!/usr/bin/env bash
set -euo pipefail

echo "Running Canvas LLM artifact health tests..."

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

REGISTRY="scripts/canvas_llm_phase22/artifact_registry.py"
PHASE22="scripts/canvas_llm_phase22/phase22_workstation.py"
T="$(mktemp -d "${TMPDIR:-/tmp}/artifact-health.XXXXXX")"
trap 'rm -rf "$T"' EXIT

PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/teacher-ai-workstation-pycache" python3 -m py_compile "$REGISTRY" "$PHASE22"

python3 "$REGISTRY" self-test

python3 - <<'PY' "$T/registry.sqlite3"
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path('.').resolve()))
from scripts.canvas_llm_phase22 import phase22_workstation as p22
from scripts.canvas_llm_phase22 import artifact_registry as reg

db_path = Path(sys.argv[1])
db = p22.WorkstationDB(db_path)
db.migrate()
db.seed_from_fixture()
week = p22.instructional_week_by_code('Q1W5')
assert week is not None
wid = db.create_week(week['startsOn'])
week_data = db.get_week(wid)
for subject_plan in week_data['subjects']:
    if subject_plan['subject'] != 'math':
        continue
    for index, day in enumerate(subject_plan['days']):
        fields = {'lesson': str(18 + index), 'title': f'Lesson {18 + index}'}
        if index == 1:
            fields = {'lesson': '', 'tests': '4', 'title': 'Written Assessment 4'}
        db.patch_table(
            'daily_subject_entries',
            day['id'],
            fields,
            day['version'],
        )
db.generate_week(wid)

before_rows = [dict(row) for row in db.connect().execute('SELECT * FROM drafts WHERE weekly_plan_id=? ORDER BY id', (wid,))]
records = reg.load_registry_from_db(db, wid)
after_rows = [dict(row) for row in db.connect().execute('SELECT * FROM drafts WHERE weekly_plan_id=? ORDER BY id', (wid,))]

assert before_rows == after_rows, 'registry read must not mutate drafts'
assert reg.registry_is_read_only()

tables = [row[0] for row in db.connect().execute("SELECT name FROM sqlite_master WHERE type='table'")]
assert 'artifact_registry' not in tables

kinds = {record.artifact_kind for record in records}
assert 'assignment' in kinds, 'assignments must be discovered'
assert 'announcement' in kinds, 'announcements must be discovered'
assert 'newsletter' in kinds, 'newsletter artifacts must be discovered'
assert 'daily_brief' in kinds, 'daily teacher briefs must be discovered'

encoded_once = json.dumps([record.to_dict() for record in records], sort_keys=True)
encoded_twice = json.dumps([record.to_dict() for record in reg.load_registry_from_db(db, wid)], sort_keys=True)
assert encoded_once == encoded_twice, 'registry must be deterministic'

assignment = next(record for record in records if record.artifact_kind == 'assignment')
assert reg.evaluate_artifact_health(assignment) == 'PASS'

announcement = next(
    record for record in records
    if record.artifact_kind == 'announcement' and record.subject != p22.HOMEROOM_NEWSLETTER_SUBJECT
)
if announcement.needs_review or announcement.warnings:
    assert reg.evaluate_artifact_health(announcement) == 'WARN'
else:
    assert reg.evaluate_artifact_health(announcement) == 'PASS'

newsletter_update = next(record for record in records if record.artifact_kind == 'newsletter_update')
assert reg.evaluate_artifact_health(newsletter_update) == 'BLOCK'

daily_brief = next(record for record in records if record.artifact_kind == 'daily_brief')
assert daily_brief.preview_only is True
assert daily_brief.email_sends_allowed is False

source = Path('scripts/canvas_llm_phase22/artifact_registry.py').read_text().lower()
for forbidden in ('canvas.instructure', 'smtp', 'sendgrid', 'gmail', 'urllib.request', 'requests.post'):
    assert forbidden not in source

phase26 = Path('scripts/canvas-llm-phase-26-unified-weekly-production-workstation-status.sh')
phase27 = Path('scripts/canvas-llm-phase-27-canvas-readiness-and-safety-diff-status.sh')
assert phase26.exists() and phase27.exists()

print('PASS artifact registry discovers assignments')
print('PASS artifact registry discovers announcements')
print('PASS artifact registry discovers newsletter artifacts')
print('PASS artifact registry discovers Daily Teacher Briefs')
print('PASS no duplicate artifact storage created')
print('PASS registry is deterministic')
print('PASS approval health rules work')
print('PASS no artifact mutation occurs')
print('PASS no Canvas calls')
print('PASS no email transport')
print('PASS Phase 26 and Phase 27 untouched')
PY

bin/chief-of-staff --canvas-llm-artifact-health-status | grep -q 'Canvas LLM Artifact Health'

echo "PASS Canvas LLM artifact health tests complete"
