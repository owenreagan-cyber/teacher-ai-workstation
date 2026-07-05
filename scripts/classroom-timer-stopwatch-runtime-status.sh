#!/usr/bin/env bash
# Read-only Classroom Timer & Stopwatch runtime prototype status. Does not launch browser.
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

app_dir="apps/classroom-timer-stopwatch"
planning_doc="docs/classroom-utilities/classroom-timer-stopwatch-planning.md"
runtime_packet="docs/app-ecosystem/implementation-packets/classroom-timer-stopwatch-runtime-approval-packet.md"
impl_packet="docs/app-ecosystem/implementation-packets/classroom-timer-stopwatch-implementation-packet.md"
gate_doc="docs/app-ecosystem/runtime-implementation-approval-gate.md"
checklist_doc="docs/app-ecosystem/runtime-app-boundary-checklist.md"
matrix_doc="docs/app-ecosystem/app-production-readiness-matrix.md"
manifest_path="assistant/app-ecosystem/samples/runtime-approval-manifest.json"
production_registry_path="assistant/curriculum-builder/registry/v0-2/production-registry.json"
sentinel="assistant/curriculum-builder/registry/candidate-v0-2-production/BLOCKED-NO-WRITES.sentinel"

section 'Classroom Timer & Stopwatch Runtime Prototype (Level 3)'
cat <<'EOF'
Status: Owen-approved Level 3 local-only prototype
Runtime-approved apps: Classroom Timer & Stopwatch only
Other apps runtime-approved: no
Student data: blocked — absolute
Persistence/storage: blocked
Audio/animation: blocked
Network/API: blocked
Chief of Staff launches app: no
EOF

section 'Authority and Planning Cross-Links'
check_file "${planning_doc}"
check_file "${runtime_packet}"
check_file "${impl_packet}"
check_file "${gate_doc}"
check_file "${checklist_doc}"
check_doc_contains "${runtime_packet}" "Level 3" "runtime packet Level 3"
check_doc_contains "${impl_packet}" "Level 3 approved by Owen" "implementation packet Level 3 approval"

section 'Prototype Files'
for f in index.html styles.css timer.js presets.json README.md; do
  check_file "${app_dir}/${f}"
done

section 'Runtime Features (Static Verification)'
check_doc_contains "${app_dir}/timer.js" 'mode = "countdown"' "countdown mode"
check_doc_contains "${app_dir}/timer.js" 'setMode("stopwatch")' "stopwatch mode"
check_doc_contains "${app_dir}/timer.js" 'function start(' "start control"
check_doc_contains "${app_dir}/timer.js" 'function pause(' "pause control"
check_doc_contains "${app_dir}/timer.js" 'function reset(' "reset control"
check_doc_contains "${app_dir}/timer.js" 'setInterval' "timer interval (approved for this app)"
check_doc_contains "${app_dir}/index.html" 'btn-start' "start button in HTML"
check_doc_contains "${app_dir}/index.html" 'btn-pause' "pause button in HTML"
check_doc_contains "${app_dir}/index.html" 'btn-reset' "reset button in HTML"
check_doc_contains "${app_dir}/index.html" 'time-display' "classroom display element"
check_doc_contains "${app_dir}/index.html" 'sr-announcer' "screen reader announcer region"
check_doc_contains "${app_dir}/index.html" 'aria-live="polite"' "aria-live status region"
check_doc_contains "${app_dir}/index.html" 'keyboard-hints' "keyboard hints documented"
check_doc_contains "${app_dir}/styles.css" ':focus-visible' "focus-visible styling"
check_doc_contains "${app_dir}/timer.js" 'function announceStatus' "preset/status announcement helper"
check_doc_contains "${app_dir}/timer.js" 'Preset applied:' "preset apply announcement text"
check_doc_contains "${app_dir}/timer.js" 'applyPreset(' "keyboard preset selection"
check_doc_contains "${app_dir}/timer.js" 'if (running)' "duplicate interval guard"
for preset in "1 minute" "3 minutes" "5 minutes" "10 minutes" "Warmup" "Transition" "Exit ticket"; do
  check_doc_contains "${app_dir}/timer.js" "${preset}" "preset ${preset}"
done

section 'Blocked APIs Absent (Timer App Files)'
timer_files="${app_dir}/timer.js ${app_dir}/index.html"
for pattern in localStorage sessionStorage indexedDB fetch XMLHttpRequest oauth openai anthropic ollama \
  Audio requestAnimationFrame cookie document.cookie navigator.mediaDevices; do
  if grep -Fq -- "${pattern}" ${timer_files} 2>/dev/null; then
    fail "blocked API reference in timer app: ${pattern}"
  else
    pass "no blocked API reference: ${pattern}"
  fi
