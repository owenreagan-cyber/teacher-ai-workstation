#!/usr/bin/env bash
set -u

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT" || exit 1

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

pass() { PASS_COUNT=$((PASS_COUNT + 1)); printf 'PASS: %s\n' "$1"; }
fail() { FAIL_COUNT=$((FAIL_COUNT + 1)); printf 'FAIL: %s\n' "$1"; }

DETECTOR="scripts/canvas_llm_phase22/canvas_duplicate_detector.py"
CLEANUP="scripts/canvas_llm_phase22/canvas_cleanup_manager.py"
COMM="scripts/canvas_llm_phase22/communication_status.py"
DUP_TEST="tests/canvas-llm-duplicate-detection-test.sh"
CLEANUP_TEST="tests/canvas-llm-cleanup-safety-test.sh"
COMM_TEST="tests/canvas-llm-communication-status-test.sh"

echo "Canvas LLM Canvas Hygiene Status"
echo "--------------------------------"
echo

for file in "$DETECTOR" "$CLEANUP" "$COMM"; do
  [[ -f "$file" ]] && pass "$(basename "$file") exists" || fail "$(basename "$file") missing"
done

grep -F -- '--canvas-duplicate-scan' bin/chief-of-staff >/dev/null && pass "chief-of-staff dispatches duplicate scan" || fail "duplicate scan dispatch missing"
grep -F -- '--canvas-cleanup-preview' bin/chief-of-staff >/dev/null && pass "chief-of-staff dispatches cleanup preview" || fail "cleanup preview dispatch missing"
grep -F -- '--communication-status' bin/chief-of-staff >/dev/null && pass "chief-of-staff dispatches communication status" || fail "communication status dispatch missing"

PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/teacher-ai-workstation-pycache" python3 -m py_compile "$DETECTOR" "$CLEANUP" "$COMM" >/dev/null 2>&1 && pass "C2C0 Python syntax passes" || fail "C2C0 Python syntax fails"

python3 "$DETECTOR" self-test >/dev/null 2>&1 && pass "duplicate detector self-test passes" || fail "duplicate detector self-test fails"
python3 "$CLEANUP" self-test >/dev/null 2>&1 && pass "cleanup manager self-test passes" || fail "cleanup manager self-test fails"
python3 "$COMM" self-test >/dev/null 2>&1 && pass "communication status self-test passes" || fail "communication status self-test fails"

bash "$DUP_TEST" >/tmp/c2c0-dup-test.txt 2>&1 && pass "duplicate detection regression passes" || { cat /tmp/c2c0-dup-test.txt; fail "duplicate detection regression fails"; }
bash "$CLEANUP_TEST" >/tmp/c2c0-cleanup-test.txt 2>&1 && pass "cleanup safety regression passes" || { cat /tmp/c2c0-cleanup-test.txt; fail "cleanup safety regression fails"; }
bash "$COMM_TEST" >/tmp/c2c0-comm-test.txt 2>&1 && pass "communication status regression passes" || { cat /tmp/c2c0-comm-test.txt; fail "communication status regression fails"; }

bin/chief-of-staff --canvas-duplicate-scan | grep -Fq 'Canvas Duplicate Scan' && pass "duplicate scan report header" || fail "duplicate scan report header missing"
bin/chief-of-staff --canvas-cleanup-preview | grep -Fq 'Cleanup Preview' && pass "cleanup preview report header" || fail "cleanup preview report header missing"
bin/chief-of-staff --communication-status | grep -Fq 'Communication System' && pass "communication status report header" || fail "communication status report header missing"

python3 - <<'PY' >/dev/null 2>&1
from pathlib import Path
import sys
sys.path.insert(0, str(Path('.').resolve()))
from scripts.canvas_llm_phase22 import canvas_duplicate_detector as dd
from scripts.canvas_llm_phase22 import canvas_cleanup_manager as cm
from scripts.canvas_llm_phase22 import communication_status as cs
assert dd.duplicate_detector_has_no_writes()
assert cm.cleanup_manager_has_no_automatic_deletion()
assert cs.communication_has_no_sends()
PY
[[ $? -eq 0 ]] && pass "C2C0 layer has no writes, deletions, or sends" || fail "C2C0 security checks failed"

echo
echo "Summary"
echo "-------"
printf 'PASS: %s\n' "$PASS_COUNT"
printf 'WARN: %s\n' "$WARN_COUNT"
printf 'FAIL: %s\n' "$FAIL_COUNT"
[[ "$FAIL_COUNT" -eq 0 ]]
