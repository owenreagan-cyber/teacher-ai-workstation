#!/usr/bin/env bash
set -euo pipefail

echo "Running weekly workflow guardrails regression tests..."

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

export PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/teacher-ai-workstation-pycache"

TOTAL_PASS=0
TOTAL_FAIL=0

note_pass() { TOTAL_PASS=$((TOTAL_PASS + 1)); }
note_fail() { TOTAL_FAIL=$((TOTAL_FAIL + 1)); echo "FAIL: $1"; }

PKG="scripts/canvas_llm_weekly_guardrails"

echo
echo "Compilation"
echo "----------------------------------------"
if python3 -m py_compile "$PKG"/*.py; then
  note_pass
else
  note_fail "guardrail modules failed to compile"
fi

echo
echo "Targeted Regression Suite (11 checks)"
echo "----------------------------------------"
if python3 - <<'PY'
import sys
sys.path.insert(0, ".")

from scripts.canvas_llm_weekly_guardrails import (
    BLOCK_FRESH_PULL_REQUIRED, BLOCK_LAUNCH_REQUIRED, BLOCK_LIVE_READ_REQUIRED,
    BLOCK_PREVIOUS_WEEK_MISSING, BLOCK_QUESTION_REQUIRED, BLOCK_READ_FAILURE,
    LaunchState, NewsletterGuardState,
    approval_is_not_launch, build_blockers, can_build, invalidate, is_fresh,
    is_launched, launch_blockers, mark_read_failure, new_session_snapshot,
    newsletter_blockers, prune_expired_dates, record_fresh_pull, weekdays_for_week,
)

passed = []
failed = []

def check(name, cond, detail=""):
    if cond:
        passed.append(name)
    else:
        failed.append((name, detail))

def q1w5_snapshot():
    return record_fresh_pull(
        new_session_snapshot(), week_code="Q1W5", starts_on="2026-08-17", ends_on="2026-08-21",
        weekdays=weekdays_for_week("2026-08-17"),
        previous_week_starts_on="2026-08-10", previous_week_ends_on="2026-08-14",
        source_range="'4B - Reagan'!A1:Z40", source_revision="rev-0001",
        pulled_at="2026-08-16T00:00:00Z",
    )

# 1. Fresh pacing required at weekly-session start.
s = new_session_snapshot()
check("01 fresh pacing required at session start",
      (not can_build(s)) and BLOCK_FRESH_PULL_REQUIRED in build_blockers(s), build_blockers(s))

# 2. Refresh command forces new pacing read.
s = q1w5_snapshot()
check("02 fresh pull satisfies guard", is_fresh(s) and can_build(s))
invalidate(s)
check("02 refresh forces new pacing read",
      (not can_build(s)) and BLOCK_FRESH_PULL_REQUIRED in build_blockers(s), build_blockers(s))

# 3. Pacing read failure blocks build.
s = mark_read_failure(q1w5_snapshot(), "network down")
check("03 pacing read failure blocks build",
      (not can_build(s)) and BLOCK_READ_FAILURE in build_blockers(s), build_blockers(s))

# 4. Previous-week pacing used for reflection.
s = record_fresh_pull(
    new_session_snapshot(), week_code="Q1W5", starts_on="2026-08-17", ends_on="2026-08-21",
    weekdays=weekdays_for_week("2026-08-17"),
    previous_week_starts_on="", previous_week_ends_on="",
    pulled_at="2026-08-16T00:00:00Z",
)
check("04 previous-week pacing required for reflection",
      (not can_build(s)) and BLOCK_PREVIOUS_WEEK_MISSING in build_blockers(s), build_blockers(s))

# 5. Live Homeroom read required.
check("05 live Homeroom read required",
      BLOCK_LIVE_READ_REQUIRED in newsletter_blockers(NewsletterGuardState(live_read=False, question_asked=True)))

# 6. Expired newsletter dates removed.
kept, removed, ambiguous = prune_expired_dates(
    [{"label": "First Day of School", "date": "2026-08-17"},
     {"label": "Past Event", "date": "2026-08-01"},
     {"label": "Curriculum Night", "date": "2026-08-27"}],
    "2026-08-16",
)
check("06 expired newsletter dates removed",
      removed == [{"label": "Past Event", "date": "2026-08-01"}], removed)

# 7. Future newsletter dates preserved.
check("07 future newsletter dates preserved",
      {"label": "Curriculum Night", "date": "2026-08-27"} in kept
      and {"label": "First Day of School", "date": "2026-08-17"} in kept, kept)

# 8. Newsletter addition question required before final review.
check("08 newsletter question required before final review",
      BLOCK_QUESTION_REQUIRED in newsletter_blockers(NewsletterGuardState(live_read=True, question_asked=False)))

# 9. Final launch approval required.
check("09 explicit launch required", BLOCK_LAUNCH_REQUIRED in launch_blockers(LaunchState(final_review_shown=True)))
check("09 approval is not launch", approval_is_not_launch())
check("09 explicit launch accepted",
      is_launched(LaunchState(final_review_shown=True, launch_command="Launch"))
      and is_launched(LaunchState(final_review_shown=True, launch_command="Apply Q1W5"))
      and launch_blockers(LaunchState(launch_command="Publish it")) == [])

# 10. No duplicate weekly pages (existing detector flags duplicates).
from scripts.canvas_llm_phase22.canvas_duplicate_detector import detect_duplicates
dup_reports = detect_duplicates()
page_dups = [r for r in dup_reports if r.object_type == "page"]
check("10 no duplicate weekly pages (detector flags duplicates)", bool(page_dups), page_dups)

# 11. No Canvas writes when preflight fails (existing Phase 18E + write gate).
from scripts.canvas_llm_phase18d.contracts import (
    ApprovalRecord, CanvasSnapshot, DeploymentIntent, DryRunPacket,
)
from scripts.canvas_llm_phase18e.policy import OwnerCanvasPolicy
from scripts.canvas_llm_phase18e.preconditions import evaluate_preconditions, record_approval_bindings
from scripts.canvas_llm_phase18e.adapter import build_writer_requests
from scripts.canvas_llm_phase27.canonicalize import canonical_hash
from scripts.canvas_llm_phase22.write_gate import evaluate_write, attempt_write

POLICY = OwnerCanvasPolicy(publish_state="resolved", publish_decision="published")
CFG = {"math": {"course_id": "M", "module_id": "MM", "assignment_group_id": "MA"}}

blocked = DeploymentIntent(
    id="i-blocked", operation="CREATE", object_type="assignment", course="math",
    canonical_source="canonical_rule", target_locator="math-homework-q1w5",
    desired_state={"title": "Math Homework", "course_id": "M", "assignment_group_id": "MA",
                   "assigned_date": "2026-08-24", "due_at": "2026-08-24", "timezone": "America/New_York"},
    provenance=[{"sourceType": "canonical-weekly-plan", "sourceRef": "wp-Q1W5", "details": "x"}],
    preconditions={"week_code": "Q1W5", "expected_object_id": "", "expected_current_hash": ""},
    blockers=["ownership_uncertain"],
)
p = DryRunPacket(
    week_code="Q1W5", canonical_plan_identity="wp-Q1W5", canonical_revision="wp-Q1W5",
    preview_identity="preview-1", preview_hash="abc", snapshot_identity="snap-1",
    snapshot_hash="snap", target_environment="sandbox", intents=[blocked],
)
p.packet_hash = canonical_hash({
    "week_code": p.week_code, "canonical_revision": p.canonical_revision,
    "preview_hash": p.preview_hash, "snapshot_hash": p.snapshot_hash,
    "target_environment": p.target_environment, "intents": [i.to_dict() for i in p.intents],
})
bindings = record_approval_bindings(packet=p, policy=POLICY, canvas_config=CFG)
approval = ApprovalRecord(
    packet_hash=p.packet_hash, reviewer="Owner", approved_at="2026-08-16T00:00:00Z",
    scope="full-week", approved_intent_ids=["i-blocked"], preconditions=bindings,
)
snap = CanvasSnapshot(week_code="Q1W5", snapshot_id="snap-1", objects=[])
report = evaluate_preconditions(p, blocked, approval, POLICY, canvas_config=CFG, snapshot=snap)
reqs = build_writer_requests(p, approval, POLICY, canvas_config=CFG, snapshot=snap)
check("11 preflight fail -> zero writer requests", reqs == [], [r.request_id for r in reqs])

gate = evaluate_write("create", "page", "p-1", approved=True, approved_by="Teacher", approved_at="2026-08-16T00:00:00Z")
check("11 write gate stays closed", attempt_write(gate).gate_state == "BLOCKED", attempt_write(gate).gate_state)

total = len(passed) + len(failed)
for name in passed:
    print(f"PASS scenario: {name}")
for name, detail in failed:
    print(f"FAIL scenario: {name} -> {detail}")
print(f"SCENARIO_TOTAL: {total}")
print(f"SCENARIO_PASS: {len(passed)}")
print(f"SCENARIO_FAIL: {len(failed)}")
assert len(failed) == 0, failed
assert total >= 11, f"only {total} scenarios (need >=11)"
PY
then
  note_pass
else
  note_fail "targeted regression suite failed"
fi

echo
echo "Summary"
echo "----------------------------------------"
echo "TOTAL_PASS: ${TOTAL_PASS}"
echo "TOTAL_FAIL: ${TOTAL_FAIL}"

if [[ "$TOTAL_FAIL" -ne 0 ]]; then
  exit 1
fi
echo "PASS: weekly workflow guardrails regression tests complete"
