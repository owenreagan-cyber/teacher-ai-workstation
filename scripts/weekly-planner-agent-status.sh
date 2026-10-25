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
LIVE_DOC="docs/programs/canvas-llm/weekly-planner-live-reconciliation.md"
BASELINE_DOC="docs/programs/canvas-llm/weekly-planner-baseline-consistency.md"
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
require_file "$PKG/live_sources.py"
require_file "$PKG/cross_source.py"
require_file "$PKG/owner_instructions.py"
require_file "$PKG/delivery.py"
require_file "$PKG/publish.py"
require_file "$PKG/schedule_config.py"
require_file "$DOC"
require_file "$CHANGE_DOC"
require_file "$PUBLISH_DOC"
require_file "$LIVE_DOC"
require_file "$BASELINE_DOC"
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
for mod in snapshot change_detection event_store impact freshness canvas_observation reconciliation live_sources cross_source owner_instructions delivery publish schedule_config; do
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
echo "No Canvas Write Path (read-only GET is authorized this phase)"
echo "----------------------------------------"
if grep -RInE 'requests\.(post|put|patch|delete)|http\.client|canvas_writer|canvas_connector|Phase22LiveCanvasClient|method="(POST|PUT|PATCH|DELETE)"' \
  "$PKG"/*.py >/tmp/wpa_write_scan.txt 2>/dev/null; then
  cat /tmp/wpa_write_scan.txt
  fail "Canvas write/mutation path found in agent package"
else
  pass "no Canvas write/mutation path in agent package"
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
echo "Live Read-Only Reconciliation (real GET-only probe)"
echo "----------------------------------------"
PROBE_JSON="$(python3 - <<'PY' 2>/dev/null
import json
try:
    from scripts.weekly_planner_agent import service
    q, w = service.resolve_target_week()
    probe = service.live_probe(q, w)
    probe["probe_error"] = None
except Exception as exc:  # noqa: BLE001
    probe = {"probe_error": f"{type(exc).__name__}: {exc}", "pacing_read_ok": False, "canvas_read_ok": False}
print(json.dumps(probe))
PY
)"
if [[ -z "$PROBE_JSON" ]]; then
  warn "live probe could not run (python error)"
else
  PROBE_ERR="$(python3 -c "import json,sys; print(json.loads(sys.stdin.read()).get('probe_error') or '')" <<<"$PROBE_JSON")"
  PACING_OK="$(python3 -c "import json,sys; print('yes' if json.loads(sys.stdin.read()).get('pacing_read_ok') else 'no')" <<<"$PROBE_JSON")"
  CANVAS_OK="$(python3 -c "import json,sys; print('yes' if json.loads(sys.stdin.read()).get('canvas_read_ok') else 'no')" <<<"$PROBE_JSON")"
  if [[ -n "$PROBE_ERR" ]]; then
    warn "live read-only probe blocked: $PROBE_ERR"
  else
    if [[ "$PACING_OK" == "yes" ]]; then
      pass "live Google pacing GET-only read succeeded"
    else
      warn "live Google pacing GET-only read did not succeed"
    fi
    if [[ "$CANVAS_OK" == "yes" ]]; then
      pass "live Canvas GET-only read succeeded (token never printed)"
    else
      warn "live Canvas GET-only read did not succeed (credentials unavailable or network)"
    fi
  fi
fi

echo
echo "Agent Reconciliation State (persisted, read-only)"
echo "----------------------------------------"
STATUS_JSON="$(python3 - <<'PY' 2>/dev/null
import json
from scripts.weekly_planner_agent import service
print(json.dumps(service.agent_status(), default=str))
PY
)"
if [[ -z "$STATUS_JSON" ]]; then
  warn "agent status could not be computed"
else
  read_field() { python3 -c "import json,sys; d=json.loads(sys.stdin.read()); print(d.get('$1'))" <<<"$STATUS_JSON"; }
  echo "  current week: $(read_field current_week)"
  echo "  pacing freshness: $(read_field pacing_freshness)"
  echo "  canvas freshness: $(read_field canvas_freshness)"
  echo "  last live GET-only sync: $(read_field last_live_sync_at)"
  echo "  baseline consistency: $(read_field baseline_consistency)"
  echo "  unresolved cross-source conflicts: $(read_field cross_source_conflicts)"
  echo "  assessment conflicts: $(read_field assessment_conflicts)"
  echo "  override-backed conflicts: $(read_field override_backed_conflicts)"
  echo "  unresolved changes: $(read_field unresolved_changes)"
  echo "  assessment date watch alerts: $(read_field assessment_watch)"
  echo "  Friday review state: $(read_field friday_review_state)"
  echo "  Friday review blocked: $(read_field friday_review_blocked)"
  echo "  approval readiness: $(read_field approval_readiness)"
  echo "  notification mode: $(read_field notification_mode)"
  echo "  email enabled: $(read_field email_enabled)"
  echo "  scheduler active: $(read_field scheduler_active)"
  echo "  last publication: $(read_field last_publication)"

  CONSISTENCY="$(read_field baseline_consistency)"
  case "$CONSISTENCY" in
    PASS) pass "baseline consistency: sources agree or all material conflicts resolved" ;;
    WARN) warn "baseline consistency: non-blocking conflict or owner override with lower-authority disagreement" ;;
    FAIL) fail "baseline consistency: material unresolved conflict makes approval unsafe" ;;
    *)    warn "baseline consistency: unknown state ($CONSISTENCY)" ;;
  esac
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
