#!/usr/bin/env bash
# Read-only Chief of Staff Command Index v1 status only.
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
  local path="$1"
  local needle="$2"
  local label="$3"
  if [[ ! -f "${path}" ]]; then
    fail "${path} must mention ${label}"
    return
  fi
  if grep -Fq -- "${needle}" "${path}"; then
    pass "doc mentions ${label}"
  else
    fail "${path} must mention ${label}"
  fi
}

check_bash_syntax() {
  local path="$1"
  if bash -n "${path}"; then
    pass "bash syntax ok: ${path}"
  else
    fail "bash syntax failed: ${path}"
  fi
}

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "${repo_root}" ]]; then
  repo_root="$(cd "${script_dir}/.." && pwd -P)"
fi
cd "${repo_root}"

index_doc="docs/chief-of-staff-command-index-v1.md"
agent_core_doc="docs/chief-of-staff-agent-core.md"
v1_foundation_doc="docs/chief-of-staff-v1-foundation.md"
manifest_file="assistant/chief-of-staff/v1/command-surface-manifest.json"
commands_script="scripts/chief-of-staff-commands.sh"
v1_foundation_script="scripts/chief-of-staff-v1-foundation-status.sh"
next_action_script="scripts/chief-of-staff-next-action.sh"
chief_of_staff="bin/chief-of-staff"
dashboard_doc="docs/chief-of-staff-dashboard.md"

section 'Chief of Staff Command Index v1'
cat <<'EOF'
Status: read-only command index status only
Network calls: no
Lesson generation: no
EOF

check_file "${index_doc}"
check_doc_contains "${index_doc}" "Index status: active_v1" "index active_v1"
check_doc_contains "${index_doc}" "Implemented Commands" "implemented commands section"
check_doc_contains "${index_doc}" "Planned Commands" "planned commands section"
check_doc_contains "${index_doc}" "Blocked Commands" "blocked commands section"
check_doc_contains "${index_doc}" "--commands" "commands command documented"
check_doc_contains "${index_doc}" "--next-action" "next-action command documented"
check_doc_contains "${index_doc}" "--validate-all" "validate-all command documented"
check_doc_contains "${index_doc}" "--proof-run" "proof-run command documented"
check_doc_contains "${index_doc}" "--daily-status" "daily-status command documented"
check_doc_contains "${index_doc}" "--closeout" "closeout command documented"
check_doc_contains "${index_doc}" "--approval-queue" "approval-queue command documented"
check_doc_contains "${index_doc}" "--blocker-queue" "blocker-queue command documented"
check_doc_contains "${index_doc}" "--mode-status" "mode-status command documented"
check_doc_contains "${index_doc}" "Curriculum Builder" "curriculum builder commands documented"
check_doc_contains "${index_doc}" "Canvas LLM" "canvas llm commands documented"
check_doc_contains "${index_doc}" "no lesson generation" "no lesson generation boundary"

check_file "${agent_core_doc}"
check_file "${v1_foundation_doc}"
check_file "${manifest_file}"
check_file "${commands_script}"
check_bash_syntax "${commands_script}"
check_file "${v1_foundation_script}"
check_bash_syntax "${v1_foundation_script}"

check_file "${next_action_script}"
check_bash_syntax "${next_action_script}"

if [[ -f "${chief_of_staff}" ]]; then
  if grep -Fq -- '--next-action' "${chief_of_staff}"; then
    pass "chief-of-staff exposes --next-action"
  else
    fail "chief-of-staff missing --next-action"
  fi
  if grep -Fq -- '--chief-of-staff-command-index-v1-status' "${chief_of_staff}"; then
    pass "chief-of-staff exposes --chief-of-staff-command-index-v1-status"
  else
    fail "chief-of-staff missing --chief-of-staff-command-index-v1-status"
  fi
  if grep -Fq -- '--commands' "${chief_of_staff}"; then
    pass "chief-of-staff exposes --commands"
  else
    fail "chief-of-staff missing --commands"
  fi
  if grep -Fq -- '--chief-of-staff-v1-status' "${chief_of_staff}"; then
    pass "chief-of-staff exposes --chief-of-staff-v1-status"
  else
    fail "chief-of-staff missing --chief-of-staff-v1-status"
  fi
else
  fail "chief-of-staff missing"
fi

check_doc_contains "${dashboard_doc}" "next-action" "dashboard doc references next-action"

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"

if [[ "${FAIL_COUNT}" -gt 0 ]]; then
  exit 1
fi

exit 0
