"""Credential lifecycle: opaque device tokens, Keychain references, rotation.

Raw secrets never enter SQLite. The database stores only a credential id, a
Keychain reference, a salted one-way verifier, and lifecycle timestamps. The
production macOS provider stores the secret itself in the login Keychain via
the ``security`` command. Tests inject a fake provider.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
import secrets
import sqlite3
import subprocess
import sys
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Protocol

from .models import (
    CREDENTIAL_TYPES,
    DeviceError,
    new_credential_id,
    utc_now,
    validate_credential_id,
)

LOG = logging.getLogger("cosd.devices.credentials")

KEYCHAIN_SERVICE = "com.chiefofstaff.cosd.device"
KEYCHAIN_TIMEOUT_S = 10


class CredentialProviderError(Exception):
    """The protected credential store is unavailable or refused an operation."""


class CredentialInvalid(Exception):
    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


class CredentialProvider(Protocol):
    def get_secret(self, reference: str) -> str | None: ...

    def set_secret(self, reference: str, secret: str) -> None: ...

    def delete_secret(self, reference: str) -> None: ...


class MemoryCredentialProvider:
    """Ephemeral provider for tests and non-macOS development only."""

    def __init__(self) -> None:
        self._values: dict[str, str] = {}
        self._lock = threading.Lock()

    def get_secret(self, reference: str) -> str | None:
        with self._lock:
            return self._values.get(reference)

    def set_secret(self, reference: str, secret: str) -> None:
        with self._lock:
            self._values[reference] = secret

    def delete_secret(self, reference: str) -> None:
        with self._lock:
            self._values.pop(reference, None)

    def count(self) -> int:
        with self._lock:
            return len(self._values)


class KeychainCredentialProvider:
    """macOS login Keychain through the ``security`` CLI (no shell, no plaintext)."""

    def __init__(
        self,
        service: str = KEYCHAIN_SERVICE,
        *,
        runner: Callable[[list[str]], Any] | None = None,
    ) -> None:
        self.service = service
        self._runner = runner or _default_security_runner

    def _run(self, args: list[str]) -> Any:
        try:
            return self._runner(["security", *args])
        except (OSError, subprocess.SubprocessError) as exc:  # pragma: no cover - platform path
            raise CredentialProviderError("keychain command failed") from exc

    @staticmethod
    def _not_found(result: Any) -> bool:
        rc = int(getattr(result, "returncode", 1))
        if rc == 44:  # errSecItemNotFound
            return True
        text = f"{getattr(result, 'stderr', '') or ''} {getattr(result, 'stdout', '') or ''}".lower()
        return "could not be found" in text or "item not found" in text

    def get_secret(self, reference: str) -> str | None:
        result = self._run(
            ["find-generic-password", "-s", self.service, "-a", reference, "-w"]
        )
        if int(getattr(result, "returncode", 1)) == 0:
            value = str(getattr(result, "stdout", "") or "").rstrip("\n")
            return value or None
        if self._not_found(result):
            return None
        raise CredentialProviderError("keychain read failed")

    def set_secret(self, reference: str, secret: str) -> None:
        result = self._run(
            [
                "add-generic-password",
                "-U",
                "-s",
                self.service,
                "-a",
                reference,
                "-w",
                secret,
            ]
        )
        if int(getattr(result, "returncode", 1)) != 0:
            raise CredentialProviderError("keychain write failed")

    def delete_secret(self, reference: str) -> None:
        result = self._run(
            ["delete-generic-password", "-s", self.service, "-a", reference]
        )
        if int(getattr(result, "returncode", 1)) == 0 or self._not_found(result):
            return
        raise CredentialProviderError("keychain delete failed")


def _default_security_runner(args: list[str]) -> Any:  # pragma: no cover - platform path
    return subprocess.run(
        args,
        capture_output=True,
        text=True,
        timeout=KEYCHAIN_TIMEOUT_S,
        check=False,
    )


def default_credential_provider() -> CredentialProvider:
    """The provider used by a real daemon.

    macOS uses the login Keychain. Tests set ``COSD_CREDENTIAL_PROVIDER=memory``.
    Non-macOS hosts use an ephemeral provider because the production target is
    macOS; this is documented and never substitutes plaintext persistence.
    """
    choice = (os.environ.get("COSD_CREDENTIAL_PROVIDER") or "").strip().lower()
    if choice == "memory":
        return MemoryCredentialProvider()
    if sys.platform == "darwin":
        return KeychainCredentialProvider()
    LOG.warning(
        "Keychain is unavailable on %s; using an ephemeral in-memory credential provider "
        "for this non-production host",
        sys.platform,
    )
    return MemoryCredentialProvider()


def _verifier(secret: str, salt: str) -> str:
    return hashlib.sha256((salt + secret).encode("utf-8")).hexdigest()


def _parse_expiry(value: str | None) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise DeviceError("expires_at must be an ISO 8601 timestamp or null")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise DeviceError("expires_at must be an ISO 8601 timestamp") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).isoformat(timespec="milliseconds")


def _expired(expires_at: str | None) -> bool:
    if not expires_at:
        return False
    try:
        parsed = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
    except ValueError:
        return True  # unparseable expiry fails closed
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) >= parsed


@dataclass(frozen=True)
class IssuedCredential:
    credential_id: str
    device_id: str
    credential_type: str
    token: str
    keychain_ref: str
    created_at: str
    expires_at: str | None

    def public_dict(self) -> dict[str, Any]:
        return {
            "credential_id": self.credential_id,
            "device_id": self.device_id,
            "credential_type": self.credential_type,
            "status": "active",
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "rotated_at": None,
            "revoked_at": None,
        }


@dataclass(frozen=True)
class CredentialVerification:
    credential_id: str
    device_id: str
    credential_type: str
    expires_at: str | None


EventRecorder = Callable[..., None]


class CredentialService:
    def __init__(
        self,
        db: Any,
        provider: CredentialProvider,
        *,
        record_event: EventRecorder | None = None,
    ) -> None:
        self._db = db
        self._provider = provider
        self._record_event = record_event

    @property
    def provider(self) -> CredentialProvider:
        return self._provider

    def _event(self, conn: sqlite3.Connection | None, kind: str, **fields: Any) -> None:
        if self._record_event is not None:
            self._record_event(conn, kind, **fields)

    def _insert(
        self,
        conn: sqlite3.Connection,
        *,
        credential_id: str,
        device_id: str,
        credential_type: str,
        keychain_ref: str,
        verifier: str,
        salt: str,
        created_at: str,
        expires_at: str | None,
    ) -> None:
        conn.execute(
            """INSERT INTO device_credentials(
                credential_id, device_id, credential_type, keychain_ref, verifier,
                verifier_salt, status, created_at, expires_at, rotated_at, revoked_at
            ) VALUES (?, ?, ?, ?, ?, ?, 'active', ?, ?, NULL, NULL)""",
            (
                credential_id,
                device_id,
                credential_type,
                keychain_ref,
                verifier,
                salt,
                created_at,
                expires_at,
            ),
        )

    def issue(
        self,
        device_id: str,
        *,
        credential_type: str = "device_access",
        expires_at: str | None = None,
        actor: str = "local_owner",
        conn: sqlite3.Connection | None = None,
    ) -> IssuedCredential:
        if credential_type not in CREDENTIAL_TYPES:
            raise DeviceError("unsupported credential_type")
        expires = _parse_expiry(expires_at)
        credential_id = new_credential_id()
        salt = secrets.token_hex(16)
        secret = secrets.token_urlsafe(32)
        token = f"{credential_id}.{secret}"
        keychain_ref = f"device:{credential_id}"
        verifier = _verifier(secret, salt)
        created_at = utc_now()

        # Refuse a second active credential for one device. Rotation marks the
        # old row rotated inside the same transaction, then issues the new one.
        active = self._db.query_one(
            "SELECT credential_id FROM device_credentials WHERE device_id = ? AND status = 'active'",
            (device_id,),
        )
        if active is not None:
            raise DeviceError(
                "device already has an active credential; rotate or revoke it first",
                kind="conflict",
                http_status=409,
            )

        try:
            self._provider.set_secret(keychain_ref, secret)
        except CredentialProviderError as exc:
            raise DeviceError("credential store unavailable", kind="unavailable", http_status=503) from exc

        try:
            if conn is not None:
                self._insert(
                    conn,
                    credential_id=credential_id,
                    device_id=device_id,
                    credential_type=credential_type,
                    keychain_ref=keychain_ref,
                    verifier=verifier,
                    salt=salt,
                    created_at=created_at,
                    expires_at=expires,
                )
                self._event(
                    conn,
                    "device.credential_created",
                    device_id=device_id,
                    credential_id=credential_id,
                    actor=actor,
                    result="ok",
                    details={"credential_type": credential_type, "expires_at": expires},
                )
            else:
                with self._db.transaction() as own:
                    self._insert(
                        own,
                        credential_id=credential_id,
                        device_id=device_id,
                        credential_type=credential_type,
                        keychain_ref=keychain_ref,
                        verifier=verifier,
                        salt=salt,
                        created_at=created_at,
                        expires_at=expires,
                    )
                    self._event(
                        own,
                        "device.credential_created",
                        device_id=device_id,
                        credential_id=credential_id,
                        actor=actor,
                        result="ok",
                        details={"credential_type": credential_type, "expires_at": expires},
                    )
        except Exception:
            try:
                self._provider.delete_secret(keychain_ref)
            except Exception:  # noqa: BLE001 - best effort cleanup
                pass
            raise

        return IssuedCredential(
            credential_id=credential_id,
            device_id=device_id,
            credential_type=credential_type,
            token=token,
            keychain_ref=keychain_ref,
            created_at=created_at,
            expires_at=expires,
        )

    def rotate(self, credential_id: str, *, actor: str = "local_owner") -> IssuedCredential:
        credential_id = validate_credential_id(credential_id)
        row = self._db.query_one(
            "SELECT * FROM device_credentials WHERE credential_id = ?", (credential_id,)
        )
        if row is None:
            raise DeviceError("credential not found", kind="not_found", http_status=404)
        if row["status"] != "active":
            raise DeviceError(
                f"credential is {row['status']}, not active",
                kind="conflict",
                http_status=409,
            )
        device_id = row["device_id"]
        new_id = new_credential_id()
        salt = secrets.token_hex(16)
        secret = secrets.token_urlsafe(32)
        token = f"{new_id}.{secret}"
        keychain_ref = f"device:{new_id}"
        verifier = _verifier(secret, salt)
        created_at = utc_now()

        try:
            self._provider.set_secret(keychain_ref, secret)
        except CredentialProviderError as exc:
            raise DeviceError("credential store unavailable", kind="unavailable", http_status=503) from exc

        try:
            with self._db.transaction() as conn:
                updated = conn.execute(
                    "UPDATE device_credentials SET status = 'rotated', rotated_at = ? "
                    "WHERE credential_id = ? AND status = 'active'",
                    (created_at, credential_id),
                )
                if updated.rowcount != 1:
                    raise DeviceError(
                        "credential is no longer active", kind="conflict", http_status=409
                    )
                self._insert(
                    conn,
                    credential_id=new_id,
                    device_id=device_id,
                    credential_type=row["credential_type"],
                    keychain_ref=keychain_ref,
                    verifier=verifier,
                    salt=salt,
                    created_at=created_at,
                    expires_at=row["expires_at"],
                )
                self._event(
                    conn,
                    "device.credential_rotated",
                    device_id=device_id,
                    credential_id=new_id,
                    actor=actor,
                    result="ok",
                    details={"previous_credential_id": credential_id},
                )
        except Exception:
            try:
                self._provider.delete_secret(keychain_ref)
            except Exception:  # noqa: BLE001
                pass
            raise

        # The old secret is useless once the row is rotated; remove it if able.
        try:
            self._provider.delete_secret(row["keychain_ref"])
        except Exception:  # noqa: BLE001 - status already blocks it
            LOG.warning("could not delete rotated credential secret from store")

        return IssuedCredential(
            credential_id=new_id,
            device_id=device_id,
            credential_type=row["credential_type"],
            token=token,
            keychain_ref=keychain_ref,
            created_at=created_at,
            expires_at=row["expires_at"],
        )

    def revoke(
        self,
        credential_id: str,
        *,
        actor: str = "local_owner",
        reason: str = "",
    ) -> dict[str, Any]:
        credential_id = validate_credential_id(credential_id)
        now = utc_now()
        with self._db.transaction() as conn:
            row = conn.execute(
                "SELECT * FROM device_credentials WHERE credential_id = ?", (credential_id,)
            ).fetchone()
            if row is None:
                raise DeviceError("credential not found", kind="not_found", http_status=404)
            if row["status"] == "revoked":
                return self._metadata(row)
            conn.execute(
                "UPDATE device_credentials SET status = 'revoked', revoked_at = ? "
                "WHERE credential_id = ?",
                (now, credential_id),
            )
            self._event(
                conn,
                "device.credential_revoked",
                device_id=row["device_id"],
                credential_id=credential_id,
                actor=actor,
                result="ok",
                details={"reason": reason} if reason else {},
            )
            updated = conn.execute(
                "SELECT * FROM device_credentials WHERE credential_id = ?", (credential_id,)
            ).fetchone()
        try:
            self._provider.delete_secret(row["keychain_ref"])
        except Exception:  # noqa: BLE001 - DB status already blocks authentication
            LOG.warning("could not delete revoked credential secret from store")
        return self._metadata(updated)

    def revoke_all_for_device(
        self,
        device_id: str,
        *,
        actor: str = "local_owner",
        reason: str = "",
        conn: sqlite3.Connection | None = None,
    ) -> list[str]:
        """Revoke every active credential. Returns Keychain refs to delete."""
        now = utc_now()
        refs: list[str] = []

        def _apply(c: sqlite3.Connection) -> None:
            rows = c.execute(
                "SELECT * FROM device_credentials WHERE device_id = ? AND status = 'active'",
                (device_id,),
            ).fetchall()
            for row in rows:
                c.execute(
                    "UPDATE device_credentials SET status = 'revoked', revoked_at = ? "
                    "WHERE credential_id = ?",
                    (now, row["credential_id"]),
                )
                refs.append(row["keychain_ref"])
                self._event(
                    c,
                    "device.credential_revoked",
                    device_id=device_id,
                    credential_id=row["credential_id"],
                    actor=actor,
                    result="ok",
                    details={"reason": reason} if reason else {},
                )

        if conn is not None:
            _apply(conn)
        else:
            with self._db.transaction() as own:
                _apply(own)
            for ref in refs:
                try:
                    self._provider.delete_secret(ref)
                except Exception:  # noqa: BLE001
                    LOG.warning("could not delete revoked credential secret from store")
        return refs

    def delete_secrets(self, refs: list[str]) -> None:
        for ref in refs:
            try:
                self._provider.delete_secret(ref)
            except Exception:  # noqa: BLE001
                LOG.warning("could not delete credential secret from store")

    def verify_token(self, token: str) -> CredentialVerification:
        if not isinstance(token, str) or "." not in token:
            raise CredentialInvalid("malformed")
        credential_id, secret = token.split(".", 1)
        if not secret or not _valid_hex(credential_id):
            raise CredentialInvalid("malformed")
        row = self._db.query_one(
            "SELECT * FROM device_credentials WHERE credential_id = ?", (credential_id,)
        )
        if row is None:
            raise CredentialInvalid("unknown")
        if row["status"] != "active":
            raise CredentialInvalid(f"status_{row['status']}")
        if _expired(row["expires_at"]):
            raise CredentialInvalid("expired")
        try:
            stored = self._provider.get_secret(row["keychain_ref"])
        except CredentialProviderError as exc:
            raise CredentialProviderError("credential store unavailable") from exc
        if not stored or not hmac.compare_digest(secret, stored):
            raise CredentialInvalid("mismatch")
        if not hmac.compare_digest(_verifier(secret, row["verifier_salt"]), row["verifier"]):
            raise CredentialInvalid("verifier_mismatch")
        return CredentialVerification(
            credential_id=row["credential_id"],
            device_id=row["device_id"],
            credential_type=row["credential_type"],
            expires_at=row["expires_at"],
        )

    def active_for_device(self, credential_id: str, device_id: str) -> bool:
        row = self._db.query_one(
            "SELECT status, expires_at FROM device_credentials "
            "WHERE credential_id = ? AND device_id = ?",
            (credential_id, device_id),
        )
        return bool(row and row["status"] == "active" and not _expired(row["expires_at"]))

    def list_for_device(self, device_id: str) -> list[dict[str, Any]]:
        rows = self._db.query_all(
            "SELECT * FROM device_credentials WHERE device_id = ? ORDER BY created_at DESC",
            (device_id,),
        )
        return [self._metadata(row) for row in rows]

    @staticmethod
    def _metadata(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "credential_id": row["credential_id"],
            "device_id": row["device_id"],
            "credential_type": row["credential_type"],
            "status": row["status"],
            "created_at": row["created_at"],
            "expires_at": row["expires_at"],
            "rotated_at": row["rotated_at"],
            "revoked_at": row["revoked_at"],
        }


def _valid_hex(value: str) -> bool:
    if len(value) != 32:
        return False
    return all(ch in "0123456789abcdef" for ch in value)
