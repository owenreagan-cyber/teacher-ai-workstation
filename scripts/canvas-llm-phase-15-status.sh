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
    pass "Phase 15 file exists: $path"
  else
    fail "Missing Phase 15 file: $path"
  fi
}

require_executable() {
  local path="$1"
  if [[ -x "$path" ]]; then
    pass "Phase 15 executable exists: $path"
  else
    fail "Missing or non-executable Phase 15 script: $path"
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

REPORT="docs/programs/canvas-llm/canvas-phase-15-readiness-relationship-report.md"
ANALYZER="scripts/canvas-llm-phase-15-readiness-report.py"
LOCAL_MANIFEST=".local/canvas-llm/approved-course-metadata/manifest.json"

echo "Canvas LLM Phase 15: Historical-to-Current Readiness and Relationship Report"
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

if git check-ignore -q .local/canvas-llm/approved-course-metadata; then
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
  pass "Phase 15 analyzer regenerated report successfully"
else
  echo "$analyzer_output"
  fail "Phase 15 analyzer failed"
fi

echo
echo "Report Content Checks"
echo "----------------------------------------"
require_contains "$REPORT" "Fetched course count: \`19\`" "Report proves 19 fetched courses"
require_contains "$REPORT" "Current 2026-2027 courses exist but are mostly empty shells." "Report states current courses are mostly empty shells"
require_contains "$REPORT" "Historical 2024-2025 and 2025-2026 courses contain enough files" "Report states historical courses are rich enough for planning"
require_contains "$REPORT" "Homeroom/newsletter courses are included but kept separate" "Report separates Homeroom/newsletter from academic scoring"
require_contains "$REPORT" "| Math | 19428 | 2024-2025" "Report identifies Math template"
require_contains "$REPORT" "| Reading/Spelling | 19419 | 2024-2025" "Report identifies Reading/Spelling template"
require_contains "$REPORT" "| Language Arts | 19426 | 2024-2025" "Report identifies Language Arts template"
require_contains "$REPORT" "| History | 21934 | 2025-2026" "Report identifies History template"
require_contains "$REPORT" "| Science | 21970 | 2025-2026" "Report identifies Science template"
require_contains "$REPORT" "| Homeroom | 19424 | 2024-2025" "Report identifies Homeroom newsletter template"
require_contains "$REPORT" "Canvas LLM Phase 16: Preview-Only Canvas Module/File/Page Relationship Map" "Report recommends Phase 16"

echo
echo "Safety Content Checks"
echo "----------------------------------------"
require_contains "$REPORT" "Phase 15 does not fetch from Canvas." "Report blocks Canvas fetch"
require_contains "$REPORT" "Phase 15 does not write to Canvas." "Report blocks Canvas writes"
require_contains "$REPORT" "Phase 15 does not download files." "Report blocks file downloads"
require_contains "$REPORT" "Phase 15 does not ingest page, announcement, assignment, or file bodies." "Report blocks body ingestion"
require_contains "$REPORT" "Phase 15 does not access student data" "Report blocks student data"
require_contains "$REPORT" "Phase 15 does not track the school Canvas URL or tokens." "Report blocks tracked URL/tokens"

echo
echo "Tracked Token And URL Guards"
echo "----------------------------------------"
if grep -RInE 'canvas\.instructure\.com|Authorization: Bearer [A-Za-z0-9]|CANVAS_API_TOKEN=.*[A-Za-z0-9_=-]{8,}|access_token["'\''"]?[[:space:]]*[:=][[:space:]]*["'\''"]?[A-Za-z0-9_=-]{8,}' \
  "$REPORT" "$ANALYZER" >/tmp/canvas_phase_15_secret_scan.txt 2>/dev/null; then
  cat /tmp/canvas_phase_15_secret_scan.txt
  fail "Possible tracked Canvas URL/token pattern found in Phase 15 report/analyzer"
else
  pass "No tracked school Canvas URL/token pattern found in Phase 15 report/analyzer"
fi
rm -f /tmp/canvas_phase_15_secret_scan.txt

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
