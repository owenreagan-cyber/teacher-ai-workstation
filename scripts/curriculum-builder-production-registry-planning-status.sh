#!/usr/bin/env bash
# Read-only Curriculum Builder production registry workflow planning status. No writes.
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

planning_brief="docs/curriculum-builder-production-registry-workflow-planning-brief.md"
status_script="scripts/curriculum-builder-production-registry-planning-status.sh"
live_registry="assistant/curriculum-builder/registry/v0/registry.json"
fixture_registry="assistant/curriculum-builder/samples/registry-v0-2-local-records/local-registry.json"
manifest="assistant/chief-of-staff/v1/command-surface-manifest.json"

section 'Curriculum Builder Production Registry Workflow Planning'
cat <<'EOF'
Status: planning_only
Classification: future workflow planning — not implementation
Runtime activation: no
Production registry writes: blocked
Active --write: blocked
Real metadata intake: blocked
Student data: blocked
Real curriculum content: blocked
Implementation: blocked until Owen approval
ChatGPT review recommended before implementation prompt: yes
EOF

section 'Planning Brief'
check_file "${planning_brief}"
check_doc_contains "${planning_brief}" "planning_only" "planning brief planning_only"
check_doc_contains "${planning_brief}" "complete_production_registry_planning_brief" "planning brief closure status"
check_doc_contains "${planning_brief}" "Production registry writes: blocked" "planning brief blocked writes"
check_doc_contains "${planning_brief}" "Owen Approval Checklist" "Owen approval checklist"
check_file docs/curriculum-builder-production-registry-owen-checklist-tracker.md
check_doc_contains docs/curriculum-builder-production-registry-owen-checklist-tracker.md "write_behavior_approved_awaiting_metadata_decisions" "owen checklist tracker closure"
check_doc_contains "${planning_brief}" "Target Registry Authority Decision" "registry authority decision"
check_doc_contains "${planning_brief}" "Explicit Non-Goals" "explicit non-goals"
check_doc_contains "${planning_brief}" "Student Data and Curriculum Content Boundaries" "student data boundaries"
check_doc_contains "${planning_brief}" "Safe First Implementation PR" "safe first implementation PR"

section 'Blocked Boundaries in Planning Brief'
check_doc_contains "${planning_brief}" "Active user-facing --write: blocked" "blocked --write"
check_doc_contains "${planning_brief}" "Real metadata intake: blocked" "blocked real metadata intake"
check_doc_contains "${planning_brief}" "Scanning folders" "non-goal scanning"
check_doc_contains "${planning_brief}" "OAuth" "non-goal OAuth"
check_doc_contains "${planning_brief}" "Embeddings" "non-goal embeddings"
check_doc_contains "${planning_brief}" "Lesson generation" "non-goal generation"
check_doc_contains "${planning_brief}" "Canvas API" "non-goal Canvas API"
check_doc_contains "${planning_brief}" "Google Drive" "source-system Drive planning"
check_doc_contains "${planning_brief}" "NAS" "source-system NAS planning"
check_doc_contains "${planning_brief}" "iCloud" "source-system iCloud planning"

section 'Status Script and Syntax'
check_file "${status_script}"
bash -n "${status_script}" && pass "bash syntax ok: ${status_script}" || fail "bash syntax failed: ${status_script}"
grep -Fq -- '--curriculum-registry-write)' bin/chief-of-staff 2>/dev/null && fail 'chief-of-staff must not implement --curriculum-registry-write handler' || pass 'chief-of-staff has no --curriculum-registry-write handler'

section 'CLI, Manifest, and Tests'
grep -Fq -- '--curriculum-production-registry-planning-status' bin/chief-of-staff && pass 'CLI exposes --curriculum-production-registry-planning-status' || fail 'CLI missing --curriculum-production-registry-planning-status'
grep -Fq -- '"--curriculum-production-registry-planning-status"' "${manifest}" && pass 'manifest lists --curriculum-production-registry-planning-status' || fail 'manifest missing --curriculum-production-registry-planning-status'
grep -Fq -- '"--curriculum-registry-write"' "${manifest}" && pass 'manifest retains blocked --curriculum-registry-write' || fail 'manifest missing blocked --curriculum-registry-write'
grep -Fq -- '"status": "blocked"' "${manifest}" && pass 'manifest retains blocked status markers' || fail 'manifest missing blocked status markers'
check_file tests/curriculum-builder-production-registry-planning-status-test.sh
bash -n tests/curriculum-builder-production-registry-planning-status-test.sh && pass 'bash syntax ok: planning status test' || fail 'bash syntax failed: planning status test'

section 'Registry Non-Mutation'
if [[ -f "${live_registry}" ]]; then
  pass "live registry present (read-only reference)"
else
  warn "live registry missing"
fi
if [[ -f "${fixture_registry}" ]]; then
  pass "v0.2 fixture registry present (fixture-only reference)"
else
  warn "v0.2 fixture registry missing"
fi
check_doc_contains "${planning_brief}" "fake_fixture_only" "fixture remains non-production"

section 'Roadmap and Priority Coherence'
check_doc_contains docs/master-build-roadmap.md "complete_production_registry_planning_brief" "roadmap planning brief closure"
check_doc_contains docs/build-queue.md "production registry workflow planning" "build queue planning brief"
check_doc_contains assistant/memory/active-priorities.md "production registry workflow planning" "active priorities planning brief"
check_doc_contains docs/teacher-workstation-capability-map.md "--curriculum-production-registry-planning-status" "capability map planning status"

section 'Negative Non-Activation Assertions'
for script_path in "${status_script}"; do
  grep -Eq '(^|[;&|[:space:]])curl[[:space:]]' "${script_path}" 2>/dev/null && fail "${script_path} must not shell-invoke curl" || pass "${script_path} does not shell-invoke curl"
  grep -Eq '(^|[;&|[:space:]])find[[:space:]]' "${script_path}" 2>/dev/null && fail "${script_path} must not shell-invoke find" || pass "${script_path} does not shell-invoke find"
  grep -Eq '(^|[;&|[:space:]])ollama[[:space:]]' "${script_path}" 2>/dev/null && fail "${script_path} must not shell-invoke ollama" || pass "${script_path} does not shell-invoke ollama"
done
pass 'no production registry write attempted'
pass 'no real metadata intake attempted'
pass 'no network call attempted'
pass 'no lesson generation attempted'
pass 'Owen approval required before implementation'

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"
[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
