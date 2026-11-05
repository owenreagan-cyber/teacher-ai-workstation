"""Historical reminder noise and target-week assessment safety."""
import unittest

from scripts.weekly_planner_agent import change_detection as cd
from scripts.weekly_planner_agent import snapshot


def make_snapshot(announcements, assessments=None, week_id="Q2W5"):
    data = snapshot.blank_snapshot(2, 5, week_id)
    data["pacing"]["status"] = "OK"
    data["canvas"]["status"] = "OK"

    cells = {}
    for subject, assessment_date in (assessments or {}).items():
        cells[f"{subject}|Monday"] = {
            "assessment": {
                "name": "Test 1",
                "date": assessment_date,
                "day": "Monday",
            }
        }

    data["pacing"]["cells"] = cells
    data["canvas"]["courses"] = {
        subject: {
            "announcements": items,
            "pages": [],
            "assignments": [],
        }
        for subject, items in announcements.items()
    }
    return data


def announcement(title, scheduled):
    return {
        "title": title,
        "delayed_post_at": scheduled,
        "posted_at": scheduled,
    }


class ReminderScopeTests(unittest.TestCase):
    def test_historical_announcements_not_q2w5_alerts(self):
        dates = [
            "2026-08-10T19:00:00Z",
            "2026-08-19T19:00:00Z",
            "2026-08-26T19:00:00Z",
            "2026-10-27T19:00:00Z",
        ]
        sn = make_snapshot({
            "math": [
                announcement(f"Test Reminder {i}", value)
                for i, value in enumerate(dates)
            ]
        }, {"math": "2026-11-10"})

        self.assertEqual(cd._reminder_obsolete_events(sn), [])

    def test_homeroom_not_assessment_reminder(self):
        sn = make_snapshot({
            "homeroom": [
                announcement(
                    "General Reminder",
                    "2026-11-10T19:00:00Z",
                )
            ]
        }, {"math": "2026-11-10"})

        self.assertEqual(cd._reminder_obsolete_events(sn), [])

    def test_correct_sunday_reminder_for_monday_assessment(self):
        sn = make_snapshot({
            "math": [
                announcement(
                    "Math Assessment Reminder",
                    "2026-11-09T02:00:00Z",
                )
            ]
        }, {"math": "2026-11-09"})

        # November 9 at 02:00 UTC is Sunday November 8 EST.
        self.assertEqual(cd._reminder_obsolete_events(sn), [])

    def test_wrong_day_still_detected(self):
        sn = make_snapshot({
            "math": [
                announcement(
                    "Math Assessment Reminder",
                    "2026-11-10T20:00:00Z",
                )
            ]
        }, {"math": "2026-11-12"})

        found = cd._reminder_obsolete_events(sn)
        self.assertEqual(len(found), 1)
        self.assertEqual(
            found[0].classification,
            cd.CHANGE_REMINDER_OBSOLETE,
        )
        self.assertTrue(found[0].requires_teacher_approval)

    def test_does_not_match_other_subject_assessment(self):
        sn = make_snapshot({
            "language_arts": [
                announcement(
                    "Language Arts Test Reminder",
                    "2026-11-10T20:00:00Z",
                )
            ]
        }, {"math": "2026-11-11"})

        self.assertEqual(cd._reminder_obsolete_events(sn), [])

    def test_first_announcement_is_not_reminder(self):
        sn = make_snapshot({
            "math": [
                announcement(
                    "Written Assessment 1",
                    "2026-11-10T20:00:00Z",
                )
            ]
        }, {"math": "2026-11-12"})

        self.assertEqual(cd._reminder_obsolete_events(sn), [])

    def test_unknown_week_does_not_invent_alert(self):
        sn = make_snapshot({
            "math": [
                announcement(
                    "Math Reminder",
                    "2026-11-10T20:00:00Z",
                )
            ]
        }, {"math": "2026-11-12"}, week_id="UNKNOWN")

        self.assertEqual(cd._reminder_obsolete_events(sn), [])


if __name__ == "__main__":
    unittest.main()
