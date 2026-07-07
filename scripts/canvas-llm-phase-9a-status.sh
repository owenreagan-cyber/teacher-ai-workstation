#!/usr/bin/env bash
# Read-only Canvas LLM Phase 9A sandbox metadata fetch scaffold status.
set -euo pipefail

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

pass() { PASS_COUNT=$((PASS_COUNT + 1)); printf 'PASS: %s\n' "$1"; }
warn() { WARN_COUNT=$((WARN_COUNT + 1)); printf 'WARN: %s\n' "$1"; }
fail() { FAIL_COUNT=$((FAIL_COUNT + 1)); printf 'FAIL: %s\n' "$1"; }
section() { printf '\n%s\n' "$1"; printf '%s\n' '----------------------------------------'; }

check_file() {
  [[ -f "$1" ]] && pass "file exists: $1" || fail "file missing: $1"
}

check_executable() {
  [[ -x "$1" ]] && pass "executable exists: $1" || fail "executable missing: $1"
}

check_contains() {
  local file="$1"
  local phrase="$2"
  local label="$3"
  if [[ ! -f "$file" ]]; then
    fail "$file missing for $label"
    return
  fi
  grep -F -- "$phrase" "$file" >/dev/null && pass "file mentions $label" || fail "$file must mention $label"
}

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
[[ -z "${repo_root}" ]] && repo_root="$(cd "${script_dir}/.." && pwd -P)"
cd "${repo_root}"

doc="docs/programs/canvas-llm/canvas-phase-9a-sandbox-metadata-fetch-scaffold.md"
scaffold="scripts/canvas-llm-sandbox-metadata-fetch-scaffold.py"

section "Canvas LLM Phase 9A Sandbox Metadata Fetch Scaffold"
cat <<'STATUS'
Status: canvas_llm_phase_9a_sandbox_metadata_fetch_scaffold_complete
Classification: gated read-only metadata fetch scaffold
Runtime activation: dry-run by default
Approved course ID: 24399 only
Canvas API/OAuth/live reads: scaffolded but blocked unless separately approved execution phase
Canvas writes/publishing: blocked
Student data: blocked
Real curriculum body ingestion: blocked
Runtime SQLite/database writes: blocked
Generation/RAG/embeddings: blocked
STATUS

section "Phase 9A Artifacts"
check_file "${doc}"
check_executable "${scaffold}"
python3 -m py_compile "${scaffold}" >/dev/null 2>&1 && pass "scaffold Python compiles" || fail "scaffold Python compile failed"

section "Documentation Boundary"
check_contains "${doc}" "default behavior must remain dry-run only" "dry-run default"
check_contains "${doc}" "Course ID | \`24399\`" "approved course ID 24399"
check_contains "${doc}" "No other real Canvas course ID is approved" "no other course approved"
check_contains "${doc}" "CANVAS_API_TOKEN" "token env name only"
check_contains "${doc}" "no token in tracked files" "no token in tracked files"
check_contains "${doc}" ".local/canvas-llm/sandbox-metadata/course-24399/" "approved local staging path"
check_contains "${doc}" "rm -rf .local/canvas-llm/sandbox-metadata/course-24399" "rollback command"
check_contains "${doc}" "dry-run command works without network or token" "dry-run without network/token"
check_contains "${doc}" "course ID guard rejects non-24399 IDs" "course ID rejection requirement"

section "Scaffold Dry-Run"
if "${scaffold}" dry-run >/tmp/canvas-phase-9a-dry-run.out 2>&1; then
  pass "dry-run command succeeds"
else
  fail "dry-run command failed"
  cat /tmp/canvas-phase-9a-dry-run.out || true
fi

for phrase in \
  '"course_id": "24399"' \
  '"network_access": false' \
  '"canvas_api_call": false' \
  '"oauth": false' \
  '"live_read": false' \
  '"canvas_write": false' \
  '"student_data": false' \
  '"token_value_printed": false'
