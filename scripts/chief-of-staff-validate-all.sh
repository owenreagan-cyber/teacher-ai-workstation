#!/usr/bin/env bash
# Read-only validation orchestration. Calls existing validators; does not replace them.
#
# Execution model (fast by default):
#   validate-all -> foundation/status checks -> optional smoke (COS_VALIDATE_INCLUDE_SMOKE=1)
#   Must never call proof-run or chief-of-staff-v1-operating-test.sh.
#
# Environment:
#   COS_VALIDATE_INCLUDE_SMOKE=1  Include tests/smoke-chief-of-staff-cli.sh (slow; off by default).
#   COS_VALIDATE_INCLUDE_PHASE1=1   Include scripts/phase-1-status.sh (slow; off by default).
#   COS_VALIDATE_ALREADY_RUNNING    Set internally; nested validate-all fails immediately.
set -euo pipefail

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0
TRACK_FAILURE=0
VALIDATE_TMP=""

pass() {
  PASS_COUNT=$((PASS_COUNT + 1))
  printf 'PASS: %s\n' "$1"
}

warn() {
  WARN_COUNT=$((WARN_COUNT + 1))
  printf 'WARN: %s\n' "$1"
}

fail() {
  FAIL_COUNT=$((FAIL_COUNT + 1))
  TRACK_FAILURE=1
  printf 'FAIL: %s\n' "$1"
}

section() {
  printf '\n%s\n' "$1"
  printf '%s\n' '----------------------------------------'
}

cleanup() {
  if [[ -n "${VALIDATE_TMP}" ]]; then
    rm -f "${VALIDATE_TMP}"
  fi
}
trap cleanup EXIT

run_track() {
  local label="$1"
  local script="$2"
  shift 2
  if [[ ! -f "${script}" ]]; then
    fail "${label} script missing: ${script}"
    return
  fi
  local output result fail_count
  output="$("${script}" "$@" 2>&1)" || result=$?
  result="${result:-0}"
  fail_count="$(printf '%s\n' "${output}" | awk '/^Summary$/{p=1; next} p && /^FAIL:/{v=$2} END{print v+0}')"
  if [[ "${result}" != "0" || "${fail_count}" -gt 0 ]]; then
    printf '%s\n' "${output}" | tail -20
    fail "${label} failed"
  else
    pass "${label} completed"
  fi
}

run_test() {
  local label="$1"
  local script="$2"
  if [[ ! -f "${script}" ]]; then
    fail "${label} test missing: ${script}"
    return
  fi
  VALIDATE_TMP="$(mktemp "${TMPDIR:-/tmp}/chief-of-staff-validate-all-test.XXXXXX")"
  if bash "${script}" >"${VALIDATE_TMP}" 2>&1; then
    pass "${label} passed"
  else
    cat "${VALIDATE_TMP}"
    fail "${label} failed"
  fi
  rm -f "${VALIDATE_TMP}"
  VALIDATE_TMP=""
}

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "${repo_root}" ]]; then
  repo_root="$(cd "${script_dir}/.." && pwd -P)"
fi
cd "${repo_root}"

if [[ -n "${COS_VALIDATE_ALREADY_RUNNING:-}" ]]; then
  printf 'FAIL: recursive validate-all detected\n'
  exit 1
fi
export COS_VALIDATE_ALREADY_RUNNING=1

section 'Chief of Staff Validate All'
cat <<'EOF'
Status: read-only validation orchestration
Network calls: no
Lesson generation: no
Replaces validators: no
EOF

