#!/usr/bin/env bash
set -euo pipefail

echo "Running Canvas LLM assignment draft generator tests..."

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

GENERATOR="scripts/canvas_llm_phase22/assignment_draft_generator.py"

PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/teacher-ai-workstation-pycache" python3 -m py_compile "$GENERATOR"
python3 "$GENERATOR" self-test

python3 - <<'PY'
import sys
from pathlib import Path

sys.path.insert(0, str(Path('.').resolve()))
from scripts.canvas_llm_phase22 import pacing_parser as pacing
from scripts.canvas_llm_phase22 import assignment_draft_generator as gen

week_meta = {'code': 'Q1W2', 'startsOn': '2026-08-10', 'endsOn': '2026-08-14'}
rows = [
    {'subject': 'math', 'weekday': 'Monday', 'entry_date': '2026-08-10', 'lesson': '2', 'tests': '', 'title': 'Lesson 2', 'notes': ''},
    {'subject': 'math', 'weekday': 'Tuesday', 'entry_date': '2026-08-11', 'lesson': '3', 'tests': '', 'title': 'Lesson 3', 'notes': ''},
    {'subject': 'math', 'weekday': 'Wednesday', 'entry_date': '2026-08-12', 'lesson': '4', 'tests': '', 'title': 'Lesson 4', 'notes': ''},
    {'subject': 'math', 'weekday': 'Thursday', 'entry_date': '2026-08-13', 'lesson': '5', 'tests': '', 'title': 'Lesson 5', 'notes': ''},
    {'subject': 'reading', 'weekday': 'Monday', 'entry_date': '2026-08-10', 'lesson': '2', 'tests': '', 'title': 'Lesson 2', 'notes': ''},
    {'subject': 'reading', 'weekday': 'Tuesday', 'entry_date': '2026-08-11', 'lesson': '3', 'tests': '', 'title': 'Lesson 3', 'notes': ''},
    {'subject': 'reading', 'weekday': 'Wednesday', 'entry_date': '2026-08-12', 'lesson': '4', 'tests': '', 'title': 'Lesson 4', 'notes': ''},
    {'subject': 'reading', 'weekday': 'Thursday', 'entry_date': '2026-08-13', 'lesson': '5', 'tests': '', 'title': 'Lesson 5', 'notes': ''},
    {'subject': 'spelling', 'weekday': 'Friday', 'entry_date': '2026-08-14', 'lesson': '', 'tests': '5', 'title': 'Spelling Test 5', 'notes': ''},
    {'subject': 'history', 'weekday': 'Monday', 'entry_date': '2026-08-10', 'lesson': '1', 'tests': '', 'title': 'Chapter 1', 'notes': ''},
]
plan = pacing.parse_rows_to_plan(week_meta, rows)
drafts = gen.generate_drafts_from_plan(plan)
summary = gen.summarize_drafts(drafts, plan.week_code)

assert summary.generated >= 8
assert summary.needs_review >= 2
assert summary.blocked >= 1

for draft in drafts:
    assert draft.artifact_id and draft.content_hash and draft.source_rule
    record = gen.draft_to_registry_record(draft)
    assert record.artifact_id == draft.artifact_id
    assert record.canvas_writes_allowed is False

queue_items = gen.build_queue_items_for_drafts(drafts)
assert len(queue_items) == len(drafts)

decisions = gen.teacher_decision_points_for_drafts(drafts)
assert decisions
assert all(d['automatic_selection'] is False for d in decisions)

assert gen.generator_performs_no_canvas_writes()

print('PASS draft creation')
print('PASS policies attached')
print('PASS teacher decision points')
print('PASS artifact IDs and registry integration')
PY

bin/chief-of-staff --assignment-draft-preview | grep -q 'No Canvas writes performed'

echo "PASS Canvas LLM assignment draft generator tests complete"