done

section 'Only Timer Runtime Approved'
if command -v python3 >/dev/null 2>&1; then
  approved_report="$(python3 <<'PY'
import json
from pathlib import Path
m = json.loads(Path("assistant/app-ecosystem/samples/runtime-approval-manifest.json").read_text())
approved = [e for e in m["entries"] if e.get("runtime_approved")]
print(len(approved))
for e in approved:
    print("SLUG:", e.get("slug"))
print("COUNT:", m.get("runtime_approved_count", -1))
PY
)"
  approved_count="${approved_report%%$'\n'*}"
  [[ "${approved_count}" == "1" ]] && pass 'exactly one app runtime_approved in manifest' || fail "runtime_approved count must be 1 (got ${approved_count})"
  grep -q 'SLUG: classroom-timer-stopwatch' <<<"${approved_report}" && pass 'only classroom-timer-stopwatch runtime approved' || fail 'runtime approved app must be classroom-timer-stopwatch only'
  grep -q 'COUNT: 1' <<<"${approved_report}" && pass 'manifest runtime_approved_count is 1' || fail 'manifest runtime_approved_count must be 1'
else
  warn 'python3 not available for manifest approval check'
fi
other_app_dirs=0
if [[ -d apps ]]; then
  for d in apps/*/; do
    [[ -d "${d}" ]] || continue
    [[ "${d}" == "apps/classroom-timer-stopwatch/" ]] && continue
    other_app_dirs=1
    fail "unexpected app runtime directory: ${d}"
  done
  [[ "${other_app_dirs}" == "0" ]] && pass 'no other app directories under apps/'
fi

section 'No Other App Runtime Artifacts'
for forbidden in \
  'docs/classroom-utilities/interactive-bingo-caller.html' \
  'apps/interactive-bingo-caller' \
  'assistant/classroom-utilities/runtime/interactive-bingo-caller'; do
  [[ -e "${forbidden}" ]] && fail "forbidden other-app runtime artifact: ${forbidden}" || pass "no forbidden other-app artifact: ${forbidden}"
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
check_doc_contains docs/build-queue.md "classroom timer" "build queue timer runtime"
check_doc_contains docs/whole-system-master-roadmap-build-state-report.md "Level 3" "whole-system report Level 3 timer"
check_doc_contains "${matrix_doc}" "Runtime-approved apps: 1" "matrix one runtime approved"

section 'Dashboard and Validate-All Wiring'
grep -Fq -- 'classroom-timer-stopwatch-runtime-status.sh' scripts/chief-of-staff-dashboard.sh && pass 'dashboard wires timer runtime status' || fail 'dashboard missing timer runtime status'
grep -Fq -- 'classroom-timer-stopwatch-runtime-status.sh' scripts/chief-of-staff-validate-all.sh && pass 'validate-all wires timer runtime status' || fail 'validate-all missing timer runtime status'
source scripts/validation-smoke-tier-boundary.sh
check_smoke_excludes_deep_validation 'classroom-timer-stopwatch-runtime' 'Classroom timer stopwatch runtime'

section 'CLI, Manifest, and Tests'
bash -n "${BASH_SOURCE[0]}" && pass "bash syntax ok: ${BASH_SOURCE[0]}" || fail "bash syntax failed: status script"
grep -Fq -- '--classroom-timer-stopwatch-runtime-status' bin/chief-of-staff && pass 'CLI exposes --classroom-timer-stopwatch-runtime-status' || fail 'CLI missing --classroom-timer-stopwatch-runtime-status'
grep -Fq -- '"--classroom-timer-stopwatch-runtime-status"' assistant/chief-of-staff/v1/command-surface-manifest.json && pass 'manifest lists --classroom-timer-stopwatch-runtime-status' || fail 'manifest missing --classroom-timer-stopwatch-runtime-status'
check_file tests/classroom-timer-stopwatch-runtime-status-test.sh
check_file tests/classroom-timer-stopwatch-runtime-static-safety-test.sh
bash -n tests/classroom-timer-stopwatch-runtime-status-test.sh && pass 'bash syntax ok: runtime status test' || fail 'bash syntax failed: runtime status test'

section 'Negative Non-Activation Assertions'
status_script="${BASH_SOURCE[0]}"
grep -Eq '(^|[;&|[:space:]])curl[[:space:]]' "${status_script}" 2>/dev/null && fail "${status_script} must not shell-invoke curl" || pass "${status_script} does not shell-invoke curl"
grep -Eq '(^|[;&|[:space:]])open[[:space:]]' "${status_script}" 2>/dev/null && fail "${status_script} must not shell-invoke open" || pass "${status_script} does not shell-invoke open"
pass 'timer app not launched by status script'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
