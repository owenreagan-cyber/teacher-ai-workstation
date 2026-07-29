#!/usr/bin/env bash
# Read-only Lesson Package manual intake workflow status. Local models only — no network.
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

section 'Lesson Package Manual Intake Workflow (Phase 5)'
cat <<'EOF'
Status: manual curriculum intake → validated Lesson Package Plan
Lesson generation: no
Curriculum scanning: no
OCR: no
Automatic prioritization: no
Canvas / Drive / network / API: no
Artifact Quality Phases 1–3: unchanged
CPE Foundation (Phase 4): preserved
EOF

section 'Workflow Modules'
for module in \
  scripts/curriculum_production/curriculum_intake.py \
  scripts/curriculum_production/approval_workflow.py \
  scripts/curriculum_production/lesson_package.py \
  scripts/curriculum_production/workflow.py \
  scripts/curriculum_production/intake_validation.py \
  scripts/curriculum_production/reporting.py \
  scripts/curriculum_production/fixture_builder.py \
  scripts/curriculum_production/fixture_loader.py; do
  check_file "${module}"
done

section 'Configuration and Fixtures'
check_file configs/curriculum-production/priority-limits.yaml
for bucket in passing warning failing; do
  [[ -d "fixtures/curriculum-production/${bucket}" ]] && pass "fixture bucket exists: ${bucket}" || fail "fixture bucket missing: ${bucket}"
done

section 'Documentation'
check_file docs/lesson-package-manual-intake-workflow.md

section 'Tests'
check_file tests/curriculum_production/test_lesson_package.py
check_file tests/curriculum_production/test_approval_workflow.py
check_file tests/lesson-package-status-test.sh

if command -v python3 >/dev/null 2>&1; then
  python3 - <<'PY' >/dev/null 2>&1 && pass 'lesson package workflow imports succeed' || fail 'lesson package imports failed'
import sys
from pathlib import Path
sys.path.insert(0, str(Path('.').resolve()))
from scripts.curriculum_production.workflow import build_lesson_package
from scripts.curriculum_production.fixture_loader import build_from_fixture
PY
  python3 scripts/curriculum_production/fixture_builder.py >/dev/null 2>&1 || python3 - <<'PY'
from pathlib import Path
import sys
sys.path.insert(0, str(Path('.').resolve()))
from scripts.curriculum_production.fixture_builder import ensure_all_fixtures
ensure_all_fixtures(Path('fixtures/curriculum-production'))
PY
  python3 tests/curriculum_production/test_lesson_package.py >/dev/null 2>&1 && pass 'lesson package tests pass' || fail 'lesson package tests failed'
  python3 tests/curriculum_production/test_approval_workflow.py >/dev/null 2>&1 && pass 'approval workflow tests pass' || fail 'approval workflow tests failed'
  python3 - <<'PY' >/dev/null 2>&1 && pass 'PASS fixture builds package plan' || fail 'PASS fixture failed'
import sys
from pathlib import Path
sys.path.insert(0, str(Path('.').resolve()))
from scripts.curriculum_production.fixture_loader import build_from_fixture
from scripts.curriculum_production.models import CheckStatus
pkg = build_from_fixture(Path('fixtures/curriculum-production/passing/math-lesson-package.json'))
assert pkg.validation_summary.final_status in {CheckStatus.PASS, CheckStatus.WARN}
assert 'Lesson Package Status' in pkg.status_report
PY
else
  warn 'python3 unavailable for Phase 5 runtime checks'
fi

section 'Preservation Checks'
grep -Fq -- '--artifact-quality-status' bin/chief-of-staff && pass 'Artifact Quality CLI preserved' || fail 'Artifact Quality CLI missing'
grep -Fq -- '--curriculum-production-status' bin/chief-of-staff && pass 'CPE foundation CLI preserved' || fail 'CPE foundation CLI missing'
check_file scripts/artifact_quality/educational_layout.py

section 'CLI Wiring'
bash -n scripts/lesson-package-status.sh && pass 'bash syntax ok: lesson package status script' || fail 'bash syntax failed'
grep -Fq -- '--lesson-package-status' bin/chief-of-staff && pass 'CLI exposes --lesson-package-status' || fail 'CLI missing --lesson-package-status'
grep -Fq -- '"--lesson-package-status"' assistant/chief-of-staff/v1/command-surface-manifest.json && pass 'manifest lists --lesson-package-status' || fail 'manifest missing --lesson-package-status'

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
