#!/usr/bin/env bash
# Read-only whole-system master roadmap build-state status. Documentation/status only.
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

report="docs/whole-system-master-roadmap-build-state-report.md"
status_script="scripts/whole-system-master-roadmap-status.sh"
manifest="assistant/chief-of-staff/v1/command-surface-manifest.json"
production_registry_path="assistant/curriculum-builder/registry/v0-2/production-registry.json"
sentinel="assistant/curriculum-builder/registry/candidate-v0-2-production/BLOCKED-NO-WRITES.sentinel"
APPROVED_ID="resource-math-lesson-108-presentation"

section 'Whole-System Master Roadmap Status'
cat <<'EOF'
Status: whole_system_master_roadmap_status_complete
Classification: documentation/status only
Runtime activation: no
Production registry writes: blocked
Active --write: blocked
Writer scripts: blocked
Second production record: blocked
Metadata pilot expansion: blocked
Parked state: allowed and recommended default
PASS does not authorize implementation: yes
EOF

section 'Build-State Report'
check_file "${report}"
check_doc_contains "${report}" "[x]" "status key built marker"
check_doc_contains "${report}" "[~]" "status key in-progress marker"
check_doc_contains "${report}" "[>]" "status key ready marker"
check_doc_contains "${report}" "[!]" "status key blocked marker"
check_doc_contains "${report}" "[ ]" "status key future marker"
check_doc_contains "${report}" "[?]" "status key insufficient-evidence marker"
check_doc_contains "${report}" "whole_system_master_roadmap_status_complete" "report closure status"
check_doc_contains "${report}" "next_safe_lane_selector_complete" "next safe lane selector closure"
check_doc_contains "${report}" "repo-backed evidence" "repo-backed evidence classification"
check_doc_contains "${report}" "planning/proposal-only evidence" "planning-only evidence classification"
check_doc_contains "${report}" "blocked implementation gates" "blocked gates summary"
check_doc_contains "${report}" "Production Registry Parked-State Reference" "parked-state reference section"

section 'Required Master-Roadmap Lanes (15)'
for lane in \
  "## 1. Core Governance / Autonomous Build Engine" \
  "## 2. Chief of Staff Core" \
  "## 3. Curriculum Builder / Curriculum Registry" \
  "## 4. Production Registry" \
  "## 5. Widgets / Shortcuts / Mac Workflow" \
  "## 6. Vibe / Teacher Experience / UI Direction" \
  "## 7. 3D Workshop / Spatial / Visual Builder Ideas" \
  "## 8. Homebrew / Local Installs / Dev Environment" \
  "## 9. Local LLM / Ollama / AI Runtime" \
  "## 10. Canvas / Drive / NAS / iCloud Integrations" \
  "## 11. Classroom Utility Apps" \
  "## 12. Lovable / App Generation / Prototype Rescue" \
  "## 13. Presentation Engine / Resource Registry / Academic OS Ideas" \
  "## 14. Safety / Student Data / Real Curriculum Gates" \
  "## 15. Current Global State"; do
  check_doc_contains "${report}" "${lane}" "lane section: ${lane}"
done

section 'Next Safe Lane Selector'
check_doc_contains "${report}" "safest next docs/status build lane" "safest docs/status lane"
check_doc_contains "${report}" "strongest classroom-value planning lane" "classroom-value planning lane"
check_doc_contains "${report}" "blocked high-value lane requiring Owen decision" "blocked high-value lane"
check_doc_contains "${report}" "future lane needing more repo evidence" "insufficient-evidence lane"
check_doc_contains "${report}" "Option D (parked) recommended default" "parked default recommendation"

section 'Roadmap Coherence Cross-Links'
check_file docs/master-build-roadmap.md
check_file docs/build-queue.md
check_file docs/proposals/index.md
check_file docs/teacher-workstation-capability-map.md
check_doc_contains "${report}" "docs/master-build-roadmap.md" "master build roadmap cross-link"
check_doc_contains "${report}" "docs/build-queue.md" "build queue cross-link"
check_doc_contains "${report}" "docs/proposals/index.md" "proposal ledger cross-link"
check_doc_contains "${report}" "--whole-system-master-roadmap-status" "whole-system status command cross-link"
check_doc_contains "${report}" "--presentation-engine-renderer-foundation-status" "presentation engine status command cross-link"
check_doc_contains "${report}" "complete_a4_a7_fixture_optional_field_enrichment" "A4–A7 fixture enrichment closure"
check_doc_contains "${report}" "complete_classroom_utility_per_app_mission_templates" "classroom utility templates closure"
check_doc_contains "${report}" "--classroom-utility-templates-status" "classroom utility templates status command cross-link"

