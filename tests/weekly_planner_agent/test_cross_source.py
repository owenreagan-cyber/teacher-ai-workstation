"""Baseline cross-source consistency engine — deterministic acceptance tests.

Covers the required scenarios: first-run conflict/match, owner-override authority,
canvas-only / pacing-only conflicts, posted-announcement correction, reminder
reschedule, repeated-polling dedup, and source-outage safety.
"""
from __future__ import annotations

import os
import tempfile
import unittest
from unittest import mock

from scripts.weekly_planner_agent import assessment_watch as aw
from scripts.weekly_planner_agent import cross_source as cs
from scripts.weekly_planner_agent import reconciliation
from scripts.weekly_planner_agent import snapshot as snap
from scripts.weekly_planner_agent.event_store import EventStore
from scripts.weekly_planner_agent.models import Assessment, Authority, DayPlan, WeeklyPlan


def _plan(assessment_date="2026-11-05", *, override=None) -> WeeklyPlan:
    plan = WeeklyPlan(week_id="Q2W3", quarter=2, week=3)
    day = DayPlan(
        subject="math", day="Thursday", date=assessment_date, lesson="WA8",
        classwork=["WA8"], homework=[],
        assessment=Assessment(name="Written Assessment 8", subject="math",
                              day="Thursday", date=assessment_date),
        authority=Authority.OWNER_INSTRUCTION if override else Authority.VERIFIED_PACING,
        teacher_override=override,
    )
    plan.upsert_day(day)
    return plan


def _snapshot(pacing_date="2026-11-05", *, canvas_due=None, canvas_status="OK",
              canvas_announcements=None) -> dict[str, Any]:
    sn = snap.blank_snapshot(2, 3, "Q2W3")
    sn["pacing"]["status"] = snap.SNAPSHOT_OK
    sn["pacing"]["cells"] = {
        "math|Thursday": {
            "lesson": "Written Assessment 8", "chapter": None,
            "classwork": ["Written Assessment 8"], "homework": [],
            "assessment": {"name": "Written Assessment 8", "date": pacing_date, "day": "Thursday"},
        },
    }
    sn["canvas"]["status"] = canvas_status
    if canvas_status == "OK":
        sn["canvas"]["observed_at"] = "2026-10-24T12:00:00Z"
        sn["canvas"]["courses"] = {
            "math": {
                "front_page": {"title": "Q2W3 Math", "page_id": "q2w3"},
                "pages": [{"title": "Q2W3 Math", "page_id": "q2w3", "front_page": True}],
                "assignments": [{"name": "SM5: Written Assessment 8", "due_at": canvas_due}],
                "announcements": canvas_announcements or [
                    {"title": "Written Assessment 8 - Thursday, November 5", "message": "",
                     "delayed_post_at": None, "posted_at": "2026-10-30T20:00:00Z"},
                    {"title": "Math Assessment Reminder", "message": "",
                     "delayed_post_at": "2026-11-04T12:00:00Z", "posted_at": None},
                ],
            }
        }
    return sn


def _override(date):
    return {
        "kind": "owner_instruction", "instruction_id": "test",
        "reason": "test override", "day": "Thursday",
        "assessment_date": date, "lesson": "WA8", "assessments": ["Written Assessment 8"],
    }


