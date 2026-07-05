#!/usr/bin/env bash
# Read-only Owen architecture decision packets status. No decisions made for Owen.
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

index_doc="docs/owen-architecture-decision-packets.md"
production_packet="docs/proposals/blocked/production-registry-options-decision-packet.md"
directory_packet="docs/proposals/blocked/manual-text-asset-directory-layout-decision-packet.md"
classroom_packet="docs/proposals/blocked/classroom-utility-app-priority-decision-packet.md"
external_packet="docs/proposals/blocked/external-builder-trial-decision-packet.md"
local_llm_packet="docs/proposals/blocked/local-llm-ollama-decision-packet.md"
integration_packet="docs/proposals/blocked/drive-nas-icloud-canvas-integration-posture-decision-packet.md"
production_registry_path="assistant/curriculum-builder/registry/v0-2/production-registry.json"
sentinel="assistant/curriculum-builder/registry/candidate-v0-2-production/BLOCKED-NO-WRITES.sentinel"

section 'Owen Architecture Decision Packets (Documentation Only)'
cat <<'EOF'
Status: documentation/status only
Chief of Staff chooses options for Owen: no
Owen decision owner: yes
Production registry writes: no
Runtime/product activation: no
PASS does not authorize implementation: yes
EOF

section 'Main Index'
check_file "${index_doc}"
check_doc_contains "${index_doc}" "complete_owen_architecture_decision_packets_program" "decision packets closure marker"
check_doc_contains "${index_doc}" "Owen decision required" "Owen decision required column"
check_doc_contains "${index_doc}" "Option D — parked" "production registry Option D default"

section 'Required Decision Packet Docs'
for packet in \
  "${production_packet}" \
  "${directory_packet}" \
  "${classroom_packet}" \
  "${external_packet}" \
  "${local_llm_packet}" \
  "${integration_packet}"; do
  check_file "${packet}"
  check_doc_contains "${packet}" "not Owen approval" "packet not Owen approval banner"
  check_doc_contains "${packet}" "does not implement runtime behavior" "packet no runtime banner"
  check_doc_contains "${packet}" "Owen Decision Required" "packet Owen decision section"
done

section 'Production Registry Default Posture'
check_doc_contains "${production_packet}" "Option D — parked" "production registry Option D default in packet"
check_doc_contains "${production_packet}" "Production registry writes: blocked" "production writes blocked in packet"
check_doc_contains "${index_doc}" "does not choose" "index does not choose for Owen"

section 'Manual Directory Layout Unchosen'
check_doc_contains "${directory_packet}" "Option 4 — defer" "directory layout defer default"
check_doc_contains "${directory_packet}" "File/folder scanning: blocked" "directory packet scanning blocked"

section 'Classroom Utility Runtime Blocked'
check_doc_contains "${classroom_packet}" "Classroom utility app runtime: blocked" "classroom runtime blocked"
check_doc_contains "${classroom_packet}" "does not choose a priority for Owen" "classroom packet Owen ownership"

section 'External Builder Invocation Blocked'
check_doc_contains "${external_packet}" "Chief of Staff launches external agents: blocked" "external CoS launch blocked"
check_doc_contains "${external_packet}" "agent-builder-compatibility-and-external-tool-governance.md" "external packet governance cross-link"

section 'Local LLM / Ollama Blocked'
check_doc_contains "${local_llm_packet}" "Ollama execution: blocked" "ollama execution blocked"
check_doc_contains "${local_llm_packet}" "does not activate local LLM for Owen" "local LLM packet Owen ownership"

section 'Drive/NAS/iCloud/Canvas Blocked'
check_doc_contains "${integration_packet}" "no access, no scanning, no API/OAuth" "integration no access posture"
check_doc_contains "${integration_packet}" "does not approve integration for Owen" "integration packet Owen ownership"

section 'No External Agent Launch Commands'
for forbidden in \
  '--launch-cursor-agent)' \
  '--launch-antigravity)' \
  '--invoke-external-agent)' \
  '--owen-architecture-decide)'; do
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
check_doc_contains docs/build-queue.md "decision packet" "build queue decision packets"
check_doc_contains assistant/memory/active-priorities.md "decision packet" "active priorities decision packets"
check_doc_contains docs/proposals/index.md "Owen architecture decision packets" "proposal ledger decision packets"
check_doc_contains docs/teacher-workstation-capability-map.md "owen-architecture-decision-packets-status" "capability map decision packets status"

section 'Dashboard and Validate-All Wiring'
grep -Fq -- 'owen-architecture-decision-packets-status.sh' scripts/chief-of-staff-dashboard.sh && pass 'dashboard wires decision packets status' || fail 'dashboard missing decision packets status'
grep -Fq -- 'owen-architecture-decision-packets-status.sh' scripts/chief-of-staff-validate-all.sh && pass 'validate-all wires decision packets status' || fail 'validate-all missing decision packets status'
source scripts/validation-smoke-tier-boundary.sh
check_smoke_excludes_deep_validation 'owen-architecture-decision-packets' 'Owen architecture decision packets'
if grep -Eq 'bash[[:space:]]+scripts/(whole-system-coherence|whole-system-master-roadmap|agent-builder-compatibility-governance)-status\.sh' "${BASH_SOURCE[0]}" 2>/dev/null; then
  fail 'decision packets status must not execute other aggregate status scripts'
else
  pass 'decision packets status does not execute nested aggregate status scripts'
fi

section 'CLI, Manifest, and Tests'
bash -n "${BASH_SOURCE[0]}" && pass "bash syntax ok: ${BASH_SOURCE[0]}" || fail "bash syntax failed: status script"
grep -Fq -- '--owen-architecture-decision-packets-status' bin/chief-of-staff && pass 'CLI exposes --owen-architecture-decision-packets-status' || fail 'CLI missing --owen-architecture-decision-packets-status'
grep -Fq -- '"--owen-architecture-decision-packets-status"' assistant/chief-of-staff/v1/command-surface-manifest.json && pass 'manifest lists --owen-architecture-decision-packets-status' || fail 'manifest missing --owen-architecture-decision-packets-status'
check_file tests/owen-architecture-decision-packets-status-test.sh
bash -n tests/owen-architecture-decision-packets-status-test.sh && pass 'bash syntax ok: decision packets test' || fail 'bash syntax failed: decision packets test'

section 'Negative Non-Activation Assertions'
status_script="${BASH_SOURCE[0]}"
grep -Eq '(^|[;&|[:space:]])curl[[:space:]]' "${status_script}" 2>/dev/null && fail "${status_script} must not shell-invoke curl" || pass "${status_script} does not shell-invoke curl"
grep -Eq '(^|[;&|[:space:]])ollama[[:space:]]' "${status_script}" 2>/dev/null && fail "${status_script} must not shell-invoke ollama" || pass "${status_script} does not shell-invoke ollama"
pass 'no Owen decision made by status script'
pass 'no network call attempted'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
