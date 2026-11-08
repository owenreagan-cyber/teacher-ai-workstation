"""HTTP handlers for /v1/tasks/*."""
from __future__ import annotations

import json
import re
from typing import Any
from urllib.parse import parse_qs, urlparse

from .tasks import TaskError, TaskRegistry

_TASK_PATH = re.compile(
    r"^/v1/tasks(?:/([a-f0-9]{32}))?(?:/(cancel|retry|history|execute|attempts|checkpoints))?$"
)


def _read_json(handler, max_bytes: int) -> dict[str, Any] | None:
    length = int(handler.headers.get("Content-Length", "0") or "0")
    if length > max_bytes:
        raise TaskError("request too large", kind="usage", http_status=413)
    if length == 0:
        return {}
    raw = handler.rfile.read(length)
    try:
        data = json.loads(raw.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise TaskError("invalid JSON", kind="usage", http_status=400)
    if not isinstance(data, dict):
        raise TaskError("body must be an object", kind="usage")
    return data


def dispatch_task_request(handler, *, registry: TaskRegistry, max_body: int) -> tuple[int, dict[str, Any]] | None:
    path = urlparse(handler.path).path
    m = _TASK_PATH.match(path)
    if not m and path != "/v1/tasks":
        if path.startswith("/v1/tasks"):
            return 404, {"ok": False, "error": "not found", "error_kind": "not_found"}
        return None
    task_id, action = (m.group(1), m.group(2)) if m else (None, None)
    method = handler.command

    try:
        if path == "/v1/tasks" and method == "GET":
            qs = parse_qs(urlparse(handler.path).query)
            state = qs.get("state", [None])[0]
            kind = qs.get("kind", [None])[0]
            limit = int(qs.get("limit", ["50"])[0])
            offset = int(qs.get("offset", ["0"])[0])
            body = registry.list_tasks(state=state, kind=kind, limit=limit, offset=offset)
            return 200, body
        if path == "/v1/tasks" and method == "POST":
            data = _read_json(handler, max_body)
            task, reused = registry.create_task(
                kind=str(data.get("kind", "")),
                title=str(data.get("title", "")),
                description=str(data.get("description", "")),
                payload=data.get("payload"),
                priority=int(data.get("priority", 0)),
                idempotency_key=data.get("idempotency_key"),
                requested_by=str(data.get("requested_by", "")),
                source=str(data.get("source", "api")),
                data_class=str(data.get("data_class", "internal")),
            )
            return (200 if reused else 201), {"ok": True, "task": task, "reused": reused}
        if task_id and action is None and method == "GET":
            return 200, {"ok": True, "task": registry.get_task(task_id)}
        if task_id and action == "history" and method == "GET":
            return 200, registry.get_task_history(task_id)
        if task_id and action == "cancel" and method == "POST":
            data = _read_json(handler, max_body)
            reason = str((data or {}).get("reason", ""))
            task = registry.cancel_task(task_id, reason=reason)
            return 200, {"ok": True, "task": task}
        if task_id and action == "retry" and method == "POST":
            task = registry.retry_task(task_id)
            return 200, {"ok": True, "task": task}
        if task_id and action in ("execute", "attempts", "checkpoints"):
            return None
        if path.startswith("/v1/tasks"):
            return 405, {"ok": False, "error": "method not allowed", "error_kind": "method"}
    except TaskError as exc:
        return exc.http_status, {"ok": False, "error": str(exc), "error_kind": exc.kind}
    return None
