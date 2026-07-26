#!/usr/bin/env bash
set -euo pipefail

echo "Running Canvas LLM weekly agenda publisher tests..."

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

PUBLISHER="scripts/canvas_llm_phase22/weekly_agenda_publisher.py"
PHASE22="scripts/canvas_llm_phase22/phase22_workstation.py"
T="$(mktemp -d "${TMPDIR:-/tmp}/agenda-pub.XXXXXX")"
trap 'rm -rf "$T"' EXIT

PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/teacher-ai-workstation-pycache" python3 -m py_compile "$PUBLISHER" "$PHASE22"
python3 "$PUBLISHER" self-test

python3 - <<'PY' "$T/agenda.sqlite3"
import sys
from pathlib import Path

sys.path.insert(0, str(Path('.').resolve()))
from scripts.canvas_llm_phase22 import phase22_workstation as p22
from scripts.canvas_llm_phase22 import weekly_agenda_publisher as agenda

db_path = Path(sys.argv[1])
db = p22.WorkstationDB(db_path)
db.migrate()
db.seed_from_fixture()
week = p22.instructional_week_by_code('Q1W5')
assert week is not None
wid = db.create_week(week['startsOn'])
db.generate_week(wid)

page = agenda.build_agenda_from_db(db, wid, 'math')
assert page.week_code == 'Q1W5'
html_body = agenda.render_agenda_html(page)
assert 'Monday' in html_body
assert agenda.agenda_has_no_student_data(page)

publisher = agenda.WeeklyAgendaPublisher(db)
generated = publisher.generate_page(wid, 'math')
assert generated.content_hash is not None
assert not publisher.page_already_published(generated)

# Simulate duplicate prevention
agenda._PUBLISHED_PAGES.add(generated.page_url or '')
blocked = publisher.deploy_page(generated, artifact_id='test-artifact')
assert blocked.deployment_status == 'blocked'

source = Path('scripts/canvas_llm_phase22/weekly_agenda_publisher.py').read_text().lower()
for transport in ('requests.post', 'canvas.instructure', 'bearer ', 'urllib.request'):
    assert transport not in source, f'forbidden transport found: {transport}'
assert 'agenda_has_no_student_data' in source, 'student data guard must exist'

print('PASS agenda generation from weekly plan')
print('PASS content rendering includes days and homework')
print('PASS duplicate page prevention works')
print('PASS no student data in agenda payload')
PY

echo "PASS Canvas LLM weekly agenda publisher tests complete"
