"""Live read-only source adapters: read-only guard + pacing normalization.

Deterministic, no network, no credentials. Proves the live reconciliation path
cannot issue non-GET verbs and normalizes pacing faithfully.
"""
from __future__ import annotations

import unittest

from scripts.weekly_planner_agent import live_sources
from scripts.weekly_planner_agent.live_sources import (
    NonGetVerbError,
    ReadOnlyCanvasClient,
)


class _FakeCanvas:
    """Minimal GET-only fake backing the read-only guard."""

    def list_pages(self, course_id):
        return [{"url": "q2w3", "title": "Q2W3", "body": "<p>x</p>",
                 "published": True, "front_page": True}]

    def list_assignments(self, course_id):
        return []

    def list_announcements(self, course_id):
        return []

    def list_assignment_groups(self, course_id):
        return []

    def get_course(self, course_id):
        return {"id": course_id, "name": "Math"}

    def list_active_announcements(self, context_codes=None):
        return []


class ReadOnlyGuardTest(unittest.TestCase):
    def test_read_methods_pass_through(self):
        guard = ReadOnlyCanvasClient(client=_FakeCanvas())
        pages = guard.list_pages(26404)
        self.assertEqual(pages[0]["page_id"], "q2w3")  # url exposed as stable id
        self.assertEqual(guard.get_course(26404)["name"], "Math")

    def test_non_get_verb_fails_closed(self):
        guard = ReadOnlyCanvasClient(client=_FakeCanvas())
        for name, verb in (
            ("create_assignment", "POST"),
            ("update_page", "PUT"),
            ("post_announcement", "POST"),
            ("delete_assignment", "DELETE"),
            ("patch_page", "PATCH"),
            ("set_front_page", "PUT"),
        ):
            with self.assertRaises(NonGetVerbError):
                getattr(guard, name)(26404)
            self.assertGreaterEqual(guard.mutation_audit[verb], 1, name)

    def test_source_has_no_write_verbs(self):
        import pathlib
        source = pathlib.Path(live_sources.__file__).read_text(encoding="utf-8")
        for tok in (".post(", ".put(", ".patch(", ".delete(",
                    'method="POST"', 'method="PUT"', 'method="PATCH"', 'method="DELETE"'):
            self.assertNotIn(tok, source)


class PacingNormalizationTest(unittest.TestCase):
    def test_math_lesson_and_assessment(self):
        week = {
            "week": {"code": "Q2W3"},
            "days": {
                "Monday": {"date": "2026-10-26", "subjects": {"math": {"raw": "L31"}}},
                "Tuesday": {"date": "2026-10-27", "subjects": {"math": {"raw": "WA8"}}},
            },
            "unitContext": {},
        }
        cells = live_sources.normalize_pacing_cells(week, active_subjects=["math"])
        self.assertEqual(cells["math|Monday"]["lesson"], "Lesson 31")
        self.assertEqual(cells["math|Tuesday"]["assessment"]["name"], "Written Assessment 8")
        self.assertEqual(cells["math|Tuesday"]["assessment"]["date"], "2026-10-27")
        self.assertIsNone(cells["math|Monday"]["assessment"])

    def test_science_chapter_and_quiz(self):
        week = {
            "week": {"code": "Q2W3"},
            "days": {
                "Monday": {"date": "2026-10-26", "subjects": {"science": {"raw": "U1 Ch5 Reading"}}},
                "Tuesday": {"date": "2026-10-27", "subjects": {"science": {"raw": "U1 Ch5 Finish + Quiz"}}},
            },
            "unitContext": {"science": "Force and Motion"},
        }
        cells = live_sources.normalize_pacing_cells(week, active_subjects=["science"])
        self.assertIsNotNone(cells["science|Monday"]["lesson"])
        self.assertIsNotNone(cells["science|Tuesday"]["assessment"])

    def test_course_map_subject_keys(self):
        course_map = live_sources.build_course_map(2)  # Q2: science active
        self.assertEqual(course_map["math"], 26404)
        self.assertEqual(course_map["reading_spelling"], 26442)
        self.assertEqual(course_map["language_arts"], 28171)
        self.assertEqual(course_map["science"], 28166)
        self.assertEqual(course_map["homeroom"], 26429)


if __name__ == "__main__":
    unittest.main()
