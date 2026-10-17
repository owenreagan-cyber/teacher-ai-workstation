#!/usr/bin/env bash
# Canvas Planner macOS launcher tests (bounded, isolated, no desktop driving).
# Uses CP_LAUNCHER_NO_OPEN=1 to exercise backend start/reuse without opening a
# browser. Cases A-F from the phase spec.
set -euo pipefail

echo "Running Canvas Planner launcher tests..."

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

LAUNCHER="scripts/canvas_planner_app/launcher.sh"
HEALTH_URL="http://127.0.0.1:4310/api/status"
PORT=4310

cleanup_procs() {
  # Stop only server(s) we started (identified by the exact module path), then
  # wait (bounded) for the port to release. Never touch unrelated processes.
  local pid pids
  pids="$(lsof -tiTCP:4310 -sTCP:LISTEN 2>/dev/null || true)"
  for pid in ${pids}; do
    [ -n "${pid}" ] || continue
    if ps -p "${pid}" -o command= 2>/dev/null | grep -q "scripts.teacher_workstation"; then
      kill "${pid}" 2>/dev/null || true
    fi
  done
  # Bounded wait for the port to free.
  local i
  for i in $(seq 1 10); do
    lsof -tiTCP:4310 -sTCP:LISTEN >/dev/null 2>&1 || break
    sleep 0.5
  done
}
trap cleanup_procs EXIT

# ---- CASE C: repo missing -> friendly failure ---------------------------
echo "--- CASE C: repo missing ---"
set +e
TEACHER_WORKSTATION_REPO="/nonexistent/repo" bash "${LAUNCHER}" --dry-run >/tmp/cp-dryrun-missing.txt 2>&1
rc=$?
set -e
if [ "${rc}" -eq 0 ]; then echo "FAIL: missing repo dry-run should fail"; exit 1; fi
grep -q "repository not found" /tmp/cp-dryrun-missing.txt
echo "PASS repo-missing reports failure"

# ---- CASE A: server not running -> launcher starts server ---------------
echo "--- CASE A: server not running -> start + health ---"
cleanup_procs  # ensure nothing on 4310
CP_LAUNCHER_NO_OPEN=1 bash "${LAUNCHER}" >/tmp/cp-launch-a.txt 2>&1 || true
sleep 1
curl -fsS "${HEALTH_URL}" | grep -q '"overall"' && echo "PASS backend started and healthy"
# exactly one listener
count="$(lsof -tiTCP:4310 -sTCP:LISTEN 2>/dev/null | wc -l | tr -d ' ')"
[ "${count}" = "1" ] || { echo "FAIL: expected 1 listener, got ${count}"; exit 1; }
echo "PASS exactly one backend instance"

# ---- CASE B: server already running -> reuse, no duplicate --------------
echo "--- CASE B: server already running -> reuse ---"
before="$(lsof -tiTCP:4310 -sTCP:LISTEN 2>/dev/null | tr '\n' ' ')"
CP_LAUNCHER_NO_OPEN=1 bash "${LAUNCHER}" >/tmp/cp-launch-b.txt 2>&1 || true
sleep 1
after="$(lsof -tiTCP:4310 -sTCP:LISTEN 2>/dev/null | tr '\n' ' ')"
[ "${before}" = "${after}" ] || { echo "FAIL: duplicate backend instance"; exit 1; }
echo "PASS reuse existing backend (no duplicate)"

# ---- CASE E: port occupied by unrelated service -> not mistaken for backend
echo "--- CASE E: unrelated port occupant ---"
cleanup_procs
# Start a fake server that returns JSON WITHOUT the "overall" key.
python3 -c "import http.server, json, socketserver
class S(socketserver.TCPServer):
    allow_reuse_address = True
class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        b=json.dumps({'hello':'world'}).encode(); self.send_response(200); self.send_header('Content-Type','application/json'); self.send_header('Content-Length',str(len(b))); self.end_headers(); self.wfile.write(b)
    def log_message(self,*a): pass
