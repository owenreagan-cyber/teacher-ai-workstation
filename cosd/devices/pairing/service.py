"""Pairing request, redemption, owner approval, issuance, and delivery service."""

from __future__ import annotations

import base64
import hmac
import json
import logging
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

from ..models import (
    PROFILES,
    DeviceError,
    new_device_id,
    validate_app_version,
    validate_choice,
    validate_device_id,
    validate_display_name,
    validate_metadata,
    validate_owner_id,
)
from ..permissions import permissions_for
from ..registry import DeviceRegistry
from .codes import (
    CODE_LENGTH,
    DEFAULT_CODE_TTL_S,
    MAX_CODE_ATTEMPTS,
    MAX_CODE_TTL_S,
    generate_code_material,
    qr_payload,
    verify_pairing_code,
)
from .crypto import (
    CryptoError,
    EnvelopeCipher,
    default_envelope_cipher,
    public_key_fingerprint,
)
from .models import EnrollmentInvitation, EnrollmentRecord, EnrollmentRedemption
from .rate_limit import PairingRateLimiter
from .states import PairingState, ensure_transition

LOG = logging.getLogger("cosd.devices.pairing")

DEFAULT_APPROVAL_TTL_S = 3600
DEFAULT_DELIVERY_TTL_S = 600
MAX_DELIVERY_TTL_S = 3600
PROTOCOL_VERSION = 1
_ALLOWED_UPDATES = frozenset(
    {
        "status",
        "reason",
        "display_name",
        "device_type",
        "platform",
        "app_version",
        "owner_id",
        "requested_profile",
        "approved_profile",
        "requested_permissions_json",
        "approved_permissions_json",
        "device_public_key",
        "device_key_algorithm",
        "device_nonce",
        "public_key_fingerprint",
        "protocol_version",
        "pairing_code_hash",
        "pairing_code_salt",
        "pairing_code_expires_at",
        "request_token_hash",
        "request_token_salt",
        "failed_attempts",
        "device_id",
        "credential_id",
        "delivery_ref",
        "replaces_device_id",
        "metadata_json",
        "expires_at",
        "redeemed_at",
        "approved_at",
        "completed_at",
        "rejected_at",
        "cancelled_at",
        "delivery_expires_at",
    }
)


def _dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _stamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="milliseconds")


def _dumps(value: Any) -> str:
    return json.dumps(value, separators=(",", ":"), ensure_ascii=False, sort_keys=True)


def _loads_list(raw: str | None) -> tuple[str, ...]:
    try:
        value = json.loads(raw or "[]")
    except (TypeError, ValueError):
        return ()
    if not isinstance(value, list):
        return ()
    return tuple(item for item in value if isinstance(item, str))


def _row_to_record(row: sqlite3.Row) -> EnrollmentRecord:
    protocol_version = row["protocol_version"]
    if protocol_version is None:
        # A row with no protocol version cannot be interpreted. This used to
        # surface as a bare TypeError when a reset cursor produced a row of
        # NULLs; fail closed with a controlled error instead.
        raise DeviceError(
            "enrollment record is not usable (missing protocol version)",
            kind="conflict",
            http_status=409,
        )
    return EnrollmentRecord(
        enrollment_id=row["enrollment_id"],
        status=row["status"],
        source=row["source"],
        display_name=row["display_name"],
        device_type=row["device_type"],
        platform=row["platform"],
        app_version=row["app_version"],
        owner_id=row["owner_id"],
        requested_profile=row["requested_profile"],
        approved_profile=row["approved_profile"],
        requested_permissions=_loads_list(row["requested_permissions_json"]),
        approved_permissions=_loads_list(row["approved_permissions_json"]),
        public_key_fingerprint=row["public_key_fingerprint"],
        protocol_version=int(protocol_version),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        expires_at=row["expires_at"],
        redeemed_at=row["redeemed_at"],
        approved_at=row["approved_at"],
        completed_at=row["completed_at"],
        rejected_at=row["rejected_at"],
        cancelled_at=row["cancelled_at"],
        delivery_expires_at=row["delivery_expires_at"],
        device_id=row["device_id"],
        credential_id=row["credential_id"],
        replaces_device_id=row["replaces_device_id"],
        reason=row["reason"],
        failed_attempts=int(row["failed_attempts"]),
    )


