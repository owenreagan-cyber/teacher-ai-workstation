#!/usr/bin/env bash
# Read-only Canvas LLM Phase 6 fake/local knowledge DB validator status.
set -euo pipefail

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

pass() { PASS_COUNT=$((PASS_COUNT + 1)); printf 'PASS: %s\n' "$1"; }
warn() { WARN_COUNT=$((WARN_COUNT + 1)); printf 'WARN: %s\n' "$1"; }
fail() { FAIL_COUNT=$((FAIL_COUNT + 1)); printf 'FAIL: %s\n' "$1"; }
section() { printf '\n%s\n' "$1"; printf '%s\n' '----------------------------------------'; }

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
[[ -z "${repo_root}" ]] && repo_root="$(cd "${script_dir}/.." && pwd -P)"
cd "${repo_root}"

section "Canvas LLM Phase 6 Fake/Local Knowledge DB Validator"
cat <<'STATUS'
Status: canvas_llm_phase_6_fake_local_knowledge_db_validator_complete
Classification: read-only fake/local fixture validator only
Runtime activation: no
Canvas API/OAuth/live reads: blocked
Canvas writes/publishing: blocked
Student data: blocked
Real curriculum ingestion: blocked
Runtime SQLite/database writes: blocked
Generation/RAG/embeddings: blocked
STATUS

section "Phase 6 Artifacts"
[[ -x scripts/canvas-llm-knowledge-db-validator.py ]] && pass "validator script exists and is executable" || fail "validator script missing or not executable"
python3 -m py_compile scripts/canvas-llm-knowledge-db-validator.py >/dev/null 2>&1 && pass "validator Python compiles" || fail "validator Python compile failed"

section "Validator Run"
if scripts/canvas-llm-knowledge-db-validator.py >/tmp/canvas-llm-knowledge-db-validator.out 2>&1; then
  pass "knowledge DB validator passes"
else
  fail "knowledge DB validator failed"
  tail -60 /tmp/canvas-llm-knowledge-db-validator.out || true
fi

if grep -F "FAIL: 0" /tmp/canvas-llm-knowledge-db-validator.out >/dev/null; then
  pass "validator reports FAIL: 0"
else
  fail "validator did not report FAIL: 0"
fi

if grep -F "WARN: 0" /tmp/canvas-llm-knowledge-db-validator.out >/dev/null; then
  pass "validator reports WARN: 0"
else
  fail "validator did not report WARN: 0"
fi

section "Phase 5 Continuity"
if bin/chief-of-staff --canvas-llm-phase-5-status >/tmp/canvas-phase-5-status.out 2>&1; then
  pass "Phase 5 status still passes"
else
  fail "Phase 5 status failed"
  tail -40 /tmp/canvas-phase-5-status.out || true
fi

section "Boundary Assertions"
grep -F "Canvas API/OAuth/live reads: blocked" scripts/canvas-llm-knowledge-db-validator.py >/dev/null && pass "validator documents Canvas API blocked" || fail "validator must document Canvas API blocked"
grep -F "Real curriculum ingestion: blocked" scripts/canvas-llm-knowledge-db-validator.py >/dev/null && pass "validator documents real curriculum ingestion blocked" || fail "validator must document real curriculum ingestion blocked"
grep -F "Generation/RAG/embeddings: blocked" scripts/canvas-llm-knowledge-db-validator.py >/dev/null && pass "validator documents generation/RAG/embeddings blocked" || fail "validator must document generation/RAG/embeddings blocked"
grep -F "validator performs no network access" /tmp/canvas-llm-knowledge-db-validator.out >/dev/null && pass "validator confirms no network access" || fail "validator must confirm no network access"
grep -F "validator reads fake/local repo fixtures only" /tmp/canvas-llm-knowledge-db-validator.out >/dev/null && pass "validator confirms fake/local repo fixtures only" || fail "validator must confirm fake/local repo fixtures only"

section "Summary"
printf 'PASS: %s\n' "${PASS_COUNT}"
printf 'WARN: %s\n' "${WARN_COUNT}"
printf 'FAIL: %s\n' "${FAIL_COUNT}"

[[ "${FAIL_COUNT}" -gt 0 ]] && exit 1
exit 0
