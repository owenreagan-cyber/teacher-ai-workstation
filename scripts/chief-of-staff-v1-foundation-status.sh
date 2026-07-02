#!/usr/bin/env bash
# Read-only Chief of Staff v1 Agent Core (Program B1) foundation status.
set -euo pipefail

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

pass() { PASS_COUNT=$((PASS_COUNT + 1)); printf 'PASS: %s\n' "$1"; }
warn() { WARN_COUNT=$((WARN_COUNT + 1)); printf 'WARN: %s\n' "$1"; }
fail() { FAIL_COUNT=$((FAIL_COUNT + 1)); printf 'FAIL: %s\n' "$1"; }
section() { printf '\n%s\n' "$1"; printf '%s\n' '----------------------------------------'; }

check_file() {
  [[ -f "$1" ]] && pass "file exists: $1" || fail "file missing: $1"
}

check_doc_contains() {
  local path="$1" needle="$2" label="$3"
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
  bash -n "$1" && pass "bash syntax ok: $1" || fail "bash syntax failed: $1"
}

run_status() {
  local label="$1" script="$2"
  if [[ ! -f "${script}" ]]; then
    fail "${label} status script missing: ${script}"
    return 1
  fi
  if bash "${script}" >/dev/null 2>&1; then
    pass "${label} status exits 0"
    return 0
  fi
  fail "${label} status failed"
  return 1
}

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
[[ -z "${repo_root}" ]] && repo_root="$(cd "${script_dir}/.." && pwd -P)"
cd "${repo_root}"

section 'Chief of Staff v1 Agent Core (Program B1)'
cat <<'EOF'
Status: read-only foundation status only
Lesson generation: no
Network calls: no
Automation: no
Integration activation: no
EOF

check_file docs/chief-of-staff-v1-foundation.md
check_file docs/chief-of-staff-agent-core.md
check_file docs/chief-of-staff-operating-model.md
check_file docs/chief-of-staff-proof-workflow.md
check_file docs/chief-of-staff-command-index-v1.md
check_file assistant/chief-of-staff/v1/command-surface-manifest.json

check_doc_contains docs/chief-of-staff-agent-core.md "must not become" "agent core non-ownership boundaries"
check_doc_contains docs/chief-of-staff-operating-model.md "approval gate" "approval gate in operating model"
check_doc_contains docs/chief-of-staff-proof-workflow.md "branch deletion" "branch deletion in proof workflow"
check_doc_contains docs/chief-of-staff-command-index-v1.md "Implemented Commands" "implemented commands section"
check_doc_contains docs/chief-of-staff-command-index-v1.md "Planned Commands" "planned commands section"
check_doc_contains docs/chief-of-staff-command-index-v1.md "Blocked Commands" "blocked commands section"

check_file scripts/chief-of-staff-commands.sh
check_bash_syntax scripts/chief-of-staff-commands.sh
check_file scripts/chief-of-staff-command-index-v1-status.sh
check_bash_syntax scripts/chief-of-staff-command-index-v1-status.sh

if [[ -f bin/chief-of-staff ]]; then
  grep -Fq -- '--commands' bin/chief-of-staff && pass 'CLI exposes --commands' || fail 'CLI missing --commands'
  grep -Fq -- '--chief-of-staff-v1-status' bin/chief-of-staff && pass 'CLI exposes --chief-of-staff-v1-status' || fail 'CLI missing --chief-of-staff-v1-status'
else
  fail 'chief-of-staff CLI missing'
fi

run_status 'Command Index v1' scripts/chief-of-staff-command-index-v1-status.sh || true
run_status 'Commands surface' scripts/chief-of-staff-commands.sh || true
run_status 'Next Action' scripts/chief-of-staff-next-action.sh || true

pass 'no activation attempted'
pass 'no network call attempted'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"

[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
