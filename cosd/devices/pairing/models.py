"""Bounded pairing/enrollment records safe to return to clients."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class EnrollmentRecord:
    enrollment_id: str
    status: str
    source: str
    display_name: str
    device_type: str
    platform: str
    app_version: str
    owner_id: str
    requested_profile: str
    approved_profile: str | None
    requested_permissions: tuple[str, ...] = ()
    approved_permissions: tuple[str, ...] = ()
    public_key_fingerprint: str | None = None
    protocol_version: int = 1
    created_at: str = ""
    updated_at: str = ""
    expires_at: str = ""
    redeemed_at: str | None = None
    approved_at: str | None = None
    completed_at: str | None = None
    rejected_at: str | None = None
    cancelled_at: str | None = None
    delivery_expires_at: str | None = None
    device_id: str | None = None
    credential_id: str | None = None
    replaces_device_id: str | None = None
    reason: str | None = None
    failed_attempts: int = 0

    def public_dict(self) -> dict[str, Any]:
        return {
            "enrollment_id": self.enrollment_id,
            "status": self.status,
            "source": self.source,
            "display_name": self.display_name,
            "device_type": self.device_type,
            "platform": self.platform,
            "app_version": self.app_version,
            "owner_id": self.owner_id,
            "requested_profile": self.requested_profile,
            "approved_profile": self.approved_profile,
            "requested_permissions": list(self.requested_permissions),
            "approved_permissions": list(self.approved_permissions),
            "public_key_fingerprint": self.public_key_fingerprint,
            "protocol_version": self.protocol_version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "expires_at": self.expires_at,
            "redeemed_at": self.redeemed_at,
            "approved_at": self.approved_at,
            "completed_at": self.completed_at,
            "rejected_at": self.rejected_at,
            "cancelled_at": self.cancelled_at,
            "delivery_expires_at": self.delivery_expires_at,
            "device_id": self.device_id,
            "credential_id": self.credential_id,
            "replaces_device_id": self.replaces_device_id,
            "reason": self.reason,
            "failed_attempts": self.failed_attempts,
        }


@dataclass(frozen=True)
class EnrollmentInvitation:
    enrollment: EnrollmentRecord
    pairing_code: str
    qr_payload: str

    def public_dict(self) -> dict[str, Any]:
        return {
            "ok": True,
            "enrollment": self.enrollment.public_dict(),
            "pairing_code": self.pairing_code,
            "qr_payload": self.qr_payload,
            "expires_at": self.enrollment.expires_at,
        }


@dataclass(frozen=True)
class EnrollmentRedemption:
    enrollment: EnrollmentRecord
    request_token: str

    def public_dict(self) -> dict[str, Any]:
        return {
            "ok": True,
            "enrollment": self.enrollment.public_dict(),
            "request_token": self.request_token,
            "expires_at": self.enrollment.expires_at,
        }
