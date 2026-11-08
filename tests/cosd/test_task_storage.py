"""SQLite storage layer tests."""
from __future__ import annotations

import os
import sqlite3
import stat
import threading
import unittest

from support import CosdStateTest

from cos.config import FILE_MODE, STATE_DIR_MODE

from cosd.storage import BUSY_TIMEOUT_MS, SCHEMA_VERSION, TaskDatabase, database_path


class StorageTests(CosdStateTest):
    def test_init_wal_and_permissions(self):
        db = TaskDatabase(self.state)
        self.assertEqual(db.integrity_check(), "ok")
        mode = db.execute("PRAGMA journal_mode").fetchone()[0]
        self.assertEqual(mode.lower(), "wal")
        self.assertEqual(db.execute("PRAGMA foreign_keys").fetchone()[0], 1)
        path = database_path(self.state)
        self.assertTrue(path.is_file())
        self.assertEqual(stat.S_IMODE(path.stat().st_mode), FILE_MODE)
        self.assertEqual(stat.S_IMODE(path.parent.stat().st_mode) & 0o777, STATE_DIR_MODE)
        row = db.execute("SELECT value FROM schema_meta WHERE key='schema_version'").fetchone()
        self.assertEqual(int(row[0]), SCHEMA_VERSION)

    def test_transaction_rollback(self):
        db = TaskDatabase(self.state)
        before = db.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        with self.assertRaises(RuntimeError):
            with db.transaction() as conn:
                conn.execute(
                    """INSERT INTO tasks(
                        id, kind, title, state, priority, payload_json, created_at, updated_at,
                        schema_version, content_fingerprint, data_class
                    ) VALUES ('x', 'k', 't', 'QUEUED', 0, '{}', 'a', 'a', 1, 'fp', 'internal')"""
                )
                raise RuntimeError("abort")
        after = db.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        self.assertEqual(before, after)

    def test_concurrent_writes(self):
        db = TaskDatabase(self.state)
        errors: list[str] = []

        def worker(i: int):
            try:
                with db.transaction() as conn:
                    conn.execute(
                        """INSERT INTO tasks(
                            id, kind, title, state, priority, payload_json, created_at, updated_at,
                            schema_version, content_fingerprint, data_class
                        ) VALUES (?, 'k', ?, 'QUEUED', 0, '{}', 'a', 'a', 1, ?, 'internal')""",
                        (f"id{i:04d}", f"t{i}", f"fp{i}"),
                    )
            except sqlite3.Error as exc:
                errors.append(str(exc))

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(errors, [])
        self.assertEqual(db.execute("SELECT COUNT(*) FROM tasks").fetchone()[0], 20)

    def test_busy_timeout_configured(self):
        db = TaskDatabase(self.state)
        row = db.execute(f"PRAGMA busy_timeout").fetchone()
        self.assertGreaterEqual(int(row[0]), BUSY_TIMEOUT_MS)


class IntegrityTests(CosdStateTest):
    def test_integrity_after_workload(self):
        db = TaskDatabase(self.state)
        for i in range(5):
            with db.transaction() as conn:
                conn.execute(
                    """INSERT INTO tasks(
                        id, kind, title, state, priority, payload_json, created_at, updated_at,
                        schema_version, content_fingerprint, data_class
                    ) VALUES (?, 'k', 't', 'QUEUED', 0, '{}', 'a', 'a', 1, ?, 'internal')""",
                    (f"z{i}", f"fp{i}"),
                )
        self.assertEqual(db.integrity_check(), "ok")
