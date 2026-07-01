#!/usr/bin/env bash
# Read-only Lesson Planning v1 foundation status only. No generation, network calls, or writes.
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

check_doc_contains() {
  local file="$1"
  local phrase="$2"
  local label="$3"
  if [[ ! -f "${file}" ]]; then
    fail "${file} must mention ${label}"
    return
  fi

  if grep -F -- "${phrase}" "${file}" >/dev/null; then
    pass "doc mentions ${label}"
  else
    fail "${file} must mention ${label}"
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

check_help_contains() {
  local flag="$1"
  if bin/chief-of-staff --help | grep -F -- "${flag}" >/dev/null; then
    pass "help contains ${flag}"
  else
    fail "help must contain ${flag}"
  fi
}

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "${repo_root}" ]]; then
  repo_root="$(cd "${script_dir}/.." && pwd -P)"
fi
cd "${repo_root}"

foundation_doc="docs/lesson-planning-v1-foundation.md"
workflow_guide="docs/lesson-planning-workflow-guide.md"
review_checklist="docs/safe-local-lesson-review-checklist.md"
workspace_readme="assistant/lesson-planning/README.md"
schema_file="assistant/lesson-planning/workflow/v0/lesson-workflow-schema.json"
sample_workflow="assistant/lesson-planning/workflow/v0/sample-lesson-workflow-001.json"
workflow_readme="assistant/lesson-planning/workflow/v0/README.md"
workspace_status="scripts/lesson-planning-status.sh"
workflow_validator="scripts/lesson-planning-workflow-v0-validator.sh"
workflow_status="scripts/lesson-workflow-status.sh"

section 'Lesson Planning v1 Foundation'
cat <<'EOF'
Status: documentation/status/workflow schema only
Lesson generation: no
Generated briefs: no
Generated drafts: no
Real review notes: no
Student data: no
LLM calls: no
APIs: no
Retrieval: no
Renderers: no
Network calls: no
EOF

section 'Foundation Documentation'
check_file "${foundation_doc}"
check_file "${workflow_guide}"
check_file "${review_checklist}"
check_file "${workspace_readme}"
check_doc_contains "${foundation_doc}" "no lesson generation" "no lesson generation boundary"
check_doc_contains "${foundation_doc}" "--lesson-planning-foundation-status" "foundation status command"
check_doc_contains "${foundation_doc}" "sample-lesson-workflow-001.json" "sample workflow fixture"

section 'Workflow Schema v0'
check_file "${schema_file}"
check_file "${sample_workflow}"
check_file "${workflow_readme}"
check_file "${workflow_validator}"
check_bash_syntax "${workflow_validator}"

if [[ -f "${workflow_validator}" ]]; then
  if bash "${workflow_validator}" >/dev/null 2>&1; then
    pass "workflow v0 validator exits 0 on sample workflow"
  else
    fail "workflow v0 validator failed on sample workflow"
  fi
fi

if command -v python3 >/dev/null 2>&1; then
  for json_file in "${schema_file}" "${sample_workflow}"; do
    if python3 -m json.tool "${json_file}" >/dev/null 2>&1; then
      pass "JSON parses: ${json_file}"
    else
      fail "JSON does not parse: ${json_file}"
    fi
  done
else
  warn 'python3 not available for JSON parse checks'
fi

section 'Workspace and Workflow Status'
check_file "${workspace_status}"
check_file "${workflow_status}"
check_bash_syntax "${workspace_status}"
check_bash_syntax "${workflow_status}"

if [[ -f "${workspace_status}" ]]; then
  if bash "${workspace_status}" >/dev/null 2>&1; then
    pass "lesson planning workspace status exits 0"
  else
    fail "lesson planning workspace status failed"
  fi
fi

section 'Chief of Staff Integration'
check_help_contains "--lesson-planning-foundation-status"
check_help_contains "--lesson-planning-workflow-v0-validate"
check_bash_syntax "bin/chief-of-staff"

pass 'no write action attempted'
pass 'no lesson generation attempted'
pass 'no network call attempted'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"

if [[ "${FAIL_COUNT}" -gt 0 ]]; then
  exit 1
fi

exit 0
