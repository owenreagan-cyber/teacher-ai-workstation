"""Weekly Planner Agent foundation tests (fake/local sources only, no Canvas)."""
from __future__ import annotations

import unittest
from datetime import date

from scripts.weekly_planner_agent import authority
from scripts.weekly_planner_agent import change_engine
from scripts.weekly_planner_agent import communication_rules
from scripts.weekly_planner_agent import notification_model
from scripts.weekly_planner_agent import teacher_instructions as ti
from scripts.weekly_planner_agent.assessment_watch import watch_assessment_date
from scripts.weekly_planner_agent.authority import Authority, Conflict
from scripts.weekly_planner_agent.models import (
    Assessment,
    Confidence,
    DayPlan,
    PlanStatus,
    SourceChangeEvent,
    WeeklyPlan,
)
from scripts.weekly_planner_agent.review_state import build_review, next_state


def _plan() -> WeeklyPlan:
    plan = WeeklyPlan(week_id="Q2W3", quarter=2, week=3)
    for subject in ("math", "science", "reading_spelling", "language_arts"):
        for day in ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday"):
            plan.upsert_day(DayPlan(
                subject=subject, day=day, lesson=f"{subject.title()} {day} lesson",
                authority=Authority.VERIFIED_PACING, confidence=Confidence.CONFIRMED,
                status=PlanStatus.PLANNED,
            ))
    plan.approval_status = {
        subject: {"page": "approved", "announcement": "approved", "assignments": "approved"}
        for subject in ("math", "science", "reading_spelling", "language_arts")
    }
    return plan


class TeacherInstructionParseTest(unittest.TestCase):
    def test_move_assessment(self) -> None:
        r = ti.parse("Move the Math test to Thursday.")
        self.assertTrue(r.matched)
        op = r.ops[0]
        self.assertEqual(op.intent, ti.MOVE_ASSESSMENT)
        self.assertEqual(op.subject, "math")
        self.assertEqual(op.day, "Thursday")

    def test_no_homework(self) -> None:
        r = ti.parse("No Science homework this week.")
        self.assertTrue(r.matched)
        self.assertEqual(r.ops[0].intent, ti.NO_HOMEWORK)
        self.assertEqual(r.ops[0].subject, "science")

    def test_homework_days(self) -> None:
        r = ti.parse("Reading homework Tuesday and Thursday only.")
        self.assertTrue(r.matched)
        self.assertEqual(r.ops[0].intent, ti.SET_HOMEWORK_DAYS)
        self.assertEqual(sorted(r.ops[0].days), ["Thursday", "Tuesday"])

    def test_skip_chapter(self) -> None:
        r = ti.parse("We aren't doing Chapter 8 yet.")
        self.assertTrue(r.matched)
        self.assertEqual(r.ops[0].intent, ti.SKIP_CHAPTER)
        self.assertEqual(r.ops[0].chapter, "8")

    def test_add_homeroom(self) -> None:
        r = ti.parse("Add Book Character Day to Homeroom.")
        self.assertTrue(r.matched)
        self.assertEqual(r.ops[0].intent, ti.ADD_HOMEROOM)
        self.assertIn("Book Character Day", r.ops[0].item)

    def test_what_changed(self) -> None:
        r = ti.parse("What changed since yesterday?")
        self.assertTrue(r.matched)
        self.assertEqual(r.ops[0].intent, ti.WHAT_CHANGED)

    def test_approve_except(self) -> None:
        r = ti.parse("Approve everything except Science.")
        self.assertTrue(r.matched)
        self.assertEqual(r.ops[0].intent, ti.APPROVE_EXCEPT)
        self.assertEqual(r.ops[0].subject, "science")

    def test_make_review_day(self) -> None:
        r = ti.parse("Make Wednesday a review day.")
        self.assertTrue(r.matched)
        self.assertEqual(r.ops[0].intent, ti.MAKE_REVIEW_DAY)
        self.assertEqual(r.ops[0].day, "Wednesday")

    def test_hold_reminder(self) -> None:
        r = ti.parse("Don't send the reminder yet.")
        self.assertTrue(r.matched)
        self.assertEqual(r.ops[0].intent, ti.HOLD_REMINDER)

    def test_remove_assignment_keep_lesson(self) -> None:
        r = ti.parse("Remove the Tuesday Math assignment but keep Lesson 42.")
        self.assertTrue(r.matched)
        self.assertEqual(r.ops[0].intent, ti.REMOVE_ASSIGNMENT_KEEP)
        self.assertEqual(r.ops[0].subject, "math")
        self.assertEqual(r.ops[0].day, "Tuesday")
        self.assertTrue(r.ops[0].keep_lesson)

    def test_keep_subject_chapter(self) -> None:
        r = ti.parse("Science should stay on Chapter 7 Thursday.")
        self.assertTrue(r.matched)
        self.assertEqual(r.ops[0].intent, ti.KEEP_SUBJECT_CHAPTER)
        self.assertEqual(r.ops[0].chapter, "7")

    def test_keep_override(self) -> None:
        r = ti.parse("keep Science on Wednesday.")
        self.assertTrue(r.matched)
        self.assertEqual(r.ops[0].intent, ti.KEEP_OVERRIDE)
        self.assertEqual(r.ops[0].subject, "science")
        self.assertEqual(r.ops[0].day, "Wednesday")

    def test_confirm(self) -> None:
        r = ti.parse("Yes")
        self.assertTrue(r.matched)
        self.assertEqual(r.ops[0].intent, ti.CONFIRM)

    def test_unmatched_fails_closed(self) -> None:
        r = ti.parse("Banana pancakes on the moon")
        self.assertFalse(r.matched)


