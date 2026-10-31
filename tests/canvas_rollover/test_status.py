"""Chief of Staff rollover status lifecycle regression tests."""
import unittest
from datetime import date, datetime, timezone
from unittest import mock

from scripts.canvas_llm_rollover import rollover, schedule, status
from scripts.canvas_llm_intake import week_resolution
import scripts.instructional_weeks as instructional_weeks


class PublishedStatusTest(unittest.TestCase):
    def setUp(self):
        self.readiness = {
            "manifest": {
                "from_week": "Q2W3",
                "to_week": "Q2W4",
                "scheduled_at": "2026-10-30T20:00:00Z",
                "timezone": "America/New_York",
                "academic_courses": [],
                "homeroom": {"course_id": 26429},
                "weekly_announcements": [],
            },
            "blockers": [],
            "ready": True,
            "needs_owen": False,
        }
        self.now = datetime(2026, 10, 31, 19, 17, tzinfo=timezone.utc)

    def _calendar_patches(self):
        return (
            mock.patch.object(
                instructional_weeks,
                "week_range",
                return_value=(date(2026, 11, 2), date(2026, 11, 6)),
            ),
            mock.patch.object(
                week_resolution,
                "find_week",
                return_value={"quarter": 2, "week": 4},
            ),
        )

    def test_published_verified_does_not_require_new_publication_time(self):
        patches = self._calendar_patches()
        with (
            mock.patch.object(
                rollover, "build_readiness", return_value=self.readiness
            ),
            mock.patch.object(
                rollover.ledger, "load_rollover_ledger",
                return_value={"lifecycle": schedule.PUBLISHED_VERIFIED},
            ),
            mock.patch.object(
                schedule, "resolve_publication_time",
                side_effect=AssertionError(
                    "published rollover must not re-enter publication-time gate"
                ),
            ) as time_gate,
            patches[0],
            patches[1],
        ):
            result = rollover.status(2, 3, 2, 4, now=self.now)

        self.assertEqual(result["status"], schedule.PUBLISHED_VERIFIED)
        self.assertFalse(result["publication_time_required"])
        self.assertFalse(result["needs_owen"])
        self.assertFalse(any(
            "Owner-selected publication time required" in item
            for item in result["blockers"]
        ))
        time_gate.assert_not_called()

        rendered = status._text(result)
        self.assertIn("Completed rollover window:", rendered)
        self.assertNotIn("OWNER SELECTION REQUIRED", rendered)

    def test_unpublished_expired_window_still_requires_owner_time(self):
        patches = self._calendar_patches()
        with (
            mock.patch.object(
                rollover, "build_readiness", return_value=self.readiness
            ),
            mock.patch.object(
                rollover.ledger, "load_rollover_ledger", return_value=None
            ),
            mock.patch.object(
                schedule,
                "resolve_publication_time",
                return_value={
                    "requires_owner_time": True,
                    "canonical_scheduled_at": "2026-10-30T20:00:00Z",
                },
            ),
            patches[0],
            patches[1],
        ):
            result = rollover.status(2, 3, 2, 4, now=self.now)

        self.assertTrue(result["publication_time_required"])
        self.assertTrue(result["needs_owen"])
        self.assertTrue(any(
            "Owner-selected publication time required" in item
            for item in result["blockers"]
        ))


if __name__ == "__main__":
    unittest.main()
