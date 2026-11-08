"""SQLite persistence for cosd tasks (WAL, private state dir)."""
from __future__ import annotations

import os
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from cos.config import FILE_MODE, STATE_DIR_MODE, state_dir

SCHEMA_VERSION = 1
DB_FILENAME = "tasks.sqlite3"
BUSY_TIMEOUT_MS = 5000

_SCHEMA_V1 = """
CREATE TABLE IF NOT EXISTS schema_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    idempotency_key TEXT UNIQUE,
    kind TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    state TEXT NOT NULL,
    priority INTEGER NOT NULL DEFAULT 0,
    payload_json TEXT NOT NULL DEFAULT '{}',
    result_json TEXT,
    error_json TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    started_at TEXT,
    completed_at TEXT,
    cancelled_at TEXT,
    requested_by TEXT NOT NULL DEFAULT '',
    source TEXT NOT NULL DEFAULT 'api',
    schema_version INTEGER NOT NULL,
    content_fingerprint TEXT NOT NULL,
    data_class TEXT NOT NULL DEFAULT 'internal'
);

CREATE TABLE IF NOT EXISTS task_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    previous_state TEXT,
    new_state TEXT,
    details_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS task_metadata (
    key TEXT PRIMARY KEY,
    value_json TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_tasks_state ON tasks(state);
CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at);
CREATE INDEX IF NOT EXISTS idx_tasks_updated_at ON tasks(updated_at);
CREATE INDEX IF NOT EXISTS idx_tasks_kind ON tasks(kind);
CREATE INDEX IF NOT EXISTS idx_task_events_task_id ON task_events(task_id);
CREATE INDEX IF NOT EXISTS idx_task_events_created_at ON task_events(created_at);
"""


def database_path(base: Path | None = None) -> Path:
    root = base or state_dir()
    return root / "cosd" / DB_FILENAME


def _ensure_private_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=STATE_DIR_MODE)


def _chmod_db(path: Path) -> None:
    if path.exists():
        os.chmod(path, FILE_MODE)


class TaskDatabase:
    """Thread-safe SQLite access with explicit transactions."""

    def __init__(self, base: Path | None = None, *, path: Path | None = None):
        self._path = path or database_path(base)
        self._lock = threading.RLock()
        _ensure_private_dir(self._path)
        self._conn = self._connect()
        self._migrate()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(
            str(self._path),
            timeout=BUSY_TIMEOUT_MS / 1000.0,
            isolation_level="IMMEDIATE",
            check_same_thread=False,
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute(f"PRAGMA busy_timeout = {BUSY_TIMEOUT_MS}")
        _chmod_db(self._path)
        return conn

    @property
    def path(self) -> Path:
        return self._path

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    def _migrate(self) -> None:
        with self._lock:
            self._conn.executescript(_SCHEMA_V1)
            row = self._conn.execute(
                "SELECT value FROM schema_meta WHERE key = 'schema_version'"
            ).fetchone()
            if row is None:
                self._conn.execute(
                    "INSERT INTO schema_meta(key, value) VALUES ('schema_version', ?)",
                    (str(SCHEMA_VERSION),),
                )
            else:
                current = int(row["value"])
                if current > SCHEMA_VERSION:
                    raise RuntimeError(f"database schema {current} newer than cosd {SCHEMA_VERSION}")
                if current < SCHEMA_VERSION:
                    self._conn.execute(
                        "UPDATE schema_meta SET value = ? WHERE key = 'schema_version'",
                        (str(SCHEMA_VERSION),),
                    )
            self._conn.commit()

    @contextmanager
    def _transaction(self) -> Iterator[sqlite3.Connection]:
        with self._lock:
            try:
                yield self._conn
                self._conn.commit()
            except Exception:
                self._conn.rollback()
                raise

    def execute(self, sql: str, params: tuple | list = ()) -> sqlite3.Cursor:
        with self._lock:
            return self._conn.execute(sql, params)

    def executemany(self, sql: str, seq: list[tuple]) -> None:
        with self._lock:
            self._conn.executemany(sql, seq)

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        with self._transaction() as conn:
            yield conn

    def integrity_check(self) -> str:
        row = self.execute("PRAGMA integrity_check").fetchone()
        return str(row[0]) if row else "unknown"
