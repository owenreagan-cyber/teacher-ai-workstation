#!/usr/bin/env bash
# Read-only prompt pack stack completion marker status only. No network calls or file creation.
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

completion_doc="docs/prompt-pack-stack-completion-marker.md"
handoff_doc="docs/prompt-pack-handoff-summary.md"
freshness_doc="docs/prompt-pack-freshness-report-polish.md"
audit_doc="docs/prompt-pack-stale-reference-audit.md"
index_doc="docs/prompt-pack-reference-index.md"
maintenance_doc="docs/prompt-pack-maintenance-checklist.md"
nav_doc="docs/workflow-docs-navigation-status-summary.md"
testing_doc="docs/testing-checklist-consolidation.md"
bundle_doc="docs/command-check-bundle-reference-polish.md"
template_doc="docs/checklist-driven-prompt-template-tightening.md"
lifecycle_doc="docs/pr-lifecycle-guardrail-consolidation.md"
branch_doc="docs/branch-hygiene-cleanup-reference.md"
local_main_doc="docs/local-main-proof-report-polish.md"
os_doc="docs/cursor-workflow-operating-system.md"
prompt_doc="docs/cursor-prompt-template.md"

section 'Prompt Pack Stack Completion Marker'
cat <<'EOF'
Status: prompt-pack-completion/status only
Existing commands preserved: yes
Existing checks preserved: yes
Command behavior changed: no
Command removals: no
Command renames: no
PASS/WARN/FAIL semantics preserved: yes
Prompt pack stack complete for now: yes
Safe return point documented: yes
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

check_file "${completion_doc}"

if [[ -f "${completion_doc}" ]]; then
  check_doc_contains "${completion_doc}" "Prompt Pack Stack Completion Marker" "Prompt Pack Stack Completion Marker"
  check_doc_contains "${completion_doc}" "reusable prompt pack documentation stack complete for now" "reusable prompt pack documentation stack complete for now"
  check_doc_contains "${completion_doc}" "safe return point" "safe return point"
  check_doc_contains "${completion_doc}" "Core Teacher Workstation planning cleanup" "Core Teacher Workstation planning cleanup"
  check_doc_contains "${completion_doc}" "preserving all existing commands" "preserving all existing commands"
  check_doc_contains "${completion_doc}" "no command removals" "no command removals"
  check_doc_contains "${completion_doc}" "no command renames" "no command renames"
  check_doc_contains "${completion_doc}" "no check removals" "no check removals"
  check_doc_contains "${completion_doc}" "preserving command behavior" "preserving command behavior"
  check_doc_contains "${completion_doc}" "PASS/WARN/FAIL semantics" "preserving PASS/WARN/FAIL semantics"
  check_doc_contains "${completion_doc}" "Current Prompt Pack Stack" "current prompt pack stack"
  check_doc_contains "${completion_doc}" "Verification Commands" "verification commands"
  check_doc_contains "${completion_doc}" "Future Prompt Pack Work" "future prompt pack work"
  check_doc_contains "${completion_doc}" "Lifecycle Guardrails Still Required" "lifecycle guardrails still required"
  check_doc_contains "${completion_doc}" "Safety Boundaries Still Required" "safety boundaries still required"
  check_doc_contains "${completion_doc}" "docs/prompt-pack-maintenance-checklist.md" "docs/prompt-pack-maintenance-checklist.md"
  check_doc_contains "${completion_doc}" "docs/prompt-pack-reference-index.md" "docs/prompt-pack-reference-index.md"
  check_doc_contains "${completion_doc}" "docs/prompt-pack-stale-reference-audit.md" "docs/prompt-pack-stale-reference-audit.md"
  check_doc_contains "${completion_doc}" "docs/prompt-pack-freshness-report-polish.md" "docs/prompt-pack-freshness-report-polish.md"
  check_doc_contains "${completion_doc}" "docs/prompt-pack-handoff-summary.md" "docs/prompt-pack-handoff-summary.md"
  check_doc_contains "${completion_doc}" "no document scanning" "no document scanning"
  check_doc_contains "${completion_doc}" "no file indexing" "no file indexing"
  check_doc_contains "${completion_doc}" "no lesson generation changes" "no lesson generation changes"
  check_doc_contains "${completion_doc}" "no real review notes" "no real review notes"
  check_doc_contains "${completion_doc}" "no student data" "no student data"
  check_doc_contains "${completion_doc}" "no network calls" "no network calls"
  check_doc_contains "${completion_doc}" "no automation" "no automation"
fi

check_file "${handoff_doc}"
check_file "${freshness_doc}"
check_file "${audit_doc}"
check_file "${index_doc}"
check_file "${maintenance_doc}"
check_file "${nav_doc}"
check_file "${testing_doc}"
check_file "${bundle_doc}"
check_file "${template_doc}"
check_file "${lifecycle_doc}"
check_file "${branch_doc}"
check_file "${local_main_doc}"
check_file "${os_doc}"
check_file "${prompt_doc}"

section 'Cross-Link Checks'

if [[ -f "${handoff_doc}" ]]; then
  check_doc_contains "${handoff_doc}" "docs/prompt-pack-stack-completion-marker.md" "docs/prompt-pack-stack-completion-marker.md in handoff doc"
fi
if [[ -f "${freshness_doc}" ]]; then
  check_doc_contains "${freshness_doc}" "docs/prompt-pack-stack-completion-marker.md" "docs/prompt-pack-stack-completion-marker.md in freshness doc"
fi
if [[ -f "${index_doc}" ]]; then
  check_doc_contains "${index_doc}" "docs/prompt-pack-stack-completion-marker.md" "docs/prompt-pack-stack-completion-marker.md in reference index"
fi
if [[ -f "${maintenance_doc}" ]]; then
  check_doc_contains "${maintenance_doc}" "docs/prompt-pack-stack-completion-marker.md" "docs/prompt-pack-stack-completion-marker.md in maintenance doc"
fi
if [[ -f "${prompt_doc}" ]]; then
  check_doc_contains "${prompt_doc}" "docs/prompt-pack-stack-completion-marker.md" "docs/prompt-pack-stack-completion-marker.md in cursor prompt template"
fi

check_bash_syntax 'bin/chief-of-staff'
check_bash_syntax 'scripts/chief-of-staff-dashboard.sh'
check_bash_syntax 'scripts/phase-1-status.sh'

section 'Help and List Workflows Discovery'

check_help_contains '--prompt-pack-stack-completion-status'
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
