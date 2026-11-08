"""Reusable enrollment-client foundation for future device clients.

The private key stays in the client's secure store; only the public key is sent.
Production macOS uses the Keychain-backed store. Tests use a memory store and
fake envelope cipher.
"""

from __future__ import annotations

import base64
import hashlib
import json
import secrets
from dataclasses import dataclass
from typing import Any, Callable, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from ..credentials import CredentialProviderError, KeychainCredentialProvider
from .crypto import (
    CryptoError,
    EnvelopeCipher,
    generate_x25519_identity,
    public_key_fingerprint,
)

KEYCHAIN_SERVICE = "com.chiefofstaff.enrollment.device"
CREDENTIAL_ACCOUNT = "device_access_credential"
PROTOCOL_VERSION = 1


class EnrollmentClientError(Exception):
    def __init__(self, message: str, *, kind: str = "internal", status: int = 0):
        super().__init__(message)
        self.kind = kind
        self.status = status


@dataclass(frozen=True)
class DeviceIdentity:
    private_key: bytes
    public_key: str
    fingerprint: str


def generate_device_identity() -> DeviceIdentity:
    private_key, public_key = generate_x25519_identity()
    return DeviceIdentity(
        private_key=private_key,
        public_key=public_key,
        fingerprint=public_key_fingerprint(public_key),
    )


class SecureDeviceStore(Protocol):
    def get(self, account: str = CREDENTIAL_ACCOUNT) -> str | None: ...

    def set(self, value: str, account: str = CREDENTIAL_ACCOUNT) -> None: ...

    def delete(self, account: str = CREDENTIAL_ACCOUNT) -> None: ...


class MemoryDeviceStore:
    def __init__(self) -> None:
        self._values: dict[str, str] = {}

    def get(self, account: str = CREDENTIAL_ACCOUNT) -> str | None:
        return self._values.get(account)

    def set(self, value: str, account: str = CREDENTIAL_ACCOUNT) -> None:
        self._values[account] = value

    def delete(self, account: str = CREDENTIAL_ACCOUNT) -> None:
        self._values.pop(account, None)


class KeychainDeviceStore:
    """Destination-device Keychain store (macOS). Tests inject a fake runner."""

    def __init__(self, runner: Callable[[list[str]], Any] | None = None) -> None:
        self._provider = KeychainCredentialProvider(
            service=KEYCHAIN_SERVICE, runner=runner
        )

    def get(self, account: str = CREDENTIAL_ACCOUNT) -> str | None:
        try:
            return self._provider.get_secret(account)
        except CredentialProviderError as exc:
            raise EnrollmentClientError("device secure store unavailable") from exc

    def set(self, value: str, account: str = CREDENTIAL_ACCOUNT) -> None:
        try:
            self._provider.set_secret(account, value)
        except CredentialProviderError as exc:
            raise EnrollmentClientError("device secure store unavailable") from exc

    def delete(self, account: str = CREDENTIAL_ACCOUNT) -> None:
        try:
            self._provider.delete_secret(account)
        except CredentialProviderError as exc:
            raise EnrollmentClientError("device secure store unavailable") from exc


