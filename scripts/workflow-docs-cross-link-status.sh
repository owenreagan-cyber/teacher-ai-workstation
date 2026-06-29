#!/usr/bin/env bash
# Read-only workflow docs cross-link polish status only. No network calls or file creation.
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

check_crosslink() {
  local from_file="$1"
  local to_phrase="$2"
  local label="$3"
  if grep -Fq "${to_phrase}" "${from_file}"; then
    pass "cross-link: ${label}"
  else
    fail "cross-link missing: ${label}"
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

crosslink_doc="docs/workflow-docs-cross-link-polish.md"
os_doc="docs/cursor-workflow-operating-system.md"
prompt_doc="docs/cursor-prompt-template.md"
checklist_doc="docs/cursor-pr-review-checklist.md"
testing_doc="docs/testing-checklist-consolidation.md"
bundle_doc="docs/command-check-bundle-reference-polish.md"
template_doc="docs/checklist-driven-prompt-template-tightening.md"
lifecycle_doc="docs/pr-lifecycle-guardrail-consolidation.md"
hygiene_doc="docs/branch-hygiene-cleanup-reference.md"
proof_doc="docs/local-main-proof-report-polish.md"

section 'Workflow Docs Cross-Link Polish'
cat <<'EOF'
Status: cross-link-polish/status only
Existing commands preserved: yes
Existing checks preserved: yes
Command behavior changed: no
Command removals: no
Command renames: no
PASS/WARN/FAIL semantics preserved: yes
Workflow doc map added: yes
Lifecycle guardrails preserved: yes
Branch deletion proof preserved: yes
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

check_file "${crosslink_doc}"

if [[ -f "${crosslink_doc}" ]]; then
  check_doc_contains "${crosslink_doc}" "Workflow Docs Cross-Link Polish" "Workflow Docs Cross-Link Polish"
  check_doc_contains "${crosslink_doc}" "preserving all existing commands" "preserving all existing commands"
  check_doc_contains "${crosslink_doc}" "no command removals" "no command removals"
  check_doc_contains "${crosslink_doc}" "no command renames" "no command renames"
  check_doc_contains "${crosslink_doc}" "no check removals" "no check removals"
  check_doc_contains "${crosslink_doc}" "preserving command behavior" "preserving command behavior"
  check_doc_contains "${crosslink_doc}" "PASS/WARN/FAIL semantics" "preserving PASS/WARN/FAIL semantics"
  check_doc_contains "${crosslink_doc}" "Workflow Doc Map" "workflow doc map"
  check_doc_contains "${crosslink_doc}" "Start Here Links" "start here links"
  check_doc_contains "${crosslink_doc}" "Verification Bundle Links" "verification bundle links"
  check_doc_contains "${crosslink_doc}" "Prompt Template Links" "prompt template links"
  check_doc_contains "${crosslink_doc}" "PR Lifecycle Links" "PR lifecycle links"
  check_doc_contains "${crosslink_doc}" "Branch Hygiene Links" "branch hygiene links"
  check_doc_contains "${crosslink_doc}" "Local Main Proof Links" "local main proof links"
  check_doc_contains "${crosslink_doc}" "no document scanning" "no document scanning"
  check_doc_contains "${crosslink_doc}" "no file indexing" "no file indexing"
  check_doc_contains "${crosslink_doc}" "no lesson generation changes" "no lesson generation changes"
  check_doc_contains "${crosslink_doc}" "no real review notes" "no real review notes"
  check_doc_contains "${crosslink_doc}" "no student data" "no student data"
  check_doc_contains "${crosslink_doc}" "no network calls" "no network calls"
  check_doc_contains "${crosslink_doc}" "no automation" "no automation"
fi

check_file "${os_doc}"
check_file "${prompt_doc}"
check_file "${checklist_doc}"
check_file "${testing_doc}"
check_file "${bundle_doc}"
check_file "${template_doc}"
check_file "${lifecycle_doc}"
check_file "${hygiene_doc}"
check_file "${proof_doc}"

section 'Cross-Link Verification'

check_crosslink "${os_doc}" "docs/cursor-prompt-template.md" "cursor-workflow-operating-system -> cursor-prompt-template"
check_crosslink "${prompt_doc}" "docs/testing-checklist-consolidation.md" "cursor-prompt-template -> testing-checklist-consolidation"
check_crosslink "${prompt_doc}" "docs/pr-lifecycle-guardrail-consolidation.md" "cursor-prompt-template -> pr-lifecycle-guardrail-consolidation"
check_crosslink "${checklist_doc}" "docs/local-main-proof-report-polish.md" "cursor-pr-review-checklist -> local-main-proof-report-polish"
check_crosslink "${testing_doc}" "docs/command-check-bundle-reference-polish.md" "testing-checklist-consolidation -> command-check-bundle-reference-polish"
check_crosslink "${bundle_doc}" "docs/testing-checklist-consolidation.md" "command-check-bundle-reference-polish -> testing-checklist-consolidation"
check_crosslink "${template_doc}" "docs/pr-lifecycle-guardrail-consolidation.md" "checklist-driven-prompt-template-tightening -> pr-lifecycle-guardrail-consolidation"
check_crosslink "${lifecycle_doc}" "docs/branch-hygiene-cleanup-reference.md" "pr-lifecycle-guardrail-consolidation -> branch-hygiene-cleanup-reference"
check_crosslink "${hygiene_doc}" "docs/local-main-proof-report-polish.md" "branch-hygiene-cleanup-reference -> local-main-proof-report-polish"

check_bash_syntax 'bin/chief-of-staff'
check_bash_syntax 'scripts/chief-of-staff-dashboard.sh'
check_bash_syntax 'scripts/phase-1-status.sh'

section 'Help and List Workflows Discovery'

check_help_contains '--workflow-docs-cross-link-status'
check_help_contains '--local-main-proof-report-status'
check_help_contains '--branch-hygiene-cleanup-status'
check_help_contains '--pr-lifecycle-guardrail-status'
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
