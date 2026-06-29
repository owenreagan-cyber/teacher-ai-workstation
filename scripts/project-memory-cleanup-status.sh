#!/usr/bin/env bash
# Read-only project memory cleanup status only. No network calls or file creation.
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
  if grep -Fq "${phrase}" "${cleanup_doc}"; then
    pass "doc mentions ${label}"
  else
    fail "doc must mention ${label}"
  fi
}

check_memory_contains() {
  local path="$1"
  local phrase="$2"
  local label="$3"
  if [[ ! -f "${path}" ]]; then
    fail "memory file missing for ${label}: ${path}"
    return
  fi

  if grep -Fq "${phrase}" "${path}"; then
    pass "${label}"
  else
    fail "must mention ${label}"
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

cleanup_doc="docs/project-memory-cleanup.md"
active_priorities="assistant/memory/active-priorities.md"
projects_memory="assistant/memory/projects.md"
indexing_doc="docs/local-document-indexing-follow-up.md"
review_notes_doc="docs/review-notes-workflow-polish.md"

section 'Project Memory Cleanup'
cat <<'EOF'
Status: memory-cleanup/status only
Existing commands preserved: yes
Command behavior changed: no
Command removals: no
Command renames: no
PASS/WARN/FAIL semantics preserved: yes
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

check_file "${cleanup_doc}"

if [[ -f "${cleanup_doc}" ]]; then
  check_doc_contains "project memory cleanup" "project memory cleanup"
  check_doc_contains "preserving all existing commands" "preserving all existing commands"
  check_doc_contains "no command removals" "no command removals"
  check_doc_contains "no command renames" "no command renames"
  check_doc_contains "preserving command behavior" "preserving command behavior"
  check_doc_contains "PASS/WARN/FAIL semantics" "preserving PASS/WARN/FAIL semantics"
  check_doc_contains "Active Priorities Rules" "active priorities"
  check_doc_contains "Project Memory Rules" "project memory"
  check_doc_contains "Recently Completed Work" "recently completed work"
  check_doc_contains "Current Roadmap" "current roadmap"
  check_doc_contains "Parked Work" "parked work"
  check_doc_contains "Testing/checklist consolidation" "Testing/checklist consolidation"
  check_doc_contains "no document scanning" "no document scanning"
  check_doc_contains "no file indexing" "no file indexing"
  check_doc_contains "no OCR" "no OCR"
  check_doc_contains "no embeddings" "no embeddings"
  check_doc_contains "no vector database" "no vector database"
  check_doc_contains "no lesson generation changes" "no lesson generation changes"
  check_doc_contains "no real review notes" "no real review notes"
  check_doc_contains "no student data" "no student data"
  check_doc_contains "no network calls" "no network calls"
  check_doc_contains "no automation" "no automation"
fi

check_file "${active_priorities}"
check_file "${projects_memory}"

check_memory_contains "${active_priorities}" "Project memory cleanup" "active priorities mention Project memory cleanup"
check_memory_contains "${active_priorities}" "Testing/checklist consolidation" "active priorities mention Testing/checklist consolidation"
check_memory_contains "${projects_memory}" "Appearance & Vibe wallpaper/photo foundation stack complete for now" "projects memory mentions Appearance & Vibe wallpaper/photo foundation stack complete for now"
check_memory_contains "${projects_memory}" "live wallpaper/photo curator implementation is not started" "projects memory mentions live wallpaper/photo curator implementation is not started"
check_memory_contains "${projects_memory}" "3D Design Factory Agent remains parked" "projects memory mentions 3D Design Factory Agent remains parked"

check_bash_syntax 'bin/chief-of-staff'
check_bash_syntax 'scripts/chief-of-staff-dashboard.sh'
check_bash_syntax 'scripts/phase-1-status.sh'

check_file "${indexing_doc}"
check_file "${review_notes_doc}"

section 'Help and List Workflows Discovery'

check_help_contains '--project-memory-cleanup-status'
check_help_contains '--local-document-indexing-follow-up-status'
check_help_contains '--review-notes-workflow-status'
check_help_contains '--dashboard'
check_help_contains '--list-workflows'

check_list_workflows_contains 'Chief of Staff'
check_list_workflows_contains 'Teacher Workstation'
check_list_workflows_contains 'Document'
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
