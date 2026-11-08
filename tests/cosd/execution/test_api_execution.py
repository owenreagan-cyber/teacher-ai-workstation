"""HTTP execution API tests."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tests" / "cosd"))
from support import CosdStateTest, RunningServer, http_json  # noqa: E402


class ExecutionApiTests(CosdStateTest):
    def setUp(self):
        super().setUp()
        self.srv = RunningServer(self.state)

    def tearDown(self):
        self.srv.stop()
        super().tearDown()

    def test_execute_and_attempts(self):
        _, created = http_json(
            self.srv.port,
            "/v1/tasks",
            method="POST",
            token=self.srv.token,
            body={"kind": "noop", "title": "api"},
        )
        tid = created["task"]["id"]
        status, body = http_json(
            self.srv.port, f"/v1/tasks/{tid}/execute", method="POST", token=self.srv.token, body={}
        )
        self.assertEqual(status, 200)
        self.assertTrue(body.get("ok"))
        _, attempts = http_json(self.srv.port, f"/v1/tasks/{tid}/attempts", token=self.srv.token)
        self.assertGreaterEqual(len(attempts["attempts"]), 1)

    def test_queue_status_requires_auth(self):
        status, _ = http_json(self.srv.port, "/v1/queue")
        self.assertEqual(status, 401)

    def test_unregistered_kind_fails(self):
        _, created = http_json(
            self.srv.port,
            "/v1/tasks",
            method="POST",
            token=self.srv.token,
            body={"kind": "shell", "title": "bad"},
        )
        tid = created["task"]["id"]
        status, body = http_json(
            self.srv.port, f"/v1/tasks/{tid}/execute", method="POST", token=self.srv.token, body={}
        )
        self.assertIn(status, (200, 500))
        self.assertFalse(body.get("ok", True))
