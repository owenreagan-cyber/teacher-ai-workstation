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
    pass "Phase 12 file exists: $path"
  else
    fail "Missing Phase 12 file: $path"
  fi
}

echo "Canvas LLM Phase 12: Fake/Local Sandbox Metadata Import Artifact Gate"
echo "----------------------------------------"

require_file "scripts/canvas-llm-sandbox-import-artifact-preview.py"
require_file "scripts/canvas-llm-phase-12-status.sh"
require_file "fixtures/canvas-llm/import-preview/README.md"
require_file "fixtures/canvas-llm/import-preview/fake-local-sandbox-import-artifact-course-24399.json"

echo
echo "Phase 12 Artifact Preview"
echo "----------------------------------------"
if phase12_output="$(scripts/canvas-llm-sandbox-import-artifact-preview.py)"; then
  echo "$phase12_output"
  pass "Phase 12 fake/local import artifact validator passed"
else
  echo "$phase12_output"
  fail "Phase 12 fake/local import artifact validator failed"
fi

if echo "$phase12_output" | grep -q "WARN: announcements_metadata has 0 records in sandbox staging"; then
  warn "announcements_metadata has 0 records in sandbox staging"
else
  fail "Expected announcements_metadata warning was not preserved"
fi

echo
echo "Phase 12 JSON Safety Proof"
echo "----------------------------------------"
if python3 - <<'PY'
import json
from pathlib import Path

artifact = Path("fixtures/canvas-llm/import-preview/fake-local-sandbox-import-artifact-course-24399.json")
data = json.loads(artifact.read_text(encoding="utf-8"))

assert data["course_id"] == 24399
assert data["course_scope"]["approved_course_ids"] == [24399]
assert data["real_metadata_copied"] is False
assert data["import_performed"] is False
assert data["knowledge_db_write"] is False
assert data["runtime_database_write"] is False
assert data["canvas_api_call"] is False
assert data["production_write"] is False
assert data["canonical_catalog_write"] is False
assert data["student_data"] is False
assert data["real_curriculum_body_ingestion"] is False
assert data["generation_rag_embeddings"] is False
assert data["local_model_ollama_execution"] is False
assert data["tracked_school_canvas_url"] is False
assert data["tracked_tokens_or_secrets"] is False
assert data["local_staging_committed"] is False
PY
then
  pass "Artifact JSON parses and preserves required Phase 12 safety flags"
else
  fail "Artifact JSON safety validation failed"
fi

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
echo "Phase 12 Sensitive Marker Guard"
echo "----------------------------------------"
if grep -RInE 'canvas\.instructure\.com|Authorization: Bearer|CANVAS_TOKEN|canvas_token|access_token|Bearer ' \
  fixtures/canvas-llm/import-preview >/tmp/canvas_phase12_sensitive_scan.txt 2>/dev/null; then
  cat /tmp/canvas_phase12_sensitive_scan.txt
  fail "Phase 12 fixture introduced tracked school Canvas URL or token-like marker"
else
  pass "Phase 12 fixture has no tracked school Canvas URL or token-like marker"
fi
rm -f /tmp/canvas_phase12_sensitive_scan.txt

echo
echo "Course Scope Guard"
echo "----------------------------------------"
if grep -RInE 'course_id[^0-9]*[0-9]{5,}|course-[0-9]{5,}' \
  fixtures/canvas-llm/import-preview \
  | grep -v '24399' >/tmp/canvas_phase12_course_id_scan.txt 2>/dev/null; then
  cat /tmp/canvas_phase12_course_id_scan.txt
  fail "Found exact real non-demo course ID other than approved 24399 in Phase 12 fixture"
else
  pass "No exact real non-demo course IDs found in Phase 12 fixture other than approved 24399"
fi
rm -f /tmp/canvas_phase12_course_id_scan.txt

echo
echo "Phase 11 Continuity"
echo "----------------------------------------"
if phase11_output="$(bin/chief-of-staff --canvas-llm-phase-11-status)"; then
  echo "$phase11_output" | tail -10
  if echo "$phase11_output" | grep -q "FAIL: 0"; then
    pass "Phase 11 status still passes"
  else
    fail "Phase 11 status did not report FAIL: 0"
  fi
else
  echo "$phase11_output"
  fail "Phase 11 status command failed"
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
