#!/usr/bin/env bash
set -euo pipefail

echo "Running Canvas launcher live-transport fake tests..."

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

TRANSPORT="scripts/canvas_llm_phase22/canvas_connection_manager.py"
WRITER="scripts/canvas_llm_phase22/canvas_writer.py"
LAUNCH="scripts/canvas_llm_phase22/canvas_launcher.py"
T="$(mktemp -d "${TMPDIR:-/tmp}/canvas-launch-transport.XXXXXX")"
trap 'rm -rf "$T"' EXIT

python3 -m py_compile "$TRANSPORT" "$WRITER" "$LAUNCH"
python3 "$TRANSPORT" self-test
python3 "$WRITER" self-test
python3 "$LAUNCH" self-test

python3 - <<'PY'
from pathlib import Path
from unittest import mock
import sys

sys.path.insert(0, str(Path('.').resolve()))
from scripts.canvas_llm_phase22 import canvas_connection_manager as transport
from scripts.canvas_llm_phase22 import canvas_writer as writer
from scripts.canvas_llm_phase22 import canvas_launcher as launcher

MATH = transport.MATH_COURSE_ID
READING = transport.READING_COURSE_ID
ELA = transport.ELA_COURSE_ID

store = transport.MOCK_LIVE_STORE
store['pages'].clear()
store['assignments'].clear()
store['announcements'].clear()

# --- Seed fake store with objects under test ---
store['assignments']['2001'] = {
    'id': '2001', 'course_id': MATH, 'name': 'SM5: Lesson 14', 'title': 'SM5: Lesson 14',
    'assignment_group': 'Homework/Class Work', 'counts_toward_final_grade': True,
    'omit_from_final_grade': False, 'published': True,
}
store['assignments']['2002'] = {
    'id': '2002', 'course_id': MATH, 'name': 'SM5: Lesson 17', 'title': 'SM5: Lesson 17',
    'assignment_group': 'Homework/Class Work', 'counts_toward_final_grade': True,
    'omit_from_final_grade': False, 'published': True,
}
store['announcements']['3001'] = {
    'id': '3001', 'course_id': READING, 'title': 'Spelling Test 15 - Wednesday, August 19',
    'message': '<p>old</p>', 'published': True,
}
store['announcements']['3002'] = {
    'id': '3002', 'course_id': READING, 'title': 'Reminder - Spelling Test 15 Tomorrow',
    'message': '<p>keep</p>', 'published': True,
}
store['pages']['q1w5-august-17-21-2026'] = {
    'id': 'p1', 'url': 'q1w5-august-17-21-2026', 'course_id': ELA,
    'title': 'Q1W5 - August 17-21, 2026', 'body': '<p>old body</p>', 'published': False,
}

# --- approved assignment UPDATE works ---
res = writer.update_assignment_live(
    course_id=MATH, assignment_id='2001', title='SM5: Lesson 14',
    new_title='SM5: Lesson 14 Homework', approved=True, test_mode=True,
)
assert res.write_status == 'WRITTEN', res.to_dict()
assert store['assignments']['2001']['name'] == 'SM5: Lesson 14 Homework'
print('PASS approved assignment UPDATE works')

# --- approved assignment REMOVE works ---
res = writer.delete_assignment_live(
    course_id=MATH, assignment_id='2002', title='SM5: Lesson 17',
    approved=True, test_mode=True,
)
assert res.write_status == 'WRITTEN', res.to_dict()
assert '2002' not in store['assignments']
print('PASS approved assignment REMOVE works')

# --- approved announcement UPDATE works ---
res = writer.update_announcement_live(
    course_id=READING, topic_id='3001', title='Spelling Test 15 - Wednesday, August 19',
    message='<p>new message</p>', approved=True, test_mode=True,
)
assert res.write_status == 'WRITTEN', res.to_dict()
assert store['announcements']['3001']['message'] == '<p>new message</p>'
print('PASS approved announcement UPDATE works')

