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

from cos.config import FILE_MODE, ensure_private_dir

from ..storage import BUSY_TIMEOUT_MS, database_path

DEVICE_SCHEMA_VERSION = 2
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

# P1b.4c: enrollment requests and durable pairing rate limits. These tables
# share the same database file. Enrollment rows deliberately have no foreign
# key to devices so a rejected/expired request and its audit remain readable.
_SCHEMA_V2 = """
-- P0.3c.1: one durable reservation per enrollment. The primary key is the
-- concurrency guard: a second approval of the same enrollment cannot insert a
-- second row, so it fails closed instead of issuing a second credential.
CREATE TABLE IF NOT EXISTS credential_reservations (
    enrollment_id TEXT PRIMARY KEY,
    reservation_id TEXT NOT NULL UNIQUE,
    credential_id TEXT NOT NULL,
    delivery_ref TEXT NOT NULL,
    device_profile TEXT NOT NULL,
    public_key_fingerprint TEXT NOT NULL,
    expected_state TEXT NOT NULL,
    generation INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    attempts INTEGER NOT NULL DEFAULT 0,
    state TEXT NOT NULL CHECK(state IN ('pending','cleanup_failed')),
    reason TEXT
);

CREATE INDEX IF NOT EXISTS idx_credential_reservations_expires
    ON credential_reservations(expires_at);

-- P0.3c.2: one durable reservation per credential being rotated. The primary
-- key is the credential id, so two concurrent rotations of the same credential
-- cannot both proceed.
CREATE TABLE IF NOT EXISTS credential_rotation_reservations (
    credential_id TEXT PRIMARY KEY,
    reservation_id TEXT NOT NULL UNIQUE,
    new_credential_id TEXT NOT NULL,
    new_keychain_ref TEXT NOT NULL,
    device_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    attempts INTEGER NOT NULL DEFAULT 0,
    state TEXT NOT NULL CHECK(state IN ('pending','cleanup_failed')),
    reason TEXT
);

CREATE TABLE IF NOT EXISTS enrollment_requests (
    enrollment_id TEXT PRIMARY KEY,
    status TEXT NOT NULL CHECK(status IN
        ('PENDING','AWAITING_OWNER_APPROVAL','APPROVED','REJECTED','EXPIRED','COMPLETED','CANCELLED')),
    source TEXT NOT NULL DEFAULT 'owner_invitation',
    display_name TEXT NOT NULL CHECK(length(display_name) BETWEEN 1 AND 80),
    device_type TEXT NOT NULL CHECK(device_type IN ('mac','iphone','ipad','other')),
    platform TEXT NOT NULL CHECK(platform IN ('macos','ios','ipados','unknown')),
    app_version TEXT NOT NULL DEFAULT '',
    owner_id TEXT NOT NULL DEFAULT 'unassigned',
    requested_profile TEXT NOT NULL,
    approved_profile TEXT,
    requested_permissions_json TEXT NOT NULL DEFAULT '[]',
    approved_permissions_json TEXT,
    device_public_key TEXT,
    device_key_algorithm TEXT,
    device_nonce TEXT,
    public_key_fingerprint TEXT,
    protocol_version INTEGER NOT NULL DEFAULT 1,
    pairing_code_hash TEXT,
    pairing_code_salt TEXT,
    pairing_code_expires_at TEXT,
    request_token_hash TEXT,
    request_token_salt TEXT,
    failed_attempts INTEGER NOT NULL DEFAULT 0,
    reason TEXT,
    device_id TEXT,
    credential_id TEXT,
    delivery_ref TEXT,
    replaces_device_id TEXT,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    redeemed_at TEXT,
    approved_at TEXT,
    completed_at TEXT,
    rejected_at TEXT,
    cancelled_at TEXT,
    delivery_expires_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_enrollment_status ON enrollment_requests(status);
CREATE INDEX IF NOT EXISTS idx_enrollment_expires ON enrollment_requests(expires_at);
CREATE INDEX IF NOT EXISTS idx_enrollment_fingerprint
    ON enrollment_requests(public_key_fingerprint);

CREATE TABLE IF NOT EXISTS pairing_rate_limits (
    bucket TEXT PRIMARY KEY,
    window_started_at TEXT NOT NULL,
    attempts INTEGER NOT NULL,
    blocked_until TEXT
);
"""


def _ensure_private_dir(path: Path) -> None:
    ensure_private_dir(path.parent)


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
            self._conn.executescript(_SCHEMA_V2)
            columns = {
                row[1] for row in self._conn.execute("PRAGMA table_info(devices)").fetchall()
            }
            if "public_key_fingerprint" not in columns:
                self._conn.execute(
                    "ALTER TABLE devices ADD COLUMN public_key_fingerprint TEXT"
                )
            self._conn.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_devices_active_fingerprint "
                "ON devices(public_key_fingerprint) "
                "WHERE public_key_fingerprint IS NOT NULL AND status = 'active'"
            )
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
                    self._conn.execute(
                        "UPDATE schema_meta SET value = ? WHERE key = ?",
                        (str(DEVICE_SCHEMA_VERSION), DEVICE_SCHEMA_KEY),
                    )
            self._conn.commit()

    def execute(self, sql: str, params: tuple | list = ()) -> sqlite3.Cursor:
        """Run a statement whose rows will **not** be read (writes, DDL, PRAGMA).

        The lock is held only for the ``execute`` call. Reading rows from the
        returned cursor is unsafe: another thread can commit on this shared
        connection before the fetch, which resets the open statement and yields
        a row whose columns are all NULL. Any read must use :meth:`query_one`
        or :meth:`query_all`, which hold the lock through the fetch.
        """
        with self._lock:
            return self._conn.execute(sql, params)

    def query_one(self, sql: str, params: tuple | list = ()) -> sqlite3.Row | None:
        """Run a read and materialize one row while holding the lock."""
        with self._lock:
            return self._conn.execute(sql, params).fetchone()

    def query_all(self, sql: str, params: tuple | list = ()) -> list[sqlite3.Row]:
        """Run a read and materialize every row while holding the lock."""
        with self._lock:
            return self._conn.execute(sql, params).fetchall()

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
        row = self.query_one("PRAGMA integrity_check")
        return str(row[0]) if row else "unknown"
