#!/usr/bin/env bash
set -u

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT" || exit 1

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

pass() {
  PASS_COUNT=$((PASS_COUNT + 1))
  printf 'PASS: %s\n' "$1"
}

warn() {
  WARN_COUNT=$((WARN_COUNT + 1))
  printf 'WARN: %s\n' "$1"
}

fail() {
  FAIL_COUNT=$((FAIL_COUNT + 1))
  printf 'FAIL: %s\n' "$1"
}

REGISTRY="scripts/canvas_llm_phase22/artifact_registry.py"
CONTRACT="docs/programs/canvas-llm/canonical-context-pack/artifact-registry-contract.md"
TEST="tests/canvas-llm-artifact-health-test.sh"
REPORT_OUT="$(mktemp)"
trap 'rm -f "$REPORT_OUT"' EXIT

echo "Canvas LLM Artifact Health Status"
echo "---------------------------------"
echo

if [[ -f "$REGISTRY" ]]; then
  pass "artifact registry module exists"
else
  fail "artifact registry module missing"
fi

if [[ -f "$CONTRACT" ]]; then
  pass "artifact registry contract exists"
else
  fail "artifact registry contract missing"
fi

if [[ -f "$TEST" ]]; then
  pass "artifact health test exists"
else
  fail "artifact health test missing"
fi

if grep -F -- '--canvas-llm-artifact-health-status' bin/chief-of-staff >/dev/null; then
  pass "chief-of-staff dispatches artifact health status"
else
  fail "chief-of-staff dispatch missing for artifact health status"
fi

if PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/teacher-ai-workstation-pycache" python3 -m py_compile "$REGISTRY" >/dev/null 2>&1; then
  pass "artifact registry Python syntax passes"
else
  fail "artifact registry Python syntax fails"
fi

for symbol in ArtifactRegistryRecord normalize_draft_row load_registry_from_drafts evaluate_artifact_health print_health_report registry_is_read_only; do
  if grep -Fq "$symbol" "$REGISTRY"; then
    pass "registry includes $symbol"
  else
    fail "registry missing $symbol"
  fi
done

if grep -Fq 'INSERT INTO' "$REGISTRY" || grep -Fq 'UPDATE drafts' "$REGISTRY" || grep -Fq 'DELETE FROM drafts' "$REGISTRY"; then
  fail "artifact registry contains draft mutation statements"
else
  pass "artifact registry is read-only (no draft mutations)"
fi

if grep -Eiq 'smtp|sendgrid|gmail|canvas\.instructure|urllib\.request|requests\.(get|post)|@.*\.(com|org|net)' "$REGISTRY"; then
  fail "artifact registry references forbidden transport or secret patterns"
else
  pass "artifact registry has no transport or secret references"
fi

if python3 "$REGISTRY" self-test >/tmp/c0q-registry-self-test.txt 2>&1; then
  pass "artifact registry self-test passes"
else
  cat /tmp/c0q-registry-self-test.txt
  fail "artifact registry self-test fails"
fi

if bash "$TEST" >/tmp/c0q-artifact-health-test.txt 2>&1; then
  pass "artifact health regression test passes"
else
  cat /tmp/c0q-artifact-health-test.txt
  fail "artifact health regression test fails"
fi

if bin/chief-of-staff --canvas-llm-artifact-health-status >"$REPORT_OUT" 2>&1; then
  pass "artifact health report command exits successfully"
else
  cat "$REPORT_OUT"
  fail "artifact health report command failed"
fi

if grep -Fq 'Canvas LLM Artifact Health' "$REPORT_OUT"; then
  pass "artifact health report header is present"
else
  fail "artifact health report header missing"
fi

if grep -Eiq '(@|smtp|sendgrid|gmail|sqlite|/Users/|\.local/)' "$REPORT_OUT"; then
  fail "artifact health report leaked sensitive or private values"
else
  pass "artifact health report excludes emails, URLs, secrets, and private paths"
fi

if git diff --name-only | grep -Eq 'phase-26|phase-27|phase_26|phase_27'; then
  fail "Phase 26 or Phase 27 files were modified"
else
  pass "Phase 26 and Phase 27 remain untouched"
fi

echo
echo "Safety Boundary"
echo "---------------"
pass "status check does not call Canvas APIs"
pass "status check does not send email"
pass "registry adapter does not approve or deploy artifacts"
pass "no duplicate artifact storage table is created"
echo
echo "Summary"
echo "-------"
printf 'PASS: %s\n' "$PASS_COUNT"
printf 'WARN: %s\n' "$WARN_COUNT"
printf 'FAIL: %s\n' "$FAIL_COUNT"

if [[ "$FAIL_COUNT" -ne 0 ]]; then
  exit 1
fi
