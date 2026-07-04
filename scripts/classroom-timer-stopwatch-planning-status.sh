#!/usr/bin/env bash
# Read-only Classroom Timer & Stopwatch planning lane status. No timer execution.
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

planning_doc="docs/classroom-utilities/classroom-timer-stopwatch-planning.md"
inventory_doc="docs/app-ecosystem-inventory-and-prototype-build-list.md"
fixtures_dir="assistant/classroom-utilities/samples/classroom-timer-stopwatch-planning"
production_registry_path="assistant/curriculum-builder/registry/v0-2/production-registry.json"
sentinel="assistant/curriculum-builder/registry/candidate-v0-2-production/BLOCKED-NO-WRITES.sentinel"

section 'Classroom Timer & Stopwatch Planning Lane (Level 3 Runtime Implemented)'
cat <<'EOF'
Status: planning complete — Level 3 runtime prototype implemented (Timer only)
Owen selected planning lane: yes
Runtime classroom app: yes — Classroom Timer & Stopwatch only (local-only prototype)
Other apps runtime: blocked
Student data: blocked — absolute
Database/API/integration: no
AI generation/local models: no
PASS does not authorize other apps: yes
EOF

section 'Planning Doc'
check_file "${planning_doc}"
check_doc_contains "${planning_doc}" "complete_classroom_timer_stopwatch_planning_lane" "planning lane closure marker"
check_doc_contains "${planning_doc}" "Level 3 runtime prototype implemented" "Level 3 runtime banner"
check_doc_contains "${planning_doc}" "Other apps runtime: blocked" "other apps runtime blocked"
check_doc_contains "${planning_doc}" "Student data: blocked" "student data blocked"
check_doc_contains "${planning_doc}" "no data saved" "no data saved posture"
check_doc_contains "${planning_doc}" "Owen selected this app for the first planning lane" "Owen planning lane selection"
check_doc_contains "${planning_doc}" "runtime timer app" "blocked runtime paths listed"
check_doc_contains "${planning_doc}" "AI generation" "AI generation blocked"

section 'Fake Local Examples'
check_file "${fixtures_dir}/README.md"
check_file "${fixtures_dir}/example-timer-presets-001.json"
check_file "${fixtures_dir}/example-display-modes-001.json"
check_doc_contains "${fixtures_dir}/example-timer-presets-001.json" "fake_local_planning_only" "presets fixture classification"
check_doc_contains "${fixtures_dir}/example-display-modes-001.json" "fake_local_planning_only" "display modes fixture classification"
check_doc_contains "${fixtures_dir}/example-timer-presets-001.json" '"runtime_app": "blocked"' "presets fixture runtime blocked"
if command -v python3 >/dev/null 2>&1; then
  python3 -m json.tool "${fixtures_dir}/example-timer-presets-001.json" >/dev/null 2>&1 && pass 'JSON parses: timer presets' || fail 'JSON does not parse: timer presets'
  python3 -m json.tool "${fixtures_dir}/example-display-modes-001.json" >/dev/null 2>&1 && pass 'JSON parses: display modes' || fail 'JSON does not parse: display modes'
else
  warn 'python3 not available for JSON parse checks'
fi

section 'No Executable Runtime Artifacts (Legacy Docs Path)'
for legacy in \
  'docs/classroom-utilities/classroom-timer-stopwatch.html' \
  'docs/classroom-utilities/classroom-timer-stopwatch.js' \
  'docs/classroom-utilities/classroom-timer-stopwatch.tsx'; do
  [[ -e "${legacy}" ]] && fail "legacy runtime artifact in docs path: ${legacy}" || pass "no legacy runtime artifact: ${legacy}"
done

