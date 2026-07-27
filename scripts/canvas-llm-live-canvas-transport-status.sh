#!/usr/bin/env bash
set -u

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT" || exit 1

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

pass() { PASS_COUNT=$((PASS_COUNT + 1)); printf 'PASS: %s\n' "$1"; }
fail() { FAIL_COUNT=$((FAIL_COUNT + 1)); printf 'FAIL: %s\n' "$1"; }

TRANSPORT="scripts/canvas_llm_phase22/canvas_connection_manager.py"
WRITER="scripts/canvas_llm_phase22/canvas_writer.py"
TRANSPORT_TEST="tests/canvas-llm-live-canvas-transport-test.sh"

echo "Canvas LLM Live Canvas Transport Status"
echo "---------------------------------------"
echo

[[ -f "$TRANSPORT" ]] && pass "live transport module exists" || fail "live transport module missing"
grep -F -- '--canvas-live-transport-status' bin/chief-of-staff >/dev/null && pass "chief-of-staff dispatches live transport status" || fail "dispatch missing"

PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/teacher-ai-workstation-pycache" python3 -m py_compile "$TRANSPORT" "$WRITER" >/dev/null 2>&1 && pass "live transport Python syntax passes" || fail "live transport Python syntax fails"
CANVAS_LLM_LIVE_TRANSPORT_TEST=1 python3 "$TRANSPORT" self-test >/dev/null 2>&1 && pass "live transport self-test passes" || fail "live transport self-test fails"

CANVAS_LLM_LIVE_TRANSPORT_TEST=1 bin/chief-of-staff --canvas-live-transport-status > /tmp/c2c2-transport.txt 2>&1 && pass "live transport report exits successfully" || { cat /tmp/c2c2-transport.txt; fail "live transport report failed"; }
grep -Fq 'Canvas Live Transport' /tmp/c2c2-transport.txt && pass "live transport report header present" || fail "live transport report header missing"
grep -Fq 'ENABLED' /tmp/c2c2-transport.txt && pass "live transport report shows enabled transport" || fail "enabled transport missing"
grep -Fq 'CONTROLLED' /tmp/c2c2-transport.txt && pass "live transport report shows controlled write gate" || fail "controlled write gate missing"

[[ -x "$TRANSPORT_TEST" ]] && bash "$TRANSPORT_TEST" >/dev/null 2>&1 && pass "live canvas transport test passes" || fail "live canvas transport test fails"

echo
echo "Summary"
echo "-------"
printf 'PASS: %s\n' "$PASS_COUNT"
printf 'WARN: %s\n' "$WARN_COUNT"
printf 'FAIL: %s\n' "$FAIL_COUNT"
[[ "$FAIL_COUNT" -eq 0 ]]
