"""Change-detection engine tests (fake/local fixtures)."""
from __future__ import annotations

import json
import unittest

from scripts.weekly_planner_agent import change_detection as cd
from scripts.weekly_planner_agent import snapshot as snap


def _snap(*, week_id="Q2W3", cells=None, canvas=None):
    s = snap.blank_snapshot(2, 3, week_id)
    s["pacing"]["status"] = snap.SNAPSHOT_OK
    s["pacing"]["identity"] = {"name": "FPK Pacing", "tab": "4A"}
    s["pacing"]["cells"] = cells or {}
    if canvas:
        s["canvas"] = canvas
    return s


def _math_cell(day, date):
    return {
        "math|" + day: {
            "lesson": "WA8", "chapter": None, "classwork": ["WA8"], "homework": [],
            "assessment": {"name": "Written Assessment 8", "date": date, "day": day},
        }
    }


class ChangeDetectionTest(unittest.TestCase):
    def test_assessment_date_changed(self) -> None:
        prev = _snap(cells=_math_cell("Thursday", "2026-11-05"))
        curr = _snap(cells=_math_cell("Thursday", "2026-11-06"))
        events = cd.detect_changes(prev, curr)
        kinds = {e.classification for e in events}
        self.assertIn(cd.CHANGE_ASSESSMENT_DATE, kinds)
        ev = next(e for e in events if e.classification == cd.CHANGE_ASSESSMENT_DATE)
        self.assertTrue(ev.family_comms_affected)
        self.assertTrue(ev.live_canvas_stale)
        self.assertTrue(ev.requires_teacher_approval)
        self.assertIn("Math weekly page", ev.affected_artifacts)
        self.assertIn("Math day-before reminder", ev.affected_artifacts)

    def test_assessment_identity_changed(self) -> None:
        prev = _snap(cells=_math_cell("Thursday", "2026-11-05"))
        curr = _snap(cells={
            "math|Thursday": {
                "lesson": "WA9", "chapter": None, "classwork": ["WA9"], "homework": [],
                "assessment": {"name": "Written Assessment 9", "date": "2026-11-05", "day": "Thursday"},
            }
        })
        kinds = {e.classification for e in cd.detect_changes(prev, curr)}
        self.assertIn(cd.CHANGE_ASSESSMENT_IDENTITY, kinds)

    def test_lesson_and_homework_changed(self) -> None:
        prev = _snap(cells={"math|Monday": {"lesson": "L39", "homework": ["39 hw"]}})
        curr = _snap(cells={"math|Monday": {"lesson": "L40", "homework": []}})
        kinds = {e.classification for e in cd.detect_changes(prev, curr)}
        self.assertIn(cd.CHANGE_LESSON, kinds)
        self.assertIn(cd.CHANGE_HOMEWORK, kinds)

    def test_source_identity_changed(self) -> None:
        prev = _snap(cells=_math_cell("Thursday", "2026-11-05"))
        curr = _snap(cells=_math_cell("Thursday", "2026-11-05"))
        curr["pacing"]["identity"] = {"name": "Different Sheet", "tab": "4B"}
        kinds = {e.classification for e in cd.detect_changes(prev, curr)}
        self.assertIn(cd.CHANGE_SOURCE_IDENTITY, kinds)

    def test_source_stale_is_not_deletion(self) -> None:
        prev = _snap(cells=_math_cell("Thursday", "2026-11-05"))
        curr = _snap(cells=_math_cell("Thursday", "2026-11-05"))
        curr["pacing"]["status"] = snap.SNAPSHOT_UNAVAILABLE
        events = cd.detect_changes(prev, curr)
        kinds = {e.classification for e in events}
        self.assertIn(cd.CHANGE_SOURCE_STALE, kinds)
        self.assertNotIn(cd.CHANGE_ASSESSMENT_REMOVED, kinds)

    def test_stable_event_id_dedup(self) -> None:
        prev = _snap(cells=_math_cell("Thursday", "2026-11-05"))
        curr = _snap(cells=_math_cell("Thursday", "2026-11-06"))
        first = cd.detect_changes(prev, curr)
        second = cd.detect_changes(prev, curr)
        self.assertEqual([e.event_id for e in first], [e.event_id for e in second])

    def test_canvas_assignment_due_and_missing(self) -> None:
        prev_canvas = {"status": "OK", "observed_at": "2026-11-01T00:00:00Z", "courses": {
            "math": {"course_id": 26404, "front_page": None, "pages": [],
                     "assignments": [{"id": "a1", "name": "HW39", "due_at": "2026-11-04T03:59:00Z"}],
                     "announcements": []},
        }}
        curr_canvas = {"status": "OK", "observed_at": "2026-11-02T00:00:00Z", "courses": {
            "math": {"course_id": 26404, "front_page": None, "pages": [],
                     "assignments": [{"id": "a1", "name": "HW39", "due_at": "2026-11-05T03:59:00Z"}],
                     "announcements": []},
        }}
        prev = _snap(canvas=prev_canvas)
        curr = _snap(canvas=curr_canvas)
        kinds = {e.classification for e in cd.detect_changes(prev, curr)}
        self.assertIn(cd.CHANGE_ASSIGNMENT_DUE, kinds)

        # Now the assignment disappears entirely.
        curr_canvas["courses"]["math"]["assignments"] = []
        kinds = {e.classification for e in cd.detect_changes(prev, _snap(canvas=curr_canvas))}
        self.assertIn(cd.CHANGE_ASSIGNMENT_MISSING, kinds)

    def test_direct_canvas_edit_detected(self) -> None:
        prev_canvas = {"status": "OK", "courses": {"math": {
            "course_id": 26404, "front_page": None,
            "pages": [{"page_id": "p1", "title": "Q2W3", "body_hash": "aaaa"}],
            "assignments": [], "announcements": [],
        }}}
        curr_canvas = json.loads(json.dumps(prev_canvas))
        curr_canvas["courses"]["math"]["pages"][0]["body_hash"] = "bbbb"
        kinds = {e.classification for e in cd.detect_changes(_snap(canvas=prev_canvas), _snap(canvas=curr_canvas))}
        self.assertIn(cd.CHANGE_PAGE_BODY, kinds)

    def test_reminder_duplicated_and_missing(self) -> None:
        prev_canvas = {"status": "OK", "courses": {"math": {
            "course_id": 26404, "front_page": None, "pages": [], "assignments": [],
            "announcements": [{"id": "r1", "title": "Math Assessment Reminder"}],
        }}}
        dup_canvas = json.loads(json.dumps(prev_canvas))
        dup_canvas["courses"]["math"]["announcements"].append(
            {"id": "r2", "title": "Math Assessment Reminder"})
        kinds = {e.classification for e in cd.detect_changes(_snap(canvas=prev_canvas), _snap(canvas=dup_canvas))}
        self.assertIn(cd.CHANGE_REMINDER_DUPLICATED, kinds)

        gone_canvas = json.loads(json.dumps(prev_canvas))
        gone_canvas["courses"]["math"]["announcements"] = []
        kinds = {e.classification for e in cd.detect_changes(_snap(canvas=prev_canvas), _snap(canvas=gone_canvas))}
        self.assertIn(cd.CHANGE_REMINDER_MISSING, kinds)

    def test_reminder_obsolete_when_scheduled_off_assessment(self) -> None:
        cells = _math_cell("Thursday", "2026-11-05")
        canvas = {"status": "OK", "courses": {"math": {
            "course_id": 26404, "front_page": None, "pages": [], "assignments": [],
            "announcements": [{"id": "r1", "title": "Math Assessment Reminder",
                               "delayed_post_at": "2026-11-04T20:00:00Z"}],
        }}}
        prev = _snap(cells=cells, canvas=canvas)
        # Assessment moves to Friday; reminder still scheduled for Wednesday.
        cells_new = _math_cell("Friday", "2026-11-06")
        curr = _snap(cells=cells_new, canvas=canvas)
        kinds = {e.classification for e in cd.detect_changes(prev, curr)}
        self.assertIn(cd.CHANGE_REMINDER_OBSOLETE, kinds)


if __name__ == "__main__":
    unittest.main()
