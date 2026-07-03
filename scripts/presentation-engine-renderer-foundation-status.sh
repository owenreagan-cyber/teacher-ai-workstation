#!/usr/bin/env bash
# Read-only Presentation Engine renderer-foundation planning status. No rendering, export, or generation.
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
check_absent_in_fixtures() {
  local pattern="$1" label="$2"
  local hits=0 f
  for f in assistant/presentation-engine/samples/renderer-planning/*.json; do
    [[ -f "${f}" ]] || continue
    if grep -qiE "${pattern}" "${f}" 2>/dev/null; then
      hits=1
      fail "fixture ${f} must not contain ${label}"
    fi
  done
  [[ "${hits}" == "0" ]] && pass "planning fixtures exclude ${label}"
}

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
[[ -z "${repo_root}" ]] && repo_root="$(cd "${script_dir}/.." && pwd -P)"
cd "${repo_root}"

foundation_doc="docs/presentation-engine-renderer-foundation.md"
interface_doc="docs/presentation-engine-static-renderer-interface-plan.md"
boundary_doc="docs/presentation-engine-blocked-runtime-boundaries.md"
plan_fixture="assistant/presentation-engine/samples/renderer-planning/example-presentation-plan-001.json"
outline_fixture="assistant/presentation-engine/samples/renderer-planning/example-slide-outline-001.json"
negative_fixture="assistant/presentation-engine/samples/renderer-planning/negative/blocked-runtime-export-example.json"
production_registry_path="assistant/curriculum-builder/registry/v0-2/production-registry.json"
sentinel="assistant/curriculum-builder/registry/candidate-v0-2-production/BLOCKED-NO-WRITES.sentinel"
APPROVED_ID="resource-math-lesson-108-presentation"

section 'Presentation Engine Renderer Foundation (Planning Only)'
cat <<'EOF'
Status: documentation/status/fixture planning only
Runtime rendering: no
Slide export: no
AI generation: no
Real curriculum ingestion: no
Integrations: no
Student data: no
Production registry writes: no
PASS does not authorize implementation: yes
EOF

section 'Foundation Documents'
check_file "${foundation_doc}"
check_file "${interface_doc}"
check_file "${boundary_doc}"
check_doc_contains "${foundation_doc}" "complete_presentation_engine_renderer_foundation_planning" "closure status"
check_doc_contains "${foundation_doc}" "Local-First Posture" "local-first posture"
check_doc_contains "${foundation_doc}" "not generate, render, or export" "no runtime generation boundary"
check_doc_contains "${interface_doc}" "presentation_plan" "presentation_plan concept"
check_doc_contains "${interface_doc}" "slide_outline" "slide_outline concept"
check_doc_contains "${interface_doc}" "theme_profile" "theme_profile concept"
check_doc_contains "${interface_doc}" "teacher_display_mode" "teacher_display_mode concept"
check_doc_contains "${interface_doc}" "resource_reference_label" "resource_reference_label concept"
check_doc_contains "${interface_doc}" "speaker_notes_label" "speaker_notes_label concept"
check_doc_contains "${interface_doc}" "classroom_interaction_hint" "classroom_interaction_hint concept"
check_doc_contains "${interface_doc}" "export_target" "export_target concept"
check_doc_contains "${boundary_doc}" "Runtime rendering" "runtime rendering blocked"
check_doc_contains "${boundary_doc}" "Slide export" "slide export blocked"
check_doc_contains "${boundary_doc}" "AI generation" "AI generation blocked"
check_doc_contains "${boundary_doc}" "Student data" "student data blocked"

section 'Fake Local Fixtures'
check_file "assistant/presentation-engine/samples/renderer-planning/README.md"
check_file "${plan_fixture}"
check_file "${outline_fixture}"
check_file "${negative_fixture}"
check_doc_contains "${plan_fixture}" "fake_local_planning_only" "plan fixture classification"
check_doc_contains "${plan_fixture}" "fake-local-resource-label" "fake resource label"
check_doc_contains "${plan_fixture}" "Example Fraction Review Display" "fake title label"
check_doc_contains "${outline_fixture}" "fake_local_planning_only" "outline fixture classification"
check_doc_contains "${negative_fixture}" "negative_blocked_fields_reference" "negative fixture classification"

if command -v python3 >/dev/null 2>&1; then
  for f in "${plan_fixture}" "${outline_fixture}" "${negative_fixture}"; do
    python3 -m json.tool "${f}" >/dev/null 2>&1 && pass "JSON parses: ${f}" || fail "JSON does not parse: ${f}"
  done
else
  warn 'python3 not available for JSON parse checks'
fi

section 'Fixture Safety (Positive Fixtures Only)'
check_absent_in_fixtures 'drive\.google|docs\.google' 'Drive URLs'
check_absent_in_fixtures 'https?://' 'HTTP URLs'
check_absent_in_fixtures '/Users/|/home/|smb://|icloud' 'local or NAS paths'
check_absent_in_fixtures 'student_name|student_id' 'student identifiers'
check_absent_in_fixtures 'generation_prompt|openai|anthropic' 'generation prompt fields'

section 'No Runtime Renderer / Export / Generation Scripts'
runtime_hits=0
for candidate in scripts/*presentation-engine*render* scripts/*presentation-engine*export* scripts/*presentation-engine*generat*; do
  [[ -e "${candidate}" ]] || continue
  [[ "${candidate}" == *status* ]] && continue
  runtime_hits=1
  fail "runtime script must not exist: ${candidate}"
done
[[ "${runtime_hits}" == "0" ]] && pass 'no presentation-engine runtime renderer/export/generation scripts'

for f in scripts/presentation-engine-*.sh; do
  [[ -e "${f}" ]] || continue
  [[ "${f}" == *status* ]] && pass "status script allowed: ${f}" && continue
  fail "unexpected presentation-engine script: ${f}"
done
[[ ! -e scripts/presentation-engine-render.sh ]] && pass 'no scripts/presentation-engine-render.sh' || fail 'scripts/presentation-engine-render.sh must not exist'
[[ ! -e scripts/presentation-engine-export.sh ]] && pass 'no scripts/presentation-engine-export.sh' || fail 'scripts/presentation-engine-export.sh must not exist'
[[ ! -e scripts/presentation-engine-generate.sh ]] && pass 'no scripts/presentation-engine-generate.sh' || fail 'scripts/presentation-engine-generate.sh must not exist'

grep -Fq -- '--presentation-engine-render)' bin/chief-of-staff 2>/dev/null && fail 'CLI must not expose --presentation-engine-render' || pass 'CLI has no --presentation-engine-render'
grep -Fq -- '--presentation-engine-export)' bin/chief-of-staff 2>/dev/null && fail 'CLI must not expose --presentation-engine-export' || pass 'CLI has no --presentation-engine-export'
grep -Fq -- '--presentation-engine-generate)' bin/chief-of-staff 2>/dev/null && fail 'CLI must not expose --presentation-engine-generate' || pass 'CLI has no --presentation-engine-generate'

section 'Production Registry Parked-State Proof'
check_file "${production_registry_path}"
check_file "${sentinel}"
record_count="$(python3 -c "import json; d=json.load(open('${production_registry_path}')); print(len(d.get('records',[])))" 2>/dev/null || echo 0)"
[[ "${record_count}" == "1" ]] && pass 'production registry records count exactly 1' || fail "production registry records count must be 1 (got ${record_count})"
grep -Fq -- "${APPROVED_ID}" "${production_registry_path}" && pass 'approved record ID present' || fail 'approved record ID missing'
grep -Fq -- '--curriculum-registry-write)' bin/chief-of-staff 2>/dev/null && fail 'chief-of-staff must not implement --curriculum-registry-write handler' || pass 'chief-of-staff has no --curriculum-registry-write handler'
writer_scripts_present=0
for candidate in scripts/*production-registry*write*; do
  [[ -e "${candidate}" ]] && writer_scripts_present=1
done
[[ "${writer_scripts_present}" == "0" ]] && pass 'no production-registry writer scripts in scripts/' || fail 'writer scripts must not exist'

section 'Roadmap and Capability Coherence'
check_doc_contains docs/whole-system-master-roadmap-build-state-report.md "Presentation Engine" "whole-system report presentation engine"
check_doc_contains docs/master-build-roadmap.md "Presentation Engine" "master build roadmap presentation engine"
check_doc_contains docs/build-queue.md "Presentation Engine" "build queue presentation engine"
check_doc_contains docs/teacher-workstation-capability-map.md "Presentation Engine" "capability map presentation engine"
check_doc_contains assistant/memory/active-priorities.md "Presentation Engine" "active priorities presentation engine"

section 'CLI, Manifest, and Tests'
bash -n "${BASH_SOURCE[0]}" && pass "bash syntax ok: ${BASH_SOURCE[0]}" || fail "bash syntax failed: status script"
grep -Fq -- '--presentation-engine-renderer-foundation-status' bin/chief-of-staff && pass 'CLI exposes --presentation-engine-renderer-foundation-status' || fail 'CLI missing --presentation-engine-renderer-foundation-status'
grep -Fq -- '"--presentation-engine-renderer-foundation-status"' assistant/chief-of-staff/v1/command-surface-manifest.json && pass 'manifest lists --presentation-engine-renderer-foundation-status' || fail 'manifest missing --presentation-engine-renderer-foundation-status'
check_file tests/presentation-engine-renderer-foundation-status-test.sh
bash -n tests/presentation-engine-renderer-foundation-status-test.sh && pass 'bash syntax ok: presentation engine test' || fail 'bash syntax failed: presentation engine test'

section 'Negative Non-Activation Assertions'
status_script="${BASH_SOURCE[0]}"
grep -Eq '(^|[;&|[:space:]])curl[[:space:]]' "${status_script}" 2>/dev/null && fail "${status_script} must not shell-invoke curl" || pass "${status_script} does not shell-invoke curl"
grep -Eq '(^|[;&|[:space:]])ollama[[:space:]]' "${status_script}" 2>/dev/null && fail "${status_script} must not shell-invoke ollama" || pass "${status_script} does not shell-invoke ollama"
grep -Eq '(^|[;&|[:space:]])(keynote|powerpoint|soffice)[[:space:]]' "${status_script}" 2>/dev/null && fail "${status_script} must not shell-invoke slide tools" || pass "${status_script} does not shell-invoke slide tools"
pass 'no rendering attempted'
pass 'no export attempted'
pass 'no generation attempted'
pass 'no real curriculum ingestion attempted'
pass 'no network call attempted'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
