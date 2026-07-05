#!/usr/bin/env bash
# Read-only app runtime approval gate status. No app runtime. No writes.
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

gate_doc="docs/app-ecosystem/runtime-implementation-approval-gate.md"
checklist_doc="docs/app-ecosystem/runtime-app-boundary-checklist.md"
matrix_doc="docs/app-ecosystem/app-production-readiness-matrix.md"
program_doc="docs/app-runtime-approval-gate-program.md"
manifest_path="assistant/app-ecosystem/samples/runtime-approval-manifest.json"
planning_program="docs/app-ecosystem-planning-lanes-program.md"
planning_manifest="assistant/app-ecosystem/samples/planning-lanes-manifest.json"
blocked_summary="docs/proposals/blocked/high-risk-app-planning-blocked-summary.md"
timer_candidate="docs/app-ecosystem/implementation-packets/classroom-timer-stopwatch-runtime-approval-packet.md"
production_registry_path="assistant/curriculum-builder/registry/v0-2/production-registry.json"
sentinel="assistant/curriculum-builder/registry/candidate-v0-2-production/BLOCKED-NO-WRITES.sentinel"

section 'App Runtime Approval Gate (Documentation Only)'
cat <<'EOF'
Status: production-readiness — Timer Level 3 only
Runtime-approved apps: 1 (Classroom Timer & Stopwatch)
Other apps runtime-approved: no
Planning-complete equals runtime-approved: no
Chief of Staff implements apps: no
Chief of Staff launches apps: no
Student data: blocked — absolute
PASS does not authorize other apps: yes
EOF

section 'Core Gate Artifacts'
check_file "${gate_doc}"
check_doc_contains "${gate_doc}" "complete_app_runtime_approval_gate_program" "gate closure marker"
check_doc_contains "${gate_doc}" "Planning lane completion does not approve runtime implementation" "planning not runtime banner"
check_doc_contains "${gate_doc}" "Fake/local fixtures do not approve runtime data handling" "fixtures not approval banner"
check_file "${checklist_doc}"
check_file "${matrix_doc}"
check_file "${program_doc}"
check_file "${manifest_path}"
check_file "${timer_candidate}"
check_doc_contains "${timer_candidate}" "Level 3" "timer candidate Level 3 reference"
check_file apps/classroom-timer-stopwatch/index.html
check_file scripts/classroom-timer-stopwatch-runtime-status.sh

section 'Planning Lanes Program Cross-Check'
check_file "${planning_program}"
check_file scripts/app-ecosystem-planning-lanes-status.sh
check_file "${planning_manifest}"
check_file "${blocked_summary}"

section 'Manifest Readiness Verification'
if command -v python3 >/dev/null 2>&1; then
  python3 -m json.tool "${manifest_path}" >/dev/null 2>&1 && pass 'JSON parses: runtime approval manifest' || fail 'JSON does not parse: runtime approval manifest'
  manifest_report="$(python3 <<'PY'
import json
from pathlib import Path
m = json.loads(Path("assistant/app-ecosystem/samples/runtime-approval-manifest.json").read_text())
entries = m.get("entries", [])
approved = [e for e in entries if e.get("runtime_approved")]
print(len(entries))
print("APPROVED:", len(approved))
for e in approved:
    print("SLUG:", e.get("slug"))
missing_packets = []
for e in entries:
    if e.get("implementation_packet"):
        if not Path(e["implementation_packet"]).is_file():
            missing_packets.append(e["slug"])
print("MISSING_PACKETS:", ",".join(missing_packets) if missing_packets else "none")
count = m.get("runtime_approved_count", -1)
print("APPROVED_COUNT:", count)
if count != 1:
    print("BAD_APPROVED_COUNT")
else:
    print("APPROVED_COUNT_OK")
if len(approved) != 1 or (approved and approved[0].get("slug") != "classroom-timer-stopwatch"):
    print("BAD_APPROVED_SET")
else:
    print("APPROVED_SET_OK")
PY
)"
  entry_count="${manifest_report%%$'\n'*}"
  [[ "${entry_count}" == "52" ]] && pass 'manifest lists 52 apps' || fail "manifest must list 52 apps (got ${entry_count})"
  grep -q 'APPROVED: 1' <<<"${manifest_report}" && pass 'exactly one app runtime_approved in manifest' || fail 'manifest must have exactly one runtime_approved app'
  grep -q 'APPROVED_SET_OK' <<<"${manifest_report}" && pass 'only classroom-timer-stopwatch runtime approved' || fail 'only classroom-timer-stopwatch may be runtime approved'
  grep -q 'APPROVED_COUNT_OK' <<<"${manifest_report}" && pass 'manifest runtime_approved_count is 1' || fail 'manifest runtime_approved_count must be 1'
  grep -q 'MISSING_PACKETS: none' <<<"${manifest_report}" && pass 'all listed implementation packets exist' || fail "missing implementation packets: $(grep MISSING_PACKETS <<<"${manifest_report}")"
  packet_count="$(python3 -c "import json; m=json.load(open('${manifest_path}')); print(m.get('tier_1_3_packet_count',0))" 2>/dev/null || echo 0)"
  [[ "${packet_count}" == "27" ]] && pass 'manifest declares 27 Tier 1–3 packets' || fail "Tier 1–3 packet count must be 27 (got ${packet_count})"
