#!/usr/bin/env bash
# Teacher Workstation read-only UI tests (local server, no Canvas, no writes).
set -euo pipefail

echo "Running Teacher Workstation UI tests..."

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

MODULES=(
  "scripts/teacher_workstation/__init__.py"
  "scripts/teacher_workstation/adapter.py"
  "scripts/teacher_workstation/server.py"
  "scripts/teacher_workstation/__main__.py"
)
PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/teacher-ai-workstation-pycache" python3 -m py_compile "${MODULES[@]}"

# 1. Static asset presence.
for f in index.html styles.css app.js; do
  test -f "apps/teacher-workstation/$f" || { echo "FAIL missing asset $f"; exit 1; }
done
echo "PASS static assets present"

# 2. Adapter self-test (pure, no network).
python3 -m scripts.teacher_workstation.adapter self-test
echo "PASS adapter self-test"

# 3. Server self-test (no write-verb handlers beyond 405 stubs).
python3 -m scripts.teacher_workstation.server self-test
echo "PASS server self-test"

# 4. Source scan: local-mutation routes terminate at local state; the ONLY path
#    to Canvas is the narrowly-scoped guarded deployment coordinator (never a
#    generic proxy, never a direct phase22 write-transport import); local-only
#    bind; no secret emission.
python3 - <<'PY'
from pathlib import Path
src = Path("scripts/teacher_workstation/server.py").read_text()
mut = Path("scripts/teacher_workstation/mutate.py").read_text()
dep = Path("scripts/teacher_workstation/deploy.py").read_text()
# POST/DELETE route to the local mutate layer; PUT/PATCH are 405.
for verb in ("do_POST", "do_PUT", "do_PATCH", "do_DELETE"):
    assert verb in src, f"{verb} stub missing"
assert "from . import mutate" in src
assert "read-only: no write route here" in src
# Approval routes exist and are local-only.
assert 'parts[4] == "approve"' in src, "approve route missing"
assert 'parts[4] == "revoke-approval"' in src, "revoke-approval route missing"
# Guarded deployment routes exist and require production mode.
assert 'parts[4] == "preflight"' in src, "preflight route missing"
assert 'parts[4] == "deploy"' in src, "deploy route missing"
assert "production" in dep and "production=true" in dep, "deploy must require production mode"
# The UI server must NOT import phase22 write transport directly; it reaches
# Canvas only through scripts/canvas_llm_deploy (the coordinator).
for f in (src, mut, dep):
    for tok in ("canvas_connection_" + "manager", "canvas_" + "writer", "Phase22Live" + "CanvasClient",
                "create_" + "assignment", "update_" + "page", "create_" + "announcement",
                "update_" + "announcement"):
        assert tok not in f, f"Canvas write token {tok!r} leaked into UI server source"
assert "scripts.canvas_llm_deploy" in dep, "deploy routes must delegate to the deployment coordinator"
# No generic Canvas proxy routes.
for f in (src, dep):
    for tok in ("/canvas/request", "/canvas/object", "/canvas/update", "/canvas/"):
        assert tok not in f, f"generic Canvas proxy token {tok!r} in UI server source"
# Local-only bind.
assert 'HOST = "127.0.0.1"' in src
assert "0.0.0.0" not in src
# No token/secret emission in UI server source.
for f in (src, mut, dep):
    for tok in ("CANVAS_TOKEN", "Authorization", "Bearer", "verifier=", "client_secret"):
        assert tok not in f, f"forbidden token {tok!r} in UI server source"
print("PASS source safety: guarded-deploy-only Canvas path, no proxy, local bind, no secrets")
PY

# 5. Live server smoke test (start, GET routes, verify read-only + no secrets).
# Hermetic guard: snapshot the mutable Q2W3 owner state so this test never
# corrupts real owner input (owner overrides / teacher input / approvals).
# Restored at the end.
SNAP_DIR="$(mktemp -d)"
Q2W3_DIR=".local/canvas-llm/intake/2026-2027/q2/w3"
for _f in owner-overrides.json teacher-input.json approvals/approval-manifest.json; do
  if [ -f "${Q2W3_DIR}/${_f}" ]; then
    mkdir -p "${SNAP_DIR}/$(dirname "${_f}")"
    cp "${Q2W3_DIR}/${_f}" "${SNAP_DIR}/${_f}"
  fi
