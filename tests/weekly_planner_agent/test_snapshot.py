"""Snapshot persistence tests (fake/local, no Canvas)."""
from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts.weekly_planner_agent import snapshot as snap


class SnapshotTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp()
        self.env = mock.patch.dict(os.environ, {"TAW_STATE_ROOT": self.tmp})
        self.env.start()

    def tearDown(self) -> None:
        self.env.stop()

    def test_first_baseline_has_no_prior(self) -> None:
        self.assertFalse(snap.has_prior(2, 3))
        self.assertIsNone(snap.load(2, 3))

    def test_save_then_load_roundtrip(self) -> None:
        s = snap.blank_snapshot(2, 3, "Q2W3")
        s["pacing"]["status"] = snap.SNAPSHOT_OK
        s["pacing"]["cells"] = {"math|Thursday": {"lesson": "WA8"}}
        snap.save(2, 3, s)
        loaded = snap.load(2, 3)
        self.assertEqual(loaded["snapshot_id"], s["snapshot_id"])
        self.assertEqual(loaded["pacing"]["cells"]["math|Thursday"]["lesson"], "WA8")

    def test_restart_preserves_snapshot(self) -> None:
        s = snap.blank_snapshot(2, 3, "Q2W3")
        s["pacing"]["cells"] = {"math|Thursday": {"lesson": "L39"}}
        snap.save(2, 3, s)
        # Simulate a fresh process: re-read from disk (no in-memory state).
        reloaded = snap.load(2, 3)
        self.assertEqual(reloaded["pacing"]["cells"]["math|Thursday"]["lesson"], "L39")
        self.assertTrue(snap.has_prior(2, 3))
        self.assertEqual(len(snap.history(2, 3)), 1)

    def test_corrupted_snapshot_fails_safely(self) -> None:
        snap.snapshot_path(2, 3).parent.mkdir(parents=True, exist_ok=True)
        snap.snapshot_path(2, 3).write_text("{ not json", encoding="utf-8")
        with self.assertRaises(snap.SnapshotCorrupt):
            snap.load(2, 3)

    def test_unknown_schema_fails_safely(self) -> None:
        bad = snap.blank_snapshot(2, 3, "Q2W3")
        bad["schema_version"] = 999
        snap.snapshot_path(2, 3).parent.mkdir(parents=True, exist_ok=True)
        snap.snapshot_path(2, 3).write_text(
            __import__("json").dumps(bad), encoding="utf-8")
        with self.assertRaises(snap.SnapshotCorrupt):
            snap.load(2, 3)

    def test_fingerprint_is_stable(self) -> None:
        cells = {"a": 1, "b": {"c": 2}}
        self.assertEqual(snap.fingerprint(cells), snap.fingerprint(dict(cells)))


if __name__ == "__main__":
    unittest.main()
