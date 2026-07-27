#!/usr/bin/env bash
set -u

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT" || exit 1

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

pass() { PASS_COUNT=$((PASS_COUNT + 1)); printf 'PASS: %s\n' "$1"; }
fail() { FAIL_COUNT=$((FAIL_COUNT + 1)); printf 'FAIL: %s\n' "$1"; }

CONN="scripts/canvas_llm_phase22/canvas_connection.py"
LIVE="scripts/canvas_llm_phase22/live_q1w2_deployment.py"
LIVE_TEST="tests/canvas-llm-live-q1w2-deployment-test.sh"

echo "Canvas LLM Canvas Connection Status"
echo "-----------------------------------"
echo

[[ -f "$CONN" ]] && pass "canvas connection module exists" || fail "canvas connection module missing"
grep -F -- '--canvas-connection-status' bin/chief-of-staff >/dev/null && pass "chief-of-staff dispatches canvas connection status" || fail "dispatch missing"

PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/teacher-ai-workstation-pycache" python3 -m py_compile "$CONN" >/dev/null 2>&1 && pass "canvas connection Python syntax passes" || fail "canvas connection Python syntax fails"
CANVAS_LLM_CONNECTION_TEST_MODE=1 python3 "$CONN" self-test >/dev/null 2>&1 && pass "canvas connection self-test passes" || fail "canvas connection self-test fails"

CANVAS_LLM_CONNECTION_TEST_MODE=1 bin/chief-of-staff --canvas-connection-status > /tmp/c2c1-conn.txt 2>&1 && pass "canvas connection report exits successfully" || { cat /tmp/c2c1-conn.txt; fail "canvas connection report failed"; }
grep -Fq 'Authentication:' /tmp/c2c1-conn.txt && pass "canvas connection report header present" || fail "canvas connection report header missing"
grep -Fq 'CONTROLLED' /tmp/c2c1-conn.txt && pass "canvas connection report shows controlled writes" || fail "controlled writes missing"

python3 - <<'PY' >/dev/null 2>&1
from pathlib import Path
import sys
sys.path.insert(0, str(Path('.').resolve()))
from scripts.canvas_llm_phase22 import canvas_connection as conn
assert conn.connection_has_no_network_writes()
PY
[[ $? -eq 0 ]] && pass "canvas connection layer has no network writes" || fail "canvas connection security checks failed"

echo
echo "Summary"
echo "-------"
printf 'PASS: %s\n' "$PASS_COUNT"
printf 'WARN: %s\n' "$WARN_COUNT"
printf 'FAIL: %s\n' "$FAIL_COUNT"
[[ "$FAIL_COUNT" -eq 0 ]]