# --- approved announcement REMOVE works ---
res = writer.delete_announcement_live(
    course_id=READING, topic_id='3001', title='Spelling Test 15 - Wednesday, August 19',
    approved=True, test_mode=True,
)
assert res.write_status == 'WRITTEN', res.to_dict()
assert '3001' not in store['announcements']
print('PASS approved announcement REMOVE works')

# --- approved page UPDATE works (in place, no CREATE) ---
res = writer.update_page_live(
    course_id=ELA, page_ref='q1w5-august-17-21-2026', title='Q1W5 - August 17-21, 2026',
    body='<p>new body</p>', published=True, approved=True, test_mode=True,
)
assert res.write_status == 'WRITTEN', res.to_dict()
assert store['pages']['q1w5-august-17-21-2026']['body'] == '<p>new body</p>'
assert store['pages']['q1w5-august-17-21-2026']['published'] is True
print('PASS approved page UPDATE works')

# --- page CREATE remains blocked through the launcher ---
page_create_rows = [
    {'course': 'Language Arts', 'course_id': ELA, 'object_type': 'page', 'existing': None,
     'existing_id': None, 'action': 'CREATE', 'resulting_title': 'q1w5-brand-new-page',
     'body': '<p>x</p>'},
]
before = set(store['pages'].keys())
count = launcher._apply_approved(page_create_rows, test_mode=True)
assert count == 0, 'page CREATE must produce zero writes'
assert set(store['pages'].keys()) == before, 'page CREATE must not create a page'
print('PASS page CREATE remains blocked')

# --- unapproved manifests still cannot write ---
res = writer.update_assignment_live(
    course_id=MATH, assignment_id='2001', title='SM5: Lesson 14 Homework',
    new_title='NOPE', approved=False, test_mode=True,
)
assert res.write_status == 'BLOCKED', res.to_dict()
print('PASS unapproved manifest cannot write')

# --- launcher dispatch: approved assignment UPDATE works end-to-end via _apply_approved ---
update_rows = [
    {'course': 'Math', 'course_id': MATH, 'object_type': 'assignment', 'existing': 'SM5: Lesson 14',
     'existing_id': 2001, 'action': 'UPDATE', 'resulting_title': 'SM5: Lesson 14 Homework',
     'timing': '', 'reason': 'rename'},
]
count = launcher._apply_approved(update_rows, test_mode=True)
assert count == 1, count
assert store['assignments']['2001']['name'] == 'SM5: Lesson 14 Homework'
print('PASS launcher dispatch approved assignment UPDATE')

# --- drift blocks before write ---
MINIMAL = {
    'weekCode': 'Q1W5',
    'approval': {'teacherApproved': True, 'approvedBy': 'Teacher'},
    'actions': [
        {'course': 'Math', 'course_id': MATH, 'object_type': 'assignment',
         'existing': 'SM5: Lesson 14', 'existing_id': 2001, 'action': 'UPDATE',
         'resulting_title': 'SM5: Lesson 14 Homework', 'timing': '', 'reason': 'rename'},
    ],
}
CLEAN = {'courses': {str(MATH): {
    'pages': [], 'announcements': [],
    'assignments': [{'id': 2001, 'name': 'SM5: Lesson 14'}],
}}}
DRIFTED = {'courses': {str(MATH): {
    'pages': [], 'announcements': [],
    'assignments': [{'id': 2001, 'name': 'SM5: Lesson 14 CHANGED EXTERNALLY'}],
}}}
with mock.patch.object(launcher, 'load_manifest', return_value=MINIMAL), \
     mock.patch.object(launcher, '_fetch_live_inventory', side_effect=[CLEAN, DRIFTED]), \
     mock.patch.object(launcher, '_write_backup', return_value=Path('/tmp/dummy.json')):
    rc = launcher.command_launch('Q1W5', test_mode=True)
    assert rc == 1, 'drift between preflight and write must block'
