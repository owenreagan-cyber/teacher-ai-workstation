"""Central authorization for device principals and the trusted local owner."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from .credentials import CredentialInvalid, CredentialProviderError
from .models import DeviceError
from .permissions import ALL_PERMISSIONS, KILL_SWITCH_SENSITIVE, permissions_for
from .registry import DeviceRegistry

LOG = logging.getLogger("cosd.devices.authorization")


@dataclass(frozen=True)
class Principal:
    kind: str  # "local_owner" | "device"
    device_id: str | None
    profile: str
    permissions: frozenset[str]
    credential_id: str | None = None

    @property
    def is_local_owner(self) -> bool:
        return self.kind == "local_owner"


LOCAL_OWNER_PRINCIPAL = Principal(
    kind="local_owner",
    device_id=None,
    profile="owner",
    permissions=permissions_for("owner"),
    credential_id=None,
)


class DeviceAuthenticationError(Exception):
    """Invalid or unavailable device authentication. Never falls back to master."""

    def __init__(self, message: str, *, reason: str = "invalid", unavailable: bool = False):
        super().__init__(message)
        self.reason = reason
        self.unavailable = unavailable


class AuthorizationDenied(Exception):
    def __init__(
        self,
        permission: str,
        reason: str,
        *,
        device_id: str | None = None,
        profile: str | None = None,
    ):
        super().__init__(f"denied {permission}: {reason}")
        self.permission = permission
        self.reason = reason
        self.device_id = device_id
        self.profile = profile


class DeviceAuthorizationService:
    """Evaluates identity, status, credential, profile, permission, and kill switch."""

    def __init__(
        self,
        registry: DeviceRegistry,
        *,
        kill_switch=None,
        audit=None,
    ) -> None:
        self.registry = registry
        self.credentials = registry.credentials
        self.kill_switch = kill_switch
        self._audit = audit

    # ------------------------------------------------------------ authentication

    def authenticate_device_token(self, token: str) -> Principal:
        if not isinstance(token, str) or not token.strip():
            self._audit_failure(device_id="unknown", credential_id=None, reason="missing")
            raise DeviceAuthenticationError("missing device credential", reason="missing")
        token = token.strip()
        try:
            verification = self.credentials.verify_token(token)
        except CredentialInvalid as exc:
            credential_id = token.split(".", 1)[0] if "." in token else None
            self._audit_failure(
                device_id="unknown", credential_id=credential_id, reason=exc.reason
            )
            raise DeviceAuthenticationError(
                "invalid device credential", reason=exc.reason
            ) from exc
        except CredentialProviderError as exc:
            credential_id = token.split(".", 1)[0] if "." in token else None
            self._audit_failure(
                device_id="unknown",
                credential_id=credential_id,
                reason="credential_store_unavailable",
            )
            raise DeviceAuthenticationError(
                "credential store unavailable", reason="credential_store_unavailable", unavailable=True
            ) from exc

        try:
            device = self.registry.get_device(verification.device_id)
        except DeviceError:
            self._audit_failure(
                device_id=verification.device_id,
                credential_id=verification.credential_id,
                reason="device_not_found",
            )
            raise DeviceAuthenticationError("invalid device credential", reason="device_not_found")

        if device.status != "active":
            reason = f"device_{device.status}"
            self._audit_failure(
                device_id=device.device_id,
                credential_id=verification.credential_id,
                reason=reason,
                profile=device.device_profile,
            )
            raise DeviceAuthenticationError("device is not active", reason=reason)
        if device.device_profile == "revoked":
            self._audit_failure(
                device_id=device.device_id,
                credential_id=verification.credential_id,
                reason="profile_revoked",
                profile=device.device_profile,
            )
            raise DeviceAuthenticationError("device is revoked", reason="profile_revoked")

        principal = Principal(
            kind="device",
            device_id=device.device_id,
            profile=device.device_profile,
            permissions=permissions_for(device.device_profile),
            credential_id=verification.credential_id,
        )
        try:
            self.registry.record_auth_event(
                "device.auth_ok",
                device_id=device.device_id,
                result="ok",
                profile=device.device_profile,
                credential_id=verification.credential_id,
            )
        except DeviceError as exc:
            # An authenticated request that cannot be audited fails closed.
            LOG.error("device auth audit unavailable: %s", exc)
            raise DeviceAuthenticationError(
                "security audit unavailable", reason="audit_unavailable", unavailable=True
            ) from exc
        except Exception as exc:  # noqa: BLE001 - database/audit outage
            LOG.error("device auth audit unavailable: %s", exc)
            raise DeviceAuthenticationError(
                "security audit unavailable", reason="audit_unavailable", unavailable=True
            ) from exc
        self.registry.touch_last_seen(device.device_id)
        return principal

    # ------------------------------------------------------------ authorization

    def authorize(self, principal: Principal, permission: str) -> None:
        if permission not in ALL_PERMISSIONS:
            self._deny(principal, permission, "unknown_permission")
        if principal.is_local_owner:
            # The trusted local owner keeps the master-token behaviour. The
            # existing downstream policy gate still enforces the kill switch.
            if permission not in LOCAL_OWNER_PRINCIPAL.permissions:
                self._deny(principal, permission, "not_permitted")
            return

        if principal.device_id is None or principal.credential_id is None:
            self._deny(principal, permission, "ambiguous_identity")
        try:
            device = self.registry.get_device(principal.device_id)
        except DeviceError:
            self._deny(principal, permission, "device_not_found")
        if device.status != "active":
            self._deny(principal, permission, f"device_{device.status}", device=device)
        if device.device_profile == "revoked":
            self._deny(principal, permission, "profile_revoked", device=device)
        if not self.credentials.active_for_device(principal.credential_id, device.device_id):
            self._deny(principal, permission, "credential_not_active", device=device)
        if permission not in permissions_for(device.device_profile):
            self._deny(principal, permission, "profile_does_not_grant", device=device)
        if permission in KILL_SWITCH_SENSITIVE and self.kill_switch is not None:
            try:
                stopped = self.kill_switch.is_set()
            except Exception:  # noqa: BLE001 - cannot tell -> stopped
                stopped = True
            if stopped:
                self._deny(principal, permission, "kill_switch", device=device)

    # ------------------------------------------------------------------ helpers

    def _deny(
        self,
        principal: Principal,
        permission: str,
        reason: str,
        *,
        device=None,
    ) -> None:
        device_id = device.device_id if device is not None else principal.device_id
        profile = device.device_profile if device is not None else principal.profile
        try:
            self.registry.record_auth_event(
                "authorization.denied",
                device_id=device_id or "local_owner",
                result="denied",
                reason=reason,
                profile=profile,
                credential_id=principal.credential_id,
            )
        except DeviceError as exc:
            LOG.error("could not audit authorization denial: %s", exc)
        except Exception as exc:  # noqa: BLE001 - database outage
            LOG.error("could not audit authorization denial: %s", exc)
        raise AuthorizationDenied(
            permission, reason, device_id=device_id, profile=profile
        )

    def _audit_failure(
        self,
        *,
        device_id: str,
        credential_id: str | None,
        reason: str,
        profile: str | None = None,
    ) -> None:
        try:
            self.registry.record_auth_event(
                "device.auth_failed",
                device_id=device_id,
                result="denied",
                reason=reason,
                profile=profile,
                credential_id=credential_id,
            )
        except DeviceError as exc:
            LOG.error("could not audit device authentication failure: %s", exc)
        except Exception as exc:  # noqa: BLE001 - database outage
            LOG.error("could not audit device authentication failure: %s", exc)