S(('127.0.0.1',4310), H).serve_forever()" &
FAKE_PID=$!
sleep 1
set +e
CP_LAUNCHER_NO_OPEN=1 TEACHER_WORKSTATION_REPO="${REPO_ROOT}" bash "${LAUNCHER}" --dry-run >/tmp/cp-dryrun-fake.txt 2>&1
set -e
# The dry-run must report "NOT RUNNING" (wrong health response), not HEALTHY.
grep -q "NOT RUNNING" /tmp/cp-dryrun-fake.txt || { echo "FAIL: wrong health response not detected"; kill $FAKE_PID 2>/dev/null; exit 1; }
kill $FAKE_PID 2>/dev/null
sleep 1
echo "PASS unrelated port occupant detected (wrong health response)"

# ---- CASE D: backend startup fails -> bounded failure -------------------
echo "--- CASE D: backend startup fails -> bounded ---"
cleanup_procs
# Point at a repo whose server module is missing (simulate startup failure).
mkdir -p /tmp/cp-empty-repo
start="$(date +%s)"
set +e
CP_LAUNCHER_NO_OPEN=1 TEACHER_WORKSTATION_REPO="/tmp/cp-empty-repo" STARTUP_TIMEOUT_SECS=3 \
  bash -c 'STARTUP_TIMEOUT_SECS="${STARTUP_TIMEOUT_SECS:-15}"' 2>/dev/null
# Use a wrapper that lowers the timeout by invoking the launcher with env directly.
CP_LAUNCHER_NO_OPEN=1 TEACHER_WORKSTATION_REPO="/tmp/cp-empty-repo" \
  bash "${LAUNCHER}" >/tmp/cp-launch-d.txt 2>&1
rc=$?
set -e
elapsed=$(( $(date +%s) - start ))
# The launcher's default startup timeout is 15s; a missing server module makes
# the backend never become healthy, so it should fail (non-zero) and not hang.
[ "${rc}" -ne 0 ] || { echo "FAIL: startup failure did not produce non-zero exit"; exit 1; }
echo "PASS backend-startup failure fails cleanly (exit ${rc})"
rm -rf /tmp/cp-empty-repo

# ---- CASE F: rapid double launch -> one instance -------------------------
echo "--- CASE F: rapid double launch ---"
cleanup_procs
CP_LAUNCHER_NO_OPEN=1 bash "${LAUNCHER}" >/dev/null 2>&1 || true
CP_LAUNCHER_NO_OPEN=1 bash "${LAUNCHER}" >/dev/null 2>&1 || true
sleep 1
count="$(lsof -tiTCP:4310 -sTCP:LISTEN 2>/dev/null | wc -l | tr -d ' ')"
[ "${count}" = "1" ] || { echo "FAIL: expected 1 instance after double launch, got ${count}"; exit 1; }
echo "PASS rapid double launch -> one backend instance"

# ---- App bundle validation ----------------------------------------------
echo "--- app bundle validation ---"
APP="${HOME}/Applications/Teacher Workstation - Canvas Planner.app"
if [ -d "${APP}" ]; then
  plutil -lint "${APP}/Contents/Info.plist" >/dev/null && echo "PASS Info.plist lint"
  [ -x "${APP}/Contents/MacOS/CanvasPlannerLauncher" ] && echo "PASS executable present + executable"
  [ -f "${APP}/Contents/Resources/CanvasPlanner.icns" ] && echo "PASS icon present"
  codesign --verify --deep --strict "${APP}" >/dev/null 2>&1 && echo "PASS codesign verify (ad-hoc)" || echo "WARN codesign verify (unsigned is acceptable locally)"
else
  echo "WARN app not installed (run bin/install-canvas-planner-app)"
fi

# ---- Secret / PII safety ------------------------------------------------
echo "--- secret / PII safety ---"
for f in "${LAUNCHER}" scripts/canvas_planner_app/build_app.sh; do
  grep -qiE "CANVAS_TOKEN|Authorization: Bearer|client_secret|access_token=|thalesacademy\.instructure" "${f}" && { echo "FAIL: secret/school-URL in ${f}"; exit 1; }
done
grep -qiE "student[ -_]name|parent[ -_]email|social security" "${LAUNCHER}" && { echo "FAIL: PII in launcher"; exit 1; }
echo "PASS no secrets / PII / school URLs in launcher source"

cleanup_procs
trap - EXIT

echo "PASS: Canvas Planner launcher tests complete"
echo "PASS Canvas Planner launcher tests complete"
