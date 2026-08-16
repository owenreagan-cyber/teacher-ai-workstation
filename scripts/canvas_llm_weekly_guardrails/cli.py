#!/usr/bin/env python3
"""Read-only CLI for the weekly workflow guardrails.

Encodes the FPK pacing source identity, runs a deterministic self-check, and
prints the guardrail posture. Zero Canvas writes. No network. No token access.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.canvas_llm_weekly_guardrails import (  # noqa: E402
    BLOCK_FRESH_PULL_REQUIRED,
    BLOCK_LAUNCH_REQUIRED,
    BLOCK_LIVE_READ_REQUIRED,
    BLOCK_PREVIOUS_WEEK_MISSING,
    BLOCK_QUESTION_REQUIRED,
    BLOCK_READ_FAILURE,
    FPK_SHEET_NAME,
    FPK_SPREADSHEET_ID,
    LaunchState,
    NewsletterGuardState,
    approval_is_not_launch,
    build_blockers,
    can_build,
    invalidate,
    is_fresh,
    is_launched,
    launch_blockers,
    mark_read_failure,
    new_session_snapshot,
    newsletter_blockers,
    prune_expired_dates,
    record_fresh_pull,
    weekdays_for_week,
)


def _q1w5_snapshot():
    return record_fresh_pull(
        new_session_snapshot(),
        week_code="Q1W5",
        starts_on="2026-08-17",
        ends_on="2026-08-21",
        weekdays=weekdays_for_week("2026-08-17"),
        previous_week_starts_on="2026-08-10",
        previous_week_ends_on="2026-08-14",
        source_range="'4B - Reagan'!A1:Z40",
        source_revision="rev-0001",
        pulled_at="2026-08-16T00:00:00Z",
    )


def _selfcheck() -> int:
    failures: list[str] = []

    # 1. Fresh session blocks build until a live pacing read.
    if not can_build(new_session_snapshot()) and BLOCK_FRESH_PULL_REQUIRED in build_blockers(new_session_snapshot()):
        print("PASS: fresh session blocks build until a live pacing read")
    else:
        failures.append("fresh-required")
        print("FAIL: fresh pacing guard did not block")

    # 2. Fresh pull satisfies the guard.
    snap = _q1w5_snapshot()
    if is_fresh(snap) and can_build(snap):
        print("PASS: fresh live read satisfies the guard")
    else:
        failures.append("fresh-satisfies")
        print("FAIL: fresh read did not satisfy guard")

    # 3. Invalidate forces re-read.
    invalidate(snap)
    if not can_build(snap) and BLOCK_FRESH_PULL_REQUIRED in build_blockers(snap):
        print("PASS: refresh invalidates snapshot and forces re-read")
    else:
        failures.append("invalidate")
        print("FAIL: invalidate did not force re-read")

    # 4. Read failure blocks.
    fail_snap = mark_read_failure(_q1w5_snapshot(), "network down")
    if not can_build(fail_snap) and BLOCK_READ_FAILURE in build_blockers(fail_snap):
        print("PASS: pacing read failure blocks build")
    else:
        failures.append("read-failure")
        print("FAIL: read failure did not block")

    # 5. Previous week required for reflection.
    prev_missing = record_fresh_pull(
        new_session_snapshot(),
        week_code="Q1W5",
        starts_on="2026-08-17",
        ends_on="2026-08-21",
        weekdays=weekdays_for_week("2026-08-17"),
        previous_week_starts_on="",
        previous_week_ends_on="",
        pulled_at="2026-08-16T00:00:00Z",
    )
    if not can_build(prev_missing) and BLOCK_PREVIOUS_WEEK_MISSING in build_blockers(prev_missing):
        print("PASS: previous-week pacing required for reflection")
    else:
        failures.append("prev-week")
        print("FAIL: previous-week guard missing")

    # 6. Live Homeroom read required.
    if BLOCK_LIVE_READ_REQUIRED in newsletter_blockers(NewsletterGuardState(live_read=False, question_asked=True)):
        print("PASS: live Homeroom read required before newsletter edit")
    else:
        failures.append("live-read")
        print("FAIL: live Homeroom read guard missing")

    # 7-8. Newsletter dates cleanup.
    kept, removed, ambiguous = prune_expired_dates(
        [
            {"label": "First Day of School", "date": "2026-08-17"},
            {"label": "Past Event", "date": "2026-08-01"},
            {"label": "Curriculum Night", "date": "2026-08-27"},
            {"label": "Unclear Event", "date": ""},
        ],
        "2026-08-16",
    )
    if (
        removed == [{"label": "Past Event", "date": "2026-08-01"}]
        and {"label": "Curriculum Night", "date": "2026-08-27"} in kept
        and any(a.get("label") == "Unclear Event" for a in ambiguous)
    ):
        print("PASS: newsletter dates cleanup removes expired, preserves future, surfaces ambiguous")
    else:
        failures.append("dates")
        print("FAIL: newsletter dates cleanup wrong")

    # 8. Newsletter question required before final review.
    if BLOCK_QUESTION_REQUIRED in newsletter_blockers(NewsletterGuardState(live_read=True, question_asked=False)):
        print("PASS: newsletter question required before final review")
    else:
        failures.append("question")
        print("FAIL: newsletter question guard missing")

    # 9. Launch gate.
    if not is_launched(LaunchState(final_review_shown=True)) and BLOCK_LAUNCH_REQUIRED in launch_blockers(LaunchState(final_review_shown=True)):
        print("PASS: explicit launch command required")
    else:
        failures.append("launch")
        print("FAIL: launch gate missing")
    if approval_is_not_launch():
        print("PASS: approval/final-review does not imply launch")
    else:
        failures.append("launch-approval")
        print("FAIL: approval incorrectly implied launch")
    if is_launched(LaunchState(final_review_shown=True, launch_command="Apply Q1W5")) and launch_blockers(LaunchState(launch_command="Launch")) == []:
        print("PASS: explicit launch command satisfies the gate")
    else:
        failures.append("launch-ok")
        print("FAIL: explicit launch command not accepted")

    if failures:
        print(f"Self-check failed: {failures}")
        return 1
    print("PASS: weekly workflow guardrails self-check complete")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="canvas_llm_weekly_guardrails", description="Weekly workflow guardrails")
    parser.add_argument("--selfcheck", action="store_true", help="run the read-only self-check")
    parser.add_argument("--policy", action="store_true", help="print the canonical FPK pacing source identity as JSON")
    args = parser.parse_args(argv)

    if args.selfcheck:
        return _selfcheck()
    if args.policy:
        print(json.dumps({"spreadsheet_id": FPK_SPREADSHEET_ID, "sheet": FPK_SHEET_NAME}, indent=2, sort_keys=True))
        return 0
    print(f"FPK pacing source: {FPK_SPREADSHEET_ID} tab {FPK_SHEET_NAME}")
    print("Fresh pull: REQUIRED each weekly session")
    print("Refresh command: invalidates snapshot and forces re-read")
    print("Launch: explicit command required (approval is not launch)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
