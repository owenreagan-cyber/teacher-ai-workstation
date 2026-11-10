"""Execute one claimed task through registered handlers."""
from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from typing import Any

from cos.audit import AuditLog
from cos.config import load_config
from cos.policy import KillSwitch

from cosd.tasks import TaskRegistry, TaskState, _json_dumps, _utc_now

from .checkpoints import latest_checkpoint_db, write_checkpoint
from .dispatcher import ExecutionDenied, HandlerRegistry
from .leases import release_lease, renew_lease
from .retry import next_retry_at


class WorkerRunner:
    def __init__(self, registry: TaskRegistry, handlers: HandlerRegistry):
        self.registry = registry
        self.handlers = handlers

    def _audit(self, kind: str, **fields) -> None:
        AuditLog(load_config().audit_path)(kind, **fields)

    def _governance(self) -> None:
        ks = KillSwitch(load_config().state_dir)
        if ks.is_set():
            raise ExecutionDenied("kill switch active", permanent=False)

    def execute_claimed(
        self,
        *,
        task_id: str,
        attempt_id: int,
        worker_id: str,
        lease_id: str,
    ) -> dict[str, Any]:
        self._governance()
        task = self.registry.get_task(task_id)
        try:
            spec = self.handlers.get(task["kind"])
        except ExecutionDenied as exc:
            return self._fail(
                task_id,
                attempt_id,
                worker_id,
                lease_id,
                type("spec", (), {"retryable": False, "max_attempts": 1})(),
                error={"error": str(exc), "retriable": False},
                permanent=True,
            )
        attempt = self.registry.db.query_one(
            "SELECT * FROM execution_attempts WHERE id = ?", (attempt_id,)
        )
        if not attempt or attempt["worker_id"] != worker_id:
            raise RuntimeError("attempt ownership mismatch")
        now = _utc_now()
        with self.registry.db.transaction() as conn:
            conn.execute(
                "UPDATE execution_attempts SET state = 'RUNNING', heartbeat_at = ? WHERE id = ?",
                (now, attempt_id),
            )
            renew_lease(conn, lease_id=lease_id, worker_id=worker_id)
        checkpoint = latest_checkpoint_db(
            self.registry.db, attempt_id=attempt_id, checkpoint_key="progress"
        )

        def _run():
            return spec.execute(task["payload"], checkpoint)

        try:
            with ThreadPoolExecutor(max_workers=1) as pool:
                out = pool.submit(_run).result(timeout=spec.timeout_s)
        except FuturesTimeout:
            return self._fail(
                task_id,
                attempt_id,
                worker_id,
                lease_id,
                spec,
                error={"error": "timeout", "retriable": spec.retryable},
                permanent=False,
            )
        except ExecutionDenied as exc:
            return self._fail(
                task_id,
                attempt_id,
                worker_id,
                lease_id,
                spec,
                error={"error": str(exc), "retriable": not exc.permanent},
                permanent=exc.permanent,
            )
        except Exception as exc:  # noqa: BLE001
            return self._fail(
                task_id,
                attempt_id,
                worker_id,
                lease_id,
                spec,
                error={"error": type(exc).__name__, "retriable": spec.retryable},
                permanent=False,
            )

        if isinstance(out, dict) and "_checkpoint" in out:
            cp = out.pop("_checkpoint")
            with self.registry.db.transaction() as conn:
                write_checkpoint(
                    conn,
                    task_id=task_id,
                    attempt_id=attempt_id,
                    checkpoint_key=cp["checkpoint_key"],
                    data=cp["data"],
                )
                conn.execute(
                    "UPDATE execution_attempts SET state = 'CHECKPOINTED', heartbeat_at = ? WHERE id = ?",
                    (_utc_now(), attempt_id),
                )
                renew_lease(conn, lease_id=lease_id, worker_id=worker_id)
            return {"ok": True, "status": "checkpointed", "partial": out}

        return self._complete(task_id, attempt_id, worker_id, lease_id, result=out)

    def _complete(
        self,
        task_id: str,
        attempt_id: int,
        worker_id: str,
        lease_id: str,
        *,
        result: dict,
    ) -> dict[str, Any]:
        now = _utc_now()
        result_json = _json_dumps(result)
        with self.registry.db.transaction() as conn:
            conn.execute(
                """UPDATE execution_attempts SET state = 'COMPLETED', finished_at = ?, heartbeat_at = ?,
                   result_json = ? WHERE id = ?""",
                (now, now, result_json, attempt_id),
            )
            release_lease(conn, lease_id=lease_id, worker_id=worker_id)
            row = conn.execute("SELECT state FROM tasks WHERE id = ?", (task_id,)).fetchone()
            prev = row["state"]
            conn.execute(
                """UPDATE tasks SET state = ?, updated_at = ?, completed_at = ?, result_json = ?,
                   retry_after_at = NULL WHERE id = ?""",
                (TaskState.COMPLETED.value, now, now, result_json, task_id),
            )
            conn.execute(
                """INSERT INTO task_events(task_id, event_type, previous_state, new_state, details_json, created_at)
                   VALUES (?, 'completed', ?, ?, ?, ?)""",
                (task_id, prev, TaskState.COMPLETED.value, _json_dumps({"attempt_id": attempt_id}), now),
            )
        self._audit("cosd_task_completed", task_id=task_id, attempt_id=attempt_id)
        return {"ok": True, "status": "completed", "result": result}

    def _fail(
        self,
        task_id: str,
        attempt_id: int,
        worker_id: str,
        lease_id: str,
        spec,
        *,
        error: dict,
        permanent: bool,
    ) -> dict[str, Any]:
        now = _utc_now()
        err_json = _json_dumps(error)
        attempt_number = self.registry.db.query_one(
            "SELECT attempt_number FROM execution_attempts WHERE id = ?", (attempt_id,)
        )["attempt_number"]
        retry_at = None
        if not permanent and error.get("retriable") and spec.retryable:
            retry_at = next_retry_at(attempt_number, max_attempts=spec.max_attempts)
            if retry_at:
                task_state = TaskState.FAILED.value
            else:
                permanent = True
        new_task_state = TaskState.FAILED.value if permanent or not retry_at else TaskState.FAILED.value
        with self.registry.db.transaction() as conn:
            conn.execute(
                """UPDATE execution_attempts SET state = ?, finished_at = ?, heartbeat_at = ?, error_json = ?
                   WHERE id = ?""",
                ("FAILED" if permanent or not retry_at else "RETRY_WAIT", now, now, err_json, attempt_id),
            )
            release_lease(conn, lease_id=lease_id, worker_id=worker_id)
            row = conn.execute("SELECT state FROM tasks WHERE id = ?", (task_id,)).fetchone()
            prev = row["state"]
            conn.execute(
                """UPDATE tasks SET state = ?, updated_at = ?, error_json = ?, retry_after_at = ? WHERE id = ?""",
                (new_task_state, now, err_json, retry_at, task_id),
            )
            conn.execute(
                """INSERT INTO task_events(task_id, event_type, previous_state, new_state, details_json, created_at)
                   VALUES (?, 'failed', ?, ?, ?, ?)""",
                (task_id, prev, new_task_state, _json_dumps({"error": error, "retry_after_at": retry_at}), now),
            )
        self._audit("cosd_task_failed", task_id=task_id, attempt_id=attempt_id)
        return {"ok": False, "status": "failed", "error": error, "retry_after_at": retry_at}