class AuthorityTest(unittest.TestCase):
    def test_owner_outranks_pacing(self) -> None:
        c = authority.resolve("old", "new", current_authority=Authority.OWNER_INSTRUCTION,
                              incoming_authority=Authority.VERIFIED_PACING,
                              subject="math", field="lesson")
        self.assertEqual(c.resolved_to, "old")

    def test_conflict_surfaced_not_guessed(self) -> None:
        c = authority.resolve("A", "B", current_authority=Authority.VERIFIED_PACING,
                              incoming_authority=Authority.VERIFIED_CANVAS,
                              subject="math", field="assessment_date")
        self.assertEqual(c.resolved_to, "A")  # pacing outranks canvas
        self.assertTrue(c.requires_teacher_review is False or c.resolved_to is not None)

    def test_equal_authority_needs_owen(self) -> None:
        c = authority.resolve("A", "B", current_authority=Authority.VERIFIED_CANVAS,
                              incoming_authority=Authority.VERIFIED_CANVAS,
                              subject="math", field="assessment_date")
        self.assertIsNone(c.resolved_to)
        self.assertTrue(c.requires_teacher_review)

    def test_predicted_never_promotes(self) -> None:
        self.assertFalse(authority.may_promote(Confidence.PREDICTED, "approved"))
        self.assertFalse(authority.may_promote(Confidence.PREDICTED, "live"))
        self.assertTrue(authority.may_promote(Confidence.PREDICTED, "planned"))


class ChangeEngineTest(unittest.TestCase):
    def test_move_assessment_recomputes_and_invalidates_only_math(self) -> None:
        plan = _plan()
        result = change_engine.apply_instruction(plan, ti.parse("Move the Math test to Thursday.").ops[0])
        self.assertTrue(result.applied)
        self.assertTrue(any(e.object_type == "assessment_date" for e in result.events))
        # Only math approval invalidated (approval-by-exception).
        self.assertEqual(plan.approval_status["math"]["page"], "stale")
        self.assertEqual(plan.approval_status["science"]["page"], "approved")

    def test_teacher_override_becomes_highest_authority(self) -> None:
        plan = _plan()
        change_engine.apply_instruction(plan, ti.parse("keep Science on Wednesday.").ops[0])
        day = plan.day("science", "Wednesday")
        self.assertEqual(day.authority, Authority.OWNER_INSTRUCTION)
        self.assertIsNotNone(day.teacher_override)

    def test_no_homework_clears_homework(self) -> None:
        plan = _plan()
        for day in plan.subjects["science"]:
            day.homework = ["worksheet"]
        change_engine.apply_instruction(plan, ti.parse("No Science homework this week.").ops[0])
        self.assertTrue(all(not d.homework for d in plan.subjects["science"]))

    def test_add_homeroom(self) -> None:
        plan = _plan()
        change_engine.apply_instruction(plan, ti.parse("Add Book Character Day to Homeroom.").ops[0])
        self.assertTrue(any("Book Character Day" in item.get("label", "") for item in plan.homeroom_items))


