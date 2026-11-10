"""Durable execution checkpoints."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

MAX_CHECKPOINT_BYTES = 16_384


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def _validate(data: dict) -> str:
    raw = json.dumps(data, separators=(",", ":"), sort_keys=True)
    if len(raw.encode("utf-8")) > MAX_CHECKPOINT_BYTES:
        raise ValueError("checkpoint too large")
    return raw


def write_checkpoint(
    conn,
    *,
    task_id: str,
    attempt_id: int,
    checkpoint_key: str,
    data: dict,
) -> dict[str, Any]:
    if not checkpoint_key or len(checkpoint_key) > 64:
        raise ValueError("invalid checkpoint_key")
    payload = _validate(data)
    now = _utc_now()
    conn.execute(
        """INSERT INTO execution_checkpoints(
            task_id, attempt_id, checkpoint_key, checkpoint_json, created_at
        ) VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(attempt_id, checkpoint_key) DO UPDATE SET
            checkpoint_json = excluded.checkpoint_json,
            created_at = excluded.created_at""",
        (task_id, attempt_id, checkpoint_key, payload, now),
    )
    return {"checkpoint_key": checkpoint_key, "created_at": now}


def latest_checkpoint_db(db, *, attempt_id: int, checkpoint_key: str) -> dict | None:
    row = db.query_one(
        """SELECT checkpoint_json FROM execution_checkpoints
           WHERE attempt_id = ? AND checkpoint_key = ?""",
        (attempt_id, checkpoint_key),
    )
    if not row:
        return None
    return json.loads(row["checkpoint_json"])


def list_checkpoints_db(db, task_id: str) -> list[dict[str, Any]]:
    rows = db.query_all(
        """SELECT id, attempt_id, checkpoint_key, checkpoint_json, created_at
           FROM execution_checkpoints WHERE task_id = ? ORDER BY id ASC""",
        (task_id,),
    )
    return [
        {
            "id": r["id"],
            "attempt_id": r["attempt_id"],
            "checkpoint_key": r["checkpoint_key"],
            "data": json.loads(r["checkpoint_json"]),
            "created_at": r["created_at"],
        }
        for r in rows
    ]