run_track "Cursor Workflow" scripts/cursor-workflow-status.sh
run_track "Cursor Operating Modes" scripts/cursor-operating-modes-status.sh
run_track "Autonomous Build Engine" scripts/autonomous-build-engine-status.sh
run_track "Governance Lane" scripts/governance-lane-status.sh
run_track "Chief of Staff Command Index v1" scripts/chief-of-staff-command-index-v1-status.sh
run_track "Chief of Staff v1 Agent Core" scripts/chief-of-staff-v1-foundation-status.sh
run_track "Teacher Workstation Health Monitor" scripts/teacher-workstation-health-status.sh
run_track "Teacher Workstation System Updater" scripts/teacher-workstation-system-updater-status.sh
run_track "Workstation Ops Lane" scripts/workstation-ops-lane-status.sh
run_track "AI Tool Routing" scripts/ai-tool-routing-status.sh
run_track "Local LLM Workstation" scripts/local-llm-workstation-status.sh
run_track "Mac Workstation Experience" scripts/mac-workstation-experience-status.sh
run_track "Widget and Shortcut Builder" scripts/widget-shortcut-builder-status.sh
run_track "Vibe / Wallpaper / Widgets Planning Gate" scripts/vibe-wallpaper-widgets-planning-status.sh
run_track "Classroom App Lab" scripts/classroom-app-lab-status.sh
run_track "Classroom Utility Templates" scripts/classroom-utility-templates-status.sh
run_track "Lovable Classroom App Builder" scripts/lovable-classroom-app-builder-status.sh
run_track "3D Builder Workshop Agent" scripts/3d-builder-workshop-agent-status.sh
run_track "Chief of Staff Next Action" scripts/chief-of-staff-next-action.sh
run_track "Curriculum Registry v0" scripts/curriculum-registry-v0-status.sh
run_track "Curriculum Output Contract v0" scripts/curriculum-output-contract-v0-status.sh
run_track "Curriculum Binding v0" scripts/curriculum-binding-v0-status.sh
run_track "Curriculum Builder Foundation" scripts/curriculum-builder-foundation-status.sh
run_track "Curriculum Builder Contract Schemas" scripts/curriculum-builder-contract-schemas-status.sh
run_track "Curriculum Builder Registry v0.2 Dry-Run" scripts/curriculum-builder-registry-v0-2-status.sh
run_track "Curriculum Builder Registry v0.2 Local Records" scripts/curriculum-builder-registry-v0-2-local-records-status.sh
run_track "Curriculum Builder Registry v0.2 Renderer" scripts/curriculum-builder-registry-v0-2-renderer-status.sh
run_track "Curriculum Builder Registry v0.2 Retrieval" scripts/curriculum-builder-registry-v0-2-retrieval-status.sh
run_track "Curriculum Builder Production Registry Planning" scripts/curriculum-builder-production-registry-planning-status.sh
run_track "Production Registry Governance" scripts/curriculum-builder-production-registry-governance-status.sh
run_track "Owen Production Registry Checklist" scripts/curriculum-builder-production-registry-owen-checklist-status.sh
run_track "Production Registry Phase 2 Preflight" scripts/curriculum-builder-production-registry-phase-2-preflight-status.sh
run_track "Production Registry Metadata Boundary" scripts/curriculum-builder-production-registry-metadata-boundary-status.sh
run_track "Production Registry Empty File" scripts/curriculum-builder-production-registry-empty-file-status.sh
run_track "Production Registry Metadata Pilot Plan" scripts/curriculum-builder-production-registry-metadata-pilot-plan-status.sh
run_track "Production Registry First Record" scripts/curriculum-builder-production-registry-first-record-status.sh
run_track "Production Registry Next Gate" scripts/curriculum-builder-production-registry-next-gate-status.sh
run_track "Whole-System Master Roadmap" scripts/whole-system-master-roadmap-status.sh
run_track "Whole-System Coherence" scripts/whole-system-coherence-status.sh
run_track "Agent Builder Governance" scripts/agent-builder-compatibility-governance-status.sh
run_track "Owen Decision Packets" scripts/owen-architecture-decision-packets-status.sh
run_track "App Ecosystem Inventory" scripts/app-ecosystem-inventory-status.sh
run_track "Timer Stopwatch Planning" scripts/classroom-timer-stopwatch-planning-status.sh
run_track "Timer Stopwatch Runtime" scripts/classroom-timer-stopwatch-runtime-status.sh
run_track "App Ecosystem Planning Lanes" scripts/app-ecosystem-planning-lanes-status.sh
run_track "App Runtime Approval Gate" scripts/app-runtime-approval-gate-status.sh
run_track "Presentation Engine Renderer Foundation" scripts/presentation-engine-renderer-foundation-status.sh
run_track "Teacher Knowledge Vault M0 Architecture Freeze" scripts/teacher-knowledge-vault-m0-architecture-freeze-status.sh
run_track "Gemini Discovery Classification Intake" scripts/gemini-discovery-classification-intake-status.sh
run_track "Markdown Frontmatter Planning" scripts/markdown-frontmatter-planning-status.sh
run_track "Curriculum Source Readiness" scripts/curriculum-source-readiness-status.sh
run_track "Curriculum Builder Registry Lane" scripts/curriculum-builder-registry-lane-status.sh
run_track "Curriculum Builder Registry A4-A7 Fixture Schema" scripts/curriculum-builder-registry-a4-a7-fixture-schema-status.sh

section 'Direct Validators'
run_track "Registry v0 Validator" scripts/curriculum-registry-v0-validator.sh
run_track "Registry v0.2 Dry-Run Validator" scripts/curriculum-builder-registry-v0-2-dry-run.sh
run_track "Registry v0.2 Local Records Validator" scripts/curriculum-builder-registry-v0-2-local-records-validate.sh
run_track "Output Contract v0 Validator" scripts/curriculum-output-contract-v0-validator.sh
run_track "Binding v0 Validator" scripts/curriculum-binding-v0-validator.sh

section 'Test Suites'
run_test "Curriculum Contract Suite v0" tests/curriculum-contract-suite-v0-test.sh
run_test "Vibe / Wallpaper / Widgets Planning Status" tests/vibe-wallpaper-widgets-planning-status-test.sh
if [[ "${COS_VALIDATE_INCLUDE_SMOKE:-}" == "1" ]]; then
  run_test "Smoke Chief of Staff CLI" tests/smoke-chief-of-staff-cli.sh
else
  pass "smoke CLI skipped (set COS_VALIDATE_INCLUDE_SMOKE=1 to include)"
fi

if [[ "${COS_VALIDATE_INCLUDE_PHASE1:-}" == "1" ]]; then
  section 'Phase 1 Status (optional)'
  run_track "Phase 1 Status" scripts/phase-1-status.sh
else
  pass "phase-1 status skipped (set COS_VALIDATE_INCLUDE_PHASE1=1 to include)"
fi

section 'Summary'
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"

if [[ "${TRACK_FAILURE}" -gt 0 ]]; then
  exit 1
fi
exit 0
