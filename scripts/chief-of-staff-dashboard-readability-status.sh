#!/usr/bin/env bash
# Read-only dashboard readability status only. No network calls or file operations.
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
  if grep -Fq "${phrase}" "${readability_doc}"; then
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

readability_doc="docs/chief-of-staff-dashboard-readability-pass.md"
return_to_core_doc="docs/return-to-chief-of-staff-core.md"
dashboard_script="scripts/chief-of-staff-dashboard.sh"

section 'Chief of Staff Dashboard Readability Pass'
cat <<'EOF'
Status: readability/status only
Dashboard checks preserved: yes
PASS/WARN/FAIL semantics preserved: yes
Existing commands preserved: yes
Live integrations: no
Network calls: no
Automation added: no
Wallpaper/photo curator implementation: not started
Student data: no
EOF

section 'Workflow Checks'

check_file "${readability_doc}"

if [[ -f "${readability_doc}" ]]; then
  check_doc_contains "dashboard readability" "dashboard readability"
  check_doc_contains "preserving all existing checks" "preserving all existing checks"
  check_doc_contains "PASS/WARN/FAIL semantics" "preserving PASS/WARN/FAIL semantics"
  check_doc_contains "preserving existing commands" "preserving existing commands"
  check_doc_contains "Appearance & Vibe foundation checks" "Appearance & Vibe foundation checks"
  check_doc_contains "live wallpaper/photo curator implementation remains not started" "live wallpaper/photo curator implementation remains not started"
  check_doc_contains "no network calls" "no network calls"
  check_doc_contains "no automation" "no automation"
  check_doc_contains "no student data" "no student data"
fi

check_file "${return_to_core_doc}"
check_file "${dashboard_script}"

check_bash_syntax 'bin/chief-of-staff'
check_bash_syntax "${dashboard_script}"
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
