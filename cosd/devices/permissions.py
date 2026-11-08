"""Granular permissions and the profile matrix (ADR-021).

Profiles are fixed sets of permissions. Nothing inherits from owner: a school
or partner device only holds what its profile lists here. Unknown profiles and
unknown permissions fail closed (empty set / False).
"""

from __future__ import annotations

from .models import PROFILES

# Granular permissions. `ask` is included because asking the model is a
# capability in its own right; it is not the same as task capture or execution.
PERMISSIONS = (
    "ask",
    "status.read",
    "tasks.read",
    "tasks.create",
    "tasks.edit",
    "tasks.cancel",
    "tasks.retry",
    "tasks.execute",
    "history.read",
    "sessions.read",
    "sessions.create",
    "runtime.manage",
    "devices.read",
    "devices.manage",
    "credentials.manage",
)

ALL_PERMISSIONS = frozenset(PERMISSIONS)

PROFILE_PERMISSIONS: dict[str, frozenset[str]] = {
    # Full authorized control of the local owner context.
    "owner": ALL_PERMISSIONS,
    # Approved personal workflows. No daemon administration, no device admin.
    "personal": frozenset(
        {
            "ask",
            "status.read",
            "tasks.read",
            "tasks.create",
            "tasks.edit",
            "tasks.cancel",
            "tasks.retry",
            "tasks.execute",
            "history.read",
            "sessions.read",
            "sessions.create",
        }
    ),
    # Explicitly shared capabilities only. No private personal history,
    # no task execution, no administration.
    "partner": frozenset(
        {
            "ask",
            "status.read",
            "tasks.read",
            "tasks.create",
        }
    ),
    # Restricted school workflows: capture + restricted ask + status only.
    # No task listing (cross-device exposure), no history, no execution,
    # no device administration, no master credential distribution.
    "school": frozenset(
        {
            "ask",
            "status.read",
            "tasks.create",
        }
    ),
    # Permitted status and task history only; never mutates records.
    "read_only": frozenset(
        {
            "status.read",
            "tasks.read",
            "history.read",
        }
    ),
    # Create tasks without asking, reading, editing, or executing.
    "capture_only": frozenset(
        {
            "status.read",
            "tasks.create",
        }
    ),
    # No access at all.
    "revoked": frozenset(),
}

# Operations that must be denied while the cos kill switch is set for a
# device principal. The trusted local owner keeps the existing downstream
# policy behaviour (for example /v1/ask returns 503 from run_ask).
KILL_SWITCH_SENSITIVE = frozenset(
    {
        "ask",
        "tasks.create",
        "tasks.edit",
        "tasks.cancel",
        "tasks.retry",
        "tasks.execute",
    }
)


def permissions_for(profile: str) -> frozenset[str]:
    """The permission set for a profile. Unknown profiles get nothing."""
    return PROFILE_PERMISSIONS.get(profile, frozenset())


def has_permission(profile: str, permission: str) -> bool:
    if permission not in ALL_PERMISSIONS:
        return False
    return permission in permissions_for(profile)


def all_profiles() -> tuple[str, ...]:
    return PROFILES
