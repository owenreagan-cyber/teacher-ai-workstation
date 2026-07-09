#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPORT_DIR="$ROOT_DIR/docs/programs/canvas-llm/phase-19a-archaeology"
HANDOFF="$ROOT_DIR/docs/programs/canvas-llm/current-handoff.md"
MEMORY="$ROOT_DIR/docs/programs/canvas-llm/memory/phase-19a-memory.md"

passes=0
warns=0
fails=0

emit() {
  local kind="$1"
  local message="$2"
  printf '%s: %s\n' "$kind" "$message"
  case "$kind" in
    PASS) passes=$((passes + 1)) ;;
    WARN) warns=$((warns + 1)) ;;
    FAIL) fails=$((fails + 1)) ;;
  esac
}

require_file() {
  local path="$1"
  local label="$2"
  if [[ -f "$path" ]]; then
    emit PASS "$label exists"
  else
    emit FAIL "$label is missing: ${path#$ROOT_DIR/}"
  fi
}

require_text() {
  local path="$1"
  local pattern="$2"
  local label="$3"
  if [[ ! -f "$path" ]]; then
    emit FAIL "$label cannot be checked because file is missing: ${path#$ROOT_DIR/}"
    return
  fi

  if grep -Eq "$pattern" "$path"; then
    emit PASS "$label"
  else
    emit FAIL "$label"
  fi
}

echo "Canvas LLM Phase 19A Archaeology Report Status"
echo "----------------------------------------------"

require_file "$HANDOFF" "current handoff"
require_file "$MEMORY" "Phase 19A memory"

for report in \
  source-availability.md \
  owner-canonical-decisions.md \
  legacy-feature-survival-matrix.md \
  business-rules-catalog.md \
  legacy-risks.md \
  unanswered-questions.md \
  future-architecture-recommendation.md
do
  require_file "$REPORT_DIR/$report" "archaeology report $report"
done

require_text "$REPORT_DIR/source-availability.md" "pacing-sync-pilot.*missing|Status: missing" "source availability records missing pacing-sync-pilot evidence"
require_text "$REPORT_DIR/owner-canonical-decisions.md" "SM5" "owner decisions include SM5"
require_text "$REPORT_DIR/owner-canonical-decisions.md" "RM4" "owner decisions include RM4"
require_text "$REPORT_DIR/owner-canonical-decisions.md" "ELA4" "owner decisions include ELA4"
require_text "$REPORT_DIR/owner-canonical-decisions.md" "HIST4" "owner decisions include HIST4"
require_text "$REPORT_DIR/owner-canonical-decisions.md" "SCI4" "owner decisions include SCI4"
require_text "$REPORT_DIR/owner-canonical-decisions.md" "Does Not Count Toward Final Grade" "owner decisions include Study Guide excluded-from-final rule"
require_text "$REPORT_DIR/business-rules-catalog.md" "OWNER_APPROVED" "business rules catalog separates owner-approved rules"
require_text "$REPORT_DIR/legacy-feature-survival-matrix.md" "Reading \\+ Spelling Together Logic|Reading \\+ Spelling Together" "survival matrix includes Reading/Spelling Together"
require_text "$REPORT_DIR/legacy-risks.md" "Direct Canvas mutation functions" "legacy risks include direct Canvas mutation risk"
require_text "$REPORT_DIR/future-architecture-recommendation.md" "Evidence Vault" "architecture recommendation includes Evidence Vault"
require_text "$REPORT_DIR/future-architecture-recommendation.md" "Medical Center" "architecture recommendation includes Medical Center"
require_text "$REPORT_DIR/unanswered-questions.md" "write gate" "unanswered questions include write gate decisions"

require_text "$HANDOFF" "5af1ecd" "handoff references PR #300 baseline"
require_text "$HANDOFF" "Phase 19B" "handoff recommends Phase 19B"
require_text "$MEMORY" "Phase 19A Archaeology Report Update" "memory records archaeology report update"
require_text "$MEMORY" "phase-19a-archaeology" "memory references archaeology report directory"

echo
echo "Safety Boundary"
echo "---------------"
emit PASS "status check is documentation-only"
emit PASS "status check does not call Canvas APIs"
emit PASS "status check does not fetch live Canvas data"
emit PASS "status check does not write to Canvas"
emit PASS "status check does not access student data"
emit PASS "status check does not read raw .local metadata"

echo
echo "Summary"
echo "-------"
echo "PASS: $passes"
echo "WARN: $warns"
echo "FAIL: $fails"

if [[ "$fails" -gt 0 ]]; then
  exit 1
fi
