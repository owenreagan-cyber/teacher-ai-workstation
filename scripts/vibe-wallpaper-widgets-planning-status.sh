#!/usr/bin/env bash
# Read-only Vibe / Wallpaper / Widgets planning gate status. No runtime, install, or Mac mutation.
set -euo pipefail

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

pass() { PASS_COUNT=$((PASS_COUNT + 1)); printf 'PASS: %s\n' "$1"; }
warn() { WARN_COUNT=$((WARN_COUNT + 1)); printf 'WARN: %s\n' "$1"; }
fail() { FAIL_COUNT=$((FAIL_COUNT + 1)); printf 'FAIL: %s\n' "$1"; }
section() { printf '\n%s\n' "$1"; printf '%s\n' '----------------------------------------'; }

check_file() {
  [[ -f "$1" ]] && pass "file exists: $1" || fail "file missing: $1"
}

check_doc_contains() {
  local path="$1" needle="$2" label="$3"
  if [[ ! -f "${path}" ]]; then
    fail "${path} must mention ${label}"
    return
  fi
  grep -Fq -- "${needle}" "${path}" && pass "doc mentions ${label}" || fail "${path} must mention ${label}"
}

check_no_path() {
  [[ -e "$1" ]] && fail "forbidden path exists: $1" || pass "forbidden path absent: $1"
}

check_json() {
  local path="$1"
  if [[ ! -f "${path}" ]]; then
    fail "JSON file missing: ${path}"
    return
  fi
  if command -v python3 >/dev/null 2>&1; then
    python3 -m json.tool "${path}" >/dev/null 2>&1 && pass "JSON parses: ${path}" || fail "JSON does not parse: ${path}"
  else
    warn "python3 unavailable; JSON parse skipped: ${path}"
  fi
}

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
[[ -z "${repo_root}" ]] && repo_root="$(cd "${script_dir}/.." && pwd -P)"
cd "${repo_root}"

planning_gate="docs/vibe-wallpaper-widgets/vibe-wallpaper-widgets-planning-gate.md"
vibe_brief="docs/vibe-wallpaper-widgets/teacher-workstation-vibe-brief.md"
wallpaper_plan="docs/vibe-wallpaper-widgets/wallpaper-concept-plan.md"
widget_plan="docs/vibe-wallpaper-widgets/widget-concept-plan.md"
shortcut_plan="docs/vibe-wallpaper-widgets/shortcut-concept-plan.md"
workshop_plan="docs/vibe-wallpaper-widgets/visual-workshop-concept-plan.md"
runtime_gate="docs/vibe-wallpaper-widgets/runtime-install-approval-gate.md"
sample_dir="assistant/vibe-wallpaper-widgets/samples"
production_registry_path="assistant/curriculum-builder/registry/v0-2/production-registry.json"
sentinel="assistant/curriculum-builder/registry/candidate-v0-2-production/BLOCKED-NO-WRITES.sentinel"
runtime_manifest="assistant/app-ecosystem/samples/runtime-approval-manifest.json"

section 'Vibe / Wallpaper / Widgets Planning Gate'
cat <<'EOF'
Status: planning/docs/status/tests only
Runtime approval: none
Widget install: blocked
Shortcut install: blocked
Shortcut execution: blocked
Wallpaper changes: blocked
Mac system changes: blocked
Homebrew installs: blocked
App execution: blocked
External integrations: blocked
AI generation/runtime behavior: blocked
EOF

section 'Required Planning Docs'
for path in \
  "${planning_gate}" \
  "${vibe_brief}" \
  "${wallpaper_plan}" \
  "${widget_plan}" \
  "${shortcut_plan}" \
  "${workshop_plan}" \
  "${runtime_gate}"; do
  check_file "${path}"
