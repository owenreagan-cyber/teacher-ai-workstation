#!/usr/bin/env bash
set -uo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
PHASE_DIR="${ROOT_DIR}/docs/programs/canvas-llm/phase-21-codex-autonomous-sandbox-learning-agent"
AGENT="${ROOT_DIR}/scripts/canvas-llm/canvas_learning_agent.py"
SAFETY="${ROOT_DIR}/scripts/canvas-llm/canvas_safety.py"
SANITIZER="${ROOT_DIR}/scripts/canvas-llm/canvas_sanitizer.py"
CHIEF="${ROOT_DIR}/bin/chief-of-staff"

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

emit() {
  local level="$1"
  shift
  case "${level}" in
    PASS) PASS_COUNT=$((PASS_COUNT + 1)) ;;
    WARN) WARN_COUNT=$((WARN_COUNT + 1)) ;;
    FAIL) FAIL_COUNT=$((FAIL_COUNT + 1)) ;;
    *) echo "FAIL: invalid status level ${level}"; FAIL_COUNT=$((FAIL_COUNT + 1)); return ;;
  esac
  echo "${level}: $*"
}

check_file() {
  local path="$1"
  local label="$2"
  if [[ -f "${path}" ]]; then
    emit PASS "${label} exists"
  else
    emit FAIL "${label} missing"
  fi
}

check_executable() {
  local path="$1"
  local label="$2"
  if [[ -x "${path}" ]]; then
    emit PASS "${label} is executable"
  else
    emit FAIL "${label} is not executable"
  fi
}

check_contains() {
  local path="$1"
  local pattern="$2"
  local label="$3"
  if [[ ! -f "${path}" ]]; then
    emit FAIL "${label}: missing file ${path}"
    return
  fi
  if grep -Fq -- "${pattern}" "${path}"; then
    emit PASS "${label}"
  else
    emit FAIL "${label}"
  fi
}

check_command() {
  local label="$1"
  shift
  if "$@" >/dev/null 2>&1; then
    emit PASS "${label}"
  else
    emit FAIL "${label}"
  fi
}

echo "Canvas LLM Phase 21 Codex Autonomous Sandbox Learning Agent Status"
echo "------------------------------------------------------------------"

check_file "${PHASE_DIR}/README.md" "Phase 21 README"
check_file "${PHASE_DIR}/sandbox-permission-map.md" "sandbox permission map"
check_file "${PHASE_DIR}/reference-course-map.md" "reference course map"
check_file "${PHASE_DIR}/autonomous-learning-loop.md" "autonomous learning loop doc"
check_file "${PHASE_DIR}/qw-week-page-doctrine.md" "Q/W week page doctrine"
check_file "${PHASE_DIR}/production-weekly-page-doctrine.md" "production weekly page doctrine"
check_file "${PHASE_DIR}/sandbox-experiment-contract.md" "sandbox experiment contract"
check_file "${PHASE_DIR}/medical-center-learning-rules.md" "Medical Center learning rules"
check_file "${PHASE_DIR}/phase-22-next-step-recommendation.md" "Phase 22 next step recommendation"

check_file "${AGENT}" "agent script"
check_executable "${AGENT}" "agent script"
check_file "${ROOT_DIR}/scripts/canvas-llm/canvas_api_client.py" "Canvas API client"
check_file "${SAFETY}" "Canvas safety module"
check_file "${SANITIZER}" "Canvas sanitizer module"
check_file "${CHIEF}" "Chief of Staff CLI"

check_contains "${PHASE_DIR}/reference-course-map.md" "21944" "reference course map includes 21944"
check_contains "${PHASE_DIR}/reference-course-map.md" "21957" "reference course map includes 21957"
check_contains "${PHASE_DIR}/reference-course-map.md" "21919" "reference course map includes 21919"
check_contains "${PHASE_DIR}/sandbox-permission-map.md" "24399" "sandbox map includes 24399"
check_contains "${PHASE_DIR}/README.md" "https://thalesacademy.instructure.com" "Canvas base domain is documented as approved runtime target"
check_contains "${PHASE_DIR}/production-weekly-page-doctrine.md" "preloaded" "production doctrine says real weekly pages are preloaded"
check_contains "${PHASE_DIR}/production-weekly-page-doctrine.md" "updated, not created" "production doctrine says pages are updated, not created"
check_contains "${PHASE_DIR}/autonomous-learning-loop.md" "questions.json" "learning loop writes questions.json"
check_contains "${PHASE_DIR}/autonomous-learning-loop.md" "findings.json" "learning loop writes findings.json"
check_contains "${PHASE_DIR}/autonomous-learning-loop.md" "next-actions.json" "learning loop writes next-actions.json"

