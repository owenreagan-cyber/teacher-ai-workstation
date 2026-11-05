"""Historical reminder cleanup: deterministic, isolated tests."""
import os
import tempfile
import unittest
from unittest import mock

from scripts.weekly_planner_agent import reconciliation
from scripts.weekly_planner_agent.event_store import EventStore
from scripts.weekly_planner_agent.models import SourceChangeEvent

OLD = "2026-10-27T19:00:00Z"
FUTURE = "2026-11-10T19:00:00Z"

SUBJECTS = {
    "homeroom": 2,
    "language_arts": 3,
    "math": 4,
    "reading_spelling": 8,
}


def event(subject, title, timestamp, eid):
    return SourceChangeEvent(
        source="canvas",
        subject=subject,
        object_type="reminder",
        old_value=timestamp,
        new_value="2026-11-11",
        classification="reminder_obsolete",
        object_identity=f"{subject}:reminder:{title}",
        week_id="Q2W5",
        event_id=eid,
        requires_teacher_approval=True,
    )


def course(items):
    return {
        "announcements": items,
        "pages": [],
        "assignments": [],
    }


class HistoryCleanupTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.env = mock.patch.dict(
            os.environ, {"TAW_STATE_ROOT": self.tmp.name}
        )
        self.env.start()
        self.store = EventStore(2, 5)

    def tearDown(self):
        self.env.stop()
        self.tmp.cleanup()

    def sync(self, courses, status="OK"):
        return reconciliation.sync_and_detect(
            2, 5,
            week_id="Q2W5",
            pacing={"status": "OK", "cells": {}},
            canvas={"status": status, "courses": courses},
        )

    def test_17_historical_events_superseded_and_retained(self):
        events = []
        courses = {}

        for subject, count in SUBJECTS.items():
            items = []
            for i in range(count):
                title = f"Old Reminder {subject} {i}"
                events.append(event(
                    subject, title, OLD, f"old-{subject}-{i}"
                ))
                items.append({
                    "title": title, "delayed_post_at": OLD
                })
            courses[subject] = course(items)

        self.store.record(events)
        result = self.sync(courses)

        self.assertEqual(result["historical_reminders_superseded"], 17)
        self.assertEqual(len(self.store.all()), 17)
        self.assertEqual(len(self.store.unresolved()), 0)
        self.assertTrue(all(
            e["resolution_action"] == "superseded"
            and e["resolved_by"] == "system"
            for e in self.store.all()
        ))
        self.assertEqual(result["canvas_writes"], 0)
        self.assertEqual(result["notifications_delivered"], 0)

        again = self.sync(courses)
        self.assertEqual(again["historical_reminders_superseded"], 0)
        self.assertEqual(len(self.store.all()), 17)

    def test_upcoming_reminder_is_preserved(self):
        self.store.record([
            event("math", "Old Reminder", OLD, "old"),
            event("math", "Upcoming Reminder", FUTURE, "future"),
        ])

        result = self.sync({
            "math": course([
                {"title": "Old Reminder", "delayed_post_at": OLD},
                {"title": "Upcoming Reminder", "delayed_post_at": FUTURE},
            ])
        })

        self.assertEqual(result["historical_reminders_superseded"], 1)
        self.assertEqual(
            [e["event_id"] for e in self.store.unresolved()],
            ["future"],
        )

    def test_changed_timestamp_not_superseded(self):
        self.store.record([
            event("math", "Old Reminder", OLD, "old")
        ])

        result = self.sync({
            "math": course([
                {
                    "title": "Old Reminder",
                    "delayed_post_at": "2026-10-26T19:00:00Z",
                }
            ])
        })

        self.assertEqual(result["historical_reminders_superseded"], 0)
        self.assertEqual(len(self.store.unresolved()), 1)

    def test_source_outage_preserves_event(self):
        self.store.record([
            event("math", "Old Reminder", OLD, "old")
        ])

        result = self.sync({
            "math": course([
                {"title": "Old Reminder", "delayed_post_at": OLD}
            ])
        }, status="UNAVAILABLE")

        self.assertEqual(result["historical_reminders_superseded"], 0)
        self.assertEqual(len(self.store.unresolved()), 1)

    def test_duplicate_title_is_ambiguous(self):
        self.store.record([
            event("math", "Old Reminder", OLD, "old")
        ])

        item = {"title": "Old Reminder", "delayed_post_at": OLD}

        result = self.sync({
            "math": course([item, dict(item)])
        })

        self.assertEqual(result["historical_reminders_superseded"], 0)
        self.assertEqual(len(self.store.unresolved()), 1)


if __name__ == "__main__":
    unittest.main()
