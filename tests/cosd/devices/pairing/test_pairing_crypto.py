"""Authenticated envelope contract tests (real X25519/AES-GCM when available)."""
from __future__ import annotations

import json
import unittest

from cosd.devices.pairing import PairingService
from cosd.devices.pairing.client import generate_device_identity
from cosd.devices.pairing.crypto import (
    CryptoError,
    FakeEnvelopeCipher,
    X25519AesGcmEnvelope,
    generate_x25519_identity,
    public_key_fingerprint,
)
from pairing_support import PairingStateTest

try:
    import cryptography  # noqa: F401

    HAVE_CRYPTO = True
except ImportError:  # pragma: no cover - dependency path
    HAVE_CRYPTO = False


class EnvelopeTests(unittest.TestCase):
    def test_fake_cipher_round_trip_and_context_binding(self):
        cipher = FakeEnvelopeCipher()
        context = b"context-a"
        envelope = cipher.encrypt(public_key="unused", plaintext=b"payload", context=context)
        self.assertEqual(
            cipher.decrypt(private_key=b"unused", envelope=envelope, context=context),
            b"payload",
        )
        with self.assertRaises(CryptoError):
            cipher.decrypt(private_key=b"unused", envelope=envelope, context=b"context-b")

    @unittest.skipUnless(HAVE_CRYPTO, "cryptography package unavailable")
    def test_x25519_aes_gcm_round_trip(self):
        private_key, public_key = generate_x25519_identity()
        cipher = X25519AesGcmEnvelope()
        context = b"chief-enroll-v1\ntest\nfingerprint"
        envelope = cipher.encrypt(
            public_key=public_key, plaintext=b"credential-token", context=context
        )
        self.assertEqual(envelope["alg"], cipher.algorithm)
        self.assertEqual(
            cipher.decrypt(private_key=private_key, envelope=envelope, context=context),
            b"credential-token",
        )
        with self.assertRaises(CryptoError):
            cipher.decrypt(
                private_key=private_key, envelope=envelope, context=b"different-context"
            )

    @unittest.skipUnless(HAVE_CRYPTO, "cryptography package unavailable")
    def test_wrong_private_key_cannot_decrypt(self):
        private_key, public_key = generate_x25519_identity()
        other_private, _ = generate_x25519_identity()
        cipher = X25519AesGcmEnvelope()
        context = b"context"
        envelope = cipher.encrypt(public_key=public_key, plaintext=b"secret", context=context)
        with self.assertRaises(CryptoError):
            cipher.decrypt(private_key=other_private, envelope=envelope, context=context)

    def test_fingerprint_is_stable_and_one_way(self):
        raw = b"\x02" * 32
        first = public_key_fingerprint(raw)
        second = public_key_fingerprint(raw)
        self.assertEqual(first, second)
        self.assertEqual(len(first), 64)
        self.assertNotIn(raw.hex(), first)


@unittest.skipUnless(HAVE_CRYPTO, "cryptography package unavailable")
class RealPairingEnvelopeTests(PairingStateTest):
    def test_full_service_flow_with_real_envelope(self):
        cipher = X25519AesGcmEnvelope()
        self.pairing = PairingService(
            self.registry, cipher=cipher, clock=lambda: self.now
        )
        invitation = self.invite(display_name="Real iPad")
        identity = generate_device_identity()
        redemption = self.redeem(invitation, identity)
        _, device, _ = self.approve(invitation)
        envelope = self.complete(invitation, redemption, identity)
        context = (
            f"chief-enroll-v1\n{invitation.enrollment.enrollment_id}\n{identity.fingerprint}"
        ).encode("utf-8")
        credential = json.loads(
            cipher.decrypt(
                private_key=identity.private_key, envelope=envelope, context=context
            )
        )
        self.assertEqual(credential["device_id"], device["device_id"])
        self.assertEqual(
            self.auth.authenticate_device_token(credential["token"]).device_id,
            device["device_id"],
        )


if __name__ == "__main__":
    unittest.main()
