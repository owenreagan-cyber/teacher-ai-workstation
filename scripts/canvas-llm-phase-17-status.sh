#!/usr/bin/env bash
set -euo pipefail

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

pass() {
  PASS_COUNT=$((PASS_COUNT + 1))
  echo "PASS: $1"
}

warn() {
  WARN_COUNT=$((WARN_COUNT + 1))
  echo "WARN: $1"
}

fail() {
  FAIL_COUNT=$((FAIL_COUNT + 1))
  echo "FAIL: $1"
}

require_file() {
  local path="$1"
  if [[ -f "$path" ]]; then
    pass "Phase 17 file exists: $path"
  else
    fail "Missing Phase 17 file: $path"
  fi
}

require_executable() {
  local path="$1"
  if [[ -x "$path" ]]; then
    pass "Phase 17 executable exists: $path"
  else
    fail "Missing or non-executable Phase 17 script: $path"
  fi
}

require_contains() {
  local path="$1"
  local pattern="$2"
  local description="$3"
  if grep -Fq "$pattern" "$path"; then
    pass "$description"
  else
    fail "$description"
  fi
}

REPORT="docs/programs/canvas-llm/canvas-phase-17-preview-setup-action-packet.md"
ANALYZER="scripts/canvas-llm-phase-17-setup-action-packet.py"
LOCAL_ROOT=".local/canvas-llm/approved-course-metadata"
LOCAL_MANIFEST="${LOCAL_ROOT}/manifest.json"
PHASE16_REPORT="docs/programs/canvas-llm/canvas-phase-16-preview-relationship-map.md"

echo "Canvas LLM Phase 17: Preview-Only Canvas Setup Action Packet"
echo "----------------------------------------"

require_executable "$ANALYZER"
require_file "$REPORT"
require_file "$PHASE16_REPORT"
require_file "docs/programs/canvas-llm/canvas-llm-phase-plan.md"

echo
echo "Local Phase 14B Metadata Source Guard"
echo "----------------------------------------"
if [[ -f "$LOCAL_MANIFEST" ]]; then
  pass "Phase 14B local metadata manifest exists"
else
  fail "Phase 14B local metadata manifest is missing"
fi

if git check-ignore -q "$LOCAL_ROOT"; then
  pass "Phase 14B local metadata root is ignored"
else
  fail "Phase 14B local metadata root is not ignored"
fi

if [[ -z "$(git ls-files .local/canvas-llm)" ]]; then
  pass ".local Canvas metadata is not tracked"
else
  fail ".local Canvas metadata is tracked"
fi

echo
echo "Analyzer Regeneration Proof"
echo "----------------------------------------"
if analyzer_output="$("$ANALYZER")"; then
  echo "$analyzer_output"
  pass "Phase 17 analyzer regenerated report successfully"
else
  echo "$analyzer_output"
  fail "Phase 17 analyzer failed"
fi

echo
echo "Report Content Checks"
echo "----------------------------------------"
require_contains "$REPORT" "Setup Packet Summary" "Report includes setup packet summary"
require_contains "$REPORT" "| Math | highest | 19428 | 26404 |" "Report includes Math setup packet"
require_contains "$REPORT" "| Reading/Spelling | highest | 19419 | 26442 |" "Report includes Reading/Spelling setup packet"
require_contains "$REPORT" "| Language Arts | high | 19426 | 26495 |" "Report includes Language Arts setup packet"
require_contains "$REPORT" "| History | medium | 21934 | 26493 |" "Report includes History setup packet"
require_contains "$REPORT" "| Science | medium | 21970 | 26496 |" "Report includes Science setup packet"
require_contains "$REPORT" "| Homeroom/Newsletter | high | 19424 | 26427 |" "Report includes Homeroom/newsletter setup packet"
require_contains "$REPORT" "Subject-by-Subject Preview Setup Actions" "Report includes subject-by-subject setup actions"
require_contains "$REPORT" "Cross-Course Setup Order" "Report includes cross-course setup order"
require_contains "$REPORT" "Folder / File Grouping Priorities" "Report includes folder/file grouping priorities"
require_contains "$REPORT" "Module Shell Priorities" "Report includes module shell priorities"
require_contains "$REPORT" "Page Placement Priorities" "Report includes page placement priorities"
require_contains "$REPORT" "Assignment Relationship References" "Report includes assignment relationship references"
require_contains "$REPORT" "Homeroom / Newsletter Packet" "Report includes Homeroom/newsletter packet"
require_contains "$REPORT" "Canvas LLM Phase 18: Canvas Setup Write Gate Readiness Review" "Report recommends Phase 18"

