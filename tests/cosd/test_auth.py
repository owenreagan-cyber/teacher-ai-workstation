"""Authentication and policy tests for cosd."""
from __future__ import annotations

import json
import unittest

from support import CosdStateTest, RunningServer, http_json

from cos.audit import verify
from cos.policy import KillSwitch

from cosd.auth import ensure_token, revoke_token, rotate_token


class AuthTests(CosdStateTest):
    def setUp(self):
        super().setUp()
        self.srv = RunningServer(self.state)

    def tearDown(self):
        self.srv.stop()
        super().tearDown()

    def test_missing_token(self):
        status, body = http_json(self.srv.port, "/v1/status")
        self.assertEqual(status, 401)

    def test_invalid_token(self):
        status, _ = http_json(self.srv.port, "/v1/status", token="bad-token")
        self.assertEqual(status, 401)

    def test_rotation_invalidates_old(self):
        old = self.srv.token
        rotate_token(self.state)
        status, _ = http_json(self.srv.port, "/v1/status", token=old)
        self.assertEqual(status, 401)
        new = ensure_token(self.state).token
        status, body = http_json(self.srv.port, "/v1/status", token=new)
        self.assertEqual(status, 200)
        self.assertTrue(body["ok"])

    def test_revocation(self):
        old = self.srv.token
        revoke_token(self.state)
        status, _ = http_json(self.srv.port, "/v1/status", token=old)
        self.assertEqual(status, 401)


class PolicyTests(CosdStateTest):
    def setUp(self):
        super().setUp()
        self.srv = RunningServer(self.state)

    def tearDown(self):
        self.srv.stop()
        super().tearDown()

    def test_kill_switch_enforced(self):
        KillSwitch(self.state).stop("cosd test")
        status, body = http_json(
            self.srv.port,
            "/v1/ask",
            method="POST",
            token=self.srv.token,
            body={"question": "what time is it"},
        )
        self.assertEqual(status, 503)
        self.assertEqual(body["error_kind"], "stopped")
        KillSwitch(self.state).resume()

    def test_audit_chain_intact(self):
        http_json(self.srv.port, "/v1/status", token="wrong")
        http_json(self.srv.port, "/v1/status", token=self.srv.token)
        audit = self.state / "audit.jsonl"
        self.assertTrue(audit.is_file())
        self.assertTrue(verify(audit).ok)


class HealthPrivacyTests(CosdStateTest):
    def setUp(self):
        super().setUp()
        self.srv = RunningServer(self.state)

    def tearDown(self):
        self.srv.stop()
        super().tearDown()

    def test_health_and_status_exclude_secrets(self):
        _, health = http_json(self.srv.port, "/health")
        _, status = http_json(self.srv.port, "/v1/status", token=self.srv.token)
        blob = json.dumps({**health, **status})
        self.assertNotIn(self.srv.token, blob)
        token_path = self.state / "cosd" / "api.token"
        if token_path.is_file():
            self.assertNotIn(token_path.read_text().strip(), blob)
