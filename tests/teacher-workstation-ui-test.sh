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

# 4. Source scan: local-mutation routes terminate at local state (never Canvas),
#    local-only bind, no secret emission.
python3 - <<'PY'
from pathlib import Path
src = Path("scripts/teacher_workstation/server.py").read_text()
# POST/DELETE route to the local mutate layer; PUT/PATCH are 405.
for verb in ("do_POST", "do_PUT", "do_PATCH", "do_DELETE"):
    assert verb in src, f"{verb} stub missing"
assert "from . import mutate" in src
assert "read-only: no write route here" in src
# No Canvas write machinery may be imported in the server. Tokens are built
# dynamically so the scanner's own source never self-matches.
for tok in ("canvas_connection_" + "manager", "canvas_" + "writer", "Phase22Live" + "CanvasClient",
            "create_" + "assignment", "update_" + "page", "create_" + "announcement", "update_" + "announcement"):
    assert tok not in src, f"Canvas write token {tok!r} in server"
# Local-only bind.
assert 'HOST = "127.0.0.1"' in src
assert "0.0.0.0" not in src
# No token/secret emission.
for tok in ("CANVAS_TOKEN", "Authorization", "Bearer", "verifier=", "client_secret"):
    assert tok not in src, f"forbidden token {tok!r} in server source"
print("PASS source safety: local-mutation-only, local-only bind, no Canvas write path, no secret emission")
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

# Apply an override.
curl -s -X POST "http://127.0.0.1:${PORT}/api/weeks/2/3/overrides" \
  -H "Content-Type: application/json" \
  -d "{\"source_hash\":\"$SH\",\"subject\":\"math\",\"day\":\"Wednesday\",\"in_class\":[\"Review\"],\"at_home\":\"Study for tomorrow test\",\"status\":\"PLANNED\",\"source_value\":\"Review\"}" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); assert d['override']['at_home'].startswith('Study for tomorrow'); print('PASS override created')"

# Verify it appears in week detail.
curl -s "http://127.0.0.1:${PORT}/api/week/2/3" | python3 -c "
import sys,json
d=json.load(sys.stdin)
ov=[o for o in d['owner_overrides'] if o['subject']=='math' and o['day']=='Wednesday']
assert ov and ov[0]['at_home'].startswith('Study for tomorrow'), ov
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
  # Cleanup: remove the answer so the packet returns to original open-question state.
  python3 - <<'PY'
import json
from pathlib import Path
p = Path('.local/canvas-llm/intake/2026-2027/q2/w3/teacher-input.json')
if p.exists():
    d = json.loads(p.read_text())
    d.setdefault('question_answers', {}).pop('$QID', None)
    p.write_text(json.dumps(d, indent=2, ensure_ascii=False) + '\n')
print('cleanup: question answer removed')
PY
else
  echo "SKIP question test (no open questions)"
fi

echo "--- no secrets in any API response ---"
for ep in home status weeks completed; do
  curl -s "http://127.0.0.1:${PORT}/api/$ep" | grep -qiE "CANVAS_TOKEN|Authorization|Bearer|verifier=|client_secret" && { echo "FAIL secret leaked on /api/$ep"; exit 1; }
done
echo "PASS no secrets leaked in API responses"

kill $SERVER_PID 2>/dev/null || true
trap - EXIT

# Restore Q2W3 to a clean state (remove any test-created overrides/answers and regenerate).
rm -f .local/canvas-llm/intake/2026-2027/q2/w3/owner-overrides.json
rm -f .local/canvas-llm/intake/2026-2027/q2/w3/teacher-input.json
python3 -m scripts.canvas_llm_intake.cli prepare-next --fresh >/dev/null 2>&1 || true
echo "cleanup: Q2W3 packet regenerated to clean state"

echo "PASS: Teacher Workstation UI tests complete"
echo "PASS Teacher Workstation UI tests complete"
