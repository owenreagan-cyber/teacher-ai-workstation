#!/usr/bin/env bash
# Read-only Classroom Utility per-app mission templates status. Planning only — no runtime apps.
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

mission_template="docs/classroom-utility-per-app-mission-template.md"
candidate_matrix="docs/classroom-utility-app-candidate-matrix.md"
boundary_doc="docs/classroom-utility-student-data-boundaries.md"
templates_dir="docs/classroom-utility-templates"
fixtures_dir="assistant/classroom-utilities/samples/planning"
production_registry_path="assistant/curriculum-builder/registry/v0-2/production-registry.json"
sentinel="assistant/curriculum-builder/registry/candidate-v0-2-production/BLOCKED-NO-WRITES.sentinel"

section 'Classroom Utility Per-App Mission Templates (Planning Only)'
cat <<'EOF'
Status: documentation/status/fixture planning only
Runtime classroom apps: no
Student data: fake labels only
Real rosters/grades/behavior logs: no
Integrations: no
AI generation: no
Production registry writes: no
PASS does not authorize implementation: yes
EOF

section 'Canonical Planning Docs'
check_file "${mission_template}"
check_file "${candidate_matrix}"
check_file "${boundary_doc}"
check_doc_contains "${mission_template}" "complete_classroom_utility_per_app_mission_templates" "mission template closure"
check_doc_contains "${mission_template}" "No student data unless explicitly approved" "student data prohibition"
check_doc_contains "${boundary_doc}" "blocked — absolute" "absolute student data block"
check_doc_contains "${candidate_matrix}" "ClassPass" "ClassPass candidate"
check_doc_contains "${candidate_matrix}" "Email Responder" "Email Responder candidate"

section 'Per-App Planning Template Pack'
for tpl in \
  classpass-planning-template.md \
  smart-seating-planning-template.md \
  prize-board-planning-template.md \
  coin-store-ledger-planning-template.md \
  noise-meter-planning-template.md \
  spelling-studio-planning-template.md \
  classroom-arcade-planning-template.md \
  ua-jobs-management-planning-template.md \
  email-responder-planning-template.md; do
  check_file "${templates_dir}/${tpl}"
  check_doc_contains "${templates_dir}/${tpl}" "planning-only" "planning-only banner in ${tpl}"
  check_doc_contains "${templates_dir}/${tpl}" "blocked" "blocked boundary in ${tpl}"
done

section 'Fake Local Fixtures'
check_file "${fixtures_dir}/README.md"
for fx in \
  example-classpass-labels-001.json \
  example-smart-seating-labels-001.json \
  example-prize-board-labels-001.json; do
  check_file "${fixtures_dir}/${fx}"
  check_doc_contains "${fixtures_dir}/${fx}" "fake_local_planning_only" "fixture classification in ${fx}"
done
check_file "${fixtures_dir}/negative/blocked-student-data-fields.json"

if command -v python3 >/dev/null 2>&1; then
  for f in "${fixtures_dir}"/example-*.json; do
    [[ -f "${f}" ]] || continue
    python3 -m json.tool "${f}" >/dev/null 2>&1 && pass "JSON parses: ${f}" || fail "JSON does not parse: ${f}"
  done
else
  warn 'python3 not available for JSON parse checks'
fi

section 'Fixture Safety (Positive Fixtures)'
for f in "${fixtures_dir}"/example-*.json; do
  [[ -f "${f}" ]] || continue
  if grep -qiE 'https?://|@.*\.(com|edu)|oauth|api_key|iep_' "${f}" 2>/dev/null; then
    fail "positive fixture must not contain URLs/emails/oauth: ${f}"
  else
    pass "positive fixture excludes forbidden URL/email/oauth patterns: $(basename "${f}")"
  fi
  if grep -qiE '"real_student_name"|"grade_value"|"parent_email"' "${f}" 2>/dev/null; then
    fail "positive fixture must not contain real student data field names: ${f}"
  else
    pass "positive fixture excludes forbidden student-data field names: $(basename "${f}")"
  fi
done

