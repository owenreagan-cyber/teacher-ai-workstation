"""Compatibility with the existing loopback master-token clients."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from device_support import DeviceStateTest, http_json_auth


class CompatibilityTests(DeviceStateTest):
    def setUp(self):
        super().setUp()
        self.srv = self.start_server()

    def tearDown(self):
        self.srv.stop()
        super().tearDown()

    def bearer(self):
        return f"Bearer {self.srv.token}"

    def test_existing_endpoints_still_work_with_master_token(self):
        status, body = http_json_auth(
            self.srv.port, "/health"
        )
        self.assertEqual(status, 200)
        self.assertTrue(body["ok"])

        status, body = http_json_auth(
            self.srv.port, "/v1/status", authorization=self.bearer()
        )
        self.assertEqual(status, 200)
        self.assertTrue(body["ok"])

        status, body = http_json_auth(
            self.srv.port,
            "/v1/tasks",
            method="POST",
            authorization=self.bearer(),
            body={"kind": "diagnostic", "title": "compat"},
        )
        self.assertEqual(status, 201)
        task_id = body["task"]["id"]
        status, body = http_json_auth(
            self.srv.port, "/v1/tasks", authorization=self.bearer()
        )
        self.assertEqual(status, 200)
        self.assertEqual(body["total"], 1)
        status, _ = http_json_auth(
            self.srv.port, f"/v1/tasks/{task_id}", authorization=self.bearer()
        )
        self.assertEqual(status, 200)

        status, body = http_json_auth(
            self.srv.port,
            "/v1/ask",
            method="POST",
            authorization=self.bearer(),
            body={"question": "what time is it"},
        )
        self.assertEqual(status, 200)
        self.assertTrue(body["ok"])

    def test_master_token_is_not_a_device_token(self):
        status, body = http_json_auth(
            self.srv.port,
            "/v1/status",
            authorization=f"Chief-Device {self.srv.token}",
        )
        self.assertEqual(status, 401)

    def test_device_registry_uses_one_database_file(self):
        self.make_device()
        cosd_dir = self.state / "cosd"
        names = sorted(p.name for p in cosd_dir.iterdir() if p.is_file())
        self.assertIn("tasks.sqlite3", names)
        self.assertNotIn("devices.sqlite3", names)

    def test_device_operations_leave_api_token_untouched(self):
        token_path = self.state / "cosd" / "api.token"
        before = token_path.read_text(encoding="utf-8")
        device, _ = self.make_device()
        self.registry.disable_device(device.device_id)
        self.registry.revoke_device(device.device_id)
        after = token_path.read_text(encoding="utf-8")
        self.assertEqual(before, after)

    def test_no_raw_token_or_keychain_reference_in_api_json(self):
        status, body = http_json_auth(
            self.srv.port,
            "/v1/devices",
            method="POST",
            authorization=self.bearer(),
            body={"display_name": "Leak check", "device_profile": "read_only"},
        )
        self.assertEqual(status, 201)
        text = json.dumps(body)
        self.assertNotIn("keychain_ref", text)
        self.assertNotIn("verifier", text)
        self.assertNotIn("verifier_salt", text)
        self.assertNotIn("secret", text)
        device_id = body["device"]["device_id"]
        status, creds = http_json_auth(
            self.srv.port,
            f"/v1/devices/{device_id}/credentials",
            authorization=self.bearer(),
        )
        self.assertEqual(status, 200)
        self.assertNotIn("keychain_ref", json.dumps(creds))
        self.assertNotIn("verifier", json.dumps(creds))


if __name__ == "__main__":
    unittest.main()
