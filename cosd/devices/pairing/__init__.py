"""Secure device pairing and enrollment foundation (P1b.4c).

Local-only in this phase: requests, code redemption, owner approval, credential
issuance, and an authenticated delivery envelope contract. No remote listener,
Tailscale, TLS gateway, or remote credential delivery is enabled.
"""

from .client import (
    DeviceEnrollmentClient,
    DeviceIdentity,
    EnrollmentClientError,
    KeychainDeviceStore,
    MemoryDeviceStore,
    SecureDeviceStore,
    generate_device_identity,
)
from .crypto import (
    CryptoError,
    EnvelopeCipher,
    FakeEnvelopeCipher,
    UnavailableEnvelopeCipher,
    X25519AesGcmEnvelope,
    default_envelope_cipher,
    public_key_fingerprint,
)
from .models import EnrollmentInvitation, EnrollmentRecord, EnrollmentRedemption
from .service import PairingService

__all__ = [
    "CryptoError",
    "DeviceEnrollmentClient",
    "DeviceIdentity",
    "EnrollmentClientError",
    "EnrollmentInvitation",
    "EnrollmentRecord",
    "EnrollmentRedemption",
    "EnvelopeCipher",
    "FakeEnvelopeCipher",
    "KeychainDeviceStore",
    "MemoryDeviceStore",
    "PairingService",
    "SecureDeviceStore",
    "UnavailableEnvelopeCipher",
    "X25519AesGcmEnvelope",
    "default_envelope_cipher",
    "generate_device_identity",
    "public_key_fingerprint",
]
