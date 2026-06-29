#!/usr/bin/env bash
# Read-only command/check bundle reference polish status only. No network calls or file creation.
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
  if grep -Fq "${phrase}" "${reference_doc}"; then
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

reference_doc="docs/command-check-bundle-reference-polish.md"
checklist_doc="docs/testing-checklist-consolidation.md"
prompt_template_doc="docs/cursor-prompt-template.md"
pr_checklist_doc="docs/cursor-pr-review-checklist.md"

section 'Command/Check Bundle Reference Polish'
cat <<'EOF'
Status: reference-polish/status only
Existing commands preserved: yes
Existing checks preserved: yes
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

check_file "${reference_doc}"

if [[ -f "${reference_doc}" ]]; then
  check_doc_contains "command/check bundle reference polish" "command/check bundle reference polish"
  check_doc_contains "docs/testing-checklist-consolidation.md" "docs/testing-checklist-consolidation.md"
  check_doc_contains "preserving all existing commands" "preserving all existing commands"
  check_doc_contains "no command removals" "no command removals"
  check_doc_contains "no command renames" "no command renames"
  check_doc_contains "no check removals" "no check removals"
  check_doc_contains "preserving command behavior" "preserving command behavior"
  check_doc_contains "PASS/WARN/FAIL semantics" "preserving PASS/WARN/FAIL semantics"
  check_doc_contains "Quick Bundle Picker" "Quick Bundle Picker"
  check_doc_contains "Core Verification Bundle" "Core Verification Bundle"
  check_doc_contains "Documentation/Status PR Bundle" "Documentation/Status PR Bundle"
  check_doc_contains "Teacher Planning and Review Bundle" "Teacher Planning and Review Bundle"
  check_doc_contains "Document Indexing Safety Bundle" "Document Indexing Safety Bundle"
  check_doc_contains "Appearance & Vibe Safety Bundle" "Appearance & Vibe Safety Bundle"
  check_doc_contains "Pre-Commit Review Bundle" "Pre-Commit Review Bundle"
  check_doc_contains "Post-Merge Verification Bundle" "Post-Merge Verification Bundle"
  check_doc_contains "Cursor prompt reuse rules" "Cursor prompt reuse rules"
  check_doc_contains "no document scanning" "no document scanning"
  check_doc_contains "no file indexing" "no file indexing"
  check_doc_contains "no lesson generation changes" "no lesson generation changes"
  check_doc_contains "no real review notes" "no real review notes"
  check_doc_contains "no student data" "no student data"
  check_doc_contains "no network calls" "no network calls"
  check_doc_contains "no automation" "no automation"
fi

check_file "${checklist_doc}"
check_file "${prompt_template_doc}"
check_file "${pr_checklist_doc}"

check_bash_syntax 'bin/chief-of-staff'
check_bash_syntax 'scripts/chief-of-staff-dashboard.sh'
check_bash_syntax 'scripts/phase-1-status.sh'

section 'Help and List Workflows Discovery'

check_help_contains '--command-check-bundle-reference-status'
check_help_contains '--testing-checklist-status'
check_help_contains '--project-memory-cleanup-status'
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