print('PASS drift blocks before write')

# --- backup failure blocks before write ---
with mock.patch.object(launcher, 'load_manifest', return_value=MINIMAL), \
     mock.patch.object(launcher, '_fetch_live_inventory', return_value=CLEAN), \
     mock.patch.object(launcher, '_write_backup', side_effect=OSError('no space on device')):
    rc = launcher.command_launch('Q1W5', test_mode=True)
    assert rc == 1, 'backup failure must block before write'
print('PASS backup failure blocks before write')

# --- announcement CREATE carries ISO delayed_post_at ---
store['announcements'].clear()
ann = writer.create_announcement_live(
    course_id=READING, title='Reminder - Chapter 2 Test Tomorrow',
    message='<p>Good afternoon,</p><p>Test.</p>',
    delayed_post_at='2026-08-20T20:00:00Z', approved=True, test_mode=True,
)
assert ann.write_status == 'WRITTEN', ann.to_dict()
assert store['announcements'][ann.target_id]['delayed_post_at'] == '2026-08-20T20:00:00Z'
print('PASS announcement CREATE carries ISO delayed_post_at')

# --- manifest CREATE rows carry ISO due_at / delayed_post_at; UPDATE rows never set due_at ---
manifest = launcher.load_manifest('Q1W5')
create_assign = [a for a in manifest['actions'] if a.get('action') == 'CREATE' and a.get('object_type') == 'assignment']
assert all(a.get('due_at') and a['due_at'].endswith('Z') for a in create_assign), create_assign
create_ann = [a for a in manifest['actions'] if a.get('action') == 'CREATE' and a.get('object_type') == 'announcement']
assert all(a.get('delayed_post_at') and a['delayed_post_at'].endswith('Z') for a in create_ann), create_ann
update_rows = [a for a in manifest['actions'] if a.get('action') == 'UPDATE']
assert all(not a.get('due_at') for a in update_rows), 'UPDATE rows must not rewrite due dates'
print('PASS manifest CREATE ISO dates + UPDATE no-due-date invariant')

# --- HTTP 403 becomes a clean BLOCKED result, not an uncaught traceback ---
import urllib.error

class _ForbiddenClient:
    transport = 'live'
    def update_page(self, *a, **kw):
        raise transport.CanvasTransportError('PUT', '/api/v1/courses/26493/pages/q1w5-august-17-21-2026', 403, 'forbidden')

res = writer.update_page_live(
    course_id=26493, page_ref='q1w5-august-17-21-2026', title='Q1W5 - August 17-21, 2026',
    body='<p>x</p>', published=True, approved=True, client=_ForbiddenClient(),
)
assert res.write_status == 'BLOCKED', res.to_dict()
assert any('canvas_transport_error' in b and '403' in b for b in res.blockers), res.to_dict()
print('PASS HTTP 403 page update returns clean BLOCKED')

# --- transport request converts raw HTTPError into CanvasTransportError ---
client = transport.Phase22LiveCanvasClient(base_url='https://example.instructure.com', token='x')
path_403 = f'/api/v1/courses/{MATH}/pages/p'
url_403 = f'https://example.instructure.com{path_403}'
req_patcher = mock.patch.object(
    transport.urllib.request, 'urlopen',
    side_effect=urllib.error.HTTPError(url_403, 403, 'Forbidden', {}, None),
)
with req_patcher:
    try:
        client.request('PUT', path_403, data={'wiki_page[body]': 'x'})
        raise AssertionError('expected CanvasTransportError')
    except transport.CanvasTransportError as exc:
        assert exc.status == 403, exc
        assert 'PUT' in str(exc) and path_403 in str(exc), exc
        assert 'Bearer' not in str(exc) and 'x' not in str(exc), 'token must never leak'
print('PASS transport 403 raises CanvasTransportError without leaking token')

print('PASS Canvas launcher live-transport fake tests complete')
PY

echo "PASS Canvas launcher live-transport fake tests complete"
