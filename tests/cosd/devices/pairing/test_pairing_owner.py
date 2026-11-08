"""Owner approval, rejection, cancellation, profile selection, and expiry."""
from __future__ import annotations

import unittest

from pairing_support import PairingStateTest

from cosd.devices import DeviceError


class OwnerApprovalTests(PairingStateTest):
    def test_owner_approval_creates_device_and_credential(self):
        invitation = self.invite(requested_profile="school")
        identity = self.identity()
        self.redeem(invitation, identity)
        record, device, credential = self.approve(invitation, profile="school")
        self.assertEqual(record.status, "APPROVED")
        self.assertEqual(record.approved_profile, "school")
        self.assertEqual(record.approved_permissions, ("ask", "status.read", "tasks.create"))
        self.assertEqual(device["device_profile"], "school")
        self.assertEqual(device["status"], "active")
        self.assertEqual(credential["status"], "active")
        self.assertNotIn("token", credential)
        self.assertNotIn("keychain_ref", credential)
        self.assertEqual(record.device_id, device["device_id"])
        self.assertEqual(record.credential_id, credential["credential_id"])

    def test_owner_can_select_a_different_profile_than_requested(self):
        invitation = self.invite(requested_profile="school")
        self.redeem(invitation)
        record, device, _ = self.approve(invitation, profile="read_only")
        self.assertEqual(record.requested_profile, "school")
        self.assertEqual(record.approved_profile, "read_only")
        self.assertEqual(record.approved_permissions, ("history.read", "status.read", "tasks.read"))
        self.assertEqual(device["device_profile"], "read_only")

    def test_owner_profile_is_not_automatic(self):
        invitation = self.invite(requested_profile="owner")
        self.redeem(invitation)
        with self.assertRaises(DeviceError) as caught:
            self.approve(invitation, profile="owner")
        self.assertEqual(caught.exception.http_status, 409)
        record, device, _ = self.approve(invitation, profile="owner", allow_owner=True)
        self.assertEqual(device["device_profile"], "owner")
        self.assertEqual(record.approved_profile, "owner")

    def test_approval_requires_confirmation(self):
        invitation = self.invite()
        self.redeem(invitation)
        with self.assertRaises(DeviceError):
            self.pairing.approve(
                invitation.enrollment.enrollment_id, device_profile="school", confirm=False
            )

    def test_approval_before_redemption_is_rejected(self):
        invitation = self.invite()
        with self.assertRaises(DeviceError) as caught:
            self.approve(invitation)
        self.assertEqual(caught.exception.http_status, 409)

    def test_duplicate_approval_is_rejected(self):
        invitation = self.invite()
        self.redeem(invitation)
        self.approve(invitation)
        with self.assertRaises(DeviceError) as caught:
            self.approve(invitation)
        self.assertEqual(caught.exception.http_status, 409)

    def test_expired_approval_is_rejected(self):
        invitation = self.invite()
        self.redeem(invitation)
        self.advance(self.pairing.approval_ttl_s + 1)
        with self.assertRaises(DeviceError) as caught:
            self.approve(invitation)
        self.assertEqual(caught.exception.http_status, 409)
        self.assertEqual(
            self.pairing.get_enrollment(invitation.enrollment.enrollment_id).status,
            "EXPIRED",
        )

    def test_rejection_creates_no_device(self):
        invitation = self.invite()
        self.redeem(invitation)
        record = self.pairing.reject(
            invitation.enrollment.enrollment_id, reason="not mine", confirm=True
        )
        self.assertEqual(record.status, "REJECTED")
        self.assertIsNone(record.device_id)
        self.assertEqual(self.registry.list_devices()["total"], 0)
        with self.assertRaises(DeviceError):
            self.pairing.reject(invitation.enrollment.enrollment_id, confirm=True)

    def test_cancellation_of_pending_request(self):
        invitation = self.invite()
        record = self.pairing.cancel(invitation.enrollment.enrollment_id, confirm=True)
        self.assertEqual(record.status, "CANCELLED")
        with self.assertRaises(DeviceError):
            self.redeem(invitation)

    def test_cancellation_after_approval_revokes_device(self):
        invitation = self.invite()
        self.redeem(invitation)
        _, device, _ = self.approve(invitation)
        record = self.pairing.cancel(
            invitation.enrollment.enrollment_id, reason="changed mind", confirm=True
        )
        self.assertEqual(record.status, "CANCELLED")
        self.assertEqual(self.registry.get_device(device["device_id"]).status, "revoked")

    def test_pending_list_contains_requested_and_approved(self):
        pending = self.invite(display_name="Pending iPad")
        approved = self.invite(display_name="Approved iPad")
        self.redeem(approved)
        self.approve(approved)
        listing = self.pairing.list_pending()
        names = {item["display_name"] for item in listing["enrollments"]}
        self.assertIn("Pending iPad", names)
        self.assertIn("Approved iPad", names)
        self.assertEqual(listing["total"], 2)
        self.assertTrue(all("pairing_code" not in item for item in listing["enrollments"]))


if __name__ == "__main__":
    unittest.main()
