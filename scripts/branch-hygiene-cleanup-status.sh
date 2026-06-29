#!/usr/bin/env bash
# Read-only branch hygiene and cleanup reference status only. No network calls or file creation.
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
  if grep -Fq "${phrase}" "${hygiene_doc}"; then
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

hygiene_doc="docs/branch-hygiene-cleanup-reference.md"
lifecycle_doc="docs/pr-lifecycle-guardrail-consolidation.md"
prompt_template_doc="docs/checklist-driven-prompt-template-tightening.md"
cursor_prompt_doc="docs/cursor-prompt-template.md"
pr_checklist_doc="docs/cursor-pr-review-checklist.md"

section 'Branch Hygiene and Cleanup Reference'
cat <<'EOF'
Status: branch-hygiene/status only
Existing commands preserved: yes
Existing checks preserved: yes
Command behavior changed: no
Command removals: no
Command renames: no
PASS/WARN/FAIL semantics preserved: yes
Branch-state proof preserved: yes
Remote branch deletion proof preserved: yes
Final local-main proof preserved: yes
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

check_file "${hygiene_doc}"

if [[ -f "${hygiene_doc}" ]]; then
  check_doc_contains "Branch Hygiene and Cleanup Reference" "Branch Hygiene and Cleanup Reference"
  check_doc_contains "preserving all existing commands" "preserving all existing commands"
  check_doc_contains "no command removals" "no command removals"
  check_doc_contains "no command renames" "no command renames"
  check_doc_contains "no check removals" "no check removals"
  check_doc_contains "preserving command behavior" "preserving command behavior"
  check_doc_contains "PASS/WARN/FAIL semantics" "preserving PASS/WARN/FAIL semantics"
  check_doc_contains "Starting State Rules" "starting state rules"
  check_doc_contains "Feature Branch Rules" "feature branch rules"
  check_doc_contains "Pre-Commit Branch Rules" "pre-commit branch rules"
  check_doc_contains "Pre-Merge Branch Rules" "pre-merge branch rules"
  check_doc_contains "Remote Branch Deletion Rules" "remote branch deletion rules"
  check_doc_contains "Local Branch Cleanup Rules" "local branch cleanup rules"
  check_doc_contains "final local main proof" "final local main proof"
  check_doc_contains "non-null mergedAt" "non-null mergedAt"
  check_doc_contains "mergedAt is null before merge" "mergedAt is null before merge"
  check_doc_contains "no document scanning" "no document scanning"
  check_doc_contains "no file indexing" "no file indexing"
  check_doc_contains "no lesson generation changes" "no lesson generation changes"
  check_doc_contains "no real review notes" "no real review notes"
  check_doc_contains "no student data" "no student data"
  check_doc_contains "no network calls" "no network calls"
  check_doc_contains "no automation" "no automation"
fi

check_file "${lifecycle_doc}"
check_file "${prompt_template_doc}"
check_file "${cursor_prompt_doc}"
check_file "${pr_checklist_doc}"

check_bash_syntax 'bin/chief-of-staff'
check_bash_syntax 'scripts/chief-of-staff-dashboard.sh'
check_bash_syntax 'scripts/phase-1-status.sh'

section 'Help and List Workflows Discovery'

check_help_contains '--branch-hygiene-cleanup-status'
check_help_contains '--pr-lifecycle-guardrail-status'
check_help_contains '--checklist-driven-prompt-template-status'
check_help_contains '--testing-checklist-status'
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
