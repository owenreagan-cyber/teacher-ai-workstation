"""Real email transport adapter — deterministic tests (no network, no send)."""
from __future__ import annotations

import os
import tempfile
import unittest
from unittest import mock

from scripts.weekly_planner_agent import mail_transport


class MailTransportTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.env = mock.patch.dict(os.environ, {"TAW_STATE_ROOT": self.tmp})
        self.env.start()

    def tearDown(self):
        self.env.stop()

    def _enable_email(self):
        from scripts.weekly_planner_agent import schedule_config as sc
        sc.write_config(delivery={
            "mode": "email", "email_enabled": True,
            "email_recipient": "owen.reagan@thalesacademy.org",
        })

    def test_disabled_email_fails_closed(self):
        result = mail_transport.send("s", "b")
        self.assertFalse(result["accepted"])
        self.assertEqual(result["error"], "EMAIL_DISABLED")

    def test_recipient_safety_delegated_to_canonical_allowlist(self):
        from scripts.canvas_llm_grade_check import emailer
        self.assertIsNotNone(emailer.check_recipient_safety("parent@example.com"))
        self.assertIsNone(emailer.check_recipient_safety("owen.reagan@thalesacademy.org"))

    def test_gmail_transport_maps_to_accepted(self):
        self._enable_email()
        fake = type("R", (), {"sent": True, "message_id": "m1"})()
        with mock.patch.object(mail_transport.gmail_transport, "oauth_ready", return_value=True), \
             mock.patch.object(mail_transport.gmail_transport, "send_via_gmail_api", return_value=fake):
            result = mail_transport.send("subj", "body")
            self.assertTrue(result["accepted"])
            self.assertEqual(result["transport"], "gmail")
            self.assertEqual(result["message_id"], "m1")

    def test_smtp_transport_maps_to_accepted(self):
        self._enable_email()
        with mock.patch.object(mail_transport.gmail_transport, "oauth_ready", return_value=False), \
             mock.patch.object(mail_transport.emailer, "_smtp_config",
                               return_value={"host": "smtp.example.com", "port": "587",
                                             "user": "oreagan81@gmail.com", "password": "x",
                                             "from": "oreagan81@gmail.com"}), \
             mock.patch.object(mail_transport.emailer, "_send_smtp", return_value=None):
            result = mail_transport.send("subj", "body")
            self.assertTrue(result["accepted"])
            self.assertEqual(result["transport"], "smtp")

    def test_no_transport_fails_closed(self):
        self._enable_email()
        with mock.patch.object(mail_transport.gmail_transport, "oauth_ready", return_value=False), \
             mock.patch.object(mail_transport.emailer, "_smtp_config",
                               return_value={"host": "", "port": "587", "user": "", "password": "", "from": ""}):
            result = mail_transport.send("subj", "body")
            self.assertFalse(result["accepted"])
            self.assertEqual(result["error"], "EMAIL_TRANSPORT_NOT_CONFIGURED")

    def test_status_never_sends(self):
        status = mail_transport.transport_status()
        for key in ("gmail_ready", "smtp_ready", "enabled", "recipient_configured"):
            self.assertIn(key, status)


if __name__ == "__main__":
    unittest.main()
