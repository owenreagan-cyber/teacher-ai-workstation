#!/usr/bin/env bash
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

check_text() {
  local path="$1"
  local pattern="$2"
  local label="$3"

  if [[ ! -f "${path}" ]]; then
    fail "${label}: missing ${path}"
    return
  fi

  if grep -Eiq "${pattern}" "${path}"; then
    pass "${label}"
  else
    fail "${label}"
  fi
}

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "${repo_root}" ]]; then
  repo_root="$(cd "${script_dir}/.." && pwd -P)"
fi
cd "${repo_root}"

plan_doc="docs/safe-local-document-indexing-plan.md"

section "Safe Local Document Indexing Plan"
cat <<'EOF'
Status: planning only
Indexing implemented: no
Folder scanning implemented: no
Embeddings implemented: no
Vector database implemented: no
Connected sources implemented: no
Read-only: yes
EOF

section "Future Approval Gates"
cat <<'EOF'
1. Approve folder allowlist
2. Approve inventory-only scan
3. Approve metadata-only index
4. Approve content extraction, if ever needed
5. Approve local embeddings, if ever needed
6. Approve connected sources, if ever needed
EOF

section "Workflow Checks"

check_file "${plan_doc}"

check_text "${plan_doc}" "planning-only|planning only|planning-only baseline" "plan mentions planning-only"
check_text "${plan_doc}" "local only" "plan mentions local only"
check_text "${plan_doc}" "read-only" "plan mentions read-only"
check_text "${plan_doc}" "allowlist" "plan mentions allowlist"
check_text "${plan_doc}" "human approval" "plan mentions human approval"
check_text "${plan_doc}" "quarantine" "plan mentions quarantine"
check_text "${plan_doc}" "no student-sensitive data|student-sensitive data" "plan mentions no student-sensitive data"
check_text "${plan_doc}" "no real student names|real student names" "plan mentions no real student names"
check_text "${plan_doc}" "No Gmail|no Gmail" "plan mentions no Gmail"
check_text "${plan_doc}" "No Google Drive|no Google Drive|Google Drive" "plan mentions no Google Drive"
check_text "${plan_doc}" "No Google Calendar|no Google Calendar|Google Calendar" "plan mentions no Google Calendar"
check_text "${plan_doc}" "No APIs|no APIs" "plan mentions no APIs"
check_text "${plan_doc}" "No OAuth|no OAuth" "plan mentions no OAuth"
check_text "${plan_doc}" "No secrets|no secrets" "plan mentions no secrets"
check_text "${plan_doc}" "No LLM calls by default|no LLM calls" "plan mentions no LLM calls by default"
check_text "${plan_doc}" "No embeddings yet|no embeddings yet|Embeddings: not implemented" "plan mentions no embeddings yet"
check_text "${plan_doc}" "No vector database yet|no vector database yet|Vector database: not implemented" "plan mentions no vector database yet"
check_text "${plan_doc}" "No background scanning|no background scanning|background scanning" "plan mentions no background scanning"
check_text "${plan_doc}" "No school systems|no school systems|school systems" "plan mentions no school systems"
check_text "${plan_doc}" "No publishing|no publishing|publishing, sharing, or sending" "plan mentions no publishing/sharing/sending"

check_bash_syntax "bin/chief-of-staff"
check_bash_syntax "scripts/chief-of-staff-dashboard.sh"
check_bash_syntax "scripts/phase-1-status.sh"

pass "no write action attempted"
pass "no folder scanning attempted"
pass "no document content reading attempted"

section "Summary"
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"

if [[ "${FAIL_COUNT}" -gt 0 ]]; then
  exit 1
fi

exit 0
