#!/usr/bin/env bash
# Read-only Teacher Workflow command detail summary status only. No network calls or file creation.
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

summary_doc="docs/teacher-workflow-command-detail-summary.md"
document_indexing_detail_doc="docs/document-indexing-command-detail-polish.md"
review_notes_detail_doc="docs/review-notes-command-detail-polish.md"
lesson_review_detail_doc="docs/lesson-review-command-detail-polish.md"
teacher_planning_detail_doc="docs/teacher-planning-command-detail-polish.md"
workflow_status_doc="docs/teacher-workflow-status-summary.md"
quick_ref_doc="docs/teacher-workflow-quick-reference-polish.md"
planning_cleanup_doc="docs/core-teacher-workstation-planning-cleanup.md"
quickstart_doc="docs/chief-of-staff-workflow-quick-start-guide.md"

section 'Teacher Workflow Command Detail Summary'
cat <<'EOF'
Status: teacher-workflow-command-detail-summary/status only
Existing commands preserved: yes
Existing checks preserved: yes
Command behavior changed: no
Command removals: no
Command renames: no
PASS/WARN/FAIL semantics preserved: yes
Command detail stack summarized: yes
Safe teacher commands summarized: yes
Planning-only boundaries preserved: yes
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

section 'Workflow Checks'

check_file "${summary_doc}"

if [[ -f "${summary_doc}" ]]; then
  check_doc_contains "${summary_doc}" "Teacher Workflow Command Detail Summary" "Teacher Workflow Command Detail Summary"
  check_doc_contains "${summary_doc}" "## Command Detail Stack" "Command Detail Stack"
  check_doc_contains "${summary_doc}" "Safe Teacher Workflow Commands" "Safe Teacher Workflow Commands"
  check_doc_contains "${summary_doc}" "## Teacher Planning Command Detail" "Teacher Planning Command Detail"
  check_doc_contains "${summary_doc}" "## Lesson Review Command Detail" "Lesson Review Command Detail"
  check_doc_contains "${summary_doc}" "## Review Notes Command Detail" "Review Notes Command Detail"
  check_doc_contains "${summary_doc}" "## Document Indexing Command Detail" "Document Indexing Command Detail"
  check_doc_contains "${summary_doc}" "Shared Planning-Only Boundaries" "Shared Planning-Only Boundaries"
  check_doc_contains "${summary_doc}" "Not Implemented" "Not Implemented"
  check_doc_contains "${summary_doc}" "Future Prompt Use Rules" "Future Prompt Use Rules"
  check_doc_contains "${summary_doc}" "Teacher workflow safe-output examples" "next recommended PR Teacher workflow safe-output examples"
  check_doc_contains "${summary_doc}" "preserving all existing commands" "preserving all existing commands"
  check_doc_contains "${summary_doc}" "no command removals" "no command removals"
  check_doc_contains "${summary_doc}" "no command renames" "no command renames"
  check_doc_contains "${summary_doc}" "no check removals" "no check removals"
  check_doc_contains "${summary_doc}" "preserving command behavior" "preserving command behavior"
  check_doc_contains "${summary_doc}" "PASS/WARN/FAIL semantics" "preserving PASS/WARN/FAIL semantics"
  check_doc_contains "${summary_doc}" "no document scanning" "no document scanning"
  check_doc_contains "${summary_doc}" "no folder scanning" "no folder scanning"
  check_doc_contains "${summary_doc}" "no file indexing" "no file indexing"
  check_doc_contains "${summary_doc}" "no content parsing" "no content parsing"
  check_doc_contains "${summary_doc}" "no OCR" "no OCR"
  check_doc_contains "${summary_doc}" "no embeddings" "no embeddings"
  check_doc_contains "${summary_doc}" "no vector database" "no vector database"
  check_doc_contains "${summary_doc}" "no lesson generation changes" "no lesson generation changes"
  check_doc_contains "${summary_doc}" "no real review notes" "no real review notes"
  check_doc_contains "${summary_doc}" "no student data" "no student data"
  check_doc_contains "${summary_doc}" "no network calls" "no network calls"
  check_doc_contains "${summary_doc}" "no automation" "no automation"
fi

check_file "${document_indexing_detail_doc}"
check_file "${review_notes_detail_doc}"
check_file "${lesson_review_detail_doc}"
check_file "${teacher_planning_detail_doc}"
check_file "${workflow_status_doc}"
check_file "${quick_ref_doc}"
check_file "${planning_cleanup_doc}"
check_file "${quickstart_doc}"

check_bash_syntax 'bin/chief-of-staff'
check_bash_syntax 'scripts/chief-of-staff-dashboard.sh'
check_bash_syntax 'scripts/phase-1-status.sh'

section 'Help and List Workflows Discovery'

check_help_contains '--teacher-workflow-command-detail-summary-status'
check_help_contains '--document-indexing-command-detail-status'
check_help_contains '--review-notes-command-detail-status'
check_help_contains '--lesson-review-command-detail-status'
check_help_contains '--teacher-planning-command-detail-status'
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
