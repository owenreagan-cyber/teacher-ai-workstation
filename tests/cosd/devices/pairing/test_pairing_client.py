"""Reusable enrollment-client foundation across the six test device classes."""
from __future__ import annotations

import unittest

from pairing_support import PairingStateTest, http_json_auth

from cosd.devices.pairing import (
    CryptoError,
    DeviceEnrollmentClient,
    FakeEnvelopeCipher,
    MemoryDeviceStore,
    generate_device_identity,
)
from cosd.devices.pairing.client import test_identity

DEVICES = [
    ("personal Mac", "mac", "macos", "personal"),
    ("partner Mac", "mac", "macos", "partner"),
    ("school Mac", "mac", "macos", "school"),
    ("personal iPhone", "iphone", "ios", "personal"),
    ("personal iPad", "ipad", "ipados", "personal"),
    ("school iPad", "ipad", "ipados", "school"),
]


class ClientFoundationTests(PairingStateTest):
    def setUp(self):
        super().setUp()
        self.srv = self.start_pairing_server()

    def tearDown(self):
        self.srv.stop()
        super().tearDown()

    def owner(self, method, path, body=None):
        return http_json_auth(
            self.srv.port,
            path,
            method=method,
            body=body,
            authorization=f"Bearer {self.srv.token}",
        )

    def test_six_device_classes_complete_enrollment(self):
        for index, (label, device_type, platform, profile) in enumerate(DEVICES):
            with self.subTest(label=label):
                status, invitation = self.owner(
                    "POST",
                    "/v1/enroll/request",
                    {
                        "display_name": label,
                        "device_type": device_type,
                        "platform": platform,
                        "requested_profile": profile,
                    },
                )
                self.assertEqual(status, 201, invitation)
                enrollment_id = invitation["enrollment"]["enrollment_id"]
                identity = test_identity(f"client-{index}".encode("utf-8"))
                client = DeviceEnrollmentClient(
                    f"http://127.0.0.1:{self.srv.port}",
                    identity=identity,
                    cipher=FakeEnvelopeCipher(),
                    store=MemoryDeviceStore(),
                )
                client.redeem(
                    enrollment_id=enrollment_id,
                    pairing_code=invitation["pairing_code"],
                    display_name=label,
                    device_type=device_type,
                    platform=platform,
                    requested_profile=profile,
                )
                self.assertEqual(client.status()["enrollment"]["status"], "AWAITING_OWNER_APPROVAL")
                status, approved = self.owner(
                    "POST",
                    f"/v1/devices/pending/{enrollment_id}/approve",
                    {"device_profile": profile, "confirm": True},
                )
                self.assertEqual(status, 200, approved)
                self.assertEqual(client.status()["enrollment"]["status"], "APPROVED")
                credential = client.complete()
                self.assertEqual(credential["profile"], profile)
                self.assertEqual(credential["device_id"], approved["device"]["device_id"])
                token = client.stored_credential()
                self.assertTrue(token)
                principal = self.auth.authenticate_device_token(token)
                self.assertEqual(principal.device_id, approved["device"]["device_id"])
                self.assertEqual(principal.profile, profile)

    def test_client_refuses_non_loopback(self):
        with self.assertRaises(Exception):
            DeviceEnrollmentClient(
                "http://192.0.2.1:8765",
                identity=test_identity(),
                cipher=FakeEnvelopeCipher(),
                store=MemoryDeviceStore(),
            )

    def test_generated_identity_has_public_material(self):
        try:
            identity = generate_device_identity()
        except CryptoError:
            self.skipTest("cryptography package unavailable")
        self.assertEqual(len(identity.private_key), 32)
        self.assertTrue(identity.public_key)
        self.assertEqual(len(identity.fingerprint), 64)


if __name__ == "__main__":
    unittest.main()
