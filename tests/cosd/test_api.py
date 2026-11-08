"""HTTP API contract tests for cosd (hermetic, fixture mode)."""
from __future__ import annotations

import json
import logging
import time
import unittest
from unittest import mock

from support import CosdStateTest, RunningServer, http_json

from cosd.constants import MAX_BODY_BYTES
from cosd import server as cosd_server


class ApiTests(CosdStateTest):
    def setUp(self):
        super().setUp()
        self.srv = RunningServer(self.state)

    def tearDown(self):
        self.srv.stop()
        super().tearDown()

    def test_health_no_auth(self):
        status, body = http_json(self.srv.port, "/health")
        self.assertEqual(status, 200)
        self.assertTrue(body["ok"])
        self.assertEqual(body["service"], "cosd")
        self.assertNotIn("token", json.dumps(body))

    def test_status_requires_auth(self):
        status, body = http_json(self.srv.port, "/v1/status")
        self.assertEqual(status, 401)
        self.assertFalse(body["ok"])

    def test_status_ok(self):
        status, body = http_json(self.srv.port, "/v1/status", token=self.srv.token)
        self.assertEqual(status, 200)
        self.assertTrue(body["ok"])
        self.assertEqual(body["cosd"], "0.1.0")
        self.assertIn("fixture", body)

    def test_ask_fastpath(self):
        status, body = http_json(
            self.srv.port,
            "/v1/ask",
            method="POST",
            token=self.srv.token,
            body={"question": "what time is it"},
        )
        self.assertEqual(status, 200)
        self.assertTrue(body["ok"])
        self.assertIn("text", body)

    def test_ask_invalid_body(self):
        status, body = http_json(
            self.srv.port,
            "/v1/ask",
            method="POST",
            token=self.srv.token,
            body={},
        )
        self.assertEqual(status, 400)
        self.assertFalse(body["ok"])

    def test_unknown_route(self):
        status, body = http_json(self.srv.port, "/v1/nope", token=self.srv.token)
        self.assertEqual(status, 404)

    def test_method_not_allowed(self):
        status, body = http_json(
            self.srv.port,
            "/v1/ask",
            method="PUT",
            token=self.srv.token,
        )
        self.assertEqual(status, 405)
        self.assertEqual(body["error_kind"], "method")

    def test_oversized_request(self):
        big = b"x" * (MAX_BODY_BYTES + 1)
        status, body = http_json(
            self.srv.port,
            "/v1/ask",
            method="POST",
            token=self.srv.token,
            raw_body=big,
        )
        self.assertEqual(status, 413)

    def test_token_not_logged(self):
        records: list[str] = []

        class Capture(logging.Handler):
            def emit(self, record):
                records.append(record.getMessage())

        root = logging.getLogger("cosd")
        handler = Capture()
        root.addHandler(handler)
        self.addCleanup(root.removeHandler, handler)
        http_json(self.srv.port, "/v1/status", token=self.srv.token)
        joined = "\n".join(records)
        self.assertNotIn(self.srv.token, joined)


class AskTimeoutTest(CosdStateTest):
    def test_ask_timeout(self):
        def slow_ask(*_a, **_k):
            time.sleep(2)
            return 0, {"ok": True, "text": "late"}

        with mock.patch.object(cosd_server, "ASK_TIMEOUT_S", 0.05), mock.patch.object(
            cosd_server, "run_ask", slow_ask
        ):
            srv = RunningServer(self.state, use_subprocess=False)
            try:
                status, body = http_json(
                    srv.port,
                    "/v1/ask",
                    method="POST",
                    token=srv.token,
                    body={"question": "ping"},
                )
                self.assertEqual(status, 504)
                self.assertEqual(body["error_kind"], "timeout")
            finally:
                srv.stop()


class BindTests(unittest.TestCase):
    def test_non_loopback_rejected(self):
        from cosd.server import validate_bind_host

        with self.assertRaises(ValueError):
            validate_bind_host("0.0.0.0")
        self.assertEqual(validate_bind_host("localhost"), "127.0.0.1")