section 'No Runtime Classroom App Scripts'
runtime_hits=0
for candidate in scripts/*classroom-utility*app* scripts/*classpass* scripts/*smart-seating*; do
  [[ -e "${candidate}" ]] || continue
  [[ "${candidate}" == *templates-status* ]] && continue
  runtime_hits=1
  fail "runtime classroom app script must not exist: ${candidate}"
done
[[ "${runtime_hits}" == "0" ]] && pass 'no classroom utility runtime app scripts in scripts/'
[[ ! -e scripts/classroom-utility-app-run.sh ]] && pass 'no scripts/classroom-utility-app-run.sh' || fail 'scripts/classroom-utility-app-run.sh must not exist'

grep -Fq -- '--classroom-utility-app-run)' bin/chief-of-staff 2>/dev/null && fail 'CLI must not expose runtime app run command' || pass 'CLI has no classroom utility app run command'
grep -Fq -- '--classroom-utility-generate)' bin/chief-of-staff 2>/dev/null && fail 'CLI must not expose generation command' || pass 'CLI has no classroom utility generate command'

section 'CAL1 Cross-Links'
check_doc_contains docs/classroom-app-lab-prototype-rescue-foundation.md "complete_v1_cal1" "CAL1 foundation closure"
check_file docs/proposals/blocked/classroom-utility-apps-external-ideas.md

section 'Production Registry Parked-State Proof'
if [[ -f "${production_registry_path}" ]] && command -v python3 >/dev/null 2>&1; then
  record_count="$(python3 -c "import json; d=json.load(open('${production_registry_path}')); print(len(d.get('records',[])))" 2>/dev/null || echo 0)"
  [[ "${record_count}" == "1" ]] && pass 'production registry records count exactly 1' || fail "production registry records count must be 1 (got ${record_count})"
  [[ -f "${sentinel}" ]] && pass 'BLOCKED-NO-WRITES.sentinel intact' || fail 'BLOCKED-NO-WRITES.sentinel missing'
  grep -Fq -- '--curriculum-registry-write)' bin/chief-of-staff 2>/dev/null && fail 'chief-of-staff must not implement --curriculum-registry-write handler' || pass 'chief-of-staff has no --curriculum-registry-write handler'
else
  warn 'production registry parked-state proof skipped'
fi

section 'Roadmap and Capability Coherence'
check_doc_contains docs/whole-system-master-roadmap-build-state-report.md "Classroom Utility" "whole-system report classroom utility"
check_doc_contains docs/master-build-roadmap.md "Classroom App Lab" "master build roadmap CAL1"
check_doc_contains docs/build-queue.md "Classroom Utility" "build queue classroom utility"
check_doc_contains docs/teacher-workstation-capability-map.md "Classroom App Lab" "capability map CAL"
check_doc_contains assistant/memory/active-priorities.md "Classroom Utility" "active priorities classroom utility"

section 'CLI, Manifest, and Tests'
bash -n "${BASH_SOURCE[0]}" && pass "bash syntax ok: ${BASH_SOURCE[0]}" || fail "bash syntax failed: status script"
grep -Fq -- '--classroom-utility-templates-status' bin/chief-of-staff && pass 'CLI exposes --classroom-utility-templates-status' || fail 'CLI missing --classroom-utility-templates-status'
grep -Fq -- '"--classroom-utility-templates-status"' assistant/chief-of-staff/v1/command-surface-manifest.json && pass 'manifest lists --classroom-utility-templates-status' || fail 'manifest missing --classroom-utility-templates-status'
check_file tests/classroom-utility-templates-status-test.sh
bash -n tests/classroom-utility-templates-status-test.sh && pass 'bash syntax ok: classroom utility templates test' || fail 'bash syntax failed: templates test'

section 'Negative Non-Activation Assertions'
status_script="${BASH_SOURCE[0]}"
grep -Eq '(^|[;&|[:space:]])curl[[:space:]]' "${status_script}" 2>/dev/null && fail "${status_script} must not shell-invoke curl" || pass "${status_script} does not shell-invoke curl"
grep -Eq '(^|[;&|[:space:]])ollama[[:space:]]' "${status_script}" 2>/dev/null && fail "${status_script} must not shell-invoke ollama" || pass "${status_script} does not shell-invoke ollama"
pass 'no runtime classroom app execution attempted'
pass 'no student data ingestion attempted'
pass 'no network call attempted'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
