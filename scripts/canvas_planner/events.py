"""Append-only local event history for Canvas Planner actions."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def event_path(week_dir: Path) -> Path:
    return week_dir / "planner" / "events.jsonl"


def append_event(
    week_dir: Path,
    *,
    action: str,
    actor: str,
    reason: str,
    before: Any = None,
    after: Any = None,
    undo: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Append one auditable event and return it."""
    event = {
        "event_id": str(uuid.uuid4()),
        "at": _now(),
        "action": action,
        "actor": actor,
        "reason": reason,
        "before": before,
        "after": after,
        "undo": undo,
    }
    path = event_path(week_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
    return event


def read_events(week_dir: Path) -> list[dict[str, Any]]:
    path = event_path(week_dir)
    if not path.exists():
        return []
    events: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            events.append(value)
    return events
