"""Authenticated local device API tests."""
from __future__ import annotations

import unittest
from unittest import mock

from device_support import DeviceStateTest, http_json_auth

import cosd.server as cosd_server
from cosd.devices import CredentialProviderError


class FailingProvider:
    def get_secret(self, reference):
        raise CredentialProviderError("unavailable")

    def set_secret(self, reference, secret):
        raise CredentialProviderError("unavailable")

    def delete_secret(self, reference):
        raise CredentialProviderError("unavailable")


class DeviceApiTests(DeviceStateTest):
    def setUp(self):
        super().setUp()
        self.srv = self.start_server()

    def tearDown(self):
        self.srv.stop()
        super().tearDown()

    def bearer(self):
        return f"Bearer {self.srv.token}"

    def call(self, path, *, method="GET", body=None, authorization=None):
        return http_json_auth(
            self.srv.port,
            path,
            method=method,
            body=body,
            authorization=authorization if authorization is not None else self.bearer(),
        )

    def test_requires_authentication(self):
        status, body = http_json_auth(self.srv.port, "/v1/devices")
        self.assertEqual(status, 401)
        self.assertEqual(body["error_kind"], "auth")
        status, _ = http_json_auth(
            self.srv.port, "/v1/devices", authorization="Bearer deadbeef"
        )
        self.assertEqual(status, 401)

    def test_register_list_detail_update_disable_enable_revoke_remove(self):
        status, body = self.call(
            "/v1/devices",
            method="POST",
            body={
                "display_name": "Classroom iPad",
                "device_type": "ipad",
                "platform": "ipados",
                "owner_id": "school",
                "device_profile": "school",
                "metadata": {"tag": "cart-1"},
            },
        )
        self.assertEqual(status, 201)
        self.assertTrue(body["ok"])
        device = body["device"]
        self.assertEqual(device["device_profile"], "school")
        self.assertEqual(device["status"], "active")
        self.assertIn("credential", body)
        for forbidden in ("token", "secret", "verifier", "keychain_ref"):
            self.assertNotIn(forbidden, body["credential"])
            self.assertNotIn(forbidden, str(body["device"]))
        device_id = device["device_id"]

        status, body = self.call("/v1/devices")
        self.assertEqual(status, 200)
        self.assertEqual(body["total"], 1)
        self.assertEqual(body["devices"][0]["device_id"], device_id)

        status, body = self.call(f"/v1/devices/{device_id}")
        self.assertEqual(status, 200)
        self.assertEqual(body["device"]["display_name"], "Classroom iPad")

        status, body = self.call(
            f"/v1/devices/{device_id}",
            method="PATCH",
            body={"display_name": "Front iPad", "device_profile": "read_only"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(body["device"]["display_name"], "Front iPad")
        self.assertEqual(body["device"]["device_profile"], "read_only")

        status, body = self.call(
            f"/v1/devices/{device_id}", method="PATCH", body={"trust_level": "limited"}
        )
        self.assertEqual(status, 200)
        self.assertEqual(body["device"]["trust_level"], "limited")

        status, body = self.call(f"/v1/devices/{device_id}/disable", method="POST", body={})
        self.assertEqual(status, 200)
        self.assertEqual(body["device"]["status"], "disabled")
        status, body = self.call(f"/v1/devices/{device_id}/enable", method="POST", body={})
        self.assertEqual(status, 200)
        self.assertEqual(body["device"]["status"], "active")
        status, body = self.call(f"/v1/devices/{device_id}/revoke", method="POST", body={})
        self.assertEqual(status, 200)
        self.assertEqual(body["device"]["status"], "revoked")
        status, body = self.call(f"/v1/devices/{device_id}", method="DELETE")
        self.assertEqual(status, 200)
        self.assertTrue(body["removed"])
        status, _ = self.call(f"/v1/devices/{device_id}")
        self.assertEqual(status, 404)

    def test_bootstrap_is_idempotent(self):
        status, body = self.call("/v1/devices/bootstrap", method="POST", body={"confirm": True})
        self.assertEqual(status, 201)
        self.assertTrue(body["created"])
        self.assertTrue(body["device"]["is_primary_owner"])
        self.assertEqual(body["device"]["device_profile"], "owner")
        first = body["device"]["device_id"]
        status, body = self.call(
            "/v1/devices/bootstrap", method="POST", body={"confirm": True, "display_name": "Mac"}
        )
        self.assertEqual(status, 200)
        self.assertFalse(body["created"])
        self.assertEqual(body["device"]["device_id"], first)
        status, _ = self.call(f"/v1/devices/{first}/revoke", method="POST", body={})
        self.assertEqual(status, 409)

    def test_bootstrap_requires_confirmation(self):
        status, body = self.call("/v1/devices/bootstrap", method="POST", body={})
        self.assertEqual(status, 400)
        self.assertEqual(body["error_kind"], "usage")

    def test_invalid_requests(self):
        status, body = self.call("/v1/devices", method="POST", body={})
        self.assertEqual(status, 400)
        status, body = self.call(
            "/v1/devices", method="POST", body={"display_name": "x", "bogus": 1}
        )
        self.assertEqual(status, 400)
        status, body = self.call("/v1/devices", method="POST", body={"display_name": "x", "device_type": "toaster"})
        self.assertEqual(status, 400)
        status, _ = self.call("/v1/devices/" + "a" * 32)
        self.assertEqual(status, 404)
        status, _ = self.call("/v1/devices/" + "a" * 32 + "/disable", method="GET")
        self.assertEqual(status, 405)

    def test_delete_active_conflicts(self):
        _, body = self.call(
            "/v1/devices", method="POST", body={"display_name": "Active", "device_profile": "school"}
        )
        status, _ = self.call(f"/v1/devices/{body['device']['device_id']}", method="DELETE")
        self.assertEqual(status, 409)

    def test_list_limit_is_clamped(self):
        status, body = self.call("/v1/devices?limit=9999")
        self.assertEqual(status, 200)
        self.assertEqual(body["limit"], 100)

    def test_device_principal_school_permissions(self):
        device, issued = self.make_device(device_profile="school")
        auth = f"Chief-Device {issued.token}"
        status, body = self.call("/v1/status", authorization=auth)
        self.assertEqual(status, 200)
        self.assertTrue(body["ok"])
        status, body = self.call("/v1/devices", authorization=auth)
        self.assertEqual(status, 403)
        self.assertEqual(body["error_kind"], "forbidden")
        status, body = self.call("/v1/tasks", authorization=auth)
        self.assertEqual(status, 403)
        status, body = self.call(
            "/v1/tasks", method="POST", authorization=auth,
            body={"kind": "capture", "title": "from school iPad"},
        )
        self.assertEqual(status, 201)

    def test_capture_only_cannot_execute(self):
        device, issued = self.make_device(device_profile="capture_only")
        _, task = self.call(
            "/v1/tasks", method="POST", body={"kind": "diagnostic", "title": "run me"}
        )
        task_id = task["task"]["id"]
        auth = f"Chief-Device {issued.token}"
        status, body = self.call(f"/v1/tasks/{task_id}/execute", method="POST", authorization=auth)
        self.assertEqual(status, 403)
        self.assertEqual(body["permission"], "tasks.execute")

    def test_revoked_token_is_rejected_without_master_fallback(self):
        device, issued = self.make_device(device_profile="personal")
        self.registry.revoke_device(device.device_id)
        status, body = self.call("/v1/status", authorization=f"Chief-Device {issued.token}")
        self.assertEqual(status, 401)
        self.assertNotEqual(body.get("ok"), True)
        # Presenting the master token under the device scheme must not work.
        status, _ = self.call(
            "/v1/status", authorization=f"Chief-Device {self.srv.token}"
        )
        self.assertEqual(status, 401)

    def test_disabled_token_is_rejected(self):
        device, issued = self.make_device(device_profile="personal")
        self.registry.disable_device(device.device_id)
        status, _ = self.call("/v1/status", authorization=f"Chief-Device {issued.token}")
        self.assertEqual(status, 401)

    def test_keychain_outage_is_503_not_master_fallback(self):
        device, issued = self.make_device(device_profile="personal")
        self.srv.stop()
        self.srv = self.start_server(credential_provider=FailingProvider())
        status, body = self.call("/v1/status", authorization=f"Chief-Device {issued.token}")
        self.assertEqual(status, 503)
        self.assertEqual(body["error_kind"], "unavailable")
        # The master-token path still works.
        status, _ = self.call("/v1/status")
        self.assertEqual(status, 200)

    def test_device_registry_outage_does_not_break_local_daemon(self):
        self.srv.stop()
        with mock.patch.object(
            cosd_server.DeviceRegistry, "open", side_effect=RuntimeError("migration failed")
        ):
            self.srv = self.start_server()
        status, body = self.call("/v1/devices")
        self.assertEqual(status, 503)
        self.assertEqual(body["error_kind"], "unavailable")
        status, _ = self.call("/v1/status")
        self.assertEqual(status, 200)
        status, _ = self.call("/v1/tasks")
        self.assertEqual(status, 200)


if __name__ == "__main__":
    unittest.main()