class CrossSourceScanTest(unittest.TestCase):
    def test_a_first_run_conflict(self):
        # pacing Thursday, canvas Friday (due 2026-11-06 12:00Z -> ET Nov 6).
        plan = _plan("2026-11-05")
        sn = _snapshot("2026-11-05", canvas_due="2026-11-06T12:00:00Z")
        events = cs.scan(sn, plan=plan)
        date_conflicts = [e for e in events if e.object_type == cs.ASSESSMENT_DATE]
        self.assertEqual(len(date_conflicts), 1)
        e = date_conflicts[0]
        self.assertEqual(e.classification, "cross_source_conflict")
        self.assertEqual(e.old_value, "2026-11-05")
        self.assertEqual(e.new_value, "2026-11-06")
        self.assertTrue(any("weekly page" in a for a in e.affected_artifacts))
        self.assertTrue(any("assignment" in a for a in e.affected_artifacts))
        self.assertTrue(e.requires_teacher_approval)

    def test_b_first_run_match(self):
        plan = _plan("2026-11-05")
        sn = _snapshot("2026-11-05", canvas_due="2026-11-05T12:00:00Z")
        events = cs.scan(sn, plan=plan)
        self.assertEqual([e for e in events if e.object_type == cs.ASSESSMENT_DATE], [])

    def test_c_owner_override_wins(self):
        plan = _plan("2026-11-05", override=_override("2026-11-05"))
        sn = _snapshot("2026-11-06", canvas_due="2026-11-06T12:00:00Z")  # both Fri
        events = cs.scan(sn, plan=plan)
        types = {e.object_type for e in events}
        self.assertIn(cs.PACING_VS_OVERRIDE, types)
        self.assertIn(cs.ASSESSMENT_DATE, types)
        for e in events:
            self.assertEqual(e.authority_winner, "OWNER_INSTRUCTION")
            self.assertIsNotNone(e.teacher_override)
        # Plan (override) remains Thursday — never silently rewritten.
        self.assertEqual(plan.day("math", "Thursday").assessment.date, "2026-11-05")
        self.assertEqual(plan.day("math", "Thursday").authority, Authority.OWNER_INSTRUCTION)

    def test_d_canvas_only_conflict(self):
        plan = _plan("2026-11-05", override=_override("2026-11-05"))
        sn = _snapshot("2026-11-05", canvas_due="2026-11-06T12:00:00Z")  # canvas Fri
        events = cs.scan(sn, plan=plan)
        self.assertEqual([e.object_type for e in events], [cs.ASSESSMENT_DATE])
        self.assertEqual(events[0].authority_winner, "OWNER_INSTRUCTION")
        self.assertEqual(events[0].old_value, "2026-11-05")
        self.assertEqual(events[0].new_value, "2026-11-06")
        self.assertEqual(plan.day("math", "Thursday").assessment.date, "2026-11-05")

    def test_e_pacing_only_conflict(self):
        plan = _plan("2026-11-05", override=_override("2026-11-05"))
        sn = _snapshot("2026-11-06", canvas_due="2026-11-05T12:00:00Z")  # canvas Thu
        events = cs.scan(sn, plan=plan)
        self.assertEqual([e.object_type for e in events], [cs.PACING_VS_OVERRIDE])
        self.assertEqual(events[0].authority_winner, "OWNER_INSTRUCTION")
        self.assertEqual(events[0].old_value, "2026-11-05")  # override date
        self.assertEqual(events[0].new_value, "2026-11-06")  # pacing date
        self.assertEqual(plan.day("math", "Thursday").assessment.date, "2026-11-05")

    def test_i_source_outage_no_conflict(self):
        plan = _plan("2026-11-05")
        sn = _snapshot("2026-11-05", canvas_status=snap.SNAPSHOT_UNAVAILABLE)
        self.assertEqual(cs.scan(sn, plan=plan), [])
        summary = cs.scan_summary(sn, plan=plan)
        self.assertEqual(summary["status"], "SOURCE_UNAVAILABLE")
        self.assertTrue(summary["unknown_stale"])
        self.assertEqual(summary["conflict_count"], 0)

    def test_g_scheduled_reminder_obsolete(self):
        plan = _plan("2026-11-05")
        sn = _snapshot(
            "2026-11-05", canvas_due="2026-11-05T12:00:00Z",
            canvas_announcements=[
                {"title": "Math Weekly Update", "message": "", "delayed_post_at": None,
                 "posted_at": "2026-10-30T20:00:00Z"},
                {"title": "Math Assessment Reminder", "message": "",
                 # Scheduled for a non-day-before date (Nov 3 vs expected Nov 4).
                 "delayed_post_at": "2026-11-03T12:00:00Z", "posted_at": None},
            ],
        )
        events = cs.scan(sn, plan=plan)
        obsolete = [e for e in events if e.object_type == cs.REMINDER_OBSOLETE]
        self.assertEqual(len(obsolete), 1)


class CrossSourceReconcileTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.env = mock.patch.dict(os.environ, {"TAW_STATE_ROOT": self.tmp})
        self.env.start()

    def tearDown(self):
        self.env.stop()

    def test_h_repeated_polling_dedups(self):
        plan = _plan("2026-11-05")
        pacing = {"identity": {"name": "FPK"}, "cells": reconciliation.pacing_cells_from_plan(plan)}
        canvas = {
            "status": "OK", "observed_at": "2026-10-24T12:00:00Z",
            "courses": {"math": {
                "front_page": {"title": "Q2W3 Math", "page_id": "q2w3"},
                "pages": [{"title": "Q2W3 Math", "page_id": "q2w3", "front_page": True}],
                "assignments": [{"name": "SM5: Written Assessment 8",
                                 "due_at": "2026-11-06T12:00:00Z"}],
                "announcements": [{"title": "Math Weekly Update", "message": "",
                                   "delayed_post_at": None, "posted_at": "2026-10-30T20:00:00Z"}],
            }},
        }
        r1 = reconciliation.sync_and_detect(2, 3, week_id="Q2W3", pacing=pacing, canvas=canvas, plan=plan)
        r2 = reconciliation.sync_and_detect(2, 3, week_id="Q2W3", pacing=pacing, canvas=canvas, plan=plan)
        cross = [e for e in EventStore(2, 3).unresolved()
                 if e.get("classification") == "cross_source_conflict"]
        date_cross = [e for e in cross if e.get("object_type") == "assessment_date"]
        self.assertEqual(len(date_cross), 1)  # one unresolved conflict
        self.assertEqual(r2["new_events_added"], 0)  # no duplicate
        self.assertEqual(r1["canvas_writes"], 0)
        self.assertEqual(r1["notifications_delivered"], 0)


class PublishGateConflictTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.env = mock.patch.dict(os.environ, {"TAW_STATE_ROOT": self.tmp})
        self.env.start()

    def tearDown(self):
        self.env.stop()

    def _seed_conflict(self, *, winner="VERIFIED_PACING", canvas_value="2026-11-06",
                       authoritative="2026-11-05"):
        from scripts.weekly_planner_agent import publish as pub
        from scripts.weekly_planner_agent.models import SourceChangeEvent
        ev = SourceChangeEvent(
            source="cross_source", subject="math", object_type="assessment_date",
            old_value=authoritative, new_value=canvas_value,
            classification="cross_source_conflict", object_identity="math|written|8",
            authority_winner=winner, canvas_value=canvas_value,
            event_id="ev-conflict",
        )
        EventStore(2, 3).record([ev])

    def test_material_conflict_blocks_publish(self):
        from scripts.weekly_planner_agent import publish as pub
        plan = _plan("2026-11-05")
        service = __import__("scripts.weekly_planner_agent.service", fromlist=["service"])
        service.save_plan(2, 3, plan)
        self._seed_conflict()
        gate = pub.build_publish_gate(2, 3, plan=plan, snapshot=None,
                                      rollover_readiness={"ready": True, "blockers": []})
        self.assertFalse(gate["ready"])
        self.assertTrue(any("cross-source" in b.lower() for b in gate["blockers"]))

    def test_override_with_canvas_agreement_does_not_block(self):
        # Override wins, Canvas agrees with the override (only pacing disagreed).
        from scripts.weekly_planner_agent import publish as pub
        plan = _plan("2026-11-05", override=_override("2026-11-05"))
        service = __import__("scripts.weekly_planner_agent.service", fromlist=["service"])
        service.save_plan(2, 3, plan)
        self._seed_conflict(winner="OWNER_INSTRUCTION", canvas_value="2026-11-05",
                            authoritative="2026-11-05")
        gate = pub.build_publish_gate(2, 3, plan=plan, snapshot=None,
                                      rollover_readiness={"ready": True, "blockers": []})
        self.assertFalse(any("cross-source" in b.lower() for b in gate["blockers"]))


class PostedCommunicationTest(unittest.TestCase):
    def test_f_posted_announcement_requires_correction(self):
        # Temporal change: Thursday -> Friday, but the announcement already posted.
        from scripts.weekly_planner_agent.models import SourceChangeEvent
        event = SourceChangeEvent(
            source="pacing", subject="math", object_type="assessment_date",
            old_value="2026-11-05", new_value="2026-11-06",
            classification="assessment_date_changed",
            object_identity="math|Thursday|Written Assessment 8",
            affected_artifacts=["Math weekly page", "Math assessment assignment",
                                "Math first parent announcement", "Math day-before reminder"],
            requires_teacher_approval=True, family_comms_affected=True,
            event_id="ev-posted",
        )
        canvas = {
            "status": "OK",
            "courses": {"math": {
                "front_page": {"title": "Q2W3 Math"},
                "assignments": [{"name": "SM5: Written Assessment 8",
                                 "due_at": "2026-11-05T12:00:00Z"}],
                "announcements": [
                    # First announcement already posted.
                    {"title": "Written Assessment 8 - Thursday, November 5", "message": "",
                     "delayed_post_at": None, "posted_at": "2026-10-30T20:00:00Z"},
                    # Day-before reminder not yet posted.
                    {"title": "Math Assessment Reminder", "message": "",
                     "delayed_post_at": "2026-11-04T12:00:00Z", "posted_at": None},
                ],
            }},
        }
        watch = aw.build_watch([event], canvas)
        self.assertEqual(len(watch), 1)
        entry = watch[0]
        self.assertTrue(entry["already_posted"]["first_announcement"])
        self.assertTrue(entry["recommended_action"]["requires_approval"])
        self.assertIn("correction", entry["recommended_action"]["action"])


if __name__ == "__main__":
    unittest.main()