do
  grep -F -- "$phrase" /tmp/canvas-phase-9a-dry-run.out >/dev/null && pass "dry-run output proves $phrase" || fail "dry-run output missing $phrase"
done

section "Scaffold Validate"
if "${scaffold}" validate >/tmp/canvas-phase-9a-validate.out 2>&1; then
  pass "validate command succeeds"
else
  fail "validate command failed"
  cat /tmp/canvas-phase-9a-validate.out || true
fi
grep -F "no Canvas API call was performed" /tmp/canvas-phase-9a-validate.out >/dev/null && pass "validate confirms no Canvas API call" || fail "validate must confirm no Canvas API call"

section "Course And Live Fetch Guards"
if "${scaffold}" --course-id 99999 dry-run >/tmp/canvas-phase-9a-wrong-course.out 2>&1; then
  fail "wrong course ID was accepted"
else
  pass "wrong course ID rejected"
fi
grep -F "course ID must be 24399" /tmp/canvas-phase-9a-wrong-course.out >/dev/null && pass "wrong course rejection message is explicit" || fail "wrong course rejection message missing"

if "${scaffold}" live-fetch >/tmp/canvas-phase-9a-live-fetch.out 2>&1; then
  fail "live fetch command was accepted"
else
  pass "live fetch command blocked"
fi
grep -F "live Canvas fetch is intentionally not implemented in Phase 9A" /tmp/canvas-phase-9a-live-fetch.out >/dev/null && pass "live fetch blocked message is explicit" || fail "live fetch blocked message missing"

section "Endpoint And Token Guards"
check_contains "${scaffold}" "ALLOWED_ENDPOINT_CLASSES" "endpoint allowlist"
check_contains "${scaffold}" "BLOCKED_ENDPOINT_CLASSES" "blocked endpoint classes"
check_contains "${scaffold}" "users" "users blocked"
check_contains "${scaffold}" "enrollments" "enrollments blocked"
check_contains "${scaffold}" "submissions" "submissions blocked"
check_contains "${scaffold}" "grades" "grades blocked"
check_contains "${scaffold}" "TOKEN_ENV_NAME = \"CANVAS_API_TOKEN\"" "token env name constant"
check_contains "${scaffold}" "token value is not printed" "token value not printed"

section "Course ID Guard"
if python3 - "${doc}" "${scaffold}" <<'PYSCAN'
import re
import sys
from pathlib import Path

allowed = {"24399"}
bad = {}
for file_name in sys.argv[1:]:
    text = Path(file_name).read_text(encoding="utf-8")
    ids = sorted(set(re.findall(r"\b\d{5}\b", text)))
    blocked = [course_id for course_id in ids if course_id not in allowed]
    if blocked:
        bad[file_name] = blocked

if bad:
    for file_name, ids in bad.items():
        print(f"{file_name}: {', '.join(ids)}")
    sys.exit(1)

print("Phase 9A tracked files contain only allowed demo course ID 24399")
PYSCAN
then
  pass "tracked Phase 9A files avoid non-demo real course IDs"
else
  fail "tracked Phase 9A files must not contain non-demo real course IDs"
fi

section "Network/API Code Guard"
if grep -R "requests\|urllib\|curl\|http.client\|urlopen" "${scaffold}" >/tmp/canvas-phase-9a-network-grep.out 2>&1; then
  fail "network/API execution code found in Phase 9A scaffold"
  cat /tmp/canvas-phase-9a-network-grep.out || true
else
  pass "no network/API execution library usage found in Phase 9A scaffold"
fi

section "Phase 8 Continuity"
if bin/chief-of-staff --canvas-llm-phase-8-status >/tmp/canvas-phase-8-status.out 2>&1; then
  pass "Phase 8 status still passes"
else
  fail "Phase 8 status failed"
  tail -40 /tmp/canvas-phase-8-status.out || true
fi

section "Summary"
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"

[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
