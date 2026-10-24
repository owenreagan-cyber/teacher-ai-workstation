"""End-to-end acceptance scenario: persistent change detection + reconciliation.

Deterministic, fake/local only. No Canvas writes, no real notifications.
"""
from __future__ import annotations

import os
import tempfile
import unittest
from unittest import mock

from scripts.weekly_planner_agent import reconciliation
from scripts.weekly_planner_agent import service
from scripts.weekly_planner_agent.event_store import EventStore
from scripts.weekly_planner_agent.models import (
    Assessment,
    Authority,
    DayPlan,
    PlanStatus,
    WeeklyPlan,
)


def _baseline_plan() -> WeeklyPlan:
    plan = WeeklyPlan(week_id="Q2W3", quarter=2, week=3,
                      date_range={"start": "2026-10-26", "end": "2026-10-30"})
    plan.source_provenance = {"name": "FPK Pacing Guides", "tab": "4A - Reagan",
                              "spreadsheet_id": "fake-spreadsheet"}
    plan.upsert_day(DayPlan(
        subject="math", day="Thursday", date="2026-11-05", lesson="WA8",
        classwork=["WA8"], homework=[],
        assessment=Assessment(name="Written Assessment 8", subject="math",
                              day="Thursday", date="2026-11-05"),
        authority=Authority.VERIFIED_PACING, status=PlanStatus.CONFIRMED_SOURCE,
    ))
    for day in ("Monday", "Tuesday", "Wednesday", "Friday"):
        plan.upsert_day(DayPlan(subject="math", day=day, lesson=f"L {day}",
                                authority=Authority.VERIFIED_PACING))
    plan.upsert_day(DayPlan(subject="science", day="Wednesday", lesson="Chapter 7",
                            authority=Authority.VERIFIED_PACING))
    plan.approval_status = {
        "math": {"page": "approved", "assignments": "approved",
                 "announcement": "approved", "assessment_reminder": "approved"},
        "science": {"page": "approved"},
    }
    return plan


class AcceptanceScenarioTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp()
        self.env = mock.patch.dict(os.environ, {"TAW_STATE_ROOT": self.tmp})
        self.env.start()

    def tearDown(self) -> None:
        self.env.stop()

    def test_full_scenario(self) -> None:
        # 1. Persist baseline: Math WA8 Thursday.
        baseline = _baseline_plan()
        service.save_plan(2, 3, baseline)
        pacing_baseline = {"identity": baseline.source_provenance,
                           "cells": reconciliation.pacing_cells_from_plan(baseline)}

        # 2. First observation establishes a baseline (no false alerts).
        report = service.sync(2, 3, pacing=pacing_baseline)
        self.assertTrue(report["baseline"])
        self.assertEqual(report["changes"], [])

        # 3. Change the pacing fixture to Friday and re-sync.
        changed = _baseline_plan()
        math_thu = changed.day("math", "Thursday")
        math_thu.assessment.date = "2026-11-06"
        math_thu.assessment.day = "Friday"
        pacing_changed = {"identity": baseline.source_provenance,
                          "cells": reconciliation.pacing_cells_from_plan(changed)}

        report = service.sync(2, 3, pacing=pacing_changed)
        self.assertFalse(report["baseline"])

        # 4. Exactly one Assessment Date Watch event.
        watch_events = [e for e in report["events"]
                        if e["classification"] == "assessment_date_changed"]
        self.assertEqual(len(watch_events), 1)
        event = watch_events[0]

        # 5. Affected artifacts identified.
        affected = event["affected_artifacts"]
        self.assertTrue(any("weekly page" in a for a in affected))
        self.assertTrue(any("assignment" in a for a in affected))
        self.assertTrue(any("announcement" in a for a in affected))
        self.assertTrue(any("reminder" in a for a in affected))

        # 6. Notification draft asks Owen whether to update.
        self.assertEqual(len(report["notifications"]), 1)
        draft = report["notifications"][0]
        self.assertIn("Would you like me to update the live Canvas items", draft["body"])
        self.assertIn("Written Assessment 8", draft["body"])

        # 7. Unaffected subject approvals preserved; math invalidated.
        self.assertIn("math:page", report["invalidated_approvals"])
        self.assertEqual(baseline.approval_status["science"]["page"], "approved")
        loaded = service.load_plan(2, 3)
        self.assertEqual(loaded.approval_status["science"]["page"], "approved")

        # 8. Simulated plain-language instruction revises the candidate plan.
        result = service.instruct(2, 3, "Yes, but leave the reminder scheduled for now.")
        self.assertTrue(result["matched"])
        revised = service.load_plan(2, 3)
        math_day = next(d for d in revised.subjects["math"] if d.assessment is not None)
        self.assertEqual(math_day.assessment.date, "2026-11-06")

        # 9. Persist across restart (fresh store/load from disk).
        store = EventStore(2, 3)
        self.assertEqual(len(store.all()), 1)
        self.assertIn("assessment_date_changed", store.all()[0]["classification"])
        fresh_plan = service.load_plan(2, 3)
        fresh_math = next(d for d in fresh_plan.subjects["math"] if d.assessment is not None)
        self.assertEqual(fresh_math.assessment.date, "2026-11-06")

        # 10. No Canvas writes and no real notifications.
        self.assertEqual(report["canvas_writes"], 0)
        self.assertEqual(report["notifications_delivered"], 0)


if __name__ == "__main__":
    unittest.main()
