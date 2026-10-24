#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

export PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/teacher-ai-workstation-pycache"

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

pass() { PASS_COUNT=$((PASS_COUNT + 1)); echo "PASS: $1"; }
warn() { WARN_COUNT=$((WARN_COUNT + 1)); echo "WARN: $1"; }
fail() { FAIL_COUNT=$((FAIL_COUNT + 1)); echo "FAIL: $1"; }

require_file() {
  if [[ -f "$1" ]]; then pass "file exists: $1"; else fail "missing file: $1"; fi
}

PKG="scripts/weekly_planner_agent"
DOC="docs/programs/canvas-llm/weekly-planner-agent-foundation.md"
CHANGE_DOC="docs/programs/canvas-llm/weekly-planner-change-detection.md"
PUBLISH_DOC="docs/programs/canvas-llm/weekly-planner-guarded-publish.md"
TESTS="tests/weekly_planner_agent"

echo "Weekly Planner Agent — Foundation + Change Detection + Guarded Publish"
echo "------------------------------------------------------------------------"

require_file "$PKG/__init__.py"
require_file "$PKG/models.py"
require_file "$PKG/authority.py"
require_file "$PKG/teacher_instructions.py"
require_file "$PKG/change_engine.py"
require_file "$PKG/assessment_watch.py"
require_file "$PKG/communication_rules.py"
require_file "$PKG/notification_model.py"
require_file "$PKG/review_state.py"
require_file "$PKG/service.py"
require_file "$PKG/snapshot.py"
require_file "$PKG/change_detection.py"
require_file "$PKG/event_store.py"
require_file "$PKG/impact.py"
require_file "$PKG/canvas_observation.py"
require_file "$PKG/freshness.py"
require_file "$PKG/reconciliation.py"
require_file "$PKG/delivery.py"
require_file "$PKG/publish.py"
require_file "$PKG/schedule_config.py"
require_file "$DOC"
require_file "$CHANGE_DOC"
require_file "$PUBLISH_DOC"
require_file "$TESTS/test_agent.py"
require_file "$TESTS/test_snapshot.py"
require_file "$TESTS/test_change_detection.py"
require_file "$TESTS/test_event_store.py"
require_file "$TESTS/test_canvas_observation.py"
require_file "$TESTS/test_reconciliation.py"
require_file "$TESTS/test_delivery.py"
require_file "$TESTS/test_publish.py"

echo
echo "Module Compilation"
echo "----------------------------------------"
if python3 -m py_compile "$PKG"/*.py; then
  pass "agent modules compile"
else
  fail "agent modules failed to compile"
fi

echo
echo "Self-Test (no network/write path)"
echo "----------------------------------------"
if python3 -m scripts.weekly_planner_agent.service; then
  pass "agent service self-test passed"
else
  fail "agent service self-test failed"
fi
for mod in snapshot change_detection event_store impact freshness canvas_observation reconciliation delivery publish schedule_config; do
  if python3 -m "scripts.weekly_planner_agent.$mod" >/dev/null 2>&1; then
    pass "agent $mod self-test passed"
  else
    fail "agent $mod self-test failed"
  fi
done

echo
echo "Unit Tests"
echo "----------------------------------------"
if python3 -m unittest discover -s tests/weekly_planner_agent >/tmp/wpa_test_out.txt 2>&1; then
  pass "agent unit tests passed"
else
  cat /tmp/wpa_test_out.txt
  fail "agent unit tests failed"
fi

echo
echo "No Canvas Write / Network Path"
echo "----------------------------------------"
if grep -RInE 'requests\.(post|put|patch|delete)|canvas_writer|canvas_connector|http\.client|urllib\.request|gspread|service_account|Phase22LiveCanvasClient' \
  "$PKG"/*.py >/tmp/wpa_write_scan.txt 2>/dev/null; then
  cat /tmp/wpa_write_scan.txt
  fail "Canvas write/mutation/network path found in agent package"
else
  pass "no Canvas write/mutation/network path in agent package"
fi
rm -f /tmp/wpa_write_scan.txt /tmp/wpa_test_out.txt

echo
echo "Notification Delivery Gate (email disabled by default)"
echo "----------------------------------------"
if python3 - <<'PY' >/dev/null 2>&1
import os, tempfile
os.environ["TAW_STATE_ROOT"] = tempfile.mkdtemp()
from scripts.weekly_planner_agent import schedule_config
cfg = schedule_config.delivery_config()
assert cfg["mode"] == "preview"
assert cfg["email_enabled"] is False
print("OK")
PY
then
  pass "email delivery disabled by default (mode=preview)"
else
  fail "email delivery is not disabled by default"
fi

echo
echo "Scheduler Not Installed"
echo "----------------------------------------"
if launchctl print "gui/$(id -u)/com.teacher-ai-workstation.canvas-friday" >/dev/null 2>&1; then
  warn "Friday LaunchAgent appears installed/loaded (not installed by this phase)"
else
  pass "Friday LaunchAgent is not installed or loaded"
fi

echo
echo "Chief of Staff Wiring"
echo "----------------------------------------"
if grep -Fq -- '--weekly-planner-agent-status' bin/chief-of-staff; then
  pass "chief-of-staff exposes --weekly-planner-agent-status"
else
  fail "chief-of-staff missing --weekly-planner-agent-status"
fi

echo
echo "Active Announcement Feed Fix (context_codes[])"
echo "----------------------------------------"
if grep -q 'context_codes' scripts/canvas_llm_intake/canvas_readonly.py; then
  pass "list_active_announcements includes context_codes[] (HTTP 400 fix)"
else
  fail "list_active_announcements still missing context_codes[]"
fi

echo
echo "Summary"
echo "----------------------------------------"
echo "PASS: ${PASS_COUNT}"
echo "WARN: ${WARN_COUNT}"
echo "FAIL: ${FAIL_COUNT}"

if [[ "$FAIL_COUNT" -ne 0 ]]; then
  exit 1
fi
