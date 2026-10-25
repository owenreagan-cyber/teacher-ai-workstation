"""Fake-client live reconciliation: the full live_sync path, no network.

Mocks the live source adapters and proves the end-to-end observe→detect→impact→
assessment-watch pipeline reports a real assessment date change with zero
Canvas writes and zero notifications delivered.
"""
from __future__ import annotations

import os
import tempfile
import unittest
from unittest import mock

from scripts.weekly_planner_agent import service


def _pacing(cells):
    return {
        "status": "OK",
        "observed_at": "2026-10-24T12:00:00Z",
        "identity": {"name": "FPK", "tab": "4A - Reagan", "spreadsheet_id": "fake"},
        "source_timestamp": "2026-10-24T12:00:00Z",
        "cells": cells,
    }


def _canvas(assignment_due="2026-11-05T23:59:00Z"):
    return {
        "status": "OK",
        "observed_at": "2026-10-24T12:00:00Z",
        "courses": {
            "math": {
                "front_page": {"title": "Q2W3 Math", "page_id": "q2w3"},
                "assignments": [{"id": "a1", "name": "SM5: Written Assessment 8",
                                 "due_at": assignment_due}],
                "announcements": [],
                "pages": [], "assignment_groups": [],
            }
        },
    }


def _math_cells(date):
    return {
        "math|Thursday": {
            "lesson": "Written Assessment 8", "chapter": None,
            "classwork": ["Written Assessment 8"], "homework": [],
            "assessment": {"name": "Written Assessment 8", "date": date, "day": "Thursday"},
        },
    }


class LiveReconciliationTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.env = mock.patch.dict(os.environ, {"TAW_STATE_ROOT": self.tmp})
        self.env.start()

    def tearDown(self):
        self.env.stop()

    def test_live_sync_detects_assessment_date_change(self):
        with mock.patch("scripts.weekly_planner_agent.live_sources.live_sync_sources") as m:
            # Baseline: pacing says Thursday (2026-11-05).
            m.return_value = {"pacing": _pacing(_math_cells("2026-11-05")),
                              "canvas": _canvas("2026-11-05T23:59:00Z")}
            report = service.live_sync(2, 3)
            self.assertTrue(report["baseline"])
            self.assertEqual(report["live"]["canvas_writes"], 0)

            # Change: pacing says Friday (2026-11-06); Canvas still due Thursday.
            m.return_value = {"pacing": _pacing(_math_cells("2026-11-06")),
                              "canvas": _canvas("2026-11-05T23:59:00Z")}
            report = service.live_sync(2, 3)
            self.assertFalse(report["baseline"])

        events = [e for e in report["events"] if e["classification"] == "assessment_date_changed"]
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["old_value"], "2026-11-05")
        self.assertEqual(events[0]["new_value"], "2026-11-06")

        watch = report["assessment_watch"]
        self.assertEqual(len(watch), 1)
        self.assertEqual(watch[0]["old_date"], "2026-11-05")
        self.assertEqual(watch[0]["new_date"], "2026-11-06")
        self.assertEqual(watch[0]["canvas_state"]["assignment"]["due_at"], "2026-11-05T23:59:00Z")
        self.assertIn("Would you like me to prepare", watch[0]["ask"])

        # Hard read-only + non-live guarantees.
        self.assertEqual(report["live"]["canvas_read_only"], True)
        self.assertEqual(report["live"]["canvas_writes"], 0)
        self.assertEqual(report["live"]["notifications_delivered"], 0)
        self.assertEqual(report["canvas_writes"], 0)
        self.assertEqual(report["notifications_delivered"], 0)


if __name__ == "__main__":
    unittest.main()
