#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python3 scripts/canvas_llm_phase22/validate_canonical_knowledge.py

python3 - <<'PY'
import json
from pathlib import Path

paths = [
    "config/curriculum/canvas-course-mappings.json",
    "config/curriculum/math/saxon-math-5/lesson-power-up-map.json",
    "config/curriculum/math/saxon-math-5/fact-test-practice-map.json",
    "config/curriculum/reading/reading-mastery-4/comprehension-location-map.json",
    "config/curriculum/spelling/cumulative-test-word-lists.json",
    "config/curriculum/canvas/agenda-page-rules.json",
]

for relative in paths:
    path = Path(relative)
    json.loads(path.read_text(encoding="utf-8"))
    print(f"PASS: valid JSON {relative}")
PY

if git ls-files '.local/*' | grep -q .; then
  echo "FAIL: tracked .local artifact found"
  exit 1
fi

echo "PASS: no .local artifacts tracked"

if git grep -nEi \
  'CANVAS_API_TOKEN[[:space:]]*=|service_role_key[[:space:]]*=|private_key[[:space:]]*=' \
  -- \
  config/curriculum \
  docs/programs/teacher-knowledge-vault \
  docs/programs/canvas-llm/phase-22-predictive-weekly-planning-workstation/canonical-owner-rules.md \
  scripts/canvas_llm_phase22/validate_canonical_knowledge.py \
  tests/canvas-llm-phase-22-canonical-knowledge-test.sh
then
  echo "FAIL: possible secret assignment found"
  exit 1
fi

echo "PASS: no secret assignments found"
echo "PASS: canonical knowledge validation complete"