else
  warn 'python3 not available for manifest verification'
fi

section 'Readiness Matrix Content'
check_doc_contains "${matrix_doc}" "Runtime-approved apps: 1" "matrix one runtime approved"
check_doc_contains "${matrix_doc}" "level_3_runtime_prototype_implemented" "matrix Level 3 timer state"
check_doc_contains "${matrix_doc}" "planning_complete_runtime_candidate" "matrix runtime candidate state"
check_doc_contains "${matrix_doc}" "proposal_only_blocked_student_data" "matrix student data blocked state"
check_doc_contains "${matrix_doc}" "Level 3" "matrix level 3 documented"

section 'Timer Runtime Prototype Only'
check_file apps/classroom-timer-stopwatch/timer.js
other_apps=0
if [[ -d apps ]]; then
  for d in apps/*/; do
    [[ "${d}" == "apps/classroom-timer-stopwatch/" ]] && continue
    other_apps=1
    fail "unexpected app directory: ${d}"
  done
  [[ "${other_apps}" == "0" ]] && pass 'only classroom-timer-stopwatch under apps/'
fi

section 'No Unauthorized Runtime Artifacts'
for forbidden in \
  'assistant/classroom-utilities/runtime/classroom-timer-stopwatch' \
  'docs/classroom-utilities/classroom-timer-stopwatch.html' \
  'docs/classroom-utilities/interactive-bingo-caller.js'; do
  [[ -e "${forbidden}" ]] && fail "forbidden runtime artifact exists: ${forbidden}" || pass "no forbidden runtime artifact: ${forbidden}"
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
check_doc_contains docs/build-queue.md "runtime approval gate" "build queue approval gate"
check_doc_contains assistant/memory/active-priorities.md "runtime approval gate" "active priorities approval gate"
check_doc_contains docs/proposals/index.md "Runtime approval gate" "proposal ledger approval gate"
check_doc_contains docs/teacher-workstation-capability-map.md "app-runtime-approval-gate-status" "capability map approval gate status"
check_doc_contains docs/whole-system-master-roadmap-build-state-report.md "complete_app_runtime_approval_gate_program" "whole-system report approval gate closure"

section 'Dashboard and Validate-All Wiring'
grep -Fq -- 'app-runtime-approval-gate-status.sh' scripts/chief-of-staff-dashboard.sh && pass 'dashboard wires approval gate status' || fail 'dashboard missing approval gate status'
grep -Fq -- 'app-runtime-approval-gate-status.sh' scripts/chief-of-staff-validate-all.sh && pass 'validate-all wires approval gate status' || fail 'validate-all missing approval gate status'
grep -Fq -- 'classroom-timer-stopwatch-runtime-status.sh' scripts/chief-of-staff-validate-all.sh && pass 'validate-all wires timer runtime status' || fail 'validate-all missing timer runtime status'
source scripts/validation-smoke-tier-boundary.sh
check_smoke_excludes_deep_validation 'app-runtime-approval-gate' 'App runtime approval gate'

section 'CLI, Manifest, and Tests'
bash -n "${BASH_SOURCE[0]}" && pass "bash syntax ok: ${BASH_SOURCE[0]}" || fail "bash syntax failed: status script"
grep -Fq -- '--app-runtime-approval-gate-status' bin/chief-of-staff && pass 'CLI exposes --app-runtime-approval-gate-status' || fail 'CLI missing --app-runtime-approval-gate-status'
grep -Fq -- '"--app-runtime-approval-gate-status"' assistant/chief-of-staff/v1/command-surface-manifest.json && pass 'manifest lists --app-runtime-approval-gate-status' || fail 'manifest missing --app-runtime-approval-gate-status'
check_file tests/app-runtime-approval-gate-status-test.sh
bash -n tests/app-runtime-approval-gate-status-test.sh && pass 'bash syntax ok: approval gate test' || fail 'bash syntax failed: approval gate test'

section 'Negative Non-Activation Assertions'
status_script="${BASH_SOURCE[0]}"
grep -Eq '(^|[;&|[:space:]])curl[[:space:]]' "${status_script}" 2>/dev/null && fail "${status_script} must not shell-invoke curl" || pass "${status_script} does not shell-invoke curl"
grep -Eq '(^|[;&|[:space:]])ollama[[:space:]]' "${status_script}" 2>/dev/null && fail "${status_script} must not shell-invoke ollama" || pass "${status_script} does not shell-invoke ollama"
pass 'no classroom app executed by gate status'
pass 'Timer Level 3 does not authorize other apps'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
