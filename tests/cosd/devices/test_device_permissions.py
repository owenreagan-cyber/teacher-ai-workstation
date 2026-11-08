"""Permission matrix and central authorization tests."""
from __future__ import annotations

import unittest

from device_support import DeviceStateTest

from cosd.devices import (
    AuthorizationDenied,
    DeviceAuthenticationError,
    LOCAL_OWNER_PRINCIPAL,
)
from cosd.devices.permissions import PERMISSIONS, has_permission, permissions_for

EXPECTED = {
    "owner": set(PERMISSIONS),
    "personal": {
        "ask", "status.read", "tasks.read", "tasks.create", "tasks.edit",
        "tasks.cancel", "tasks.retry", "tasks.execute", "history.read",
        "sessions.read", "sessions.create",
    },
    "partner": {"ask", "status.read", "tasks.read", "tasks.create"},
    "school": {"ask", "status.read", "tasks.create"},
    "read_only": {"status.read", "tasks.read", "history.read"},
    "capture_only": {"status.read", "tasks.create"},
    "revoked": set(),
}


class MatrixTests(unittest.TestCase):
    def test_every_profile_and_permission(self):
        for profile, expected in EXPECTED.items():
            self.assertEqual(set(permissions_for(profile)), expected, profile)
            for permission in PERMISSIONS:
                self.assertEqual(
                    has_permission(profile, permission),
                    permission in expected,
                    f"{profile} / {permission}",
                )

    def test_unknown_profile_and_permission_fail_closed(self):
        self.assertEqual(permissions_for("superuser"), frozenset())
        self.assertFalse(has_permission("owner", "root.everything"))

    def test_least_privilege(self):
        for profile in ("personal", "partner", "school", "read_only", "capture_only", "revoked"):
            for permission in ("devices.read", "devices.manage", "credentials.manage", "runtime.manage"):
                self.assertFalse(has_permission(profile, permission), f"{profile}/{permission}")

    def test_school_boundaries(self):
        for permission in (
            "tasks.read", "tasks.execute", "history.read", "sessions.read",
            "sessions.create", "runtime.manage", "devices.read", "devices.manage",
        ):
            self.assertFalse(has_permission("school", permission), permission)
        self.assertTrue(has_permission("school", "tasks.create"))

    def test_partner_has_no_private_history(self):
        for permission in ("history.read", "sessions.read", "sessions.create", "tasks.execute"):
            self.assertFalse(has_permission("partner", permission), permission)

    def test_capture_only_cannot_execute_or_ask(self):
        self.assertFalse(has_permission("capture_only", "tasks.execute"))
        self.assertFalse(has_permission("capture_only", "ask"))
        self.assertFalse(has_permission("capture_only", "tasks.read"))
        self.assertTrue(has_permission("capture_only", "tasks.create"))

    def test_read_only_cannot_mutate(self):
        for permission in ("tasks.create", "tasks.edit", "tasks.cancel", "tasks.retry", "tasks.execute"):
            self.assertFalse(has_permission("read_only", permission), permission)

    def test_revoked_has_nothing(self):
        self.assertEqual(permissions_for("revoked"), frozenset())


class AuthorizationTests(DeviceStateTest):
    def principal_for(self, profile, **overrides):
        fields = {
            "display_name": f"{profile} device",
            "device_type": "ipad",
            "platform": "ipados",
            "owner_id": "test",
            "device_profile": profile,
        }
        fields.update(overrides)
        device, issued = self.make_device(**fields)
        principal = self.auth.authenticate_device_token(issued.token)
        return device, issued, principal

    def test_school_permissions_enforced(self):
        _, _, principal = self.principal_for("school")
        for permission in ("status.read", "ask", "tasks.create"):
            self.auth.authorize(principal, permission)
        for permission in ("tasks.read", "history.read", "sessions.read", "devices.manage", "tasks.execute"):
            with self.assertRaises(AuthorizationDenied):
                self.auth.authorize(principal, permission)

    def test_capture_only_cannot_execute(self):
        _, _, principal = self.principal_for("capture_only")
        self.auth.authorize(principal, "tasks.create")
        with self.assertRaises(AuthorizationDenied):
            self.auth.authorize(principal, "tasks.execute")
        with self.assertRaises(AuthorizationDenied):
            self.auth.authorize(principal, "ask")

    def test_partner_cannot_administer_devices(self):
        _, _, principal = self.principal_for("partner")
        self.auth.authorize(principal, "tasks.read")
        with self.assertRaises(AuthorizationDenied):
            self.auth.authorize(principal, "devices.read")
        with self.assertRaises(AuthorizationDenied):
            self.auth.authorize(principal, "devices.manage")

    def test_read_only_cannot_mutate(self):
        _, _, principal = self.principal_for("read_only")
        self.auth.authorize(principal, "tasks.read")
        with self.assertRaises(AuthorizationDenied):
            self.auth.authorize(principal, "tasks.create")

    def test_personal_can_execute_but_not_administer(self):
        _, _, principal = self.principal_for("personal")
        self.auth.authorize(principal, "tasks.execute")
        self.auth.authorize(principal, "sessions.read")
        with self.assertRaises(AuthorizationDenied):
            self.auth.authorize(principal, "credentials.manage")

    def test_disable_immediately_invalidates_authorization(self):
        device, issued, principal = self.principal_for("personal")
        self.auth.authorize(principal, "tasks.read")
        self.registry.disable_device(device.device_id)
        with self.assertRaises(AuthorizationDenied):
            self.auth.authorize(principal, "tasks.read")
        with self.assertRaises(DeviceAuthenticationError):
            self.auth.authenticate_device_token(issued.token)

    def test_enable_restores_same_identity(self):
        device, issued, _ = self.principal_for("personal")
        self.registry.disable_device(device.device_id)
        restored = self.registry.enable_device(device.device_id)
        self.assertEqual(restored.device_id, device.device_id)
        principal = self.auth.authenticate_device_token(issued.token)
        self.auth.authorize(principal, "tasks.read")

    def test_revocation_immediately_invalidates(self):
        device, issued, principal = self.principal_for("personal")
        self.registry.revoke_device(device.device_id)
        with self.assertRaises(AuthorizationDenied):
            self.auth.authorize(principal, "tasks.read")
        with self.assertRaises(DeviceAuthenticationError):
            self.auth.authenticate_device_token(issued.token)

    def test_unknown_permission_denied(self):
        _, _, principal = self.principal_for("owner")
        with self.assertRaises(AuthorizationDenied):
            self.auth.authorize(principal, "root.everything")

    def test_local_owner_keeps_master_behaviour(self):
        for permission in PERMISSIONS:
            self.auth.authorize(LOCAL_OWNER_PRINCIPAL, permission)
        (self.state / "STOP").write_text("stopped test\n", encoding="utf-8")
        for permission in PERMISSIONS:
            self.auth.authorize(LOCAL_OWNER_PRINCIPAL, permission)

    def test_device_kill_switch_denies_execution_but_allows_status(self):
        _, _, principal = self.principal_for("personal")
        (self.state / "STOP").write_text("stopped test\n", encoding="utf-8")
        self.auth.authorize(principal, "status.read")
        with self.assertRaises(AuthorizationDenied) as caught:
            self.auth.authorize(principal, "tasks.execute")
        self.assertEqual(caught.exception.reason, "kill_switch")


if __name__ == "__main__":
    unittest.main()
