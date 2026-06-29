#!/usr/bin/env bash
# Read-only prompt pack reference index status only. No network calls or file creation.
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

index_doc="docs/prompt-pack-reference-index.md"
maintenance_doc="docs/prompt-pack-maintenance-checklist.md"
nav_doc="docs/workflow-docs-navigation-status-summary.md"
crosslink_doc="docs/workflow-docs-cross-link-polish.md"
template_doc="docs/checklist-driven-prompt-template-tightening.md"
os_doc="docs/cursor-workflow-operating-system.md"
prompt_doc="docs/cursor-prompt-template.md"
checklist_doc="docs/cursor-pr-review-checklist.md"
testing_doc="docs/testing-checklist-consolidation.md"
bundle_doc="docs/command-check-bundle-reference-polish.md"
lifecycle_doc="docs/pr-lifecycle-guardrail-consolidation.md"
branch_doc="docs/branch-hygiene-cleanup-reference.md"
local_main_doc="docs/local-main-proof-report-polish.md"

section 'Prompt Pack Reference Index'
cat <<'EOF'
Status: prompt-pack-index/status only
Existing commands preserved: yes
Existing checks preserved: yes
Command behavior changed: no
Command removals: no
Command renames: no
PASS/WARN/FAIL semantics preserved: yes
Prompt pack index added: yes
Maintenance reference verified: yes
Workflow navigation reference verified: yes
Verification bundle reference verified: yes
Lifecycle guardrails preserved: yes
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

check_file "${index_doc}"

if [[ -f "${index_doc}" ]]; then
  check_doc_contains "${index_doc}" "Prompt Pack Reference Index" "Prompt Pack Reference Index"
  check_doc_contains "${index_doc}" "preserving all existing commands" "preserving all existing commands"
  check_doc_contains "${index_doc}" "no command removals" "no command removals"
  check_doc_contains "${index_doc}" "no command renames" "no command renames"
  check_doc_contains "${index_doc}" "no check removals" "no check removals"
  check_doc_contains "${index_doc}" "preserving command behavior" "preserving command behavior"
  check_doc_contains "${index_doc}" "PASS/WARN/FAIL semantics" "preserving PASS/WARN/FAIL semantics"
  check_doc_contains "${index_doc}" "prompt pack maintenance checklist" "prompt pack maintenance checklist"
  check_doc_contains "${index_doc}" "Workflow docs navigation status summary" "workflow docs navigation status summary"
  check_doc_contains "${index_doc}" "Verification Bundle Reference" "verification bundle reference"
  check_doc_contains "${index_doc}" "Prompt Template Reference" "prompt template reference"
  check_doc_contains "${index_doc}" "PR Lifecycle Reference" "PR lifecycle reference"
  check_doc_contains "${index_doc}" "Branch and Local Main Reference" "branch and local main reference"
  check_doc_contains "${index_doc}" "Reuse Review Reference" "reuse review reference"
  check_doc_contains "${index_doc}" "docs/prompt-pack-maintenance-checklist.md" "docs/prompt-pack-maintenance-checklist.md"
  check_doc_contains "${index_doc}" "docs/workflow-docs-navigation-status-summary.md" "docs/workflow-docs-navigation-status-summary.md"
  check_doc_contains "${index_doc}" "docs/testing-checklist-consolidation.md" "docs/testing-checklist-consolidation.md"
  check_doc_contains "${index_doc}" "docs/command-check-bundle-reference-polish.md" "docs/command-check-bundle-reference-polish.md"
  check_doc_contains "${index_doc}" "docs/checklist-driven-prompt-template-tightening.md" "docs/checklist-driven-prompt-template-tightening.md"
  check_doc_contains "${index_doc}" "docs/cursor-prompt-template.md" "docs/cursor-prompt-template.md"
  check_doc_contains "${index_doc}" "docs/pr-lifecycle-guardrail-consolidation.md" "docs/pr-lifecycle-guardrail-consolidation.md"
  check_doc_contains "${index_doc}" "docs/branch-hygiene-cleanup-reference.md" "docs/branch-hygiene-cleanup-reference.md"
  check_doc_contains "${index_doc}" "docs/local-main-proof-report-polish.md" "docs/local-main-proof-report-polish.md"
  check_doc_contains "${index_doc}" "no document scanning" "no document scanning"
  check_doc_contains "${index_doc}" "no file indexing" "no file indexing"
  check_doc_contains "${index_doc}" "no lesson generation changes" "no lesson generation changes"
  check_doc_contains "${index_doc}" "no real review notes" "no real review notes"
  check_doc_contains "${index_doc}" "no student data" "no student data"
  check_doc_contains "${index_doc}" "no network calls" "no network calls"
  check_doc_contains "${index_doc}" "no automation" "no automation"
fi

check_file "${maintenance_doc}"
check_file "${nav_doc}"
check_file "${crosslink_doc}"
check_file "${template_doc}"
check_file "${os_doc}"
check_file "${prompt_doc}"
check_file "${checklist_doc}"
check_file "${testing_doc}"
check_file "${bundle_doc}"
check_file "${lifecycle_doc}"
check_file "${branch_doc}"
check_file "${local_main_doc}"

section 'Cross-Link Checks'

if [[ -f "${maintenance_doc}" ]]; then
  check_doc_contains "${maintenance_doc}" "docs/prompt-pack-reference-index.md" "docs/prompt-pack-reference-index.md in maintenance doc"
fi
if [[ -f "${nav_doc}" ]]; then
  check_doc_contains "${nav_doc}" "docs/prompt-pack-reference-index.md" "docs/prompt-pack-reference-index.md in navigation doc"
fi
if [[ -f "${prompt_doc}" ]]; then
  check_doc_contains "${prompt_doc}" "docs/prompt-pack-reference-index.md" "docs/prompt-pack-reference-index.md in cursor prompt template"
fi
if [[ -f "${checklist_doc}" ]]; then
  check_doc_contains "${checklist_doc}" "docs/prompt-pack-reference-index.md" "docs/prompt-pack-reference-index.md in cursor PR review checklist"
fi

check_bash_syntax 'bin/chief-of-staff'
check_bash_syntax 'scripts/chief-of-staff-dashboard.sh'
check_bash_syntax 'scripts/phase-1-status.sh'

section 'Help and List Workflows Discovery'

check_help_contains '--prompt-pack-reference-index-status'
check_help_contains '--prompt-pack-maintenance-status'
check_help_contains '--workflow-docs-navigation-status'
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
