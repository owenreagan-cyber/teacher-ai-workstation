#!/usr/bin/env bash
set -euo pipefail

echo "Running Canvas LLM canvas drift tests..."

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

DRIFT="scripts/canvas_llm_phase22/canvas_drift.py"
REPAIR="scripts/canvas_llm_phase22/canvas_repair_center.py"

PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/teacher-ai-workstation-pycache" python3 -m py_compile "$DRIFT" "$REPAIR"
python3 "$DRIFT" self-test
python3 "$REPAIR" self-test

python3 - <<'PY'
import sys
from pathlib import Path

sys.path.insert(0, str(Path('.').resolve()))
from scripts.canvas_llm_phase22 import canvas_drift as drift
from scripts.canvas_llm_phase22 import canvas_writer as writer
from scripts.canvas_llm_phase22 import canvas_connector as connector
from scripts.canvas_llm_phase22 import canvas_repair_center as repair_center

writer.FAKE_CANVAS_STORE['pages'].clear()

expected = 'August Newsletter'
actual = 'July Newsletter'
body = '<p>content</p>'
target = 'newsletter-page'
writer.FAKE_CANVAS_STORE['pages'][target] = {
    'course_id': connector.SANDBOX_COURSE_ID,
    'title': actual,
    'body': body,
    'body_hash': writer.body_hash(actual, body),
}

stale = drift.build_drift_report(
    'artifact-newsletter',
    target_type='page',
    target_id=target,
    course_id=connector.SANDBOX_COURSE_ID,
    expected_title=expected,
    expected_hash=writer.body_hash(expected, body),
)
assert stale is not None
assert stale.difference_type == 'STALE_VERSION'
assert stale.requires_teacher_approval is True

missing = drift.build_drift_report(
    'artifact-missing',
    target_type='page',
    target_id='missing-object',
    course_id=connector.SANDBOX_COURSE_ID,
    expected_title='Weekly Agenda',
    expected_hash=writer.body_hash('Weekly Agenda', '<p>a</p>'),
)
assert missing is not None
assert missing.difference_type == 'OBJECT_MISSING'

version = drift.record_deployment_version(
    drift.CanvasDeploymentVersion(
        artifact_id='artifact-newsletter',
        content_hash=writer.body_hash(expected, body),
        canvas_object_id=target,
        revision=1,
        published_at='2026-07-26T00:00:00Z',
        verified_at='2026-07-26T00:00:00Z',
    )
)
assert drift.latest_deployment_version('artifact-newsletter') == version

summary = repair_center.build_repair_center([stale, missing])
assert summary.issues == 2
assert summary.needs_approval == 2
assert drift.drift_has_no_auto_repair()

print('PASS missing object drift detected')
print('PASS stale version drift detected')
print('PASS repair recommendation created')
print('PASS version tracking works')
PY

bin/chief-of-staff --canvas-repair-center | grep -q 'No repairs executed'

echo "PASS Canvas LLM canvas drift tests complete"
