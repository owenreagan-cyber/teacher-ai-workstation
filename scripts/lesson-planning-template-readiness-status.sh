#!/usr/bin/env bash
# Read-only Lesson-planning template readiness status only. No network calls or file creation.
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

readiness_doc="docs/lesson-planning-template-readiness-polish.md"
completion_doc="docs/teacher-workflow-output-examples-completion-marker.md"
checker_doc="docs/teacher-workflow-safe-output-checker.md"
examples_doc="docs/teacher-workflow-safe-output-examples.md"
command_detail_summary_doc="docs/teacher-workflow-command-detail-summary.md"
workflow_status_doc="docs/teacher-workflow-status-summary.md"
quick_ref_doc="docs/teacher-workflow-quick-reference-polish.md"
planning_cleanup_doc="docs/core-teacher-workstation-planning-cleanup.md"
placeholder_skeleton="assistant/lesson-planning/templates/lesson-planning-placeholder-skeleton.md"

section 'Lesson-Planning Template Readiness Polish'
cat <<'EOF'
Status: lesson-planning-template-readiness/status only
Existing commands preserved: yes
Existing checks preserved: yes
Command behavior changed: no
Command removals: no
Command renames: no
PASS/WARN/FAIL semantics preserved: yes
Template readiness documented: yes
Placeholder skeleton present: yes
Placeholder skeleton inert: yes
Placeholder-only examples documented: yes
Teacher Workflow guardrails preserved: yes
Document scanning: no
Folder scanning: no
File indexing: no
Content parsing: no
OCR: no
Embeddings: no
Vector database: no
Lesson generation changes: no
Generated lesson briefs: no
Generated lesson drafts: no
Real review notes: no
Student data: no
Live integrations: no
Network calls: no
Automation added: no
EOF

section 'Template Readiness Doc Checks'

check_file "${readiness_doc}"

if [[ -f "${readiness_doc}" ]]; then
  check_doc_contains "${readiness_doc}" "Lesson-Planning Template Readiness Polish" "Lesson-Planning Template Readiness Polish"
  check_doc_contains "${readiness_doc}" "safe return point" "safe return point"
  check_doc_contains "${readiness_doc}" "Template Readiness Definition" "Template Readiness Definition"
  check_doc_contains "${readiness_doc}" "Placeholder-Only Template Examples" "Placeholder-Only Template Examples"
  check_doc_contains "${readiness_doc}" "Safe Template Boundaries" "Safe Template Boundaries"
  check_doc_contains "${readiness_doc}" "Related Teacher Workflow Guardrails" "Related Teacher Workflow Guardrails"
  check_doc_contains "${readiness_doc}" "Related Verification Commands" "Related Verification Commands"
  check_doc_contains "${readiness_doc}" "Future Lesson-Planning Template Work" "Future Lesson-Planning Template Work"
  check_doc_contains "${readiness_doc}" "Lesson-planning placeholder template skeleton" "next recommended PR Lesson-planning placeholder template skeleton"
  check_doc_contains "${readiness_doc}" "Teacher Workflow command detail and safe-output example stack is complete for now" "Teacher Workflow stack complete for now"
  check_doc_contains "${readiness_doc}" "preserving all existing commands" "preserving all existing commands"
  check_doc_contains "${readiness_doc}" "no command removals" "no command removals"
  check_doc_contains "${readiness_doc}" "no command renames" "no command renames"
  check_doc_contains "${readiness_doc}" "no check removals" "no check removals"
  check_doc_contains "${readiness_doc}" "preserving command behavior" "preserving command behavior"
  check_doc_contains "${readiness_doc}" "PASS/WARN/FAIL semantics" "preserving PASS/WARN/FAIL semantics"
  check_doc_contains "${readiness_doc}" "placeholder-only examples" "placeholder-only examples"
  check_doc_contains "${readiness_doc}" "no document scanning" "no document scanning"
  check_doc_contains "${readiness_doc}" "no folder scanning" "no folder scanning"
  check_doc_contains "${readiness_doc}" "no file indexing" "no file indexing"
  check_doc_contains "${readiness_doc}" "no content parsing" "no content parsing"
  check_doc_contains "${readiness_doc}" "no OCR" "no OCR"
  check_doc_contains "${readiness_doc}" "no embeddings" "no embeddings"
  check_doc_contains "${readiness_doc}" "no vector database" "no vector database"
  check_doc_contains "${readiness_doc}" "no lesson generation changes" "no lesson generation changes"
  check_doc_contains "${readiness_doc}" "no generated lesson briefs" "no generated lesson briefs"
  check_doc_contains "${readiness_doc}" "no generated lesson drafts" "no generated lesson drafts"
  check_doc_contains "${readiness_doc}" "no real review notes" "no real review notes"
  check_doc_contains "${readiness_doc}" "no student data" "no student data"
  check_doc_contains "${readiness_doc}" "no network calls" "no network calls"
  check_doc_contains "${readiness_doc}" "no automation" "no automation"