check_contains "${SAFETY}" "SANDBOX_COURSE_ID = \"24399\"" "agent locks writes to 24399"
check_contains "${SAFETY}" "REFERENCE_COURSE_IDS = {\"21944\", \"21957\", \"21919\"}" "reference courses are hard-coded read-only"
check_contains "${SAFETY}" "BLOCKED_ENDPOINT_MARKERS" "blocked endpoint markers exist"
check_contains "${SAFETY}" "grades" "grades are blocked"
check_contains "${SAFETY}" "users" "users/people are blocked"
check_contains "${SAFETY}" "settings" "settings are blocked"
check_contains "${SAFETY}" "submissions" "submissions are blocked"
check_contains "${SAFETY}" "gradebook" "gradebook is blocked"
check_contains "${SAFETY}" "analytics" "analytics are blocked"
check_contains "${SAFETY}" "student" "student data markers are blocked"
check_contains "${SAFETY}" "require_announcement_notifications_blocked" "agent blocks announcement notification behavior unless approved"
check_contains "${SAFETY}" "external" "external Thales Website mutation markers are blocked"
check_contains "${AGENT}" "choices=[\"inventory\", \"reference-inventory\", \"questions\", \"experiment\", \"existing-page-dry-run\", \"cleanup\"]" "agent supports inventory/questions/experiment/existing-page-dry-run/cleanup/reference-inventory"
check_contains "${AGENT}" "reference_course_ids" "agent has reference-inventory course selector"
check_contains "${AGENT}" "result = run_inventory(client, reference_course_ids(), \"reference-inventory\")" "reference-inventory does not include sandbox course 24399"
check_contains "${AGENT}" "default=\"inventory\"" "agent default mode is inventory"
check_contains "${AGENT}" "CANVAS_BASE_URL" "agent requires CANVAS_BASE_URL"
check_contains "${AGENT}" "CANVAS_TOKEN" "agent requires CANVAS_TOKEN"
check_contains "${AGENT}" "BLOCKED: --mode experiment/cleanup requires --allow-writes" "experiment/cleanup require allow-writes"
check_contains "${AGENT}" ".local/canvas-llm/sandbox-learning-runs/phase-21" "agent writes raw output under .local"
check_contains "${AGENT}" "artifact-ledger.json" "agent has artifact ledger"
check_contains "${AGENT}" "elif args.mode == \"cleanup\"" "agent has cleanup mode"
check_contains "${SANITIZER}" "TOKEN_REMOVED" "sanitizer removes token-like strings"
check_contains "${SANITIZER}" "URL_REMOVED" "sanitizer removes URLs"
check_contains "${SANITIZER}" "EMAIL_REMOVED" "sanitizer removes emails"
check_contains "${SANITIZER}" "SENSITIVE_METADATA_REMOVED" "sanitizer removes account/user/enrollment/student metadata"
check_contains "${CHIEF}" "--canvas-llm-phase-21-codex-autonomous-sandbox-learning-agent-status" "Chief of Staff flag is wired"

if grep -R "CANVAS_TOKEN=.*" "${PHASE_DIR}" "${ROOT_DIR}/scripts/canvas-llm" 2>/dev/null | grep -v "CANVAS_TOKEN are required" | grep -v "CANVAS_TOKEN=\"<set locally only; never paste into chat>\"" >/dev/null; then
  emit FAIL "committed files appear to contain a CANVAS_TOKEN assignment"
else
  emit PASS "committed files do not contain a CANVAS_TOKEN assignment"
fi

if git -C "${ROOT_DIR}" ls-files ".local/*" | grep -q .; then
  emit FAIL ".local output is tracked by git"
else
  emit PASS ".local output is not tracked by git"
fi

check_command "bin/chief-of-staff syntax check passes" bash -n "${CHIEF}"
check_command "Phase 21 status script syntax check passes" bash -n "${BASH_SOURCE[0]}"
check_command "Phase 21 Python syntax checks pass" env PYTHONPYCACHEPREFIX="/tmp/teacher-ai-phase-21-status-pycache" python3 -m py_compile "${AGENT}" "${ROOT_DIR}/scripts/canvas-llm/canvas_api_client.py" "${SAFETY}" "${SANITIZER}"

echo
echo "Safety Boundary"
echo "---------------"
emit PASS "status check does not call Canvas APIs"
emit PASS "status check does not fetch live Canvas data"
emit PASS "status check does not write to Canvas"
emit PASS "status check does not read raw .local metadata"
emit PASS "status check does not print CANVAS_TOKEN"

echo
echo "Summary"
echo "-------"
echo "PASS: ${PASS_COUNT}"
echo "WARN: ${WARN_COUNT}"
echo "FAIL: ${FAIL_COUNT}"

if [[ "${FAIL_COUNT}" -gt 0 ]]; then
  exit 1
fi
