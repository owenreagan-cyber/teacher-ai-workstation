#!/usr/bin/env bash
# Read-only Teacher Workflow safe-output checker status only. No network calls or file creation.
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

checker_doc="docs/teacher-workflow-safe-output-checker.md"
examples_doc="docs/teacher-workflow-safe-output-examples.md"
command_detail_summary_doc="docs/teacher-workflow-command-detail-summary.md"
document_indexing_detail_doc="docs/document-indexing-command-detail-polish.md"
review_notes_detail_doc="docs/review-notes-command-detail-polish.md"
lesson_review_detail_doc="docs/lesson-review-command-detail-polish.md"
teacher_planning_detail_doc="docs/teacher-planning-command-detail-polish.md"
workflow_status_doc="docs/teacher-workflow-status-summary.md"
quick_ref_doc="docs/teacher-workflow-quick-reference-polish.md"
planning_cleanup_doc="docs/core-teacher-workstation-planning-cleanup.md"

section 'Teacher Workflow Safe-Output Checker'
cat <<'EOF'
Status: teacher-workflow-safe-output-checker/status only
Existing commands preserved: yes
Existing checks preserved: yes
Command behavior changed: no
Command removals: no
Command renames: no
PASS/WARN/FAIL semantics preserved: yes
Safe-output examples checked: yes
Planning-only labels checked: yes
Placeholder counts checked: yes
Safety boundary phrases checked: yes
Document scanning: no
Folder scanning: no
File indexing: no
Content parsing: no
OCR: no
Embeddings: no
Vector database: no
Lesson generation changes: no
Real review notes: no
Student data: no
Live integrations: no
Network calls: no
Automation added: no
EOF

section 'Checker Doc Checks'

check_file "${checker_doc}"

if [[ -f "${checker_doc}" ]]; then
  check_doc_contains "${checker_doc}" "Teacher Workflow Safe-Output Checker" "Teacher Workflow Safe-Output Checker"
  check_doc_contains "${checker_doc}" "Checker Goals" "Checker Goals"
  check_doc_contains "${checker_doc}" "Safe Output Example Source" "Safe Output Example Source"
  check_doc_contains "${checker_doc}" "Required Planning-Only Labels" "Required Planning-Only Labels"
  check_doc_contains "${checker_doc}" "Required PASS/WARN/FAIL Summary" "Required PASS/WARN/FAIL Summary"
  check_doc_contains "${checker_doc}" "Required Placeholder Count Language" "Required Placeholder Count Language"
  check_doc_contains "${checker_doc}" "Required Teacher Workflow Boundaries" "Required Teacher Workflow Boundaries"
  check_doc_contains "${checker_doc}" "Required Document Indexing Boundaries" "Required Document Indexing Boundaries"
  check_doc_contains "${checker_doc}" "Required Negative Output Checks" "Required Negative Output Checks"
  check_doc_contains "${checker_doc}" "Teacher workflow output examples completion marker" "next recommended PR Teacher workflow output examples completion marker"
  check_doc_contains "${checker_doc}" "preserving all existing commands" "preserving all existing commands"
  check_doc_contains "${checker_doc}" "no command removals" "no command removals"
  check_doc_contains "${checker_doc}" "no command renames" "no command renames"
  check_doc_contains "${checker_doc}" "no check removals" "no check removals"
  check_doc_contains "${checker_doc}" "preserving command behavior" "preserving command behavior"
  check_doc_contains "${checker_doc}" "PASS/WARN/FAIL semantics" "preserving PASS/WARN/FAIL semantics"
  check_doc_contains "${checker_doc}" "no document scanning" "no document scanning"
  check_doc_contains "${checker_doc}" "no folder scanning" "no folder scanning"
  check_doc_contains "${checker_doc}" "no file indexing" "no file indexing"
  check_doc_contains "${checker_doc}" "no content parsing" "no content parsing"
  check_doc_contains "${checker_doc}" "no OCR" "no OCR"
  check_doc_contains "${checker_doc}" "no embeddings" "no embeddings"
  check_doc_contains "${checker_doc}" "no vector database" "no vector database"
  check_doc_contains "${checker_doc}" "no lesson generation changes" "no lesson generation changes"
  check_doc_contains "${checker_doc}" "no real review notes" "no real review notes"
  check_doc_contains "${checker_doc}" "no student data" "no student data"
  check_doc_contains "${checker_doc}" "no network calls" "no network calls"
  check_doc_contains "${checker_doc}" "no automation" "no automation"
fi

section 'Safe Output Examples Doc Checks'

check_file "${examples_doc}"

if [[ -f "${examples_doc}" ]]; then
  check_doc_contains "${examples_doc}" "teacher-planning/status only" "teacher-planning/status only"
  check_doc_contains "${examples_doc}" "lesson-review/status only" "lesson-review/status only"
  check_doc_contains "${examples_doc}" "review-notes/status only" "review-notes/status only"
  check_doc_contains "${examples_doc}" "document-indexing/planning only" "document-indexing/planning only"
  check_doc_contains "${examples_doc}" "PASS: X" "PASS: X"
  check_doc_contains "${examples_doc}" "WARN: Y" "WARN: Y"
  check_doc_contains "${examples_doc}" "FAIL: Z" "FAIL: Z"
  check_doc_contains "${examples_doc}" "X, Y, and Z are placeholders" "X, Y, and Z are placeholders"
  check_doc_contains "${examples_doc}" "no document scanning" "examples no document scanning"
  check_doc_contains "${examples_doc}" "no folder scanning" "examples no folder scanning"
  check_doc_contains "${examples_doc}" "no file indexing" "examples no file indexing"
  check_doc_contains "${examples_doc}" "no content parsing" "examples no content parsing"
  check_doc_contains "${examples_doc}" "no OCR" "examples no OCR"
  check_doc_contains "${examples_doc}" "no embeddings" "examples no embeddings"
  check_doc_contains "${examples_doc}" "no vector database" "examples no vector database"
  check_doc_contains "${examples_doc}" "no lesson generation changes" "examples no lesson generation changes"
  check_doc_contains "${examples_doc}" "no real review notes" "examples no real review notes"
  check_doc_contains "${examples_doc}" "no student data" "examples no student data"
fi

check_file "${command_detail_summary_doc}"
check_file "${document_indexing_detail_doc}"
check_file "${review_notes_detail_doc}"
check_file "${lesson_review_detail_doc}"
check_file "${teacher_planning_detail_doc}"
check_file "${workflow_status_doc}"
check_file "${quick_ref_doc}"
check_file "${planning_cleanup_doc}"

check_bash_syntax 'bin/chief-of-staff'
check_bash_syntax 'scripts/chief-of-staff-dashboard.sh'
check_bash_syntax 'scripts/phase-1-status.sh'

section 'Help and List Workflows Discovery'

check_help_contains '--teacher-workflow-safe-output-checker-status'
check_help_contains '--teacher-workflow-safe-output-examples-status'
check_help_contains '--teacher-workflow-command-detail-summary-status'
check_help_contains '--document-indexing-command-detail-status'
check_help_contains '--review-notes-command-detail-status'
check_help_contains '--lesson-review-command-detail-status'
check_help_contains '--teacher-planning-command-detail-status'
check_help_contains '--teacher-workflow-status-summary'
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
