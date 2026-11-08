"""Security properties: replay, escalation, binding, and no master-token leakage."""
from __future__ import annotations

import json
import unittest

from pairing_support import PairingStateTest, http_json_auth

from cosd.auth import ensure_token
from cosd.devices import DeviceError
from cosd.devices.pairing import DeviceEnrollmentClient, FakeEnvelopeCipher, MemoryDeviceStore
from cosd.devices.pairing.client import test_identity
from cosd.server import validate_bind_host


class PairingSecurityTests(PairingStateTest):
    def test_master_token_is_never_in_invitation_or_credential(self):
        invitation = self.invite()
        identity = self.identity()
        redemption = self.redeem(invitation, identity)
        self.approve(invitation)
        envelope = self.complete(invitation, redemption, identity)
        credential = self.decrypt(invitation, envelope, identity)
        master = ensure_token(self.state).token
        self.assertNotIn(master, json.dumps(invitation.public_dict()))
        self.assertNotIn(master, json.dumps(credential))
        rows = self.registry.db.execute("SELECT * FROM device_credentials").fetchall()
        self.assertNotIn(master, " ".join(str(v) for row in rows for v in tuple(row)))

    def test_qr_contains_no_permanent_credential(self):
        invitation = self.invite()
        text = invitation.qr_payload.lower()
        for forbidden in ("token", "secret", "credential", "private", "keychain"):
            self.assertNotIn(forbidden, text)
        self.assertIn(invitation.enrollment.enrollment_id, text)

    def test_private_key_is_never_sent_to_server(self):
        identity = self.identity(b"private-check")
        invitation = self.invite()
        self.redeem(invitation, identity)
        row = self.registry.db.execute(
            "SELECT device_public_key, device_nonce FROM enrollment_requests WHERE enrollment_id = ?",
            (invitation.enrollment.enrollment_id,),
        ).fetchone()
        self.assertIn(identity.public_key, row["device_public_key"])
        self.assertNotIn(identity.private_key.decode("latin-1"), str(tuple(row)))

    def test_profile_escalation_is_owner_controlled(self):
        invitation = self.invite(requested_profile="owner")
        self.redeem(invitation)
        with self.assertRaises(DeviceError):
            self.approve(invitation, profile="owner")
        record, device, _ = self.approve(invitation, profile="school")
        self.assertEqual(record.requested_profile, "owner")
        self.assertEqual(device["device_profile"], "school")

    def test_remote_network_enrollment_is_not_enabled(self):
        with self.assertRaises(ValueError):
            validate_bind_host("0.0.0.0")
        with self.assertRaises(ValueError):
            validate_bind_host("100.64.0.10")
        with self.assertRaises(Exception):
            DeviceEnrollmentClient(
                "https://example.invalid",
                identity=test_identity(),
                cipher=FakeEnvelopeCipher(),
                store=MemoryDeviceStore(),
            )

    def test_replayed_code_after_completion_is_denied(self):
        invitation = self.invite()
        identity = self.identity()
        redemption = self.redeem(invitation, identity)
        self.approve(invitation)
        self.complete(invitation, redemption, identity)
        with self.assertRaises(DeviceError) as caught:
            self.redeem(invitation, identity)
        self.assertIn(caught.exception.http_status, (409, 410))

    def test_status_requires_the_enrollment_request_token(self):
        invitation = self.invite()
        self.redeem(invitation)
        with self.assertRaises(DeviceError) as caught:
            self.pairing.status(invitation.enrollment.enrollment_id, "wrong-token")
        self.assertEqual(caught.exception.http_status, 401)

    def test_device_token_cannot_approve_or_manage(self):
        _, issued = self.make_device(device_profile="school")
        self.srv = self.start_pairing_server()
        try:
            invitation = self.invite()
            status, body = http_json_auth(
                self.srv.port,
                f"/v1/devices/pending/{invitation.enrollment.enrollment_id}/approve",
                method="POST",
                body={"device_profile": "school", "confirm": True},
                authorization=f"Chief-Device {issued.token}",
            )
            self.assertEqual(status, 403)
            self.assertEqual(body["error_kind"], "forbidden")
        finally:
            self.srv.stop()


if __name__ == "__main__":
    unittest.main()
