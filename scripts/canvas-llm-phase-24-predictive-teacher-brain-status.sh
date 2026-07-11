#!/usr/bin/env bash
set -euo pipefail

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

pass() { PASS_COUNT=$((PASS_COUNT + 1)); printf 'PASS: %s\n' "$1"; }
warn() { WARN_COUNT=$((WARN_COUNT + 1)); printf 'WARN: %s\n' "$1"; }
fail() { FAIL_COUNT=$((FAIL_COUNT + 1)); printf 'FAIL: %s\n' "$1"; }

echo "Canvas LLM Phase 24 Predictive Teacher Brain Status"
echo "---------------------------------------------------"

M=scripts/canvas_llm_phase24/predict_week.py
V=scripts/canvas_llm_phase24/validate_prediction.py
P=fixtures/canvas-llm/phase-24/predictive-teacher-brain.json

for f in \
  "$M" \
  "$V" \
  scripts/canvas_llm_phase24/__init__.py \
  scripts/canvas_llm_phase24/models.py \
  scripts/canvas_llm_phase24/pacing_knowledge.py \
  scripts/canvas_llm_phase24/correction_memory.py \
  scripts/canvas_llm_phase24/rule_engine.py \
  fixtures/canvas-llm/phase-24/predictive-teacher-brain.json \
  fixtures/canvas-llm/phase-24/predictive-teacher-brain.manifest.json \
  docs/programs/canvas-llm/phase-24-predictive-teacher-brain/README.md \
  docs/programs/canvas-llm/phase-24-predictive-teacher-brain/teacher-brain-architecture.md \
  docs/programs/canvas-llm/phase-24-predictive-teacher-brain/prediction-source-hierarchy.md \
  docs/programs/canvas-llm/phase-24-predictive-teacher-brain/future-canvas-deployment-boundary.md \
  docs/programs/canvas-llm/phase-24-predictive-teacher-brain/implementation-report.md \
  scripts/canvas-llm-phase-24-predictive-teacher-brain-status.sh \
  tests/canvas-llm-phase-24-predictive-teacher-brain-test.sh \
  bin/chief-of-staff; do
  if [[ -f "$f" ]]; then
    pass "$f exists"
  else
    fail "$f missing"
  fi
done

PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/teacher-ai-workstation-pycache" python3 -m py_compile \
  "$M" "$V" \
  scripts/canvas_llm_phase24/models.py \
  scripts/canvas_llm_phase24/pacing_knowledge.py \
  scripts/canvas_llm_phase24/correction_memory.py \
  scripts/canvas_llm_phase24/rule_engine.py >/tmp/p24py.txt 2>&1 && pass "Python syntax passes" || { cat /tmp/p24py.txt; fail "Python syntax fails"; }

T=$(mktemp -d "${TMPDIR:-/tmp}/phase24-status.XXXXXX")
trap 'rm -rf "$T"' EXIT
OUT="$T/phase24-demo.json"
python3 "$M" --week Q1W5 --input "$P" --output "$OUT" >/tmp/p24build.txt 2>&1 && pass "predicted week builds" || { cat /tmp/p24build.txt; fail "predicted week build fails"; }
python3 "$V" "$OUT" >"$T/validate.txt" 2>&1 && pass "predicted week validates" || { cat "$T/validate.txt"; fail "predicted week validation fails"; }

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
