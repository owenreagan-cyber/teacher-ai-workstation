"""Lifecycle transitions, primary-owner protection, and removal provenance."""
from __future__ import annotations

import unittest

from device_support import DeviceStateTest

from cosd.devices import DeviceError
from cosd.devices.credentials import CredentialInvalid
from cosd.devices.models import PrimaryDeviceProtected
from cosd.devices.registry import RECOVERY_PHRASE


class LifecycleTests(DeviceStateTest):
    def test_disable_enable_revoke(self):
        device, issued = self.make_device()
        disabled = self.registry.disable_device(device.device_id)
        self.assertEqual(disabled.status, "disabled")
        enabled = self.registry.enable_device(device.device_id)
        self.assertEqual(enabled.status, "active")
        revoked = self.registry.revoke_device(device.device_id)
        self.assertEqual(revoked.status, "revoked")
        self.assertIsNotNone(revoked.revoked_at)
        with self.assertRaises(CredentialInvalid):
            self.registry.credentials.verify_token(issued.token)

    def test_revoked_cannot_be_enabled(self):
        device, _ = self.make_device()
        self.registry.revoke_device(device.device_id)
        with self.assertRaises(DeviceError) as caught:
            self.registry.enable_device(device.device_id)
        self.assertEqual(caught.exception.kind, "conflict")

    def test_active_device_cannot_be_removed(self):
        device, _ = self.make_device()
        with self.assertRaises(DeviceError) as caught:
            self.registry.remove_device(device.device_id)
        self.assertEqual(caught.exception.kind, "conflict")

    def test_remove_disabled_device(self):
        device, _ = self.make_device()
        self.registry.disable_device(device.device_id)
        result = self.registry.remove_device(device.device_id)
        self.assertTrue(result["removed"])
        with self.assertRaises(DeviceError):
            self.registry.get_device(device.device_id)
        self.assertEqual(
            self.registry.db.execute(
                "SELECT COUNT(*) AS c FROM device_credentials WHERE device_id = ?",
                (device.device_id,),
            ).fetchone()["c"],
            0,
        )

    def test_primary_owner_is_protected(self):
        device, _, _ = self.registry.bootstrap_primary_mac(confirm=True)
        for operation in (
            lambda: self.registry.disable_device(device.device_id),
            lambda: self.registry.revoke_device(device.device_id),
            lambda: self.registry.remove_device(device.device_id),
            lambda: self.registry.change_profile(device.device_id, "personal"),
        ):
            with self.assertRaises(PrimaryDeviceProtected):
                operation()

    def test_primary_recovery_requires_exact_phrase(self):
        device, _, _ = self.registry.bootstrap_primary_mac(confirm=True)
        with self.assertRaises(DeviceError):
            self.registry.release_primary_protection(
                device.device_id, confirm_phrase="please"
            )
        recovered = self.registry.release_primary_protection(
            device.device_id, confirm_phrase=RECOVERY_PHRASE
        )
        self.assertFalse(recovered.is_primary_owner)
        self.registry.disable_device(device.device_id)
        self.registry.revoke_device(device.device_id)
        self.registry.remove_device(device.device_id)
        with self.assertRaises(DeviceError):
            self.registry.get_device(device.device_id)
        events = self.registry.events_for(device.device_id)
        kinds = {event["event_type"] for event in events}
        self.assertIn("device.primary_recovery", kinds)
        self.assertIn("device.removed", kinds)

    def test_audit_provenance_survives_removal(self):
        device, _ = self.make_device(display_name="Cart iPad")
        self.registry.disable_device(device.device_id)
        self.registry.remove_device(device.device_id)
        events = self.registry.events_for(device.device_id)
        self.assertTrue(events)
        self.assertEqual(events[0]["display_name"], "Cart iPad")
        kinds = {event["event_type"] for event in events}
        self.assertIn("device.registered", kinds)
        self.assertIn("device.removed", kinds)
        raw = (self.state / "audit.jsonl").read_text(encoding="utf-8")
        self.assertIn(device.device_id, raw)
        self.assertIn("device.removed", raw)

    def test_idempotent_disable_and_revoke(self):
        device, _ = self.make_device()
        self.registry.disable_device(device.device_id)
        self.assertEqual(self.registry.disable_device(device.device_id).status, "disabled")
        self.registry.revoke_device(device.device_id)
        self.assertEqual(self.registry.revoke_device(device.device_id).status, "revoked")


if __name__ == "__main__":
    unittest.main()
