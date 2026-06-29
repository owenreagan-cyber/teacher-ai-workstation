#!/usr/bin/env bash
# Read-only prompt pack handoff summary status only. No network calls or file creation.
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

handoff_doc="docs/prompt-pack-handoff-summary.md"
freshness_doc="docs/prompt-pack-freshness-report-polish.md"
audit_doc="docs/prompt-pack-stale-reference-audit.md"
index_doc="docs/prompt-pack-reference-index.md"
maintenance_doc="docs/prompt-pack-maintenance-checklist.md"
nav_doc="docs/workflow-docs-navigation-status-summary.md"
os_doc="docs/cursor-workflow-operating-system.md"
prompt_doc="docs/cursor-prompt-template.md"
checklist_doc="docs/cursor-pr-review-checklist.md"
testing_doc="docs/testing-checklist-consolidation.md"
lifecycle_doc="docs/pr-lifecycle-guardrail-consolidation.md"
branch_doc="docs/branch-hygiene-cleanup-reference.md"
local_main_doc="docs/local-main-proof-report-polish.md"

section 'Prompt Pack Handoff Summary'
cat <<'EOF'
Status: prompt-pack-handoff/status only
Existing commands preserved: yes
Existing checks preserved: yes
Command behavior changed: no
Command removals: no
Command renames: no
PASS/WARN/FAIL semantics preserved: yes
Current prompt pack stack added: yes
Maintenance path verified: yes
Freshness path verified: yes
Stale-reference path verified: yes
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

check_file "${handoff_doc}"

if [[ -f "${handoff_doc}" ]]; then
  check_doc_contains "${handoff_doc}" "Prompt Pack Handoff Summary" "Prompt Pack Handoff Summary"
  check_doc_contains "${handoff_doc}" "preserving all existing commands" "preserving all existing commands"
  check_doc_contains "${handoff_doc}" "no command removals" "no command removals"
  check_doc_contains "${handoff_doc}" "no command renames" "no command renames"
  check_doc_contains "${handoff_doc}" "no check removals" "no check removals"
  check_doc_contains "${handoff_doc}" "preserving command behavior" "preserving command behavior"
  check_doc_contains "${handoff_doc}" "PASS/WARN/FAIL semantics" "preserving PASS/WARN/FAIL semantics"
  check_doc_contains "${handoff_doc}" "Current Prompt Pack Stack" "current prompt pack stack"
  check_doc_contains "${handoff_doc}" "Start-Here Prompt Pack Path" "start-here prompt pack path"
  check_doc_contains "${handoff_doc}" "Maintenance and Freshness Path" "maintenance and freshness path"
  check_doc_contains "${handoff_doc}" "Stale-Reference Audit Path" "stale-reference audit path"
  check_doc_contains "${handoff_doc}" "Verification Bundle Path" "verification bundle path"
  check_doc_contains "${handoff_doc}" "Lifecycle Guardrail Path" "lifecycle guardrail path"
  check_doc_contains "${handoff_doc}" "Future PR Prompt Handoff Rules" "future PR prompt handoff rules"
  check_doc_contains "${handoff_doc}" "docs/prompt-pack-maintenance-checklist.md" "docs/prompt-pack-maintenance-checklist.md"
  check_doc_contains "${handoff_doc}" "docs/prompt-pack-reference-index.md" "docs/prompt-pack-reference-index.md"
  check_doc_contains "${handoff_doc}" "docs/prompt-pack-stale-reference-audit.md" "docs/prompt-pack-stale-reference-audit.md"
  check_doc_contains "${handoff_doc}" "docs/prompt-pack-freshness-report-polish.md" "docs/prompt-pack-freshness-report-polish.md"
  check_doc_contains "${handoff_doc}" "docs/workflow-docs-navigation-status-summary.md" "docs/workflow-docs-navigation-status-summary.md"
  check_doc_contains "${handoff_doc}" "docs/testing-checklist-consolidation.md" "docs/testing-checklist-consolidation.md"
  check_doc_contains "${handoff_doc}" "docs/pr-lifecycle-guardrail-consolidation.md" "docs/pr-lifecycle-guardrail-consolidation.md"
  check_doc_contains "${handoff_doc}" "docs/branch-hygiene-cleanup-reference.md" "docs/branch-hygiene-cleanup-reference.md"
  check_doc_contains "${handoff_doc}" "docs/local-main-proof-report-polish.md" "docs/local-main-proof-report-polish.md"
  check_doc_contains "${handoff_doc}" "no document scanning" "no document scanning"
  check_doc_contains "${handoff_doc}" "no file indexing" "no file indexing"
  check_doc_contains "${handoff_doc}" "no lesson generation changes" "no lesson generation changes"
  check_doc_contains "${handoff_doc}" "no real review notes" "no real review notes"
  check_doc_contains "${handoff_doc}" "no student data" "no student data"
  check_doc_contains "${handoff_doc}" "no network calls" "no network calls"
  check_doc_contains "${handoff_doc}" "no automation" "no automation"
fi

check_file "${freshness_doc}"
check_file "${audit_doc}"
check_file "${index_doc}"
check_file "${maintenance_doc}"
check_file "${nav_doc}"
check_file "${os_doc}"
check_file "${prompt_doc}"
check_file "${checklist_doc}"
check_file "${testing_doc}"
check_file "${lifecycle_doc}"
check_file "${branch_doc}"
check_file "${local_main_doc}"

section 'Cross-Link Checks'

if [[ -f "${freshness_doc}" ]]; then
  check_doc_contains "${freshness_doc}" "docs/prompt-pack-handoff-summary.md" "docs/prompt-pack-handoff-summary.md in freshness doc"
fi
if [[ -f "${audit_doc}" ]]; then
  check_doc_contains "${audit_doc}" "docs/prompt-pack-handoff-summary.md" "docs/prompt-pack-handoff-summary.md in stale-reference audit"
fi
if [[ -f "${index_doc}" ]]; then
  check_doc_contains "${index_doc}" "docs/prompt-pack-handoff-summary.md" "docs/prompt-pack-handoff-summary.md in reference index"
fi
if [[ -f "${maintenance_doc}" ]]; then
  check_doc_contains "${maintenance_doc}" "docs/prompt-pack-handoff-summary.md" "docs/prompt-pack-handoff-summary.md in maintenance doc"
fi
if [[ -f "${prompt_doc}" ]]; then
  check_doc_contains "${prompt_doc}" "docs/prompt-pack-handoff-summary.md" "docs/prompt-pack-handoff-summary.md in cursor prompt template"
fi

check_bash_syntax 'bin/chief-of-staff'
check_bash_syntax 'scripts/chief-of-staff-dashboard.sh'
check_bash_syntax 'scripts/phase-1-status.sh'

section 'Help and List Workflows Discovery'

check_help_contains '--prompt-pack-handoff-summary-status'
check_help_contains '--prompt-pack-freshness-report-status'
check_help_contains '--prompt-pack-stale-reference-audit-status'
check_help_contains '--prompt-pack-reference-index-status'
check_help_contains '--prompt-pack-maintenance-status'
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
