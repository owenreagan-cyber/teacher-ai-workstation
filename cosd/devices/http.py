"""HTTP routing for /v1/devices (loopback-only, owner-authenticated)."""

from __future__ import annotations

import json
import logging
import re
from typing import Any
from urllib.parse import parse_qs, urlparse

from .authorization import Principal
from .models import DeviceError
from .registry import DeviceRegistry

LOG = logging.getLogger("cosd.devices.http")

_DEVICE_PATH = re.compile(
    r"^/v1/devices(?:/(?P<device_id>[a-f0-9]{32}))?"
    r"(?:/(?P<action>disable|enable|revoke|recover-primary|credentials|credentials/rotate|credentials/revoke))?$"
)

_CREATE_FIELDS = {
    "display_name",
    "device_type",
    "platform",
    "owner_id",
    "device_profile",
    "trust_level",
    "app_version",
    "metadata",
    "issue_credential",
    "credential_expires_at",
}
_PATCH_FIELDS = {"display_name", "device_profile", "trust_level", "app_version", "metadata"}


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


def _actor(principal: Principal) -> str:
    return "local_owner" if principal.is_local_owner else f"device:{principal.device_id}"


def _error(exc: DeviceError) -> tuple[int, dict[str, Any]]:
    return exc.http_status, {"ok": False, "error": str(exc), "error_kind": exc.kind}


