#!/usr/bin/env bash
set -u

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

pass() { PASS_COUNT=$((PASS_COUNT + 1)); printf 'PASS: %s\n' "$1"; }
warn() { WARN_COUNT=$((WARN_COUNT + 1)); printf 'WARN: %s\n' "$1"; }
fail() { FAIL_COUNT=$((FAIL_COUNT + 1)); printf 'FAIL: %s\n' "$1"; }

echo "Phase 27 Canvas readiness and safety diff status"
echo "-------------------------------------------------"
echo "(Phase 27B recovery in progress: core safety subsystems below are real;"
echo " see docs/programs/canvas-llm/phase-27-canvas-readiness-and-safety-diff/"
echo " phase-27-gap-audit.md for subsystems not yet built in this checkpoint.)"

M=scripts/canvas_llm_phase27
for f in \
  "$M/__init__.py" \
  "$M/models.py" \
  "$M/canonicalize.py" \
  "$M/canvas_snapshot.py" \
  "$M/matching.py" \
  "$M/comparison.py" \
  "$M/safety_diff.py" \
  "$M/dependency_graph.py" \
  "$M/transport.py" \
  "$M/freshness.py" \
  "$M/ledger.py" \
  "$M/approval_gate.py" \
  "$M/manifest.py" \
  "$M/phase27_readiness.py" \
  "$M/validate_phase27.py" \
  fixtures/canvas-llm/phase-27/synthetic-canvas-snapshot.json \
  fixtures/canvas-llm/phase-27/synthetic-canvas-snapshot-stale.json \
  fixtures/canvas-llm/phase-27/synthetic-canvas-snapshot-expired.json \
  fixtures/canvas-llm/phase-27/alias-registry.json \
  docs/programs/canvas-llm/phase-27-canvas-readiness-and-safety-diff/phase-27-gap-audit.md \
  docs/programs/canvas-llm/phase-27-canvas-readiness-and-safety-diff/validator-quality-audit.md \
  docs/programs/canvas-llm/phase-27-canvas-readiness-and-safety-diff/cross-phase-validator-audit.md \
  tests/canvas-llm-phase-27-canvas-readiness-and-safety-diff-test.sh; do
  if [[ -f "$f" ]]; then
    pass "$f exists"
  else
    fail "$f missing"
  fi
done

PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/teacher-ai-workstation-pycache" python3 -m py_compile "$M"/*.py \
  >/tmp/p27py.txt 2>&1 && pass "Python syntax passes" || { cat /tmp/p27py.txt; fail "Python syntax fails"; }

T=$(mktemp -d "${TMPDIR:-/tmp}/phase27-status.XXXXXX")
trap 'rm -rf "$T"' EXIT
P=apps/unified-weekly-production/data/phase26-demo.json
S=fixtures/canvas-llm/phase-27/synthetic-canvas-snapshot.json
O="$T/phase27.json"
LEDGER="$T/ledger.db"

python3 "$M/phase27_readiness.py" build --week Q1W5 --phase26-packet "$P" --snapshot "$S" \
  --output "$O" --ledger "$LEDGER" >"$T/build.txt" 2>&1 && pass "build produces a manifest" \
  || { cat "$T/build.txt"; fail "build fails"; }

python3 "$M/validate_phase27.py" "$O" >"$T/validate.txt" 2>&1 && pass "validate passes on a real build" \
  || { cat "$T/validate.txt"; fail "validate fails on a real build"; }

python3 "$M/phase27_readiness.py" compare --manifest "$O" --snapshot "$S" >"$T/compare.txt" 2>&1 \
  && pass "compare recomputes and matches a real build" || { cat "$T/compare.txt"; fail "compare fails"; }

python3 "$M/phase27_readiness.py" compare --manifest "$T/nope.json" --snapshot "$T/nope2.json" \
  >/dev/null 2>&1
[[ $? -ne 0 ]] && pass "compare is not a no-op (fails nonzero on invalid input)" \
  || fail "compare is a no-op"

python3 - "$O" <<'PY' >/tmp/p27statuses.txt 2>&1
import json, sys
payload = json.loads(open(sys.argv[1], encoding="utf-8").read())
statuses = {item["comparisonStatus"] for item in payload["safetyDiff"]}
required = {"CREATE", "UPDATE", "UNCHANGED", "BLOCKED", "CONFLICT", "OMIT", "DELETE_CANDIDATE"}
missing = required - statuses
assert not missing, f"missing: {missing}"
assert payload["deploymentManifestV1"]["executable"] is False
print("ok")
PY
[[ $? -eq 0 ]] && pass "all seven Safety Diff states present, executable=false" \
  || { cat /tmp/p27statuses.txt; fail "Safety Diff state coverage incomplete"; }

python3 "$M/phase27_readiness.py" health-check --manifest "$O" >"$T/health.txt" 2>&1 \
  && pass "health-check runs deterministic checks" || { cat "$T/health.txt"; fail "health-check fails"; }

python3 "$M/phase27_readiness.py" export --manifest "$O" --output-root "$T/exports" >"$T/export.txt" 2>&1 \
  && pass "export writes a real, validated package" || { cat "$T/export.txt"; fail "export fails"; }

if grep -q "expectedStatus" "$S"; then
  fail "fixture forces classification via expectedStatus"
else
  pass "no expectedStatus fixture-forcing"
fi

python3 "$M/phase27_readiness.py" ledger-status --ledger "$LEDGER" >"$T/ledger-status.txt" 2>&1 \
  && pass "ledger-status inspects the real SQLite ledger" || { cat "$T/ledger-status.txt"; fail "ledger-status fails"; }

python3 - <<'PY' >/tmp/p27transport.txt 2>&1
import sys
sys.path.insert(0, ".")
from scripts.canvas_llm_phase27.transport import DisabledCanvasTransport, MutationNotAllowedError
t = DisabledCanvasTransport()
try:
    t.create_page()
    raise AssertionError("mutation not rejected")
except MutationNotAllowedError:
    pass
print("ok")
PY
[[ $? -eq 0 ]] && pass "transport mutation rejection is real (raises MutationNotAllowedError)" \
  || { cat /tmp/p27transport.txt; fail "transport mutation rejection is not real"; }

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
