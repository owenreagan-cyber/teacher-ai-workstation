"""Daemon API surface expected by cosd.client."""
from __future__ import annotations

import unittest

from support import CosdStateTest, RunningServer, http_json


class DaemonApiCompatibilityTest(CosdStateTest):
    def setUp(self):
        super().setUp()
        self.srv = RunningServer(self.state)

    def tearDown(self):
        self.srv.stop()
        super().tearDown()

    def test_health_contract(self):
        status, body = http_json(self.srv.port, "/health")
        self.assertEqual(status, 200)
        self.assertTrue(body.get("ok"))
        self.assertEqual(body.get("service"), "cosd")
        self.assertIn("version", body)

    def test_status_requires_auth(self):
        status, body = http_json(self.srv.port, "/v1/status")
        self.assertEqual(status, 401)
        self.assertEqual(body.get("error_kind"), "auth")

    def test_status_authenticated_matches_client_probe(self):
        status, body = http_json(self.srv.port, "/v1/status", token=self.srv.token)
        self.assertEqual(status, 200)
        self.assertTrue(body.get("ok"))
        from cosd.client import CosdClient

        client = CosdClient(self.state)
        ep = client.discover()
        self.assertIsNotNone(ep)
        assert ep is not None
        self.assertTrue(ep.authenticated)
        self.assertGreaterEqual(tuple(int(x) for x in ep.version.split(".")[:3]), (0, 1, 0))

    def test_ask_contract_fields(self):
        status, body = http_json(
            self.srv.port,
            "/v1/ask",
            method="POST",
            token=self.srv.token,
            body={"question": "ping"},
        )
        self.assertEqual(status, 200)
        self.assertTrue(body.get("ok"))
        self.assertTrue("text" in body or "answer" in body)


if __name__ == "__main__":
    unittest.main()
