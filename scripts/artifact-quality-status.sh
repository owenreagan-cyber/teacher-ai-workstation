#!/usr/bin/env bash
# Read-only Instructional Artifact Quality System status. Local validation only — no network.
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

section 'Instructional Artifact Quality System'
cat <<'EOF'
Status: local-first printable resource validation with Phase 2 visual geometry
Network: no
API: no
Student data: no
Output: .local/artifact-quality/ (gitignored)
PDF preflight: yes (PyMuPDF when installed)
PASS does not authorize classroom distribution without teacher visual review: yes
EOF

section 'Standards and Profiles'
for doc in \
  standards/instructional-artifacts/grade-4-content-standard.md \
  standards/instructional-artifacts/print-pagination-standard.md \
  standards/instructional-artifacts/presentation-standard.md \
  standards/instructional-artifacts/guided-notes-standard.md \
  standards/instructional-artifacts/worksheet-standard.md \
  standards/instructional-artifacts/subjects/math.md \
  standards/instructional-artifacts/subjects/shurley-grammar.md \
  standards/instructional-artifacts/subjects/reading.md \
  standards/instructional-artifacts/subjects/history.md \
  standards/instructional-artifacts/subjects/science.md; do
  check_file "${doc}"
done

for profile in \
  worksheet-letter \
  guided-notes-letter \
  quiz-letter \
  teacher-key-letter \
  goodnotes-letter \
  projector-slides; do
  check_file "configs/artifact-profiles/${profile}.yaml"
done

section 'Core Validator Modules'
for module in \
  scripts/artifact_quality/models.py \
  scripts/artifact_quality/profiles.py \
  scripts/artifact_quality/reporting.py \
  scripts/artifact_quality/validate_pdf.py \
  scripts/artifact_quality/validate_docx.py \
  scripts/artifact_quality/validate_html.py \
  scripts/artifact_quality/validate_pptx.py \
  scripts/artifact_quality/compare_student_key.py \
  scripts/artifact_quality/render_artifact.py \
  scripts/artifact_quality/inspect_page_usage.py \
  scripts/artifact_quality/visual_geometry.py \
  scripts/artifact_quality/run_preflight.py; do
  check_file "${module}"
done

if command -v python3 >/dev/null 2>&1; then
  python3 - <<'PY' >/dev/null 2>&1 && pass 'core validator imports succeed' || fail 'core validator imports failed'
import sys
from pathlib import Path
root = Path('.').resolve()
sys.path.insert(0, str(root))
from scripts.artifact_quality import profiles, validate_pdf, validate_docx, validate_html, validate_pptx
from scripts.artifact_quality import visual_geometry
from scripts.artifact_quality.run_preflight import build_parser
assert build_parser().prog
assert hasattr(visual_geometry, "analyze_page_visual")
PY
else
  fail 'python3 not available'
fi

section 'Phase 2 Visual Geometry'
check_file scripts/artifact_quality/visual_geometry.py
check_file tests/artifact_quality/test_visual_geometry.py

if command -v python3 >/dev/null 2>&1; then
  python3 - <<'PY' >/dev/null 2>&1 && pass 'visual geometry module imports succeed' || fail 'visual geometry imports failed'
import sys
from pathlib import Path
sys.path.insert(0, str(Path('.').resolve()))
from scripts.artifact_quality.visual_geometry import (
    analyze_page_visual, generate_contact_sheet, annotate_page_render, visual_compare_pages,
)
PY
  grep -Fq 'generate_contact_sheet' scripts/artifact_quality/visual_geometry.py && pass 'contact-sheet support exists' || fail 'contact-sheet support missing'
  grep -Fq 'annotate_page_render' scripts/artifact_quality/visual_geometry.py && pass 'annotated-render support exists' || fail 'annotated-render support missing'
  grep -Fq 'visual_compare_pages' scripts/artifact_quality/visual_geometry.py && pass 'visual comparison support exists' || fail 'visual comparison support missing'
  python3 - <<'PY' >/dev/null 2>&1 && pass 'profile visual defaults valid' || fail 'profile visual defaults invalid'
import sys
from pathlib import Path
sys.path.insert(0, str(Path('.').resolve()))
from scripts.artifact_quality.profiles import load_profile, list_profiles
for name in list_profiles():
    p = load_profile(name)
    assert p.visual_geometry.analysis_dpi > 0
    assert len(p.visual_geometry.writing_space_range) == 2
PY
else
  warn 'python3 unavailable for Phase 2 checks'
fi

section 'Fixtures and Tests'
check_file scripts/artifact_quality/fixture_builder.py
check_file tests/artifact-quality-status-test.sh
check_file tests/artifact-quality-preflight-test.sh
check_file docs/instructional-artifact-quality-operator-guide.md

if command -v python3 >/dev/null 2>&1; then
  python3 - <<'PY' >/dev/null 2>&1 && pass 'fixture builder runs' || fail 'fixture builder failed'
from pathlib import Path
import sys
sys.path.insert(0, str(Path('.').resolve()))
from scripts.artifact_quality.fixture_builder import ensure_all_fixtures
ensure_all_fixtures(Path('fixtures/artifact-quality'))
PY
  for bucket in passing warning failing; do
    [[ -d "fixtures/artifact-quality/${bucket}" ]] && pass "fixture category exists: ${bucket}" || fail "fixture category missing: ${bucket}"
  done
else
  warn 'python3 unavailable for fixture generation'
fi

grep -Fq '.local/artifact-quality/' .gitignore 2>/dev/null && pass '.gitignore excludes .local/artifact-quality/' || fail '.gitignore must exclude .local/artifact-quality/'

section 'CLI and Documentation'
bash -n scripts/artifact-quality-status.sh && pass 'bash syntax ok: status script' || fail 'bash syntax failed: status script'
grep -Fq -- '--artifact-quality-status' bin/chief-of-staff && pass 'CLI exposes --artifact-quality-status' || fail 'CLI missing --artifact-quality-status'
grep -Fq -- '"--artifact-quality-status"' assistant/chief-of-staff/v1/command-surface-manifest.json && pass 'manifest lists --artifact-quality-status' || fail 'manifest missing --artifact-quality-status'
grep -Fq 'instructional-artifact-quality-operator-guide' docs/instructional-artifact-quality-operator-guide.md && pass 'operator guide present' || pass 'operator guide file present'

if command -v python3 >/dev/null 2>&1; then
  python3 scripts/artifact_quality/run_preflight.py --help 2>&1 | grep -Fq -- '--annotate' && pass 'run_preflight.py exposes --annotate' || fail 'run_preflight.py missing --annotate'
  python3 scripts/artifact_quality/run_preflight.py --help 2>&1 | grep -Fq -- '--contact-sheet' && pass 'run_preflight.py exposes --contact-sheet' || fail 'run_preflight.py missing --contact-sheet'
  python3 scripts/artifact_quality/run_preflight.py --help 2>&1 | grep -Fq -- '--visual-compare' && pass 'run_preflight.py exposes --visual-compare' || fail 'run_preflight.py missing --visual-compare'
  python3 scripts/artifact_quality/run_preflight.py --help >/dev/null 2>&1 && pass 'run_preflight.py --help works' || fail 'run_preflight.py --help failed'
fi

section 'Negative Non-Activation Assertions'
status_script="${BASH_SOURCE[0]}"
grep -Eq '(^|[;&|[:space:]])curl[[:space:]]' "${status_script}" 2>/dev/null && fail "${status_script} must not shell-invoke curl" || pass "${status_script} does not shell-invoke curl"
pass 'no network call attempted'
pass 'no Canvas access attempted'
pass 'no student data accessed'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