done

PORT=4310
python3 -m scripts.teacher_workstation > /tmp/tw-server.log 2>&1 &
SERVER_PID=$!
# The snapshot restore must run on ANY exit (including early FAIL), otherwise a
# failing assertion corrupts real .local owner state. Trap both cleanup steps.
restore_snapshot() {
  for _f in owner-overrides.json teacher-input.json approvals/approval-manifest.json; do
    if [ -f "${SNAP_DIR}/${_f}" ]; then
      mkdir -p "${Q2W3_DIR}/$(dirname "${_f}")"
      cp "${SNAP_DIR}/${_f}" "${Q2W3_DIR}/${_f}"
    else
      rm -f "${Q2W3_DIR}/${_f}"
    fi
  done
  rm -rf "${SNAP_DIR}"
  # Regenerate the packet from the restored owner state (no network).
  python3 - <<'PY' >/dev/null 2>&1 || true
from scripts.canvas_llm_intake import intake
intake.build_intake(quarter=2, week=3, fresh=False, canvas=None, include_canvas_context=False)
PY
}
trap 'kill $SERVER_PID 2>/dev/null || true; restore_snapshot' EXIT

# Wait for the server to come up.
for _ in $(seq 1 30); do
  if curl -s -o /dev/null "http://127.0.0.1:${PORT}/api/home"; then break; fi
  sleep 0.3
done

echo "--- home ---"
HOME_JSON="$(curl -s "http://127.0.0.1:${PORT}/api/home")"
echo "$HOME_JSON" | python3 -c "import sys,json; d=json.load(sys.stdin); assert 'today' in d and 'weeks' in d; print('PASS /api/home shape')"

echo "--- status ---"
curl -s "http://127.0.0.1:${PORT}/api/status" | python3 -c "import sys,json; d=json.load(sys.stdin); assert 'overall' in d; print('PASS /api/status shape')"

echo "--- weeks ---"
curl -s "http://127.0.0.1:${PORT}/api/weeks" | python3 -c "import sys,json; d=json.load(sys.stdin); assert isinstance(d, list); print('PASS /api/weeks shape')"

echo "--- week detail (Q2W3) ---"
curl -s "http://127.0.0.1:${PORT}/api/week/2/3" | python3 -c "
import sys,json
d=json.load(sys.stdin)
assert d['week_code'] == 'Q2W3'
# Structural assertions only — Q2W3 planning state changes as owner input
# advances, so do not assert a specific lifecycle or pending-day label.
assert set(d['day_states'].keys()) >= {'math','reading_spelling','language_arts','science','history'}
assert isinstance(d['open_questions'], list)
assert isinstance(d['assignments'], list)
print('PASS /api/week/2/3: Q2W3 structural shape')
"

echo "--- completed latest ---"
curl -s "http://127.0.0.1:${PORT}/api/completed" | python3 -c "
import sys,json
d=json.load(sys.stdin)
assert d['latest']['week_code'] == 'Q2W2'
print('PASS /api/completed: Q2W2')
"

echo "--- index.html served ---"
curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:${PORT}/" | grep -q 200 && echo "PASS / serves 200"

echo "--- PUT/PATCH remain 405 (not implemented) ---"
for verb in PUT PATCH; do
  code="$(curl -s -o /dev/null -w "%{http_code}" -X "$verb" "http://127.0.0.1:${PORT}/api/weeks")"
  test "$code" = "405" || { echo "FAIL $verb returned $code (expected 405)"; exit 1; }
done
echo "PASS PUT/PATCH return 405"

echo "--- POST/DELETE to non-planning routes return 405 (no arbitrary write) ---"
code="$(curl -s -o /dev/null -w "%{http_code}" -X POST "http://127.0.0.1:${PORT}/api/weeks")"
test "$code" = "405" || { echo "FAIL bare POST /api/weeks returned $code"; exit 1; }
echo "PASS bare POST /api/weeks returns 405 (only planning routes allowed)"

echo "--- local mutation: create + read back + restore an owner override (Q2W3 Math Wednesday) ---"
# First read current source_hash.
SH="$(curl -s "http://127.0.0.1:${PORT}/api/week/2/3" | python3 -c "import sys,json; print(json.load(sys.stdin)['source_hash'])")"

