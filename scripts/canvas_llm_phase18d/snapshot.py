"""Read-only live Canvas snapshot model and validation (Phase 18D).

Pure data handling only. Snapshot *capture* against the real read-only connector
is intentionally kept out of this import-safe module: a future execution phase
may implement it, but the contracts and diff logic here must never transitively
load any Canvas execution modules.

Snapshot data is supplied by the caller (tests, fixtures, or a future
read-only adapter). This module validates that supplied snapshot is well-formed
so malformed live responses fail closed instead of being guessed at.
"""

from __future__ import annotations

from typing import Any

from scripts.canvas_llm_phase27.canonicalize import canonical_hash

from .contracts import CanvasSnapshot, SnapshotObject

_VALID_OBJECT_TYPES = {"agenda_page", "assignment", "announcement"}
_REQUIRED_OBJECT_FIELDS = {"object_id", "object_type", "course", "locator", "title"}


def snapshot_from_dicts(week_code: str, snapshot_id: str, objects: list[dict[str, Any]], **kwargs: Any) -> CanvasSnapshot:
    """Build a CanvasSnapshot from plain dicts (test/fixture convenience)."""
    parsed = [SnapshotObject(**obj) for obj in objects]
    return CanvasSnapshot(week_code=week_code, snapshot_id=snapshot_id, objects=parsed, **kwargs)


def validate_snapshot(snapshot: CanvasSnapshot) -> list[str]:
    """Return structural errors for a snapshot; empty list means well-formed."""
    errors: list[str] = []
    if not snapshot.week_code:
        errors.append("snapshot missing week_code")
    if not snapshot.snapshot_id:
        errors.append("snapshot missing snapshot_id")
    seen_ids: set[str] = set()
    for i, obj in enumerate(snapshot.objects):
        for key in _REQUIRED_OBJECT_FIELDS:
            if not str(getattr(obj, key, "") or "").strip():
                errors.append(f"snapshot object {i} missing {key!r}")
        if obj.object_type not in _VALID_OBJECT_TYPES:
            errors.append(f"snapshot object {i} has invalid object_type {obj.object_type!r}")
        if not isinstance(obj.current_state, dict):
            errors.append(f"snapshot object {i} current_state is not a dict")
        if obj.object_id in seen_ids:
            errors.append(f"snapshot object {i} duplicates object_id {obj.object_id!r}")
        seen_ids.add(obj.object_id)
    return errors


def snapshot_hash(snapshot: CanvasSnapshot) -> str:
    """Deterministic semantic hash of a snapshot (order-independent across objects)."""
    payload = [o.to_dict() for o in sorted(snapshot.objects, key=lambda o: (o.course, o.object_type, o.locator))]
    return canonical_hash({"week_code": snapshot.week_code, "objects": payload})
