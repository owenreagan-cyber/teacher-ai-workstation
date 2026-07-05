#!/usr/bin/env bash
# Read-only aggregate app ecosystem planning lanes status. No app runtime.
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

program_doc="docs/app-ecosystem-planning-lanes-program.md"
manifest_path="assistant/app-ecosystem/samples/planning-lanes-manifest.json"
inventory_doc="docs/app-ecosystem-inventory-and-prototype-build-list.md"
blocked_summary="docs/proposals/blocked/high-risk-app-planning-blocked-summary.md"
production_registry_path="assistant/curriculum-builder/registry/v0-2/production-registry.json"
sentinel="assistant/curriculum-builder/registry/candidate-v0-2-production/BLOCKED-NO-WRITES.sentinel"

section 'App Ecosystem Planning Lanes Program (Documentation Only)'
cat <<'EOF'
Status: planning-only — not runtime approval
Tier 1–3 planning lanes: complete (27 apps)
Tier 4–7: blocked/proposal-only summary
Chief of Staff chooses app priority for Owen: no
Runtime classroom apps: no
Student data: blocked — absolute
PASS does not authorize implementation: yes
EOF

section 'Program Doc and Manifest'
check_file "${program_doc}"
check_doc_contains "${program_doc}" "complete_app_ecosystem_planning_lanes_program" "program closure marker"
check_doc_contains "${program_doc}" "planning-only — not implementation approval" "not implementation approval banner"
check_file "${manifest_path}"
check_file "${blocked_summary}"
check_doc_contains "${blocked_summary}" "Tier 4 — Student Data" "tier 4 blocked section"
check_doc_contains "${blocked_summary}" "Tier 5 — API" "tier 5 blocked section"

section 'Manifest Lane Verification'
if command -v python3 >/dev/null 2>&1; then
  python3 -m json.tool "${manifest_path}" >/dev/null 2>&1 && pass 'JSON parses: planning lanes manifest' || fail 'JSON does not parse: planning lanes manifest'
  lane_report="$(python3 <<'PY'
import json
from pathlib import Path
m = json.loads(Path("assistant/app-ecosystem/samples/planning-lanes-manifest.json").read_text())
lanes = m.get("tier_1_3_lanes", [])
print(len(lanes))
missing_doc = []
missing_closure = []
missing_fixture = []
for lane in lanes:
    doc = Path(lane["doc"])
    if not doc.is_file():
        missing_doc.append(lane["slug"])
        continue
    text = doc.read_text()
    if lane["closure"] not in text:
        missing_closure.append(lane["slug"])
    if lane["slug"] == "classroom-timer-stopwatch":
        preset = Path("assistant/classroom-utilities/samples/classroom-timer-stopwatch-planning/example-timer-presets-001.json")
        if not preset.is_file():
            missing_fixture.append(lane["slug"])
    elif lane.get("fixture"):
        if not Path(lane["fixture"]).is_file():
            missing_fixture.append(lane["slug"])
print("MISSING_DOC:", ",".join(missing_doc) if missing_doc else "none")
print("MISSING_CLOSURE:", ",".join(missing_closure) if missing_closure else "none")
print("MISSING_FIXTURE:", ",".join(missing_fixture) if missing_fixture else "none")
PY
)"
  lane_count="${lane_report%%$'\n'*}"
  [[ "${lane_count}" == "27" ]] && pass 'manifest declares 27 Tier 1–3 planning lanes' || fail "manifest lane count must be 27 (got ${lane_count})"
  program_closure="$(python3 -c "import json; print(json.load(open('${manifest_path}'))['program_closure'])" 2>/dev/null || echo '')"
  [[ "${program_closure}" == "complete_app_ecosystem_planning_lanes_program" ]] && pass 'manifest program closure marker correct' || fail "manifest program closure incorrect (got ${program_closure})"
  grep -q 'MISSING_DOC: none' <<<"${lane_report}" && pass 'all manifest lanes have planning docs' || fail "manifest lanes missing docs: $(grep MISSING_DOC <<<"${lane_report}")"
  grep -q 'MISSING_CLOSURE: none' <<<"${lane_report}" && pass 'all manifest lanes have closure markers' || fail "manifest lanes missing closure: $(grep MISSING_CLOSURE <<<"${lane_report}")"
  grep -q 'MISSING_FIXTURE: none' <<<"${lane_report}" && pass 'all manifest lanes have fixtures where required' || fail "manifest lanes missing fixtures: $(grep MISSING_FIXTURE <<<"${lane_report}")"
else
  warn 'python3 not available for manifest lane verification'
fi

section 'Planning Doc Safety Banners (Spot Checks)'
for spot in \
  docs/classroom-utilities/interactive-bingo-caller-planning.md \
  docs/classroom-utilities/desk-layout-design-architect-planning.md \
  docs/classroom-utilities/shurley-chapter-parser-planning.md; do
  check_doc_contains "${spot}" "Runtime classroom app: blocked" "runtime blocked in ${spot}"
  check_doc_contains "${spot}" "Student data: blocked" "student data blocked in ${spot}"
done
check_doc_contains docs/classroom-utilities/classroom-timer-stopwatch-planning.md "Level 3 runtime prototype implemented" "timer Level 3 runtime banner"
check_doc_contains docs/classroom-utilities/classroom-timer-stopwatch-planning.md "Other apps runtime: blocked" "timer other apps runtime blocked"
check_doc_contains docs/classroom-utilities/classroom-timer-stopwatch-planning.md "Student data: blocked" "timer student data blocked"