done
check_doc_contains "${planning_gate}" "complete_vibe_wallpaper_widgets_planning_gate_program" "planning gate closure"
check_doc_contains "${planning_gate}" "Vibe is not a runtime shell" "vibe non-runtime meaning"
check_doc_contains "${vibe_brief}" "fake/local illustrations" "fake/local example policy"
check_doc_contains "${wallpaper_plan}" "Wallpaper concepts do not approve wallpaper changes" "wallpaper not approved"
check_doc_contains "${widget_plan}" "Widget concepts do not approve widget files" "widget install not approved"
check_doc_contains "${shortcut_plan}" "Shortcut concepts must not include shortcut payloads" "shortcut payloads blocked"
check_doc_contains "${workshop_plan}" "not a page, component, app, or executable shell" "visual workshop runtime blocked"
check_doc_contains "${runtime_gate}" "Planning docs do not approve widget installation" "runtime gate widget block"
check_doc_contains "${runtime_gate}" "Wallpaper concepts do not approve changing wallpaper" "runtime gate wallpaper block"
check_doc_contains "${runtime_gate}" "Shortcut concepts do not approve installing or running shortcuts" "runtime gate shortcut block"
check_doc_contains "${runtime_gate}" "Visual workshop concepts do not approve app execution" "runtime gate app execution block"
check_doc_contains "${runtime_gate}" "Owen must explicitly approve any future runtime/install mission" "Owen approval requirement"

section 'Fake / Local Examples'
for path in \
  "${sample_dir}/teacher-vibe-palette.fake.json" \
  "${sample_dir}/wallpaper-concepts.fake.json" \
  "${sample_dir}/widget-concepts.fake.json" \
  "${sample_dir}/shortcut-concepts.fake.json" \
  "${sample_dir}/visual-workshop-zones.fake.json"; do
  check_file "${path}"
  check_json "${path}"
  check_doc_contains "${path}" "fake_fixture_only" "fake fixture marker: ${path}"
  check_doc_contains "${path}" "future_approval_needed" "future approval marker: ${path}"
done

section 'Fake Example Safety'
if command -v python3 >/dev/null 2>&1; then
  sample_report="$(python3 <<'PY'
import json
from pathlib import Path

sample_dir = Path("assistant/vibe-wallpaper-widgets/samples")
bad = []
missing_fields = []
required = {"concept_name", "teacher_use_case", "visual_mood", "safe_status", "blocked_runtime_actions", "future_approval_needed"}
blocked_needles = [
    "/Users/", "/Volumes/", "Desktop", "Documents", "Downloads", "iCloud", "Drive", "NAS",
    "AppleScript", "osascript", "defaults write", "LaunchAgent", "cron", "OAuth",
    "api_key", "student", "student_name", "real_curriculum", ".shortcut"
]
for path in sorted(sample_dir.glob("*.fake.json")):
    data = json.loads(path.read_text())
    if data.get("safe_status") != "fake_fixture_only":
        bad.append(f"{path}: top-level safe_status is not fake_fixture_only")
    if data.get("runtime_approved") is True or data.get("install_approved") is True:
        bad.append(f"{path}: top-level approval must not be true")
    text = path.read_text()
    for needle in blocked_needles:
        if needle in text:
            bad.append(f"{path}: blocked token {needle}")
    for concept in data.get("concepts", []):
        missing = sorted(required - set(concept))
        if missing:
            missing_fields.append(f"{path}:{concept.get('concept_name','unknown')} missing {','.join(missing)}")
        if concept.get("safe_status") != "fake_fixture_only":
            bad.append(f"{path}:{concept.get('concept_name','unknown')} safe_status is not fake_fixture_only")
        if not concept.get("blocked_runtime_actions"):
            bad.append(f"{path}:{concept.get('concept_name','unknown')} has no blocked_runtime_actions")
print("BAD:", "none" if not bad else " | ".join(bad))
print("MISSING:", "none" if not missing_fields else " | ".join(missing_fields))
print("COUNT:", len(list(sample_dir.glob("*.fake.json"))))
PY
)"
  grep -Fq 'BAD: none' <<<"${sample_report}" && pass 'fake examples avoid blocked runtime/install content' || fail "$(grep '^BAD:' <<<"${sample_report}")"
  grep -Fq 'MISSING: none' <<<"${sample_report}" && pass 'fake examples include required concept fields' || fail "$(grep '^MISSING:' <<<"${sample_report}")"
  grep -Fq 'COUNT: 5' <<<"${sample_report}" && pass 'five fake example files present' || fail "expected five fake example files: $(grep '^COUNT:' <<<"${sample_report}")"
else
  warn 'python3 unavailable; fake example structural checks skipped'
fi

