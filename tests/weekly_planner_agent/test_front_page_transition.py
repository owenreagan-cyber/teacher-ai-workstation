"""Upcoming-week front-page safety and post-release drift regression."""
import os
import tempfile
import unittest
from datetime import datetime
from unittest import mock
from zoneinfo import ZoneInfo

from scripts.canvas_llm_intake import week_resolution
from scripts.canvas_llm_rollover import ledger as rollover_ledger
from scripts.weekly_planner_agent import cross_source, reconciliation, snapshot
from scripts.weekly_planner_agent.event_store import EventStore
from scripts.weekly_planner_agent.models import SourceChangeEvent
from scripts.weekly_planner_agent import publish

SUBJECTS = ("math", "reading_spelling", "language_arts", "science")
ET = ZoneInfo("America/New_York")


def sources(front_week="Q2W4"):
    pacing = {"status": "OK", "cells": {}}
    canvas = {
        "status": "OK",
        "courses": {
            subject: {
                "front_page": {
                    "title": f"{front_week} {subject}",
                    "page_id": f"{front_week}-{subject}",
                },
                "pages": [
                    {
                        "title": f"{front_week} {subject}",
                        "page_id": f"{front_week}-{subject}",
                    },
                    {
                        "title": f"Q2W5 {subject}",
                        "page_id": f"Q2W5-{subject}",
                    },
                ],
                "assignments": [],
                "announcements": [],
            }
            for subject in SUBJECTS
        },
    }
    return pacing, canvas


def make_snapshot(front_week="Q2W4"):
    pacing, canvas = sources(front_week)
    data = snapshot.blank_snapshot(2, 5, "Q2W5")
    data["pacing"] = pacing
    data["canvas"] = canvas
    return data


class FrontPageTransitionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.env = mock.patch.dict(
            os.environ,
            {"TAW_STATE_ROOT": self.tmp.name},
        )
        self.env.start()
        self.ledger = mock.patch.object(
            rollover_ledger,
            "load_rollover_ledger",
            return_value=None,
        )
        self.ledger.start()

    def tearDown(self):
        self.ledger.stop()
        self.env.stop()
        self.tmp.cleanup()

    def set_date(self, year, month, day):
        return mock.patch.object(
            week_resolution,
            "_now_local",
            return_value=datetime(year, month, day, 12, tzinfo=ET),
        )

    def test_staged_q2w5_with_live_q2w4_is_expected(self):
        with self.set_date(2026, 11, 1):
            due, expected = cross_source.front_page_transition_state(
                make_snapshot()
            )
            found = cross_source.scan(make_snapshot())

        self.assertFalse(due)
        self.assertEqual(expected, set(SUBJECTS))
        self.assertFalse(any(
            e.object_type == "front_page" for e in found
        ))

    def test_prepublication_unrelated_front_page_is_conflict(self):
        with self.set_date(2026, 11, 1):
            found = cross_source.scan(make_snapshot("Q1W1"))

        drift = [e for e in found if e.object_type == "front_page"]
        self.assertEqual(len(drift), 4)
        self.assertTrue(all(
            e.object_identity.endswith(":front_page") for e in drift
        ))

    def test_historical_false_positive_superseded_without_deletion(self):
        store = EventStore(2, 5)
        for subject in SUBJECTS:
            store.record([SourceChangeEvent(
                source="cross_source",
                subject=subject,
                object_type="front_page",
                old_value="Q2W5",
                new_value=f"Q2W4 {subject}",
                classification="cross_source_conflict",
                object_identity=f"{subject}:front_page",
                event_id=f"historical-{subject}",
            )])

        unrelated = SourceChangeEvent(
            source="cross_source",
            subject="math",
            object_type="assessment_date",
            old_value="2026-11-10",
            new_value="2026-11-11",
            classification="cross_source_conflict",
            object_identity="math:assessment_date:sample",
            event_id="unrelated-assessment",
        )
        store.record([unrelated])

        pacing, canvas = sources()
        with self.set_date(2026, 11, 1):
            report = reconciliation.sync_and_detect(
                2, 5, week_id="Q2W5",
                pacing=pacing, canvas=canvas,
            )

        history = store.all()
        old = [e for e in history
               if e.get("object_type") == "front_page"]
        self.assertEqual(len(old), 4)
        self.assertTrue(all(
            e["resolution_action"] == "superseded" for e in old
        ))
        self.assertEqual(len(store.unresolved()), 1)
        self.assertEqual(
            store.unresolved()[0]["event_id"],
            "unrelated-assessment",
        )
        self.assertEqual(len(report["cross_source_conflicts"]), 1)
        self.assertEqual(report["canvas_writes"], 0)
        self.assertEqual(report["notifications_delivered"], 0)

    def test_postrelease_drift_is_new_blocking_event(self):
        with self.set_date(2026, 11, 9):
            found = cross_source.scan(make_snapshot())

        drift = [e for e in found if e.object_type == "front_page"]
        self.assertEqual(len(drift), 4)
        self.assertTrue(all(
            e.object_identity.endswith(":front_page:post_release")
            for e in drift
        ))
        self.assertTrue(all(
            publish._conflict_blocks_publish(e.to_dict())
            for e in drift
        ))

    def test_verified_early_release_detects_drift(self):
        with (
            self.set_date(2026, 11, 6),
            mock.patch.object(
                rollover_ledger,
                "load_rollover_ledger",
                return_value={"lifecycle": "PUBLISHED_VERIFIED"},
            ),
        ):
            found = cross_source.scan(make_snapshot())

        drift = [e for e in found if e.object_type == "front_page"]
        self.assertEqual(len(drift), 4)
        self.assertTrue(all(
            e.object_identity.endswith(":front_page:post_release")
            for e in drift
        ))


if __name__ == "__main__":
    unittest.main()
