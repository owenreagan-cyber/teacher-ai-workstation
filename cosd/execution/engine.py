"""Execution engine façade."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from cosd.tasks import TaskRegistry

from .dispatcher import HandlerRegistry
from .checkpoints import list_checkpoints_db
from .queue import ExecutionQueue, QueueError
from .recovery import Recovery
from .worker import WorkerRunner


class ExecutionEngine:
    def __init__(self, registry: TaskRegistry):
        self.registry = registry
        self.queue = ExecutionQueue(registry)
        self.handlers = HandlerRegistry(registry)
        self.worker = WorkerRunner(registry, self.handlers)
        self.recovery = Recovery(registry, self.handlers)
        self._accepting = True

    @classmethod
    def open(cls, base: Path | None = None) -> ExecutionEngine:
        return cls(TaskRegistry.open(base))

    def startup_recovery(self) -> dict[str, Any]:
        return self.recovery.run()

    def prepare_shutdown(self, *, wait_s: float = 5.0) -> None:
        self._accepting = False
        self.queue.set_paused(True)

    def execute_task(self, task_id: str, *, worker_id: str | None = None) -> dict[str, Any]:
        if not self._accepting:
            raise QueueError("engine not accepting work", http_status=503, kind="stopped")
        claim = self.queue.claim_task(task_id, worker_id=worker_id)
        return self.worker.execute_claimed(
            task_id=task_id,
            attempt_id=claim["attempt_id"],
            worker_id=claim["worker_id"],
            lease_id=claim["lease_id"],
        )

    def list_attempts(self, task_id: str) -> dict[str, Any]:
        self.registry.get_task(task_id)
        rows = self.registry.db.query_all(
            """SELECT id, task_id, attempt_number, worker_id, state, started_at, heartbeat_at,
                      finished_at, error_json, result_json
               FROM execution_attempts WHERE task_id = ? ORDER BY attempt_number ASC""",
            (task_id,),
        )
        attempts = []
        for r in rows:
            attempts.append(
                {
                    "id": r["id"],
                    "task_id": r["task_id"],
                    "attempt_number": r["attempt_number"],
                    "worker_id": r["worker_id"],
                    "state": r["state"],
                    "started_at": r["started_at"],
                    "heartbeat_at": r["heartbeat_at"],
                    "finished_at": r["finished_at"],
                    "error": json.loads(r["error_json"]) if r["error_json"] else None,
                    "result": json.loads(r["result_json"]) if r["result_json"] else None,
                }
            )
        return {"ok": True, "task_id": task_id, "attempts": attempts}

    def list_checkpoints(self, task_id: str) -> dict[str, Any]:
        self.registry.get_task(task_id)
        return {"ok": True, "task_id": task_id, "checkpoints": list_checkpoints_db(self.registry.db, task_id)}

    def list_workers(self) -> dict[str, Any]:
        rows = self.registry.db.query_all(
            """SELECT lease_id, task_id, worker_id, acquired_at, expires_at, heartbeat_at, state
               FROM worker_leases ORDER BY acquired_at DESC LIMIT 100"""
        )
        return {
            "ok": True,
            "workers": [dict(r) for r in rows],
        }