section 'No Runtime / Install Artifacts In This Lane'
check_no_path "assistant/vibe-wallpaper-widgets/widgets"
check_no_path "assistant/vibe-wallpaper-widgets/shortcuts"
check_no_path "assistant/vibe-wallpaper-widgets/runtime"
check_no_path "assistant/vibe-wallpaper-widgets/apps"
check_no_path "docs/vibe-wallpaper-widgets/index.html"
check_no_path "docs/vibe-wallpaper-widgets/app.js"
check_no_path "docs/vibe-wallpaper-widgets/styles.css"
if find docs/vibe-wallpaper-widgets assistant/vibe-wallpaper-widgets -type f \( -name '*.scpt' -o -name '*.shortcut' -o -name '*.plist' -o -name '*.command' -o -name '*.app' -o -name '*.js' -o -name '*.html' -o -name '*.css' \) | grep -q .; then
  fail 'lane must not include executable UI, shortcut, plist, app, or script artifacts'
else
  pass 'lane has no executable UI, shortcut, plist, app, or script artifacts'
fi

section 'Blocked Existing Hazardous Surfaces'
check_doc_contains docs/mac-workstation-non-activation-boundaries.md "Mac system changes: blocked" "Mac system changes blocked"
check_doc_contains docs/mac-workstation-non-activation-boundaries.md "Wallpaper apply: blocked" "wallpaper apply blocked"
check_doc_contains docs/widget-shortcut-builder-non-activation-boundaries.md "Widget install: blocked" "widget install blocked"
check_doc_contains docs/widget-shortcut-builder-non-activation-boundaries.md "Shortcut install: blocked" "shortcut install blocked"
check_doc_contains docs/widget-shortcut-builder-non-activation-boundaries.md "Shortcut execution: blocked" "shortcut execution blocked"
check_doc_contains docs/local-llm-workstation-status-foundation.md "Ollama install | blocked" "Ollama install blocked"
check_doc_contains docs/teacher-workstation-system-updater-foundation.md "Dependency install/upgrade | blocked" "Homebrew/install blocked by updater"
check_doc_contains docs/app-ecosystem/runtime-implementation-approval-gate.md "Planning lane completion does not approve runtime implementation" "runtime gate planning boundary"

section 'Production Registry and Timer Runtime Posture'
if [[ -f "${production_registry_path}" ]] && command -v python3 >/dev/null 2>&1; then
  record_count="$(python3 -c "import json; d=json.load(open('${production_registry_path}')); print(len(d.get('records',[])))" 2>/dev/null || echo 0)"
  [[ "${record_count}" == "1" ]] && pass 'production registry records count exactly 1' || fail "production registry records count must be 1 (got ${record_count})"
else
  fail "production registry parked-state proof unavailable: ${production_registry_path}"
