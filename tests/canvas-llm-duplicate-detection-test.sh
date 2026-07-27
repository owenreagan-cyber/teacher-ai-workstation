#!/usr/bin/env bash
set -euo pipefail

echo "Running Canvas LLM duplicate detection tests..."

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

DETECTOR="scripts/canvas_llm_phase22/canvas_duplicate_detector.py"

PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/teacher-ai-workstation-pycache" python3 -m py_compile "$DETECTOR"
python3 "$DETECTOR" self-test

python3 - <<'PY'
from pathlib import Path
import sys

sys.path.insert(0, str(Path('.').resolve()))
from scripts.canvas_llm_phase22 import canvas_duplicate_detector as detector

reports = detector.detect_duplicates()
page = next(item for item in reports if item.object_type == 'page')
assert detector.PAGE_TITLE in page.titles
assert 'Q1W2 Weekly Agenda Copy' in page.titles
assert page.safe_action == 'PROTECTED'
assert 'Front Page protected' in (page.detail or '')

assignment = next(
    item for item in reports
    if item.object_type == 'assignment' and 'SM5: Lesson 2' in item.titles
)
assert assignment.safe_action == 'BLOCKED'
assert 'grading activity' in (assignment.detail or '').lower()

reading = next(
    item for item in reports
    if item.object_type == 'assignment' and 'RM4: Lesson 3' in item.titles
)
assert reading.safe_action == 'SAFE_DELETE_CANDIDATE'

announcement = next(
    item for item in reports
    if item.object_type == 'announcement' and item.safe_action == 'NEEDS_APPROVAL'
)
assert announcement.requires_teacher_approval is True

summary = detector.scan_duplicates()
assert summary.pages_status == 'PASS'
assert summary.assignments_status == 'PASS'
assert summary.announcements_status == 'PASS'

assert detector.duplicate_detector_has_no_writes()

print('PASS page duplicate detection')
print('PASS front page protection')
print('PASS assignment grade protection')
print('PASS announcement detection')
PY

bin/chief-of-staff --canvas-duplicate-scan | grep -q 'Canvas Duplicate Scan'
bin/chief-of-staff --canvas-duplicate-scan | grep -q 'PASS'

echo "PASS Canvas LLM duplicate detection tests complete"
