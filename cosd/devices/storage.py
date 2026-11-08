"""SQLite storage for the local device registry.

The device tables live in the existing cosd database file
(``<state>/cosd/tasks.sqlite3``) so there is no second database. A dedicated
``device_schema_version`` key keeps this migration independent of the task
schema; a failed device migration must not take the task registry down.
"""

from __future__ import annotations

import os
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from cos.config import FILE_MODE, STATE_DIR_MODE

from ..storage import BUSY_TIMEOUT_MS, database_path

DEVICE_SCHEMA_VERSION = 1
DEVICE_SCHEMA_KEY = "device_schema_version"

_SCHEMA_V1 = """
CREATE TABLE IF NOT EXISTS schema_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS devices (
    device_id TEXT PRIMARY KEY,
    display_name TEXT NOT NULL CHECK(length(display_name) BETWEEN 1 AND 80),
    device_type TEXT NOT NULL CHECK(device_type IN ('mac','iphone','ipad','other')),
    platform TEXT NOT NULL CHECK(platform IN ('macos','ios','ipados','unknown')),
    owner_id TEXT NOT NULL CHECK(length(owner_id) BETWEEN 1 AND 64),
    device_profile TEXT NOT NULL CHECK(device_profile IN
        ('owner','personal','partner','school','read_only','capture_only','revoked')),
    trust_level TEXT NOT NULL CHECK(trust_level IN
        ('owner','trusted','limited','restricted','untrusted')),
    status TEXT NOT NULL CHECK(status IN ('active','disabled','revoked','removed')),
    app_version TEXT NOT NULL DEFAULT '',
    registered_at TEXT NOT NULL,
    last_seen_at TEXT,
    updated_at TEXT NOT NULL,
    revoked_at TEXT,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    is_primary_owner INTEGER NOT NULL DEFAULT 0 CHECK(is_primary_owner IN (0,1))
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_devices_single_primary_owner
    ON devices(is_primary_owner) WHERE is_primary_owner = 1;
CREATE INDEX IF NOT EXISTS idx_devices_status ON devices(status);
CREATE INDEX IF NOT EXISTS idx_devices_profile ON devices(device_profile);

CREATE TABLE IF NOT EXISTS device_credentials (
    credential_id TEXT PRIMARY KEY,
    device_id TEXT NOT NULL REFERENCES devices(device_id) ON DELETE CASCADE,
    credential_type TEXT NOT NULL CHECK(credential_type IN ('device_access')),
    keychain_ref TEXT NOT NULL,
    verifier TEXT NOT NULL,
    verifier_salt TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('active','rotated','expired','revoked')),
    created_at TEXT NOT NULL,
    expires_at TEXT,
    rotated_at TEXT,
    revoked_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_device_credentials_device
    ON device_credentials(device_id);
CREATE INDEX IF NOT EXISTS idx_device_credentials_status
    ON device_credentials(status);

-- Deliberately no foreign key: security events must remain attributable after
-- a device row is removed.
CREATE TABLE IF NOT EXISTS device_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id TEXT NOT NULL,
    display_name TEXT,
    event_type TEXT NOT NULL,
    result TEXT NOT NULL,
    profile TEXT,
    credential_id TEXT,
    actor TEXT,
    details_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_device_events_device
    ON device_events(device_id);
CREATE INDEX IF NOT EXISTS idx_device_events_created
    ON device_events(created_at);
"""


def _ensure_private_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=STATE_DIR_MODE)


def _chmod_db(path: Path) -> None:
    if path.exists():
        os.chmod(path, FILE_MODE)


class DeviceDatabase:
    """Thread-safe access to the device tables in the shared cosd database."""

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
                "SELECT value FROM schema_meta WHERE key = ?", (DEVICE_SCHEMA_KEY,)
            ).fetchone()
            if row is None:
                self._conn.execute(
                    "INSERT INTO schema_meta(key, value) VALUES (?, ?)",
                    (DEVICE_SCHEMA_KEY, str(DEVICE_SCHEMA_VERSION)),
                )
            else:
                current = int(row["value"])
                if current > DEVICE_SCHEMA_VERSION:
                    raise RuntimeError(
                        f"device schema {current} newer than cosd {DEVICE_SCHEMA_VERSION}"
                    )
                if current < DEVICE_SCHEMA_VERSION:
                    # Only v1 exists. Future migrations branch here by version.
                    self._conn.execute(
                        "UPDATE schema_meta SET value = ? WHERE key = ?",
                        (str(DEVICE_SCHEMA_VERSION), DEVICE_SCHEMA_KEY),
                    )
            self._conn.commit()

    def execute(self, sql: str, params: tuple | list = ()) -> sqlite3.Cursor:
        with self._lock:
            return self._conn.execute(sql, params)

    @contextmanager
    def _transaction(self) -> Iterator[sqlite3.Connection]:
        with self._lock:
            try:
                yield self._conn
                self._conn.commit()
            except Exception:
                self._conn.rollback()
                raise

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        with self._transaction() as conn:
            yield conn

    def integrity_check(self) -> str:
        row = self.execute("PRAGMA integrity_check").fetchone()
        return str(row[0]) if row else "unknown"