# Apply an override using a clearly test-only value (never a value that could
# be confused with real owner input like "Study for tomorrow's test.").
curl -s -X POST "http://127.0.0.1:${PORT}/api/weeks/2/3/overrides" \
  -H "Content-Type: application/json" \
  -d "{\"source_hash\":\"$SH\",\"subject\":\"math\",\"day\":\"Wednesday\",\"in_class\":[\"Review\"],\"at_home\":\"TEST OVERRIDE — DO NOT USE\",\"status\":\"PLANNED\",\"source_value\":\"Review\"}" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); assert d['override']['at_home'].startswith('TEST OVERRIDE'); print('PASS override created')"

# Verify it appears in week detail.
curl -s "http://127.0.0.1:${PORT}/api/week/2/3" | python3 -c "
import sys,json
d=json.load(sys.stdin)
ov=[o for o in d['owner_overrides'] if o['subject']=='math' and o['day']=='Wednesday']
assert ov and ov[0]['at_home'].startswith('TEST OVERRIDE'), ov
print('PASS override visible in week detail')
"

# Restore source (cleanup — return packet to original state).
curl -s -X POST "http://127.0.0.1:${PORT}/api/weeks/2/3/restore-source" \
  -H "Content-Type: application/json" \
  -d "{\"source_hash\":\"$SH\",\"subject\":\"math\",\"day\":\"Wednesday\"}" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); assert d['removed'] is True; print('PASS override restored (cleanup)')"

echo "--- stale edit rejected ---"
curl -s -X POST "http://127.0.0.1:${PORT}/api/weeks/2/3/overrides" \
  -H "Content-Type: application/json" \
  -d '{"source_hash":"WRONG-HASH","subject":"math","day":"Wednesday","at_home":"x"}' \
  -o /dev/null -w "%{http_code}" | grep -q 409 && echo "PASS stale edit returns 409" || { echo "FAIL stale edit not rejected"; exit 1; }

echo "--- answer a question (then verify it is answered) ---"
QID="$(curl -s "http://127.0.0.1:${PORT}/api/week/2/3" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['open_questions'][0]['question_id'] if d['open_questions'] else '')")"
if [ -n "$QID" ]; then
  curl -s -X POST "http://127.0.0.1:${PORT}/api/weeks/2/3/questions/${QID}/answer" \
    -H "Content-Type: application/json" \
    -d "{\"source_hash\":\"$SH\",\"answer\":\"Test answer\"}" \
    | python3 -c "import sys,json; d=json.load(sys.stdin); assert d['answered']=='$QID'; print('PASS question answered')"
  # Cleanup: remove the injected answer so the packet returns to its prior state.
  # (The hermetic snapshot restore at the end is the authoritative cleanup.)
  QID="$QID" python3 - <<'PY'
import json, os
from pathlib import Path
p = Path('.local/canvas-llm/intake/2026-2027/q2/w3/teacher-input.json')
if p.exists():
    d = json.loads(p.read_text())
    d.setdefault('question_answers', {}).pop(os.environ['QID'], None)
    p.write_text(json.dumps(d, indent=2, ensure_ascii=False) + '\n')
print('cleanup: question answer removed')
PY
else
  echo "SKIP question test (no open questions)"
fi

echo "--- approval: unknown artifact type rejected (400) ---"
code="$(curl -s -o /dev/null -w "%{http_code}" -X POST "http://127.0.0.1:${PORT}/api/weeks/2/3/approve" \
  -H "Content-Type: application/json" \
  -d "{\"source_hash\":\"$SH\",\"subject\":\"math\",\"artifact_type\":\"bogus\",\"expected_artifact_hash\":\"x\"}")"
test "$code" = "400" || { echo "FAIL unknown artifact type returned $code (expected 400)"; exit 1; }
echo "PASS unknown artifact type rejected"

echo "--- approval: wrong artifact hash rejected (409 STALE) ---"
code="$(curl -s -o /dev/null -w "%{http_code}" -X POST "http://127.0.0.1:${PORT}/api/weeks/2/3/approve" \
  -H "Content-Type: application/json" \
  -d "{\"source_hash\":\"$SH\",\"subject\":\"math\",\"artifact_type\":\"page\",\"expected_artifact_hash\":\"WRONG\"}")"
