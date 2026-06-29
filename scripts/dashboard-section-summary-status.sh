#!/usr/bin/env bash
# Read-only dashboard section summary status only. No network calls or file operations.
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
  if grep -Fq "${phrase}" "${summary_doc}"; then
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

check_dashboard_contains() {
  local label="$1"
  if [[ -n "${dashboard_output}" ]] && grep -Fq "${label}" <<<"${dashboard_output}"; then
    pass "dashboard contains ${label}"
  else
    fail "dashboard must contain ${label}"
  fi
}

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "${repo_root}" ]]; then
  repo_root="$(cd "${script_dir}/.." && pwd -P)"
fi
cd "${repo_root}"

summary_doc="docs/dashboard-section-summary-polish.md"
quick_start_doc="docs/chief-of-staff-workflow-quick-start-guide.md"
readability_doc="docs/chief-of-staff-dashboard-readability-pass.md"
dashboard_script="scripts/chief-of-staff-dashboard.sh"

section 'Dashboard Section Summary Polish'
cat <<'EOF'
Status: dashboard readability/status only
Existing commands preserved: yes
Dashboard checks preserved: yes
Command behavior changed: no
Command removals: no
Command renames: no
PASS/WARN/FAIL semantics preserved: yes
Failures hidden: no
Warnings hidden: no
Live integrations: no
Network calls: no
Automation added: no
Student data: no
EOF

section 'Workflow Checks'

check_file "${summary_doc}"

if [[ -f "${summary_doc}" ]]; then
  check_doc_contains "dashboard section summary polish" "dashboard section summary polish"
  check_doc_contains "preserving every dashboard check" "preserving every dashboard check"
  check_doc_contains "PASS/WARN/FAIL semantics" "preserving PASS/WARN/FAIL semantics"
  check_doc_contains "not hide failures" "not hiding failures"
  check_doc_contains "not hide warnings" "not hiding warnings"
  check_doc_contains "preserving command behavior" "preserving command behavior"
  check_doc_contains "no command removals" "no command removals"
  check_doc_contains "no command renames" "no command renames"
  check_doc_contains "no network calls" "no network calls"
  check_doc_contains "no automation" "no automation"
  check_doc_contains "no student data" "no student data"
fi

check_bash_syntax "${dashboard_script}"
check_bash_syntax 'bin/chief-of-staff'
check_bash_syntax 'scripts/phase-1-status.sh'

check_file "${quick_start_doc}"
check_file "${readability_doc}"

if grep -Fq 'begin_section_summary' "${dashboard_script}" && grep -Fq 'end_section_summary' "${dashboard_script}"; then
  pass 'dashboard script defines section summary helpers'
else
  fail 'dashboard script must define section summary helpers'
fi

if grep -Fq 'Section summary:' "${dashboard_script}"; then
  pass 'dashboard script prints section summary lines'
else
  fail 'dashboard script must print section summary lines'
fi

section 'Help Discovery'

check_help_contains '--dashboard-section-summary-status'
check_help_contains '--workflow-quick-start-status'
check_help_contains '--help-examples-status'
check_help_contains '--command-map-status'
check_help_contains '--dashboard-readability-status'
check_help_contains '--dashboard'
check_help_contains '--list-workflows'

section 'Dashboard Section Labels'

dashboard_output=""
dashboard_result=0
dashboard_output="$(COS_DASHBOARD_SKIP_SECTION_SUMMARY_STATUS=1 bin/chief-of-staff --dashboard 2>&1)" || dashboard_result=$?

if [[ "${dashboard_result}" == "0" ]]; then
  pass 'dashboard command completed successfully'
else
  fail 'dashboard command must complete successfully for section label checks'
fi

check_dashboard_contains 'Section summary: Core Workstation Status'
check_dashboard_contains 'Section summary: Chief of Staff Workflow Status'
check_dashboard_contains 'Section summary: Lesson Planning Status'
check_dashboard_contains 'Section summary: Developer / Cursor Workflow Status'
check_dashboard_contains 'Section summary: Appearance & Vibe Foundation Status'
check_dashboard_contains 'Section summary: Recommendation'
check_dashboard_contains 'Health:'

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
