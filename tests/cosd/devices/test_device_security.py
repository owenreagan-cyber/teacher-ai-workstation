"""Security failure tests: revoked, disabled, expired, escalated, unavailable."""
from __future__ import annotations

import sqlite3
import unittest
from datetime import datetime, timedelta, timezone
from unittest import mock

from device_support import DeviceStateTest

from cosd.devices import (
    AuthorizationDenied,
    CredentialProviderError,
    DeviceAuthenticationError,
    DeviceError,
    DeviceRegistry,
    MemoryCredentialProvider,
)
from cosd.devices.credentials import CredentialInvalid
from cosd.devices.models import PrimaryDeviceProtected
from cosd.devices.storage import DeviceDatabase


class SecurityTests(DeviceStateTest):
    def test_stolen_credential_after_revocation(self):
        device, issued = self.make_device(device_profile="personal")
        self.registry.revoke_device(device.device_id)
        with self.assertRaises(DeviceAuthenticationError):
            self.auth.authenticate_device_token(issued.token)

    def test_disabled_device_with_valid_credential(self):
        device, issued = self.make_device(device_profile="personal")
        self.registry.disable_device(device.device_id)
        with self.assertRaises(DeviceAuthenticationError) as caught:
            self.auth.authenticate_device_token(issued.token)
        self.assertEqual(caught.exception.reason, "device_disabled")

    def test_expired_credential(self):
        past = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
        _, issued = self.make_device(device_profile="personal", credential_expires_at=past)
        with self.assertRaises(DeviceAuthenticationError) as caught:
            self.auth.authenticate_device_token(issued.token)
        self.assertEqual(caught.exception.reason, "expired")

    def test_rotated_credential_reuse(self):
        device, issued = self.make_device(device_profile="personal")
        self.registry.rotate_credential(device.device_id)
        with self.assertRaises(DeviceAuthenticationError) as caught:
            self.auth.authenticate_device_token(issued.token)
        self.assertEqual(caught.exception.reason, "status_rotated")

    def test_revoked_credential_reuse(self):
        device, issued = self.make_device(device_profile="personal")
        self.registry.revoke_credential(device.device_id)
        with self.assertRaises(DeviceAuthenticationError) as caught:
            self.auth.authenticate_device_token(issued.token)
        self.assertEqual(caught.exception.reason, "status_revoked")

    def test_cross_profile_escalation_attempts(self):
        for profile in ("school", "partner", "read_only", "capture_only"):
            device, issued = self.make_device(
                display_name=f"{profile} device", device_profile=profile
            )
            principal = self.auth.authenticate_device_token(issued.token)
            with self.assertRaises(AuthorizationDenied):
                self.auth.authorize(principal, "devices.manage")
            with self.assertRaises(AuthorizationDenied):
                self.auth.authorize(principal, "credentials.manage")

    def test_school_device_requesting_personal_history(self):
        device, issued = self.make_device(device_profile="school")
        principal = self.auth.authenticate_device_token(issued.token)
        for permission in ("history.read", "sessions.read", "sessions.create"):
            with self.assertRaises(AuthorizationDenied):
                self.auth.authorize(principal, permission)

    def test_partner_device_requesting_device_administration(self):
        device, issued = self.make_device(device_profile="partner")
        principal = self.auth.authenticate_device_token(issued.token)
        with self.assertRaises(AuthorizationDenied):
            self.auth.authorize(principal, "devices.manage")

    def test_capture_only_device_requesting_execution(self):
        device, issued = self.make_device(device_profile="capture_only")
        principal = self.auth.authenticate_device_token(issued.token)
        with self.assertRaises(AuthorizationDenied) as caught:
            self.auth.authorize(principal, "tasks.execute")
        self.assertEqual(caught.exception.reason, "profile_does_not_grant")

    def test_attempt_to_remove_primary_owner(self):
        device, _, _ = self.registry.bootstrap_primary_mac(confirm=True)
        with self.assertRaises(PrimaryDeviceProtected):
            self.registry.remove_device(device.device_id)
        self.assertTrue(self.registry.get_device(device.device_id).is_primary_owner)

    def test_ambiguous_device_identity_fails_closed(self):
        from cosd.devices.authorization import Principal

        weird = Principal(
            kind="device", device_id=None, profile="owner",
            permissions=frozenset({"devices.manage"}),
        )
        with self.assertRaises(AuthorizationDenied) as caught:
            self.auth.authorize(weird, "devices.manage")
        self.assertEqual(caught.exception.reason, "ambiguous_identity")

    def test_device_database_unavailable(self):
        with mock.patch.object(
            DeviceDatabase, "_connect", side_effect=sqlite3.OperationalError("disk unavailable")
        ):
            with self.assertRaises(sqlite3.OperationalError):
                DeviceRegistry.open(
                    self.state, credential_provider=MemoryCredentialProvider(), audit=None
                )

    def test_keychain_unavailable_is_not_a_master_fallback(self):
        device, issued = self.make_device(device_profile="personal")

        class Down:
            def get_secret(self, reference):
                raise CredentialProviderError("down")

            def set_secret(self, reference, secret):
                raise CredentialProviderError("down")

            def delete_secret(self, reference):
                raise CredentialProviderError("down")

        original = self.registry.credentials._provider
        self.registry.credentials._provider = Down()
        try:
            with self.assertRaises(DeviceAuthenticationError) as caught:
                self.auth.authenticate_device_token(issued.token)
            self.assertTrue(caught.exception.unavailable)
        finally:
            self.registry.credentials._provider = original

    def test_device_operations_do_not_change_master_token(self):
        from cosd.auth import ensure_token

        before = ensure_token(self.state).token
        device, _ = self.make_device()
        self.registry.rename_device(device.device_id, "Renamed")
        self.registry.disable_device(device.device_id)
        self.registry.revoke_device(device.device_id)
        after = ensure_token(self.state).token
        self.assertEqual(before, after)

    def test_school_device_cannot_be_changed_into_personal_by_itself(self):
        # The registry profile change is an owner-admin operation, not a device
        # operation. A school principal can never call it.
        device, issued = self.make_device(device_profile="school")
        principal = self.auth.authenticate_device_token(issued.token)
        with self.assertRaises(AuthorizationDenied):
            self.auth.authorize(principal, "devices.manage")
        self.assertEqual(self.registry.get_device(device.device_id).device_profile, "school")


if __name__ == "__main__":
    unittest.main()