test "$code" = "409" || { echo "FAIL wrong hash returned $code (expected 409)"; exit 1; }
echo "PASS wrong artifact hash rejected with 409"

echo "--- approval: approve Math page (happy path), verify provenance, revoke ---"
MATH_PAGE_HASH="$(curl -s "http://127.0.0.1:${PORT}/api/week/2/3" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['draft_hashes']['math']['page'])")"
curl -s -X POST "http://127.0.0.1:${PORT}/api/weeks/2/3/approve" \
  -H "Content-Type: application/json" \
  -d "{\"source_hash\":\"$SH\",\"subject\":\"math\",\"artifact_type\":\"page\",\"expected_artifact_hash\":\"$MATH_PAGE_HASH\"}" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); assert d['state']=='APPROVED'; print('PASS Math page approved')"
curl -s "http://127.0.0.1:${PORT}/api/week/2/3" | python3 -c "
import sys,json
d=json.load(sys.stdin)
rec=d['approval_records']['math']['page']
assert rec['state']=='APPROVED' and rec['approved_by']=='OWNER_UI', rec
print('PASS approval recorded with OWNER_UI provenance + hash binding')
"
curl -s -X POST "http://127.0.0.1:${PORT}/api/weeks/2/3/revoke-approval" \
  -H "Content-Type: application/json" \
  -d "{\"source_hash\":\"$SH\",\"subject\":\"math\",\"artifact_type\":\"page\"}" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); assert d['state']=='PENDING'; print('PASS Math page approval revoked')"

echo "--- approval: READY_TO_PUBLISH remains false after partial approval ---"
curl -s "http://127.0.0.1:${PORT}/api/week/2/3" | python3 -c "
import sys,json
d=json.load(sys.stdin)
assert d['ready_to_publish'] is False, 'partial approval must not reach READY_TO_PUBLISH'
print('PASS READY_TO_PUBLISH remains false after partial approval')
"

echo "--- deployment: preflight (dry-run) returns plan, no Canvas GET ---"
curl -s -X POST "http://127.0.0.1:${PORT}/api/weeks/2/3/preflight" \
  -H "Content-Type: application/json" -d '{"production": false}' \
  | python3 -c "
import sys,json
d=json.load(sys.stdin)
assert d['plan']['week_code']=='Q2W3', d
assert 'LIVE CANVAS CONTEXT UNAVAILABLE' in d['warnings'][0], d['warnings']
print('PASS dry-run preflight returns plan (no Canvas)')
"

echo "--- deployment: deploy without production mode is rejected ---"
code="$(curl -s -o /dev/null -w "%{http_code}" -X POST "http://127.0.0.1:${PORT}/api/weeks/2/3/deploy" \
  -H "Content-Type: application/json" \
  -d '{"preflight_id":"x","expected_source_hash":"","expected_approval_snapshot_hash":"","owner_confirmation":"DEPLOY Q2W3","production":false}')"
test "$code" = "400" || { echo "FAIL deploy without production returned $code (expected 400)"; exit 1; }
echo "PASS deploy without production rejected"

echo "--- deployment: no generic Canvas proxy route ---"
for ep in "canvas/request" "canvas/object" "canvas/update"; do
  code="$(curl -s -o /dev/null -w "%{http_code}" -X POST "http://127.0.0.1:${PORT}/api/weeks/2/3/$ep" -d '{}')"
  test "$code" = "405" || { echo "FAIL /api/weeks/2/3/$ep returned $code (expected 405)"; exit 1; }
done
echo "PASS no generic Canvas proxy route"

echo "--- no secrets in any API response ---"
for ep in home status weeks completed; do
  curl -s "http://127.0.0.1:${PORT}/api/$ep" | grep -qiE "CANVAS_TOKEN|Authorization|Bearer|verifier=|client_secret" && { echo "FAIL secret leaked on /api/$ep"; exit 1; }
done
echo "PASS no secrets leaked in API responses"

kill $SERVER_PID 2>/dev/null || true
trap - EXIT
restore_snapshot
echo "cleanup: Q2W3 packet restored from snapshot (no network)"

echo "PASS: Teacher Workstation UI tests complete"
echo "PASS Teacher Workstation UI tests complete"
