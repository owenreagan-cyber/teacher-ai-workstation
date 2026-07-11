#!/usr/bin/env bash
set -euo pipefail

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

pass() { PASS_COUNT=$((PASS_COUNT + 1)); printf 'PASS: %s\n' "$1"; }
warn() { WARN_COUNT=$((WARN_COUNT + 1)); printf 'WARN: %s\n' "$1"; }
fail() { FAIL_COUNT=$((FAIL_COUNT + 1)); printf 'FAIL: %s\n' "$1"; }

check_file() {
  if [[ -f "$1" ]]; then
    pass "$2 exists"
  else
    fail "$2 missing"
  fi
}

echo "Canvas LLM Phase 23 Weekly Content Production Engine Status"
echo "-----------------------------------------------------------"

M=scripts/canvas_llm_phase23/phase23_content_engine.py
V=scripts/canvas_llm_phase23/validate_phase23_packet.py
A=apps/weekly-content-production

for f in \
  "$M" \
  "$V" \
  fixtures/canvas-llm/phase-23/synthetic-weekly-content.json \
  fixtures/canvas-llm/phase-23/synthetic-weekly-content.manifest.json \
  docs/programs/canvas-llm/phase-23-weekly-content-production-engine/README.md \
  docs/programs/canvas-llm/phase-23-weekly-content-production-engine/implementation-report.md \
  "$A/index.html" \
  "$A/styles.css" \
  "$A/workstation.js" \
  tests/canvas-llm-phase-23-weekly-content-production-engine-test.sh \
  scripts/canvas-llm-phase-23-weekly-content-production-engine-status.sh \
  bin/chief-of-staff; do
  check_file "$f" "$f"
done

PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/teacher-ai-workstation-pycache" python3 -m py_compile "$M" "$V" >/tmp/p23py.txt 2>&1 && pass "Python syntax passes" || { cat /tmp/p23py.txt; fail "Python syntax fails"; }

T=$(mktemp -d "${TMPDIR:-/tmp}/phase23-status.XXXXXX")
trap 'rm -rf "$T"' EXIT

python3 "$M" build-demo --out "$T/demo.json" >/tmp/p23demo.txt 2>&1 && pass "demo packet builds" || { cat /tmp/p23demo.txt; fail "demo packet build fails"; }
python3 "$V" "$T/demo.json" >"$T/validate.txt" 2>&1 && pass "demo packet validates" || { cat "$T/validate.txt"; fail "demo packet validation fails"; }

grep -q '^WARN: due-time.unresolved' "$T/validate.txt" && pass "due-time unresolved warning is present" || fail "due-time warning missing"
grep -q '^PASS: reading-test-14.checkout Reading Test 14 correctly has no checkout reminder$' "$T/validate.txt" && pass "Reading Test 14 no-checkout PASS is present" || fail "Reading Test 14 no-checkout PASS missing"
grep -q '^FAIL: 0$' "$T/validate.txt" && pass "validator reported zero failures" || fail "validator reported failures"
grep -q '^WARN: 1$' "$T/validate.txt" && pass "validator reported one warning" || fail "validator warning count incorrect"

python3 "$M" self-test >/tmp/p23self.txt 2>&1 && pass "self-test passes" || { cat /tmp/p23self.txt; fail "self-test fails"; }

if git ls-files .local | grep -q .; then
  fail ".local output is tracked by git"
else
  pass ".local output is not tracked by git"
fi

warn "Canvas assignment due-time convention remains owner-unresolved"

echo
echo "Summary"
echo "-------"
echo "PASS: ${PASS_COUNT}"
echo "WARN: ${WARN_COUNT}"
echo "FAIL: ${FAIL_COUNT}"

[[ "${FAIL_COUNT}" -eq 0 ]]
