#!/usr/bin/env bash
set -euo pipefail

echo "Running Canvas LLM live Q1W2 deployment tests..."

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

LIVE="scripts/canvas_llm_phase22/live_q1w2_deployment.py"
CONN="scripts/canvas_llm_phase22/canvas_connection.py"
RENDERER="scripts/canvas_llm_phase22/canvas_html_renderer.py"
DETECTOR="scripts/canvas_llm_phase22/canvas_duplicate_detector.py"

export CANVAS_LLM_CONNECTION_TEST_MODE=1
export CANVAS_LLM_LIVE_Q1W2_APPROVED=1

PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/teacher-ai-workstation-pycache" python3 -m py_compile "$LIVE" "$CONN" "$RENDERER" "$DETECTOR"
python3 "$CONN" self-test
python3 "$LIVE" self-test

python3 - <<'PY'
from pathlib import Path
import sys

sys.path.insert(0, str(Path('.').resolve()))
from scripts.canvas_llm_phase22 import live_q1w2_deployment as live
from scripts.canvas_llm_phase22 import canvas_connection as conn
from scripts.canvas_llm_phase22 import canvas_duplicate_detector as detector
from scripts.canvas_llm_phase22 import canvas_html_renderer as renderer
from scripts.canvas_llm_phase22 import canvas_course_resolver as routes
from scripts.canvas_llm_phase22 import deployment_context as ctx

from scripts.canvas_llm_phase22 import canvas_connection_manager as transport

live.LIVE_CANVAS_STORE['pages'].clear()
live.LIVE_CANVAS_STORE['assignments'].clear()
live.LIVE_CANVAS_STORE['announcements'].clear()
transport.MOCK_LIVE_STORE['pages'].clear()
transport.MOCK_LIVE_STORE['assignments'].clear()

status = conn.build_connection_status(test_mode=True)
assert status.authentication == 'PASS'
assert status.course_mapping == 'PASS'
assert status.writes == 'CONTROLLED'

dup = live.run_duplicate_scan()
assert dup.pages_status == 'PASS'

html_body = renderer.render_q1w2_weekly_agenda_html()
assert 'kl_wrapper_3' in html_body
assert 'Study for Friday' in html_body
assert 'Homework: None' not in html_body
for day in ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'):
    assert day in html_body

report = live.execute_live_deployment(approved=True, test_mode=True)
assert report.page_status == 'CREATED'
assert report.assignments_created == 9
assert report.announcement_status == 'DRAFT'
assert report.verification == 'PASS'

page = transport.MOCK_LIVE_STORE['pages'][next(item.object_id for item in report.records if item.object_type == 'page')]
assert page['front_page'] is True
assert page['published'] is True

sm5_5 = transport.MOCK_LIVE_STORE['assignments'][next(item.object_id for item in report.records if item.title == 'SM5: Lesson 5')]
assert sm5_5['counts_toward_final_grade'] is False

rm4_4 = transport.MOCK_LIVE_STORE['assignments'][next(item.object_id for item in report.records if item.title == 'RM4: Lesson 4')]
assert rm4_4['counts_toward_final_grade'] is False

ann = live.LIVE_CANVAS_STORE['announcements'][next(item.object_id for item in report.records if item.object_type == 'announcement')]
assert ann['published'] is False
assert 'Mr. Reagan' in ann['body']
for blocked in ('study guide', 'answer key', 'practice word list'):
    assert blocked not in ann['body'].lower()

math_route = routes.resolve_route('math', 'lesson')
assert math_route.course_id == 26404
assert math_route.prefix == 'SM5'

manual = ctx.validate_deployment_context(
    ctx.DeploymentContext(
        subject='language-arts',
        assignment_type='lesson',
        course_id=26495,
        canonical_prefix='ELA4',
        assignment_group='Homework',
        title='ELA4: Journal',
    ),
    target_type='assignment',
)
assert manual.allowed is False

assert live.live_deployment_has_no_network()
assert live.BLOCKED_OPERATIONS

print('PASS connection')
print('PASS duplicate scan')
print('PASS page creation')
print('PASS assignment creation')
print('PASS grading states')
print('PASS announcement restrictions')
print('PASS manual subjects')
PY

bin/chief-of-staff --canvas-connection-status | grep -q 'PASS'
bin/chief-of-staff --canvas-duplicate-scan | grep -q 'PASS'
bin/chief-of-staff --live-q1w2-deployment-preview | grep -q 'Q1W2 Weekly Agenda'
bin/chief-of-staff --live-q1w2-deployment-status | grep -q 'PASS'

echo "PASS Canvas LLM live Q1W2 deployment tests complete"
