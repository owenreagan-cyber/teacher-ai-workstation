"""Startup reconciliation for interrupted executions."""
from __future__ import annotations

from typing import Any

from cos.audit import AuditLog
from cos.config import load_config

from cosd.tasks import TaskRegistry, TaskState, _json_dumps, _utc_now

from .dispatcher import HandlerRegistry
from .checkpoints import latest_checkpoint_db
from .leases import expire_stale_leases, lease_expired


class Recovery:
    def __init__(self, registry: TaskRegistry, handlers: HandlerRegistry):
        self.registry = registry
        self.handlers = handlers

    def run(self) -> dict[str, Any]:
        repaired: list[dict[str, str]] = []
        with self.registry.db.transaction() as conn:
            expire_stale_leases(conn)
            rows = conn.execute(
                """SELECT t.id AS task_id, t.state AS task_state, t.kind,
                          a.id AS attempt_id, a.state AS attempt_state, a.worker_id,
                          l.lease_id, l.expires_at, l.state AS lease_state
                   FROM tasks t
                   JOIN execution_attempts a ON a.task_id = t.id
                   LEFT JOIN worker_leases l ON l.task_id = t.id AND l.state = 'active'
                   WHERE t.state = ? AND a.finished_at IS NULL""",
                (TaskState.RUNNING.value,),
            ).fetchall()
            for row in rows:
                lease_active = row["lease_id"] and row["lease_state"] == "active"
                if lease_active and not lease_expired(row["expires_at"]):
                    continue
                policy = "block_on_interrupt"
                try:
                    policy = self.handlers.get(row["kind"]).recovery_policy
                except Exception:
                    pass
                action = self._reconcile(conn, row, policy)
                repaired.append({"task_id": row["task_id"], "action": action})
        if repaired:
            AuditLog(load_config().audit_path)("cosd_recovery_scan", count=len(repaired))
        return {"ok": True, "repaired": repaired}

    def _reconcile(self, conn, row, policy: str) -> str:
        task_id = row["task_id"]
        attempt_id = row["attempt_id"]
        now = _utc_now()
        cp = latest_checkpoint_db(self.registry.db, attempt_id=attempt_id, checkpoint_key="progress")
        if row["lease_id"]:
            conn.execute(
                "UPDATE worker_leases SET state = 'expired' WHERE lease_id = ?", (row["lease_id"],)
            )
        conn.execute(
            """UPDATE execution_attempts SET state = 'RECOVERING', finished_at = ?, heartbeat_at = ?,
               error_json = ? WHERE id = ?""",
            (now, now, _json_dumps({"interrupted": True}), attempt_id),
        )
        if policy == "safe_replay":
            new_state = TaskState.QUEUED.value
            action = "requeued"
        elif policy == "checkpoint_resume" and cp:
            new_state = TaskState.BLOCKED.value
            action = "blocked_checkpoint"
        else:
            new_state = TaskState.BLOCKED.value
            action = "blocked_uncertain"
        prev = row["task_state"]
        conn.execute(
            "UPDATE tasks SET state = ?, updated_at = ? WHERE id = ?", (new_state, now, task_id)
        )
        conn.execute(
            """INSERT INTO task_events(task_id, event_type, previous_state, new_state, details_json, created_at)
               VALUES (?, 'recovery', ?, ?, ?, ?)""",
            (task_id, prev, new_state, _json_dumps({"policy": policy}), now),
        )
        return action
