"""HTTP routing for P1b.4c pairing and local enrollment management."""

from __future__ import annotations

import json
import logging
import re
from typing import Any
from urllib.parse import parse_qs, urlparse

from ..models import DeviceError
from .service import PairingService

LOG = logging.getLogger("cosd.devices.pairing.http")

_ENROLL_STATUS = re.compile(r"^/v1/enroll/status/(?P<enrollment_id>[a-f0-9]{32})(?:/complete)?$")
_PENDING = re.compile(
    r"^/v1/devices/pending(?:/(?P<enrollment_id>[a-f0-9]{32}))?"
    r"(?:/(?P<action>approve|reject|cancel))?$"
)

_INVITE_FIELDS = {
    "display_name",
    "device_type",
    "platform",
    "app_version",
    "requested_profile",
    "owner_id",
    "metadata",
    "ttl_seconds",
}
_REDEEM_FIELDS = {
    "enrollment_id",
    "pairing_code",
    "device_public_key",
    "device_key_algorithm",
    "device_nonce",
    "display_name",
    "device_type",
    "platform",
    "app_version",
    "requested_profile",
    "protocol_version",
}


def _read_json(handler, max_bytes: int) -> dict[str, Any]:
    length = int(handler.headers.get("Content-Length", "0") or "0")
    if length > max_bytes:
        raise DeviceError("request too large", kind="usage", http_status=413)
    if length == 0:
        return {}
    raw = handler.rfile.read(length)
    try:
        data = json.loads(raw.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise DeviceError("invalid JSON", kind="usage", http_status=400)
    if not isinstance(data, dict):
        raise DeviceError("body must be an object", kind="usage", http_status=400)
    return data


def _reject_unknown(body: dict[str, Any], allowed: set[str]) -> None:
    unknown = set(body) - allowed
    if unknown:
        raise DeviceError(f"unknown fields: {', '.join(sorted(unknown))}", kind="usage")


def _enrollment_token(handler) -> str | None:
    header = handler.headers.get("Authorization") or ""
    if header.startswith("Enrollment "):
        token = header[len("Enrollment ") :].strip()
        return token or None
    return None


def dispatch_pairing_request(
    handler,
    *,
    pairing: PairingService,
    max_body: int,
    owner_actor: str | None,
) -> tuple[int, dict[str, Any]] | None:
    parsed = urlparse(handler.path)
    path = parsed.path
    method = handler.command
    if not (
        path == "/v1/enroll/request"
        or path == "/v1/enroll/redeem"
        or path.startswith("/v1/enroll/status/")
        or path == "/v1/devices/pending"
        or path.startswith("/v1/devices/pending/")
    ):
        return None
    try:
        if path == "/v1/enroll/request":
            if method != "POST":
                return 405, {"ok": False, "error": "method not allowed", "error_kind": "method"}
            if owner_actor is None:
                raise DeviceError("owner authentication required", kind="forbidden", http_status=403)
            body = _read_json(handler, max_body)
            _reject_unknown(body, _INVITE_FIELDS)
            invitation = pairing.create_invitation(
                display_name=str(body.get("display_name") or ""),
                device_type=str(body.get("device_type") or "other"),
                platform=str(body.get("platform") or "unknown"),
                app_version=str(body.get("app_version") or ""),
                requested_profile=str(body.get("requested_profile") or "capture_only"),
                owner_id=str(body.get("owner_id") or "unassigned"),
                metadata=body.get("metadata"),
                actor=owner_actor,
                ttl_s=int(body.get("ttl_seconds") or 600),
            )
            return 201, invitation.public_dict()

        if path == "/v1/enroll/redeem":
            if method != "POST":
                return 405, {"ok": False, "error": "method not allowed", "error_kind": "method"}
            body = _read_json(handler, max_body)
            _reject_unknown(body, _REDEEM_FIELDS)
            source = handler.client_address[0] if handler.client_address else "local"
            redemption = pairing.redeem(
                pairing_code=str(body.get("pairing_code") or ""),
                device_public_key=str(body.get("device_public_key") or ""),
                device_key_algorithm=str(body.get("device_key_algorithm") or "x25519"),
                device_nonce=body.get("device_nonce"),
                enrollment_id=body.get("enrollment_id"),
                display_name=body.get("display_name"),
                device_type=body.get("device_type"),
                platform=body.get("platform"),
                app_version=str(body.get("app_version") or ""),
                requested_profile=body.get("requested_profile"),
                protocol_version=int(body.get("protocol_version") or 1),
                source=source,
                actor="enrolling_device",
            )
            return 200, redemption.public_dict()

        match = _ENROLL_STATUS.match(path)
        if match is not None:
            enrollment_id = match.group("enrollment_id")
            token = _enrollment_token(handler)
            if token is None:
                raise DeviceError("enrollment token required", kind="auth", http_status=401)
            if path.endswith("/complete"):
                if method != "POST":
                    return 405, {"ok": False, "error": "method not allowed", "error_kind": "method"}
                _read_json(handler, max_body)
                envelope = pairing.complete(enrollment_id, token)
                return 200, {"ok": True, "envelope": envelope}
            if method != "GET":
                return 405, {"ok": False, "error": "method not allowed", "error_kind": "method"}
            record = pairing.status(enrollment_id, token)
            return 200, {"ok": True, "enrollment": record.public_dict()}

        pending = _PENDING.match(path)
        if pending is not None:
            enrollment_id = pending.group("enrollment_id")
            action = pending.group("action")
            if owner_actor is None:
                raise DeviceError("owner authentication required", kind="forbidden", http_status=403)
            if path == "/v1/devices/pending":
                if method != "GET":
                    return 405, {"ok": False, "error": "method not allowed", "error_kind": "method"}
                query = parse_qs(parsed.query)
                result = pairing.list_pending(
                    limit=int((query.get("limit") or ["50"])[0]),
                    offset=int((query.get("offset") or ["0"])[0]),
                )
                return 200, {"ok": True, **result}
            if enrollment_id is None:
                return 404, {"ok": False, "error": "not found", "error_kind": "not_found"}
            if action is None:
                if method != "GET":
                    return 405, {"ok": False, "error": "method not allowed", "error_kind": "method"}
                return 200, {
                    "ok": True,
                    "enrollment": pairing.get_enrollment(enrollment_id).public_dict(),
                }
            if method != "POST":
                return 405, {"ok": False, "error": "method not allowed", "error_kind": "method"}
            body = _read_json(handler, max_body)
            if action == "approve":
                _reject_unknown(
                    body,
                    {"device_profile", "confirm", "allow_owner", "replaces_device_id"},
                )
                record, device, credential = pairing.approve(
                    enrollment_id,
                    device_profile=str(body.get("device_profile") or ""),
                    confirm=body.get("confirm") is True,
                    allow_owner=body.get("allow_owner") is True,
                    replaces_device_id=body.get("replaces_device_id"),
                    actor=owner_actor,
                )
                return 200, {
                    "ok": True,
                    "enrollment": record.public_dict(),
                    "device": device,
                    "credential": credential,
                }
            if action == "reject":
                _reject_unknown(body, {"reason", "confirm"})
                record = pairing.reject(
                    enrollment_id,
                    reason=str(body.get("reason") or ""),
                    confirm=body.get("confirm") is True,
                    actor=owner_actor,
                )
                return 200, {"ok": True, "enrollment": record.public_dict()}
            if action == "cancel":
                _reject_unknown(body, {"reason", "confirm"})
                record = pairing.cancel(
                    enrollment_id,
                    reason=str(body.get("reason") or ""),
                    confirm=body.get("confirm") is True,
                    actor=owner_actor,
                )
                return 200, {"ok": True, "enrollment": record.public_dict()}
        return 404, {"ok": False, "error": "not found", "error_kind": "not_found"}
    except DeviceError as exc:
        return exc.http_status, {
            "ok": False,
            "error": str(exc),
            "error_kind": exc.kind,
        }
    except ValueError as exc:
        return 400, {"ok": False, "error": str(exc), "error_kind": "usage"}
    except Exception:  # noqa: BLE001 - no internals leak
        LOG.exception("pairing API failure")
        return 500, {"ok": False, "error": "internal error", "error_kind": "internal"}
