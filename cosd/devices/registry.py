"""Central device lifecycle and registry service."""

from __future__ import annotations

import logging
import platform as host_platform
import sqlite3
from contextlib import nullcontext
from pathlib import Path
from typing import Any, Callable

from .credentials import (
    CredentialProvider,
    CredentialService,
    IssuedCredential,
    default_credential_provider,
)
from .models import (
    DEVICE_TYPES,
    PLATFORMS,
    PROFILES,
    STATUSES,
    TRUST_BY_PROFILE,
    TRUST_LEVELS,
    DeviceError,
    DeviceRecord,
    PrimaryDeviceProtected,
    new_device_id,
    parse_metadata,
    utc_now,
    validate_app_version,
    validate_choice,
    validate_device_id,
    validate_display_name,
    validate_fingerprint,
    validate_metadata,
    validate_owner_id,
)
from .storage import DeviceDatabase

LOG = logging.getLogger("cosd.devices.registry")

RECOVERY_PHRASE = "RECOVER PRIMARY OWNER"
MAX_LIST_LIMIT = 100


class DeviceRegistry:
    """The authoritative local inventory of devices and their lifecycle state."""

    def __init__(
        self,
        db: DeviceDatabase,
        credentials: CredentialService,
        *,
        audit: Any | None = None,
    ) -> None:
        self.db = db
        self.credentials = credentials
        self._audit = audit

    @classmethod
    def open(
        cls,
        base: Path | None = None,
        *,
        credential_provider: CredentialProvider | None = None,
        audit: Any | None = None,
    ) -> "DeviceRegistry":
        db = DeviceDatabase(base)
        service = CredentialService(
            db,
            credential_provider or default_credential_provider(),
            record_event=lambda conn, kind, **fields: _record_event(
                db, audit, conn, kind, strict=True, **fields
            ),
        )
        return cls(db, service, audit=audit)

    def close(self) -> None:
        self.db.close()

    # ------------------------------------------------------------------ audit

    def _record_event(
        self,
        conn: sqlite3.Connection,
        kind: str,
        *,
        device_id: str,
        display_name: str | None = None,
        result: str = "ok",
        profile: str | None = None,
        credential_id: str | None = None,
        actor: str = "local_owner",
        details: dict[str, Any] | None = None,
    ) -> None:
        _record_event(
            self.db,
            self._audit,
            conn,
            kind,
            device_id=device_id,
            display_name=display_name,
            result=result,
            profile=profile,
            credential_id=credential_id,
            actor=actor,
            details=details,
            strict=True,
        )

    def record_auth_event(
        self,
        kind: str,
        *,
        device_id: str,
        result: str,
        reason: str = "",
        profile: str | None = None,
        credential_id: str | None = None,
    ) -> None:
        """Record a security event. Raises DeviceError if audit is unavailable."""
        with self.db.transaction() as conn:
            self._record_event(
                conn,
                kind,
                device_id=device_id,
                result=result,
                profile=profile,
                credential_id=credential_id,
                actor="device_auth",
                details={"reason": reason} if reason else {},
            )

    def record_event(
        self,
        conn: sqlite3.Connection,
        kind: str,
        *,
        device_id: str,
        display_name: str | None = None,
        result: str = "ok",
        profile: str | None = None,
        credential_id: str | None = None,
        actor: str = "local_owner",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Record a lifecycle/security event inside the caller's transaction."""
        self._record_event(
            conn,
            kind,
            device_id=device_id,
            display_name=display_name,
            result=result,
            profile=profile,
            credential_id=credential_id,
            actor=actor,
            details=details,
        )

    def find_by_fingerprint(self, fingerprint: str) -> list[DeviceRecord]:
        fingerprint = validate_fingerprint(fingerprint)
        if fingerprint is None:
            return []
        rows = self.db.execute(
            "SELECT * FROM devices WHERE public_key_fingerprint = ? "
            "ORDER BY registered_at DESC",
            (fingerprint,),
        ).fetchall()
        return [_row_to_device(row) for row in rows]

    def events_for(self, device_id: str, *, limit: int = 100) -> list[dict[str, Any]]:
        limit = max(1, min(int(limit), MAX_LIST_LIMIT))
        rows = self.db.execute(
            "SELECT * FROM device_events WHERE device_id = ? ORDER BY id DESC LIMIT ?",
            (device_id, limit),
        ).fetchall()
        return [
            {
                "device_id": r["device_id"],
                "display_name": r["display_name"],
                "event_type": r["event_type"],
                "result": r["result"],
                "profile": r["profile"],
                "credential_id": r["credential_id"],
                "actor": r["actor"],
                "details": _loads(r["details_json"]),
                "created_at": r["created_at"],
            }
            for r in rows
        ]

    # --------------------------------------------------------------- lifecycle

    def register_device(
        self,
        *,
        display_name: str,
        device_type: str = "other",
        platform: str = "unknown",
        owner_id: str = "unassigned",
        device_profile: str = "capture_only",
        trust_level: str | None = None,
        app_version: str = "",
        metadata: dict[str, Any] | None = None,
        is_primary_owner: bool = False,
        issue_credential: bool = True,
        credential_expires_at: str | None = None,
        device_id: str | None = None,
        actor: str = "local_owner",
        initial_status: str = "active",
        public_key_fingerprint: str | None = None,
        conn: sqlite3.Connection | None = None,
    ) -> tuple[DeviceRecord, IssuedCredential | None]:
        display_name = validate_display_name(display_name)
        device_type = validate_choice("device_type", device_type, DEVICE_TYPES)
        platform = validate_choice("platform", platform, PLATFORMS)
        owner_id = validate_owner_id(owner_id)
        device_profile = validate_choice("device_profile", device_profile, PROFILES)
        if device_profile == "revoked":
            raise DeviceError("use revoke to revoke a device, not the revoked profile")
        if initial_status not in ("active", "disabled"):
            raise DeviceError("initial_status must be active or disabled")
        trust = validate_choice(
            "trust_level",
            trust_level or TRUST_BY_PROFILE[device_profile],
            TRUST_LEVELS,
        )
        app_version = validate_app_version(app_version)
        meta = validate_metadata(metadata)
        fingerprint = validate_fingerprint(public_key_fingerprint)
        if device_id is not None:
            device_id = validate_device_id(device_id)
        else:
            device_id = new_device_id()

        now = utc_now()
        manager = self.db.transaction() if conn is None else nullcontext(conn)
        try:
            with manager as active_conn:
                if is_primary_owner:
                    existing = active_conn.execute(
                        "SELECT device_id FROM devices WHERE is_primary_owner = 1"
                    ).fetchone()
                    if existing is not None:
                        raise DeviceError(
                            "a primary owner device is already registered",
                            kind="conflict",
                            http_status=409,
                        )
                active_conn.execute(
                    """INSERT INTO devices(
                        device_id, display_name, device_type, platform, owner_id,
                        device_profile, trust_level, status, app_version,
                        registered_at, last_seen_at, updated_at, revoked_at,
                        metadata_json, is_primary_owner, public_key_fingerprint
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, ?, NULL, ?, ?, ?)""",
                    (
                        device_id,
                        display_name,
                        device_type,
                        platform,
                        owner_id,
                        device_profile,
                        trust,
                        initial_status,
                        app_version,
                        now,
                        now,
                        _dumps(meta),
                        1 if is_primary_owner else 0,
                        fingerprint,
                    ),
                )
                self._record_event(
                    active_conn,
                    "device.registered",
                    device_id=device_id,
                    display_name=display_name,
                    profile=device_profile,
                    actor=actor,
                    details={
                        "device_type": device_type,
                        "platform": platform,
                        "trust_level": trust,
                        "is_primary_owner": bool(is_primary_owner),
                        "initial_status": initial_status,
                    },
                )
                issued = None
                if issue_credential:
                    issued = self.credentials.issue(
                        device_id,
                        expires_at=credential_expires_at,
                        actor=actor,
                        conn=active_conn,
                    )
                row = active_conn.execute(
                    "SELECT * FROM devices WHERE device_id = ?", (device_id,)
                ).fetchone()
        except sqlite3.IntegrityError as exc:
            raise DeviceError(
                "device could not be registered (duplicate identity, public key, or constraint)",
                kind="conflict",
                http_status=409,
            ) from exc

        return _row_to_device(row), issued

    def bootstrap_primary_mac(
        self,
        *,
        confirm: bool = False,
        display_name: str = "Primary Mac",
        owner_id: str = "owen",
        app_version: str = "",
    ) -> tuple[DeviceRecord, IssuedCredential | None, bool]:
        """Register the primary Mac as the initial owner device, idempotently.

        Returns (device, issued_credential_or_none, created). ``created`` is
        False when a primary owner already exists (including a retry).
        """
        if confirm is not True:
            raise DeviceError("explicit owner confirmation is required")
        existing = self.db.execute(
            "SELECT * FROM devices WHERE is_primary_owner = 1"
        ).fetchone()
        if existing is not None:
            return _row_to_device(existing), None, False

        system = host_platform.system().lower()
        platform_id = "macos" if system == "darwin" else "unknown"
        metadata = {
            "bootstrap": "primary-mac",
            "os_release": host_platform.release(),
            "architecture": host_platform.machine(),
        }
        try:
            record, issued = self.register_device(
                display_name=display_name,
                device_type="mac",
                platform=platform_id,
                owner_id=owner_id,
                device_profile="owner",
                trust_level="owner",
                app_version=app_version,
                metadata=metadata,
                is_primary_owner=True,
                issue_credential=True,
                actor="local_owner",
            )
            return record, issued, True
        except DeviceError as exc:
            if exc.kind == "conflict":
                row = self.db.execute(
                    "SELECT * FROM devices WHERE is_primary_owner = 1"
                ).fetchone()
                if row is not None:
                    return _row_to_device(row), None, False
            raise

    def get_device(self, device_id: str) -> DeviceRecord:
        device_id = validate_device_id(device_id)
        row = self.db.execute(
            "SELECT * FROM devices WHERE device_id = ?", (device_id,)
        ).fetchone()
        if row is None:
            raise DeviceError("device not found", kind="not_found", http_status=404)
        return _row_to_device(row)

    def list_devices(
        self,
        *,
        status: str | None = None,
        profile: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        limit = max(1, min(int(limit), MAX_LIST_LIMIT))
        offset = max(0, int(offset))
        clauses = ["1=1"]
        params: list[Any] = []
        if status:
            clauses.append("status = ?")
            params.append(validate_choice("status", status, STATUSES))
        if profile:
            clauses.append("device_profile = ?")
            params.append(validate_choice("device_profile", profile, PROFILES))
        where = " AND ".join(clauses)
        total = self.db.execute(
            f"SELECT COUNT(*) AS c FROM devices WHERE {where}", params
        ).fetchone()["c"]
        rows = self.db.execute(
            f"""SELECT * FROM devices WHERE {where}
                ORDER BY is_primary_owner DESC, registered_at ASC, device_id ASC
                LIMIT ? OFFSET ?""",
            (*params, limit, offset),
        ).fetchall()
        return {
            "devices": [_row_to_device(r).public_dict() for r in rows],
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    def rename_device(self, device_id: str, display_name: str, *, actor: str = "local_owner") -> DeviceRecord:
        display_name = validate_display_name(display_name)
        device = self.get_device(device_id)
        if device.display_name == display_name:
            return device
        now = utc_now()
        with self.db.transaction() as conn:
            conn.execute(
                "UPDATE devices SET display_name = ?, updated_at = ? WHERE device_id = ?",
                (display_name, now, device.device_id),
            )
            self._record_event(
                conn,
                "device.renamed",
                device_id=device.device_id,
                display_name=display_name,
                profile=device.device_profile,
                actor=actor,
                details={"previous_display_name": device.display_name},
            )
        return self.get_device(device.device_id)

    def update_metadata(
        self,
        device_id: str,
        metadata: dict[str, Any] | None,
        *,
        app_version: str | None = None,
        actor: str = "local_owner",
    ) -> DeviceRecord:
        device = self.get_device(device_id)
        meta = validate_metadata(metadata)
        version = device.app_version if app_version is None else validate_app_version(app_version)
        now = utc_now()
        with self.db.transaction() as conn:
            conn.execute(
                "UPDATE devices SET metadata_json = ?, app_version = ?, updated_at = ? "
                "WHERE device_id = ?",
                (_dumps(meta), version, now, device.device_id),
            )
            self._record_event(
                conn,
                "device.metadata_changed",
                device_id=device.device_id,
                display_name=device.display_name,
                profile=device.device_profile,
                actor=actor,
                details={"changed_keys": sorted(meta), "app_version_changed": version != device.app_version},
            )
        return self.get_device(device.device_id)

    def change_profile(
        self,
        device_id: str,
        device_profile: str,
        *,
        trust_level: str | None = None,
        actor: str = "local_owner",
    ) -> DeviceRecord:
        device = self.get_device(device_id)
        device_profile = validate_choice("device_profile", device_profile, PROFILES)
        if device_profile == "revoked":
            raise DeviceError("use revoke to revoke a device, not the revoked profile")
        if device.is_primary_owner and device_profile != "owner":
            raise PrimaryDeviceProtected("the primary owner device must keep the owner profile")
        trust = validate_choice(
            "trust_level",
            trust_level or TRUST_BY_PROFILE[device_profile],
            TRUST_LEVELS,
        )
        if device.device_profile == device_profile and device.trust_level == trust:
            return device
        now = utc_now()
        with self.db.transaction() as conn:
            conn.execute(
                "UPDATE devices SET device_profile = ?, trust_level = ?, updated_at = ? "
                "WHERE device_id = ?",
                (device_profile, trust, now, device.device_id),
            )
            self._record_event(
                conn,
                "device.profile_changed",
                device_id=device.device_id,
                display_name=device.display_name,
                profile=device_profile,
                actor=actor,
                details={
                    "previous_profile": device.device_profile,
                    "previous_trust_level": device.trust_level,
                    "trust_level": trust,
                },
            )
        return self.get_device(device.device_id)

    def disable_device(self, device_id: str, *, actor: str = "local_owner") -> DeviceRecord:
        device = self.get_device(device_id)
        if device.is_primary_owner:
            raise PrimaryDeviceProtected()
        if device.status == "revoked":
            raise DeviceError("revoked devices cannot be disabled", kind="conflict", http_status=409)
        if device.status == "disabled":
            return device
        now = utc_now()
        with self.db.transaction() as conn:
            conn.execute(
                "UPDATE devices SET status = 'disabled', updated_at = ? WHERE device_id = ?",
                (now, device.device_id),
            )
            self._record_event(
                conn,
                "device.disabled",
                device_id=device.device_id,
                display_name=device.display_name,
                profile=device.device_profile,
                actor=actor,
            )
        return self.get_device(device.device_id)

    def enable_device(self, device_id: str, *, actor: str = "local_owner") -> DeviceRecord:
        device = self.get_device(device_id)
        if device.status == "revoked":
            raise DeviceError(
                "revoked devices cannot be re-enabled; re-register with owner approval",
                kind="conflict",
                http_status=409,
            )
        if device.status == "active":
            return device
        now = utc_now()
        with self.db.transaction() as conn:
            conn.execute(
                "UPDATE devices SET status = 'active', updated_at = ? WHERE device_id = ?",
                (now, device.device_id),
            )
            self._record_event(
                conn,
                "device.re_enabled",
                device_id=device.device_id,
                display_name=device.display_name,
                profile=device.device_profile,
                actor=actor,
            )
        return self.get_device(device.device_id)

    def revoke_device(
        self,
        device_id: str,
        *,
        actor: str = "local_owner",
        reason: str = "",
        conn: sqlite3.Connection | None = None,
    ) -> DeviceRecord:
        device = self.get_device(device_id)
        if device.is_primary_owner:
            raise PrimaryDeviceProtected()
        if device.status == "revoked":
            return device
        now = utc_now()
        manager = self.db.transaction() if conn is None else nullcontext(conn)
        refs: list[str] = []
        with manager as active_conn:
            active_conn.execute(
                "UPDATE devices SET status = 'revoked', revoked_at = ?, updated_at = ? "
                "WHERE device_id = ?",
                (now, now, device.device_id),
            )
            refs = self.credentials.revoke_all_for_device(
                device.device_id, actor=actor, reason=reason, conn=active_conn
            )
            self._record_event(
                active_conn,
                "device.revoked",
                device_id=device.device_id,
                display_name=device.display_name,
                profile=device.device_profile,
                actor=actor,
                details={"reason": reason} if reason else {},
            )
        if conn is None:
            self.credentials.delete_secrets(refs)
        return self.get_device(device.device_id)

    def remove_device(self, device_id: str, *, actor: str = "local_owner") -> dict[str, Any]:
        device = self.get_device(device_id)
        if device.is_primary_owner:
            raise PrimaryDeviceProtected()
        if device.status == "active":
            raise DeviceError(
                "disable or revoke the device before removing it",
                kind="conflict",
                http_status=409,
            )
        refs = [
            r["keychain_ref"]
            for r in self.db.execute(
                "SELECT keychain_ref FROM device_credentials WHERE device_id = ?",
                (device.device_id,),
            ).fetchall()
        ]
        with self.db.transaction() as conn:
            # The event is recorded before deletion and has no foreign key, so
            # provenance survives even though the registry row is gone.
            self._record_event(
                conn,
                "device.removed",
                device_id=device.device_id,
                display_name=device.display_name,
                profile=device.device_profile,
                actor=actor,
                details={"status": device.status},
            )
            conn.execute("DELETE FROM devices WHERE device_id = ?", (device.device_id,))
        self.credentials.delete_secrets(refs)
        return {
            "device_id": device.device_id,
            "display_name": device.display_name,
            "removed": True,
        }

    def release_primary_protection(
        self, device_id: str, *, confirm_phrase: str, actor: str = "local_owner"
    ) -> DeviceRecord:
        device = self.get_device(device_id)
        if not device.is_primary_owner:
            raise DeviceError("device is not the primary owner", kind="conflict", http_status=409)
        if confirm_phrase != RECOVERY_PHRASE:
            raise DeviceError(
                f"confirm_phrase must be exactly {RECOVERY_PHRASE!r}",
                kind="usage",
            )
        now = utc_now()
        with self.db.transaction() as conn:
            conn.execute(
                "UPDATE devices SET is_primary_owner = 0, updated_at = ? WHERE device_id = ?",
                (now, device.device_id),
            )
            self._record_event(
                conn,
                "device.primary_recovery",
                device_id=device.device_id,
                display_name=device.display_name,
                profile=device.device_profile,
                actor=actor,
                details={"confirm_phrase": RECOVERY_PHRASE},
            )
        return self.get_device(device.device_id)

    def touch_last_seen(self, device_id: str) -> None:
        try:
            with self.db.transaction() as conn:
                conn.execute(
                    "UPDATE devices SET last_seen_at = ? WHERE device_id = ?",
                    (utc_now(), device_id),
                )
        except Exception:  # noqa: BLE001 - last seen is informational
            LOG.warning("could not update last_seen_at for %s", device_id)

    # -------------------------------------------------------------- credentials

    def list_credentials(self, device_id: str) -> list[dict[str, Any]]:
        device = self.get_device(device_id)
        return self.credentials.list_for_device(device.device_id)

    def rotate_credential(
        self, device_id: str, credential_id: str | None = None, *, actor: str = "local_owner"
    ) -> dict[str, Any]:
        device = self.get_device(device_id)
        if device.status != "active":
            raise DeviceError("device is not active", kind="conflict", http_status=409)
        if credential_id is None:
            row = self.db.execute(
                "SELECT credential_id FROM device_credentials "
                "WHERE device_id = ? AND status = 'active'",
                (device.device_id,),
            ).fetchone()
            if row is None:
                raise DeviceError("no active credential to rotate", kind="not_found", http_status=404)
            credential_id = row["credential_id"]
        issued = self.credentials.rotate(credential_id, actor=actor)
        return issued.public_dict()

    def revoke_credential(
        self,
        device_id: str,
        credential_id: str | None = None,
        *,
        actor: str = "local_owner",
    ) -> dict[str, Any]:
        device = self.get_device(device_id)
        if credential_id is None:
            refs = self.credentials.revoke_all_for_device(
                device.device_id, actor=actor, reason="device credential revoked"
            )
            self.credentials.delete_secrets(refs)
            return {"device_id": device.device_id, "revoked": len(refs)}
        row = self.db.execute(
            "SELECT device_id FROM device_credentials WHERE credential_id = ?",
            (credential_id,),
        ).fetchone()
        if row is None:
            raise DeviceError("credential not found", kind="not_found", http_status=404)
        if row["device_id"] != device.device_id:
            raise DeviceError(
                "credential does not belong to this device",
                kind="conflict",
                http_status=409,
            )
        return self.credentials.revoke(credential_id, actor=actor)


def _record_event(
    db: DeviceDatabase,
    audit: Any | None,
    conn: sqlite3.Connection | None,
    kind: str,
    *,
    device_id: str,
    display_name: str | None = None,
    result: str = "ok",
    profile: str | None = None,
    credential_id: str | None = None,
    actor: str = "local_owner",
    details: dict[str, Any] | None = None,
    strict: bool = False,
) -> None:
    """Write a device event and the hash-chained audit record.

    When ``strict`` is true an audit failure raises DeviceError so a security
    change rolls back rather than happening without a trail.
    """
    if conn is not None:
        conn.execute(
            """INSERT INTO device_events(
                device_id, display_name, event_type, result, profile,
                credential_id, actor, details_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                device_id,
                display_name,
                kind,
                result,
                profile,
                credential_id,
                actor,
                _dumps(details or {}),
                utc_now(),
            ),
        )
    if audit is not None:
        fields = {
            "operation": kind,
            "device_id": device_id,
            "result": result,
            "profile": profile,
            "credential_id": credential_id,
            "actor": actor,
            **({"display_name": display_name} if display_name else {}),
            **({"details": details} if details else {}),
        }
        try:
            if callable(audit):
                audit(kind, **fields)
            else:
                audit.append(kind, **fields)
        except Exception as exc:  # noqa: BLE001 - audit failure must be visible
            LOG.error("device audit write failed for %s", kind)
            if strict:
                raise DeviceError(
                    "audit log unavailable", kind="unavailable", http_status=503
                ) from exc


def _row_to_device(row: sqlite3.Row) -> DeviceRecord:
    return DeviceRecord(
        device_id=row["device_id"],
        display_name=row["display_name"],
        device_type=row["device_type"],
        platform=row["platform"],
        owner_id=row["owner_id"],
        device_profile=row["device_profile"],
        trust_level=row["trust_level"],
        status=row["status"],
        app_version=row["app_version"],
        registered_at=row["registered_at"],
        last_seen_at=row["last_seen_at"],
        updated_at=row["updated_at"],
        revoked_at=row["revoked_at"],
        metadata=parse_metadata(row["metadata_json"]),
        is_primary_owner=bool(row["is_primary_owner"]),
        public_key_fingerprint=(
            row["public_key_fingerprint"]
            if "public_key_fingerprint" in row.keys()
            else None
        ),
    )


def _dumps(value: Any) -> str:
    import json

    return json.dumps(value, separators=(",", ":"), ensure_ascii=False, sort_keys=True)


def _loads(value: str) -> dict[str, Any]:
    import json

    try:
        parsed = json.loads(value or "{}")
    except (TypeError, ValueError):
        return {}
    return parsed if isinstance(parsed, dict) else {}
