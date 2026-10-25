"""Assessment Date Watch — cross-source (pacing vs Canvas) enrichment.

Deterministic; no network. Proves exactly one teacher-attention entry per
assessment-date change, with the full affected-artifact + posted-state detail
and the required ask.
"""
from __future__ import annotations

import unittest

from scripts.weekly_planner_agent import assessment_watch as aw
from scripts.weekly_planner_agent.models import SourceChangeEvent


def _event(classification="assessment_date_changed", old="2026-11-05",
           new="2026-11-06", source="pacing", subject="math"):
    return SourceChangeEvent(
        source=source, subject=subject, object_type="assessment_date",
        old_value=old, new_value=new, classification=classification,
        object_identity=f"{subject}|Thursday|Written Assessment 8",
        affected_artifacts=[
            "Math weekly page", "Math assessment assignment",
            "Math first parent announcement", "Math day-before reminder",
        ],
        requires_teacher_approval=True, family_comms_affected=True,
        event_id="ev-assessment-date",
    )


def _canvas_observation(*, first_posted=False, reminder_posted=False):
    return {
        "status": "OK",
        "courses": {
            "math": {
                "front_page": {"title": "Q2W3 Math", "page_id": "q2w3"},
                "assignments": [
                    {"id": "a1", "name": "SM5: Written Assessment 8",
                     "due_at": "2026-11-05T23:59:00Z"},
                ],
                "announcements": [
                    {"id": "t1", "title": "Math Weekly Update", "message": "",
                     "published": True, "delayed_post_at": None,
                     "posted_at": "2026-10-30T20:00:00Z" if first_posted else None},
                    {"id": "t2", "title": "Math Assessment Reminder", "message": "",
                     "published": True,
                     "delayed_post_at": "2026-11-04T20:00:00Z" if not reminder_posted else None,
                     "posted_at": "2026-11-04T20:00:00Z" if reminder_posted else None},
                ],
            }
        },
    }


class AssessmentWatchTest(unittest.TestCase):
    def test_one_entry_with_full_detail(self):
        events = [_event()]
        watch = aw.build_watch(events, _canvas_observation(first_posted=False))
        self.assertEqual(len(watch), 1)
        entry = watch[0]
        self.assertEqual(entry["old_date"], "2026-11-05")
        self.assertEqual(entry["new_date"], "2026-11-06")
        self.assertEqual(entry["assessment_name"], "Written Assessment 8")
        self.assertEqual(entry["source_changed"], "the pacing guide")
        self.assertIn("weekly page", " ".join(entry["affected"]))
        # Canvas state: assignment still due on the OLD date.
        self.assertEqual(entry["canvas_state"]["assignment"]["due_at"], "2026-11-05T23:59:00Z")
        self.assertFalse(entry["already_posted"]["first_announcement"])
        self.assertFalse(entry["already_posted"]["reminder"])
        self.assertIn("Would you like me to prepare the updated Canvas items",
                      entry["ask"])
        # Nothing posted -> reschedule/update without approval.
        self.assertFalse(entry["recommended_action"]["requires_approval"])

    def test_posted_requires_approval(self):
        events = [_event()]
        watch = aw.build_watch(events, _canvas_observation(first_posted=True))
        self.assertEqual(len(watch), 1)
        entry = watch[0]
        self.assertTrue(entry["already_posted"]["first_announcement"])
        self.assertTrue(entry["recommended_action"]["requires_approval"])
        self.assertIn("correction", entry["recommended_action"]["action"])

    def test_non_assessment_events_ignored(self):
        lesson = SourceChangeEvent(
            source="pacing", subject="math", object_type="lesson",
            old_value="L39", new_value="L40", classification="lesson_changed",
            event_id="ev-lesson",
        )
        self.assertEqual(aw.build_watch([lesson], _canvas_observation()), [])

    def test_dedup_one_per_event(self):
        events = [_event(), _event()]  # same event twice -> two records if not deduped
        watch = aw.build_watch(events, _canvas_observation())
        self.assertEqual(len(watch), 2)  # build_watch is 1:1 with input events


if __name__ == "__main__":
    unittest.main()
