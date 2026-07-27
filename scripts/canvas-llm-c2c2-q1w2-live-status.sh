#!/usr/bin/env bash
set -u

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT" || exit 1

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

pass() { PASS_COUNT=$((PASS_COUNT + 1)); printf 'PASS: %s\n' "$1"; }
fail() { FAIL_COUNT=$((FAIL_COUNT + 1)); printf 'FAIL: %s\n' "$1"; }

LIVE="scripts/canvas_llm_phase22/live_q1w2_deployment.py"
TRANSPORT_TEST="tests/canvas-llm-live-canvas-transport-test.sh"
LIVE_TEST="tests/canvas-llm-live-q1w2-deployment-test.sh"

echo "Canvas LLM C2C2 Q1W2 Live Deployment Status"
echo "-------------------------------------------"
echo

[[ -f "$LIVE" ]] && pass "c2c2 live deployment module exists" || fail "c2c2 live deployment module missing"
grep -F -- '--c2c2-q1w2-live-status' bin/chief-of-staff >/dev/null && pass "chief-of-staff dispatches c2c2 live status" || fail "c2c2 dispatch missing"

CANVAS_LLM_LIVE_TRANSPORT_TEST=1 CANVAS_LLM_LIVE_Q1W2_APPROVED=1 python3 "$LIVE" self-test >/dev/null 2>&1 && pass "c2c2 live deployment self-test passes" || fail "c2c2 live deployment self-test fails"

CANVAS_LLM_LIVE_TRANSPORT_TEST=1 CANVAS_LLM_LIVE_Q1W2_APPROVED=1 bin/chief-of-staff --c2c2-q1w2-live-status > /tmp/c2c2-live.txt 2>&1 && pass "c2c2 live status report exits successfully" || { cat /tmp/c2c2-live.txt; fail "c2c2 live status report failed"; }
grep -Fq 'C2C2 Q1W2 Live Deployment' /tmp/c2c2-live.txt && pass "c2c2 live status header present" || fail "c2c2 live status header missing"
grep -Fq 'Transport:' /tmp/c2c2-live.txt && pass "c2c2 live status transport section present" || fail "transport section missing"
grep -Fq 'LIVE' /tmp/c2c2-live.txt && pass "c2c2 live status shows live transport" || fail "live transport label missing"

[[ -x "$TRANSPORT_TEST" ]] && bash "$TRANSPORT_TEST" >/dev/null 2>&1 && pass "live transport regression test passes" || fail "live transport regression test fails"
[[ -x "$LIVE_TEST" ]] && bash "$LIVE_TEST" >/dev/null 2>&1 && pass "c2c1 live q1w2 regression test passes" || fail "c2c1 regression test fails"

echo
echo "Summary"
echo "-------"
printf 'PASS: %s\n' "$PASS_COUNT"
printf 'WARN: %s\n' "$WARN_COUNT"
printf 'FAIL: %s\n' "$FAIL_COUNT"
[[ "$FAIL_COUNT" -eq 0 ]]
