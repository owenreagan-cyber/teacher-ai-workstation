"""Notification delivery abstraction tests (fake/local sinks only)."""
from __future__ import annotations

import os
import tempfile
import unittest
from unittest import mock

from scripts.weekly_planner_agent import delivery
from scripts.weekly_planner_agent import schedule_config
from scripts.weekly_planner_agent.models import (
    NOTIFICATION_DELIVERED,
    NOTIFICATION_DRAFTED,
    NOTIFICATION_FAILED,
    NOTIFICATION_QUEUED,
    NOTIFICATION_SUPPRESSED,
)


class DeliveryTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp()
        self.env = mock.patch.dict(os.environ, {"TAW_STATE_ROOT": self.tmp})
        self.env.start()

    def tearDown(self) -> None:
        self.env.stop()

    def test_preview_sends_nothing(self) -> None:
        rec = delivery.make_record(notification_type="assessment_date_changed",
                                   subject="s", body="b")
        out = delivery.deliver(rec, mode="preview")
        self.assertEqual(out["status"], NOTIFICATION_DRAFTED)
        self.assertEqual(delivery.read_outbox(), [])

    def test_local_sink_records_deterministically(self) -> None:
        rec = delivery.make_record(notification_type="assessment_date_changed",
                                   subject="s", body="b")
        out = delivery.deliver(rec, mode="local")
        self.assertEqual(out["status"], NOTIFICATION_QUEUED)
        self.assertNotEqual(out["status"], NOTIFICATION_DELIVERED)
        self.assertEqual(len(delivery.read_outbox()), 1)

    def test_email_disabled_by_default(self) -> None:
        self.assertFalse(schedule_config.delivery_config()["email_enabled"])
        rec = delivery.make_record(notification_type="assessment_date_changed",
                                   subject="s", body="b")
        out = delivery.deliver(rec, mode="email")
        self.assertEqual(out["status"], NOTIFICATION_FAILED)
        self.assertEqual(out["error"], "EMAIL_DISABLED")

    def test_missing_recipient_blocks_real_delivery(self) -> None:
        rec = delivery.make_record(notification_type="assessment_date_changed",
                                   subject="s", body="b", recipient="")
        sink = delivery.EmailSink(enabled=True, recipient="", from_address="a@b.c")
        out = sink.deliver(rec)
        self.assertEqual(out["status"], NOTIFICATION_FAILED)
        self.assertEqual(out["error"], "RECIPIENT_MISSING")

    def test_idempotency_prevents_repeat_delivery(self) -> None:
        rec = delivery.make_record(notification_type="assessment_date_changed",
                                   subject="s", body="b", related_event_ids=["e1"])
        delivery.deliver(rec, mode="local")
        rec2 = delivery.make_record(notification_type="assessment_date_changed",
                                    subject="s", body="b", related_event_ids=["e1"])
        out2 = delivery.deliver(rec2, mode="local")
        self.assertEqual(out2["status"], NOTIFICATION_SUPPRESSED)

    def test_failure_remains_visible(self) -> None:
        rec = delivery.make_record(notification_type="assessment_date_changed",
                                   subject="s", body="b")
        out = delivery.deliver(rec, mode="email")
        self.assertEqual(out["status"], NOTIFICATION_FAILED)
        self.assertIn("error", out)
        self.assertEqual(len(out["attempts"]), 1)

    def test_notification_cannot_approve_or_publish(self) -> None:
        # A delivered record is data only; it never flips approval or publish state.
        rec = delivery.make_record(notification_type="assessment_date_changed",
                                   subject="s", body="b")
        delivery.deliver(rec, mode="local")
        for key in ("approval", "publish", "canvas_writes"):
            self.assertNotIn(key, rec)


if __name__ == "__main__":
    unittest.main()
