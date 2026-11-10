"""Claim and schedule eligible tasks."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from cos.audit import AuditLog
from cos.config import load_config

from cosd.tasks import TaskRegistry, TaskState, _json_dumps, _utc_now

from .leases import acquire_lease, expire_stale_leases, new_worker_id

QUEUE_META_KEY = "queue_control"


class QueueError(Exception):
    def __init__(self, message: str, *, http_status: int = 400, kind: str = "usage"):
        super().__init__(message)
        self.http_status = http_status
        self.kind = kind


class ExecutionQueue:
    def __init__(self, registry: TaskRegistry):
        self.registry = registry

    def _audit(self, kind: str, **fields) -> None:
        AuditLog(load_config().audit_path)(kind, **fields)

    def is_paused(self) -> bool:
        row = self.registry.db.query_one(
            "SELECT value_json FROM task_metadata WHERE key = ?", (QUEUE_META_KEY,)
        )
        if not row:
            return False
        return bool(json.loads(row["value_json"]).get("paused"))

    def set_paused(self, paused: bool) -> dict[str, Any]:
        now = _utc_now()
        with self.registry.db.transaction() as conn:
            conn.execute(
                """INSERT INTO task_metadata(key, value_json, updated_at) VALUES (?, ?, ?)
                   ON CONFLICT(key) DO UPDATE SET value_json = excluded.value_json, updated_at = excluded.updated_at""",
                (QUEUE_META_KEY, _json_dumps({"paused": paused}), now),
            )
        self._audit("cosd_queue_pause" if paused else "cosd_queue_resume")
        return {"ok": True, "paused": paused}

    def status(self) -> dict[str, Any]:
        counts = self.registry.get_task_counts()
        active = self.registry.db.query_one(
            "SELECT COUNT(*) AS c FROM worker_leases WHERE state = 'active'"
        )["c"]
        return {
            "ok": True,
            "paused": self.is_paused(),
            "task_counts": counts,
            "active_leases": active,
        }

    def list_eligible(self, *, limit: int = 50) -> list[dict[str, Any]]:
        rows = self.registry.db.query_all(
            """SELECT * FROM tasks WHERE state = ? ORDER BY priority DESC, created_at ASC LIMIT ?""",
            (TaskState.QUEUED.value, limit),
        )
        return [dict(r) for r in rows]

    def claim_task(self, task_id: str, *, worker_id: str | None = None) -> dict[str, Any]:
        if self.is_paused():
            raise QueueError("queue is paused", http_status=409, kind="conflict")
        worker_id = worker_id or new_worker_id()
        with self.registry.db.transaction() as conn:
            expire_stale_leases(conn)
            row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
            if not row:
                raise QueueError("task not found", http_status=404, kind="not_found")
            if row["state"] != TaskState.QUEUED.value:
                raise QueueError("task not eligible", http_status=409, kind="conflict")
            attempt_row = conn.execute(
                "SELECT COALESCE(MAX(attempt_number), 0) + 1 AS n FROM execution_attempts WHERE task_id = ?",
                (task_id,),
            ).fetchone()
            attempt_number = int(attempt_row["n"])
            now = _utc_now()
            cur = conn.execute(
                """INSERT INTO execution_attempts(
                    task_id, attempt_number, worker_id, state, started_at, heartbeat_at
                ) VALUES (?, ?, ?, 'CLAIMED', ?, ?)""",
                (task_id, attempt_number, worker_id, now, now),
            )
            attempt_id = cur.lastrowid
            lease = acquire_lease(conn, task_id=task_id, worker_id=worker_id, attempt_id=attempt_id)
            prev_state = row["state"]
            conn.execute(
                "UPDATE tasks SET state = ?, updated_at = ?, started_at = COALESCE(started_at, ?) WHERE id = ?",
                (TaskState.RUNNING.value, now, now, task_id),
            )
            conn.execute(
                """INSERT INTO task_events(task_id, event_type, previous_state, new_state, details_json, created_at)
                   VALUES (?, 'claimed', ?, ?, ?, ?)""",
                (task_id, prev_state, TaskState.RUNNING.value, _json_dumps({"worker_id": worker_id}), now),
            )
        self._audit("cosd_task_claimed", task_id=task_id, worker_id=worker_id, attempt_number=attempt_number)
        return {
            "ok": True,
            "task_id": task_id,
            "attempt_id": attempt_id,
            "attempt_number": attempt_number,
            "worker_id": worker_id,
            "lease_id": lease["lease_id"],
        }
