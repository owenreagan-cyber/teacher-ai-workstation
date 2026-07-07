#!/usr/bin/env bash
# Read-only Canvas LLM Phase 1 fake/local validator status. No live Canvas access.
set -euo pipefail

PASS_COUNT=0; WARN_COUNT=0; FAIL_COUNT=0
pass() { PASS_COUNT=$((PASS_COUNT + 1)); printf 'PASS: %s\n' "$1"; }
warn() { WARN_COUNT=$((WARN_COUNT + 1)); printf 'WARN: %s\n' "$1"; }
fail() { FAIL_COUNT=$((FAIL_COUNT + 1)); printf 'FAIL: %s\n' "$1"; }
section() { printf '\n%s\n' "$1"; printf '%s\n' '----------------------------------------'; }
check_file() { [[ -f "$1" ]] && pass "file exists: $1" || fail "file missing: $1"; }
check_doc_contains() {
  local file="$1" phrase="$2" label="$3"
  [[ -f "${file}" ]] || { fail "${file} must mention ${label}"; return; }
  grep -F -- "${phrase}" "${file}" >/dev/null && pass "doc mentions ${label}" || fail "${file} must mention ${label}"
}
check_help_contains() {
  bin/chief-of-staff --help | grep -F -- "$1" >/dev/null && pass "help contains $1" || fail "help must contain $1"
}

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
[[ -z "${repo_root}" ]] && repo_root="$(cd "${script_dir}/.." && pwd -P)"
cd "${repo_root}"

section 'Canvas LLM Phase 1 Status'
cat <<'EOF'
Status: canvas_llm_phase_1_fake_local_validator_complete
Classification: fake/local validation only
Runtime activation: no
Canvas API/OAuth/live reads: blocked
Canvas writes/publishing: blocked
Student data: blocked
Network access: no
PASS does not authorize live Canvas validation, generation, export, publishing, or self-healing.
EOF

section 'Phase 1 Documentation'
check_file docs/programs/canvas-llm/canvas-phase-1-fake-local-validator.md
check_doc_contains docs/programs/canvas-llm/canvas-phase-1-fake-local-validator.md "checks only committed fake/local files" "fixed fake/local scope"
check_doc_contains docs/programs/canvas-llm/canvas-phase-1-fake-local-validator.md "does not validate" "non-validation boundary"
check_doc_contains docs/programs/canvas-llm/canvas-phase-1-fake-local-validator.md "Canvas API/OAuth/live reads" "Canvas live access blocked"
check_doc_contains docs/programs/canvas-llm/canvas-validation-tiers.md "Tier 1 - Fake/Local Consistency" "Tier 1 validation tier"

section 'Validator Script'
check_file scripts/canvas-llm-fake-local-validator.sh
bash -n scripts/canvas-llm-fake-local-validator.sh && pass "bash syntax ok: scripts/canvas-llm-fake-local-validator.sh" || fail "bash syntax failed: scripts/canvas-llm-fake-local-validator.sh"
if bash scripts/canvas-llm-fake-local-validator.sh >/tmp/canvas-llm-fake-local-validator.out 2>&1; then
  pass "fake/local validator exits 0"
else
  fail "fake/local validator failed"
  tail -40 /tmp/canvas-llm-fake-local-validator.out || true
fi

section 'Command And Roadmap Integration'
check_help_contains "--canvas-llm-phase-1-status"
check_doc_contains assistant/chief-of-staff/v1/command-surface-manifest.json '"--canvas-llm-phase-1-status"' "manifest Canvas Phase 1 command"
check_doc_contains docs/chief-of-staff-command-index-v1.md "--canvas-llm-phase-1-status" "command index Canvas Phase 1 command"
check_doc_contains docs/master-plan/build-state-checklist.md "Canvas LLM Phase 1 fake/local validator" "build-state Canvas Phase 1"
check_doc_contains docs/build-queue.md "canvas_llm_phase_1_fake_local_validator_complete" "build queue Canvas Phase 1 closure"
check_doc_contains assistant/memory/active-priorities.md "Canvas LLM Phase 1 fake/local validator: complete" "active priorities Canvas Phase 1 closure"

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"; printf 'WARN: %s\n' "${WARN_COUNT}"; printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
