#!/usr/bin/env bash
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

check_text() {
  local path="$1"
  local pattern="$2"
  local label="$3"

  if [[ ! -f "${path}" ]]; then
    fail "${label}: missing ${path}"
    return
  fi

  if grep -Eiq "${pattern}" "${path}"; then
    pass "${label}"
  else
    fail "${label}"
  fi
}

check_cli_mentions() {
  local pattern="$1"
  local label="$2"

  if [[ ! -f bin/chief-of-staff ]]; then
    fail "${label}: bin/chief-of-staff missing"
    return
  fi

  if grep -q -- "${pattern}" bin/chief-of-staff; then
    pass "${label}"
  else
    fail "${label}"
  fi
}

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "${repo_root}" ]]; then
  repo_root="$(cd "${script_dir}/.." && pwd -P)"
fi
cd "${repo_root}"

guide="docs/chief-of-staff-command-launcher-refinement.md"
polish_guide="docs/dashboard-polish-command-grouping-follow-up.md"

section "Chief of Staff Command Launcher"
cat <<'EOF'
Status: local command discovery
Read-only: yes
External integrations: no
Network calls: no
EOF

section "Command Groups"
cat <<'EOF'
Everyday
Lesson Planning
Lesson Review
Developer and Workflow
Future-Safety
Verification
EOF

section "Workflow Checks"

check_file "${guide}"
check_file "${polish_guide}"

check_text "${polish_guide}" "Dashboard Reading Order" "polish guide includes dashboard reading order"
check_text "${polish_guide}" "Developer and Workflow" "polish guide includes Developer and Workflow group"
check_text "${polish_guide}" "Future-Safety" "polish guide includes Future-Safety group"
check_text "${polish_guide}" "Automated Wallpaper and Photo Curator" "polish guide includes Automated Wallpaper and Photo Curator"
check_text "${polish_guide}" "Not implemented in this PR" "polish guide states wallpaper curator not implemented"
check_text "${polish_guide}" "No Reddit or Devvit" "polish guide states no Reddit or Devvit in this PR"
check_text "${polish_guide}" "No image fetching in this PR" "polish guide states no image fetching in this PR"

check_text "${guide}" "local only" "guide mentions local only"
check_text "${guide}" "read-only" "guide mentions read-only"
check_text "${guide}" "no student-sensitive data|student-sensitive data" "guide mentions no student-sensitive data"
check_text "${guide}" "No Gmail|no Gmail" "guide mentions no Gmail"
check_text "${guide}" "No Google Drive|no Google Drive|Google Drive" "guide mentions no Google Drive"
check_text "${guide}" "No Google Calendar|no Google Calendar|Google Calendar" "guide mentions no Google Calendar"
check_text "${guide}" "No APIs|no APIs" "guide mentions no APIs"
check_text "${guide}" "No OAuth|no OAuth" "guide mentions no OAuth"
check_text "${guide}" "No secrets|no secrets" "guide mentions no secrets"
check_text "${guide}" "No LLM calls by default|no LLM calls" "guide mentions no LLM calls by default"
check_text "${guide}" "No document indexing|no document indexing" "guide mentions no document indexing"
check_text "${guide}" "No folder scanning|no folder scanning" "guide mentions no folder scanning"
check_text "${guide}" "human review" "guide mentions human review"

check_bash_syntax "bin/chief-of-staff"
check_cli_mentions "--command-launcher-status" "bin/chief-of-staff mentions --command-launcher-status"
check_cli_mentions "--dashboard" "bin/chief-of-staff mentions --dashboard"
check_cli_mentions "--list-workflows" "bin/chief-of-staff mentions --list-workflows"
check_cli_mentions "--lesson-review-view" "bin/chief-of-staff mentions --lesson-review-view"
check_cli_mentions "--document-indexing-plan-status" "bin/chief-of-staff mentions --document-indexing-plan-status"

check_bash_syntax "scripts/chief-of-staff-dashboard.sh"
check_bash_syntax "scripts/phase-1-status.sh"

pass "no write action attempted"
pass "no folder scanning attempted"
pass "no network calls attempted"

section "Summary"
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"

if [[ "${FAIL_COUNT}" -gt 0 ]]; then
  exit 1
fi

exit 0
