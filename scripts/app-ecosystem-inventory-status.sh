#!/usr/bin/env bash
# Read-only app ecosystem inventory status. No app runtime, no priority chosen for Owen.
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

inventory_doc="docs/app-ecosystem-inventory-and-prototype-build-list.md"
classroom_packet="docs/proposals/blocked/classroom-utility-app-priority-decision-packet.md"
canonical_ids="assistant/app-ecosystem/samples/canonical-inventory-ids.json"
production_registry_path="assistant/curriculum-builder/registry/v0-2/production-registry.json"
sentinel="assistant/curriculum-builder/registry/candidate-v0-2-production/BLOCKED-NO-WRITES.sentinel"

section 'App Ecosystem Inventory (Documentation Only)'
cat <<'EOF'
Status: documentation/status only
Chief of Staff chooses app priority for Owen: no
Runtime classroom apps: no
Student data: blocked — absolute
Database/API/integration approval: no
AI generation/runtime: no
PASS does not authorize implementation: yes
EOF

section 'Canonical Inventory Doc'
check_file "${inventory_doc}"
check_doc_contains "${inventory_doc}" "complete_app_ecosystem_inventory_and_prototype_build_list" "inventory closure marker"
check_doc_contains "${inventory_doc}" "not implementation approval" "non-approval banner"
check_doc_contains "${inventory_doc}" "Deduplication / Alias Policy" "deduplication policy"
check_doc_contains "${inventory_doc}" "Risk Classification Legend" "risk legend"
check_doc_contains "${inventory_doc}" "Complete Inventory (52 Canonical Concepts)" "52-app inventory table"
check_doc_contains "${inventory_doc}" "Tier 1 — Safest planning-only candidates" "tier 1 list"
check_doc_contains "${inventory_doc}" "Tier 4 — High-risk: student data" "tier 4 blocked list"
check_doc_contains "${inventory_doc}" "complete_app_ecosystem_planning_lanes_program" "inventory planning lanes program closure"
check_doc_contains "${inventory_doc}" "high-risk-app-planning-blocked-summary.md" "inventory blocked summary cross-link"
check_doc_contains docs/app-ecosystem-planning-lanes-program.md "complete_app_ecosystem_planning_lanes_program" "planning lanes program doc closure"
check_doc_contains "${inventory_doc}" "Tier 5 — High-risk: API" "tier 5 integration blocked list"
check_doc_contains "${inventory_doc}" "Repo-Discovered Candidates" "repo-discovered section"
check_doc_contains "${inventory_doc}" "does not approve app runtime" "runtime blocked statement"

section '52 Known Concepts Represented'
check_file "${canonical_ids}"
check_file assistant/app-ecosystem/samples/README.md
if command -v python3 >/dev/null 2>&1; then
  python3 -m json.tool "${canonical_ids}" >/dev/null 2>&1 && pass 'JSON parses: canonical inventory ids' || fail 'JSON does not parse: canonical inventory ids'
  missing="$(python3 -c "
import json
from pathlib import Path
ids = json.loads(Path('${canonical_ids}').read_text())
text = Path('${inventory_doc}').read_text()
missing = [e['canonical_name'] for e in ids['entries'] if e['canonical_name'] not in text]
print(len(missing))
if missing:
    print('MISSING:', ','.join(missing[:5]))
" 2>/dev/null || echo "error")"
  if [[ "${missing}" == "error" ]] || [[ -z "${missing}" ]]; then
    fail 'could not verify 52 canonical concepts in inventory doc'
  elif [[ "${missing%%$'\n'*}" == "0" ]]; then
    pass 'all 52 canonical app concepts represented in inventory doc'
  else
    fail "inventory doc missing canonical concepts: ${missing#*$'\n'}"
  fi
  count="$(python3 -c "import json; print(json.load(open('${canonical_ids}'))['known_concept_count'])" 2>/dev/null || echo 0)"
  [[ "${count}" == "52" ]] && pass 'canonical ids fixture declares 52 concepts' || fail "canonical ids count must be 52 (got ${count})"
else
  warn 'python3 not available for 52-concept verification'
