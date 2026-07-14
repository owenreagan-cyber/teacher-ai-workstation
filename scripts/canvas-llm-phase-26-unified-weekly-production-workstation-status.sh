#!/usr/bin/env bash
set -euo pipefail

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

pass() { PASS_COUNT=$((PASS_COUNT + 1)); printf 'PASS: %s\n' "$1"; }
warn() { WARN_COUNT=$((WARN_COUNT + 1)); printf 'WARN: %s\n' "$1"; }
fail() { FAIL_COUNT=$((FAIL_COUNT + 1)); printf 'FAIL: %s\n' "$1"; }

echo "Canvas LLM Phase 26 Unified Weekly Production Workstation Status"
echo "-----------------------------------------------------------------"

M=scripts/canvas_llm_phase26/phase26_workstation.py
V=scripts/canvas_llm_phase26/validate_phase26_state.py
A=apps/unified-weekly-production

for f in \
  "$M" \
  "$V" \
  scripts/canvas_llm_phase26/__init__.py \
  scripts/canvas_llm_phase26/models.py \
  scripts/canvas_llm_phase26/storage.py \
  scripts/canvas_llm_phase26/pipeline.py \
  scripts/canvas_llm_phase26/approval.py \
  scripts/canvas_llm_phase26/revisions.py \
  scripts/canvas_llm_phase26/readiness.py \
  scripts/canvas_llm_phase26/export_package.py \
  scripts/canvas_llm_phase26/deployment_manifest.py \
  docs/programs/canvas-llm/phase-26-unified-weekly-production-workstation/README.md \
  docs/programs/canvas-llm/phase-26-unified-weekly-production-workstation/architecture.md \
  docs/programs/canvas-llm/phase-26-unified-weekly-production-workstation/workflow.md \
  docs/programs/canvas-llm/phase-26-unified-weekly-production-workstation/state-model.md \
  docs/programs/canvas-llm/phase-26-unified-weekly-production-workstation/approval-model.md \
  docs/programs/canvas-llm/phase-26-unified-weekly-production-workstation/revision-history.md \
  docs/programs/canvas-llm/phase-26-unified-weekly-production-workstation/export-package.md \
  docs/programs/canvas-llm/phase-26-unified-weekly-production-workstation/deployment-manifest-preview.md \
  docs/programs/canvas-llm/phase-26-unified-weekly-production-workstation/implementation-report.md \
  "$A/index.html" \
  "$A/styles.css" \
  "$A/workstation.js" \
  docs/master-build-roadmap.md \
  docs/chief-of-staff-command-index-v1.md \
  tests/canvas-llm-phase-26-unified-weekly-production-workstation-test.sh \
  scripts/canvas-llm-phase-26-unified-weekly-production-workstation-status.sh \
  bin/chief-of-staff; do
  if [[ -f "$f" ]]; then
    pass "$f exists"
  else
    fail "$f missing"
  fi
done

PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/teacher-ai-workstation-pycache" python3 -m py_compile \
  "$M" \
  "$V" \
  scripts/canvas_llm_phase26/models.py \
  scripts/canvas_llm_phase26/storage.py \
  scripts/canvas_llm_phase26/pipeline.py \
  scripts/canvas_llm_phase26/approval.py \
  scripts/canvas_llm_phase26/revisions.py \
  scripts/canvas_llm_phase26/readiness.py \
  scripts/canvas_llm_phase26/export_package.py \
  scripts/canvas_llm_phase26/deployment_manifest.py >/tmp/p26py.txt 2>&1 && pass "Python syntax passes" || { cat /tmp/p26py.txt; fail "Python syntax fails"; }

T=$(mktemp -d "${TMPDIR:-/tmp}/phase26-status.XXXXXX")
trap 'rm -rf "$T"' EXIT
OUT="$T/phase26-demo.json"

PHASE26_LOCAL_ROOT="$T/local-root" python3 "$M" build-demo --week Q1W5 --output "$OUT" >/tmp/p26build.txt 2>&1 && pass "workstation packet builds" || { cat /tmp/p26build.txt; fail "workstation packet build fails"; }
python3 "$V" "$OUT" >"$T/validate.txt" 2>&1 && pass "workstation packet validates" || { cat "$T/validate.txt"; fail "workstation packet validation fails"; }

grep -q '^WARN: due-time.unresolved Canvas assignment due-time convention remains owner-unresolved$' "$T/validate.txt" && pass "due-time unresolved warning is present" || fail "due-time warning missing"
if grep -q '^FAIL: reading-test-14.checkout ' "$T/validate.txt"; then
  fail "Reading Test 14 produced a Checkout failure"
else
  pass "Reading Test 14 produces no Checkout failure"
fi
grep -q '^PASS: manifest.preview Deployment manifest preview is available$' "$T/validate.txt" && pass "deployment manifest preview PASS is present" || fail "deployment manifest preview PASS missing"
grep -q '^FAIL: 0$' "$T/validate.txt" && pass "validator reported zero failures" || fail "validator reported failures"

python3 - "$OUT" <<'PY'
import json
from pathlib import Path

payload = json.loads(Path(__import__('sys').argv[1]).read_text(encoding='utf-8'))
assert payload['schemaVersion'] == 1
assert payload['weekCode'] == 'Q1W5'
assert payload['validation']['failCount'] == 0
assert payload['validation']['warnCount'] == 1
assert len(payload['weekSelection']['weeks']) == 37
assert payload['weekSelection']['quarterWeekCounts'] == {'Q1': 9, 'Q2': 9, 'Q3': 9, 'Q4': 10}
assert any(item['issueType'] == 'Due-time unresolved' for item in payload['exceptionInbox'])
assert any(item['event'] == 'Reading Test 14' for item in payload['exceptionInbox'])
assert any(item['status'] == 'blocked' for item in payload['deploymentManifestPreview']['operations'])
print('PASS packet shape')
PY

if git ls-files '.local/*' | grep -q .; then
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
