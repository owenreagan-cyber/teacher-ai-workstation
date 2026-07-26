from __future__ import annotations

import os
from typing import Any


class MutationNotAllowedError(RuntimeError):
    """Raised whenever any Phase 27 transport is asked to perform a mutating
    Canvas operation. Phase 27 is read-only and preview-only; no transport in
    this module may ever complete a mutating request."""


class TransportError(RuntimeError):
    """Normalized transport error (network failure, bad host, disabled mode)."""


_MUTATING_METHODS = (
    "create_page",
    "update_page",
    "delete_page",
    "create_assignment",
    "update_assignment",
    "delete_assignment",
    "create_module",
    "update_module",
    "create_module_item",
    "update_module_item",
    "create_announcement",
    "upload_file",
    "publish_object",
)

_MUTATING_HTTP_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


class _MutationRejectingMixin:
    """Every mutating method on any Phase 27 transport raises unconditionally.
    Defined once so every transport class inherits identical, unbypassable
    rejection behavior rather than each reimplementing (and potentially
    forgetting) the same guard."""

    def request(self, method: str, url: str, **kwargs: Any) -> Any:
        if method.upper() in _MUTATING_HTTP_METHODS:
            raise MutationNotAllowedError(
                f"HTTP method {method.upper()} is not allowed by Phase 27 transports"
            )
        return self._get(method, url, **kwargs)

    def _get(self, method: str, url: str, **kwargs: Any) -> Any:  # pragma: no cover - overridden
        raise NotImplementedError


def _install_mutation_rejections(cls: type) -> type:
    def _make_rejector(name: str):
        def _rejected(self, *_args: Any, **_kwargs: Any) -> None:
            raise MutationNotAllowedError(
                f"{name} is not allowed: Phase 27 transports are read-only and preview-only"
            )

        return _rejected

    for method_name in _MUTATING_METHODS:
        setattr(cls, method_name, _make_rejector(method_name))
    return cls


@_install_mutation_rejections
class DisabledCanvasTransport(_MutationRejectingMixin):
    """Default Phase 27 transport. Every network call, mutating or not, is
    rejected. This is the transport used unless a caller explicitly opts into
    one of the other transports below."""

    def _get(self, method: str, url: str, **kwargs: Any) -> Any:
        raise TransportError("DisabledCanvasTransport permits no requests of any kind")


@_install_mutation_rejections
class SnapshotCanvasTransport(_MutationRejectingMixin):
    """Serves GET-shaped reads from an already-loaded, validated CanvasSnapshot.
    Never makes a network call."""

    def __init__(self, snapshot: Any) -> None:
        self._snapshot = snapshot

    def _get(self, method: str, url: str, **kwargs: Any) -> list[dict[str, Any]]:
        course_ref = kwargs.get("course_ref")
        if course_ref is not None:
            return self._snapshot.objects_for_course(course_ref)
        return list(self._snapshot.remoteObjects)


@_install_mutation_rejections
class FakeCanvasTransport(_MutationRejectingMixin):
    """In-memory test double for exercising transport-boundary tests without
    touching real fixtures. Read-only by construction; mutation methods are
    rejected identically to every other Phase 27 transport."""

    def __init__(self, canned_responses: dict[str, Any] | None = None) -> None:
        self._canned = canned_responses or {}
        self.calls: list[tuple[str, str]] = []

    def _get(self, method: str, url: str, **kwargs: Any) -> Any:
        self.calls.append((method.upper(), url))
        return self._canned.get(url, {})


REQUIRED_LIVE_READ_ONLY_GATES = (
    "command_flag",
    "environment_mode",
    "approved_host",
    "get_only",
)


@_install_mutation_rejections
class OptionalReadOnlyCanvasTransport(_MutationRejectingMixin):
    """Gated, disabled-by-default live read-only transport. Every gate in
    REQUIRED_LIVE_READ_ONLY_GATES must be explicitly satisfied or this
    transport refuses to make any request and falls back to disabled
    behavior. No code path in this class performs a live HTTP request as
    part of this mission; `_get` always raises until all gates are wired to
    a real, reviewed implementation."""

    def __init__(
        self,
        allow_live_read_only_flag: bool = False,
        approved_hosts: tuple[str, ...] = (),
    ) -> None:
        self._allow_live_read_only_flag = allow_live_read_only_flag
        self._approved_hosts = approved_hosts

    def _gates_satisfied(self, url: str) -> list[str]:
        satisfied = []
        if self._allow_live_read_only_flag:
            satisfied.append("command_flag")
        if os.environ.get("CANVAS_ACCESS_MODE") == "read-only":
            satisfied.append("environment_mode")
        if self._approved_hosts and any(host in url for host in self._approved_hosts):
            satisfied.append("approved_host")
        satisfied.append("get_only")  # enforced structurally by _MutationRejectingMixin
        return satisfied

    def _get(self, method: str, url: str, **kwargs: Any) -> Any:
        satisfied = set(self._gates_satisfied(url))
        missing = [g for g in REQUIRED_LIVE_READ_ONLY_GATES if g not in satisfied]
        if missing:
            raise TransportError(
                "live read-only transport disabled: missing gates " + ", ".join(missing)
            )
        raise TransportError(
            "live read-only transport is not wired to a network implementation "
            "in this mission; no live Canvas request may occur"
        )
