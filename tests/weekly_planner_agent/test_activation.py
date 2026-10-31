"""Scheduler activation — check-only proofs, guarded publish, notification idempotency.

Deterministic, no network, no real email, no launchd mutation, no live Canvas.

The fixtures use subject "science" (active in Q2, no owner instruction) so the
Q2W3 Math owner override does not interfere with the "stale approval" /
"source changed" scenarios.
"""
from __future__ import annotations

import os
import tempfile
import unittest
from datetime import datetime
from unittest import mock
from zoneinfo import ZoneInfo

from scripts.weekly_planner_agent import activation
from scripts.weekly_planner_agent import delivery
from scripts.weekly_planner_agent import publish as pub
from scripts.weekly_planner_agent import reconciliation
from scripts.weekly_planner_agent import service
from scripts.weekly_planner_agent import snapshot as snap
from scripts.weekly_planner_agent.models import (
    Assessment, Authority, DayPlan, PlanStatus, WeeklyPlan,
)

EASTERN = ZoneInfo("America/New_York")


def _plan(assessment_date="2026-11-05") -> WeeklyPlan:
    plan = WeeklyPlan(week_id="Q2W3", quarter=2, week=3,
                      date_range={"start": "2026-10-26", "end": "2026-10-30"})
    plan.source_provenance = {"name": "FPK", "tab": "4A - Reagan", "spreadsheet_id": "fake"}
    plan.upsert_day(DayPlan(
        subject="science", day="Wednesday", date=assessment_date, lesson="Quiz",
        classwork=["Quiz"], homework=[],
        assessment=Assessment(name="Science Quiz", subject="science",
                              day="Wednesday", date=assessment_date),
        authority=Authority.VERIFIED_PACING, status=PlanStatus.CONFIRMED_SOURCE,
    ))
    return plan


def _snapshot_for(plan: WeeklyPlan) -> dict:
    s = snap.blank_snapshot(2, 3, "Q2W3")
    s["pacing"]["status"] = snap.SNAPSHOT_OK
    s["pacing"]["identity"] = {"name": "FPK"}
    s["pacing"]["cells"] = reconciliation.pacing_cells_from_plan(plan)
    s["pacing"]["fingerprint"] = snap.fingerprint(s["pacing"]["cells"])
    s["canvas"]["status"] = snap.SNAPSHOT_OK
    s["canvas"]["observed_at"] = "2026-11-01T00:00:00Z"
    s["canvas"]["courses"] = {}
    return s


class PlistTest(unittest.TestCase):
    def test_calendar_only_and_no_secrets(self):
        plist = activation.build_plist()
        self.assertEqual(plist["Label"], activation.LAUNCH_AGENT_LABEL)
        for key in activation.FORBIDDEN_TRIGGER_KEYS:
            self.assertNotIn(key, plist)
        xml = activation.render_plist_xml().lower()
        for secret in ("password", "token", "secret", "refresh_token", "access_token", "smtp_"):
            self.assertNotIn(secret, xml)
        self.assertIn("--scheduled", plist["ProgramArguments"])

    def test_validate_rejects_off_schedule_triggers(self):
        plist = activation.build_plist()
        bad = dict(plist)
        bad["RunAtLoad"] = True
        with self.assertRaises(activation.ScheduleError):
            activation.validate_plist_triggers(bad)


class DispatchTest(unittest.TestCase):
    def test_friday_milestones_target_upcoming_instructional_week(self):
        cases = [
            (datetime(2026, 10, 30, 14, 0, tzinfo=EASTERN),
             "CHECK", (2, 3)),
            (datetime(2026, 10, 30, 15, 0, tzinfo=EASTERN),
             "REFRESH", (2, 4)),
            (datetime(2026, 10, 30, 15, 30, tzinfo=EASTERN),
             "NOTIFY", (2, 4)),
            (datetime(2026, 10, 30, 16, 0, tzinfo=EASTERN),
             "PUBLISH", (2, 4)),
            (datetime(2026, 11, 6, 15, 0, tzinfo=EASTERN),
             "REFRESH", (2, 5)),
            (datetime(2026, 11, 6, 16, 0, tzinfo=EASTERN),
             "PUBLISH", (2, 5)),
            (datetime(2026, 10, 27, 10, 0, tzinfo=EASTERN),
             "CHECK", (2, 3)),
        ]

        for now, expected_action, expected_week in cases:
            with self.subTest(now=now, action=expected_action):
                with (
                    mock.patch.object(
                        activation, "check_scheduled",
                        return_value={"action": "CHECK"}
                    ) as check,
                    mock.patch.object(
                        activation, "refresh_scheduled",
                        return_value={"action": "REFRESH"}
                    ) as refresh,
                    mock.patch.object(
                        activation, "notify_scheduled",
                        return_value={"action": "NOTIFY"}
                    ) as notify,
                    mock.patch.object(
                        activation, "publish_scheduled",
                        return_value={"action": "PUBLISH"}
                    ) as publish,
                ):
                    result = activation.dispatch(now)

                self.assertEqual(result["action"], expected_action)

                routes = {
                    "CHECK": check,
                    "REFRESH": refresh,
                    "NOTIFY": notify,
                    "PUBLISH": publish,
                }

                called = [name for name, route in routes.items()
                          if route.called]

                self.assertEqual(called, [expected_action])

                actual_week = routes[expected_action].call_args.args[:2]
                self.assertEqual(actual_week, expected_week)


class GuardedPublishTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.env = mock.patch.dict(os.environ, {"TAW_STATE_ROOT": self.tmp})
        self.env.start()

    def tearDown(self):
        self.env.stop()

    def _seed(self, plan):
        service.save_plan(2, 3, plan)
        snap.save(2, 3, _snapshot_for(plan))

    def _approve_effective(self):
        # Approval binds to the EFFECTIVE plan (the one service.load_plan returns,
        # which includes the Q2W3 Math owner instruction) so plan_version is
        # computed against exactly what publish_scheduled will load.
        effective = service.load_plan(2, 3)
        pub.approve_plan(2, 3, plan=effective, snapshot=snap.load(2, 3))
        return effective

    def test_no_approval_blocks_with_zero_writes(self):
        plan = _plan()
        self._seed(plan)
        result = activation.publish_scheduled(2, 3)
        self.assertFalse(result["published"])
        self.assertEqual(result["state"], "BLOCKED")
        self.assertEqual(result["canvas_writes"], 0)
        self.assertTrue(any("not approved" in b.lower() for b in result["blockers"]))

    def test_stale_approval_blocks(self):
        plan = _plan()
        self._seed(plan)
        self._approve_effective()
        # Plan changes after approval -> stale approval.
        effective = service.load_plan(2, 3)
        effective.day("science", "Wednesday").assessment.date = "2026-11-06"
        service.save_plan(2, 3, effective)
        result = activation.publish_scheduled(2, 3)
        self.assertFalse(result["published"])
        self.assertEqual(result["state"], "BLOCKED")
        self.assertEqual(result["canvas_writes"], 0)
        self.assertTrue(any("changed after approval" in b.lower() for b in result["blockers"]))

    def test_source_changed_after_approval_blocks(self):
        plan = _plan()
        self._seed(plan)
        self._approve_effective()
        changed = _snapshot_for(service.load_plan(2, 3))
        changed["pacing"]["fingerprint"] = "changed-after-approval"
        snap.save(2, 3, changed)
        result = activation.publish_scheduled(2, 3)
        self.assertFalse(result["published"])
        self.assertEqual(result["state"], "BLOCKED")
        self.assertEqual(result["canvas_writes"], 0)

    def test_fake_approved_publish_reaches_verified(self):
        from scripts.canvas_llm_rollover import rollover
        plan = _plan()
        self._seed(plan)
        self._approve_effective()
        fake_report = {"lifecycle": "PUBLISHED_VERIFIED", "verb_totals": {"GET": 2, "PUT": 1, "POST": 2}}
        with mock.patch.object(rollover, "build_readiness",
                               return_value={"ready": True, "blockers": [], "needs_owen": False}), \
             mock.patch.object(rollover, "publish_weekly_package", return_value=fake_report) as pkg:
            result = activation.publish_scheduled(2, 3, client_factory=lambda: object())
        self.assertTrue(result["published"], result)
        self.assertEqual(result["state"], "PUBLISHED_VERIFIED")
        pkg.assert_called_once()


class NotificationIdempotencyTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.env = mock.patch.dict(os.environ, {"TAW_STATE_ROOT": self.tmp})
        self.env.start()

    def tearDown(self):
        self.env.stop()

    def _enable_email(self):
        from scripts.weekly_planner_agent import schedule_config as sc
        sc.write_config(delivery={"mode": "email", "email_enabled": True,
                                  "email_recipient": "owen.reagan@thalesacademy.org"})

    def test_repeated_delivery_suppresses_duplicate(self):
        self._enable_email()
        rec1 = delivery.make_record(
            notification_type="friday_review_ready", subject="s", body="b",
            related_event_ids=["friday-review:Q2W3"], plan_version="v1",
        )
        with mock.patch("scripts.weekly_planner_agent.mail_transport.send",
                        return_value={"accepted": True, "transport": "gmail", "message_id": "m"}):
            out1 = delivery.deliver(rec1, mode="email")
            self.assertEqual(out1["status"], "sent")
            rec2 = delivery.make_record(
                notification_type="friday_review_ready", subject="s", body="b",
                related_event_ids=["friday-review:Q2W3"], plan_version="v1",
            )
            out2 = delivery.deliver(rec2, mode="email")
            self.assertEqual(out2["status"], "suppressed")

    def test_failed_delivery_does_not_suppress_retry(self):
        self._enable_email()
        rec = delivery.make_record(notification_type="pacing_changed", subject="s",
                                   body="b", related_event_ids=["ev-1"])
        with mock.patch("scripts.weekly_planner_agent.mail_transport.send",
                        return_value={"accepted": False, "transport": None,
                                      "message_id": None, "error": "smtp send error: TimeoutError"}):
            out = delivery.deliver(rec, mode="email")
            self.assertEqual(out["status"], "failed")
        rec2 = delivery.make_record(notification_type="pacing_changed", subject="s",
                                    body="b", related_event_ids=["ev-1"])
        self.assertFalse(delivery.already_delivered(rec2["idempotency_key"]))

    def test_friday_notify_suppresses_without_plan(self):
        result = service.friday_notify(2, 3)
        self.assertEqual(result["status"], "NO_PLAN")
        self.assertFalse(result["sent"])
        self.assertEqual(result["canvas_writes"], 0)


if __name__ == "__main__":
    unittest.main()
