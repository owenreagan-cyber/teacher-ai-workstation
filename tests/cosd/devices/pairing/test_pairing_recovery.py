"""Recovery: restart, expiry, unavailable stores, audit failure, re-pairing."""
from __future__ import annotations

import unittest

from pairing_support import PairingStateTest

from cosd.devices import (
    CredentialProviderError,
    DeviceError,
    DeviceRegistry,
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


class RecoveryTests(PairingStateTest):
    def reopen_pairing(self):
        self.registry.close()
        self.registry = DeviceRegistry.open(
            self.state, credential_provider=self.provider, audit=self.audit
        )
        self.pairing = PairingService(
            self.registry, cipher=FakeEnvelopeCipher(), clock=lambda: self.now
        )

    def test_interrupted_enrollment_survives_daemon_restart(self):
        invitation = self.invite(display_name="Restart iPad")
        identity = self.identity(b"restart")
        redemption = self.redeem(invitation, identity)
        self.approve(invitation)
        self.reopen_pairing()
        status = self.pairing.status(invitation.enrollment.enrollment_id, redemption.request_token)
        self.assertEqual(status.status, "APPROVED")
        envelope = self.pairing.complete(
            invitation.enrollment.enrollment_id, redemption.request_token
        )
        credential = self.decrypt(invitation, envelope, identity)
        self.assertEqual(credential["profile"], "school")

    def test_expired_code_after_restart(self):
        invitation = self.invite()
        self.reopen_pairing()
        self.advance(601)
        with self.assertRaises(DeviceError) as caught:
            self.redeem(invitation)
        self.assertEqual(caught.exception.http_status, 410)

    def test_delivery_expiry_revokes_unclaimed_device(self):
        invitation = self.invite()
        identity = self.identity(b"expiry")
        self.redeem(invitation, identity)
        _, device, _ = self.approve(invitation)
        self.advance(self.pairing.delivery_ttl_s + 1)
        record = self.pairing.get_enrollment(invitation.enrollment.enrollment_id)
        self.assertEqual(record.status, "EXPIRED")
        self.assertEqual(self.registry.get_device(device["device_id"]).status, "revoked")
        self.assertIsNone(self.provider.get_secret(f"enrollment:{invitation.enrollment.enrollment_id}"))

    def test_completion_delivery_store_unavailable(self):
        invitation = self.invite()
        identity = self.identity(b"store-down")
        redemption = self.redeem(invitation, identity)
        self.approve(invitation)
        self.pairing.provider = FailingProvider()
        with self.assertRaises(DeviceError) as caught:
            self.pairing.complete(invitation.enrollment.enrollment_id, redemption.request_token)
        self.assertEqual(caught.exception.http_status, 503)
        self.assertEqual(
            self.pairing.get_enrollment(invitation.enrollment.enrollment_id).status,
            "APPROVED",
        )

    def test_audit_failure_at_approval_rolls_back_device(self):
        invitation = self.invite()
        self.redeem(invitation)
        self.registry._audit = FailingAudit()
        with self.assertRaises(DeviceError) as caught:
            self.approve(invitation)
        self.assertEqual(caught.exception.http_status, 503)
        self.assertEqual(self.registry.list_devices()["total"], 0)
        self.assertEqual(
            self.registry.db.execute(
                "SELECT COUNT(*) AS c FROM device_credentials"
            ).fetchone()["c"],
            0,
        )

    def test_revoked_device_repair_requires_explicit_replacement(self):
        first = self.invite(display_name="First")
        identity = self.identity(b"revoked-key")
        first_redemption = self.redeem(first, identity)
        _, first_device, _ = self.approve(first)
        self.complete(first, first_redemption, identity)
        self.registry.revoke_device(first_device["device_id"])

        second = self.invite(display_name="Repaired")
        self.redeem(second, identity)
        with self.assertRaises(DeviceError) as caught:
            self.approve(second)
        self.assertEqual(caught.exception.http_status, 409)
        _, second_device, _ = self.approve(
            second, replaces_device_id=first_device["device_id"]
        )
        self.assertEqual(self.registry.get_device(second_device["device_id"]).status, "active")
        self.assertEqual(self.registry.get_device(first_device["device_id"]).status, "revoked")

    def test_cancelled_request_cannot_be_reopened(self):
        invitation = self.invite()
        self.redeem(invitation)
        self.pairing.cancel(invitation.enrollment.enrollment_id, confirm=True)
        with self.assertRaises(DeviceError) as caught:
            self.approve(invitation)
        self.assertEqual(caught.exception.http_status, 409)


if __name__ == "__main__":
    unittest.main()
