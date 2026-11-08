"""Authenticated loopback pairing API tests."""
from __future__ import annotations

import json
import unittest

from pairing_support import PairingStateTest, http_json_auth

from cosd.devices.pairing.client import test_identity


class PairingApiTests(PairingStateTest):
    def setUp(self):
        super().setUp()
        self.srv = self.start_pairing_server()

    def tearDown(self):
        self.srv.stop()
        super().tearDown()

    def call(self, path, *, method="GET", body=None, authorization=None):
        return http_json_auth(
            self.srv.port,
            path,
            method=method,
            body=body,
            authorization=authorization if authorization is not None else f"Bearer {self.srv.token}",
        )

    def create_invitation(self, **overrides):
        body = {
            "display_name": "School iPad",
            "device_type": "ipad",
            "platform": "ipados",
            "requested_profile": "school",
        }
        body.update(overrides)
        status, response = self.call("/v1/enroll/request", method="POST", body=body)
        self.assertEqual(status, 201, response)
        return response

    def test_owner_authentication_is_required(self):
        status, _ = self.call("/v1/enroll/request", method="POST", body={}, authorization="")
        self.assertEqual(status, 401)
        status, _ = self.call("/v1/devices/pending", authorization="")
        self.assertEqual(status, 401)

    def test_school_device_cannot_manage_enrollment(self):
        _, issued = self.make_device(device_profile="school")
        auth = f"Chief-Device {issued.token}"
        status, body = self.call("/v1/devices/pending", authorization=auth)
        self.assertEqual(status, 403)
        self.assertEqual(body["error_kind"], "forbidden")
        status, _ = self.call(
            "/v1/enroll/request",
            method="POST",
            body={"display_name": "Nope", "requested_profile": "school"},
            authorization=auth,
        )
        self.assertEqual(status, 403)

    def test_full_enrollment_flow(self):
        invitation = self.create_invitation()
        enrollment_id = invitation["enrollment"]["enrollment_id"]
        identity = test_identity(b"api-flow")
        status, redemption = self.call(
            "/v1/enroll/redeem",
            method="POST",
            body={
                "enrollment_id": enrollment_id,
                "pairing_code": invitation["pairing_code"],
                "device_public_key": identity.public_key,
                "device_key_algorithm": "x25519",
                "device_nonce": "YWJjZGVmZ2hpamtsbW5vcA==",
                "display_name": "School iPad",
                "device_type": "ipad",
                "platform": "ipados",
                "requested_profile": "school",
                "protocol_version": 1,
            },
        )
        self.assertEqual(status, 200, redemption)
        request_token = redemption["request_token"]
        self.assertNotIn("pairing_code", json.dumps(redemption["enrollment"]))

        status, pending = self.call("/v1/devices/pending")
        self.assertEqual(status, 200)
        self.assertEqual(pending["total"], 1)

        status, approved = self.call(
            f"/v1/devices/pending/{enrollment_id}/approve",
            method="POST",
            body={"device_profile": "school", "confirm": True},
        )
        self.assertEqual(status, 200, approved)
        self.assertEqual(approved["enrollment"]["status"], "APPROVED")
        self.assertEqual(approved["device"]["device_profile"], "school")
        self.assertNotIn("token", json.dumps(approved.get("credential", {})))

        status, status_body = self.call(
            f"/v1/enroll/status/{enrollment_id}",
            authorization=f"Enrollment {request_token}",
        )
        self.assertEqual(status, 200)
        self.assertEqual(status_body["enrollment"]["status"], "APPROVED")

        status, completed = self.call(
            f"/v1/enroll/status/{enrollment_id}/complete",
            method="POST",
            body={},
            authorization=f"Enrollment {request_token}",
        )
        self.assertEqual(status, 200, completed)
        envelope = completed["envelope"]
        ctx = (
            f"chief-enroll-v1\n{enrollment_id}\n{identity.fingerprint}"
        ).encode("utf-8")
        credential = json.loads(
            self.cipher.decrypt(
                private_key=identity.private_key, envelope=envelope, context=ctx
            )
        )
        self.assertEqual(credential["device_id"], approved["device"]["device_id"])
        self.assertEqual(
            self.auth.authenticate_device_token(credential["token"]).profile, "school"
        )

        status, replay = self.call(
            f"/v1/enroll/status/{enrollment_id}/complete",
            method="POST",
            body={},
            authorization=f"Enrollment {request_token}",
        )
        self.assertEqual(status, 409)

    def test_status_requires_enrollment_token_not_master(self):
        invitation = self.create_invitation()
        enrollment_id = invitation["enrollment"]["enrollment_id"]
        identity = test_identity(b"token-check")
        _, redemption = self.call(
            "/v1/enroll/redeem",
            method="POST",
            body={
                "enrollment_id": enrollment_id,
                "pairing_code": invitation["pairing_code"],
                "device_public_key": identity.public_key,
                "display_name": "School iPad",
                "device_type": "ipad",
                "platform": "ipados",
            },
        )
        status, _ = self.call(f"/v1/enroll/status/{enrollment_id}")
        self.assertEqual(status, 401)
        status, _ = self.call(
            f"/v1/enroll/status/{enrollment_id}",
            authorization=f"Bearer {self.srv.token}",
        )
        self.assertEqual(status, 401)
        status, _ = self.call(
            f"/v1/enroll/status/{enrollment_id}",
            authorization="Enrollment wrong-token",
        )
        self.assertEqual(status, 401)
        status, _ = self.call(
            f"/v1/enroll/status/{enrollment_id}",
            authorization=f"Enrollment {redemption['request_token']}",
        )
        self.assertEqual(status, 200)

    def test_redeem_replay_and_invalid_code(self):
        invitation = self.create_invitation()
        body = {
            "enrollment_id": invitation["enrollment"]["enrollment_id"],
            "pairing_code": invitation["pairing_code"],
            "device_public_key": test_identity(b"replay").public_key,
            "display_name": "School iPad",
            "device_type": "ipad",
            "platform": "ipados",
        }
        status, _ = self.call("/v1/enroll/redeem", method="POST", body=body)
        self.assertEqual(status, 200)
        status, response = self.call("/v1/enroll/redeem", method="POST", body=body)
        self.assertEqual(status, 409)
        self.assertEqual(response["error_kind"], "conflict")

        second = self.create_invitation(display_name="Other")
        body["pairing_code"] = "AAAA-AAAA-AAAA"
        body["enrollment_id"] = second["enrollment"]["enrollment_id"]
        status, response = self.call("/v1/enroll/redeem", method="POST", body=body)
        self.assertEqual(status, 401)
        self.assertEqual(response["error_kind"], "auth")

    def test_approval_validation(self):
        invitation = self.create_invitation()
        enrollment_id = invitation["enrollment"]["enrollment_id"]
        identity = test_identity(b"validation")
        self.call(
            "/v1/enroll/redeem",
            method="POST",
            body={
                "enrollment_id": enrollment_id,
                "pairing_code": invitation["pairing_code"],
                "device_public_key": identity.public_key,
                "display_name": "School iPad",
                "device_type": "ipad",
                "platform": "ipados",
            },
        )
        status, _ = self.call(
            f"/v1/devices/pending/{enrollment_id}/approve",
            method="POST",
            body={"device_profile": "school"},
        )
        self.assertEqual(status, 400)
        status, _ = self.call(
            f"/v1/devices/pending/{enrollment_id}/approve",
            method="POST",
            body={"confirm": True},
        )
        self.assertEqual(status, 400)
        status, response = self.call(
            f"/v1/devices/pending/{enrollment_id}/approve",
            method="POST",
            body={"device_profile": "owner", "confirm": True},
        )
        self.assertEqual(status, 409)
        status, response = self.call(
            f"/v1/devices/pending/{enrollment_id}/approve",
            method="POST",
            body={"device_profile": "school", "confirm": True},
        )
        self.assertEqual(status, 200)
        status, _ = self.call(
            f"/v1/devices/pending/{enrollment_id}/approve",
            method="POST",
            body={"device_profile": "school", "confirm": True},
        )
        self.assertEqual(status, 409)

    def test_reject_and_cancel_require_owner(self):
        invitation = self.create_invitation()
        enrollment_id = invitation["enrollment"]["enrollment_id"]
        status, _ = self.call(
            f"/v1/devices/pending/{enrollment_id}/reject",
            method="POST",
            body={"confirm": True},
            authorization="",
        )
        self.assertEqual(status, 401)
        status, response = self.call(
            f"/v1/devices/pending/{enrollment_id}/reject",
            method="POST",
            body={"confirm": True, "reason": "no"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(response["enrollment"]["status"], "REJECTED")

        second = self.create_invitation(display_name="Cancel me")
        status, response = self.call(
            f"/v1/devices/pending/{second['enrollment']['enrollment_id']}/cancel",
            method="POST",
            body={"confirm": True},
        )
        self.assertEqual(status, 200)
        self.assertEqual(response["enrollment"]["status"], "CANCELLED")

    def test_responses_never_include_secret_material(self):
        invitation = self.create_invitation()
        text = json.dumps(invitation)
        for forbidden in ("keychain_ref", "token", "secret", "private_key", "verifier"):
            self.assertNotIn(forbidden, text)
        self.assertNotIn(self.srv.token, text)
        self.assertNotIn("device_nonce", text)


if __name__ == "__main__":
    unittest.main()
