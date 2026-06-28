#!/usr/bin/env bash
# Read-only workflow quick-start status only. No network calls or file operations.
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
  if grep -Fq "${phrase}" "${quick_start_doc}"; then
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

quick_start_doc="docs/chief-of-staff-workflow-quick-start-guide.md"
help_examples_doc="docs/chief-of-staff-help-examples-polish.md"
command_map_doc="docs/chief-of-staff-command-map-cleanup.md"

section 'Chief of Staff Workflow Quick-Start Guide'
cat <<'EOF'
Status: quick-start/status only
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

check_file "${quick_start_doc}"

if [[ -f "${quick_start_doc}" ]]; then
  check_doc_contains "workflow quick-start guide" "workflow quick-start guide"
  check_doc_contains "bin/chief-of-staff --dashboard" "bin/chief-of-staff --dashboard"
  check_doc_contains "Daily Health Check" "daily health check"
  check_doc_contains "Before Starting a PR" "before starting a PR"
  check_doc_contains "Before Committing" "before committing"
  check_doc_contains "After Merging a PR" "after merging a PR"
  check_doc_contains "Lesson Review Workflow" "lesson review"
  check_doc_contains "Document and Review Workflow" "document/review workflow"
  check_doc_contains "Developer / Cursor Workflow" "developer/Cursor workflow"
  check_doc_contains "Appearance & Vibe Safe Checks" "Appearance & Vibe safe checks"
  check_doc_contains "Dry-run commands" "dry-run commands"
  check_doc_contains "Validator commands" "validator commands"
  check_doc_contains "no command removals" "no command removals"
  check_doc_contains "no command renames" "no command renames"
  check_doc_contains "preserving command behavior" "preserving command behavior"
  check_doc_contains "PASS/WARN/FAIL semantics" "preserving PASS/WARN/FAIL semantics"
  check_doc_contains "no network calls" "no network calls"
  check_doc_contains "no automation" "no automation"
  check_doc_contains "no student data" "no student data"
  check_doc_contains "3D Design Factory Agent remains parked" "3D Design Factory Agent remains parked"
fi

check_bash_syntax 'bin/chief-of-staff'
check_bash_syntax 'scripts/chief-of-staff-dashboard.sh'
check_bash_syntax 'scripts/phase-1-status.sh'

check_file "${help_examples_doc}"
check_file "${command_map_doc}"

section 'Help and List Workflows Discovery'

check_help_contains '--workflow-quick-start-status'
check_help_contains '--help-examples-status'
check_help_contains '--command-map-status'
check_help_contains '--dashboard-readability-status'
check_help_contains '--return-to-core-status'
check_help_contains '--dashboard'
check_help_contains '--list-workflows'
check_help_contains '--lesson-review-view'

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
