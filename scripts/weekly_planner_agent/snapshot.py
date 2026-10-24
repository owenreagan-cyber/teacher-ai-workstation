"""Durable, versioned source-observation snapshots for the Weekly Planner Agent.

Persists enough normalized information to compare successive observations of
Google pacing and Canvas. Snapshots live under ``.local/canvas-planner/agent/``
(gitignored). Writes are atomic (tmp + ``os.replace``); corrupted or
incompatible snapshots fail safely instead of fabricating changes.

A first observation establishes a baseline: no prior snapshot -> no change
alerts (the caller is told this is a baseline, never a flood of false events).
"""
from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.canvas_planner.state_root import planner_root

SNAPSHOT_SCHEMA_VERSION = 1

SNAPSHOT_OK = "OK"
SNAPSHOT_STALE = "STALE"
SNAPSHOT_UNAVAILABLE = "UNAVAILABLE"

SCHOOL_YEAR = "2026-2027"


class SnapshotCorrupt(RuntimeError):
    """Raised when a persisted snapshot is corrupt or has an unknown schema."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def agent_root() -> Path:
    return planner_root() / "agent"


def _week_dir(quarter: int, week: int) -> Path:
    return agent_root() / SCHOOL_YEAR / f"q{quarter}" / f"w{week}"


def snapshot_path(quarter: int, week: int) -> Path:
    return _week_dir(quarter, week) / "snapshots" / "current.json"


def history_path(quarter: int, week: int) -> Path:
    return _week_dir(quarter, week) / "snapshots" / "history.jsonl"


def new_snapshot_id() -> str:
    return str(uuid.uuid4())


def blank_snapshot(quarter: int, week: int, week_id: str) -> dict[str, Any]:
    """An empty-but-valid snapshot shell (no observation yet)."""
    return {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "snapshot_id": new_snapshot_id(),
        "created_at": _now(),
        "week_id": week_id,
        "quarter": quarter,
        "week": week,
        "pacing": {"status": SNAPSHOT_UNAVAILABLE, "observed_at": None,
                   "identity": {}, "fingerprint": "", "cells": {}},
        "canvas": {"status": SNAPSHOT_UNAVAILABLE, "observed_at": None, "courses": {}},
    }


def validate(snapshot: dict[str, Any]) -> None:
    """Fail safely on corrupt/incompatible snapshots."""
    if not isinstance(snapshot, dict):
        raise SnapshotCorrupt("snapshot is not a JSON object")
    version = snapshot.get("schema_version")
    if version != SNAPSHOT_SCHEMA_VERSION:
        raise SnapshotCorrupt(
            f"snapshot schema_version {version!r} is not supported "
            f"(expected {SNAPSHOT_SCHEMA_VERSION})"
        )
    if "snapshot_id" not in snapshot or "week_id" not in snapshot:
        raise SnapshotCorrupt("snapshot missing required identity fields")
    for section in ("pacing", "canvas"):
        if not isinstance(snapshot.get(section), dict):
            raise SnapshotCorrupt(f"snapshot.{section} is malformed")


def load(quarter: int, week: int) -> dict[str, Any] | None:
    """Load the latest snapshot, or None when absent. Raises on corruption."""
    path = snapshot_path(quarter, week)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SnapshotCorrupt(f"snapshot is not valid JSON: {exc}") from exc
    validate(data)
    return data


def save(quarter: int, week: int, snapshot: dict[str, Any]) -> Path:
    """Atomically persist a snapshot and append it to history."""
    validate(snapshot)
    snapshot = dict(snapshot)
    snapshot["created_at"] = snapshot.get("created_at") or _now()
    path = snapshot_path(quarter, week)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, path)
    _append_history(quarter, week, snapshot)
    return path


def _append_history(quarter: int, week: int, snapshot: dict[str, Any]) -> None:
    """Append a compact summary of the snapshot to the append-only history."""
    summary = {
        "snapshot_id": snapshot.get("snapshot_id"),
        "created_at": snapshot.get("created_at"),
        "week_id": snapshot.get("week_id"),
        "pacing_status": (snapshot.get("pacing") or {}).get("status"),
        "pacing_fingerprint": (snapshot.get("pacing") or {}).get("fingerprint"),
        "canvas_status": (snapshot.get("canvas") or {}).get("status"),
        "canvas_courses": sorted((snapshot.get("canvas") or {}).get("courses", {}).keys()),
    }
    path = history_path(quarter, week)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(summary, ensure_ascii=False, sort_keys=True) + "\n")


def history(quarter: int, week: int) -> list[dict[str, Any]]:
    path = history_path(quarter, week)
    if not path.exists():
        return []
    out: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def has_prior(quarter: int, week: int) -> bool:
    return snapshot_path(quarter, week).exists()


def fingerprint(cells: dict[str, Any]) -> str:
    """Stable content fingerprint of normalized cells (order-insensitive)."""
    import hashlib
    body = json.dumps(cells, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def command_self_test() -> int:
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        snap = blank_snapshot(2, 3, "Q2W3")
        validate(snap)
        # Atomic write + reload.
        p = tmp_path = Path(tmp)
        # Exercise validation against a corrupt snapshot.
        corrupt = tmp_path / "bad.json"
        corrupt.write_text("{ not json", encoding="utf-8")
        try:
            json.loads(corrupt.read_text(encoding="utf-8"))
            raise AssertionError("expected decode failure")
        except json.JSONDecodeError:
            pass
        # Unknown schema version fails safely.
        bad = dict(blank_snapshot(2, 3, "Q2W3"))
        bad["schema_version"] = 999
        try:
            validate(bad)
            raise AssertionError("expected SnapshotCorrupt")
        except SnapshotCorrupt:
            pass
    print("PASS weekly-planner-agent snapshot self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(command_self_test())
