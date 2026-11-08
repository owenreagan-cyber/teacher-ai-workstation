"""Runtime monitoring snapshot for cosd (no secrets)."""
from __future__ import annotations

import shutil
import time
from pathlib import Path
from typing import Any

from cos.config import state_dir
from cos.service import run_status

from . import __version__
from .execution.engine import ExecutionEngine
from .tasks import TaskRegistry


def _db_sizes(base: Path) -> dict[str, int | None]:
    db = base / "cosd" / "tasks.db"
    wal = base / "cosd" / "tasks.db-wal"
    out: dict[str, int | None] = {"tasks_db_bytes": None, "wal_bytes": None}
    try:
        if db.is_file():
            out["tasks_db_bytes"] = db.stat().st_size
        if wal.is_file():
            out["wal_bytes"] = wal.stat().st_size
    except OSError:
        pass
    return out


def runtime_snapshot(
    *,
    registry: TaskRegistry,
    engine: ExecutionEngine,
    cfg,
    state_base: Path | None = None,
    started_monotonic: float | None = None,
) -> dict[str, Any]:
    from .lifecycle import fetch_health, process_alive, read_pid

    base = state_base or state_dir()
    pid_rec = read_pid(base)
    health: dict[str, Any] | None = None
    if pid_rec and process_alive(pid_rec.pid):
        health = fetch_health(pid_rec.host, pid_rec.port)
    counts = registry.get_task_counts()
    paused = engine.queue.is_paused()
    leases = engine.list_workers()
    uptime_s = None
    if started_monotonic is not None:
        uptime_s = max(0, int(time.monotonic() - started_monotonic))
    disk = shutil.disk_usage(base)
    return {
        "ok": True,
        "cosd_version": __version__,
        "api_version": "v1",
        "pid": pid_rec.pid if pid_rec else None,
        "health": health,
        "uptime_s": uptime_s,
        "task_counts": counts,
        "queue_paused": paused,
        "active_leases": len(leases.get("workers", [])) if isinstance(leases, dict) else 0,
        "workers": leases,
        "storage": {
            **_db_sizes(base),
            "disk_free_bytes": disk.free,
            "disk_total_bytes": disk.total,
        },
        "model": run_status(cfg),
    }
