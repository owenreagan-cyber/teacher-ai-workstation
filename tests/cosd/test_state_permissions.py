"""Private state-directory permissions: one mechanism, corrected in place.

Regression cover for P0.1 finding A. `cosd/auth.py` used to create
`<state>/cosd` with a bare mkdir, so the directory stayed at the process umask
(0755). `storage._ensure_private_dir()` then called mkdir(mode=0o700), which is
a no-op on an existing directory. The directory was therefore never corrected.

These tests pin the authoritative behavior in `cos.config.ensure_private_dir`:
create 0700, correct a wider existing directory, leave 0700 alone, preserve
tokens and databases, touch nothing recursively, and raise when the required
mode cannot be established.
"""
from __future__ import annotations

import os
import sqlite3
import stat
import unittest
from unittest import mock

from support import CosdStateTest

from cos.config import (
    FILE_MODE,
    STATE_DIR_MODE,
    StatePermissionError,
    ensure_private_dir,
    ensure_state_dir,
)

from cosd.auth import cosd_state_dir, ensure_token, rotate_token
from cosd.storage import TaskDatabase, database_path


def mode_of(path) -> int:
    return stat.S_IMODE(os.stat(path).st_mode)


class NewDirectoryTests(CosdStateTest):
    def test_new_cosd_directory_is_created_at_0700(self):
        target = cosd_state_dir(self.state)
        self.assertFalse(target.exists())

        record = ensure_token(self.state)

        self.assertTrue(record.token)
        self.assertTrue(target.is_dir())
        self.assertEqual(mode_of(target), STATE_DIR_MODE)

    def test_state_root_is_created_at_0700(self):
        from pathlib import Path

        fresh = Path(self._tmp.name) / "fresh-root"
        self.assertFalse(fresh.exists())

        ensure_state_dir(fresh)

        self.assertEqual(mode_of(fresh), STATE_DIR_MODE)


class ExistingDirectoryTests(CosdStateTest):
    def test_world_readable_directory_is_corrected_in_place(self):
        target = cosd_state_dir(self.state)
        target.mkdir(parents=True, exist_ok=True)
        os.chmod(target, 0o755)
        self.assertEqual(mode_of(target), 0o755)

        ensure_token(self.state)

        self.assertEqual(mode_of(target), STATE_DIR_MODE)
        # The state root holds the audit log and config, so it is secured too.
        self.assertEqual(mode_of(self.state), STATE_DIR_MODE)

    def test_already_private_directory_is_left_alone(self):
        target = cosd_state_dir(self.state)
        target.mkdir(parents=True, exist_ok=True)
        os.chmod(target, STATE_DIR_MODE)
        before = os.stat(target)

        ensure_private_dir(target)

        after = os.stat(target)
        self.assertEqual(mode_of(target), STATE_DIR_MODE)
        # Already private: the directory is not re-created or chmod-ed.
        self.assertEqual(before.st_ino, after.st_ino)
        self.assertEqual(before.st_mtime_ns, after.st_mtime_ns)

    def test_correction_is_not_recursive(self):
        target = cosd_state_dir(self.state)
        target.mkdir(parents=True, exist_ok=True)
        os.chmod(target, 0o755)
        nested = target / "nested.txt"
        nested.write_text("keep me\n", encoding="utf-8")
        os.chmod(nested, 0o644)

        ensure_private_dir(target)

        self.assertEqual(mode_of(target), STATE_DIR_MODE)
        self.assertEqual(mode_of(nested), 0o644)
        self.assertEqual(nested.read_text(encoding="utf-8"), "keep me\n")


class ExistingContentTests(CosdStateTest):
    def test_existing_token_and_metadata_are_preserved(self):
        first = ensure_token(self.state)
        token_path = cosd_state_dir(self.state) / "api.token"
        meta_path = cosd_state_dir(self.state) / "auth.meta.json"
        self.assertEqual(mode_of(token_path), FILE_MODE)
        self.assertEqual(mode_of(meta_path), FILE_MODE)
        token_before = token_path.read_text(encoding="utf-8")
        meta_before = meta_path.read_text(encoding="utf-8")

        # A wider directory must not disturb the credential files or rotate the token.
        os.chmod(cosd_state_dir(self.state), 0o755)
        second = ensure_token(self.state)

        self.assertEqual(second.token, first.token)
        self.assertEqual(second.version, first.version)
        self.assertEqual(token_path.read_text(encoding="utf-8"), token_before)
        self.assertEqual(meta_path.read_text(encoding="utf-8"), meta_before)
        self.assertEqual(mode_of(token_path), FILE_MODE)
        self.assertEqual(mode_of(cosd_state_dir(self.state)), STATE_DIR_MODE)

    def test_rotation_keeps_private_directory_and_file_modes(self):
        ensure_token(self.state)
        os.chmod(cosd_state_dir(self.state), 0o755)

        rotated = rotate_token(self.state)

        self.assertEqual(rotated.version, 2)
        self.assertEqual(mode_of(cosd_state_dir(self.state)), STATE_DIR_MODE)
        self.assertEqual(mode_of(cosd_state_dir(self.state) / "api.token"), FILE_MODE)
        self.assertEqual(mode_of(cosd_state_dir(self.state) / "auth.meta.json"), FILE_MODE)
        # The rotated token must be usable immediately.
        self.assertEqual(ensure_token(self.state).token, rotated.token)

    def test_existing_database_and_rows_survive_correction(self):
        db = TaskDatabase(self.state)
        with db.transaction() as conn:
            conn.execute(
                "INSERT INTO tasks(id, kind, title, state, priority, payload_json, created_at,"
                " updated_at, schema_version, content_fingerprint, data_class)"
                " VALUES ('keep-me', 'ask', 'survivor', 'QUEUED', 0, '{}', 'a', 'a', 1, 'fp', 'internal')"
            )
        path = database_path(self.state)
        rows_before = [tuple(row) for row in db.execute("SELECT id, title FROM tasks").fetchall()]
        os.chmod(path.parent, 0o755)

        ensured = ensure_private_dir(path.parent)

        self.assertEqual(ensured, path.parent)
        self.assertEqual(mode_of(path.parent), STATE_DIR_MODE)
        self.assertEqual(mode_of(path), FILE_MODE)
        with sqlite3.connect(path) as conn:
            rows_after = conn.execute("SELECT id, title FROM tasks").fetchall()
        self.assertEqual(rows_before, rows_after)
        self.assertEqual(rows_after, [("keep-me", "survivor")])


class FailClosedTests(CosdStateTest):
    def test_unsecurable_directory_raises(self):
        target = cosd_state_dir(self.state)
        target.mkdir(parents=True, exist_ok=True)
        os.chmod(target, 0o777)

        # Simulate a filesystem where chmod silently does not take effect.
        with mock.patch("cos.config.os.chmod", lambda *a, **k: None):
            with self.assertRaises(StatePermissionError):
                ensure_private_dir(target)

    def test_token_creation_fails_closed_when_directory_cannot_be_secured(self):
        target = cosd_state_dir(self.state)
        target.mkdir(parents=True, exist_ok=True)
        os.chmod(target, 0o777)

        with mock.patch("cos.config.os.chmod", lambda *a, **k: None):
            with self.assertRaises(StatePermissionError):
                ensure_token(self.state)

        # No credential may be written into a directory that is still exposed.
        self.assertFalse((target / "api.token").exists())


if __name__ == "__main__":
    unittest.main()
