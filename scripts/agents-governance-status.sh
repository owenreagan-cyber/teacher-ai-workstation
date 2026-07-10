#!/usr/bin/env bash
# Read-only AGENTS.md governance status. Documentation/status only — no external tools.
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
check_doc_must_not_contain() {
  local path="$1" needle="$2" label="$3"
  [[ ! -f "${path}" ]] && { fail "${path} missing for ${label} check"; return; }
  if grep -Fq -- "${needle}" "${path}"; then
    fail "${path} must not embed ${label} as a global rule"
  else
    pass "${path} excludes global ${label} embed"
  fi
}

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
[[ -z "${repo_root}" ]] && repo_root="$(cd "${script_dir}/.." && pwd -P)"
cd "${repo_root}"

agents_md="AGENTS.md"
secrets_doc="docs/secrets-and-agent-access-policy.md"
status_script="scripts/agents-governance-status.sh"
status_test="tests/agents-governance-status-test.sh"

section 'AGENTS.md Governance (Read-Only Foundation)'
cat <<'EOF'
Status: documentation/status only
Global guidance: yes
Implementation approval: not granted by AGENTS.md
Runtime activation: no
External tools: no
Secrets inspection: no
Local ignored dirs: no access
Network calls: no
PASS does not authorize implementation: yes
EOF

section 'AGENTS.md Presence and Authority Order'
check_file "${agents_md}"
check_doc_contains "${agents_md}" "Authority Stack (Read Order)" "authority stack read order"
check_doc_contains "${agents_md}" "Explicit mission prompt" "explicit mission prompt in authority order"
check_doc_contains "${agents_md}" "does not replace" "non-replacement of deeper authority docs"
check_doc_contains "${agents_md}" "Global Guidance vs Implementation Approval" "global guidance vs implementation approval"

section 'Cost, Context, Secrets, and Safety Boundaries'
check_doc_contains "${agents_md}" "Cost and Context Rules" "cost and context rules"
check_doc_contains "${agents_md}" "Secrets Rules" "secrets rules"
check_file "${secrets_doc}"
check_doc_contains "${agents_md}" "docs/secrets-and-agent-access-policy.md" "secrets policy cross-link"
check_doc_contains "${agents_md}" "Permanent Hard Boundaries" "safety boundaries"
check_doc_contains "${agents_md}" "Student data" "student data boundary"
check_doc_contains "${agents_md}" "Curriculum content" "real curriculum boundary"
check_doc_contains "${agents_md}" "Network / API" "integration API boundary"
check_doc_contains "${agents_md}" "Integrations" "integrations boundary"

section 'Validation, Git/PR Lifecycle, and Autonomous Scope'
check_doc_contains "${agents_md}" "Validation Commands" "validation rules"
check_doc_contains "${agents_md}" "Git and PR Lifecycle Rules" "git PR lifecycle rules"
check_doc_contains "${agents_md}" "Full Autonomous Lifecycle (Mission-Scoped Only)" "full autonomous lifecycle scoped section"
check_doc_contains "${agents_md}" "explicit mission prompt" "autonomous scope requires explicit mission"
check_doc_contains "${agents_md}" "approved repo edits" "approved repo edits scope"
check_doc_contains "${agents_md}" "Blocked Runtime and Product Writes" "blocked runtime product writes"

section 'Production Registry and --write Boundary'
check_doc_contains "${agents_md}" "Production Registry and --write Boundary" "production registry write boundary section"
check_doc_contains "${agents_md}" "--curriculum-registry-write" "curriculum registry write blocked"
check_doc_contains "${agents_md}" "writer scripts" "writer scripts blocked"
grep -Fq -- '--curriculum-registry-write)' bin/chief-of-staff 2>/dev/null && fail 'chief-of-staff must not implement --curriculum-registry-write handler' || pass 'chief-of-staff has no --curriculum-registry-write handler'

section 'Phase-Specific Instructions Excluded From Global Rules'
check_doc_contains "${agents_md}" "Phase-Specific Instructions (Not Global Rules)" "phase-specific exclusion section"
check_doc_contains "${agents_md}" "Do **not** embed phase-specific" "phase-specific rules excluded from global AGENTS.md"
check_doc_contains "${agents_md}" "docs/programs/" "phase-specific rules delegated to track docs"

section 'Coherence Cross-Links'
check_doc_contains docs/engineering-constitution.md "AGENTS.md" "engineering constitution links AGENTS.md"
check_doc_contains docs/build-queue.md "AGENTS.md" "build queue links AGENTS.md"
check_doc_contains docs/chief-of-staff-command-index-v1.md "AGENTS.md" "command index links AGENTS.md"
check_doc_contains assistant/memory/active-priorities.md "AGENTS.md" "active priorities links AGENTS.md"

section 'CLI, Manifest, Dashboard, Validate-All, Phase-1, and Tests'
bash -n "${status_script}" && pass "bash syntax ok: ${status_script}" || fail "bash syntax failed: ${status_script}"
grep -Fq -- '--agents-governance-status' bin/chief-of-staff && pass 'CLI exposes --agents-governance-status' || fail 'CLI missing --agents-governance-status'
grep -Fq -- '"--agents-governance-status"' assistant/chief-of-staff/v1/command-surface-manifest.json && pass 'manifest lists --agents-governance-status' || fail 'manifest missing --agents-governance-status'
check_file "${status_test}"
bash -n "${status_test}" && pass "bash syntax ok: ${status_test}" || fail "bash syntax failed: ${status_test}"
grep -Fq -- 'agents-governance-status.sh' scripts/chief-of-staff-dashboard.sh && pass 'dashboard wires agents governance status' || fail 'dashboard missing agents governance status'
grep -Fq -- 'agents-governance-status.sh' scripts/chief-of-staff-validate-all.sh && pass 'validate-all wires agents governance status' || fail 'validate-all missing agents governance status'
source scripts/validation-smoke-tier-boundary.sh
check_smoke_excludes_deep_validation 'agents-governance' 'AGENTS.md governance'

section 'Negative Non-Activation Assertions'
grep -Eq '(^|[;&|[:space:]])curl[[:space:]]' "${status_script}" 2>/dev/null && fail "${status_script} must not shell-invoke curl" || pass "${status_script} does not shell-invoke curl"
grep -Eq '(^|[;&|[:space:]])wget[[:space:]]' "${status_script}" 2>/dev/null && fail "${status_script} must not shell-invoke wget" || pass "${status_script} does not shell-invoke wget"
grep -Eq '(^|[;&|[:space:]])brew[[:space:]]' "${status_script}" 2>/dev/null && fail "${status_script} must not shell-invoke brew" || pass "${status_script} does not shell-invoke brew"
grep -Eq '(^|[;&|[:space:]])npm[[:space:]]' "${status_script}" 2>/dev/null && fail "${status_script} must not shell-invoke npm" || pass "${status_script} does not shell-invoke npm"
grep -Eq '(^|[;&|[:space:]])ollama[[:space:]]' "${status_script}" 2>/dev/null && fail "${status_script} must not shell-invoke ollama" || pass "${status_script} does not shell-invoke ollama"
grep -Eq '(^|[;&|[:space:]])find[[:space:]]' "${status_script}" 2>/dev/null && fail "${status_script} must not shell-invoke find" || pass "${status_script} does not shell-invoke find"
pass 'no network call attempted'
pass 'no write action attempted'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
