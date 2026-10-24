"""Guarded publish + plan-version binding + full acceptance scenario tests."""
from __future__ import annotations

import os
import tempfile
import unittest
from unittest import mock

from scripts.weekly_planner_agent import publish as pub
from scripts.weekly_planner_agent import reconciliation
from scripts.weekly_planner_agent import service
from scripts.weekly_planner_agent import snapshot as snap
from scripts.weekly_planner_agent.event_store import EventStore
from scripts.weekly_planner_agent.models import (
    Assessment,
    Authority,
    DayPlan,
    PlanStatus,
    WeeklyPlan,
)
from scripts.canvas_llm_rollover import rollover


def _baseline_plan() -> WeeklyPlan:
    plan = WeeklyPlan(week_id="Q2W3", quarter=2, week=3,
                      date_range={"start": "2026-10-26", "end": "2026-10-30"})
    plan.source_provenance = {"name": "FPK Pacing Guides", "tab": "4A - Reagan",
                              "spreadsheet_id": "fake"}
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


def _snapshot_for(plan: WeeklyPlan, *, canvas_status="OK") -> dict[str, Any]:
    snap_obj = snap.blank_snapshot(2, 3, plan.week_id)
    snap_obj["pacing"]["status"] = snap.SNAPSHOT_OK
    snap_obj["pacing"]["identity"] = {"name": "FPK Pacing Guides"}
    snap_obj["pacing"]["cells"] = reconciliation.pacing_cells_from_plan(plan)
    snap_obj["pacing"]["fingerprint"] = snap.fingerprint(snap_obj["pacing"]["cells"])
    snap_obj["canvas"]["status"] = canvas_status
    snap_obj["canvas"]["observed_at"] = "2026-11-01T00:00:00Z"
    snap_obj["canvas"]["courses"] = {}
    return snap_obj


class PlanVersionTest(unittest.TestCase):
    def test_plan_version_is_stable_and_content_sensitive(self) -> None:
        plan = _baseline_plan()
        v1 = pub.plan_version(plan)
        self.assertEqual(v1, pub.plan_version(plan))
        plan.day("math", "Thursday").assessment.date = "2026-11-06"
        self.assertNotEqual(v1, pub.plan_version(plan))

    def test_source_fingerprint_distinguishes_snapshots(self) -> None:
        plan = _baseline_plan()
        s1 = _snapshot_for(plan)
        s2 = _snapshot_for(plan)
        s2["pacing"]["fingerprint"] = "different"
        self.assertNotEqual(pub.source_fingerprint(s1), pub.source_fingerprint(s2))


class PublishGateTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp()
        self.env = mock.patch.dict(os.environ, {"TAW_STATE_ROOT": self.tmp})
        self.env.start()

    def tearDown(self) -> None:
        self.env.stop()

    def _seed(self, plan: WeeklyPlan, snapshot: dict[str, Any]) -> None:
        service.save_plan(2, 3, plan)
        snap.save(2, 3, snapshot)

    def test_gate_blocks_without_snapshot(self) -> None:
        plan = _baseline_plan()
        service.save_plan(2, 3, plan)
        gate = pub.build_publish_gate(2, 3, plan=plan, snapshot=None,
                                      rollover_readiness={"ready": True, "blockers": []})
        self.assertFalse(gate["ready"])
        self.assertTrue(any("snapshot" in b.lower() for b in gate["blockers"]))

    def test_gate_blocks_without_approval(self) -> None:
        plan = _baseline_plan()
        self._seed(plan, _snapshot_for(plan))
        gate = pub.build_publish_gate(2, 3, plan=plan, snapshot=snap.load(2, 3),
                                      rollover_readiness={"ready": True, "blockers": []})
        self.assertFalse(gate["ready"])
        self.assertTrue(any("not approved" in b for b in gate["blockers"]))

    def test_source_change_after_approval_blocks(self) -> None:
        plan = _baseline_plan()
        self._seed(plan, _snapshot_for(plan))
        with mock.patch.object(pub, "approve_plan", wraps=lambda q, w, **kw: None):
            pass
        # Approve against the current plan/source.
        approval = pub.approve_plan(2, 3, plan=plan, snapshot=snap.load(2, 3))
        self.assertTrue(approval["approval"]["plan_version"])
        # Source changes after approval.
        changed_snap = _snapshot_for(plan)
        changed_snap["pacing"]["fingerprint"] = "changed-after-approval"
        snap.save(2, 3, changed_snap)
        gate = pub.build_publish_gate(2, 3, plan=plan, snapshot=snap.load(2, 3),
                                      rollover_readiness={"ready": True, "blockers": []})
        self.assertFalse(gate["ready"])
        self.assertTrue(any("source changed after approval" in b for b in gate["blockers"]))

    def test_plan_change_after_approval_blocks(self) -> None:
        plan = _baseline_plan()
        self._seed(plan, _snapshot_for(plan))
        pub.approve_plan(2, 3, plan=plan, snapshot=snap.load(2, 3))
        plan.day("math", "Thursday").assessment.date = "2026-11-06"
        gate = pub.build_publish_gate(2, 3, plan=plan, snapshot=snap.load(2, 3),
                                      rollover_readiness={"ready": True, "blockers": []})
        self.assertFalse(gate["ready"])
        self.assertTrue(any("plan changed after approval" in b for b in gate["blockers"]))

    def test_ready_gate_when_all_clear(self) -> None:
        plan = _baseline_plan()
        self._seed(plan, _snapshot_for(plan))
        pub.approve_plan(2, 3, plan=plan, snapshot=snap.load(2, 3))
        gate = pub.build_publish_gate(2, 3, plan=plan, snapshot=snap.load(2, 3),
                                      rollover_readiness={"ready": True, "blockers": []})
        self.assertTrue(gate["ready"], gate["blockers"])


class PublishFlowTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp()
        self.env = mock.patch.dict(os.environ, {"TAW_STATE_ROOT": self.tmp})
        self.env.start()

    def tearDown(self) -> None:
        self.env.stop()

    def test_publish_success_transitions_to_published_verified(self) -> None:
        plan = _baseline_plan()
        service.save_plan(2, 3, plan)
        snap.save(2, 3, _snapshot_for(plan))
        pub.approve_plan(2, 3, plan=plan, snapshot=snap.load(2, 3))
        fake_report = {"lifecycle": "PUBLISHED_VERIFIED", "verb_totals": {"GET": 2, "PUT": 1}}
        with mock.patch.object(rollover, "build_readiness", return_value={"ready": True, "blockers": [], "needs_owen": False}), \
             mock.patch.object(rollover, "publish_weekly_package", return_value=fake_report) as pkg:
            result = pub.publish(2, 3, client=object(), from_quarter=2, from_week=2)
        pkg.assert_called_once()
        self.assertTrue(result["published"])
        self.assertEqual(result["review_state"], "PUBLISHED_VERIFIED")
        self.assertEqual(pub.last_publish(2, 3)["lifecycle"], "PUBLISHED_VERIFIED")

    def test_publish_blocked_when_gate_fails(self) -> None:
        plan = _baseline_plan()
        service.save_plan(2, 3, plan)
        snap.save(2, 3, _snapshot_for(plan))
        # No approval -> gate fails -> publisher never invoked.
        with mock.patch.object(rollover, "build_readiness", return_value={"ready": True, "blockers": [], "needs_owen": False}), \
             mock.patch.object(rollover, "publish_weekly_package") as pkg:
            result = pub.publish(2, 3, client=object(), from_quarter=2, from_week=2)
        pkg.assert_not_called()
        self.assertFalse(result["published"])
        self.assertEqual(result["review_state"], "BLOCKED")

    def test_publish_failure_marks_blocked(self) -> None:
        plan = _baseline_plan()
        service.save_plan(2, 3, plan)
        snap.save(2, 3, _snapshot_for(plan))
        pub.approve_plan(2, 3, plan=plan, snapshot=snap.load(2, 3))
        fake_report = {"lifecycle": "BLOCKED", "verb_totals": {}}
        with mock.patch.object(rollover, "build_readiness", return_value={"ready": True, "blockers": [], "needs_owen": False}), \
             mock.patch.object(rollover, "publish_weekly_package", return_value=fake_report):
            result = pub.publish(2, 3, client=object(), from_quarter=2, from_week=2)
        self.assertFalse(result["published"])
        self.assertEqual(result["review_state"], "BLOCKED")


