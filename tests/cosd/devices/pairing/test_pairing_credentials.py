"""Credential issuance, encryption binding, replacement, and leakage tests."""
from __future__ import annotations

import json
import unittest
from datetime import datetime, timedelta, timezone

from pairing_support import PairingStateTest

from cosd.devices import (
    CredentialProviderError,
    DeviceAuthenticationError,
    DeviceError,
    DeviceRegistry,
    MemoryCredentialProvider,
)
from cosd.devices.pairing import FakeEnvelopeCipher, PairingService


class FailingProvider:
    def get_secret(self, reference):
        raise CredentialProviderError("unavailable")

    def set_secret(self, reference, secret):
        raise CredentialProviderError("unavailable")

    def delete_secret(self, reference):
        raise CredentialProviderError("unavailable")


class FailingAudit:
    def append(self, kind, **fields):
        raise OSError("audit unavailable")


class CredentialIssuanceTests(PairingStateTest):
    def approved(self, **overrides):
        invitation = self.invite(**overrides)
        identity = self.identity()
        redemption = self.redeem(invitation, identity)
        record, device, credential_meta = self.approve(invitation)
        envelope = self.complete(invitation, redemption, identity)
        credential = self.decrypt(invitation, envelope, identity)
        return invitation, identity, redemption, record, device, credential_meta, credential

    def test_credential_is_issued_only_after_approval(self):
        invitation = self.invite()
        identity = self.identity()
        self.redeem(invitation, identity)
        self.assertEqual(self.registry.list_devices()["total"], 0)
        self.approve(invitation)
        self.assertEqual(self.registry.list_devices()["total"], 1)

    def test_envelope_delivers_bound_credential(self):
        invitation, identity, _, record, device, meta, credential = self.approved()
        self.assertEqual(credential["device_id"], device["device_id"])
        self.assertEqual(credential["profile"], "school")
        self.assertEqual(credential["credential_id"], meta["credential_id"])
        principal = self.auth.authenticate_device_token(credential["token"])
        self.assertEqual(principal.device_id, device["device_id"])
        self.assertEqual(principal.profile, "school")
        self.assertEqual(
            self.pairing.get_enrollment(invitation.enrollment.enrollment_id).status,
            "COMPLETED",
        )

    def test_credential_is_not_in_sqlite_or_public_metadata(self):
        invitation, identity, _, _, device, _, credential = self.approved()
        token = credential["token"]
        secret = token.split(".", 1)[1]
        rows = self.registry.db.execute("SELECT * FROM device_credentials").fetchall()
        dumped = " ".join(str(value) for row in rows for value in tuple(row))
        self.assertNotIn(token, dumped)
        self.assertNotIn(secret, dumped)
        enrollment_row = self.registry.db.execute(
            "SELECT * FROM enrollment_requests WHERE enrollment_id = ?",
            (invitation.enrollment.enrollment_id,),
        ).fetchone()
        enrollment_dump = " ".join(str(value) for value in tuple(enrollment_row))
        self.assertNotIn(token, enrollment_dump)
        self.assertNotIn(secret, enrollment_dump)
        public = invitation.enrollment.public_dict()
        self.assertNotIn("token", json.dumps(public))
        self.assertNotIn("secret", json.dumps(public))
        self.assertNotIn("pairing_code", json.dumps(public))

    def test_audit_and_qr_never_contain_credentials(self):
        invitation, identity, _, _, _, _, credential = self.approved()
        raw = (self.state / "audit.jsonl").read_text(encoding="utf-8")
        for value in (credential["token"], credential["token"].split(".", 1)[1], invitation.pairing_code):
            self.assertNotIn(value, raw)
        self.assertNotIn("keychain_ref", raw)
        self.assertNotIn("private_key", raw)

    def test_credential_expiration_fails_closed(self):
        invitation, identity, _, _, device, _, credential = self.approved()
        past = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
        with self.registry.db.transaction() as conn:
            conn.execute(
                "UPDATE device_credentials SET expires_at = ? WHERE device_id = ?",
                (past, device["device_id"]),
            )
        with self.assertRaises(DeviceAuthenticationError):
            self.auth.authenticate_device_token(credential["token"])

    def test_revoked_device_credential_fails(self):
        _, _, _, _, device, _, credential = self.approved()
        self.registry.revoke_device(device["device_id"])
        with self.assertRaises(DeviceAuthenticationError):
            self.auth.authenticate_device_token(credential["token"])

    def test_envelope_is_bound_to_device_public_key(self):
        invitation = self.invite()
        identity = self.identity()
        self.redeem(invitation, identity)
        context_a = (
            f"chief-enroll-v1\n{invitation.enrollment.enrollment_id}\n{identity.fingerprint}"
        ).encode("utf-8")
        context_b = (
            f"chief-enroll-v1\n{invitation.enrollment.enrollment_id}\n{self.identity(b'other').fingerprint}"
        ).encode("utf-8")
        envelope = FakeEnvelopeCipher().encrypt(
            public_key=identity.public_key, plaintext=b"secret", context=context_a
        )
        self.assertEqual(
            FakeEnvelopeCipher().decrypt(
                private_key=identity.private_key, envelope=envelope, context=context_a
            ),
            b"secret",
        )
        with self.assertRaises(Exception):
            FakeEnvelopeCipher().decrypt(
                private_key=identity.private_key, envelope=envelope, context=context_b
            )

    def test_replacement_revokes_old_identity_and_preserves_history(self):
        first_invite = self.invite(display_name="Old iPad")
        identity = self.identity(b"same-key")
        first_redemption = self.redeem(first_invite, identity)
        _, first_device, _ = self.approve(first_invite)
        first_envelope = self.complete(first_invite, first_redemption, identity)
        first_credential = self.decrypt(first_invite, first_envelope, identity)

        second_invite = self.invite(display_name="New iPad")
        second_redemption = self.redeem(second_invite, identity)
        with self.assertRaises(DeviceError) as caught:
            self.approve(second_invite)
        self.assertEqual(caught.exception.http_status, 409)
        _, second_device, second_meta = self.approve(
            second_invite, replaces_device_id=first_device["device_id"]
        )
        second_envelope = self.complete(second_invite, second_redemption, identity)
        second_credential = self.decrypt(second_invite, second_envelope, identity)

        self.assertEqual(self.registry.get_device(first_device["device_id"]).status, "revoked")
        self.assertEqual(self.registry.get_device(second_device["device_id"]).status, "active")
        with self.assertRaises(DeviceAuthenticationError):
            self.auth.authenticate_device_token(first_credential["token"])
        self.assertEqual(
            self.auth.authenticate_device_token(second_credential["token"]).device_id,
            second_device["device_id"],
        )
        events = {
            event["event_type"]: event
            for event in self.registry.events_for(second_device["device_id"])
        }
        self.assertIn("device.replaced", events)
        self.assertEqual(
            events["device.replaced"]["details"]["previous_device_id"],
            first_device["device_id"],
        )
        self.assertEqual(second_meta["status"], "active")

    def test_keychain_failure_rolls_back_pairing(self):
        registry = DeviceRegistry.open(
            self.state, credential_provider=FailingProvider(), audit=self.audit
        )
        try:
            service = PairingService(registry, cipher=FakeEnvelopeCipher())
            invitation = service.create_invitation(
                display_name="No store", device_type="ipad", platform="ipados"
            )
            identity = self.identity()
            service.redeem(
                enrollment_id=invitation.enrollment.enrollment_id,
                pairing_code=invitation.pairing_code,
                device_public_key=identity.public_key,
                display_name="No store",
                device_type="ipad",
                platform="ipados",
            )
            with self.assertRaises(DeviceError) as caught:
                service.approve(
                    invitation.enrollment.enrollment_id,
                    device_profile="school",
                    confirm=True,
                )
            self.assertEqual(caught.exception.http_status, 503)
            self.assertEqual(registry.list_devices()["total"], 0)
            self.assertEqual(
                registry.db.execute(
                    "SELECT COUNT(*) AS c FROM device_credentials"
                ).fetchone()["c"],
                0,
            )
        finally:
            registry.close()

    def test_audit_failure_rolls_back_pairing_request(self):
        registry = DeviceRegistry.open(
            self.state,
            credential_provider=MemoryCredentialProvider(),
            audit=FailingAudit(),
        )
        try:
            service = PairingService(registry, cipher=FakeEnvelopeCipher())
            with self.assertRaises(DeviceError) as caught:
                service.create_invitation(
                    display_name="No audit", device_type="ipad", platform="ipados"
                )
            self.assertEqual(caught.exception.http_status, 503)
            self.assertEqual(
                registry.db.execute(
                    "SELECT COUNT(*) AS c FROM enrollment_requests"
                ).fetchone()["c"],
                0,
            )
        finally:
            registry.close()


if __name__ == "__main__":
    unittest.main()