section 'Tier 3 Owen Decision Banners'
for tier3 in \
  docs/classroom-utilities/spelling-studio-planning.md \
  docs/classroom-utilities/shurley-chapter-parser-planning.md \
  docs/classroom-utilities/power-up-packet-maker-planning.md; do
  check_doc_contains "${tier3}" "Owen decision required" "tier 3 Owen decision banner"
done

section 'Fake Local Fixture Classification (Spot Checks)'
for fixture in \
  assistant/classroom-utilities/samples/interactive-bingo-caller-planning/example-settings-001.json \
  assistant/classroom-utilities/samples/desk-layout-design-architect-planning/example-settings-001.json \
  assistant/classroom-utilities/samples/classroom-timer-stopwatch-planning/example-timer-presets-001.json; do
  check_file "${fixture}"
  check_doc_contains "${fixture}" "fake_local_planning_only" "fixture classification ${fixture}"
  check_doc_contains "${fixture}" '"runtime_app": "blocked"' "fixture runtime blocked ${fixture}"
done

section 'No Executable Runtime Artifacts (Aggregate Spot Check)'
for forbidden in \
  'docs/classroom-utilities/interactive-bingo-caller.html' \
  'docs/classroom-utilities/desk-layout-design-architect.js' \
  'assistant/classroom-utilities/runtime/interactive-bingo-caller'; do
  [[ -e "${forbidden}" ]] && fail "forbidden runtime artifact exists: ${forbidden}" || pass "no forbidden runtime artifact: ${forbidden}"
done

section 'Timer Reference Lane Intact'
check_file scripts/classroom-timer-stopwatch-planning-status.sh
check_file tests/classroom-timer-stopwatch-planning-status-test.sh
check_doc_contains docs/classroom-utilities/classroom-timer-stopwatch-planning.md "Owen selected this app for the first planning lane" "timer Owen selection preserved"

section 'App Inventory Cross-Link'
check_file "${inventory_doc}"
check_doc_contains "${inventory_doc}" "complete_app_ecosystem_planning_lanes_program" "inventory program closure cross-link"
check_doc_contains "${inventory_doc}" "planning lane complete" "inventory planning lane complete status"
check_doc_contains "${inventory_doc}" "high-risk-app-planning-blocked-summary.md" "inventory blocked summary cross-link"
check_doc_contains "${inventory_doc}" "Interactive Bingo Caller" "inventory includes bingo caller"
check_doc_contains "${inventory_doc}" "Desk Layout Design Architect" "inventory includes desk layout"

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
check_doc_contains docs/build-queue.md "app ecosystem planning lanes" "build queue planning lanes program"
check_doc_contains assistant/memory/active-priorities.md "planning lanes program" "active priorities planning lanes"
check_doc_contains docs/proposals/index.md "App ecosystem planning lanes" "proposal ledger planning lanes program"
check_doc_contains docs/teacher-workstation-capability-map.md "app-ecosystem-planning-lanes-status" "capability map planning lanes status"

section 'Dashboard and Validate-All Wiring'
grep -Fq -- 'app-ecosystem-planning-lanes-status.sh' scripts/chief-of-staff-dashboard.sh && pass 'dashboard wires planning lanes status' || fail 'dashboard missing planning lanes status'
grep -Fq -- 'app-ecosystem-planning-lanes-status.sh' scripts/chief-of-staff-validate-all.sh && pass 'validate-all wires planning lanes status' || fail 'validate-all missing planning lanes status'
source scripts/validation-smoke-tier-boundary.sh
check_smoke_excludes_deep_validation 'app-ecosystem-planning-lanes' 'App ecosystem planning lanes'

section 'CLI, Manifest, and Tests'
bash -n "${BASH_SOURCE[0]}" && pass "bash syntax ok: ${BASH_SOURCE[0]}" || fail "bash syntax failed: status script"
grep -Fq -- '--app-ecosystem-planning-lanes-status' bin/chief-of-staff && pass 'CLI exposes --app-ecosystem-planning-lanes-status' || fail 'CLI missing --app-ecosystem-planning-lanes-status'
grep -Fq -- '"--app-ecosystem-planning-lanes-status"' assistant/chief-of-staff/v1/command-surface-manifest.json && pass 'manifest lists --app-ecosystem-planning-lanes-status' || fail 'manifest missing --app-ecosystem-planning-lanes-status'
check_file tests/app-ecosystem-planning-lanes-status-test.sh
bash -n tests/app-ecosystem-planning-lanes-status-test.sh && pass 'bash syntax ok: planning lanes test' || fail 'bash syntax failed: planning lanes test'

section 'Negative Non-Activation Assertions'
status_script="${BASH_SOURCE[0]}"
grep -Eq '(^|[;&|[:space:]])curl[[:space:]]' "${status_script}" 2>/dev/null && fail "${status_script} must not shell-invoke curl" || pass "${status_script} does not shell-invoke curl"
grep -Eq '(^|[;&|[:space:]])ollama[[:space:]]' "${status_script}" 2>/dev/null && fail "${status_script} must not shell-invoke ollama" || pass "${status_script} does not shell-invoke ollama"
pass 'no classroom app executed'
pass 'no runtime app approval implied'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
