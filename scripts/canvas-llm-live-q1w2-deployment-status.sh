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
RENDERER="scripts/canvas_llm_phase22/canvas_html_renderer.py"
CONN="scripts/canvas_llm_phase22/canvas_connection.py"
LIVE_TEST="tests/canvas-llm-live-q1w2-deployment-test.sh"

echo "Canvas LLM Live Q1W2 Deployment Status"
echo "--------------------------------------"
echo

for file in "$LIVE" "$RENDERER" "$CONN"; do
  [[ -f "$file" ]] && pass "$(basename "$file") exists" || fail "$(basename "$file") missing"
done

grep -F -- '--live-q1w2-deployment-preview' bin/chief-of-staff >/dev/null && pass "chief-of-staff dispatches live preview" || fail "live preview dispatch missing"
grep -F -- '--live-q1w2-deployment-status' bin/chief-of-staff >/dev/null && pass "chief-of-staff dispatches live status" || fail "live status dispatch missing"

PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/teacher-ai-workstation-pycache" python3 -m py_compile "$LIVE" "$RENDERER" "$CONN" >/dev/null 2>&1 && pass "C2C1 Python syntax passes" || fail "C2C1 Python syntax fails"
CANVAS_LLM_CONNECTION_TEST_MODE=1 python3 "$LIVE" self-test >/dev/null 2>&1 && pass "live q1w2 deployment self-test passes" || fail "live q1w2 deployment self-test fails"
bash "$LIVE_TEST" >/tmp/c2c1-live-test.txt 2>&1 && pass "live q1w2 deployment regression passes" || { cat /tmp/c2c1-live-test.txt; fail "live q1w2 deployment regression fails"; }

CANVAS_LLM_CONNECTION_TEST_MODE=1 bin/chief-of-staff --live-q1w2-deployment-preview | grep -Fq 'LIVE Q1W2 DEPLOYMENT' && pass "live preview header" || fail "live preview header missing"
CANVAS_LLM_CONNECTION_TEST_MODE=1 CANVAS_LLM_LIVE_Q1W2_APPROVED=1 bin/chief-of-staff --live-q1w2-deployment-status | grep -Fq 'Verification:' && pass "live status header" || fail "live status header missing"

python3 - <<'PY' >/dev/null 2>&1
from pathlib import Path
import sys
sys.path.insert(0, str(Path('.').resolve()))
from scripts.canvas_llm_phase22 import live_q1w2_deployment as live
from scripts.canvas_llm_phase22 import canvas_connection as conn
assert live.live_deployment_has_no_network()
assert conn.connection_has_no_network_writes()
PY
[[ $? -eq 0 ]] && pass "C2C1 layer has no unauthorized network writes" || fail "C2C1 security checks failed"

echo
echo "Summary"
echo "-------"
printf 'PASS: %s\n' "$PASS_COUNT"
printf 'WARN: %s\n' "$WARN_COUNT"
printf 'FAIL: %s\n' "$FAIL_COUNT"
[[ "$FAIL_COUNT" -eq 0 ]]
