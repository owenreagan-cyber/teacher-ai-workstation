#!/usr/bin/env bash
set -euo pipefail

echo "Running Canvas LLM pacing parser tests..."

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

PARSER="scripts/canvas_llm_phase22/pacing_parser.py"

PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/teacher-ai-workstation-pycache" python3 -m py_compile "$PARSER"
python3 "$PARSER" self-test

python3 - <<'PY'
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path('.').resolve()))
from scripts.canvas_llm_phase22 import pacing_parser as pacing
from scripts.canvas_llm_phase22 import phase22_workstation as p22
from scripts.canvas_llm_phase22 import artifact_registry as reg

week_meta = {'code': 'Q1W2', 'startsOn': '2026-08-10', 'endsOn': '2026-08-14', 'quarter': 1, 'week': 2}
rows = [
    {'subject': 'math', 'weekday': 'Monday', 'entry_date': '2026-08-10', 'lesson': '2', 'tests': '', 'title': 'Lesson 2', 'notes': ''},
    {'subject': 'math', 'weekday': 'Friday', 'entry_date': '2026-08-14', 'lesson': '6', 'tests': '', 'title': 'Lesson 6', 'notes': ''},
    {'subject': 'reading', 'weekday': 'Monday', 'entry_date': '2026-08-10', 'lesson': '2', 'tests': '', 'title': 'Lesson 2', 'notes': ''},
    {'subject': 'spelling', 'weekday': 'Friday', 'entry_date': '2026-08-14', 'lesson': '', 'tests': '5', 'title': 'Spelling Test 5', 'notes': ''},
]
plan = pacing.parse_rows_to_plan(week_meta, rows)
assert plan.week_code == 'Q1W2'
assert plan.lessons['math'] == ['2', '6']
assert 'Spelling Test 5' in plan.assessments['spelling']

temp_db = Path(tempfile.mkstemp(suffix='.sqlite3')[1])
db = p22.WorkstationDB(temp_db)
db.migrate()
db.seed_from_fixture()
wid = reg.seed_demo_week(db)
db_plan = pacing.parse_week_from_db(db, wid)
assert db_plan.week_code
assert db_plan.subject_plans

temp_db.unlink(missing_ok=True)

print('PASS weekly plan parsing')
print('PASS lesson extraction')
print('PASS assessment extraction')
PY

echo "PASS Canvas LLM pacing parser tests complete"
