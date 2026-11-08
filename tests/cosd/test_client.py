"""cosd HTTP client tests."""
from __future__ import annotations

import json
import os
import unittest

from cosd.client import CosdClient, CosdClientError, daemon_mode_from_env, DaemonMode

from support import CosdStateTest, RunningServer


class ClientTests(CosdStateTest):
    def test_non_loopback_rejected(self):
        client = CosdClient(self.state)
        with self.assertRaises(CosdClientError):
            client._request("192.168.1.1", 80, "/v1/status")  # noqa: SLF001

    def test_discover_when_down(self):
        self.assertFalse(CosdClient(self.state).is_available())


class ClientLiveTests(CosdStateTest):
    def setUp(self):
        super().setUp()
        self.srv = RunningServer(self.state)

    def tearDown(self):
        self.srv.stop()
        super().tearDown()

    def test_ask_and_status_no_token_leak(self):
        client = CosdClient(self.state)
        self.assertTrue(client.is_available())
        code, body = client.ask(question="what time is it")
        self.assertEqual(code, 0)
        self.assertTrue(body.get("ok"))
        _, status = client.status()
        blob = json.dumps(status)
        self.assertNotIn(client._token_value(), blob)


class EnvTests(unittest.TestCase):
    def test_daemon_mode_env(self):
        old = os.environ.get("COS_USE_DAEMON")
        try:
            os.environ["COS_USE_DAEMON"] = "required"
            self.assertEqual(daemon_mode_from_env(), DaemonMode.REQUIRED)
        finally:
            if old is None:
                os.environ.pop("COS_USE_DAEMON", None)
            else:
                os.environ["COS_USE_DAEMON"] = old
