#!/usr/bin/env bash
# Read-only Canvas LLM Phase 7 API approval packet status.
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

check_contains() {
  local file="$1"
  local phrase="$2"
  local label="$3"
  if [[ ! -f "$file" ]]; then
    fail "$file missing for $label"
    return
  fi
  grep -F -- "$phrase" "$file" >/dev/null && pass "doc mentions $label" || fail "$file must mention $label"
}

check_not_contains() {
  local file="$1"
  local phrase="$2"
  local label="$3"
  if [[ ! -f "$file" ]]; then
    fail "$file missing for $label"
    return
  fi
  grep -F -- "$phrase" "$file" >/dev/null && fail "$file must not mention $label" || pass "doc does not mention $label"
}

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
[[ -z "${repo_root}" ]] && repo_root="$(cd "${script_dir}/.." && pwd -P)"
cd "${repo_root}"

doc="docs/programs/canvas-llm/canvas-phase-7-read-only-api-approval-packet.md"

section "Canvas LLM Phase 7 Read-Only API Approval Packet"
cat <<'STATUS'
Status: canvas_llm_phase_7_read_only_api_approval_packet_complete
Classification: approval packet only
Runtime activation: no
Canvas API/OAuth/live reads: blocked
Canvas writes/publishing: blocked
Student data: blocked
Real curriculum ingestion: blocked
Runtime SQLite/database writes: blocked
Generation/RAG/embeddings: blocked
STATUS

section "Phase 7 Artifacts"
check_file "${doc}"

section "Approval Packet Required Boundaries"
check_contains "${doc}" "approval packet only" "approval-packet-only classification"
check_contains "${doc}" "This phase does not connect to Canvas" "no Canvas connection"
check_contains "${doc}" "call Canvas APIs" "API call explicitly blocked"
check_contains "${doc}" "use OAuth" "OAuth explicitly blocked"
check_contains "${doc}" "use tokens" "tokens explicitly blocked"
check_contains "${doc}" "read live courses" "live reads explicitly blocked"
check_contains "${doc}" "write Canvas content" "Canvas writes explicitly blocked"
check_contains "${doc}" "student data" "student data blocked"
check_contains "${doc}" "real curriculum" "real curriculum blocked"
check_contains "${doc}" "runtime SQLite/database writes" "runtime database writes blocked"
check_contains "${doc}" "RAG" "RAG blocked"
check_contains "${doc}" "embeddings" "embeddings blocked"
check_contains "${doc}" "generate content" "generation blocked"

section "Course ID Boundary"
check_contains "${doc}" "24399" "demo sandbox candidate course ID"
check_contains "${doc}" "sandbox_demo_canvas_course" "sandbox demo source class"
check_contains "${doc}" "Candidate for future Phase 8 read-only sandbox/demo API test only" "candidate only status"
check_contains "${doc}" "current_or_upcoming_production_canvas_course" "production course class blocked"
check_contains "${doc}" "inactive_historical_canvas_course" "historical course class gated"
check_contains "${doc}" "Other course IDs are classified but not listed" "tracked doc avoids full course ID table"

section "Approval Gate Requirements"
for phrase in \
  "Canvas environment or base URL class" \
  "exact allowed course ID" \
  "allowed endpoint list" \
  "blocked endpoint list" \
  "token handling plan" \
  "local staging path" \
  "rollback/delete plan" \
  "no student data confirmation" \
  "no writes confirmation"
do
  check_contains "${doc}" "$phrase" "$phrase"
done

section "Endpoint Boundary"
for phrase in \
  "course metadata read" \
  "module list read" \
  "module item list read" \
  "page metadata read" \
  "assignment metadata read" \
  "announcement metadata read" \
  "file metadata read"
do
  check_contains "${doc}" "$phrase" "future allowed endpoint class: $phrase"
done

for phrase in \
  "submissions" \
  "grades" \
  "users" \
  "enrollments" \
  "analytics" \
  "conversations/messages" \
  "discussions with student replies" \
  "any create/update/delete/publish endpoint"
do
  check_contains "${doc}" "$phrase" "blocked endpoint class: $phrase"
done

section "Do Not Commit Full Course ID Table"
if python3 - "${doc}" <<'PYSCAN'
import re
import sys
from pathlib import Path

doc = Path(sys.argv[1])
text = doc.read_text(encoding="utf-8")
ids = sorted(set(re.findall(r"\\b\\d{5}\\b", text)))
blocked = [course_id for course_id in ids if course_id != "24399"]
if blocked:
    print("blocked course IDs found:", ", ".join(blocked))
    sys.exit(1)
print("tracked approval packet contains only allowed demo course ID 24399")
PYSCAN
then
  pass "tracked approval packet avoids full real course ID table"
else
  fail "tracked approval packet must not contain non-demo real course IDs"
fi

section "Phase 6 Continuity"
if bin/chief-of-staff --canvas-llm-phase-6-status >/tmp/canvas-phase-6-status.out 2>&1; then
  pass "Phase 6 status still passes"
else
  fail "Phase 6 status failed"
  tail -40 /tmp/canvas-phase-6-status.out || true
fi

section "Summary"
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"

[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