class PairingService:
    def __init__(
        self,
        registry: DeviceRegistry,
        *,
        cipher: EnvelopeCipher | None = None,
        clock: Callable[[], datetime] | None = None,
        code_ttl_s: int = DEFAULT_CODE_TTL_S,
        approval_ttl_s: int = DEFAULT_APPROVAL_TTL_S,
        delivery_ttl_s: int = DEFAULT_DELIVERY_TTL_S,
        max_code_attempts: int = MAX_CODE_ATTEMPTS,
        invite_limit: int = 10,
        invite_window_s: int = 60,
        redeem_limit: int = 20,
        redeem_window_s: int = 3600,
    ) -> None:
        self.registry = registry
        self.db = registry.db
        self.cipher = cipher or default_envelope_cipher()
        self.provider = registry.credentials.provider
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.code_ttl_s = max(1, min(int(code_ttl_s), MAX_CODE_TTL_S))
        self.approval_ttl_s = max(self.code_ttl_s, min(int(approval_ttl_s), 86400))
        self.delivery_ttl_s = max(1, min(int(delivery_ttl_s), MAX_DELIVERY_TTL_S))
        self.max_code_attempts = max(1, int(max_code_attempts))
        self.rate = PairingRateLimiter(self.db)
        self.invite_limit = max(1, int(invite_limit))
        self.invite_window_s = max(1, int(invite_window_s))
        self.redeem_limit = max(1, int(redeem_limit))
        self.redeem_window_s = max(1, int(redeem_window_s))

    # ------------------------------------------------------------------ helpers

    def _now(self) -> datetime:
        return self.clock().astimezone(timezone.utc)

    def _fetch(self, enrollment_id: str) -> EnrollmentRecord:
        row = self.db.query_one(
            "SELECT * FROM enrollment_requests WHERE enrollment_id = ?",
            (enrollment_id,),
        )
        if row is None:
            raise DeviceError("enrollment not found", kind="not_found", http_status=404)
        return _row_to_record(row)

    def _fetch_conn(self, conn: sqlite3.Connection, enrollment_id: str) -> sqlite3.Row:
        row = conn.execute(
            "SELECT * FROM enrollment_requests WHERE enrollment_id = ?",
            (enrollment_id,),
        ).fetchone()
        if row is None:
            raise DeviceError("enrollment not found", kind="not_found", http_status=404)
        return row

    def _update(
        self,
        conn: sqlite3.Connection,
        enrollment_id: str,
        *,
        now: datetime | None = None,
        **fields: Any,
    ) -> None:
        bad = set(fields) - _ALLOWED_UPDATES
        if bad:
            raise DeviceError(f"invalid enrollment update fields: {sorted(bad)}")
        values: dict[str, Any] = dict(fields)
        values["updated_at"] = _stamp(now or self._now())
        columns = ", ".join(f"{name} = ?" for name in values)
        conn.execute(
            f"UPDATE enrollment_requests SET {columns} WHERE enrollment_id = ?",
            (*values.values(), enrollment_id),
        )

    def _audit(
        self,
        conn: sqlite3.Connection,
        kind: str,
        *,
        enrollment_id: str,
        device_id: str | None = None,
        display_name: str | None = None,
        result: str = "ok",
        profile: str | None = None,
        credential_id: str | None = None,
        actor: str = "local_owner",
        details: dict[str, Any] | None = None,
    ) -> None:
        payload = {"enrollment_id": enrollment_id, **(details or {})}
        self.registry.record_event(
            conn,
            kind,
            device_id=device_id or f"pairing:{enrollment_id}",
            display_name=display_name,
            result=result,
            profile=profile,
            credential_id=credential_id,
            actor=actor,
            details=payload,
        )

    def _transition(
        self,
        conn: sqlite3.Connection,
        row: sqlite3.Row,
        new_state: str,
        *,
        now: datetime,
        reason: str | None = None,
        **fields: Any,
    ) -> None:
        ensure_transition(row["status"], new_state)
        updates = {"status": new_state, **fields}
        if reason is not None:
            updates["reason"] = reason
        self._update(conn, row["enrollment_id"], now=now, **updates)

    # -------------------------------------------------------------- expiration

    def _maybe_expire(self, record: EnrollmentRecord) -> EnrollmentRecord:
        now = self._now()
        if record.status in (PairingState.PENDING.value, PairingState.AWAITING_OWNER_APPROVAL.value):
            expiry = _dt(record.expires_at)
            if expiry is not None and now >= expiry:
                with self.db.transaction() as conn:
                    row = self._fetch_conn(conn, record.enrollment_id)
                    if row["status"] in (
                        PairingState.PENDING.value,
                        PairingState.AWAITING_OWNER_APPROVAL.value,
                    ):
                        self._transition(
                            conn,
                            row,
                            PairingState.EXPIRED.value,
                            now=now,
                            reason="expired",
                            pairing_code_hash=None,
                            pairing_code_salt=None,
                            request_token_hash=None,
                            request_token_salt=None,
                        )
                        self._audit(
                            conn,
                            "pairing.expired",
                            enrollment_id=row["enrollment_id"],
                            display_name=row["display_name"],
                            result="expired",
                            profile=row["requested_profile"],
                            actor="pairing_service",
                            details={"reason": "expired"},
                        )
                        self._audit(
                            conn,
                            "device.enrollment_failed",
                            enrollment_id=row["enrollment_id"],
                            display_name=row["display_name"],
                            result="denied",
                            profile=row["requested_profile"],
                            actor="pairing_service",
                            details={"failure_category": "expired"},
                        )
                return self._fetch(record.enrollment_id)
        if record.status == PairingState.APPROVED.value:
            expiry = _dt(record.delivery_expires_at)
            if expiry is not None and now >= expiry:
                with self.db.transaction() as conn:
                    row = self._fetch_conn(conn, record.enrollment_id)
                    if row["status"] == PairingState.APPROVED.value:
                        self._transition(
                            conn,
                            row,
                            PairingState.EXPIRED.value,
                            now=now,
                            reason="delivery_expired",
                            delivery_ref=None,
                        )
                        self._audit(
                            conn,
                            "pairing.expired",
                            enrollment_id=row["enrollment_id"],
                            device_id=row["device_id"],
                            display_name=row["display_name"],
                            result="expired",
                            profile=row["approved_profile"],
                            credential_id=row["credential_id"],
                            actor="pairing_service",
                            details={"reason": "delivery_expired"},
                        )
                        self._audit(
                            conn,
                            "device.enrollment_failed",
                            enrollment_id=row["enrollment_id"],
                            device_id=row["device_id"],
                            display_name=row["display_name"],
                            result="denied",
                            profile=row["approved_profile"],
                            credential_id=row["credential_id"],
                            actor="pairing_service",
                            details={"failure_category": "delivery_expired"},
                        )
                if record.device_id:
                    try:
                        self.registry.revoke_device(
                            record.device_id,
                            actor="pairing_service",
                            reason="enrollment delivery expired",
                        )
                    except Exception:  # noqa: BLE001 - expiry still stands
                        LOG.warning("could not revoke device after delivery expiry")
                try:
                    self.provider.delete_secret(f"enrollment:{record.enrollment_id}")
                except Exception:  # noqa: BLE001
                    LOG.warning("could not delete expired delivery envelope")
                return self._fetch(record.enrollment_id)
        return record

    def expire_stale(self) -> int:
        rows = self.db.query_all(
            "SELECT * FROM enrollment_requests WHERE status IN "
            "('PENDING','AWAITING_OWNER_APPROVAL','APPROVED')"
        )
        count = 0
        for row in rows:
            before = row["status"]
            self._maybe_expire(_row_to_record(row))
            after = self.db.query_one(
                "SELECT status FROM enrollment_requests WHERE enrollment_id = ?",
                (row["enrollment_id"],),
            )
            if after is not None and after["status"] == PairingState.EXPIRED.value and before != after["status"]:
                count += 1
        return count

    # -------------------------------------------------------------- invitation

    def create_invitation(
        self,
        *,
        display_name: str,
        device_type: str = "other",
        platform: str = "unknown",
        app_version: str = "",
        requested_profile: str = "capture_only",
        owner_id: str = "unassigned",
        metadata: dict[str, Any] | None = None,
        actor: str = "local_owner",
        ttl_s: int = DEFAULT_CODE_TTL_S,
    ) -> EnrollmentInvitation:
        display_name = validate_display_name(display_name)
        device_type = validate_choice("device_type", device_type, ("mac", "iphone", "ipad", "other"))
        platform = validate_choice("platform", platform, ("macos", "ios", "ipados", "unknown"))
        app_version = validate_app_version(app_version)
        requested_profile = validate_choice("requested_profile", requested_profile, PROFILES)
        if requested_profile == "revoked":
            raise DeviceError("requested_profile cannot be revoked")
        if owner_id == "unassigned":
            owner_id = {"school": "school", "partner": "partner"}.get(
                requested_profile, "owen"
            )
        owner_id = validate_owner_id(owner_id)
        meta = validate_metadata(metadata)
        self.rate.consume(
            f"invite:{actor}",
            limit=self.invite_limit,
            window_seconds=self.invite_window_s,
            now=self._now(),
        )
        now = self._now()
        ttl = max(1, min(int(ttl_s), self.code_ttl_s))
        expires = now + timedelta(seconds=ttl)
        code = generate_code_material()
        enrollment_id = new_device_id()
        stamp = _stamp(now)
        requested_permissions = sorted(permissions_for(requested_profile))
        with self.db.transaction() as conn:
            conn.execute(
                """INSERT INTO enrollment_requests(
                    enrollment_id, status, source, display_name, device_type, platform,
                    app_version, owner_id, requested_profile, approved_profile,
                    requested_permissions_json, approved_permissions_json,
                    device_public_key, device_key_algorithm, device_nonce,
                    public_key_fingerprint, protocol_version,
                    pairing_code_hash, pairing_code_salt, pairing_code_expires_at,
                    request_token_hash, request_token_salt, failed_attempts,
                    reason, device_id, credential_id, delivery_ref, replaces_device_id,
                    metadata_json, created_at, updated_at, expires_at,
                    redeemed_at, approved_at, completed_at, rejected_at, cancelled_at,
                    delivery_expires_at
                ) VALUES (?, 'PENDING', 'owner_invitation', ?, ?, ?, ?, ?, ?, NULL,
                    ?, NULL, NULL, NULL, NULL, NULL, ?, ?, ?, ?, NULL, NULL, 0,
                    NULL, NULL, NULL, NULL, NULL, ?, ?, ?, ?, NULL, NULL, NULL, NULL, NULL, NULL)""",
                (
                    enrollment_id,
                    display_name,
                    device_type,
                    platform,
                    app_version,
                    owner_id,
                    requested_profile,
                    _dumps(requested_permissions),
                    PROTOCOL_VERSION,
                    code.verifier,
                    code.salt,
                    _stamp(expires),
                    _dumps(meta),
                    stamp,
                    stamp,
                    _stamp(expires),
                ),
            )
            self._audit(
                conn,
                "pairing.requested",
                enrollment_id=enrollment_id,
                display_name=display_name,
                profile=requested_profile,
                actor=actor,
                details={
                    "source": "owner_invitation",
                    "device_type": device_type,
                    "platform": platform,
                    "code_ttl_seconds": ttl,
                },
            )
            self._audit(
                conn,
                "pairing.code_generated",
                enrollment_id=enrollment_id,
                display_name=display_name,
                profile=requested_profile,
                actor=actor,
                details={
                    "code_length": CODE_LENGTH,
                    "code_ttl_seconds": ttl,
                    "expires_at": _stamp(expires),
                },
            )
        record = self._fetch(enrollment_id)
        payload = qr_payload(
            enrollment_id=enrollment_id,
            display_code=code.display_code,
            expires_at=_stamp(expires),
        )
        return EnrollmentInvitation(
            enrollment=record, pairing_code=code.display_code, qr_payload=payload
        )

    # ------------------------------------------------------------------ redeem

    def redeem(
        self,
        *,
        pairing_code: str,
        device_public_key: str,
        device_key_algorithm: str = "x25519",
        device_nonce: str | None = None,
        enrollment_id: str | None = None,
        display_name: str | None = None,
        device_type: str | None = None,
        platform: str | None = None,
        app_version: str = "",
        requested_profile: str | None = None,
        protocol_version: int = PROTOCOL_VERSION,
        source: str = "local",
        actor: str = "enrolling_device",
    ) -> EnrollmentRedemption:
        self.rate.consume(
            f"redeem:{source}",
            limit=self.redeem_limit,
            window_seconds=self.redeem_window_s,
            now=self._now(),
        )
        if enrollment_id is not None:
            enrollment_id = validate_device_id(enrollment_id)
        if protocol_version != PROTOCOL_VERSION:
            raise DeviceError("unsupported enrollment protocol version")
        if device_key_algorithm != "x25519":
            raise DeviceError("device_key_algorithm must be x25519")
        try:
            fingerprint = public_key_fingerprint(device_public_key)
        except (DeviceError, CryptoError) as exc:
            raise DeviceError("device_public_key is invalid") from exc
        nonce = self._validate_nonce(device_nonce)
        now = self._now()

        row = self._find_code_row(enrollment_id, pairing_code)
        if row is None:
            self._audit_unknown_failure(
                enrollment_id=enrollment_id or "unknown",
                actor=actor,
                reason="invalid_code",
            )
            raise DeviceError("pairing code is invalid", kind="auth", http_status=401)

        record = _row_to_record(row)
        record = self._maybe_expire(record)
        fresh = self._fetch(record.enrollment_id)
        if fresh.status != PairingState.PENDING.value:
            self._audit_replay(fresh, actor=actor, reason=f"state_{fresh.status}")
            if fresh.status == PairingState.EXPIRED.value:
                raise DeviceError("pairing request is expired", kind="expired", http_status=410)
            raise DeviceError(
                "pairing code has already been used",
                kind="conflict",
                http_status=409,
            )

        if not verify_pairing_code(
            pairing_code,
            salt=row["pairing_code_salt"],
            verifier=row["pairing_code_hash"],
        ):
            expired_after_attempts = False
            with self.db.transaction() as conn:
                latest = self._fetch_conn(conn, fresh.enrollment_id)
                attempts = int(latest["failed_attempts"]) + 1
                if attempts >= self.max_code_attempts:
                    self._transition(
                        conn,
                        latest,
                        PairingState.EXPIRED.value,
                        now=now,
                        reason="too_many_code_attempts",
                        failed_attempts=attempts,
                        pairing_code_hash=None,
                        pairing_code_salt=None,
                    )
                    self._audit(
                        conn,
                        "pairing.expired",
                        enrollment_id=latest["enrollment_id"],
                        display_name=latest["display_name"],
                        result="expired",
                        profile=latest["requested_profile"],
                        actor=actor,
                        details={"reason": "too_many_code_attempts"},
                    )
                    self._audit(
                        conn,
                        "device.enrollment_failed",
                        enrollment_id=latest["enrollment_id"],
                        display_name=latest["display_name"],
                        result="denied",
                        profile=latest["requested_profile"],
                        actor=actor,
                        details={"failure_category": "too_many_code_attempts"},
                    )
                    expired_after_attempts = True
                else:
                    self._update(conn, latest["enrollment_id"], now=now, failed_attempts=attempts)
                    self._audit(
                        conn,
                        "device.enrollment_failed",
                        enrollment_id=latest["enrollment_id"],
                        display_name=latest["display_name"],
                        result="denied",
                        profile=latest["requested_profile"],
                        actor=actor,
                        details={"failure_category": "invalid_code", "attempt": attempts},
                    )
            if expired_after_attempts:
                raise DeviceError(
                    "too many incorrect pairing codes",
                    kind="rate_limited",
                    http_status=429,
                )
            raise DeviceError("pairing code is invalid", kind="auth", http_status=401)

        display_name = validate_display_name(display_name or fresh.display_name)
        device_type = validate_choice(
            "device_type", device_type or fresh.device_type, ("mac", "iphone", "ipad", "other")
        )
        platform = validate_choice(
            "platform", platform or fresh.platform, ("macos", "ios", "ipados", "unknown")
        )
        app_version = validate_app_version(app_version)
        requested_profile = validate_choice(
            "requested_profile",
            requested_profile or fresh.requested_profile,
            PROFILES,
        )
        if requested_profile == "revoked":
            raise DeviceError("requested_profile cannot be revoked")
        request_token = secrets.token_urlsafe(32)
        token_salt = secrets.token_hex(16)
        token_hash = hmac.new(
            token_salt.encode("utf-8"), request_token.encode("utf-8"), "sha256"
        ).hexdigest()
        approved_expires = now + timedelta(seconds=self.approval_ttl_s)
        with self.db.transaction() as conn:
            latest = self._fetch_conn(conn, fresh.enrollment_id)
            self._transition(
                conn,
                latest,
                PairingState.AWAITING_OWNER_APPROVAL.value,
                now=now,
                device_public_key=device_public_key,
                device_key_algorithm=device_key_algorithm,
                device_nonce=nonce,
                public_key_fingerprint=fingerprint,
                protocol_version=protocol_version,
                display_name=display_name,
                device_type=device_type,
                platform=platform,
                app_version=app_version,
                requested_profile=requested_profile,
                requested_permissions_json=_dumps(sorted(permissions_for(requested_profile))),
                pairing_code_hash=None,
                pairing_code_salt=None,
                request_token_hash=token_hash,
                request_token_salt=token_salt,
                redeemed_at=_stamp(now),
                expires_at=_stamp(approved_expires),
            )
            self._audit(
                conn,
                "pairing.redeemed",
                enrollment_id=latest["enrollment_id"],
                display_name=display_name,
                profile=requested_profile,
                actor=actor,
                details={
                    "device_type": device_type,
                    "platform": platform,
                    "public_key_fingerprint": fingerprint,
                    "protocol_version": protocol_version,
                    "requested_permissions": sorted(permissions_for(requested_profile)),
                },
            )
        return EnrollmentRedemption(
            enrollment=self._fetch(fresh.enrollment_id), request_token=request_token
        )

    @staticmethod
    def _validate_nonce(value: str | None) -> str:
        if value is None:
            return secrets.token_hex(16)
        if not isinstance(value, str) or not value or len(value) > 256:
            raise DeviceError("device_nonce is invalid")
        try:
            raw = base64.b64decode(value, validate=True)
        except (ValueError, TypeError):
            raw = value.encode("utf-8")
        if not (16 <= len(raw) <= 64):
            raise DeviceError("device_nonce must encode 16-64 bytes")
        return value

    def _find_code_row(self, enrollment_id: str | None, pairing_code: str) -> sqlite3.Row | None:
        if enrollment_id:
            row = self.db.query_one(
                "SELECT * FROM enrollment_requests WHERE enrollment_id = ?",
                (enrollment_id,),
            )
            return row
        rows = self.db.query_all(
            "SELECT * FROM enrollment_requests WHERE status = 'PENDING' "
            "AND pairing_code_hash IS NOT NULL ORDER BY created_at DESC LIMIT 500"
        )
        for row in rows:
            if verify_pairing_code(
                pairing_code, salt=row["pairing_code_salt"], verifier=row["pairing_code_hash"]
            ):
                return row
        return None

    def _audit_replay(self, record: EnrollmentRecord, *, actor: str, reason: str) -> None:
        try:
            with self.db.transaction() as conn:
                self._audit(
                    conn,
                    "pairing.replay_denied",
                    enrollment_id=record.enrollment_id,
                    device_id=record.device_id,
                    display_name=record.display_name,
                    result="denied",
                    profile=record.approved_profile or record.requested_profile,
                    credential_id=record.credential_id,
                    actor=actor,
                    details={"reason": reason},
                )
        except DeviceError:
            LOG.error("could not audit pairing replay denial")

    def _audit_unknown_failure(self, *, enrollment_id: str, actor: str, reason: str) -> None:
        try:
            with self.db.transaction() as conn:
                self._audit(
                    conn,
                    "device.enrollment_failed",
                    enrollment_id=enrollment_id,
                    result="denied",
                    actor=actor,
                    details={"failure_category": reason},
                )
        except DeviceError:
            LOG.error("could not audit pairing failure")

    # ------------------------------------------------------------------ status

    def verify_request_token(self, enrollment_id: str, request_token: str) -> EnrollmentRecord:
        row = self.db.query_one(
            "SELECT * FROM enrollment_requests WHERE enrollment_id = ?",
            (enrollment_id,),
        )
        if row is None or not row["request_token_hash"] or not row["request_token_salt"]:
            raise DeviceError("invalid enrollment session", kind="auth", http_status=401)
        expected = hmac.new(
            str(row["request_token_salt"]).encode("utf-8"),
            str(request_token or "").encode("utf-8"),
            "sha256",
        ).hexdigest()
        if not hmac.compare_digest(expected, row["request_token_hash"]):
            raise DeviceError("invalid enrollment session", kind="auth", http_status=401)
        record = _row_to_record(row)
        return self._maybe_expire(record)

    def status(self, enrollment_id: str, request_token: str) -> EnrollmentRecord:
        return self.verify_request_token(enrollment_id, request_token)

    def complete(self, enrollment_id: str, request_token: str) -> dict[str, Any]:
        record = self.verify_request_token(enrollment_id, request_token)
        if record.status == PairingState.COMPLETED.value:
            raise DeviceError("enrollment already completed", kind="conflict", http_status=409)
        if record.status != PairingState.APPROVED.value:
            raise DeviceError(
                f"enrollment is {record.status}, not approved",
                kind="conflict",
                http_status=409,
            )
        try:
            raw = self.provider.get_secret(f"enrollment:{record.enrollment_id}")
        except Exception as exc:  # noqa: BLE001
            raise DeviceError(
                "credential delivery store unavailable",
                kind="delivery_unavailable",
                http_status=503,
            ) from exc
        if not raw:
            raise DeviceError(
                "credential delivery envelope unavailable",
                kind="delivery_unavailable",
                http_status=503,
            )
        try:
            envelope = json.loads(raw)
        except (TypeError, ValueError) as exc:
            raise DeviceError(
                "credential delivery envelope invalid",
                kind="delivery_unavailable",
                http_status=503,
            ) from exc
        now = self._now()
        with self.db.transaction() as conn:
            latest = self._fetch_conn(conn, enrollment_id)
            self._transition(
                conn,
                latest,
                PairingState.COMPLETED.value,
                now=now,
                completed_at=_stamp(now),
                delivery_ref=None,
                pairing_code_hash=None,
                pairing_code_salt=None,
            )
            self._audit(
                conn,
                "pairing.completed",
                enrollment_id=latest["enrollment_id"],
                device_id=latest["device_id"],
                display_name=latest["display_name"],
                profile=latest["approved_profile"],
                credential_id=latest["credential_id"],
                actor="enrolling_device",
                details={},
            )
            self._audit(
                conn,
                "device.enrolled",
                enrollment_id=latest["enrollment_id"],
                device_id=latest["device_id"],
                display_name=latest["display_name"],
                profile=latest["approved_profile"],
                credential_id=latest["credential_id"],
                actor="enrolling_device",
                details={"public_key_fingerprint": latest["public_key_fingerprint"]},
            )
        try:
            self.provider.delete_secret(f"enrollment:{record.enrollment_id}")
        except Exception:  # noqa: BLE001
            LOG.warning("could not delete delivered enrollment envelope")
        return envelope

    # ---------------------------------------------------------------- approval

    def approve(
        self,
        enrollment_id: str,
        *,
        device_profile: str,
        confirm: bool = False,
        allow_owner: bool = False,
        replaces_device_id: str | None = None,
        actor: str = "local_owner",
    ) -> tuple[EnrollmentRecord, dict[str, Any], dict[str, Any]]:
        if confirm is not True:
            raise DeviceError("explicit owner confirmation is required")
        device_profile = validate_choice("device_profile", device_profile, PROFILES)
        if replaces_device_id is not None:
            replaces_device_id = validate_device_id(replaces_device_id)
        if device_profile == "revoked":
            raise DeviceError("use reject/cancel or device revoke, not the revoked profile")
        if device_profile == "owner" and allow_owner is not True:
            raise DeviceError(
                "owner profile requires explicit allow_owner confirmation",
                kind="conflict",
                http_status=409,
            )
        record = self._fetch(enrollment_id)
        record = self._maybe_expire(record)
        if record.status != PairingState.AWAITING_OWNER_APPROVAL.value:
            raise DeviceError(
                f"enrollment is {record.status}, not awaiting owner approval",
                kind="conflict",
                http_status=409,
            )
        if not record.public_key_fingerprint:
            raise DeviceError("enrollment has no device public key", kind="conflict", http_status=409)

        existing = self.registry.find_by_fingerprint(record.public_key_fingerprint)
        target = None
        if existing:
            if not replaces_device_id:
                raise DeviceError(
                    "this device key is already registered; use explicit replacement",
                    kind="conflict",
                    http_status=409,
                )
            if replaces_device_id not in {item.device_id for item in existing}:
                raise DeviceError(
                    "replaces_device_id does not match this device key",
                    kind="conflict",
                    http_status=409,
                )
            target = next(item for item in existing if item.device_id == replaces_device_id)
        elif replaces_device_id:
            raise DeviceError(
                "replaces_device_id does not match any registered device key",
                kind="conflict",
                http_status=409,
            )

        old_refs: list[str] = []
        if target is not None:
            old_refs = [
                row["keychain_ref"]
                for row in self.db.query_all(
                    "SELECT keychain_ref FROM device_credentials "
                    "WHERE device_id = ? AND status = 'active'",
                    (target.device_id,),
                )
            ]

        now = self._now()
        delivery_expires = now + timedelta(seconds=self.delivery_ttl_s)
        delivery_ref = f"enrollment:{record.enrollment_id}"
        reservation_id = secrets.token_hex(16)

        # Cheap reads + pure crypto happen before any lock is taken.
        key_row = self.db.query_one(
            "SELECT device_public_key FROM enrollment_requests WHERE enrollment_id = ?",
            (enrollment_id,),
        )
        public_key = key_row["device_public_key"] if key_row else None
        if not public_key:
            raise DeviceError(
                "enrollment has no device public key", kind="conflict", http_status=409
            )
        try:
            actual_fingerprint = public_key_fingerprint(public_key)
        except (CryptoError, DeviceError) as exc:
            raise DeviceError(
                "device public key is invalid", kind="conflict", http_status=409
            ) from exc
        if not hmac.compare_digest(actual_fingerprint, record.public_key_fingerprint):
            raise DeviceError(
                "device public key does not match the enrollment fingerprint",
                kind="conflict",
                http_status=409,
            )

        prepared = self.registry.credentials.prepare()
        # The device id is generated before the envelope so the delivered
        # credential names the device that Txn B will create.
        new_device = new_device_id()
        issued = None
        device = None
        try:
            context = self._delivery_context(
                record.enrollment_id, record.public_key_fingerprint
            )
            envelope = self.cipher.encrypt(
                public_key=public_key,
                plaintext=_dumps(
                    {
                        "v": PROTOCOL_VERSION,
                        "credential_id": prepared["credential_id"],
                        "token": prepared["token"],
                        "device_id": new_device,
                        "profile": device_profile,
                        "expires_at": prepared["expires_at"],
                    }
                ).encode("utf-8"),
                context=context,
            )
        except CryptoError as exc:
            raise DeviceError(
                "authenticated credential encryption is unavailable",
                kind="crypto_unavailable",
                http_status=503,
            ) from exc

        # --- Txn A: short, atomic reservation. Holds the lock for milliseconds.
        try:
            with self.db.transaction() as conn:
                latest = self._fetch_conn(conn, enrollment_id)
                if latest["status"] != PairingState.AWAITING_OWNER_APPROVAL.value:
                    raise DeviceError(
                        f"enrollment is {latest['status']}, not awaiting owner approval",
                        kind="conflict",
                        http_status=409,
                    )
                ensure_transition(latest["status"], PairingState.APPROVED.value)
                conn.execute(
                    """INSERT INTO credential_reservations(
                        enrollment_id, reservation_id, credential_id, delivery_ref,
                        device_profile, public_key_fingerprint, expected_state, generation,
                        created_at, expires_at, attempts, state, reason
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?, 0, 'pending', NULL)""",
                    (
                        enrollment_id,
                        reservation_id,
                        prepared["credential_id"],
                        delivery_ref,
                        device_profile,
                        record.public_key_fingerprint,
                        latest["status"],
                        now.isoformat(),
                        (now + timedelta(seconds=self.approval_ttl_s)).isoformat(),
                    ),
                )
        except sqlite3.IntegrityError as exc:
            raise DeviceError(
                "an approval for this enrollment is already in progress",
                kind="conflict",
                http_status=409,
            ) from exc

        # --- Provider work: no database lock held. Slow Keychain calls cannot
        # block unrelated device reads or writes.
        try:
            self.provider.set_secret(prepared["keychain_ref"], prepared["secret"])
            self.provider.set_secret(delivery_ref, _dumps(envelope))
        except Exception as exc:  # noqa: BLE001 - provider is external
            self._finish_failed_reservation(
                reservation_id,
                reason="provider_unavailable",
                refs=[prepared["keychain_ref"], delivery_ref],
            )
            raise DeviceError(
                "credential delivery store unavailable",
                kind="delivery_unavailable",
                http_status=503,
            ) from exc

        # --- Txn B: short, atomic activation. Revalidates everything.
        try:
            with self.db.transaction() as conn:
                claimed = conn.execute(
                    "UPDATE credential_reservations SET attempts = attempts + 1 "
                    "WHERE reservation_id = ? AND state = 'pending'",
                    (reservation_id,),
                ).rowcount
                if claimed != 1:
                    raise DeviceError(
                        "approval reservation is no longer current",
                        kind="conflict",
                        http_status=409,
                    )
                reservation = conn.execute(
                    "SELECT * FROM credential_reservations WHERE reservation_id = ?",
                    (reservation_id,),
                ).fetchone()
                if _dt(reservation["expires_at"]) <= self._now():
                    raise DeviceError(
                        "approval reservation expired", kind="conflict", http_status=409
                    )
                latest = self._fetch_conn(conn, enrollment_id)
                if latest["status"] != PairingState.AWAITING_OWNER_APPROVAL.value:
                    raise DeviceError(
                        "enrollment changed during approval",
                        kind="conflict",
                        http_status=409,
                    )
                if latest["public_key_fingerprint"] != reservation["public_key_fingerprint"]:
                    raise DeviceError(
                        "enrollment identity changed during approval",
                        kind="conflict",
                        http_status=409,
                    )
                if target is not None:
                    self.registry.revoke_device(
                        target.device_id,
                        actor=actor,
                        reason=f"replaced by enrollment {enrollment_id}",
                        conn=conn,
                    )
                metadata = {
                    "enrollment_id": record.enrollment_id,
                    "pairing_protocol": record.protocol_version,
                    "public_key_sha256": record.public_key_fingerprint,
                }
                if replaces_device_id:
                    metadata["replaced_device_id"] = replaces_device_id
                device, _unused = self.registry.register_device(
                    display_name=record.display_name,
                    device_type=record.device_type,
                    platform=record.platform,
                    owner_id=record.owner_id,
                    device_profile=device_profile,
                    app_version=record.app_version,
                    metadata=metadata,
                    is_primary_owner=False,
                    issue_credential=False,
                    device_id=new_device,
                    public_key_fingerprint=record.public_key_fingerprint,
                    actor=actor,
                    conn=conn,
                )
                issued = self.registry.credentials.insert_prepared(
                    conn, prepared, device_id=device.device_id, actor=actor
                )
                self._transition(
                    conn,
                    latest,
                    PairingState.APPROVED.value,
                    now=now,
                    approved_profile=device_profile,
                    approved_permissions_json=_dumps(sorted(permissions_for(device_profile))),
                    device_id=device.device_id,
                    credential_id=issued.credential_id,
                    delivery_ref=delivery_ref,
                    approved_at=_stamp(now),
                    delivery_expires_at=_stamp(delivery_expires),
                    replaces_device_id=replaces_device_id,
                )
                self._audit(
                    conn,
                    "pairing.approved",
                    enrollment_id=record.enrollment_id,
                    device_id=device.device_id,
                    display_name=device.display_name,
                    profile=device_profile,
                    credential_id=issued.credential_id,
                    actor=actor,
                    details={
                        "requested_profile": record.requested_profile,
                        "approved_profile": device_profile,
                        "approved_permissions": sorted(permissions_for(device_profile)),
                        "replaces_device_id": replaces_device_id,
                    },
                )
                self._audit(
                    conn,
                    "device.credential_issued",
                    enrollment_id=record.enrollment_id,
                    device_id=device.device_id,
                    display_name=device.display_name,
                    profile=device_profile,
                    credential_id=issued.credential_id,
                    actor=actor,
                    details={"delivery": "encrypted-envelope"},
                )
                if target is not None:
                    self._audit(
                        conn,
                        "device.replaced",
                        enrollment_id=record.enrollment_id,
                        device_id=device.device_id,
                        display_name=device.display_name,
                        profile=device_profile,
                        credential_id=issued.credential_id,
                        actor=actor,
                        details={
                            "previous_device_id": target.device_id,
                            "previous_profile": target.device_profile,
                            "public_key_fingerprint": record.public_key_fingerprint,
                        },
                    )
                conn.execute(
                    "DELETE FROM credential_reservations WHERE reservation_id = ?",
                    (reservation_id,),
                )
            if target is not None and old_refs:
                self.registry.credentials.delete_secrets(old_refs)
            return self._fetch(enrollment_id), device.public_dict(), issued.public_dict()
        except Exception:
            # The provider succeeded but activation did not commit. Delete both
            # provider entries; the row is never created, so nothing authenticates.
            self._finish_failed_reservation(
                reservation_id,
                reason="activation_failed",
                refs=[prepared["keychain_ref"], delivery_ref],
            )
            raise

    # ---------------------------------------------------------- reservations

    def _delete_provider_refs(self, refs: list[str]) -> bool:
        ok = True
        for ref in refs:
            try:
                self.provider.delete_secret(ref)
            except Exception:  # noqa: BLE001 - cleanup must not mask the original error
                ok = False
                LOG.warning("could not delete credential-provider reference %s", ref)
        return ok

    def _finish_failed_reservation(self, reservation_id: str, *, reason: str, refs: list[str]) -> None:
        cleaned = self._delete_provider_refs(refs)
        try:
            with self.db.transaction() as conn:
                if cleaned:
                    conn.execute(
                        "DELETE FROM credential_reservations WHERE reservation_id = ?",
                        (reservation_id,),
                    )
                else:
                    conn.execute(
                        "UPDATE credential_reservations SET state = 'cleanup_failed', reason = ? "
                        "WHERE reservation_id = ?",
                        (reason, reservation_id),
                    )
        except Exception:  # noqa: BLE001 - the reservation stays for recovery
            LOG.warning("could not update reservation %s during cleanup", reservation_id)

    def reconcile_reservations(self) -> dict[str, Any]:
        """Idempotent, bounded cleanup of stale or orphaned reservations.

        Never approves anything and never creates a device. Provider entries for
        a stale reservation are deleted before the row is removed; if deletion
        fails the row stays visible as `cleanup_failed` for the next attempt.
        """
        rows = self.db.query_all("SELECT * FROM credential_reservations")
        cleaned: list[str] = []
        remaining: list[str] = []
        for row in rows:
            enrollment = self.db.query_one(
                "SELECT status FROM enrollment_requests WHERE enrollment_id = ?",
                (row["enrollment_id"],),
            )
            expires = _dt(row["expires_at"])
            stale = (
                enrollment is None
                or enrollment["status"] != PairingState.AWAITING_OWNER_APPROVAL.value
                or (expires is not None and expires <= self._now())
                or row["state"] == "cleanup_failed"
            )
            if not stale:
                remaining.append(row["enrollment_id"])
                continue
            refs = [f"device:{row['credential_id']}", row["delivery_ref"]]
            if self._delete_provider_refs(refs):
                with self.db.transaction() as conn:
                    conn.execute(
                        "DELETE FROM credential_reservations WHERE reservation_id = ?",
                        (row["reservation_id"],),
                    )
                cleaned.append(row["enrollment_id"])
            else:
                with self.db.transaction() as conn:
                    conn.execute(
                        "UPDATE credential_reservations SET state = 'cleanup_failed' "
                        "WHERE reservation_id = ?",
                        (row["reservation_id"],),
                    )
                remaining.append(row["enrollment_id"])
        return {"ok": True, "cleaned": cleaned, "remaining": remaining}

    @staticmethod
    def _validate_nonce(value: str | None) -> str:
        if value is None:
            return secrets.token_hex(16)
        if not isinstance(value, str) or not value or len(value) > 256:
            raise DeviceError("device_nonce is invalid")
        try:
            raw = base64.b64decode(value, validate=True)
        except (ValueError, TypeError):
            raw = value.encode("utf-8")
        if not (16 <= len(raw) <= 64):
            raise DeviceError("device_nonce must encode 16-64 bytes")
        return value

    def _find_code_row(self, enrollment_id: str | None, pairing_code: str) -> sqlite3.Row | None:
        if enrollment_id:
            row = self.db.query_one(
                "SELECT * FROM enrollment_requests WHERE enrollment_id = ?",
                (enrollment_id,),
            )
            return row
        rows = self.db.query_all(
            "SELECT * FROM enrollment_requests WHERE status = 'PENDING' "
            "AND pairing_code_hash IS NOT NULL ORDER BY created_at DESC LIMIT 500"
        )
        for row in rows:
            if verify_pairing_code(
                pairing_code, salt=row["pairing_code_salt"], verifier=row["pairing_code_hash"]
            ):
                return row
        return None

    def _audit_replay(self, record: EnrollmentRecord, *, actor: str, reason: str) -> None:
        try:
            with self.db.transaction() as conn:
                self._audit(
                    conn,
                    "pairing.replay_denied",
                    enrollment_id=record.enrollment_id,
                    device_id=record.device_id,
                    display_name=record.display_name,
                    result="denied",
                    profile=record.approved_profile or record.requested_profile,
                    credential_id=record.credential_id,
                    actor=actor,
                    details={"reason": reason},
                )
        except DeviceError:
            LOG.error("could not audit pairing replay denial")

    def _audit_unknown_failure(self, *, enrollment_id: str, actor: str, reason: str) -> None:
        try:
            with self.db.transaction() as conn:
                self._audit(
                    conn,
                    "device.enrollment_failed",
                    enrollment_id=enrollment_id,
                    result="denied",
                    actor=actor,
                    details={"failure_category": reason},
                )
        except DeviceError:
            LOG.error("could not audit pairing failure")

    # ------------------------------------------------------------------ status

    def verify_request_token(self, enrollment_id: str, request_token: str) -> EnrollmentRecord:
        row = self.db.query_one(
            "SELECT * FROM enrollment_requests WHERE enrollment_id = ?",
            (enrollment_id,),
        )
        if row is None or not row["request_token_hash"] or not row["request_token_salt"]:
            raise DeviceError("invalid enrollment session", kind="auth", http_status=401)
        expected = hmac.new(
            str(row["request_token_salt"]).encode("utf-8"),
            str(request_token or "").encode("utf-8"),
            "sha256",
        ).hexdigest()
        if not hmac.compare_digest(expected, row["request_token_hash"]):
            raise DeviceError("invalid enrollment session", kind="auth", http_status=401)
        record = _row_to_record(row)
        return self._maybe_expire(record)

    def status(self, enrollment_id: str, request_token: str) -> EnrollmentRecord:
        return self.verify_request_token(enrollment_id, request_token)

    def complete(self, enrollment_id: str, request_token: str) -> dict[str, Any]:
        record = self.verify_request_token(enrollment_id, request_token)
        if record.status == PairingState.COMPLETED.value:
            raise DeviceError("enrollment already completed", kind="conflict", http_status=409)
        if record.status != PairingState.APPROVED.value:
            raise DeviceError(
                f"enrollment is {record.status}, not approved",
                kind="conflict",
                http_status=409,
            )
        try:
            raw = self.provider.get_secret(f"enrollment:{record.enrollment_id}")
        except Exception as exc:  # noqa: BLE001
            raise DeviceError(
                "credential delivery store unavailable",
                kind="delivery_unavailable",
                http_status=503,
            ) from exc
        if not raw:
            raise DeviceError(
                "credential delivery envelope unavailable",
                kind="delivery_unavailable",
                http_status=503,
            )
        try:
            envelope = json.loads(raw)
        except (TypeError, ValueError) as exc:
            raise DeviceError(
                "credential delivery envelope invalid",
                kind="delivery_unavailable",
                http_status=503,
            ) from exc
        now = self._now()
        with self.db.transaction() as conn:
            latest = self._fetch_conn(conn, enrollment_id)
            self._transition(
                conn,
                latest,
                PairingState.COMPLETED.value,
                now=now,
                completed_at=_stamp(now),
                delivery_ref=None,
                pairing_code_hash=None,
                pairing_code_salt=None,
            )
            self._audit(
                conn,
                "pairing.completed",
                enrollment_id=latest["enrollment_id"],
                device_id=latest["device_id"],
                display_name=latest["display_name"],
                profile=latest["approved_profile"],
                credential_id=latest["credential_id"],
                actor="enrolling_device",
                details={},
            )
            self._audit(
                conn,
                "device.enrolled",
                enrollment_id=latest["enrollment_id"],
                device_id=latest["device_id"],
                display_name=latest["display_name"],
                profile=latest["approved_profile"],
                credential_id=latest["credential_id"],
                actor="enrolling_device",
                details={"public_key_fingerprint": latest["public_key_fingerprint"]},
            )
        try:
            self.provider.delete_secret(f"enrollment:{record.enrollment_id}")
        except Exception:  # noqa: BLE001
            LOG.warning("could not delete delivered enrollment envelope")
        return envelope

    # ---------------------------------------------------------------- approval

    @staticmethod
    def _delivery_context(enrollment_id: str, fingerprint: str) -> bytes:
        return f"chief-enroll-v1\n{enrollment_id}\n{fingerprint}".encode("utf-8")

    @staticmethod
    def _public_key(conn: sqlite3.Connection, enrollment_id: str) -> str:
        row = conn.execute(
            "SELECT device_public_key FROM enrollment_requests WHERE enrollment_id = ?",
            (enrollment_id,),
        ).fetchone()
        if row is None or not row["device_public_key"]:
            raise DeviceError("enrollment has no device public key", kind="conflict", http_status=409)
        return str(row["device_public_key"])

    # ------------------------------------------------------------ reject/cancel

    def reject(
        self,
        enrollment_id: str,
        *,
        reason: str = "",
        confirm: bool = False,
        actor: str = "local_owner",
    ) -> EnrollmentRecord:
        if confirm is not True:
            raise DeviceError("explicit owner confirmation is required")
        record = self._fetch(enrollment_id)
        if record.status not in (
            PairingState.PENDING.value,
            PairingState.AWAITING_OWNER_APPROVAL.value,
        ):
            raise DeviceError(
                f"enrollment is {record.status} and cannot be rejected",
                kind="conflict",
                http_status=409,
            )
        now = self._now()
        with self.db.transaction() as conn:
            latest = self._fetch_conn(conn, enrollment_id)
            self._transition(
                conn,
                latest,
                PairingState.REJECTED.value,
                now=now,
                reason=reason[:200] if reason else "rejected by owner",
                rejected_at=_stamp(now),
                pairing_code_hash=None,
                pairing_code_salt=None,
                request_token_hash=None,
                request_token_salt=None,
            )
            self._audit(
                conn,
                "pairing.rejected",
                enrollment_id=enrollment_id,
                display_name=latest["display_name"],
                result="rejected",
                profile=latest["requested_profile"],
                actor=actor,
                details={"reason": reason[:200]} if reason else {},
            )
        return self._fetch(enrollment_id)

    def cancel(
        self,
        enrollment_id: str,
        *,
        reason: str = "",
        confirm: bool = False,
        actor: str = "local_owner",
    ) -> EnrollmentRecord:
        if confirm is not True:
            raise DeviceError("explicit owner confirmation is required")
        record = self._fetch(enrollment_id)
        if record.status in (
            PairingState.REJECTED.value,
            PairingState.EXPIRED.value,
            PairingState.COMPLETED.value,
            PairingState.CANCELLED.value,
        ):
            raise DeviceError(
                f"enrollment is {record.status} and cannot be cancelled",
                kind="conflict",
                http_status=409,
            )
        now = self._now()
        old_refs: list[str] = []
        if record.status == PairingState.APPROVED.value and record.device_id:
            old_refs = [
                row["keychain_ref"]
                for row in self.db.query_all(
                    "SELECT keychain_ref FROM device_credentials "
                    "WHERE device_id = ? AND status = 'active'",
                    (record.device_id,),
                )
            ]
        with self.db.transaction() as conn:
            latest = self._fetch_conn(conn, enrollment_id)
            if latest["status"] == PairingState.APPROVED.value and latest["device_id"]:
                self.registry.revoke_device(
                    latest["device_id"],
                    actor=actor,
                    reason=f"enrollment {enrollment_id} cancelled",
                    conn=conn,
                )
            self._transition(
                conn,
                latest,
                PairingState.CANCELLED.value,
                now=now,
                reason=reason[:200] if reason else "cancelled by owner",
                cancelled_at=_stamp(now),
                pairing_code_hash=None,
                pairing_code_salt=None,
                request_token_hash=None,
                request_token_salt=None,
                delivery_ref=None,
            )
            self._audit(
                conn,
                "pairing.cancelled",
                enrollment_id=enrollment_id,
                device_id=latest["device_id"],
                display_name=latest["display_name"],
                result="cancelled",
                profile=latest["approved_profile"] or latest["requested_profile"],
                credential_id=latest["credential_id"],
                actor=actor,
                details={"reason": reason[:200]} if reason else {},
            )
        try:
            self.provider.delete_secret(f"enrollment:{enrollment_id}")
        except Exception:  # noqa: BLE001
            LOG.warning("could not delete cancelled enrollment envelope")
        self.registry.credentials.delete_secrets(old_refs)
        return self._fetch(enrollment_id)

    # ------------------------------------------------------------------- lists

    def list_pending(self, *, limit: int = 50, offset: int = 0) -> dict[str, Any]:
        self.expire_stale()
        limit = max(1, min(int(limit), 100))
        offset = max(0, int(offset))
        rows = self.db.query_all(
            "SELECT * FROM enrollment_requests WHERE status IN "
            "('PENDING','AWAITING_OWNER_APPROVAL','APPROVED') "
            "ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        )
        total = self.db.query_one(
            "SELECT COUNT(*) AS c FROM enrollment_requests WHERE status IN "
            "('PENDING','AWAITING_OWNER_APPROVAL','APPROVED')"
        )["c"]
        return {
            "enrollments": [_row_to_record(row).public_dict() for row in rows],
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    def get_enrollment(self, enrollment_id: str) -> EnrollmentRecord:
        return self._maybe_expire(self._fetch(enrollment_id))
