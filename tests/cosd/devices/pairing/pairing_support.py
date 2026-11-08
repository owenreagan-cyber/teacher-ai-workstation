"""Shared hermetic helpers for pairing/enrollment suites."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

_COSD_TESTS = Path(__file__).resolve().parents[2]
_DEVICE_TESTS = Path(__file__).resolve().parents[1]
for path in (_COSD_TESTS, _DEVICE_TESTS):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from device_support import DeviceStateTest, http_json_auth  # noqa: E402

from cosd.devices.pairing import (  # noqa: E402
    DeviceEnrollmentClient,
    FakeEnvelopeCipher,
    MemoryDeviceStore,
    PairingService,
)
from cosd.devices.pairing.client import test_identity  # noqa: E402


class PairingStateTest(DeviceStateTest):
    def setUp(self):
        super().setUp()
        self.cipher = FakeEnvelopeCipher()
        self.now = datetime.now(timezone.utc)
        self.pairing = PairingService(
            self.registry,
            cipher=self.cipher,
            clock=lambda: self.now,
        )

    def advance(self, seconds: int) -> None:
        self.now = self.now + timedelta(seconds=seconds)

    def invite(self, **overrides):
        fields = {
            "display_name": "Test iPad",
            "device_type": "ipad",
            "platform": "ipados",
            "requested_profile": "school",
            "owner_id": "school",
        }
        fields.update(overrides)
        return self.pairing.create_invitation(**fields)

    def identity(self, seed: bytes = b"device-test-key"):
        return test_identity(seed)

    def redeem(self, invitation, identity=None, **overrides):
        identity = identity or self.identity()
        fields = {
            "enrollment_id": invitation.enrollment.enrollment_id,
            "pairing_code": invitation.pairing_code,
            "device_public_key": identity.public_key,
            "display_name": invitation.enrollment.display_name,
            "device_type": invitation.enrollment.device_type,
            "platform": invitation.enrollment.platform,
            "requested_profile": invitation.enrollment.requested_profile,
        }
        fields.update(overrides)
        return self.pairing.redeem(**fields)

    def approve(self, invitation, profile="school", **overrides):
        fields = {"device_profile": profile, "confirm": True}
        fields.update(overrides)
        return self.pairing.approve(invitation.enrollment.enrollment_id, **fields)

    def complete(self, invitation, redemption, identity):
        return self.pairing.complete(
            invitation.enrollment.enrollment_id, redemption.request_token
        )

    def decrypt(self, invitation, envelope, identity):
        context = (
            f"chief-enroll-v1\n{invitation.enrollment.enrollment_id}\n{identity.fingerprint}"
        ).encode("utf-8")
        return json.loads(
            self.cipher.decrypt(
                private_key=identity.private_key, envelope=envelope, context=context
            )
        )

    def client(self, server, identity=None):
        identity = identity or self.identity()
        return DeviceEnrollmentClient(
            f"http://127.0.0.1:{server.port}",
            identity=identity,
            cipher=self.cipher,
            store=MemoryDeviceStore(),
        )

    def start_pairing_server(self, **kwargs):
        kwargs.setdefault("use_subprocess", False)
        kwargs.setdefault("credential_provider", self.provider)
        kwargs.setdefault("envelope_cipher", self.cipher)
        return self.start_server(**kwargs)


__all__ = ["DeviceStateTest", "PairingStateTest", "http_json_auth"]
