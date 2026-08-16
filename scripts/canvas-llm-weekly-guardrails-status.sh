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

PKG="scripts/canvas_llm_weekly_guardrails"
CLI="$PKG/cli.py"
DOC="docs/programs/canvas-llm/canvas-weekly-workflow-guardrails.md"
TEST="tests/canvas-llm-weekly-guardrails-test.sh"

echo "Weekly Workflow Guardrails: Fresh Pacing, Newsletter, and Launch Gates"
echo "------------------------------------------------------------------------"

require_file "$PKG/__init__.py"
require_file "$PKG/pacing_session.py"
require_file "$PKG/newsletter_guard.py"
require_file "$PKG/launch_gate.py"
require_file "$CLI"
require_file "$DOC"
require_file "$TEST"

echo
echo "Module Compilation"
echo "----------------------------------------"
if python3 -m py_compile "$PKG"/*.py; then
  pass "guardrail modules compile"
else
  fail "guardrail modules failed to compile"
fi

echo
echo "CLI Self-Check"
echo "----------------------------------------"
if selfcheck_output="$(python3 "$CLI" --selfcheck 2>&1)"; then
  echo "$selfcheck_output"
  pass "guardrail CLI self-check passed"
else
  echo "$selfcheck_output"
  fail "guardrail CLI self-check failed"
fi

echo
echo "Import-Safe Pure Graph"
echo "----------------------------------------"
if python3 - <<'PY'
import sys
sys.path.insert(0, ".")
from scripts.canvas_llm_weekly_guardrails import (
    build_blockers, can_build, invalidate, is_fresh, mark_read_failure,
    new_session_snapshot, record_fresh_pull, weekdays_for_week,
    newsletter_blockers, prune_expired_dates,
    is_launched, launch_blockers, approval_is_not_launch,
)
forbidden = [
    "canvas_writer",
    "canvas_connector",
    "scripts.canvas_llm_phase22.phase22_workstation",
    "scripts.canvas_llm_phase26.pipeline",
    "requests",
    "gspread",
]
loaded = [m for m in forbidden if m in sys.modules]
assert not loaded, loaded
print("OK")
PY
then
  pass "pure guardrail modules import without execution/network modules"
else
  fail "guardrail modules pulled execution/network modules"
fi

echo
echo "Fresh Pacing Guard Behavior"
echo "----------------------------------------"
if python3 - <<'PY'
import sys
sys.path.insert(0, ".")
from scripts.canvas_llm_weekly_guardrails import (
    BLOCK_FRESH_PULL_REQUIRED, BLOCK_PREVIOUS_WEEK_MISSING, BLOCK_READ_FAILURE,
    build_blockers, can_build, invalidate, is_fresh, mark_read_failure,
    new_session_snapshot, record_fresh_pull, weekdays_for_week,
)

# Fresh session blocks.
s = new_session_snapshot()
assert not can_build(s) and BLOCK_FRESH_PULL_REQUIRED in build_blockers(s)

# Fresh pull satisfies.
s = record_fresh_pull(
    s, week_code="Q1W5", starts_on="2026-08-17", ends_on="2026-08-21",
    weekdays=weekdays_for_week("2026-08-17"),
    previous_week_starts_on="2026-08-10", previous_week_ends_on="2026-08-14",
    pulled_at="2026-08-16T00:00:00Z",
)
assert is_fresh(s) and can_build(s)

# Invalidate forces re-read.
invalidate(s)
assert not can_build(s) and BLOCK_FRESH_PULL_REQUIRED in build_blockers(s)

# Read failure blocks.
s2 = mark_read_failure(record_fresh_pull(
    new_session_snapshot(), week_code="Q1W5", starts_on="2026-08-17", ends_on="2026-08-21",
    weekdays=weekdays_for_week("2026-08-17"),
    previous_week_starts_on="2026-08-10", previous_week_ends_on="2026-08-14",
    pulled_at="2026-08-16T00:00:00Z",
), "network down")
assert not can_build(s2) and BLOCK_READ_FAILURE in build_blockers(s2)

# Previous week required.
s3 = record_fresh_pull(
    new_session_snapshot(), week_code="Q1W5", starts_on="2026-08-17", ends_on="2026-08-21",
    weekdays=weekdays_for_week("2026-08-17"),
    previous_week_starts_on="", previous_week_ends_on="",
    pulled_at="2026-08-16T00:00:00Z",
)
assert not can_build(s3) and BLOCK_PREVIOUS_WEEK_MISSING in build_blockers(s3)
print("OK")
PY
then
  pass "fresh pacing guard behavior verified"
else
  fail "fresh pacing guard behavior failed"
fi

echo
echo "Newsletter + Launch Guard Behavior"
echo "----------------------------------------"
if python3 - <<'PY'
import sys
sys.path.insert(0, ".")
from scripts.canvas_llm_weekly_guardrails import (
    BLOCK_LIVE_READ_REQUIRED, BLOCK_QUESTION_REQUIRED, BLOCK_LAUNCH_REQUIRED,
    NewsletterGuardState, LaunchState,
    newsletter_blockers, prune_expired_dates, can_finalize_newsletter,
    is_launched, launch_blockers, approval_is_not_launch,
)

# Live Homeroom read required.
assert BLOCK_LIVE_READ_REQUIRED in newsletter_blockers(NewsletterGuardState(live_read=False, question_asked=True))

# Dates cleanup: remove expired, preserve future, surface ambiguous.
kept, removed, ambiguous = prune_expired_dates(
    [{"label": "First Day of School", "date": "2026-08-17"},
     {"label": "Past Event", "date": "2026-08-01"},
     {"label": "Curriculum Night", "date": "2026-08-27"},
     {"label": "Unclear Event", "date": ""}],
    "2026-08-16",
)
assert removed == [{"label": "Past Event", "date": "2026-08-01"}]
assert {"label": "Curriculum Night", "date": "2026-08-27"} in kept
assert any(a.get("label") == "Unclear Event" for a in ambiguous)

# Question required before final review.
assert BLOCK_QUESTION_REQUIRED in newsletter_blockers(NewsletterGuardState(live_read=True, question_asked=False))
assert can_finalize_newsletter(NewsletterGuardState(live_read=True, question_asked=True))

# Launch gate.
assert BLOCK_LAUNCH_REQUIRED in launch_blockers(LaunchState(final_review_shown=True))
assert approval_is_not_launch()
assert not is_launched(LaunchState(final_review_shown=True))
assert is_launched(LaunchState(final_review_shown=True, launch_command="Launch"))
assert is_launched(LaunchState(final_review_shown=True, launch_command="Apply Q1W5"))
assert launch_blockers(LaunchState(launch_command="Publish it")) == []
print("OK")
PY
then
  pass "newsletter + launch guard behavior verified"
else
  fail "newsletter + launch guard behavior failed"
fi

echo
echo "No Canvas Write / Mutation / Token Path"
echo "----------------------------------------"
if grep -RInE 'requests\.(post|put|patch|delete)|canvas_writer|canvas_connector|http\.client|urllib\.request|attempt_live_write|gspread|service_account' \
  "$PKG"/*.py >/tmp/weekly_guardrails_write_scan.txt 2>/dev/null; then
  cat /tmp/weekly_guardrails_write_scan.txt
  fail "Canvas write/mutation/network/token path found in guardrail package"
else
  pass "no Canvas write/mutation/network/token path in guardrail package"
fi
rm -f /tmp/weekly_guardrails_write_scan.txt

echo
echo "Summary"
echo "----------------------------------------"
echo "PASS: ${PASS_COUNT}"
echo "WARN: ${WARN_COUNT}"
echo "FAIL: ${FAIL_COUNT}"

if [[ "$FAIL_COUNT" -ne 0 ]]; then
  exit 1
fi