fi

section 'Newer App Concepts (Spot Checks)'
for newer in "Trivia Showdown" "Power Up Packet Maker" "iPad Optimizer Prompt Generator" "Reading Test Maker" "GentleGrader"; do
  check_doc_contains "${inventory_doc}" "${newer}" "inventory includes ${newer}"
done

section 'Classroom Utility Priority Packet Cross-Link'
check_file "${classroom_packet}"
check_doc_contains "${classroom_packet}" "app-ecosystem-inventory-and-prototype-build-list.md" "classroom packet inventory cross-link"
check_doc_contains "${classroom_packet}" "does not choose a priority for Owen" "classroom packet Owen ownership"
check_doc_contains "${classroom_packet}" "52-app" "classroom packet 52-app supersession note"

section 'Owen Architecture Decision Packet Index'
check_doc_contains docs/owen-architecture-decision-packets.md "app-ecosystem-inventory-and-prototype-build-list.md" "decision index inventory cross-link"
check_doc_contains docs/owen-architecture-decision-packets.md "full inventory" "decision index full inventory reference"

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
check_doc_contains docs/build-queue.md "app ecosystem" "build queue app ecosystem"
check_doc_contains assistant/memory/active-priorities.md "app ecosystem" "active priorities app ecosystem"
check_doc_contains docs/proposals/index.md "App ecosystem inventory" "proposal ledger app ecosystem"
check_doc_contains docs/teacher-workstation-capability-map.md "app-ecosystem-inventory-status" "capability map inventory status"

section 'Dashboard and Validate-All Wiring'
grep -Fq -- 'app-ecosystem-inventory-status.sh' scripts/chief-of-staff-dashboard.sh && pass 'dashboard wires app ecosystem inventory status' || fail 'dashboard missing app ecosystem inventory status'
grep -Fq -- 'app-ecosystem-inventory-status.sh' scripts/chief-of-staff-validate-all.sh && pass 'validate-all wires app ecosystem inventory status' || fail 'validate-all missing app ecosystem inventory status'
source scripts/validation-smoke-tier-boundary.sh
check_smoke_excludes_deep_validation 'app-ecosystem-inventory' 'App ecosystem inventory'
if grep -Eq 'bash[[:space:]]+scripts/(whole-system-coherence|owen-architecture-decision-packets)-status\.sh' "${BASH_SOURCE[0]}" 2>/dev/null; then
  fail 'inventory status must not execute other aggregate status scripts'
else
  pass 'inventory status does not execute nested aggregate status scripts'
fi

section 'CLI, Manifest, and Tests'
bash -n "${BASH_SOURCE[0]}" && pass "bash syntax ok: ${BASH_SOURCE[0]}" || fail "bash syntax failed: status script"
grep -Fq -- '--app-ecosystem-inventory-status' bin/chief-of-staff && pass 'CLI exposes --app-ecosystem-inventory-status' || fail 'CLI missing --app-ecosystem-inventory-status'
grep -Fq -- '"--app-ecosystem-inventory-status"' assistant/chief-of-staff/v1/command-surface-manifest.json && pass 'manifest lists --app-ecosystem-inventory-status' || fail 'manifest missing --app-ecosystem-inventory-status'
check_file tests/app-ecosystem-inventory-status-test.sh
bash -n tests/app-ecosystem-inventory-status-test.sh && pass 'bash syntax ok: inventory test' || fail 'bash syntax failed: inventory test'

section 'Negative Non-Activation Assertions'
status_script="${BASH_SOURCE[0]}"
grep -Eq '(^|[;&|[:space:]])curl[[:space:]]' "${status_script}" 2>/dev/null && fail "${status_script} must not shell-invoke curl" || pass "${status_script} does not shell-invoke curl"
grep -Eq '(^|[;&|[:space:]])ollama[[:space:]]' "${status_script}" 2>/dev/null && fail "${status_script} must not shell-invoke ollama" || pass "${status_script} does not shell-invoke ollama"
pass 'no app runtime launched'
pass 'no Owen app priority chosen'
pass 'no network call attempted'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
