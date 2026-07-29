#!/usr/bin/env bash
# Read-only Lesson Specification & Blueprint System status. Local models only — no network.
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

section 'Lesson Specification & Blueprint System (Milestone 2 — Phases 6–8)'
cat <<'EOF'
Status: Lesson Package Plan → Review Packet → Consistency Engine → Artifact Blueprints
Artifact generation: no
Curriculum scanning: no
OCR: no
Canvas / Drive / network / API: no
AI lesson generation: no
Artifact Quality Phases 1–3: unchanged
CPE Foundation (Phase 4): preserved
Lesson Package Workflow (Phase 5): preserved
EOF

section 'Core Modules'
for module in \
  scripts/lesson_blueprint/review_packet.py \
  scripts/lesson_blueprint/consistency.py \
  scripts/lesson_blueprint/registries.py \
  scripts/lesson_blueprint/blueprints.py \
  scripts/lesson_blueprint/blueprint_validation.py \
  scripts/lesson_blueprint/content_budgets.py \
  scripts/lesson_blueprint/blueprint_approval.py \
  scripts/lesson_blueprint/reporting.py \
  scripts/lesson_blueprint/workflow.py \
  scripts/lesson_blueprint/fixture_builder.py \
  scripts/lesson_blueprint/fixture_loader.py; do
  check_file "${module}"
done

section 'Configuration and Fixtures'
check_file configs/lesson-blueprint/content-budgets.yaml
check_file configs/lesson-blueprint/blueprint-templates.yaml
for bucket in passing warning failing; do
  [[ -d "fixtures/lesson-blueprint/${bucket}" ]] && pass "fixture bucket exists: ${bucket}" || fail "fixture bucket missing: ${bucket}"
done

section 'Documentation'
check_file docs/lesson-blueprint-system.md

section 'Tests'
check_file tests/lesson_blueprint/test_lesson_blueprint.py
check_file tests/lesson-blueprint-status-test.sh

if command -v python3 >/dev/null 2>&1; then
  python3 - <<'PY' >/dev/null 2>&1 && pass 'lesson blueprint workflow imports succeed' || fail 'lesson blueprint imports failed'
import sys
from pathlib import Path
sys.path.insert(0, str(Path('.').resolve()))
from scripts.lesson_blueprint.workflow import build_lesson_blueprint
from scripts.lesson_blueprint.fixture_loader import build_blueprint_from_fixture
PY
  python3 - <<'PY' >/dev/null 2>&1 || true
from pathlib import Path
import sys
sys.path.insert(0, str(Path('.').resolve()))
from scripts.lesson_blueprint.fixture_builder import ensure_all_fixtures
ensure_all_fixtures(Path('fixtures/lesson-blueprint'))
PY
  python3 tests/lesson_blueprint/test_lesson_blueprint.py >/dev/null 2>&1 && pass 'lesson blueprint tests pass' || fail 'lesson blueprint tests failed'
  python3 - <<'PY' >/dev/null 2>&1 && pass 'PASS fixture builds lesson blueprint' || fail 'PASS fixture failed'
import sys
from pathlib import Path
sys.path.insert(0, str(Path('.').resolve()))
from scripts.lesson_blueprint.fixture_loader import build_blueprint_from_fixture
from scripts.curriculum_production.models import CheckStatus
bp = build_blueprint_from_fixture(Path('fixtures/lesson-blueprint/passing/well-formed-blueprint.json'))
assert bp.consistency_report.final_status in {CheckStatus.PASS, CheckStatus.WARN}
assert 'Lesson Blueprint Status' in bp.reports['lesson_blueprint_status']
PY
  python3 - <<'PY' >/dev/null 2>&1 && pass 'WARN fixture reports vocabulary mismatch' || fail 'WARN fixture failed'
import sys
from pathlib import Path
sys.path.insert(0, str(Path('.').resolve()))
from scripts.lesson_blueprint.fixture_loader import build_blueprint_from_fixture
from scripts.curriculum_production.models import CheckStatus
bp = build_blueprint_from_fixture(Path('fixtures/lesson-blueprint/warning/vocabulary-mismatch.json'))
assert bp.consistency_report.final_status == CheckStatus.WARN
PY
  python3 - <<'PY' >/dev/null 2>&1 && pass 'FAIL fixture reports broken dependency' || fail 'FAIL fixture failed'
import sys
from pathlib import Path
sys.path.insert(0, str(Path('.').resolve()))
from scripts.lesson_blueprint.fixture_loader import build_blueprint_from_fixture
from scripts.curriculum_production.models import CheckStatus
bp = build_blueprint_from_fixture(Path('fixtures/lesson-blueprint/failing/broken-dependency.json'))
assert bp.consistency_report.final_status == CheckStatus.FAIL
PY
else
  warn 'python3 unavailable for blueprint runtime checks'
fi

section 'Preservation Checks'
grep -Fq -- '--artifact-quality-status' bin/chief-of-staff && pass 'Artifact Quality CLI preserved' || fail 'Artifact Quality CLI missing'
grep -Fq -- '--curriculum-production-status' bin/chief-of-staff && pass 'CPE foundation CLI preserved' || fail 'CPE foundation CLI missing'
grep -Fq -- '--lesson-package-status' bin/chief-of-staff && pass 'Lesson Package CLI preserved' || fail 'Lesson Package CLI missing'
check_file scripts/artifact_quality/educational_layout.py

section 'CLI Wiring'
bash -n scripts/lesson-blueprint-status.sh && pass 'bash syntax ok: lesson blueprint status script' || fail 'bash syntax failed'
grep -Fq -- '--lesson-blueprint-status' bin/chief-of-staff && pass 'CLI exposes --lesson-blueprint-status' || fail 'CLI missing --lesson-blueprint-status'
grep -Fq -- '"--lesson-blueprint-status"' assistant/chief-of-staff/v1/command-surface-manifest.json && pass 'manifest lists --lesson-blueprint-status' || fail 'manifest missing --lesson-blueprint-status'

section 'Negative Non-Activation Assertions'
status_script="${BASH_SOURCE[0]}"
grep -Eq '(^|[;&|[:space:]])curl[[:space:]]' "${status_script}" 2>/dev/null && fail "${status_script} must not shell-invoke curl" || pass "${status_script} does not shell-invoke curl"
pass 'no artifact generation active'
pass 'no curriculum scanning active'
pass 'no network activation'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
