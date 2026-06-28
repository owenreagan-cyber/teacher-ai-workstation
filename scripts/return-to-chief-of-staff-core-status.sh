#!/usr/bin/env bash
# Read-only return-to-core status only. No network calls or file operations.
set -euo pipefail

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

pass() {
  PASS_COUNT=$((PASS_COUNT + 1))
  printf 'PASS: %s\n' "$1"
}

warn() {
  WARN_COUNT=$((WARN_COUNT + 1))
  printf 'WARN: %s\n' "$1"
}

fail() {
  FAIL_COUNT=$((FAIL_COUNT + 1))
  printf 'FAIL: %s\n' "$1"
}

section() {
  printf '\n%s\n' "$1"
  printf '%s\n' '----------------------------------------'
}

check_file() {
  local path="$1"
  if [[ -f "${path}" ]]; then
    pass "file exists: ${path}"
  else
    fail "file missing: ${path}"
  fi
}

check_bash_syntax() {
  local path="$1"
  if [[ ! -f "${path}" ]]; then
    fail "cannot syntax check missing file: ${path}"
    return
  fi

  if bash -n "${path}"; then
    pass "bash syntax ok: ${path}"
  else
    fail "bash syntax failed: ${path}"
  fi
}

check_doc_contains() {
  local phrase="$1"
  local label="$2"
  if grep -Fq "${phrase}" "${core_doc}"; then
    pass "doc mentions ${label}"
  else
    fail "doc must mention ${label}"
  fi
}

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "${repo_root}" ]]; then
  repo_root="$(cd "${script_dir}/.." && pwd -P)"
fi
cd "${repo_root}"

core_doc="docs/return-to-chief-of-staff-core.md"
rotation_audit_doc="docs/wallpaper-photo-rotation-handoff-safety-audit.md"
curator_readme="assistant/appearance-vibe/wallpaper-photo-curator/README.md"

section 'Return to Chief of Staff / Teacher Workstation Core'
cat <<'EOF'
Status: planning/status only
Appearance & Vibe foundation stack: complete for now
Live wallpaper/photo curator: not started
Live fetcher: no
Live image processor: no
Live scheduler: no
Live notifications: no
Live UI: no
Network calls: no
Reddit integration: no
Devvit integration: no
3D Design Factory Agent: parked
EOF

section 'Workflow Checks'

check_file "${core_doc}"

if [[ -f "${core_doc}" ]]; then
  check_doc_contains "Appearance & Vibe wallpaper/photo curator foundation stack is complete for now" "Appearance & Vibe wallpaper/photo curator foundation stack is complete for now"
  check_doc_contains "Live wallpaper/photo curator implementation is not started" "live curator implementation is not started"
  check_doc_contains "No real fetcher exists" "no real fetcher"
  check_doc_contains "No real image processor exists" "no real image processor"
  check_doc_contains "No real scheduler exists" "no real scheduler"
  check_doc_contains "No real notifications exist" "no real notifications"
  check_doc_contains "No live UI exists" "no live UI"
  check_doc_contains "Reddit remains a possible future source only" "Reddit future-only"
  check_doc_contains "Devvit remains a possible future Reddit-native companion only" "Devvit future-only"
  check_doc_contains "3D Design Factory Agent remains parked" "3D Design Factory Agent remains parked"
  check_doc_contains "Chief of Staff dashboard readability pass" "Chief of Staff dashboard readability pass"
fi

check_file "${rotation_audit_doc}"
check_file "${curator_readme}"

check_bash_syntax 'bin/chief-of-staff'
check_bash_syntax 'scripts/chief-of-staff-dashboard.sh'
check_bash_syntax 'scripts/phase-1-status.sh'

pass 'no write action attempted'
pass 'no network call attempted'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"

if [[ "${FAIL_COUNT}" -gt 0 ]]; then
  exit 1
fi

exit 0