def dispatch_device_request(
    handler,
    *,
    registry: DeviceRegistry,
    max_body: int,
    principal: Principal,
) -> tuple[int, dict[str, Any]] | None:
    parsed = urlparse(handler.path)
    path = parsed.path
    method = handler.command
    if path != "/v1/devices" and not path.startswith("/v1/devices/"):
        return None
    try:
        if path == "/v1/devices/bootstrap":
            if method != "POST":
                return 405, {"ok": False, "error": "method not allowed", "error_kind": "method"}
            body = _read_json(handler, max_body)
            _reject_unknown(body, {"confirm", "display_name", "owner_id", "app_version"})
            if body.get("confirm") is not True:
                raise DeviceError("explicit owner confirmation is required")
            device, issued, created = registry.bootstrap_primary_mac(
                confirm=True,
                display_name=str(body.get("display_name") or "Primary Mac"),
                owner_id=str(body.get("owner_id") or "owen"),
                app_version=str(body.get("app_version") or ""),
            )
            response: dict[str, Any] = {
                "ok": True,
                "created": created,
                "device": device.public_dict(),
            }
            if issued is not None:
                response["credential"] = issued.public_dict()
            return (201 if created else 200), response

        match = _DEVICE_PATH.match(path)
        if match is None:
            return 404, {"ok": False, "error": "not found", "error_kind": "not_found"}
        device_id = match.group("device_id")
        action = match.group("action")
        actor = _actor(principal)

        if path == "/v1/devices":
            if method == "GET":
                query = parse_qs(parsed.query)
                result = registry.list_devices(
                    status=(query.get("status") or [None])[0],
                    profile=(query.get("device_profile") or [None])[0],
                    limit=int((query.get("limit") or ["50"])[0]),
                    offset=int((query.get("offset") or ["0"])[0]),
                )
                return 200, {"ok": True, **result}
            if method == "POST":
                body = _read_json(handler, max_body)
                _reject_unknown(body, _CREATE_FIELDS)
                display_name = body.get("display_name")
                if not isinstance(display_name, str):
                    raise DeviceError("display_name is required")
                device, issued = registry.register_device(
                    display_name=display_name,
                    device_type=str(body.get("device_type") or "other"),
                    platform=str(body.get("platform") or "unknown"),
                    owner_id=str(body.get("owner_id") or "unassigned"),
                    device_profile=str(body.get("device_profile") or "capture_only"),
                    trust_level=body.get("trust_level"),
                    app_version=str(body.get("app_version") or ""),
                    metadata=body.get("metadata"),
                    is_primary_owner=False,
                    issue_credential=body.get("issue_credential", True) is not False,
                    credential_expires_at=body.get("credential_expires_at"),
                    actor=actor,
                )
                response = {"ok": True, "device": device.public_dict()}
                if issued is not None:
                    # Only metadata leaves the daemon. The secret stays in Keychain.
                    response["credential"] = issued.public_dict()
                return 201, response
            return 405, {"ok": False, "error": "method not allowed", "error_kind": "method"}

        if device_id is None:
            return 404, {"ok": False, "error": "not found", "error_kind": "not_found"}

        if action is None:
            if method == "GET":
                return 200, {"ok": True, "device": registry.get_device(device_id).public_dict()}
            if method == "PATCH":
                body = _read_json(handler, max_body)
                _reject_unknown(body, _PATCH_FIELDS)
                if not body:
                    raise DeviceError("no update fields supplied")
                current = registry.get_device(device_id)
                if "display_name" in body:
                    registry.rename_device(device_id, body["display_name"], actor=actor)
                if "device_profile" in body or "trust_level" in body:
                    registry.change_profile(
                        device_id,
                        body.get("device_profile", current.device_profile),
                        trust_level=body.get("trust_level"),
                        actor=actor,
                    )
                if "metadata" in body or "app_version" in body:
                    registry.update_metadata(
                        device_id,
                        body.get("metadata", current.metadata),
                        app_version=body.get("app_version", current.app_version),
                        actor=actor,
                    )
                return 200, {"ok": True, "device": registry.get_device(device_id).public_dict()}
            if method == "DELETE":
                result = registry.remove_device(device_id, actor=actor)
                return 200, {"ok": True, **result}
            return 405, {"ok": False, "error": "method not allowed", "error_kind": "method"}

        if action in ("disable", "enable", "revoke", "recover-primary"):
            if method != "POST":
                return 405, {"ok": False, "error": "method not allowed", "error_kind": "method"}
            body = _read_json(handler, max_body)
            if action == "disable":
                _reject_unknown(body, set())
                device = registry.disable_device(device_id, actor=actor)
            elif action == "enable":
                _reject_unknown(body, set())
                device = registry.enable_device(device_id, actor=actor)
            elif action == "revoke":
                _reject_unknown(body, {"reason"})
                device = registry.revoke_device(
                    device_id, actor=actor, reason=str(body.get("reason") or "")
                )
            else:
                _reject_unknown(body, {"confirm_phrase"})
                device = registry.release_primary_protection(
                    device_id,
                    confirm_phrase=str(body.get("confirm_phrase") or ""),
                    actor=actor,
                )
            return 200, {"ok": True, "device": device.public_dict()}

        if action == "credentials":
            if method != "GET":
                return 405, {"ok": False, "error": "method not allowed", "error_kind": "method"}
            return 200, {
                "ok": True,
                "device_id": device_id,
                "credentials": registry.list_credentials(device_id),
            }

        if action == "credentials/rotate":
            if method != "POST":
                return 405, {"ok": False, "error": "method not allowed", "error_kind": "method"}
            body = _read_json(handler, max_body)
            _reject_unknown(body, {"credential_id"})
            credential = registry.rotate_credential(
                device_id, body.get("credential_id"), actor=actor
            )
            return 200, {"ok": True, "credential": credential}

        if action == "credentials/revoke":
            if method != "POST":
                return 405, {"ok": False, "error": "method not allowed", "error_kind": "method"}
            body = _read_json(handler, max_body)
            _reject_unknown(body, {"credential_id", "reason"})
            result = registry.revoke_credential(
                device_id, body.get("credential_id"), actor=actor
            )
            return 200, {"ok": True, "credential": result}

        return 404, {"ok": False, "error": "not found", "error_kind": "not_found"}
    except DeviceError as exc:
        return _error(exc)
    except ValueError as exc:
        return 400, {"ok": False, "error": str(exc), "error_kind": "usage"}
    except Exception:  # noqa: BLE001 - never leak internals
        LOG.exception("device API failure")
        return 500, {"ok": False, "error": "internal error", "error_kind": "internal"}