fi
[[ -f "${sentinel}" ]] && pass 'BLOCKED-NO-WRITES.sentinel intact' || fail 'BLOCKED-NO-WRITES.sentinel missing'
grep -Fq -- '--curriculum-registry-write)' bin/chief-of-staff 2>/dev/null && fail 'chief-of-staff must not implement --curriculum-registry-write handler' || pass 'chief-of-staff has no --curriculum-registry-write handler'
writer_scripts_present=0
for candidate in scripts/*production-registry*write*; do
  [[ -e "${candidate}" ]] && writer_scripts_present=1
done
if [[ "${writer_scripts_present}" == "0" ]]; then
  pass 'no production-registry writer scripts in scripts/'
else
  fail 'writer scripts must remain absent from scripts/'
fi
if [[ -f "${runtime_manifest}" ]] && command -v python3 >/dev/null 2>&1; then
  runtime_report="$(python3 <<'PY'
import json
m = json.load(open("assistant/app-ecosystem/samples/runtime-approval-manifest.json"))
approved = [e.get("slug") for e in m.get("entries", []) if e.get("runtime_approved")]
print("COUNT:", len(approved))
print("APPROVED:", ",".join(approved))
print("DECLARED:", m.get("runtime_approved_count"))
PY
)"
  grep -Fq 'COUNT: 1' <<<"${runtime_report}" && pass 'exactly one app runtime approved' || fail "$(grep '^COUNT:' <<<"${runtime_report}")"
  grep -Fq 'APPROVED: classroom-timer-stopwatch' <<<"${runtime_report}" && pass 'Timer remains the only runtime-approved app' || fail "$(grep '^APPROVED:' <<<"${runtime_report}")"
  grep -Fq 'DECLARED: 1' <<<"${runtime_report}" && pass 'runtime manifest declares one approved app' || fail "$(grep '^DECLARED:' <<<"${runtime_report}")"
else
  fail "runtime manifest proof unavailable: ${runtime_manifest}"
fi

section 'No Activation Patterns In Status Command'
status_script="${BASH_SOURCE[0]}"
grep -Eq '(^|[;&|[:space:]])shortcuts[[:space:]]+(run|list|view|sign)' "${status_script}" 2>/dev/null && fail 'status script must not shell-invoke Shortcuts CLI' || pass 'status script does not shell-invoke Shortcuts CLI'
grep -Eq '(^|[;&|[:space:]])osascript[[:space:]]' "${status_script}" 2>/dev/null && fail 'status script must not shell-invoke osascript' || pass 'status script does not shell-invoke osascript'
grep -Eq '(^|[;&|[:space:]])defaults[[:space:]]+write' "${status_script}" 2>/dev/null && fail 'status script must not write macOS defaults' || pass 'status script does not write macOS defaults'
grep -Eq '(^|[;&|[:space:]])(brew|npm|pip|apt-get|yum)[[:space:]]+(install|upgrade|update)' "${status_script}" 2>/dev/null && fail 'status script must not invoke package-manager install/update' || pass 'status script does not invoke package-manager install/update'
grep -Eq '(^|[;&|[:space:]])(curl|wget)[[:space:]]' "${status_script}" 2>/dev/null && fail 'status script must not invoke network fetch commands' || pass 'status script does not invoke network fetch commands'
grep -Eq '(^|[;&|[:space:]])ollama[[:space:]]+(run|pull|serve)' "${status_script}" 2>/dev/null && fail 'status script must not invoke Ollama runtime' || pass 'status script does not invoke Ollama runtime'
pass 'Chief of Staff may report status only'
pass 'no widget installed by this command'
pass 'no shortcut installed or executed by this command'
pass 'no wallpaper changed by this command'
pass 'no Mac system mutation performed by this command'
pass 'no Homebrew install performed by this command'
pass 'no app executed by this command'
pass 'no external integration activated by this command'
pass 'no AI generation/runtime behavior activated by this command'
pass 'PASS/WARN/FAIL summary semantics preserved'

section 'CLI, Dashboard, Validate-All, Smoke'
bash -n "${status_script}" && pass "bash syntax ok: ${status_script}" || fail "bash syntax failed: ${status_script}"
grep -Fq -- '--vibe-wallpaper-widgets-planning-status' bin/chief-of-staff && pass 'CLI exposes --vibe-wallpaper-widgets-planning-status' || fail 'CLI missing --vibe-wallpaper-widgets-planning-status'
grep -Fq -- '"--vibe-wallpaper-widgets-planning-status"' assistant/chief-of-staff/v1/command-surface-manifest.json && pass 'manifest lists --vibe-wallpaper-widgets-planning-status' || fail 'manifest missing --vibe-wallpaper-widgets-planning-status'
grep -Fq -- 'vibe-wallpaper-widgets-planning-status.sh' scripts/chief-of-staff-dashboard.sh && pass 'dashboard wires vibe/wallpaper/widgets status' || fail 'dashboard missing vibe/wallpaper/widgets status'
grep -Fq -- 'vibe-wallpaper-widgets-planning-status.sh' scripts/chief-of-staff-validate-all.sh && pass 'validate-all wires vibe/wallpaper/widgets status' || fail 'validate-all missing vibe/wallpaper/widgets status'
source scripts/validation-smoke-tier-boundary.sh
check_smoke_excludes_deep_validation 'vibe-wallpaper-widgets-planning' 'Vibe / Wallpaper / Widgets planning'
check_file tests/vibe-wallpaper-widgets-planning-status-test.sh

section 'Roadmap and Coherence Cross-Links'
check_doc_contains docs/whole-system-master-roadmap-build-state-report.md "complete_vibe_wallpaper_widgets_planning_gate_program" "whole-system report closure"
check_doc_contains docs/whole-system-coherence-maintenance-report.md "complete_vibe_wallpaper_widgets_planning_gate_program" "coherence report closure"
check_doc_contains docs/curriculum-builder-registry-expected-warns.md "--vibe-wallpaper-widgets-planning-status" "expected WARNs entry"
check_doc_contains docs/teacher-workstation-capability-map.md "Vibe / Wallpaper / Widgets planning gate" "capability map lane"
check_doc_contains docs/build-queue.md "Vibe / Wallpaper / Widgets Planning Gate" "build queue lane"
check_doc_contains assistant/memory/active-priorities.md "Vibe / Wallpaper / Widgets Planning Gate" "active priorities lane"
check_doc_contains docs/proposals/index.md "Vibe / Wallpaper / Widgets Planning Gate" "proposal ledger lane"

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
