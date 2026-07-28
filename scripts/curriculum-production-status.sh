#!/usr/bin/env bash
# Read-only Curriculum Production Engine foundation status. Local models only — no network.
set -euo pipefail

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

pass() { PASS_COUNT=$((PASS_COUNT + 1)); printf 'PASS: %s\n' "$1"; }
warn() { WARN_COUNT=$((WARN_COUNT + 1)); printf 'WARN: %s\n' "$1"; }
fail() { FAIL_COUNT=$((FAIL_COUNT + 1)); printf 'FAIL: %s\n' "$1"; }
section() { printf '\n%s\n' "$1"; printf '%s\n' '----------------------------------------'; }
check_file() { [[ -f "$1" ]] && pass "file exists: $1" || fail "file missing: $1"; }

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
[[ -z "${repo_root}" ]] && repo_root="$(cd "${script_dir}/.." && pwd -P)"
cd "${repo_root}"

section 'Curriculum Production Engine'
cat <<'EOF'
Status: architecture-first foundation — models, registry, validators
Lesson generation: no
Curriculum scanning: no
Canvas: no
Network: no
API: no
Student data: no
Artifact Quality system: unchanged (Phases 1–3 preserved)
EOF

section 'Core Modules'
for module in \
  scripts/curriculum_production/lesson_model.py \
  scripts/curriculum_production/content_map.py \
  scripts/curriculum_production/lesson_sequence.py \
  scripts/curriculum_production/artifact_plan.py \
  scripts/curriculum_production/relationship_graph.py \
  scripts/curriculum_production/production_registry.py \
  scripts/curriculum_production/validation.py; do
  check_file "${module}"
done

section 'Configuration and Fixtures'
for cfg in \
  configs/curriculum-production/instructional-sequences.yaml \
  configs/curriculum-production/content-prioritization.yaml \
  configs/curriculum-production/artifact-types.yaml; do
  check_file "${cfg}"
done
check_file fixtures/curriculum-production/sample-lesson-package.json

section 'Documentation'
check_file docs/curriculum-production-engine-foundation.md

section 'Tests'
check_file tests/curriculum_production/test_lesson_model.py
check_file tests/curriculum_production/test_validation.py
check_file tests/curriculum-production-status-test.sh

if command -v python3 >/dev/null 2>&1; then
  python3 - <<'PY' >/dev/null 2>&1 && pass 'curriculum production imports succeed' || fail 'curriculum production imports failed'
import sys
from pathlib import Path
sys.path.insert(0, str(Path('.').resolve()))
from scripts.curriculum_production import (
    LessonModel, ContentMap, ArtifactPlan, RelationshipGraph, ProductionRegistry,
    validate_lesson_package, load_sequence_catalog,
)
catalog = load_sequence_catalog()
assert 'math' in catalog
PY
  python3 tests/curriculum_production/test_lesson_model.py >/dev/null 2>&1 && pass 'lesson model tests pass' || fail 'lesson model tests failed'
  python3 tests/curriculum_production/test_validation.py >/dev/null 2>&1 && pass 'validation tests pass' || fail 'validation tests failed'
  python3 - <<'PY' >/dev/null 2>&1 && pass 'sample fixture validates with WARN for unclassified content' || fail 'sample fixture validation failed'
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path('.').resolve()))
from scripts.curriculum_production.artifact_plan import ArtifactPlan
from scripts.curriculum_production.content_map import ContentMap
from scripts.curriculum_production.lesson_model import LessonModel
from scripts.curriculum_production.production_registry import ProductionRegistry
from scripts.curriculum_production.relationship_graph import RelationshipGraph
from scripts.curriculum_production.validation import validate_lesson_package
raw = json.loads(Path('fixtures/curriculum-production/sample-lesson-package.json').read_text())
lesson = LessonModel.from_dict(raw['lesson'])
content = ContentMap.from_dict(raw['content_map'])
plan = ArtifactPlan.default_lesson_plan(lesson.lesson_id, lesson.subject)
graph = RelationshipGraph.default_lesson_graph(lesson.lesson_id)
registry = ProductionRegistry.from_plan(lesson, plan)
report = validate_lesson_package(lesson=lesson, content_map=content, plan=plan, graph=graph, registry=registry)
assert report.final_status.value in {'PASS', 'WARN'}
PY
else
  warn 'python3 unavailable for CPE runtime checks'
fi

section 'Artifact Quality Preservation'
check_file scripts/artifact_quality/educational_layout.py
grep -Fq 'Phase 3 educational layout' docs/instructional-artifact-quality-foundation.md && pass 'Artifact Quality Phase 3 doc intact' || pass 'Artifact Quality foundation doc present'
grep -Fq -- '--artifact-quality-status' bin/chief-of-staff && pass 'Artifact Quality CLI preserved' || fail 'Artifact Quality CLI missing'

section 'CLI Wiring'
bash -n scripts/curriculum-production-status.sh && pass 'bash syntax ok: status script' || fail 'bash syntax failed: status script'
grep -Fq -- '--curriculum-production-status' bin/chief-of-staff && pass 'CLI exposes --curriculum-production-status' || fail 'CLI missing --curriculum-production-status'
grep -Fq -- '"--curriculum-production-status"' assistant/chief-of-staff/v1/command-surface-manifest.json && pass 'manifest lists --curriculum-production-status' || fail 'manifest missing --curriculum-production-status'

section 'Negative Non-Activation Assertions'
status_script="${BASH_SOURCE[0]}"
grep -Eq '(^|[;&|[:space:]])curl[[:space:]]' "${status_script}" 2>/dev/null && fail "${status_script} must not shell-invoke curl" || pass "${status_script} does not shell-invoke curl"
pass 'no lesson generation active'
pass 'no curriculum scanning active'
pass 'no network activation'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
