"""Durable event store for SourceChangeEvents with lifecycle + resolution.

Persists the lifecycle state (DETECTED → … → RESOLVED/APPROVED/IGNORED/BLOCKED)
under ``.local/canvas-planner/agent/`` (gitignored). Deduplicates repeated
observations of the same underlying change by stable ``event_id``; a resolved or
ignored event stays visible but is not re-notified, while a genuinely new change
(different old/new values) gets a new identity.

Teacher overrides are persisted as resolution records so an explicit owner
instruction outranks subsequent ordinary source refreshes until Owen changes it.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import snapshot as snap
from .models import (
    EVENT_APPROVED,
    EVENT_BLOCKED,
    EVENT_DETECTED,
    EVENT_IGNORED,
    EVENT_PLAN_UPDATED,
    EVENT_RESOLVED,
    SourceChangeEvent,
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def events_path(quarter: int, week: int) -> Path:
    return snap._week_dir(quarter, week) / "events.json"


class EventStore:
    """Load/record/resolve durable change events for one week."""

    def __init__(self, quarter: int, week: int) -> None:
        self.quarter = quarter
        self.week = week

    def load(self) -> list[dict[str, Any]]:
        path = events_path(self.quarter, self.week)
        if not path.exists():
            return []
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []
        return data if isinstance(data, list) else []

    def save(self, records: list[dict[str, Any]]) -> None:
        path = events_path(self.quarter, self.week)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(records, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        import os
        os.replace(tmp, path)

    def record(self, events: list[SourceChangeEvent]) -> dict[str, Any]:
        """Dedup + persist incoming events. Returns {added, total, skipped}."""
        records = self.load()
        by_id = {r.get("event_id"): r for r in records if r.get("event_id")}
        added = 0
        skipped = 0
        for event in events:
            eid = event.event_id or _stable_id(event)
            event.event_id = eid
            if eid in by_id:
                existing = by_id[eid]
                # Same identity + old/new -> same underlying change. If already
                # resolved/approved/ignored, keep it (visible, not re-notified).
                skipped += 1
                continue
            record = event.to_dict()
            record.setdefault("resolution_status", EVENT_DETECTED)
            record.setdefault("notification_status", "pending")
            record.setdefault("detected_at", event.timestamp)
            records.append(record)
            by_id[eid] = record
            added += 1
        self.save(records)
        return {"added": added, "total": len(records), "skipped": skipped}

    def resolve(self, event_id: str, *, action: str, actor: str = "owner") -> dict[str, Any] | None:
        """Record a resolution action against an event."""
        records = self.load()
        target = next((r for r in records if r.get("event_id") == event_id), None)
        if target is None:
            return None
        status = _action_to_status(action)
        target["resolution_status"] = status
        target["resolved_by"] = actor
        target["resolved_at"] = _now()
        target["resolution_action"] = action
        if action == "override_keep_current":
            target["teacher_override"] = {
                "subject": target.get("subject"),
                "keep": target.get("old_value"),
                "authority": "OWNER_INSTRUCTION",
                "at": _now(),
            }
        self.save(records)
        return target

    def unresolved(self) -> list[dict[str, Any]]:
        records = self.load()
        return [r for r in records if r.get("resolution_status") in (EVENT_DETECTED, None)]

    def all(self) -> list[dict[str, Any]]:
        return self.load()

    def supersede(
        self, *, classification: str, object_identities: set[str], except_ids: set[str]
    ) -> int:
        """Mark prior unresolved events of a classification+identity as superseded.

        Used for cross-source conflicts so that a *materially changed* version of
        the same disagreement supersedes the older version (one active conflict
        per identity), while an identical re-observation simply dedups.
        """
        records = self.load()
        changed = 0
        for r in records:
            if r.get("classification") != classification:
                continue
            if r.get("object_identity") not in object_identities:
                continue
            if r.get("event_id") in except_ids:
                continue
            if r.get("resolution_status") not in (EVENT_DETECTED, None):
                continue
            r["resolution_status"] = EVENT_RESOLVED
            r["resolution_action"] = "superseded"
            r["resolved_by"] = "system"
            r["resolved_at"] = _now()
            changed += 1
        if changed:
            self.save(records)
        return changed


def _stable_id(event: SourceChangeEvent) -> str:
    import hashlib
    body = "|".join([
        str(event.week_id), str(event.source), str(event.subject),
        str(event.classification), str(event.object_identity),
        str(event.old_value), str(event.new_value),
    ])
    return hashlib.sha256(body.encode("utf-8")).hexdigest()[:20]


def _action_to_status(action: str) -> str:
    return {
        "approve_updates": EVENT_APPROVED,
        "keep_current": EVENT_RESOLVED,
        "override_keep_current": EVENT_RESOLVED,
        "prepare_plan": EVENT_PLAN_UPDATED,
        "ignore": EVENT_IGNORED,
        "block": EVENT_BLOCKED,
    }.get(action, EVENT_RESOLVED)


def command_self_test() -> int:
    import tempfile
    import scripts.weekly_planner_agent.snapshot as snapmod
    tmp = Path(tempfile.mkdtemp())
    orig = snapmod.agent_root
    snapmod.agent_root = lambda: tmp
    try:
        store = EventStore(2, 3)
        ev = SourceChangeEvent(
            source="pacing", subject="math", object_type="assessment_date",
            old_value="2026-11-05", new_value="2026-11-06",
            classification="assessment_date_changed", object_identity="math|Thursday",
            week_id="Q2W3",
        )
        ev.event_id = "e1"
        r1 = store.record([ev])
        assert r1["added"] == 1
        # Duplicate observation -> dedup (no duplicate notification).
        r2 = store.record([ev])
        assert r2["added"] == 0 and r2["skipped"] == 1
        assert len(store.unresolved()) == 1
        # Resolve.
        store.resolve("e1", action="override_keep_current")
        assert store.all()[0]["teacher_override"]["authority"] == "OWNER_INSTRUCTION"
        assert len(store.unresolved()) == 0
        # A genuinely new change (different new value) -> new identity.
        ev2 = SourceChangeEvent(
            source="pacing", subject="math", object_type="assessment_date",
            old_value="2026-11-05", new_value="2026-11-07",
            classification="assessment_date_changed", object_identity="math|Thursday",
            week_id="Q2W3",
        )
        ev2.event_id = "e2"
        store.record([ev2])
        assert len(store.all()) == 2
    finally:
        snapmod.agent_root = orig
    print("PASS weekly-planner-agent event-store self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(command_self_test())