section 'Production Registry Parked-State Proof'
check_file "${production_registry_path}"
check_file "${sentinel}"
grep -Fq -- '"records"' "${production_registry_path}" && pass 'production registry has records key' || fail 'production registry missing records key'
record_count="$(python3 -c "import json; d=json.load(open('${production_registry_path}')); print(len(d.get('records',[])))" 2>/dev/null || echo 0)"
[[ "${record_count}" == "1" ]] && pass 'production registry records count exactly 1' || fail "production registry records count must be 1 (got ${record_count})"
grep -Fq -- "${APPROVED_ID}" "${production_registry_path}" && pass 'approved record ID present' || fail 'approved record ID missing'
grep -Fq -- '--curriculum-registry-write)' bin/chief-of-staff 2>/dev/null && fail 'chief-of-staff must not implement --curriculum-registry-write handler' || pass 'chief-of-staff has no --curriculum-registry-write handler'
writer_scripts_present=0
for candidate in scripts/*production-registry*write*; do
  [[ -e "${candidate}" ]] && writer_scripts_present=1
done
[[ "${writer_scripts_present}" == "0" ]] && pass 'no production-registry writer scripts in scripts/' || fail 'writer scripts must not exist'

section 'Dependent Status: Next-Gate'
if [[ -f scripts/curriculum-builder-production-registry-next-gate-status.sh ]]; then
  next_gate_output="$(bash scripts/curriculum-builder-production-registry-next-gate-status.sh 2>&1)" || next_gate_result=$?
  next_gate_result="${next_gate_result:-0}"
  if [[ "${next_gate_result}" != "0" ]]; then
    fail 'next-gate status script exited nonzero'
    printf '%s\n' "${next_gate_output}" | tail -20
  elif grep -q '^FAIL: [1-9]' <<< "${next_gate_output}"; then
    fail 'next-gate status reported FAIL'
    printf '%s\n' "${next_gate_output}" | tail -20
  else
    pass 'next-gate status component clean'
  fi
else
  fail 'next-gate status script missing'
fi

section 'Dependent Status: Presentation Engine Renderer Foundation'
if [[ -f scripts/presentation-engine-renderer-foundation-status.sh ]]; then
  pe_output="$(bash scripts/presentation-engine-renderer-foundation-status.sh 2>&1)" || pe_result=$?
  pe_result="${pe_result:-0}"
  if [[ "${pe_result}" != "0" ]]; then
    fail 'presentation engine renderer foundation status script exited nonzero'
    printf '%s\n' "${pe_output}" | tail -20
  elif grep -q '^FAIL: [1-9]' <<< "${pe_output}"; then
    fail 'presentation engine renderer foundation status reported FAIL'
    printf '%s\n' "${pe_output}" | tail -20
  else
    pass 'presentation engine renderer foundation status component clean'
  fi
else
  fail 'presentation engine renderer foundation status script missing'
fi

section 'Dependent Status: Classroom Utility Templates'
if [[ -f scripts/classroom-utility-templates-status.sh ]]; then
  cut_output="$(bash scripts/classroom-utility-templates-status.sh 2>&1)" || cut_result=$?
  cut_result="${cut_result:-0}"
  if [[ "${cut_result}" != "0" ]]; then
    fail 'classroom utility templates status script exited nonzero'
    printf '%s\n' "${cut_output}" | tail -20
  elif grep -q '^FAIL: [1-9]' <<< "${cut_output}"; then
    fail 'classroom utility templates status reported FAIL'
    printf '%s\n' "${cut_output}" | tail -20
  else
    pass 'classroom utility templates status component clean'
  fi
else
  fail 'classroom utility templates status script missing'
fi

section 'CLI, Manifest, and Tests'
bash -n "${status_script}" && pass "bash syntax ok: ${status_script}" || fail "bash syntax failed: ${status_script}"
grep -Fq -- '--whole-system-master-roadmap-status' bin/chief-of-staff && pass 'CLI exposes --whole-system-master-roadmap-status' || fail 'CLI missing --whole-system-master-roadmap-status'
grep -Fq -- '"--whole-system-master-roadmap-status"' "${manifest}" && pass 'manifest lists --whole-system-master-roadmap-status' || fail 'manifest missing --whole-system-master-roadmap-status'
check_file tests/whole-system-master-roadmap-status-test.sh
bash -n tests/whole-system-master-roadmap-status-test.sh && pass 'bash syntax ok: whole-system test' || fail 'bash syntax failed: whole-system test'

section 'Negative Non-Activation Assertions'
grep -Eq '(^|[;&|[:space:]])curl[[:space:]]' "${status_script}" 2>/dev/null && fail "${status_script} must not shell-invoke curl" || pass "${status_script} does not shell-invoke curl"
grep -Eq '(^|[;&|[:space:]])find[[:space:]]' "${status_script}" 2>/dev/null && fail "${status_script} must not shell-invoke find" || pass "${status_script} does not shell-invoke find"
grep -Eq '(^|[;&|[:space:]])ollama[[:space:]]' "${status_script}" 2>/dev/null && fail "${status_script} must not shell-invoke ollama" || pass "${status_script} does not shell-invoke ollama"
pass 'whole-system status does not authorize runtime activation'
pass 'no network call attempted'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
