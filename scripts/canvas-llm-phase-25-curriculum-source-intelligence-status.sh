#!/usr/bin/env bash
set -euo pipefail

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

pass() { PASS_COUNT=$((PASS_COUNT + 1)); printf 'PASS: %s\n' "$1"; }
warn() { WARN_COUNT=$((WARN_COUNT + 1)); printf 'WARN: %s\n' "$1"; }
fail() { FAIL_COUNT=$((FAIL_COUNT + 1)); printf 'FAIL: %s\n' "$1"; }

echo "Canvas LLM Phase 25 Curriculum Source Intelligence Status"
echo "---------------------------------------------------------"

M=scripts/canvas_llm_phase25/resolve_resources.py
V=scripts/canvas_llm_phase25/validate_resolution.py
P=fixtures/canvas-llm/phase-25/phase24-predicted-week.json
R=fixtures/canvas-llm/phase-25/resource-registry.json
C=fixtures/canvas-llm/phase-25/resource-corrections.json

for f in \
  "$M" \
  "$V" \
  scripts/canvas_llm_phase25/__init__.py \
  scripts/canvas_llm_phase25/models.py \
  scripts/canvas_llm_phase25/registry.py \
  scripts/canvas_llm_phase25/correction_memory.py \
  scripts/canvas_llm_phase25/requirements.py \
  scripts/canvas_llm_phase25/resolver.py \
  scripts/canvas_llm_phase25/integration.py \
  fixtures/canvas-llm/phase-25/resource-registry.json \
  fixtures/canvas-llm/phase-25/resource-corrections.json \
  fixtures/canvas-llm/phase-25/phase24-predicted-week.json \
  fixtures/canvas-llm/phase-25/resource-resolution-expected.json \
  docs/programs/canvas-llm/phase-25-curriculum-source-intelligence/README.md \
  docs/programs/canvas-llm/phase-25-curriculum-source-intelligence/resource-registry-schema.md \
  docs/programs/canvas-llm/phase-25-curriculum-source-intelligence/resource-resolution-hierarchy.md \
  docs/programs/canvas-llm/phase-25-curriculum-source-intelligence/teacher-correction-promotion.md \
  docs/programs/canvas-llm/phase-25-curriculum-source-intelligence/resource-safety-classification.md \
  docs/programs/canvas-llm/phase-25-curriculum-source-intelligence/phase-23-24-25-integration.md \
  docs/programs/canvas-llm/phase-25-curriculum-source-intelligence/implementation-report.md \
  tests/canvas-llm-phase-25-curriculum-source-intelligence-test.sh \
  bin/chief-of-staff; do
  if [[ -f "$f" ]]; then
    pass "$f exists"
  else
    fail "$f missing"
  fi
done

PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/teacher-ai-workstation-pycache" python3 -m py_compile \
  "$M" "$V" \
  scripts/canvas_llm_phase25/models.py \
  scripts/canvas_llm_phase25/registry.py \
  scripts/canvas_llm_phase25/correction_memory.py \
  scripts/canvas_llm_phase25/requirements.py \
  scripts/canvas_llm_phase25/resolver.py \
  scripts/canvas_llm_phase25/integration.py >/tmp/p25py.txt 2>&1 && pass "Python syntax passes" || { cat /tmp/p25py.txt; fail "Python syntax fails"; }

T=$(mktemp -d "${TMPDIR:-/tmp}/phase25-status.XXXXXX")
trap 'rm -rf "$T"' EXIT
OUT="$T/phase25-demo.json"
python3 "$M" build-demo --week Q1W5 --predictions "$P" --registry "$R" --corrections "$C" --out "$OUT" >/tmp/p25build.txt 2>&1 && pass "resource-resolution packet builds" || { cat /tmp/p25build.txt; fail "resource-resolution build fails"; }
python3 "$V" "$OUT" >"$T/validate.txt" 2>&1 && pass "resource-resolution packet validates" || { cat "$T/validate.txt"; fail "resource-resolution validation fails"; }

grep -q '^WARN: due-time.unresolved' "$T/validate.txt" && pass "due-time unresolved warning is present" || fail "due-time warning missing"
grep -q '^WARN: math-test-cadence.unresolved' "$T/validate.txt" && pass "math cadence unresolved warning is present" || fail "math cadence warning missing"
grep -q '^PASS: reading.checkout14 Checkout 14 is absent without warning$' "$T/validate.txt" && pass "Reading Test 14 no-checkout PASS is present" || fail "Reading Test 14 no-checkout PASS missing"
grep -q '^FAIL: 0$' "$T/validate.txt" && pass "validator reported zero failures" || fail "validator reported failures"

warn "Canvas assignment due-time convention remains owner-unresolved"
warn "Math test cadence remains owner-unresolved"

echo
echo "Summary"
echo "-------"
echo "PASS: ${PASS_COUNT}"
echo "WARN: ${WARN_COUNT}"
echo "FAIL: ${FAIL_COUNT}"

[[ "${FAIL_COUNT}" -eq 0 ]]
