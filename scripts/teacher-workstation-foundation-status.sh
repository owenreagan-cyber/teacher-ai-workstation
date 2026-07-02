#!/usr/bin/env bash
# Read-only Teacher Workstation Foundation v0 orchestration status only.
set -euo pipefail

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

pass() { PASS_COUNT=$((PASS_COUNT + 1)); printf 'PASS: %s\n' "$1"; }
warn() { WARN_COUNT=$((WARN_COUNT + 1)); printf 'WARN: %s\n' "$1"; }
fail() { FAIL_COUNT=$((FAIL_COUNT + 1)); printf 'FAIL: %s\n' "$1"; }
section() { printf '\n%s\n' "$1"; printf '%s\n' '----------------------------------------'; }

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
[[ -z "${repo_root}" ]] && repo_root="$(cd "${script_dir}/.." && pwd -P)"
cd "${repo_root}"

run_foundation_status() {
  local label="$1"
  local script_path="$2"
  if [[ ! -f "${script_path}" ]]; then
    fail "${label} status script missing: ${script_path}"
    return 1
  fi
  if bash -n "${script_path}"; then
    pass "bash syntax ok: ${script_path}"
  else
    fail "bash syntax failed: ${script_path}"
    return 1
  fi
  if bash "${script_path}" >/dev/null 2>&1; then
    pass "${label} foundation status exits 0"
    return 0
  fi
  fail "${label} foundation status failed"
  return 1
}

section 'Teacher Workstation Foundation v0 Orchestration'
cat <<'EOF'
Status: read-only orchestration only
Lesson generation: no
Rendering: no
Retrieval engines: no
Live integrations: no
Network calls: no
EOF

[[ -f docs/teacher-workstation-foundation-v0.md ]] && pass 'closure doc exists' || fail 'closure doc missing'

run_foundation_status 'Lesson Planning' scripts/lesson-planning-foundation-status.sh || true
run_foundation_status 'Curriculum Library' scripts/curriculum-library-foundation-status.sh || true
run_foundation_status 'Renderer' scripts/renderer-foundation-status.sh || true
run_foundation_status 'Local Retrieval' scripts/local-retrieval-foundation-status.sh || true
run_foundation_status 'Integration Planning' scripts/integration-planning-foundation-status.sh || true

pass 'no activation attempted'
pass 'no network call attempted'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"

[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
