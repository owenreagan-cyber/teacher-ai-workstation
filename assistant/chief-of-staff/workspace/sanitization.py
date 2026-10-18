"""Pure cloud-view projection for synthetic records; performs no I/O."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


class SanitizationError(ValueError):
    """Raised when a record cannot safely produce a cloud-view candidate."""


def _is_absolute_or_escaping_path(value: str) -> bool:
    parts = value.replace("\\", "/").split("/")
    return value.startswith(("/", "~/")) or ".." in parts


def _filter_value(value: Any, blocked_fields: set[str]) -> Any:
    if isinstance(value, Mapping):
        clean: dict[str, Any] = {}
        for key, child in value.items():
            if key in blocked_fields:
                continue
            if isinstance(child, str) and _is_absolute_or_escaping_path(child):
                continue
            clean[key] = _filter_value(child, blocked_fields)
        return clean
    if isinstance(value, list):
        return [_filter_value(item, blocked_fields) for item in value]
    return value


def sanitize_for_cloud(
    record: Mapping[str, Any],
    policy: Mapping[str, Any],
    *,
    allow_relative_path: bool = False,
) -> dict[str, Any]:
    """Build a candidate projection without transmitting or persisting it.

    Phase C keeps cloud access disabled. This helper exists only so policy
    behavior can be tested against fictional dictionaries.
    """

    classification = record.get("classification", {})
    sensitivity = (
        classification.get("data_sensitivity")
        if isinstance(classification, Mapping)
        else "unknown"
    )
    blocked_sensitivities = {"student_private", "restricted", "unknown"}
    if sensitivity in blocked_sensitivities:
        raise SanitizationError(f"blocked sensitivity: {sensitivity}")

    allowed = set(policy["allowed_projection_fields"])
    blocked = set(policy["local_only_fields"]) | set(
        policy["forbidden_export_fields"]
    )
    projection: dict[str, Any] = {}
    for key, value in record.items():
        output_key = "source" if key == "source_id" else key
        if key in blocked or output_key not in allowed:
            continue
        if output_key == "relative_path":
            if not allow_relative_path:
                continue
            if not isinstance(value, str) or _is_absolute_or_escaping_path(value):
                raise SanitizationError("relative path is absolute or escapes its source")
        projection[output_key] = _filter_value(value, blocked)
    return projection
