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

# 4. Source scan: no write-verb routes, no secret emission, local-only bind.
python3 - <<'PY'
from pathlib import Path
src = Path("scripts/teacher_workstation/server.py").read_text()
# Only do_GET exists as a route; write verbs are 405 stubs.
for verb in ("do_POST", "do_PUT", "do_PATCH", "do_DELETE"):
    assert verb in src, f"{verb} stub missing"
# 405 responses, not real handlers.
assert "read-only: POST disabled" in src
assert "read-only: PUT disabled" in src
assert "read-only: PATCH disabled" in src
assert "read-only: DELETE disabled" in src
# Local-only bind.
assert 'HOST = "127.0.0.1"' in src
assert "0.0.0.0" not in src
# No token/secret emission.
for tok in ("CANVAS_TOKEN", "Authorization", "Bearer", "verifier=", "client_secret"):
    assert tok not in src, f"forbidden token {tok!r} in server source"
print("PASS source safety: read-only routes, local-only bind, no secret emission")
PY

# 5. Live server smoke test (start, GET routes, verify read-only + no secrets).
PORT=4310
python3 -m scripts.teacher_workstation > /tmp/tw-server.log 2>&1 &
SERVER_PID=$!
trap 'kill $SERVER_PID 2>/dev/null || true' EXIT

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
assert d['day_states']['math']['Wednesday'] == 'REVIEW'
assert len(d['open_questions']) == 2
print('PASS /api/week/2/3: Q2W3 math Review + 2 open questions')
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

echo "--- write verbs return 405 (no write path) ---"
for verb in POST PUT PATCH DELETE; do
  code="$(curl -s -o /dev/null -w "%{http_code}" -X "$verb" "http://127.0.0.1:${PORT}/api/weeks")"
  test "$code" = "405" || { echo "FAIL $verb returned $code (expected 405)"; exit 1; }
done
echo "PASS all write verbs return 405"

echo "--- no secrets in any API response ---"
for ep in home status weeks completed; do
  curl -s "http://127.0.0.1:${PORT}/api/$ep" | grep -qiE "CANVAS_TOKEN|Authorization|Bearer|verifier=|client_secret" && { echo "FAIL secret leaked on /api/$ep"; exit 1; }
done
echo "PASS no secrets leaked in API responses"

kill $SERVER_PID 2>/dev/null || true
trap - EXIT

echo "PASS: Teacher Workstation UI tests complete"
echo "PASS Teacher Workstation UI tests complete"
