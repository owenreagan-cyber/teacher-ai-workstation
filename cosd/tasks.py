"""Task registry service (persistence only — no execution)."""
from __future__ import annotations

import hashlib
import json
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from .storage import SCHEMA_VERSION, TaskDatabase

MAX_LIST_LIMIT = 100
MAX_TITLE_LEN = 500
MAX_KIND_LEN = 64
MAX_IDEMPOTENCY_LEN = 128
MAX_JSON_BYTES = 32_768

TERMINAL_STATES = frozenset({"COMPLETED", "CANCELLED"})


class TaskState(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    BLOCKED = "BLOCKED"


class TaskError(Exception):
    def __init__(self, message: str, *, kind: str = "usage", http_status: int = 400):
        super().__init__(message)
        self.kind = kind
        self.http_status = http_status


# Central transition model (service-only paths; not arbitrary API).
_ALLOWED: dict[str, frozenset[str]] = {
    TaskState.QUEUED.value: frozenset({TaskState.RUNNING.value, TaskState.CANCELLED.value}),
    TaskState.RUNNING.value: frozenset(
        {TaskState.COMPLETED.value, TaskState.FAILED.value, TaskState.BLOCKED.value, TaskState.CANCELLED.value}
    ),
    TaskState.FAILED.value: frozenset({TaskState.QUEUED.value}),
    TaskState.BLOCKED.value: frozenset({TaskState.QUEUED.value, TaskState.CANCELLED.value}),
    TaskState.COMPLETED.value: frozenset(),
    TaskState.CANCELLED.value: frozenset(),
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def _json_dumps(obj: Any) -> str:
    return json.dumps(obj, separators=(",", ":"), ensure_ascii=False, sort_keys=True)


def _validate_json_field(name: str, value: Any, *, required_object: bool = True) -> str:
    if value is None:
        value = {}
    if not isinstance(value, (dict, list)) if not required_object else not isinstance(value, dict):
        raise TaskError(f"{name} must be a JSON object", kind="usage")
    raw = _json_dumps(value)
    if len(raw.encode("utf-8")) > MAX_JSON_BYTES:
        raise TaskError(f"{name} too large", kind="usage", http_status=413)
    return raw


def content_fingerprint(
    *,
    kind: str,
    title: str,
    description: str,
    payload: dict[str, Any],
) -> str:
    blob = _json_dumps({"kind": kind, "title": title, "description": description, "payload": payload})
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _row_to_task(row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "idempotency_key": row["idempotency_key"],
        "kind": row["kind"],
        "title": row["title"],
        "description": row["description"],
        "state": row["state"],
        "priority": row["priority"],
        "payload": json.loads(row["payload_json"] or "{}"),
        "result": json.loads(row["result_json"]) if row["result_json"] else None,
        "error": json.loads(row["error_json"]) if row["error_json"] else None,
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "started_at": row["started_at"],
        "completed_at": row["completed_at"],
        "cancelled_at": row["cancelled_at"],
        "requested_by": row["requested_by"],
        "source": row["source"],
        "schema_version": row["schema_version"],
        "data_class": row["data_class"],
    }


@dataclass
class TaskRegistry:
    db: TaskDatabase

    @classmethod
    def open(cls, base: Path | None = None) -> TaskRegistry:
        return cls(TaskDatabase(base))

    def _append_event(
        self,
        conn,
        *,
        task_id: str,
        event_type: str,
        previous_state: str | None,
        new_state: str | None,
        details: dict | None = None,
    ) -> None:
        conn.execute(
            """INSERT INTO task_events(task_id, event_type, previous_state, new_state, details_json, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                task_id,
                event_type,
                previous_state,
                new_state,
                _json_dumps(details or {}),
                _utc_now(),
            ),
        )

    def create_task(
        self,
        *,
        kind: str,
        title: str,
        description: str = "",
        payload: dict | None = None,
        priority: int = 0,
        idempotency_key: str | None = None,
        requested_by: str = "",
        source: str = "api",
        data_class: str = "internal",
    ) -> tuple[dict[str, Any], bool]:
        kind = (kind or "").strip()
        title = (title or "").strip()
        if not kind or len(kind) > MAX_KIND_LEN:
            raise TaskError("kind required (max 64 chars)", kind="usage")
        if not title or len(title) > MAX_TITLE_LEN:
            raise TaskError("title required (max 500 chars)", kind="usage")
        if idempotency_key is not None:
            idempotency_key = idempotency_key.strip()
            if not idempotency_key or len(idempotency_key) > MAX_IDEMPOTENCY_LEN:
                raise TaskError("invalid idempotency_key", kind="usage")
        if data_class not in ("public", "internal", "sensitive"):
            raise TaskError("data_class must be public, internal, or sensitive", kind="usage")
        payload = payload if payload is not None else {}
        payload_json = _validate_json_field("payload", payload)
        fp = content_fingerprint(kind=kind, title=title, description=description, payload=payload)

        if idempotency_key:
            existing = self.db.execute(
                "SELECT * FROM tasks WHERE idempotency_key = ?", (idempotency_key,)
            ).fetchone()
            if existing:
                if existing["content_fingerprint"] != fp:
                    raise TaskError(
                        "idempotency_key reused with different task content",
                        kind="conflict",
                        http_status=409,
                    )
                return _row_to_task(existing), True

        task_id = secrets.token_hex(16)
        now = _utc_now()
        with self.db.transaction() as conn:
            conn.execute(
                """INSERT INTO tasks(
                    id, idempotency_key, kind, title, description, state, priority,
                    payload_json, created_at, updated_at, requested_by, source,
                    schema_version, content_fingerprint, data_class
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    task_id,
                    idempotency_key,
                    kind,
                    title,
                    description,
                    TaskState.QUEUED.value,
                    int(priority),
                    payload_json,
                    now,
                    now,
                    requested_by,
                    source,
                    SCHEMA_VERSION,
                    fp,
                    data_class,
                ),
            )
            self._append_event(
                conn,
                task_id=task_id,
                event_type="created",
                previous_state=None,
                new_state=TaskState.QUEUED.value,
                details={"source": source},
            )
            row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        return _row_to_task(row), False

    def get_task(self, task_id: str) -> dict[str, Any]:
        row = self.db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if not row:
            raise TaskError("task not found", kind="not_found", http_status=404)
        return _row_to_task(row)

    def list_tasks(
        self,
        *,
        state: str | None = None,
        kind: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        limit = max(1, min(int(limit), MAX_LIST_LIMIT))
        offset = max(0, int(offset))
        clauses = ["1=1"]
        params: list[Any] = []
        if state:
            if state not in TaskState._value2member_map_:
                raise TaskError("invalid state filter", kind="usage")
            clauses.append("state = ?")
            params.append(state)
        if kind:
            clauses.append("kind = ?")
            params.append(kind.strip())
        where = " AND ".join(clauses)
        total = self.db.execute(f"SELECT COUNT(*) AS c FROM tasks WHERE {where}", params).fetchone()["c"]
        rows = self.db.execute(
            f"""SELECT * FROM tasks WHERE {where}
                ORDER BY created_at DESC LIMIT ? OFFSET ?""",
            (*params, limit, offset),
        ).fetchall()
        return {
            "ok": True,
            "tasks": [_row_to_task(r) for r in rows],
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    def _transition(
        self,
        task_id: str,
        *,
        new_state: str,
        event_type: str,
        details: dict | None = None,
        started_at: bool = False,
        completed_at: bool = False,
        cancelled_at: bool = False,
        result: dict | None = None,
        error: dict | None = None,
    ) -> dict[str, Any]:
        now = _utc_now()
        with self.db.transaction() as conn:
            row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
            if not row:
                raise TaskError("task not found", kind="not_found", http_status=404)
            prev = row["state"]
            if new_state not in _ALLOWED.get(prev, frozenset()):
                raise TaskError(
                    f"invalid transition {prev} -> {new_state}",
                    kind="conflict",
                    http_status=409,
                )
            sets = ["state = ?", "updated_at = ?"]
            vals: list[Any] = [new_state, now]
            if started_at:
                sets.append("started_at = ?")
                vals.append(now)
            if completed_at:
                sets.append("completed_at = ?")
                vals.append(now)
            if cancelled_at:
                sets.append("cancelled_at = ?")
                vals.append(now)
            if result is not None:
                sets.append("result_json = ?")
                vals.append(_validate_json_field("result", result))
            if error is not None:
                sets.append("error_json = ?")
                vals.append(_validate_json_field("error", error))
            vals.append(task_id)
            conn.execute(f"UPDATE tasks SET {', '.join(sets)} WHERE id = ?", vals)
            self._append_event(
                conn,
                task_id=task_id,
                event_type=event_type,
                previous_state=prev,
                new_state=new_state,
                details=details,
            )
            updated = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        return _row_to_task(updated)

    def transition_task(
        self,
        task_id: str,
        *,
        new_state: str,
        event_type: str = "transition",
        details: dict | None = None,
    ) -> dict[str, Any]:
        """Internal transition hook (e.g. future executor)."""
        extra: dict[str, Any] = {}
        if new_state == TaskState.RUNNING.value:
            extra["started_at"] = True
        if new_state == TaskState.COMPLETED.value:
            extra["completed_at"] = True
        if new_state == TaskState.CANCELLED.value:
            extra["cancelled_at"] = True
        return self._transition(task_id, new_state=new_state, event_type=event_type, details=details, **extra)

    def cancel_task(self, task_id: str, *, reason: str = "") -> dict[str, Any]:
        row = self.get_task(task_id)
        if row["state"] in TERMINAL_STATES:
            raise TaskError("task already terminal", kind="conflict", http_status=409)
        if row["state"] not in (
            TaskState.QUEUED.value,
            TaskState.RUNNING.value,
            TaskState.BLOCKED.value,
        ):
            raise TaskError("task cannot be cancelled", kind="conflict", http_status=409)
        return self._transition(
            task_id,
            new_state=TaskState.CANCELLED.value,
            event_type="cancelled",
            details={"reason": reason} if reason else {},
            cancelled_at=True,
        )

    def retry_task(self, task_id: str) -> dict[str, Any]:
        row = self.get_task(task_id)
        if row["state"] not in (TaskState.FAILED.value, TaskState.BLOCKED.value):
            raise TaskError("only FAILED or BLOCKED tasks may be retried", kind="conflict", http_status=409)
        return self._transition(
            task_id,
            new_state=TaskState.QUEUED.value,
            event_type="retry",
            details={},
        )

    def get_task_history(self, task_id: str) -> dict[str, Any]:
        self.get_task(task_id)
        rows = self.db.execute(
            """SELECT id, task_id, event_type, previous_state, new_state, details_json, created_at
               FROM task_events WHERE task_id = ? ORDER BY id ASC""",
            (task_id,),
        ).fetchall()
        events = [
            {
                "id": r["id"],
                "task_id": r["task_id"],
                "event_type": r["event_type"],
                "previous_state": r["previous_state"],
                "new_state": r["new_state"],
                "details": json.loads(r["details_json"] or "{}"),
                "created_at": r["created_at"],
            }
            for r in rows
        ]
        return {"ok": True, "task_id": task_id, "events": events}

    def get_task_counts(self) -> dict[str, int]:
        rows = self.db.execute("SELECT state, COUNT(*) AS c FROM tasks GROUP BY state").fetchall()
        counts = {s.value: 0 for s in TaskState}
        for r in rows:
            counts[r["state"]] = r["c"]
        return counts
