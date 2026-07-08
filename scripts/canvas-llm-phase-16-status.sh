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
    pass "Phase 16 file exists: $path"
  else
    fail "Missing Phase 16 file: $path"
  fi
}

require_executable() {
  local path="$1"
  if [[ -x "$path" ]]; then
    pass "Phase 16 executable exists: $path"
  else
    fail "Missing or non-executable Phase 16 script: $path"
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

REPORT="docs/programs/canvas-llm/canvas-phase-16-preview-relationship-map.md"
ANALYZER="scripts/canvas-llm-phase-16-relationship-map.py"
LOCAL_ROOT=".local/canvas-llm/approved-course-metadata"
LOCAL_MANIFEST="${LOCAL_ROOT}/manifest.json"

echo "Canvas LLM Phase 16: Preview-Only Canvas Module/File/Page Relationship Map"
echo "----------------------------------------"

require_executable "$ANALYZER"
require_file "$REPORT"
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
  pass "Phase 16 analyzer regenerated report successfully"
else
  echo "$analyzer_output"
  fail "Phase 16 analyzer failed"
fi

echo
echo "Report Content Checks"
echo "----------------------------------------"
require_contains "$REPORT" "Preview Relationship Map" "Report includes preview relationship map"
require_contains "$REPORT" "| Math | 19428 | 26404 |" "Report maps Math template to current target"
require_contains "$REPORT" "| Reading/Spelling | 19419 | 26442 |" "Report maps Reading/Spelling template to current target"
require_contains "$REPORT" "| Language Arts | 19426 | 26495 |" "Report maps Language Arts template to current target"
require_contains "$REPORT" "| History | 21934 | 26493 |" "Report maps History template to current target"
require_contains "$REPORT" "| Science | 21970 | 26496 |" "Report maps Science template to current target"
require_contains "$REPORT" "| Homeroom/Newsletter | 19424 | 26427 |" "Report maps Homeroom/newsletter template to current target"
require_contains "$REPORT" "Current Target Course Setup Order Preview" "Report includes setup order preview"
require_contains "$REPORT" "Homeroom/newsletter mapping is previewed separately" "Report separates Homeroom/newsletter mapping"
require_contains "$REPORT" "Canvas LLM Phase 17: Preview-Only Canvas Setup Action Packet" "Report recommends Phase 17"

echo
echo "Safety Content Checks"
echo "----------------------------------------"
require_contains "$REPORT" "Phase 16 does not fetch from Canvas." "Report blocks Canvas fetch"
require_contains "$REPORT" "Phase 16 does not write to Canvas." "Report blocks Canvas writes"
require_contains "$REPORT" "Phase 16 does not rename, move, upload, delete, publish, or copy Canvas objects." "Report blocks Canvas object mutation"
require_contains "$REPORT" "Phase 16 does not download files." "Report blocks file downloads"
require_contains "$REPORT" "Phase 16 does not read file contents." "Report blocks file content reads"
require_contains "$REPORT" "Phase 16 does not ingest page, announcement, assignment, or file bodies." "Report blocks body ingestion"
require_contains "$REPORT" "Phase 16 does not access student data" "Report blocks student data"
require_contains "$REPORT" "Phase 16 does not track the school Canvas URL or tokens." "Report blocks tracked URL/tokens"

echo
echo "Tracked Token And URL Guards"
echo "----------------------------------------"
if grep -RInE 'canvas\.instructure\.com|Authorization: Bearer [A-Za-z0-9]|CANVAS_API_TOKEN=.*[A-Za-z0-9_=-]{8,}|access_token["'\''"]?[[:space:]]*[:=][[:space:]]*["'\''"]?[A-Za-z0-9_=-]{8,}' \
  "$REPORT" "$ANALYZER" >/tmp/canvas_phase_16_secret_scan.txt 2>/dev/null; then
  cat /tmp/canvas_phase_16_secret_scan.txt
  fail "Possible tracked Canvas URL/token pattern found in Phase 16 report/analyzer"
else
  pass "No tracked school Canvas URL/token pattern found in Phase 16 report/analyzer"
fi
rm -f /tmp/canvas_phase_16_secret_scan.txt

echo
echo "Phase 15 Continuity"
echo "----------------------------------------"
if phase15_output="$(bin/chief-of-staff --canvas-llm-phase-15-status)"; then
  echo "$phase15_output" | tail -35
  if echo "$phase15_output" | grep -q "FAIL: 0"; then
    pass "Phase 15 status still passes"
  else
    fail "Phase 15 status did not report FAIL: 0"
  fi
else
  echo "$phase15_output"
  fail "Phase 15 status command failed"
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
