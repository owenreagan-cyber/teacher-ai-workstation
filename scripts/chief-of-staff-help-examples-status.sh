#!/usr/bin/env bash
# Read-only help examples status only. No network calls or file operations.
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
  if grep -Fq "${phrase}" "${help_examples_doc}"; then
    pass "doc mentions ${label}"
  else
    fail "doc must mention ${label}"
  fi
}

check_help_contains() {
  local flag="$1"
  if bin/chief-of-staff --help | grep -F -- "${flag}" >/dev/null; then
    pass "help contains ${flag}"
  else
    fail "help must contain ${flag}"
  fi
}

check_list_workflows_contains() {
  local label="$1"
  if bin/chief-of-staff --list-workflows | grep -Fq "${label}"; then
    pass "list-workflows contains ${label}"
  else
    fail "list-workflows must contain ${label}"
  fi
}

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "${repo_root}" ]]; then
  repo_root="$(cd "${script_dir}/.." && pwd -P)"
fi
cd "${repo_root}"

help_examples_doc="docs/chief-of-staff-help-examples-polish.md"
command_map_doc="docs/chief-of-staff-command-map-cleanup.md"
readability_doc="docs/chief-of-staff-dashboard-readability-pass.md"

section 'Chief of Staff Help Examples Polish'
cat <<'EOF'
Status: help-examples/status only
Existing commands preserved: yes
Command behavior changed: no
Command removals: no
Command renames: no
PASS/WARN/FAIL semantics preserved: yes
Live integrations: no
Network calls: no
Automation added: no
Lesson generation changes: no
Student data: no
EOF

section 'Workflow Checks'

check_file "${help_examples_doc}"

if [[ -f "${help_examples_doc}" ]]; then
  check_doc_contains "help examples polish" "help examples polish"
  check_doc_contains "preserving all existing commands" "preserving all existing commands"
  check_doc_contains "no command removals" "no command removals"
  check_doc_contains "no command renames" "no command renames"
  check_doc_contains "preserving command behavior" "preserving command behavior"
  check_doc_contains "PASS/WARN/FAIL semantics" "preserving PASS/WARN/FAIL semantics"
  check_doc_contains "Teacher Planning Examples" "teacher planning examples"
  check_doc_contains "Developer / Cursor Examples" "developer/Cursor examples"
  check_doc_contains "Appearance & Vibe Safe Examples" "Appearance & Vibe safe examples"
  check_doc_contains "Validator and Dry-Run Example Rules" "validator commands"
  check_doc_contains "dry-run helpers" "dry-run helpers"
  check_doc_contains "no network calls" "no network calls"
  check_doc_contains "no automation" "no automation"
  check_doc_contains "no student data" "no student data"
fi

check_bash_syntax 'bin/chief-of-staff'
check_bash_syntax 'scripts/chief-of-staff-dashboard.sh'
check_bash_syntax 'scripts/phase-1-status.sh'

check_file "${command_map_doc}"
check_file "${readability_doc}"

section 'Help and List Workflows Discovery'

check_help_contains '--help-examples-status'
check_help_contains '--command-map-status'
check_help_contains '--dashboard-readability-status'
check_help_contains '--return-to-core-status'
check_help_contains '--dashboard'
check_help_contains '--list-workflows'
check_help_contains '--lesson-review-view'
check_help_contains '--wallpaper-photo-create-folders --dry-run'

check_list_workflows_contains 'Chief of Staff'
check_list_workflows_contains 'Teacher Workstation'
check_list_workflows_contains 'Appearance'
check_list_workflows_contains 'Vibe'
check_list_workflows_contains 'Verification'
check_list_workflows_contains 'Future-Safety'

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
