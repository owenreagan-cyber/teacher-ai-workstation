"""Event-store lifecycle + resolution tests."""
from __future__ import annotations

import os
import tempfile
import unittest
from unittest import mock

from scripts.weekly_planner_agent import snapshot as snap
from scripts.weekly_planner_agent.event_store import EventStore
from scripts.weekly_planner_agent.models import SourceChangeEvent


def _event(new_value="2026-11-06"):
    return SourceChangeEvent(
        source="pacing", subject="math", object_type="assessment_date",
        old_value="2026-11-05", new_value=new_value,
        classification="assessment_date_changed", object_identity="math|Thursday",
        week_id="Q2W3",
    )


class EventStoreTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp()
        self.env = mock.patch.dict(os.environ, {"TAW_STATE_ROOT": self.tmp})
        self.env.start()

    def tearDown(self) -> None:
        self.env.stop()

    def test_dedup_repeated_observation(self) -> None:
        store = EventStore(2, 3)
        ev = _event()
        ev.event_id = "e1"
        self.assertEqual(store.record([ev])["added"], 1)
        # Repeated observation of the same underlying change -> no duplicate.
        self.assertEqual(store.record([ev])["added"], 0)
        self.assertEqual(store.record([ev])["skipped"], 1)
        self.assertEqual(len(store.all()), 1)

    def test_genuinely_new_change_gets_new_identity(self) -> None:
        store = EventStore(2, 3)
        e1 = _event("2026-11-06")
        e1.event_id = "e1"
        store.record([e1])
        e2 = _event("2026-11-07")  # different new value
        e2.event_id = "e2"
        store.record([e2])
        self.assertEqual(len(store.all()), 2)

    def test_resolution_and_ignore_persist(self) -> None:
        store = EventStore(2, 3)
        ev = _event()
        ev.event_id = "e1"
        store.record([ev])
        store.resolve("e1", action="override_keep_current")
        record = store.all()[0]
        self.assertEqual(record["teacher_override"]["authority"], "OWNER_INSTRUCTION")
        self.assertEqual(len(store.unresolved()), 0)
        # Ignore for now keeps the event visible (not erased).
        store.resolve("e1", action="ignore")
        self.assertEqual(store.all()[0]["resolution_status"], "IGNORED")
        self.assertEqual(len(store.all()), 1)

    def test_resolution_restart_persist(self) -> None:
        store = EventStore(2, 3)
        ev = _event()
        ev.event_id = "e1"
        store.record([ev])
        store.resolve("e1", action="approve_updates")
        # Fresh store instance reads the same durable state.
        store2 = EventStore(2, 3)
        self.assertEqual(store2.all()[0]["resolution_status"], "APPROVED")

    def test_override_persists_and_outranks_refresh(self) -> None:
        store = EventStore(2, 3)
        ev = _event()
        ev.event_id = "e1"
        store.record([ev])
        store.resolve("e1", action="override_keep_current")
        # A later ordinary refresh of the SAME change is deduped (no new alert),
        # and the override record remains authoritative.
        store.record([ev])
        record = store.all()[0]
        self.assertEqual(record["teacher_override"]["authority"], "OWNER_INSTRUCTION")
        self.assertEqual(len(store.all()), 1)


if __name__ == "__main__":
    unittest.main()
