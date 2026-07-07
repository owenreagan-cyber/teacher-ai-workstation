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
    pass "Phase 14A file exists: $path"
  else
    fail "Missing Phase 14A file: $path"
  fi
}

echo "Canvas LLM Phase 14A: Course Approval Manifest"
echo "----------------------------------------"

require_file "config/canvas-llm/approved-canvas-course-manifest.json"
require_file "docs/programs/canvas-llm/canvas-phase-14a-course-approval-manifest.md"
require_file "scripts/canvas-llm-course-approval-manifest-validator.py"
require_file "scripts/canvas-llm-phase-14a-status.sh"

echo
echo "Manifest Validator"
echo "----------------------------------------"
if manifest_output="$(scripts/canvas-llm-course-approval-manifest-validator.py)"; then
  echo "$manifest_output"
  pass "Phase 14A manifest validator passed"
else
  echo "$manifest_output"
  fail "Phase 14A manifest validator failed"
fi

echo
echo "Manifest Content Spot Checks"
echo "----------------------------------------"
if python3 - <<'PY'
import json
from pathlib import Path

path = Path("config/canvas-llm/approved-canvas-course-manifest.json")
data = json.loads(path.read_text(encoding="utf-8"))
courses = data["courses"]
ids = {course["course_id"] for course in courses}
assert 26427 in ids
assert 22254 in ids
assert 19424 in ids
assert 24399 in ids
assert len(courses) == 19
shared = {course["course_id"]: course["canonical_prefixes"] for course in courses if course["course_id"] in {26442, 21919, 19419}}
assert shared[26442] == ["RM4", "SPELL"]
assert shared[21919] == ["RM4", "SPELL"]
assert shared[19419] == ["RM4", "SPELL"]
assert data["safety"]["api_fetch_performed_by_this_manifest"] is False
assert data["safety"]["canvas_write_approved"] is False
assert data["safety"]["file_download_approved"] is False
assert data["safety"]["body_ingestion_approved"] is False
assert data["safety"]["student_data_approved"] is False
PY
then
  pass "Manifest includes HR courses, demo course, shared RM4/SPELL courses, and safety flags"
else
  fail "Manifest content spot check failed"
fi

echo
echo "No API Execution Guard"
echo "----------------------------------------"
if grep -RInE 'curl |requests\.|canvasapi|Authorization: Bearer|CANVAS_TOKEN|canvas_token|access_token' \
  config/canvas-llm/approved-canvas-course-manifest.json \
  docs/programs/canvas-llm/canvas-phase-14a-course-approval-manifest.md >/tmp/canvas_phase_14a_api_scan.txt 2>/dev/null; then
  cat /tmp/canvas_phase_14a_api_scan.txt
  fail "Phase 14A manifest/doc introduced API/token/fetch marker"
else
  pass "Phase 14A manifest/doc introduced no API call, token, or fetch marker"
fi
rm -f /tmp/canvas_phase_14a_api_scan.txt

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
echo "Phase 13 Continuity"
echo "----------------------------------------"
if phase13_output="$(bin/chief-of-staff --canvas-llm-phase-13-status)"; then
  echo "$phase13_output" | tail -35
  if echo "$phase13_output" | grep -q "FAIL: 0"; then
    pass "Phase 13 status still passes"
  else
    fail "Phase 13 status did not report FAIL: 0"
  fi
else
  echo "$phase13_output"
  fail "Phase 13 status command failed"
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