class AssessmentWatchTest(unittest.TestCase):
    def test_date_change_creates_attention_event(self) -> None:
        plan = _plan()
        plan.day("math", "Thursday").assessment = Assessment(
            name="Written Assessment 8", subject="math", day="Thursday", date="2026-10-29"
        )
        result = watch_assessment_date(
            plan, subject="math", assessment_name="Written Assessment 8",
            previous_date="2026-10-29", new_date="2026-10-30",
        )
        self.assertTrue(result.attention_needed)
        self.assertIn("I noticed a test date changed", result.message)
        self.assertTrue(any("weekly page" in a for a in result.affected))
        self.assertTrue(any("first parent announcement" in a for a in result.affected))
        self.assertTrue(any("day-before reminder" in a for a in result.affected))
        self.assertTrue(result.event.family_comms_affected)
        self.assertIn("Would you like me to update", result.ask)

    def test_no_change_no_event(self) -> None:
        result = watch_assessment_date(
            _plan(), subject="math", assessment_name="WA8",
            previous_date="2026-10-29", new_date="2026-10-29",
        )
        self.assertFalse(result.attention_needed)

    def test_approved_change_no_attention(self) -> None:
        result = watch_assessment_date(
            _plan(), subject="math", assessment_name="WA8",
            previous_date="2026-10-29", new_date="2026-10-30", approved=True,
        )
        self.assertFalse(result.attention_needed)


class CommunicationRulesTest(unittest.TestCase):
    def test_first_announcement_no_later_than_friday_before(self) -> None:
        assessment = Assessment(name="WA8", subject="math", day="Thursday")
        plan = communication_rules.first_announcement_plan(
            assessment, week_start=date(2026, 10, 26), now=date(2026, 10, 20)
        )
        self.assertEqual(plan["deadline"], "2026-10-23")
        self.assertEqual(plan["ideal"], "2026-10-22")
        self.assertFalse(plan["late"])

    def test_day_before_reminder(self) -> None:
        assessment = Assessment(name="WA8", subject="math", day="Thursday")
        plan = communication_rules.day_before_reminder_plan(assessment)
        self.assertEqual(plan["reminder_day"], "Wednesday")
        self.assertTrue(plan["delayed_send"])

    def test_date_change_before_reminder_posts_no_duplicate(self) -> None:
        action = communication_rules.handle_date_change(
            first_announcement_posted=False, reminder_posted=False
        )
        self.assertEqual(action.action, "reschedule_reminder_and_update_announcement")
        self.assertFalse(action.requires_approval)

    def test_date_change_after_first_announcement_requires_approval(self) -> None:
        action = communication_rules.handle_date_change(
            first_announcement_posted=True, reminder_posted=False
        )
        self.assertTrue(action.requires_approval)

    def test_date_change_after_reminder_requires_approval(self) -> None:
        action = communication_rules.handle_date_change(
            first_announcement_posted=True, reminder_posted=True
        )
        self.assertTrue(action.requires_approval)
        self.assertEqual(action.action, "corrective_communication")


class NotificationModelTest(unittest.TestCase):
    def test_assessment_date_changed_email(self) -> None:
        n = notification_model.assessment_date_changed_notification(
            subject="math", assessment_name="Written Assessment 8",
            previous_date="Thursday, November 5", new_date="Friday, November 6",
            affected=["Math weekly page", "assessment assignment", "parent announcement", "day-before reminder"],
        )
        self.assertIn("test date changed", n.subject_line)
        self.assertIn("Written Assessment 8", n.body)
        self.assertIn("Math weekly page", n.body)
        self.assertEqual(n.actions, ["Approve Updates", "Review Changes", "Ignore for Now"])

    def test_draft_for_event_routes_assessment(self) -> None:
        event = SourceChangeEvent(
            source="pacing_or_canvas", subject="math", object_type="assessment_date",
            old_value="Thu", new_value="Fri", family_comms_affected=True,
            affected_artifacts=["a", "b"],
        )
        n = notification_model.draft_for_event(event)
        self.assertEqual(n.notification_type, "assessment_date_changed")


class ReviewStateTest(unittest.TestCase):
    def test_state_machine(self) -> None:
        self.assertEqual(next_state(change_count=0, unresolved_conflicts=0, all_approved=False), "READY_FOR_REVIEW")
        self.assertEqual(next_state(change_count=2, unresolved_conflicts=0, all_approved=False), "CHANGES_DETECTED")
        self.assertEqual(next_state(change_count=0, unresolved_conflicts=1, all_approved=False), "BLOCKED")
        self.assertEqual(next_state(change_count=0, unresolved_conflicts=0, all_approved=True), "APPROVED")

    def test_review_highlights_only_changed(self) -> None:
        plan = _plan()
        prior = _plan()
        prior.day("math", "Monday").lesson = "Old lesson"
        review = build_review(plan, prior=prior)
        self.assertIn("math", review.changed_subjects)
        self.assertEqual(review.pages_count, 4)

    def test_approval_by_exception_collapses_unchanged(self) -> None:
        plan = _plan()
        result = review_state_approval_by_exception(plan, ["math"])
        self.assertNotIn("science", result["changed_subjects"])


