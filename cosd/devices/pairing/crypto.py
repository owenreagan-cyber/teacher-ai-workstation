"""Authenticated credential-delivery envelopes.

Production uses X25519 ECDH + HKDF-SHA256 + AES-256-GCM from the established
``cryptography`` library. The enrolling device's private key never leaves its
secure store. Tests inject ``FakeEnvelopeCipher``; it is named test-only and is
never selected by the daemon.
"""

from __future__ import annotations

import base64
import hashlib
import secrets
from typing import Any, Protocol

from ..models import DeviceError

ALGORITHM = "x25519-hkdf-sha256-aes-256-gcm"
ENVELOPE_VERSION = 1


class CryptoError(Exception):
    """The authenticated encryption implementation is unavailable."""


class EnvelopeCipher(Protocol):
    algorithm: str

    def encrypt(self, *, public_key: str, plaintext: bytes, context: bytes) -> dict[str, Any]: ...

    def decrypt(self, *, private_key: bytes, envelope: dict[str, Any], context: bytes) -> bytes: ...


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def _unb64(value: str, *, expected: int | None = None) -> bytes:
    try:
        raw = base64.b64decode(value, validate=True)
    except (ValueError, TypeError) as exc:
        raise CryptoError("invalid base64") from exc
    if expected is not None and len(raw) != expected:
        raise CryptoError(f"expected {expected} bytes")
    return raw


def public_key_fingerprint(public_key: bytes | str) -> str:
    if isinstance(public_key, str):
        public_key = _unb64(public_key, expected=32)
    if not isinstance(public_key, (bytes, bytearray)) or len(public_key) != 32:
        raise DeviceError("device public key must be 32 bytes")
    return hashlib.sha256(bytes(public_key)).hexdigest()


class X25519AesGcmEnvelope:
    algorithm = ALGORITHM

    @staticmethod
    def _modules():
        try:
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.asymmetric.x25519 import (
                X25519PrivateKey,
                X25519PublicKey,
            )
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
            from cryptography.hazmat.primitives.kdf.hkdf import HKDF
        except ImportError as exc:  # pragma: no cover - dependency path
            raise CryptoError(
                "authenticated encryption requires the cryptography package"
            ) from exc
        return X25519PrivateKey, X25519PublicKey, serialization, HKDF, hashes, AESGCM

    def _key(self, shared: bytes, context: bytes) -> bytes:
        _x, _xp, _s, HKDF, hashes, _a = self._modules()
        return HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=hashlib.sha256(context).digest(),
            info=b"chief-device-pairing-v1",
        ).derive(shared)

    def encrypt(self, *, public_key: str, plaintext: bytes, context: bytes) -> dict[str, Any]:
        X25519PrivateKey, X25519PublicKey, serialization, _h, _ha, AESGCM = self._modules()
        peer = X25519PublicKey.from_public_bytes(_unb64(public_key, expected=32))
        ephemeral = X25519PrivateKey.generate()
        shared = ephemeral.exchange(peer)
        key = self._key(shared, context)
        nonce = secrets.token_bytes(12)
        ciphertext = AESGCM(key).encrypt(nonce, plaintext, context)
        ephemeral_public = ephemeral.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        return {
            "v": ENVELOPE_VERSION,
            "alg": self.algorithm,
            "ephemeral_public_key": _b64(ephemeral_public),
            "nonce": _b64(nonce),
            "ciphertext": _b64(ciphertext),
            "context_sha256": hashlib.sha256(context).hexdigest(),
        }

    def decrypt(self, *, private_key: bytes, envelope: dict[str, Any], context: bytes) -> bytes:
        X25519PrivateKey, X25519PublicKey, _s, _h, _ha, AESGCM = self._modules()
        if not isinstance(envelope, dict):
            raise CryptoError("envelope must be an object")
        if envelope.get("v") != ENVELOPE_VERSION or envelope.get("alg") != self.algorithm:
            raise CryptoError("unsupported envelope")
        if envelope.get("context_sha256") != hashlib.sha256(context).hexdigest():
            raise CryptoError("envelope context mismatch")
        if isinstance(private_key, str):
            private_key = _unb64(private_key, expected=32)
        if not isinstance(private_key, (bytes, bytearray)) or len(private_key) != 32:
            raise CryptoError("private key must be 32 bytes")
        ephemeral = X25519PublicKey.from_public_bytes(
            _unb64(str(envelope.get("ephemeral_public_key", "")), expected=32)
        )
        shared = X25519PrivateKey.from_private_bytes(bytes(private_key)).exchange(ephemeral)
        key = self._key(shared, context)
        nonce = _unb64(str(envelope.get("nonce", "")), expected=12)
        ciphertext = _unb64(str(envelope.get("ciphertext", "")))
        try:
            return AESGCM(key).decrypt(nonce, ciphertext, context)
        except Exception as exc:  # noqa: BLE001 - cryptography raises InvalidTag
            raise CryptoError("credential envelope authentication failed") from exc


class FakeEnvelopeCipher:
    """Deterministic test-only envelope. Never selected in production."""

    algorithm = "test-only"

    def encrypt(self, *, public_key: str, plaintext: bytes, context: bytes) -> dict[str, Any]:
        return {
            "v": 0,
            "alg": self.algorithm,
            "payload": _b64(plaintext),
            "context_sha256": hashlib.sha256(context).hexdigest(),
        }

    def decrypt(self, *, private_key: bytes, envelope: dict[str, Any], context: bytes) -> bytes:
        if not isinstance(envelope, dict) or envelope.get("alg") != self.algorithm:
            raise CryptoError("unsupported test envelope")
        if envelope.get("context_sha256") != hashlib.sha256(context).hexdigest():
            raise CryptoError("envelope context mismatch")
        try:
            return _unb64(str(envelope.get("payload", "")))
        except CryptoError as exc:
            raise CryptoError("test envelope payload invalid") from exc


class UnavailableEnvelopeCipher:
    algorithm = "unavailable"

    def encrypt(self, *, public_key: str, plaintext: bytes, context: bytes) -> dict[str, Any]:
        raise CryptoError("authenticated encryption is unavailable")

    def decrypt(self, *, private_key: bytes, envelope: dict[str, Any], context: bytes) -> bytes:
        raise CryptoError("authenticated encryption is unavailable")


def default_envelope_cipher() -> EnvelopeCipher:
    try:
        import cryptography  # noqa: F401
    except ImportError:
        return UnavailableEnvelopeCipher()
    return X25519AesGcmEnvelope()


def generate_x25519_identity() -> tuple[bytes, str]:
    """(private_key_bytes, public_key_base64) for a device identity."""
    try:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
    except ImportError as exc:  # pragma: no cover - dependency path
        raise CryptoError("device identity requires the cryptography package") from exc
    private = X25519PrivateKey.generate()
    private_bytes = private.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_bytes = private.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return private_bytes, _b64(public_bytes)


def envelope_cipher_name(cipher: EnvelopeCipher) -> str:
    return getattr(cipher, "algorithm", "unknown")