echo
echo "Safety Content Checks"
echo "----------------------------------------"
require_contains "$REPORT" "Canvas API calls" "Report blocks Canvas API calls"
require_contains "$REPORT" "Live fetches" "Report blocks live fetches"
require_contains "$REPORT" "Canvas writes" "Report blocks Canvas writes"
require_contains "$REPORT" "Canvas renames" "Report blocks Canvas renames"
require_contains "$REPORT" "Canvas moves" "Report blocks Canvas moves"
require_contains "$REPORT" "Canvas uploads" "Report blocks Canvas uploads"
require_contains "$REPORT" "Canvas deletes" "Report blocks Canvas deletes"
require_contains "$REPORT" "Canvas copy/import actions" "Report blocks Canvas copy/import actions"
require_contains "$REPORT" "Canvas publish changes" "Report blocks Canvas publish changes"
require_contains "$REPORT" "File downloads" "Report blocks file downloads"
require_contains "$REPORT" "File content reads" "Report blocks file content reads"
require_contains "$REPORT" "Page body ingestion" "Report blocks page body ingestion"
require_contains "$REPORT" "Announcement body ingestion" "Report blocks announcement body ingestion"
require_contains "$REPORT" "Assignment body ingestion" "Report blocks assignment body ingestion"
require_contains "$REPORT" "Student data access" "Report blocks student data access"
require_contains "$REPORT" "Tracked school Canvas URL" "Report blocks tracked school Canvas URL"
require_contains "$REPORT" "Tracked tokens" "Report blocks tracked tokens"
require_contains "$REPORT" 'Committed `.local/...` raw metadata' "Report blocks committed raw metadata"

echo
echo "Tracked Token And URL Guards"
echo "----------------------------------------"
if grep -RInE 'canvas\.instructure\.com|Authorization: Bearer [A-Za-z0-9]|CANVAS_API_TOKEN=.*[A-Za-z0-9_=-]{8,}|access_token["'\''"]?[[:space:]]*[:=][[:space:]]*["'\''"]?[A-Za-z0-9_=-]{8,}' \
  "$REPORT" "$ANALYZER" >/tmp/canvas_phase_17_secret_scan.txt 2>/dev/null; then
  cat /tmp/canvas_phase_17_secret_scan.txt
  fail "Possible tracked Canvas URL/token pattern found in Phase 17 report/analyzer"
else
  pass "No tracked school Canvas URL/token pattern found in Phase 17 report/analyzer"
fi
rm -f /tmp/canvas_phase_17_secret_scan.txt

echo
echo "Phase 16 Continuity"
echo "----------------------------------------"
if phase16_output="$(bin/chief-of-staff --canvas-llm-phase-16-status)"; then
  echo "$phase16_output" | tail -35
  if echo "$phase16_output" | grep -q "FAIL: 0"; then
    pass "Phase 16 status still passes"
  else
    fail "Phase 16 status did not report FAIL: 0"
  fi
else
  echo "$phase16_output"
  fail "Phase 16 status command failed"
fi

echo
echo "Phase 14B Continuity"
echo "----------------------------------------"
if phase14b_output="$(bin/chief-of-staff --canvas-llm-phase-14b-status)"; then
  echo "$phase14b_output" | tail -70
  if echo "$phase14b_output" | grep -q "FAIL: 0"; then
    pass "Phase 14B status still passes"
  else
    fail "Phase 14B status did not report FAIL: 0"
  fi
else
  echo "$phase14b_output"
  fail "Phase 14B status command failed"
fi

echo
echo "Summary"
echo "----------------------------------------"
echo "PASS: ${PASS_COUNT}"
echo "WARN: ${WARN_COUNT}"
echo "FAIL: ${FAIL_COUNT}"

if [[ "$FAIL_COUNT" -ne 0 ]]; then
  exit 1
fi