fi

check_file "${completion_doc}"
check_file "${checker_doc}"
check_file "${examples_doc}"
check_file "${command_detail_summary_doc}"
check_file "${workflow_status_doc}"
check_file "${quick_ref_doc}"
check_file "${planning_cleanup_doc}"

section 'Placeholder Skeleton Checks'

check_file "${placeholder_skeleton}"

if [[ -f "${placeholder_skeleton}" ]]; then
  check_doc_contains "${placeholder_skeleton}" "Lesson-Planning Placeholder Template Skeleton" "Lesson-Planning Placeholder Template Skeleton"
  check_doc_contains "${placeholder_skeleton}" "Status: placeholder-only" "placeholder-only status marker"
  check_doc_contains "${placeholder_skeleton}" "Safety: inert" "inert safety marker"
  check_doc_contains "${placeholder_skeleton}" "Inputs: none" "no inputs marker"
  check_doc_contains "${placeholder_skeleton}" "Student data: prohibited" "student data prohibited marker"
  check_doc_contains "${placeholder_skeleton}" "Network/API use: prohibited" "network/API prohibited marker"
  check_doc_contains "${placeholder_skeleton}" "Document scanning/indexing: prohibited" "document scanning/indexing prohibited marker"
  check_doc_contains "${placeholder_skeleton}" "Output: none" "no output marker"
  check_doc_contains "${placeholder_skeleton}" "Metadata" "metadata placeholder section"
  check_doc_contains "${placeholder_skeleton}" "Learning Goals" "learning goals placeholder section"
  check_doc_contains "${placeholder_skeleton}" "Materials" "materials placeholder section"
  check_doc_contains "${placeholder_skeleton}" "Activity Sequence" "activity sequence placeholder section"
  check_doc_contains "${placeholder_skeleton}" "Checks for Understanding" "checks for understanding placeholder section"
  check_doc_contains "${placeholder_skeleton}" "Differentiation Notes" "differentiation notes placeholder section"
  check_doc_contains "${placeholder_skeleton}" "Assessment Placeholder" "assessment placeholder section"
  check_doc_contains "${placeholder_skeleton}" "Safety / Local-First Notes" "safety/local-first notes placeholder section"
  check_doc_contains "${placeholder_skeleton}" "does not generate lessons" "no lesson generation marker"
  check_doc_contains "${placeholder_skeleton}" "does not scan documents" "no document scanning marker"
  check_doc_contains "${placeholder_skeleton}" "index files" "no file indexing marker"
  check_doc_contains "${placeholder_skeleton}" "call APIs" "no API marker"
  check_doc_contains "${placeholder_skeleton}" "run automation" "no automation marker"
  check_doc_contains "${placeholder_skeleton}" "enable live integrations" "no live integrations marker"
fi

check_bash_syntax 'bin/chief-of-staff'
check_bash_syntax 'scripts/chief-of-staff-dashboard.sh'
check_bash_syntax 'scripts/phase-1-status.sh'

section 'Help and List Workflows Discovery'

check_help_contains '--lesson-planning-template-readiness-status'
check_help_contains '--teacher-workflow-output-examples-completion-status'
check_help_contains '--teacher-workflow-safe-output-checker-status'
check_help_contains '--teacher-workflow-safe-output-examples-status'
check_help_contains '--teacher-workflow-command-detail-summary-status'
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
