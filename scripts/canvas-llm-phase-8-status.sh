#!/usr/bin/env bash
# Read-only Canvas LLM Phase 8 sandbox/demo API fetch gate status.
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

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
[[ -z "${repo_root}" ]] && repo_root="$(cd "${script_dir}/.." && pwd -P)"
cd "${repo_root}"

doc="docs/programs/canvas-llm/canvas-phase-8-sandbox-api-fetch-gate.md"

section "Canvas LLM Phase 8 Sandbox/Demo API Fetch Gate"
cat <<'STATUS'
Status: canvas_llm_phase_8_sandbox_api_fetch_gate_complete
Classification: API fetch gate only
Runtime activation: no
Canvas API/OAuth/live reads: blocked until explicit execution approval
Canvas writes/publishing: blocked
Student data: blocked
Real curriculum ingestion: blocked
Runtime SQLite/database writes: blocked
Generation/RAG/embeddings: blocked
STATUS

section "Phase 8 Artifacts"
check_file "${doc}"

section "Non-Activation Boundary"
check_contains "${doc}" "This phase does not call Canvas" "no Canvas calls"
check_contains "${doc}" "does not use OAuth" "no OAuth"
check_contains "${doc}" "does not read tokens" "no token reads"
check_contains "${doc}" "does not perform network access" "no network access"
check_contains "${doc}" "does not fetch live Canvas data" "no live fetch"
check_contains "${doc}" "does not write staging output" "no staging output writes"
check_contains "${doc}" "Phase 8 is a gate only" "gate only"
check_contains "${doc}" "blocked until explicit Owen approval" "blocked until explicit approval"

section "Candidate Sandbox/Demo Scope"
check_contains "${doc}" "Candidate source class | \`sandbox_demo_canvas_course\`" "sandbox demo source class"
check_contains "${doc}" "Candidate course ID | \`24399\`" "demo course 24399"
check_contains "${doc}" "Candidate mode | read-only" "read-only candidate mode"
check_contains "${doc}" "Candidate output class | local staging metadata only" "metadata-only staging candidate"
check_contains "${doc}" "This candidate is not activated by Phase 8" "candidate not activated"

section "Required Future Approval"
for phrase in \
  "exact course ID: \`24399\`" \
  "read-only mode" \
  "exact allowed endpoint list" \
  "exact blocked endpoint list" \
  "token handling method" \
  "local staging path" \
  "allowed output file names" \
  "rollback/delete command" \
  "validation command" \
  "no student data confirmation" \
  "no Canvas writes/publishing confirmation" \
  "no real curriculum body ingestion confirmation"
do
  check_contains "${doc}" "$phrase" "$phrase"
done

section "Allowed Future Endpoint Classes"
for phrase in \
  "course metadata" \
  "modules" \
  "module items" \
  "pages metadata" \
  "assignments metadata" \
  "announcements metadata" \
  "files metadata"
do
  check_contains "${doc}" "$phrase" "future allowed endpoint: $phrase"
done

section "Blocked Endpoint Classes"
for phrase in \
  "users" \
  "enrollments" \
  "submissions" \
  "grades" \
  "analytics" \
  "conversations/messages" \
  "discussions with student replies" \
  "attendance" \
  "student work" \
  "student identity data" \
  "create/update/delete/publish endpoints"
do
  check_contains "${doc}" "$phrase" "blocked endpoint: $phrase"
done

section "Token And Staging Gates"
for phrase in \
  "does not create, request, store, validate, print, or use a Canvas token" \
  "no token in tracked files" \
  "no token in docs" \
  "no token in fixtures" \
  "no token in command output" \
  "no token in logs" \
  "no token in PR body" \
  "metadata-only output" \
  "no production registry writes" \
  "no canonical catalog writes" \
  "rollback/delete command documented before execution"
do
  check_contains "${doc}" "$phrase" "$phrase"
done

section "Course ID Guard"
if python3 - "${doc}" <<'PYSCAN'
import re
import sys
from pathlib import Path

doc = Path(sys.argv[1])
text = doc.read_text(encoding="utf-8")
ids = sorted(set(re.findall(r"\b\d{5}\b", text)))
blocked = [course_id for course_id in ids if course_id != "24399"]
if blocked:
    print("blocked course IDs found:", ", ".join(blocked))
    sys.exit(1)
print("tracked Phase 8 gate contains only allowed demo course ID 24399")
PYSCAN
then
  pass "tracked Phase 8 gate avoids non-demo real course IDs"
else
  fail "tracked Phase 8 gate must not contain non-demo real course IDs"
fi

section "Phase 7 Continuity"
if bin/chief-of-staff --canvas-llm-phase-7-status >/tmp/canvas-phase-7-status.out 2>&1; then
  pass "Phase 7 status still passes"
else
  fail "Phase 7 status failed"
  tail -40 /tmp/canvas-phase-7-status.out || true
fi

section "Summary"
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"

[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
