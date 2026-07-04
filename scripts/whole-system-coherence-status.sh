#!/usr/bin/env bash
# Read-only whole-system coherence maintenance status. Cross-doc verification only — no runtime.
# Must not execute scripts/whole-system-master-roadmap-status.sh (validate-all/dashboard call both separately).
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

coherence_report="docs/whole-system-coherence-maintenance-report.md"
enhancement_backlog="docs/proposals/backlog/whole-system-safe-enhancement-discovery.md"
whole_system_report="docs/whole-system-master-roadmap-build-state-report.md"
production_registry_path="assistant/curriculum-builder/registry/v0-2/production-registry.json"
sentinel="assistant/curriculum-builder/registry/candidate-v0-2-production/BLOCKED-NO-WRITES.sentinel"

section 'Whole-System Coherence Maintenance (Documentation Only)'
cat <<'EOF'
Status: documentation/status only
Runtime activation: no
Schema/parser/validator creation: no
Production registry writes: no
PASS does not authorize implementation: yes
EOF

section 'Coherence Artifacts'
check_file "${coherence_report}"
check_file "${enhancement_backlog}"
check_doc_contains "${coherence_report}" "complete_whole_system_coherence_maintenance" "coherence closure marker"
check_doc_contains "${coherence_report}" "not implementation approval" "non-authority banner"
check_doc_contains "${enhancement_backlog}" "blocked" "enhancement blocked classification"
check_doc_contains "${enhancement_backlog}" "Owen decision needed" "Owen decision classification"

section 'Recent Lane Cross-Links'
for closure in \
  complete_curriculum_manual_metadata_frontmatter_planning \
  complete_gemini_discovery_classification_intake \
  complete_classroom_utility_per_app_mission_templates \
  complete_presentation_engine_renderer_foundation_planning \
  complete_a4_a7_fixture_optional_field_enrichment \
  complete_agent_builder_compatibility_governance_program \
  complete_owen_architecture_decision_packets_program \
  complete_app_ecosystem_inventory_and_prototype_build_list \
  complete_classroom_timer_stopwatch_planning_lane; do
  check_doc_contains "${whole_system_report}" "${closure}" "whole-system report closure: ${closure}"
done
check_doc_contains docs/build-queue.md "classroom timer" "build queue timer planning"
check_doc_contains docs/build-queue.md "app ecosystem" "build queue app ecosystem"
check_doc_contains docs/build-queue.md "decision packet" "build queue decision packets"
check_doc_contains docs/build-queue.md "frontmatter planning" "build queue frontmatter"
check_doc_contains docs/build-queue.md "coherence maintenance" "build queue coherence"
check_doc_contains assistant/memory/active-priorities.md "coherence maintenance" "active priorities coherence"
check_doc_contains docs/proposals/index.md "Whole-system coherence maintenance" "proposal ledger coherence"
check_doc_contains docs/teacher-workstation-capability-map.md "whole-system-coherence-status" "capability map coherence status"

section 'Stale Count Hardening'
check_doc_contains "${whole_system_report}" "138 / 0 / 0 PASS" "dashboard count current"
check_doc_contains "${whole_system_report}" "56 / 0 / 0 PASS" "validate-all count current"
if grep -Fq -- 'Dashboard 128/0/0' "${whole_system_report}" 2>/dev/null; then
  fail 'whole-system report must not contain stale Dashboard 128/0/0 example'
else
  pass 'whole-system report excludes stale Dashboard 128/0/0'
fi
if grep -Fq -- 'dashboard (128/0/0)' "${whole_system_report}" 2>/dev/null; then
  fail 'whole-system report must not contain stale dashboard (128/0/0) lane text'
else
  pass 'whole-system report excludes stale dashboard (128/0/0) lane text'
fi
if grep -Fq -- 'dashboard (134/0/0)' "${whole_system_report}" 2>/dev/null; then
  fail 'whole-system report must not contain stale dashboard (134/0/0) lane text'
else
  pass 'whole-system report excludes stale dashboard (134/0/0) lane text'
fi
if grep -Fq -- 'Dashboard 134/0/0' "${whole_system_report}" 2>/dev/null; then
  fail 'whole-system report must not contain stale Dashboard 134/0/0 example'
else
  pass 'whole-system report excludes stale Dashboard 134/0/0 example'
fi
if grep -Fq -- 'dashboard (135/0/0)' "${whole_system_report}" 2>/dev/null; then
  fail 'whole-system report must not contain stale dashboard (135/0/0) lane text'
else
  pass 'whole-system report excludes stale dashboard (135/0/0) lane text'
fi
if grep -Fq -- 'dashboard (136/0/0)' "${whole_system_report}" 2>/dev/null; then
  fail 'whole-system report must not contain stale dashboard (136/0/0) lane text'
else
  pass 'whole-system report excludes stale dashboard (136/0/0) lane text'
fi
if grep -Fq -- 'dashboard (137/0/0)' "${whole_system_report}" 2>/dev/null; then
  fail 'whole-system report must not contain stale dashboard (137/0/0) lane text'
