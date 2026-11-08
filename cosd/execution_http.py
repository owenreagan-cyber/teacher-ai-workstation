"""HTTP routes for queue, workers, and task execution."""
from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

from cosd.task_http import _read_json
from cosd.tasks import TaskError, TaskRegistry

from cosd.execution.engine import ExecutionEngine
from cosd.execution.queue import QueueError

_TASK_EXEC = re.compile(r"^/v1/tasks/([a-f0-9]{32})/(execute|attempts|checkpoints)$")


def dispatch_execution_request(
    handler,
    *,
    registry: TaskRegistry,
    engine: ExecutionEngine,
    max_body: int,
) -> tuple[int, dict[str, Any]] | None:
    path = urlparse(handler.path).path
    method = handler.command

    try:
        if path == "/v1/queue" and method == "GET":
            return 200, engine.queue.status()
        if path == "/v1/queue/pause" and method == "POST":
            return 200, engine.queue.set_paused(True)
        if path == "/v1/queue/resume" and method == "POST":
            return 200, engine.queue.set_paused(False)
        if path == "/v1/workers" and method == "GET":
            return 200, engine.list_workers()
        m = _TASK_EXEC.match(path)
        if m:
            task_id, action = m.group(1), m.group(2)
            if action == "attempts" and method == "GET":
                return 200, engine.list_attempts(task_id)
            if action == "checkpoints" and method == "GET":
                return 200, engine.list_checkpoints(task_id)
            if action == "execute" and method == "POST":
                _read_json(handler, max_body)
                body = engine.execute_task(task_id)
                return 200 if body.get("ok", True) else 500, {"ok": body.get("ok", False), **body}
    except (TaskError, QueueError) as exc:
        status = getattr(exc, "http_status", 400)
        kind = getattr(exc, "kind", "usage")
        return status, {"ok": False, "error": str(exc), "error_kind": kind}
    except RuntimeError as exc:
        return 409, {"ok": False, "error": str(exc), "error_kind": "conflict"}
    if path.startswith("/v1/queue") or path == "/v1/workers":
        return 405, {"ok": False, "error": "method not allowed", "error_kind": "method"}
    return None