class DeviceEnrollmentClient:
    def __init__(
        self,
        base_url: str,
        *,
        identity: DeviceIdentity,
        cipher: EnvelopeCipher,
        store: SecureDeviceStore,
        timeout_s: float = 5.0,
    ) -> None:
        parsed = urlparse(base_url)
        if parsed.scheme != "http" or parsed.hostname not in ("127.0.0.1", "localhost"):
            raise EnrollmentClientError("enrollment client is loopback-only", kind="usage")
        self.base_url = base_url.rstrip("/")
        self.identity = identity
        self.cipher = cipher
        self.store = store
        self.timeout_s = timeout_s
        self.enrollment_id: str | None = None
        self.request_token: str | None = None
        self.device_nonce: str | None = None
        self.status_value: str | None = None

    def _request(
        self,
        method: str,
        path: str,
        *,
        body: dict[str, Any] | None = None,
        authorization: str | None = None,
    ) -> dict[str, Any]:
        data = None
        headers: dict[str, str] = {}
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"
        if authorization:
            headers["Authorization"] = authorization
        request = Request(
            f"{self.base_url}{path}", data=data, method=method, headers=headers
        )
        try:
            with urlopen(request, timeout=self.timeout_s) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            raw = exc.read().decode("utf-8")
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                payload = {"ok": False, "error": raw, "error_kind": "internal"}
            raise EnrollmentClientError(
                str(payload.get("error") or "enrollment request failed"),
                kind=str(payload.get("error_kind") or "internal"),
                status=exc.code,
            ) from exc
        except (URLError, OSError) as exc:
            raise EnrollmentClientError("cosd unreachable", kind="unavailable") from exc

    def _auth(self) -> str:
        if not self.enrollment_id or not self.request_token:
            raise EnrollmentClientError("not redeemed", kind="usage")
        return f"Enrollment {self.request_token}"

    def redeem(
        self,
        *,
        enrollment_id: str,
        pairing_code: str,
        display_name: str,
        device_type: str,
        platform: str,
        app_version: str = "",
        requested_profile: str = "capture_only",
        protocol_version: int = PROTOCOL_VERSION,
    ) -> dict[str, Any]:
        nonce = base64.b64encode(secrets.token_bytes(16)).decode("ascii")
        payload = self._request(
            "POST",
            "/v1/enroll/redeem",
            body={
                "enrollment_id": enrollment_id,
                "pairing_code": pairing_code,
                "device_public_key": self.identity.public_key,
                "device_key_algorithm": "x25519",
                "device_nonce": nonce,
                "display_name": display_name,
                "device_type": device_type,
                "platform": platform,
                "app_version": app_version,
                "requested_profile": requested_profile,
                "protocol_version": protocol_version,
            },
        )
        if payload.get("ok") is not True:
            raise EnrollmentClientError(
                str(payload.get("error") or "redeem failed"),
                kind=str(payload.get("error_kind") or "internal"),
            )
        self.enrollment_id = enrollment_id
        self.request_token = str(payload.get("request_token") or "")
        self.device_nonce = nonce
        self.status_value = str((payload.get("enrollment") or {}).get("status") or "")
        return payload

    def status(self) -> dict[str, Any]:
        payload = self._request(
            "GET",
            f"/v1/enroll/status/{self.enrollment_id}",
            authorization=self._auth(),
        )
        if payload.get("ok") is not True:
            raise EnrollmentClientError(
                str(payload.get("error") or "status failed"),
                kind=str(payload.get("error_kind") or "internal"),
            )
        self.status_value = str((payload.get("enrollment") or {}).get("status") or "")
        return payload

    def complete(self) -> dict[str, Any]:
        payload = self._request(
            "POST",
            f"/v1/enroll/status/{self.enrollment_id}/complete",
            body={},
            authorization=self._auth(),
        )
        if payload.get("ok") is not True:
            raise EnrollmentClientError(
                str(payload.get("error") or "completion failed"),
                kind=str(payload.get("error_kind") or "internal"),
            )
        envelope = payload.get("envelope")
        if not isinstance(envelope, dict):
            raise EnrollmentClientError("missing delivery envelope", kind="internal")
        context = self.delivery_context()
        try:
            plaintext = self.cipher.decrypt(
                private_key=self.identity.private_key,
                envelope=envelope,
                context=context,
            )
        except CryptoError as exc:
            raise EnrollmentClientError("credential envelope could not be decrypted") from exc
        try:
            credential = json.loads(plaintext.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise EnrollmentClientError("credential payload invalid") from exc
        token = credential.get("token")
        if not isinstance(token, str) or not token:
            raise EnrollmentClientError("credential token missing")
        self.store.set(token)
        self.status_value = "COMPLETED"
        return credential

    def delivery_context(self) -> bytes:
        if not self.enrollment_id:
            raise EnrollmentClientError("not redeemed", kind="usage")
        return (
            f"chief-enroll-v1\n{self.enrollment_id}\n{self.identity.fingerprint}"
        ).encode("utf-8")

    def stored_credential(self) -> str | None:
        return self.store.get()


def test_identity(seed: bytes = b"\x01" * 32) -> DeviceIdentity:
    """Deterministic identity for hermetic tests (not for production)."""
    if len(seed) != 32:
        seed = hashlib.sha256(seed).digest()
    public = hashlib.sha256(b"public" + seed).digest()
    encoded = base64.b64encode(public).decode("ascii")
    return DeviceIdentity(
        private_key=seed,
        public_key=encoded,
        fingerprint=public_key_fingerprint(public),
    )
