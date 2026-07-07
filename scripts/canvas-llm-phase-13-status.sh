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
    pass "Phase 13 file exists: $path"
  else
    fail "Missing Phase 13 file: $path"
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

require_not_contains() {
  local path="$1"
  local pattern="$2"
  local description="$3"

  if grep -Fq "$pattern" "$path"; then
    fail "$description"
  else
    pass "$description"
  fi
}

DOC="docs/programs/canvas-llm/canvas-phase-13-historical-homeroom-fetch-approval-gate.md"

echo "Canvas LLM Phase 13: Historical Academic + Homeroom Course Fetch Approval Gate"
echo "----------------------------------------"

require_file "$DOC"
require_file "scripts/canvas-llm-phase-13-status.sh"

echo
echo "Approval Scope"
echo "----------------------------------------"
require_contains "$DOC" "historical academic courses" "Historical academic courses are included in approved future scope"
require_contains "$DOC" "current operational courses" "Current operational courses are included in approved future scope"
require_contains "$DOC" "Homeroom/newsletter courses" "Homeroom/newsletter courses are included in approved future scope"
require_contains "$DOC" "The user approves future Canvas API access when a later phase explicitly requires it" "Future Canvas API access approval is recorded with phase gating"
require_contains "$DOC" "Course IDs must still be supplied or discovered through an approved course-listing gate" "Course IDs remain gated before fetch"

echo
echo "Approved Metadata Categories"
echo "----------------------------------------"
require_contains "$DOC" "files metadata" "Files metadata is approved for future read-only fetch"
require_contains "$DOC" "folders metadata" "Folders metadata is approved for future read-only fetch"
require_contains "$DOC" "modules metadata" "Modules metadata is approved for future read-only fetch"
require_contains "$DOC" "module_items metadata" "Module items metadata is approved for future read-only fetch"
require_contains "$DOC" "pages metadata" "Pages metadata is approved for future read-only fetch"
require_contains "$DOC" "announcements metadata" "Announcements metadata is approved for future read-only fetch"
require_contains "$DOC" "assignments metadata only when needed for file/module/page relationship mapping" "Assignments metadata is constrained to relationship mapping"

echo
echo "Homeroom Guard"
echo "----------------------------------------"
require_contains "$DOC" "Homeroom/newsletter courses are a separate course class" "Homeroom is defined as separate course class"
require_contains "$DOC" "They should not be evaluated against normal academic Canvas curriculum-file guidelines" "Homeroom is not evaluated as academic curriculum course"
require_contains "$DOC" "Phase 13 does not approve body ingestion" "Homeroom body ingestion remains blocked in Phase 13"

echo
echo "Blocked Data and Write Guards"
echo "----------------------------------------"
require_contains "$DOC" "student data remains blocked" "Student data remains blocked"
require_contains "$DOC" "Canvas writes remain blocked" "Canvas writes remain blocked"
require_contains "$DOC" "body ingestion remains blocked" "Body ingestion remains blocked"
require_contains "$DOC" "file downloads" "File downloads remain blocked"
require_contains "$DOC" "page bodies" "Page bodies remain blocked"
require_contains "$DOC" "announcement bodies" "Announcement bodies remain blocked"
require_contains "$DOC" "tracked tokens/secrets" "Tracked tokens/secrets remain blocked"
require_contains "$DOC" "tracked school Canvas URLs" "Tracked school Canvas URLs remain blocked"
require_contains "$DOC" 'committed `.local/...` fetched metadata' "Committed dot-local fetched metadata remains blocked"

echo
echo "No API Execution Guard"
echo "----------------------------------------"
require_contains "$DOC" "Phase 13 does not perform a Canvas API call" "Phase 13 explicitly performs no Canvas API call"
require_contains "$DOC" "Phase 13 does not fetch or enumerate courses" "Phase 13 explicitly performs no course fetch/enumeration"
require_not_contains "$DOC" "curl " "Phase 13 doc does not include curl fetch command"

echo
echo "Local Metadata Guard"
echo "----------------------------------------"
if git check-ignore -q .local/canvas-llm/sandbox-metadata/course-24399/manifest.json; then
  pass ".local Canvas metadata manifest is ignored"
else
  fail ".local Canvas metadata manifest is not ignored"
fi

if [[ -z "$(git ls-files .local/canvas-llm)" ]]; then
  pass ".local Canvas metadata is not tracked"
else
  fail ".local Canvas metadata is tracked"
fi

echo
echo "Phase 12 Continuity"
echo "----------------------------------------"
if phase12_output="$(bin/chief-of-staff --canvas-llm-phase-12-status)"; then
  echo "$phase12_output" | tail -25
  if echo "$phase12_output" | grep -q "FAIL: 0"; then
    pass "Phase 12 status still passes"
  else
    fail "Phase 12 status did not report FAIL: 0"
  fi
else
  echo "$phase12_output"
  fail "Phase 12 status command failed"
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
