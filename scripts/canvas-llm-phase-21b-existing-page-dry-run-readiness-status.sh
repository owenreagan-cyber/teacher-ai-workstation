#!/usr/bin/env bash
set -u

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

pass() { echo "PASS: $1"; PASS_COUNT=$((PASS_COUNT + 1)); }
warn() { echo "WARN: $1"; WARN_COUNT=$((WARN_COUNT + 1)); }
fail() { echo "FAIL: $1"; FAIL_COUNT=$((FAIL_COUNT + 1)); }

check_file() {
  local path="$1"
  local label="$2"
  if [ -f "$path" ]; then pass "$label exists"; else fail "$label missing"; fi
}

check_executable() {
  local path="$1"
  local label="$2"
  if [ -x "$path" ]; then pass "$label is executable"; else fail "$label is not executable"; fi
}

check_contains() {
  local path="$1"
  local needle="$2"
  local label="$3"
  if [ ! -f "$path" ]; then
    fail "$label missing file"
    return
  fi
  if grep -Fq -- "$needle" "$path"; then pass "$label"; else fail "$label"; fi
}

echo "Canvas LLM Phase 21B Existing Page Dry-Run Readiness Status"
echo "------------------------------------------------------------"

PHASE_DIR="docs/programs/canvas-llm/phase-21b-existing-page-dry-run-readiness"
HANDOFF_GUARDRAIL="scripts/canvas-llm-handoff-breadcrumb-repair.py"
AGENT="scripts/canvas-llm/canvas_learning_agent.py"

check_file "${PHASE_DIR}/README.md" "Phase 21B README"
check_file "${PHASE_DIR}/dry-run-review.md" "Phase 21B dry-run review"
check_file "${PHASE_DIR}/safety-boundary.md" "Phase 21B safety boundary"

check_file "${HANDOFF_GUARDRAIL}" "handoff breadcrumb guardrail"
check_executable "${HANDOFF_GUARDRAIL}" "handoff breadcrumb guardrail"
check_file "${AGENT}" "Canvas learning agent"

check_contains "${PHASE_DIR}/README.md" "existing-page dry-run mode" "README names existing-page dry-run"
check_contains "${PHASE_DIR}/README.md" "No Canvas write is approved by this phase." "README blocks write approval"
check_contains "${PHASE_DIR}/README.md" "EXISTING_PAGE_DRY_RUN_NEEDS_AGENT_HARDENING" "README records dry-run needs hardening decision"
check_contains "${PHASE_DIR}/README.md" ".local/canvas-llm/sandbox-learning-runs/phase-21/" "README keeps local artifacts ignored"

check_contains "${PHASE_DIR}/dry-run-review.md" 'target sandbox course is exactly `24399`' "dry-run requires exact sandbox target"
check_contains "${PHASE_DIR}/dry-run-review.md" "target page already exists" "dry-run requires existing page"
check_contains "${PHASE_DIR}/dry-run-review.md" "proposed operation is update-preview, not create" "dry-run blocks create operation"
check_contains "${PHASE_DIR}/dry-run-review.md" "no reference course is targeted for writes" "dry-run blocks reference writes"
check_contains "${PHASE_DIR}/dry-run-review.md" "owner approval remains required before any write" "dry-run requires owner approval"
check_contains "${PHASE_DIR}/dry-run-review.md" "WARN: no sandbox QxWy candidate page found" "dry-run review records observed warning"
check_contains "${PHASE_DIR}/dry-run-review.md" "EXISTING_PAGE_DRY_RUN_NEEDS_AGENT_HARDENING" "dry-run review records needs-hardening decision"

check_contains "${PHASE_DIR}/safety-boundary.md" "Phase 21B is dry-run only." "safety boundary says dry-run only"
check_contains "${PHASE_DIR}/safety-boundary.md" "Canvas writes" "safety boundary blocks Canvas writes"
check_contains "${PHASE_DIR}/safety-boundary.md" "--allow-writes" "safety boundary blocks allow-writes"
check_contains "${PHASE_DIR}/safety-boundary.md" "--mode experiment" "safety boundary blocks experiment mode"
check_contains "${PHASE_DIR}/safety-boundary.md" "student data" "safety boundary blocks student data"
check_contains "${PHASE_DIR}/safety-boundary.md" "CANVAS_TOKEN" "safety boundary protects token"

check_contains "${AGENT}" "existing-page-dry-run" "agent supports existing-page-dry-run"
check_contains "${AGENT}" "--allow-writes" "agent has allow-writes gate"
check_contains "${AGENT}" "24399" "agent includes sandbox 24399"

if python3 "${HANDOFF_GUARDRAIL}" --check >/tmp/canvas-llm-phase-21b-guardrail-check.txt 2>&1; then
  pass "handoff breadcrumb guardrail check passes"
else
  cat /tmp/canvas-llm-phase-21b-guardrail-check.txt
  fail "handoff breadcrumb guardrail check fails"
fi

if git ls-files .local | grep -q .; then
  fail ".local output is tracked by git"
else
  pass ".local output is not tracked by git"
fi

TOKEN_ASSIGNMENT_SCAN="/tmp/canvas-llm-phase-21b-token-assignment-scan.txt"

git grep -n -E '(^|[[:space:]])(export[[:space:]]+)?CANVAS_TOKEN=' -- docs scripts bin \
  ':!scripts/canvas-llm-phase-21b-existing-page-dry-run-readiness-status.sh' \
  >"${TOKEN_ASSIGNMENT_SCAN}" 2>/dev/null || true

if grep -v "CANVAS_TOKEN is" "${TOKEN_ASSIGNMENT_SCAN}" | grep -v "CANVAS_TOKEN must" | grep -q .; then
  cat "${TOKEN_ASSIGNMENT_SCAN}"
  fail "committed files contain a CANVAS_TOKEN assignment"
else
  pass "committed files do not contain a CANVAS_TOKEN assignment"
fi

echo
echo "Safety Boundary"
echo "---------------"
pass "status check does not call Canvas APIs"
pass "status check does not fetch live Canvas data"
pass "status check does not write to Canvas"
pass "status check does not read raw .local metadata"
pass "status check does not print CANVAS_TOKEN"

echo
echo "Summary"
echo "-------"
echo "PASS: ${PASS_COUNT}"
echo "WARN: ${WARN_COUNT}"
echo "FAIL: ${FAIL_COUNT}"

if [ "${FAIL_COUNT}" -ne 0 ]; then exit 1; fi
