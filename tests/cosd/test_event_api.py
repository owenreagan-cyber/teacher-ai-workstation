"""SSE /v1/events and /v1/runtime API tests."""
from __future__ import annotations

import unittest

from support import CosdStateTest, RunningServer, http_json


class EventApiTest(CosdStateTest):
    def setUp(self):
        super().setUp()
        self.srv = RunningServer(self.state)

    def tearDown(self):
        self.srv.stop()
        super().tearDown()

    def test_runtime_no_token_leak(self):
        status, body = http_json(self.srv.port, "/v1/runtime", token=self.srv.token)
        self.assertEqual(status, 200)
        self.assertTrue(body.get("ok"))
        self.assertIn("task_counts", body)
        raw = str(body)
        self.assertNotIn(self.srv.token, raw)

    def test_events_requires_auth(self):
        status, _ = http_json(self.srv.port, "/v1/events")
        self.assertEqual(status, 401)