class AcceptanceScenarioTest(unittest.TestCase):
    """The deterministic end-to-end acceptance sequence (fake publisher)."""

    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp()
        self.env = mock.patch.dict(os.environ, {"TAW_STATE_ROOT": self.tmp})
        self.env.start()

    def tearDown(self) -> None:
        self.env.stop()

    def _pacing(self, plan: WeeklyPlan) -> dict[str, Any]:
        return {"identity": plan.source_provenance,
                "cells": reconciliation.pacing_cells_from_plan(plan)}

    def _canvas_ok(self) -> dict[str, Any]:
        return {"status": "OK", "observed_at": "2026-11-01T00:00:00Z", "courses": {}}

    def _sync(self, plan: WeeklyPlan) -> dict[str, Any]:
        return service.sync(2, 3, pacing=self._pacing(plan), canvas=self._canvas_ok())

    def test_full_guarded_publish_sequence(self) -> None:
        baseline = _baseline_plan()

        # 1. Baseline: Math WA8 Thursday (no false alerts).
        service.save_plan(2, 3, baseline)
        self._sync(baseline)
        self.assertEqual(len(EventStore(2, 3).all()), 0)

        # 2-3. Change fixture -> Friday; one stable Assessment Date Watch event.
        src_friday = _baseline_plan()
        src_friday.day("math", "Thursday").assessment.date = "2026-11-06"
        report = self._sync(src_friday)
        watch = [e for e in report["events"] if e["classification"] == "assessment_date_changed"]
        self.assertEqual(len(watch), 1)
        event = watch[0]
        self.assertTrue(any("weekly page" in a for a in event["affected_artifacts"]))
        self.assertTrue(any("assignment" in a for a in event["affected_artifacts"]))
        self.assertTrue(any("announcement" in a for a in event["affected_artifacts"]))
        self.assertTrue(any("reminder" in a for a in event["affected_artifacts"]))

        # 4. Draft + record a complete notification in the local sink.
        nrec = service.deliver_notification(2, 3, event_id=event["event_id"], mode="local")
        self.assertEqual(nrec["status"], "queued")
        self.assertIn("Would you like me to update", nrec["body"])
        self.assertEqual(len(service.notifications(2, 3)), 1)

        # 5. Simulated plain-language instruction updates the candidate plan.
        result = service.instruct(2, 3, "Yes, but leave the reminder scheduled for now.")
        self.assertTrue(result["matched"])

        # 6. The changed candidate requires fresh approval (plan-version binding).
        revised = service.load_plan(2, 3)
        approval = pub.approve_plan(2, 3, plan=revised, snapshot=snap.load(2, 3))
        self.assertTrue(approval["approval"]["plan_version"])

        # 7. A simulated source change after approval blocks publishing.
        src_changed = _baseline_plan()
        src_changed.day("math", "Thursday").assessment.date = "2026-11-06"
        src_changed.day("science", "Wednesday").lesson = "Chapter 8"
        self._sync(src_changed)
        gate = pub.build_publish_gate(2, 3, plan=revised, snapshot=snap.load(2, 3),
                                      rollover_readiness={"ready": True, "blockers": []})
        self.assertFalse(gate["ready"])
        self.assertTrue(any("source changed after approval" in b for b in gate["blockers"]))

        # 8-9. Refresh + re-approve, then the fake publisher runs.
        pub.approve_plan(2, 3, plan=revised, snapshot=snap.load(2, 3))
        fake_report = {"lifecycle": "PUBLISHED_VERIFIED",
                       "verb_totals": {"GET": 4, "PUT": 1, "POST": 2}}
        with mock.patch.object(rollover, "build_readiness",
                               return_value={"ready": True, "blockers": [], "needs_owen": False}), \
             mock.patch.object(rollover, "publish_weekly_package", return_value=fake_report):
            published = pub.publish(2, 3, client=object(), from_quarter=2, from_week=2)

        # 10. Successful readback -> PUBLISHED_VERIFIED.
        self.assertTrue(published["published"], published["gate"]["blockers"])
        self.assertEqual(published["review_state"], "PUBLISHED_VERIFIED")

        # 11. Repeated polling/retry does not duplicate events/notifications.
        again = self._sync(src_changed)
        self.assertEqual(again["new_events_added"], 0)
        nrec2 = service.deliver_notification(2, 3, event_id=event["event_id"], mode="local")
        self.assertEqual(nrec2["status"], "suppressed")  # idempotent

        # 12. No live writes / real messages (fake client + local sink only).
        self.assertEqual(report["canvas_writes"], 0)
        self.assertEqual(report["notifications_delivered"], 0)


if __name__ == "__main__":
    unittest.main()
