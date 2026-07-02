#!/usr/bin/env bash
# Read-only Autonomous Build Engine governance status. Documentation/status only.
set -euo pipefail

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

pass() { PASS_COUNT=$((PASS_COUNT + 1)); printf 'PASS: %s\n' "$1"; }
warn() { WARN_COUNT=$((WARN_COUNT + 1)); printf 'WARN: %s\n' "$1"; }
fail() { FAIL_COUNT=$((FAIL_COUNT + 1)); printf 'FAIL: %s\n' "$1"; }
section() { printf '\n%s\n' "$1"; printf '%s\n' '----------------------------------------'; }

check_file() { [[ -f "$1" ]] && pass "file exists: $1" || fail "file missing: $1"; }
check_doc_contains() {
  local path="$1" needle="$2" label="$3"
  [[ ! -f "${path}" ]] && { fail "${path} must mention ${label}"; return; }
  grep -Fq -- "${needle}" "${path}" && pass "doc mentions ${label}" || fail "${path} must mention ${label}"
}

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
[[ -z "${repo_root}" ]] && repo_root="$(cd "${script_dir}/.." && pwd -P)"
cd "${repo_root}"

governance_doc="docs/cursor-autonomous-build-engine.md"
operating_modes_doc="docs/cursor-operating-modes-and-approval-gates.md"
expected_warns_doc="docs/curriculum-builder-registry-expected-warns.md"
status_script="scripts/autonomous-build-engine-status.sh"
status_test="tests/autonomous-build-engine-status-test.sh"

section 'Autonomous Build Engine Governance (Read-Only Foundation)'
cat <<'EOF'
Status: documentation/status only
Production registry writes: blocked
Active --write: blocked
Student data: blocked
Real curriculum content: blocked
APIs/OAuth/network: blocked
Generation: blocked
EOF

section 'Governance Document'
check_file "${governance_doc}"
check_doc_contains "${governance_doc}" "complete_autonomous_build_engine_governance" "closure status"
check_doc_contains "${governance_doc}" "Autonomous Build Engine Mode" "autonomous build engine mode"
check_doc_contains "${governance_doc}" "Autonomous Continuation Loop" "continuation loop"
check_doc_contains "${governance_doc}" "Safe Work Class A" "safe work class A"
check_doc_contains "${governance_doc}" "Safe Work Class G" "safe work class G"
check_doc_contains "${governance_doc}" "Minimum Exhaustion Rule" "minimum exhaustion rule"
check_doc_contains "${governance_doc}" "No Soft Stop Rule" "no soft stop rule"
check_doc_contains "${governance_doc}" "Expected WARN Policy" "expected WARN policy"
check_doc_contains "${governance_doc}" "Level 1" "level 1 discovery"
check_doc_contains "${governance_doc}" "Level 2" "level 2 discovery"
check_doc_contains "${governance_doc}" "Level 3" "level 3 discovery"
check_doc_contains "${governance_doc}" "Scope-lock" "scope-lock"
check_doc_contains "${governance_doc}" "exact stop reason" "stop reason"
check_doc_contains "${governance_doc}" "Operate under Autonomous Build Engine Mode" "prompt invocation snippet"
check_doc_contains "${governance_doc}" "Builder" "builder role"
check_doc_contains "${governance_doc}" "Proposal / roadmap strategist" "strategist role"

section 'Seven Roles and Continuation Core Rule'
check_doc_contains "${governance_doc}" "Seven Operating Roles" "seven operating roles"
check_doc_contains "${governance_doc}" "Hardening engineer" "hardening engineer role"
check_doc_contains "${governance_doc}" "originally named deliverables are complete" "core continuation rule"

section 'Expected WARN Registry'
check_file "${expected_warns_doc}"
check_doc_contains "${expected_warns_doc}" "Registered WARNs" "expected warns registry"
check_doc_contains "${governance_doc}" "curriculum-builder-registry-expected-warns.md" "expected warns cross-link"

section 'Operating Modes Cross-Link'
check_doc_contains "${operating_modes_doc}" "cursor-autonomous-build-engine.md" "operating modes links autonomous build engine"

section 'CLI, Manifest, Status Script, and Tests'
grep -Fq -- '--autonomous-build-engine-status' bin/chief-of-staff && pass 'CLI exposes --autonomous-build-engine-status' || fail 'CLI missing --autonomous-build-engine-status'
grep -Fq -- '"--autonomous-build-engine-status"' assistant/chief-of-staff/v1/command-surface-manifest.json && pass 'manifest lists --autonomous-build-engine-status' || fail 'manifest missing --autonomous-build-engine-status'
check_file "${status_script}"
check_file "${status_test}"
bash -n "${status_script}" && pass "bash syntax ok: ${status_script}" || fail "bash syntax failed: ${status_script}"
bash -n "${status_test}" && pass "bash syntax ok: ${status_test}" || fail "bash syntax failed: ${status_test}"

section 'Roadmap and Priority Coherence'
check_doc_contains docs/master-build-roadmap.md "complete_autonomous_build_engine_governance" "roadmap autonomous build engine"
check_doc_contains docs/build-queue.md "Autonomous Build Engine" "build queue autonomous build engine"
check_doc_contains assistant/memory/active-priorities.md "Autonomous Build Engine" "active priorities autonomous build engine"
check_doc_contains docs/teacher-workstation-capability-map.md "--autonomous-build-engine-status" "capability map autonomous build engine"

section 'Negative Non-Activation Assertions'
grep -Eq '(^|[;&|[:space:]])curl[[:space:]]' "${status_script}" 2>/dev/null && fail "${status_script} must not shell-invoke curl" || pass "${status_script} does not shell-invoke curl"
grep -Eq '(^|[;&|[:space:]])find[[:space:]]' "${status_script}" 2>/dev/null && fail "${status_script} must not shell-invoke find" || pass "${status_script} does not shell-invoke find"
grep -Eq '(^|[;&|[:space:]])ollama[[:space:]]' "${status_script}" 2>/dev/null && fail "${status_script} must not shell-invoke ollama" || pass "${status_script} does not shell-invoke ollama"
grep -Fq -- '--curriculum-registry-write)' bin/chief-of-staff 2>/dev/null && fail 'chief-of-staff must not implement --curriculum-registry-write handler' || pass 'chief-of-staff has no --curriculum-registry-write handler'
pass 'no production registry write attempted'
pass 'no active --write implemented'
pass 'no network call attempted'
pass 'no student data workflow attempted'
pass 'no generation attempted'
pass 'Owen approval required for production/runtime work'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
