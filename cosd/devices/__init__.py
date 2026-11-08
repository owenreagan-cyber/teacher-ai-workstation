"""Persistent local device registry and credential foundation (P1b.4b).

This package is deliberately local-only. It does not open a network listener,
does not pair devices, and does not issue credentials to remote clients. The
existing loopback master token remains authoritative for local clients.
"""

from .authorization import (
    LOCAL_OWNER_PRINCIPAL,
    AuthorizationDenied,
    DeviceAuthenticationError,
    DeviceAuthorizationService,
    Principal,
)
from .credentials import (
    CredentialProvider,
    CredentialProviderError,
    CredentialService,
    IssuedCredential,
    KeychainCredentialProvider,
    MemoryCredentialProvider,
    default_credential_provider,
)
from .models import DeviceError, DeviceRecord
from .permissions import PERMISSIONS, PROFILE_PERMISSIONS, has_permission, permissions_for
from .registry import DeviceRegistry

__all__ = [
    "AuthorizationDenied",
    "CredentialProvider",
    "CredentialProviderError",
    "CredentialService",
    "DeviceAuthenticationError",
    "DeviceAuthorizationService",
    "DeviceError",
    "DeviceRecord",
    "DeviceRegistry",
    "IssuedCredential",
    "KeychainCredentialProvider",
    "LOCAL_OWNER_PRINCIPAL",
    "MemoryCredentialProvider",
    "PERMISSIONS",
    "PROFILE_PERMISSIONS",
    "Principal",
    "default_credential_provider",
    "has_permission",
    "permissions_for",
]
