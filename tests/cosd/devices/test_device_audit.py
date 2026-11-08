"""Hash-chained audit integration and provenance tests."""
from __future__ import annotations

import json
import unittest

from device_support import DeviceStateTest

from cos.audit import verify
from cosd.devices.credentials import CredentialInvalid


class AuditTests(DeviceStateTest):
    def test_every_lifecycle_event_is_recorded_and_chain_is_valid(self):
        device, issued = self.make_device(display_name="Audit iPad")
        tokens = [issued.token]
        self.registry.rename_device(device.device_id, "Audit iPad 2")
        self.registry.update_metadata(device.device_id, {"tag": "audit"})
        self.registry.change_profile(device.device_id, "read_only")
        self.registry.disable_device(device.device_id)
        self.registry.enable_device(device.device_id)
        rotated = self.registry.rotate_credential(device.device_id)
        tokens.append("")
        self.registry.revoke_credential(device.device_id)

        # Re-issue is impossible after revoke; use a second device for auth events.
        device2, issued2 = self.make_device(display_name="Auth iPad")
        tokens.append(issued2.token)
        principal = self.auth.authenticate_device_token(issued2.token)
        with self.assertRaises(Exception):
            self.auth.authorize(principal, "tasks.execute")
        try:
            self.auth.authenticate_device_token("a" * 32 + ".nope")
        except Exception:
            pass
        self.registry.revoke_device(device2.device_id)
        self.registry.remove_device(device2.device_id)

        kinds = {event["event_type"] for event in self.registry.events_for(device.device_id)}
        for expected in (
            "device.registered", "device.renamed", "device.metadata_changed",
            "device.profile_changed", "device.disabled", "device.re_enabled",
            "device.credential_rotated", "device.credential_revoked",
        ):
            self.assertIn(expected, kinds)
        kinds2 = {event["event_type"] for event in self.registry.events_for(device2.device_id)}
        for expected in ("device.auth_ok", "authorization.denied", "device.revoked", "device.removed"):
            self.assertIn(expected, kinds2)

        result = verify(self.audit_path)
        self.assertEqual(result.status, "ok", result.message)
        self.assertGreater(result.records, 0)

        raw = self.audit_path.read_text(encoding="utf-8")
        for token in tokens:
            if token:
                self.assertNotIn(token, raw)
                self.assertNotIn(token.split(".", 1)[-1], raw)
        self.assertNotIn("verifier", raw)
        self.assertNotIn("keychain_ref", raw)

        records = [json.loads(line) for line in raw.splitlines() if line.strip()]
        audited_kinds = {rec["kind"] for rec in records}
        self.assertIn("device.registered", audited_kinds)
        self.assertIn("device.auth_ok", audited_kinds)
        self.assertIn("device.auth_failed", audited_kinds)
        self.assertIn("authorization.denied", audited_kinds)

    def test_removed_device_remains_attributable_in_audit(self):
        device, _ = self.make_device(display_name="Removed iPad")
        self.registry.disable_device(device.device_id)
        self.registry.remove_device(device.device_id)
        records = [json.loads(line) for line in self.audit_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        removed = [r for r in records if r["kind"] == "device.removed"]
        self.assertEqual(len(removed), 1)
        self.assertEqual(removed[0]["device_id"], device.device_id)
        self.assertIn("Removed iPad", str(removed[0]))
        self.assertTrue(self.registry.events_for(device.device_id))

    def test_audit_failure_rolls_back_security_change(self):
        class FailingAudit:
            def append(self, kind, **fields):
                raise OSError("audit disk full")

        from cosd.devices import DeviceRegistry, MemoryCredentialProvider

        registry = DeviceRegistry.open(
            self.state, credential_provider=MemoryCredentialProvider(), audit=FailingAudit()
        )
        try:
            with self.assertRaises(Exception) as caught:
                registry.register_device(display_name="No audit", device_type="ipad", platform="ipados")
            self.assertEqual(getattr(caught.exception, "kind", ""), "unavailable")
            self.assertEqual(registry.list_devices()["total"], 0)
        finally:
            registry.close()


if __name__ == "__main__":
    unittest.main()