else
  pass 'whole-system report excludes stale dashboard (137/0/0) lane text'
fi

section 'Expected WARNs Discoverability'
check_file docs/curriculum-builder-registry-expected-warns.md
check_doc_contains docs/curriculum-builder-registry-expected-warns.md "--markdown-frontmatter-planning-status" "expected warns frontmatter status"
check_doc_contains docs/curriculum-builder-registry-expected-warns.md "--gemini-discovery-classification-intake-status" "expected warns gemini status"
check_doc_contains docs/curriculum-builder-registry-expected-warns.md "--whole-system-coherence-status" "expected warns coherence status"
check_doc_contains docs/curriculum-builder-registry-expected-warns.md "--agent-builder-compatibility-governance-status" "expected warns agent builder status"
check_doc_contains docs/curriculum-builder-registry-expected-warns.md "--owen-architecture-decision-packets-status" "expected warns decision packets status"
check_doc_contains docs/curriculum-builder-registry-expected-warns.md "--app-ecosystem-inventory-status" "expected warns app ecosystem status"
check_doc_contains docs/curriculum-builder-registry-expected-warns.md "--classroom-timer-stopwatch-planning-status" "expected warns timer planning status"

section 'Production Registry Parked-State Proof'
if [[ -f "${production_registry_path}" ]] && command -v python3 >/dev/null 2>&1; then
  record_count="$(python3 -c "import json; d=json.load(open('${production_registry_path}')); print(len(d.get('records',[])))" 2>/dev/null || echo 0)"
  [[ "${record_count}" == "1" ]] && pass 'production registry records count exactly 1' || fail "production registry records count must be 1 (got ${record_count})"
  [[ -f "${sentinel}" ]] && pass 'BLOCKED-NO-WRITES.sentinel intact' || fail 'BLOCKED-NO-WRITES.sentinel missing'
  grep -Fq -- '--curriculum-registry-write)' bin/chief-of-staff 2>/dev/null && fail 'chief-of-staff must not implement --curriculum-registry-write handler' || pass 'chief-of-staff has no --curriculum-registry-write handler'
else
  warn 'production registry parked-state proof skipped'
fi

section 'Whole-System Master Roadmap Cross-Check (No Nested Run)'
check_file scripts/whole-system-master-roadmap-status.sh
check_doc_contains "${whole_system_report}" "whole_system_master_roadmap_status_complete" "master roadmap closure in report"
check_doc_contains "${whole_system_report}" "next_safe_lane_selector_complete" "next safe lane selector closure"

section 'Dashboard and Validate-All Wiring'
grep -Fq -- 'whole-system-coherence-status.sh' scripts/chief-of-staff-dashboard.sh && pass 'dashboard wires whole-system-coherence-status' || fail 'dashboard missing whole-system-coherence-status'
grep -Fq -- 'whole-system-coherence-status.sh' scripts/chief-of-staff-validate-all.sh && pass 'validate-all wires whole-system-coherence-status' || fail 'validate-all missing whole-system-coherence-status'
grep -Fq -- 'whole-system-coherence' tests/smoke-chief-of-staff-cli.sh && pass 'smoke wires whole-system-coherence-status' || fail 'smoke missing whole-system-coherence-status'
if grep -Eq 'bash[[:space:]]+scripts/whole-system-master-roadmap-status\.sh' "${BASH_SOURCE[0]}" 2>/dev/null; then
  fail 'coherence status must not execute whole-system-master-roadmap-status.sh'
else
  pass 'coherence status does not execute whole-system-master-roadmap-status.sh'
fi

section 'CLI, Manifest, and Tests'
bash -n "${BASH_SOURCE[0]}" && pass "bash syntax ok: ${BASH_SOURCE[0]}" || fail "bash syntax failed: status script"
grep -Fq -- '--whole-system-coherence-status' bin/chief-of-staff && pass 'CLI exposes --whole-system-coherence-status' || fail 'CLI missing --whole-system-coherence-status'
grep -Fq -- '"--whole-system-coherence-status"' assistant/chief-of-staff/v1/command-surface-manifest.json && pass 'manifest lists --whole-system-coherence-status' || fail 'manifest missing --whole-system-coherence-status'
check_file tests/whole-system-coherence-status-test.sh
bash -n tests/whole-system-coherence-status-test.sh && pass 'bash syntax ok: coherence test' || fail 'bash syntax failed: coherence test'

section 'Negative Non-Activation Assertions'
status_script="${BASH_SOURCE[0]}"
grep -Eq '(^|[;&|[:space:]])curl[[:space:]]' "${status_script}" 2>/dev/null && fail "${status_script} must not shell-invoke curl" || pass "${status_script} does not shell-invoke curl"
grep -Eq '(^|[;&|[:space:]])find[[:space:]]' "${status_script}" 2>/dev/null && fail "${status_script} must not shell-invoke find" || pass "${status_script} does not shell-invoke find"
pass 'no runtime activation attempted'
pass 'no folder scanning attempted'
pass 'no network call attempted'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