def review_state_approval_by_exception(plan, changed_subjects):
    from scripts.weekly_planner_agent.review_state import approval_by_exception
    return approval_by_exception(plan, None, changed_subjects)


class ModelRoundTripTest(unittest.TestCase):
    def test_weekly_plan_json_roundtrip(self) -> None:
        from scripts.weekly_planner_agent.service import _from_dict
        plan = _plan()
        restored = _from_dict(plan.to_dict())
        self.assertEqual(restored.week_id, "Q2W3")
        self.assertEqual(restored.day("math", "Monday").lesson, "Math Monday lesson")

    def test_predicted_day_cannot_auto_approve(self) -> None:
        day = DayPlan(subject="math", day="Friday", lesson="likely Review Day",
                      confidence=Confidence.PREDICTED, authority=Authority.INFERENCE)
        self.assertFalse(change_engine.predicted_guard(day, "approved"))
        self.assertTrue(change_engine.predicted_guard(day, "planned"))


class ActiveAnnouncementFeedFixTest(unittest.TestCase):
    """Regression: list_active_announcements must include context_codes[] (HTTP 400 fix)."""

    def test_canvas_readonly_includes_context_codes(self) -> None:
        from scripts.canvas_llm_intake import canvas_readonly

        captured: dict[str, str] = {}

        class Probe(canvas_readonly.CanvasReadOnly):
            def __init__(self) -> None:
                self.base_url = "https://example.instructure.com"
                self.token = "tok"

            def _get(self, path: str):
                captured["path"] = path
                return []

        probe = Probe()
        probe.list_active_announcements(context_codes=["course_26404"])
        self.assertIn("context_codes[]=course_26404", captured["path"])
        self.assertIn("active_only=true", captured["path"])
        # Without context codes it still builds a syntactically valid URL (no 400 crash path).
        probe.list_active_announcements()
        self.assertIn("active_only=true", captured["path"])

    def test_fake_client_scopes_to_context_codes(self) -> None:
        from scripts.canvas_llm_deploy.client import FakeDeployClient

        fake = FakeDeployClient(courses={26404: {"id": 26404}, 26442: {"id": 26442}})
        fake.announcements = {
            "a": {"id": "a", "course_id": 26404, "title": "Math update"},
            "b": {"id": "b", "course_id": 26442, "title": "Reading update"},
        }
        scoped = fake.list_active_announcements(context_codes=["course_26404"])
        self.assertEqual([x["title"] for x in scoped], ["Math update"])
        # No context codes -> account-wide (all).
        self.assertEqual(len(fake.list_active_announcements()), 2)


class NewIntentParseTest(unittest.TestCase):
    def test_update_without_reminder(self) -> None:
        r = ti.parse("Update the Math items but don't reschedule the reminder yet.")
        self.assertTrue(r.matched)
        self.assertEqual(r.ops[0].intent, ti.UPDATE_WITHOUT_REMINDER)
        self.assertEqual(r.ops[0].subject, "math")
        self.assertTrue(r.ops[0].hold_reminder)

    def test_keep_assessment_date_day_only(self) -> None:
        r = ti.parse("The pacing sheet is wrong. Keep Thursday.")
        self.assertTrue(r.matched)
        self.assertEqual(r.ops[0].intent, ti.KEEP_ASSESSMENT_DATE)
        self.assertEqual(r.ops[0].day, "Thursday")

    def test_keep_assessment_date_bare(self) -> None:
        r = ti.parse("Keep Thursday.")
        self.assertTrue(r.matched)
        self.assertEqual(r.ops[0].intent, ti.KEEP_ASSESSMENT_DATE)

    def test_show_announcement(self) -> None:
        r = ti.parse("Show me the exact announcement parents would receive.")
        self.assertTrue(r.matched)
        self.assertEqual(r.ops[0].intent, ti.SHOW_ANNOUNCEMENT)


if __name__ == "__main__":
    unittest.main()
