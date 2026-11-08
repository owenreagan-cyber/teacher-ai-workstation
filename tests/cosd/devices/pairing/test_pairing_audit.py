"""Hash-chained and device-event audit coverage for pairing."""
from __future__ import annotations

import json
import unittest

from pairing_support import PairingStateTest

from cos.audit import verify


class PairingAuditTests(PairingStateTest):
    def test_full_enrollment_lifecycle_is_audited(self):
        invitation = self.invite()
        identity = self.identity(b"audit")
        redemption = self.redeem(invitation, identity)
        _, device, _ = self.approve(invitation)
        envelope = self.complete(invitation, redemption, identity)
        credential = self.decrypt(invitation, envelope, identity)

        pending_events = {
            event["event_type"]
            for event in self.registry.events_for(
                f"pairing:{invitation.enrollment.enrollment_id}"
            )
        }
        device_events = {
            event["event_type"] for event in self.registry.events_for(device["device_id"])
        }
        for kind in ("pairing.requested", "pairing.code_generated", "pairing.redeemed"):
            self.assertIn(kind, pending_events)
        for kind in ("pairing.approved", "device.credential_issued", "pairing.completed", "device.enrolled"):
            self.assertIn(kind, device_events)

        result = verify(self.state / "audit.jsonl")
        self.assertEqual(result.status, "ok", result.message)
        raw = (self.state / "audit.jsonl").read_text(encoding="utf-8")
        for secret in (
            invitation.pairing_code,
            identity.private_key.decode("latin-1"),
            credential["token"],
            credential["token"].split(".", 1)[1],
        ):
            self.assertNotIn(secret, raw)
        self.assertNotIn("keychain_ref", raw)
        self.assertNotIn("verifier", raw)
        records = [json.loads(line) for line in raw.splitlines() if line.strip()]
        kinds = {record["kind"] for record in records}
        self.assertIn("pairing.code_generated", kinds)
        self.assertIn("device.enrolled", kinds)
        for record in records:
            if record["kind"].startswith("pairing."):
                self.assertIn("enrollment_id", record.get("details", {}))

    def test_rejection_cancellation_expiry_and_replay_are_audited(self):
        rejected = self.invite(display_name="Reject")
        self.redeem(rejected)
        self.pairing.reject(rejected.enrollment.enrollment_id, confirm=True)

        cancelled = self.invite(display_name="Cancel")
        self.pairing.cancel(cancelled.enrollment.enrollment_id, confirm=True)

        expired = self.invite(display_name="Expire")
        self.advance(601)
        with self.assertRaises(Exception):
            self.redeem(expired)

        replay = self.invite(display_name="Replay")
        identity = self.identity(b"replay-audit")
        self.redeem(replay, identity)
        with self.assertRaises(Exception):
            self.redeem(replay, identity)

        pending = self.invite(display_name="Fail")
        with self.assertRaises(Exception):
            self.redeem(pending, pairing_code="AAAA-AAAA-AAAA")

        kinds = {
            record["kind"]
            for record in (
                json.loads(line)
                for line in (self.state / "audit.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            )
        }
        for expected in (
            "pairing.rejected",
            "pairing.cancelled",
            "pairing.expired",
            "pairing.replay_denied",
            "device.enrollment_failed",
        ):
            self.assertIn(expected, kinds)
        self.assertEqual(verify(self.state / "audit.jsonl").status, "ok")

    def test_removed_device_keeps_pairing_provenance(self):
        invitation = self.invite(display_name="Removed")
        identity = self.identity(b"removed")
        redemption = self.redeem(invitation, identity)
        _, device, _ = self.approve(invitation)
        self.complete(invitation, redemption, identity)
        self.registry.revoke_device(device["device_id"])
        self.registry.remove_device(device["device_id"])
        events = self.registry.events_for(device["device_id"])
        kinds = {event["event_type"] for event in events}
        self.assertIn("pairing.approved", kinds)
        self.assertIn("device.enrolled", kinds)
        raw = (self.state / "audit.jsonl").read_text(encoding="utf-8")
        self.assertIn(device["device_id"], raw)
        self.assertIn(invitation.enrollment.enrollment_id, raw)


if __name__ == "__main__":
    unittest.main()
