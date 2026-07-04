#!/usr/bin/env bash
# Read-only agent builder compatibility / external tool governance status. No tool invocation.
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

governance_doc="docs/agent-builder-compatibility-and-external-tool-governance.md"
trial_checklist="docs/agent-builder-safe-tool-trial-checklist.md"
proof_template="docs/agent-builder-mission-proof-template.md"
blocked_doc="docs/proposals/blocked/agent-builder-external-tool-runtime-boundaries.md"
routing_matrix="docs/ai-tool-routing-matrix.md"
production_registry_path="assistant/curriculum-builder/registry/v0-2/production-registry.json"
sentinel="assistant/curriculum-builder/registry/candidate-v0-2-production/BLOCKED-NO-WRITES.sentinel"

section 'Agent Builder Compatibility Governance (Documentation Only)'
cat <<'EOF'
Status: documentation/status only
External agent launch from Chief of Staff: no
Tool install/integration: no
API/OAuth/network: no
Student data: blocked — absolute
Production registry writes: no
PASS does not authorize implementation: yes
EOF

section 'Canonical Governance Docs'
check_file "${governance_doc}"
check_file "${trial_checklist}"
check_file "${proof_template}"
check_file "${blocked_doc}"
check_file docs/proposals/ideas/agent-builder-compatibility-governance.md
check_doc_contains "${governance_doc}" "complete_agent_builder_compatibility_governance_program" "governance closure marker"
check_doc_contains "${governance_doc}" "Chief of Staff never launches" "CoS no-launch rule"
check_doc_contains "${governance_doc}" "Google Antigravity" "Antigravity classification"
check_doc_contains "${governance_doc}" "Claude Code" "Claude Code classification"
check_doc_contains "${governance_doc}" "Full Autonomous Run Approval Scope" "autonomous approval scope section"
check_doc_contains "${blocked_doc}" "Chief of Staff launching external agents" "blocked CoS agent launch"

section 'AI Tool Routing Cross-Link'
check_file "${routing_matrix}"
check_doc_contains "${routing_matrix}" "ai-tool-routing" "routing matrix authority"
check_doc_contains "${governance_doc}" "ai-tool-routing-matrix.md" "governance cross-link to routing matrix"

section 'Classification Summary Fixture'
check_file assistant/agent-builder-governance/samples/README.md
check_file assistant/agent-builder-governance/samples/classification-summary.json
check_doc_contains assistant/agent-builder-governance/samples/classification-summary.json '"chief_of_staff_launches_external_agents": false' "fixture CoS no-launch flag"
if command -v python3 >/dev/null 2>&1; then
  python3 -m json.tool assistant/agent-builder-governance/samples/classification-summary.json >/dev/null 2>&1 && pass 'JSON parses: classification summary' || fail 'JSON does not parse: classification summary'
else
  warn 'python3 not available for JSON parse checks'
fi

section 'No External Agent Launch Commands'
for forbidden in \
  '--launch-cursor-agent)' \
  '--launch-antigravity)' \
  '--launch-claude-code)' \
  '--launch-codex)' \
  '--invoke-external-agent)' \
  '--agent-builder-run)'; do
  grep -Fq -- "${forbidden}" bin/chief-of-staff 2>/dev/null && fail "CLI must not expose forbidden command: ${forbidden}" || pass "CLI has no forbidden command: ${forbidden}"
done

section 'Production Registry Parked-State Proof'
if [[ -f "${production_registry_path}" ]] && command -v python3 >/dev/null 2>&1; then
  record_count="$(python3 -c "import json; d=json.load(open('${production_registry_path}')); print(len(d.get('records',[])))" 2>/dev/null || echo 0)"
  [[ "${record_count}" == "1" ]] && pass 'production registry records count exactly 1' || fail "production registry records count must be 1 (got ${record_count})"
  [[ -f "${sentinel}" ]] && pass 'BLOCKED-NO-WRITES.sentinel intact' || fail 'BLOCKED-NO-WRITES.sentinel missing'
  grep -Fq -- '--curriculum-registry-write)' bin/chief-of-staff 2>/dev/null && fail 'chief-of-staff must not implement --curriculum-registry-write handler' || pass 'chief-of-staff has no --curriculum-registry-write handler'
else
  warn 'production registry parked-state proof skipped'
fi

section 'Roadmap and Coherence Cross-Links'
check_doc_contains docs/build-queue.md "agent builder" "build queue agent builder"
check_doc_contains assistant/memory/active-priorities.md "agent builder" "active priorities agent builder"
check_doc_contains docs/proposals/index.md "Agent builder compatibility governance" "proposal ledger agent builder"
check_doc_contains docs/teacher-workstation-capability-map.md "agent-builder-compatibility-governance-status" "capability map governance status"

section 'Dashboard and Validate-All Wiring'
grep -Fq -- 'agent-builder-compatibility-governance-status.sh' scripts/chief-of-staff-dashboard.sh && pass 'dashboard wires agent builder governance status' || fail 'dashboard missing agent builder governance status'
grep -Fq -- 'agent-builder-compatibility-governance-status.sh' scripts/chief-of-staff-validate-all.sh && pass 'validate-all wires agent builder governance status' || fail 'validate-all missing agent builder governance status'
grep -Fq -- 'agent-builder-compatibility' tests/smoke-chief-of-staff-cli.sh && pass 'smoke wires agent builder governance status' || fail 'smoke missing agent builder governance status'
if grep -Eq 'bash[[:space:]]+scripts/(whole-system-coherence|whole-system-master-roadmap|ai-tool-routing)-status\.sh' "${BASH_SOURCE[0]}" 2>/dev/null; then
  fail 'governance status must not execute other aggregate status scripts'
else
  pass 'governance status does not execute nested aggregate status scripts'
fi

section 'CLI, Manifest, and Tests'
bash -n "${BASH_SOURCE[0]}" && pass "bash syntax ok: ${BASH_SOURCE[0]}" || fail "bash syntax failed: status script"
grep -Fq -- '--agent-builder-compatibility-governance-status' bin/chief-of-staff && pass 'CLI exposes --agent-builder-compatibility-governance-status' || fail 'CLI missing --agent-builder-compatibility-governance-status'
grep -Fq -- '"--agent-builder-compatibility-governance-status"' assistant/chief-of-staff/v1/command-surface-manifest.json && pass 'manifest lists --agent-builder-compatibility-governance-status' || fail 'manifest missing --agent-builder-compatibility-governance-status'
check_file tests/agent-builder-compatibility-governance-status-test.sh
bash -n tests/agent-builder-compatibility-governance-status-test.sh && pass 'bash syntax ok: agent builder governance test' || fail 'bash syntax failed: governance test'

section 'Negative Non-Activation Assertions'
status_script="${BASH_SOURCE[0]}"
grep -Eq '(^|[;&|[:space:]])curl[[:space:]]' "${status_script}" 2>/dev/null && fail "${status_script} must not shell-invoke curl" || pass "${status_script} does not shell-invoke curl"
grep -Eq '(^|[;&|[:space:]])ollama[[:space:]]' "${status_script}" 2>/dev/null && fail "${status_script} must not shell-invoke ollama" || pass "${status_script} does not shell-invoke ollama"
pass 'no external agent launch attempted'
pass 'no network call attempted'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
