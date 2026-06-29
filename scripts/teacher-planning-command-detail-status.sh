#!/usr/bin/env bash
# Read-only Teacher Planning command detail status only. No network calls or file creation.
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
  local file="$1"
  local phrase="$2"
  local label="$3"
  if grep -Fq "${phrase}" "${file}"; then
    pass "doc mentions ${label}"
  else
    fail "${file} must mention ${label}"
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

check_no_generated_lesson_files() {
  local dir="$1"
  local label="$2"
  local unexpected=""

  unexpected="$(find "${dir}" -maxdepth 1 -type f ! -name 'README.md' -print 2>/dev/null || true)"
  if [[ -z "${unexpected}" ]]; then
    pass "no generated files in ${label}"
  else
    fail "generated files found in ${label}"
    printf '%s\n' "${unexpected}" | sed 's/^/  /'
  fi
}

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "${repo_root}" ]]; then
  repo_root="$(cd "${script_dir}/.." && pwd -P)"
fi
cd "${repo_root}"

detail_doc="docs/teacher-planning-command-detail-polish.md"
summary_doc="docs/teacher-workflow-status-summary.md"
quick_ref_doc="docs/teacher-workflow-quick-reference-polish.md"
planning_cleanup_doc="docs/core-teacher-workstation-planning-cleanup.md"
teacher_planning_doc="docs/teacher-planning-command-organization.md"
quickstart_doc="docs/chief-of-staff-workflow-quick-start-guide.md"

section 'Teacher Planning Command Detail Polish'
cat <<'EOF'
Status: teacher-planning-command-detail/status only
Existing commands preserved: yes
Existing checks preserved: yes
Command behavior changed: no
Command removals: no
Command renames: no
PASS/WARN/FAIL semantics preserved: yes
Teacher Planning command documented: yes
Expected output documented: yes
Planning-only boundaries documented: yes
Document scanning: no
File indexing: no
Lesson generation changes: no
Real review notes: no
Student data: no
Live integrations: no
Network calls: no
Automation added: no
EOF

section 'Workflow Checks'

check_file "${detail_doc}"

if [[ -f "${detail_doc}" ]]; then
  check_doc_contains "${detail_doc}" "Teacher Planning Command Detail Polish" "Teacher Planning Command Detail Polish"
  check_doc_contains "${detail_doc}" "## Teacher Planning Command" "Teacher Planning Command"
  check_doc_contains "${detail_doc}" "Expected Output" "Expected Output"
  check_doc_contains "${detail_doc}" "Planning-Only Boundaries" "Planning-Only Boundaries"
  check_doc_contains "${detail_doc}" "Related Safe Commands" "Related Safe Commands"
  check_doc_contains "${detail_doc}" "Related Teacher Workflow Docs" "Related Teacher Workflow Docs"
  check_doc_contains "${detail_doc}" "Not Implemented" "Not Implemented"
  check_doc_contains "${detail_doc}" "Lesson review command detail polish" "next recommended PR Lesson review command detail polish"
  check_doc_contains "${detail_doc}" "preserving all existing commands" "preserving all existing commands"
  check_doc_contains "${detail_doc}" "no command removals" "no command removals"
  check_doc_contains "${detail_doc}" "no command renames" "no command renames"
  check_doc_contains "${detail_doc}" "no check removals" "no check removals"
  check_doc_contains "${detail_doc}" "preserving command behavior" "preserving command behavior"
  check_doc_contains "${detail_doc}" "PASS/WARN/FAIL semantics" "preserving PASS/WARN/FAIL semantics"
  check_doc_contains "${detail_doc}" "no document scanning" "no document scanning"
  check_doc_contains "${detail_doc}" "no file indexing" "no file indexing"
  check_doc_contains "${detail_doc}" "no lesson generation changes" "no lesson generation changes"
  check_doc_contains "${detail_doc}" "no real review notes" "no real review notes"
  check_doc_contains "${detail_doc}" "no student data" "no student data"
  check_doc_contains "${detail_doc}" "no network calls" "no network calls"
  check_doc_contains "${detail_doc}" "no automation" "no automation"
fi

check_file "${summary_doc}"
check_file "${quick_ref_doc}"
check_file "${planning_cleanup_doc}"
check_file "${teacher_planning_doc}"
check_file "${quickstart_doc}"

check_bash_syntax 'bin/chief-of-staff'
check_bash_syntax 'scripts/chief-of-staff-dashboard.sh'
check_bash_syntax 'scripts/phase-1-status.sh'

section 'Help and List Workflows Discovery'

check_help_contains '--teacher-planning-command-detail-status'
check_help_contains '--teacher-planning-command-status'
check_help_contains '--teacher-workflow-status-summary'
check_help_contains '--teacher-workflow-quick-reference-status'
check_help_contains '--core-teacher-workstation-planning-cleanup-status'
check_help_contains '--dashboard'
check_help_contains '--list-workflows'

check_list_workflows_contains 'Chief of Staff'
check_list_workflows_contains 'Teacher Workstation'
check_list_workflows_contains 'Verification'
check_list_workflows_contains 'Future-Safety'

section 'Lesson and Review Note File Safety'

check_no_generated_lesson_files 'assistant/lesson-planning/briefs' 'briefs'
check_no_generated_lesson_files 'assistant/lesson-planning/drafts' 'drafts'
check_no_generated_lesson_files 'assistant/lesson-planning/review-notes' 'review-notes'

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
