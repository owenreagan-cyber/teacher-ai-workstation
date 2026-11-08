"""Device record types, enums, and validation for the local device registry.

Device identity is a random 128-bit value generated once and persisted. It is
never derived from an IP address, hostname, display name, or hardware serial.
"""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

DEVICE_TYPES = ("mac", "iphone", "ipad", "other")
PLATFORMS = ("macos", "ios", "ipados", "unknown")
PROFILES = ("owner", "personal", "partner", "school", "read_only", "capture_only", "revoked")
TRUST_LEVELS = ("owner", "trusted", "limited", "restricted", "untrusted")
STATUSES = ("active", "disabled", "revoked", "removed")
CREDENTIAL_TYPES = ("device_access",)
CREDENTIAL_STATUSES = ("active", "rotated", "expired", "revoked")

TRUST_BY_PROFILE = {
    "owner": "owner",
    "personal": "trusted",
    "partner": "limited",
    "school": "restricted",
    "read_only": "restricted",
    "capture_only": "restricted",
    "revoked": "untrusted",
}

MAX_DISPLAY_NAME = 80
MAX_OWNER_ID = 64
MAX_APP_VERSION = 64
MAX_METADATA_BYTES = 8192
_HEX32 = re.compile(r"^[a-f0-9]{32}$")
# Metadata is for non-sensitive labels only. Refuse keys that suggest a secret
# or student data; the registry is never a place for raw credentials or PII.
_FORBIDDEN_METADATA_KEY = re.compile(
    r"(?i)(token|secret|passw|credential|private.?key|student|pupil|ssn|social.?security|dob|birth)"
)


class DeviceError(Exception):
    """A validation, lifecycle, or storage failure with a stable error kind."""

    def __init__(self, message: str, *, kind: str = "usage", http_status: int = 400):
        super().__init__(message)
        self.kind = kind
        self.http_status = http_status


class PrimaryDeviceProtected(DeviceError):
    def __init__(self, message: str = "primary owner device is protected"):
        super().__init__(message, kind="conflict", http_status=409)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def new_device_id() -> str:
    return uuid.uuid4().hex


def new_credential_id() -> str:
    return uuid.uuid4().hex


def validate_device_id(value: str) -> str:
    if not isinstance(value, str) or not _HEX32.fullmatch(value):
        raise DeviceError("device_id must be 32 lowercase hex characters")
    return value


def validate_credential_id(value: str) -> str:
    if not isinstance(value, str) or not _HEX32.fullmatch(value):
        raise DeviceError("credential_id must be 32 lowercase hex characters")
    return value


def validate_display_name(value: str) -> str:
    if not isinstance(value, str):
        raise DeviceError("display_name must be text")
    name = value.strip()
    if not name or len(name) > MAX_DISPLAY_NAME:
        raise DeviceError(f"display_name must be 1-{MAX_DISPLAY_NAME} characters")
    if any(ord(ch) < 32 for ch in name):
        raise DeviceError("display_name must not contain control characters")
    return name


def validate_choice(name: str, value: str, choices: tuple[str, ...]) -> str:
    if not isinstance(value, str) or value not in choices:
        raise DeviceError(f"{name} must be one of {', '.join(choices)}")
    return value


def validate_owner_id(value: str) -> str:
    if not isinstance(value, str):
        raise DeviceError("owner_id must be text")
    owner = value.strip()
    if not owner or len(owner) > MAX_OWNER_ID:
        raise DeviceError(f"owner_id must be 1-{MAX_OWNER_ID} characters")
    return owner


def validate_app_version(value: str) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        raise DeviceError("app_version must be text")
    version = value.strip()
    if len(version) > MAX_APP_VERSION:
        raise DeviceError(f"app_version must be at most {MAX_APP_VERSION} characters")
    return version


def validate_metadata(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise DeviceError("metadata must be a JSON object")
    clean: dict[str, Any] = {}
    for key, item in value.items():
        if not isinstance(key, str) or not key or len(key) > 64:
            raise DeviceError("metadata keys must be 1-64 characters")
        if _FORBIDDEN_METADATA_KEY.search(key):
            raise DeviceError(f"metadata key {key!r} is not permitted")
        if isinstance(item, (dict, list)):
            # Bounded nesting is allowed, but it must be JSON serialisable.
            try:
                encoded = json.dumps(item, separators=(",", ":"), ensure_ascii=False)
            except (TypeError, ValueError):
                raise DeviceError(f"metadata.{key} is not JSON serialisable")
            if len(encoded.encode("utf-8")) > 2048:
                raise DeviceError(f"metadata.{key} is too large")
            clean[key] = item
        elif isinstance(item, (str, int, float, bool)) or item is None:
            if isinstance(item, str) and len(item) > 256:
                raise DeviceError(f"metadata.{key} is too long")
            clean[key] = item
        else:
            raise DeviceError(f"metadata.{key} has an unsupported type")
    raw = json.dumps(clean, separators=(",", ":"), ensure_ascii=False, sort_keys=True)
    if len(raw.encode("utf-8")) > MAX_METADATA_BYTES:
        raise DeviceError("metadata is too large")
    return clean


def parse_metadata(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        value = json.loads(raw)
    except (TypeError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}


@dataclass(frozen=True)
class DeviceRecord:
    device_id: str
    display_name: str
    device_type: str
    platform: str
    owner_id: str
    device_profile: str
    trust_level: str
    status: str
    app_version: str
    registered_at: str
    last_seen_at: str | None
    updated_at: str
    revoked_at: str | None
    metadata: dict[str, Any] = field(default_factory=dict)
    is_primary_owner: bool = False

    @property
    def active(self) -> bool:
        return self.status == "active"

    def public_dict(self) -> dict[str, Any]:
        """A bounded representation safe for local clients (no credential data)."""
        return {
            "device_id": self.device_id,
            "display_name": self.display_name,
            "device_type": self.device_type,
            "platform": self.platform,
            "owner_id": self.owner_id,
            "device_profile": self.device_profile,
            "trust_level": self.trust_level,
            "status": self.status,
            "app_version": self.app_version,
            "registered_at": self.registered_at,
            "last_seen_at": self.last_seen_at,
            "updated_at": self.updated_at,
            "revoked_at": self.revoked_at,
            "metadata": dict(self.metadata),
            "is_primary_owner": self.is_primary_owner,
        }