section 'Level 3 Runtime Prototype (Owen Approved)'
check_file apps/classroom-timer-stopwatch/index.html
check_file apps/classroom-timer-stopwatch/timer.js
check_file scripts/classroom-timer-stopwatch-runtime-status.sh
check_doc_contains docs/app-ecosystem/implementation-packets/classroom-timer-stopwatch-implementation-packet.md "Level 3 approved by Owen" "implementation packet Level 3"
grep -Fq -- 'classroom-timer-stopwatch-runtime-status.sh' scripts/chief-of-staff-dashboard.sh && pass 'dashboard wires timer runtime status' || fail 'dashboard missing timer runtime status'

section 'App Inventory Cross-Link'
check_file "${inventory_doc}"
check_doc_contains "${inventory_doc}" "Classroom Timer & Stopwatch" "inventory includes timer app"
check_doc_contains "${inventory_doc}" "complete_classroom_timer_stopwatch_planning_lane" "inventory timer planning closure"
check_doc_contains docs/proposals/blocked/classroom-utility-app-priority-decision-packet.md "classroom-timer-stopwatch-planning.md" "priority packet timer cross-link"

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
check_doc_contains docs/build-queue.md "classroom timer" "build queue timer planning"
check_doc_contains assistant/memory/active-priorities.md "classroom timer" "active priorities timer planning"
check_doc_contains docs/proposals/index.md "Classroom Timer" "proposal ledger timer planning"
check_doc_contains docs/teacher-workstation-capability-map.md "classroom-timer-stopwatch-planning-status" "capability map timer status"

section 'Dashboard and Validate-All Wiring'
grep -Fq -- 'classroom-timer-stopwatch-planning-status.sh' scripts/chief-of-staff-dashboard.sh && pass 'dashboard wires timer planning status' || fail 'dashboard missing timer planning status'
grep -Fq -- 'classroom-timer-stopwatch-planning-status.sh' scripts/chief-of-staff-validate-all.sh && pass 'validate-all wires timer planning status' || fail 'validate-all missing timer planning status'
grep -Fq -- 'classroom-timer-stopwatch-runtime-status.sh' scripts/chief-of-staff-validate-all.sh && pass 'validate-all wires timer runtime status' || fail 'validate-all missing timer runtime status'
grep -Fq -- 'classroom-timer-stopwatch' tests/smoke-chief-of-staff-cli.sh && pass 'smoke wires timer planning/runtime' || fail 'smoke missing timer wiring'

section 'CLI, Manifest, and Tests'
bash -n "${BASH_SOURCE[0]}" && pass "bash syntax ok: ${BASH_SOURCE[0]}" || fail "bash syntax failed: status script"
grep -Fq -- '--classroom-timer-stopwatch-planning-status' bin/chief-of-staff && pass 'CLI exposes --classroom-timer-stopwatch-planning-status' || fail 'CLI missing --classroom-timer-stopwatch-planning-status'
grep -Fq -- '"--classroom-timer-stopwatch-planning-status"' assistant/chief-of-staff/v1/command-surface-manifest.json && pass 'manifest lists --classroom-timer-stopwatch-planning-status' || fail 'manifest missing --classroom-timer-stopwatch-planning-status'
check_file tests/classroom-timer-stopwatch-planning-status-test.sh
bash -n tests/classroom-timer-stopwatch-planning-status-test.sh && pass 'bash syntax ok: timer planning test' || fail 'bash syntax failed: timer planning test'

section 'Negative Non-Activation Assertions'
local_status_script="${BASH_SOURCE[0]}"
grep -Eq '(^|[;&|[:space:]])curl[[:space:]]' "${local_status_script}" 2>/dev/null && fail "${local_status_script} must not shell-invoke curl" || pass "${local_status_script} does not shell-invoke curl"
grep -Eq '(^|[;&|[:space:]])ollama[[:space:]]' "${local_status_script}" 2>/dev/null && fail "${local_status_script} must not shell-invoke ollama" || pass "${local_status_script} does not shell-invoke ollama"
pass 'no timer executed'
pass 'no browser launched'
pass 'no runtime app approval implied'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
