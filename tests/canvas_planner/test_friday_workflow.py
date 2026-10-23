"""Friday scheduler and single-publisher tests (fixtures/fakes only)."""
from __future__ import annotations

import io
import hashlib
import tempfile
import unittest
from datetime import date, datetime
from pathlib import Path
from types import SimpleNamespace
from unittest import mock
from zoneinfo import ZoneInfo

from scripts.canvas_llm_rollover import rollover
from scripts.canvas_llm_rollover import cli as rollover_cli
from scripts.canvas_llm_rollover import homeroom as homeroom_module
from scripts.canvas_llm_deploy.client import FakeDeployClient
from scripts.canvas_llm_deploy import cli as deploy_cli
from scripts.canvas_planner import friday
from scripts.teacher_workstation import deploy


class FridayWorkflowTest(unittest.TestCase):
    def _publish_fixture(self):
        body = "<div>Approved math page</div>"
        proposed_home = {"week_label": "Q2W3", "items": ["fixture newsletter"]}
        home_body = homeroom_module.render_proposed(proposed_home)
        plan = {
            "from_week": "Q2W2", "to_week": "Q2W3", "scheduled_at": "2026-10-23T20:00:00Z",
            "timezone": "America/New_York", "source_hash": "fixture", "ready_to_publish": True,
            "academic_courses": [{
                "subject": "math", "label": "Math", "course_id": 26404,
                "to_page_slug": "q2w3", "to_page_hash": hashlib.sha256(body.encode()).hexdigest(),
                "page_body": body, "approved": True,
            }],
            "homeroom": {
                "course_id": 26429, "to_page_slug": "q2w3", "proposed_content": proposed_home,
                "proposed_content_hash": homeroom_module._body_hash(home_body),
                "source_content_hash": "home-source", "approved": True,
            },
            "assignments": [{
                "course": "math", "course_id": 26404, "title": "Math practice",
                "assignment_group": "Homework", "points_possible": 100,
                "grading_type": "percent", "submission_types": ["on_paper"],
                "due_utc": "", "omit_from_final_grade": False,
            }],
            "weekly_announcements": [{
                "subject": "math", "course_id": 26404, "title": "Math weekly update",
                "message": "Approved weekly update", "week_code": "Q2W3",
                "agenda_hash": "agenda", "page_agenda_hash": "agenda",
                "hash_consistent": True, "delayed_post_at": "2026-10-23T20:00:00Z",
            }],
            "assessment_reminders": [{
                "subject": "math", "course_id": 26404, "title": "Math assessment reminder",
                "message": "Study the approved material",
            }],
        }
        fake = FakeDeployClient(courses={
            26404: {"id": 26404, "name": "Math"}, 26429: {"id": 26429, "name": "Homeroom"},
        })
        fake.assignment_groups[26404] = [{"id": "homework", "name": "Homework"}]
        fake.seed_page(26404, "q2w3", title="Q2W3 Math", body="old math")
        fake.seed_page(26429, "q2w3", title="Q2W3 Homeroom", body="old homeroom")
        return plan, fake, {}

    def _run_publish_now(self, *, now, plan, fake, ledger_store, courses=("all",), phrase="PUBLISH NOW Q2W3 ALL"):
        def load_ledger(_quarter, _week):
            return ledger_store.get("report")

        def write_ledger(_quarter, _week, report):
            ledger_store["report"] = dict(report)
            return report

        with mock.patch.object(rollover.rollover_manifest, "build_rollover_manifest", return_value=plan), \
             mock.patch.object(rollover.ledger, "load_rollover_ledger", side_effect=load_ledger), \
             mock.patch.object(rollover.ledger, "write_rollover_ledger", side_effect=write_ledger), \
             mock.patch.object(rollover, "_record_publish_event"), \
             mock.patch.object(rollover.deploy_ledger, "finalize_published_verified", return_value={}):
            return rollover.publish_now(
                2, 2, 2, 3, client=fake, courses=list(courses),
                owner_confirmation=phrase, now=now,
            )

    def test_publish_now_early_holds_front_pages_and_weekly_updates(self) -> None:
        now = datetime(2026, 10, 23, 15, 0, tzinfo=ZoneInfo("America/New_York"))
        plan, fake, ledger_store = self._publish_fixture()
        report = self._run_publish_now(now=now, plan=plan, fake=fake, ledger_store=ledger_store)
        self.assertEqual(report["publish_now_mode"], "EARLY")
        self.assertEqual(report["lifecycle"], "EARLY_CONTENT_PUBLISHED_VERIFIED")
        self.assertEqual(fake.pages[(26404, "q2w3")]["body"], "<div>Approved math page</div>")
        self.assertFalse(fake.pages[(26404, "q2w3")]["front_page"])
        self.assertFalse(fake.pages[(26429, "q2w3")]["front_page"])
        self.assertEqual(len(fake.assignments), 1)
        self.assertEqual([a["title"] for a in fake.announcements.values()], ["Math assessment reminder"])

    def test_publish_now_late_posts_everything_and_rerun_skips(self) -> None:
        now = datetime(2026, 10, 23, 17, 0, tzinfo=ZoneInfo("America/New_York"))
        plan, fake, ledger_store = self._publish_fixture()
        report = self._run_publish_now(now=now, plan=plan, fake=fake, ledger_store=ledger_store)
        self.assertEqual(report["publish_now_mode"], "LATE")
        self.assertEqual(report["lifecycle"], "PUBLISHED_VERIFIED")
        self.assertTrue(fake.pages[(26404, "q2w3")]["front_page"])
        self.assertTrue(fake.pages[(26429, "q2w3")]["front_page"])
        self.assertEqual(len(fake.assignments), 1)
        self.assertEqual(len(fake.announcements), 2)
        puts, posts = fake._write_counts["PUT"], fake._write_counts["POST"]
        with mock.patch.object(
            rollover.ledger, "load_rollover_ledger", return_value=ledger_store.get("report")
        ):
            scheduled_readiness = rollover.run_preflight(
                2, 2, 2, 3, client=fake, manifest_override=plan,
            )
        self.assertEqual(
            scheduled_readiness["manifest"]["weekly_announcements"][0]["classification"],
            "EXACT_MATCH",
        )
        with mock.patch.object(rollover, "run_preflight", return_value=scheduled_readiness), mock.patch.object(
            rollover.ledger, "load_rollover_ledger", return_value=ledger_store.get("report")
        ):
            again = rollover.publish_weekly_package(
                2, 2, 2, 3, client=fake, owner_confirmation="ROLLOVER Q2W3",
                today=date(2026, 10, 23),
            )
        self.assertTrue(again.get("already_complete"))
        self.assertEqual(fake._write_counts["PUT"], puts)
        self.assertEqual(fake._write_counts["POST"], posts)

    def test_publish_now_after_monday_start_warns_and_publishes(self) -> None:
        now = datetime(2026, 10, 26, 9, 0, tzinfo=ZoneInfo("America/New_York"))
        plan, fake, ledger_store = self._publish_fixture()
        report = self._run_publish_now(now=now, plan=plan, fake=fake, ledger_store=ledger_store)
        self.assertEqual(report["publish_now_mode"], "AFTER_MONDAY_START")
        self.assertIn("week has already started", report["warning"])
        self.assertTrue(fake.pages[(26404, "q2w3")]["front_page"])

    def test_publish_now_can_publish_one_course_with_course_bound_phrase(self) -> None:
        now = datetime(2026, 10, 23, 17, 0, tzinfo=ZoneInfo("America/New_York"))
        plan, fake, ledger_store = self._publish_fixture()
        report = self._run_publish_now(
            now=now, plan=plan, fake=fake, ledger_store=ledger_store,
            courses=("math",), phrase="PUBLISH NOW Q2W3 MATH",
        )
        self.assertEqual(report["publish_now_mode"], "LATE")
        self.assertEqual(report["published_courses"], ["math"])
        self.assertFalse(fake.pages[(26429, "q2w3")]["front_page"])
        self.assertEqual(len(fake.assignments), 1)

    def test_publish_now_rejects_wrong_typed_confirmation_before_get_or_write(self) -> None:
        now = datetime(2026, 10, 23, 17, 0, tzinfo=ZoneInfo("America/New_York"))
        plan, fake, _ledger_store = self._publish_fixture()
        with mock.patch.object(rollover.rollover_manifest, "build_rollover_manifest", return_value=plan):
            with self.assertRaisesRegex(rollover.RolloverBlocked, "PUBLISH NOW Q2W3 ALL"):
                rollover.publish_now(
                    2, 2, 2, 3, client=fake, courses=["all"],
                    owner_confirmation="PUBLISH NOW Q2W3 MATH", now=now,
                )
        self.assertEqual(fake._write_counts["GET"], 0)
        self.assertEqual(fake._write_counts["PUT"], 0)
        self.assertEqual(fake._write_counts["POST"], 0)

    def test_friday_evening_and_weekend_resolve_the_coming_monday(self) -> None:
        cases = (
            datetime(2026, 10, 23, 17, 0, tzinfo=ZoneInfo("America/New_York")),
            datetime(2026, 10, 24, 12, 0, tzinfo=ZoneInfo("America/New_York")),
            datetime(2026, 10, 25, 12, 0, tzinfo=ZoneInfo("America/New_York")),
        )
        for now in cases:
            with self.subTest(now=now):
                self.assertEqual(friday.week_resolution.next_week(today=now.date()), (2, 3))
                self.assertEqual(friday._weeks(now.date()), (2, 2, 2, 3))

    def test_live_readonly_plans_every_write_and_performs_none(self) -> None:
        academic_body = "<div>approved math</div>"
        plan = {
            "from_week": "Q2W2", "to_week": "Q2W3", "scheduled_at": "2026-10-23T20:00:00Z",
            "timezone": "America/New_York",
            "academic_courses": [{
                "subject": "math", "label": "Math", "course_id": 1, "to_page_slug": "q2w3",
                "to_page_hash": rollover.deploy_plan._sha(academic_body), "page_body": academic_body,
                "approved": True, "front_page_action": "SET_FRONT_PAGE",
            }],
            "homeroom": {
                "course_id": 2, "to_page_slug": "q2w3", "proposed_content_hash": "different",
                "proposed_content": {"week_label": "Q2W3"}, "approved": True,
                "source_content_hash": "source", "front_page_action": "SET_FRONT_PAGE",
            },
            "assignments": [{
                "course": "math", "course_id": 1, "title": "Practice", "assignment_group": "Homework",
                "due_utc": "", "points_possible": 100, "grading_type": "percent",
            }],
            "weekly_announcements": [{
                "subject": "math", "course_id": 1, "title": "Math update", "message": "body",
                "week_code": "Q2W3", "agenda_hash": "agenda", "delayed_post_at": "2026-10-23T20:00:00Z",
                "hash_consistent": True,
            }],
            "assessment_reminders": [{
                "subject": "math", "course_id": 1, "title": "Assessment", "message": "Study",
            }],
        }
        fake = FakeDeployClient(courses={1: {"id": 1}, 2: {"id": 2}})
        fake.assignment_groups[1] = [{"id": "g1", "name": "Homework"}]
        fake.seed_page(1, "q2w3", title="Q2W3", body=academic_body, front_page=True)
        fake.seed_page(2, "q2w3", title="Q2W3 Homeroom", body="old", front_page=False)
        fake.seed_assignment(1, "Practice", assignment_group="Homework")
        fake.announcements = {
            "w": {"id": "w", "course_id": 1, "title": "Math update", "message": "body",
                  "week_code": "Q2W3", "agenda_hash": "agenda", "delayed_post_at": "2026-10-23T20:00:00Z"},
            "r": {"id": "r", "course_id": 1, "title": "Assessment", "message": "Study"},
        }
        with mock.patch.object(rollover, "build_readiness", return_value={
            "manifest": plan, "ready": True, "blockers": [], "needs_owen": False,
        }), mock.patch.object(rollover.ledger, "load_rollover_ledger", return_value=None):
            result = rollover.run_preflight(2, 2, 2, 3, fake)
        self.assertEqual(result["canvas_writes"], 0)
        self.assertEqual(fake._write_counts["POST"], 0)
        self.assertEqual(fake._write_counts["PUT"], 0)
        self.assertEqual(plan["academic_courses"][0]["page_body_action"], "SKIP")
        self.assertEqual(plan["academic_courses"][0]["front_page_action"], "SKIP")
        self.assertEqual(plan["assignments"][0]["action"], "SKIP")
        self.assertEqual(plan["weekly_announcements"][0]["action"], "SKIP")
        self.assertEqual(plan["assessment_reminders"][0]["action"], "SKIP")
        self.assertEqual(plan["homeroom"]["page_body_action"], "UPDATE")
        self.assertEqual(plan["homeroom"]["front_page_action"], "SET_FRONT_PAGE")

    def test_live_readonly_cli_constructs_only_get_capable_preflight(self) -> None:
        manifest = {
            "from_week": "Q2W2", "to_week": "Q2W3", "scheduled_at": "x", "timezone": "America/New_York",
            "academic_courses": [], "homeroom": {"course_id": 2, "to_page_slug": "q2w3",
            "front_page_action": "SKIP", "page_body_action": "SKIP", "proposed_content_hash": "h"},
            "weekly_announcements": [], "assignments": [], "assessment_reminders": [],
        }
        fake = FakeDeployClient()
        output = io.StringIO()
        with mock.patch.object(rollover_cli, "_resolve", return_value=(2, 2, 2, 3)), \
             mock.patch("scripts.canvas_llm_deploy.client.LiveDeployClient", return_value=fake), \
             mock.patch.object(rollover, "run_preflight", return_value={
                 "manifest": manifest, "ready": True, "blockers": [], "warnings": [], "canvas_writes": 0,
             }), mock.patch("sys.stdout", output):
            code = rollover_cli.main(["--dry-run", "--live-readonly"])
        self.assertEqual(code, 0)
        self.assertIn('"MODE": "LIVE_READONLY"', output.getvalue())
        self.assertIn('"CANVAS_WRITES_PERFORMED": 0', output.getvalue())
    def test_setting_is_local_and_defaults_on(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertTrue(friday.load_settings(root)["automatic_rollover"])
            friday.set_automatic_rollover(False, root)
            self.assertFalse(friday.load_settings(root)["automatic_rollover"])

    def test_direct_deploy_is_not_a_publisher(self) -> None:
        with self.assertRaisesRegex(ValueError, "Friday rollover"):
            deploy.run_deploy(
                2, 3, preflight_id="x", expected_source_hash="x",
                expected_approval_snapshot_hash="x", owner_confirmation="DEPLOY Q2W3",
                production=True,
            )
        args = SimpleNamespace(quarter=2, week=3, dry_run=False, production=True)
        with mock.patch.object(deploy_cli, "LiveDeployClient",
                               side_effect=AssertionError("must not construct live transport")):
            self.assertEqual(deploy_cli.cmd_deploy(args), 2)

    def test_partial_publish_requires_exact_phrase_and_filters_same_manifest(self) -> None:
        source = {
            "from_week": "Q2W2", "to_week": "Q2W3", "scheduled_at": "x", "timezone": "America/New_York",
            "academic_courses": [
                {"subject": "math", "approved": True},
                {"subject": "science", "approved": False},
            ],
            "weekly_announcements": [{"subject": "math"}, {"subject": "science"}],
            "assignments": [{"course": "math"}, {"course": "science"}],
            "assessment_reminders": [{"subject": "math"}, {"subject": "science"}],
            "homeroom": {"approved": False},
        }
        with mock.patch.object(rollover.rollover_manifest, "build_rollover_manifest", return_value=source):
            with self.assertRaises(rollover.RolloverBlocked):
                rollover.publish_approved_courses_only(
                    2, 2, 2, 3, client=object(), owner_confirmation="yes",
                )
            with mock.patch.object(rollover, "execute", return_value={"lifecycle": "PARTIAL_PUBLISHED_VERIFIED"}) as execute:
                result = rollover.publish_approved_courses_only(
                    2, 2, 2, 3, client=object(),
                    owner_confirmation="PUBLISH APPROVED COURSES",
                )
        sent = execute.call_args.kwargs["manifest"]
        self.assertEqual([item["subject"] for item in sent["academic_courses"]], ["math"])
        self.assertEqual([item["course"] for item in sent["assignments"]], ["math"])
        self.assertIsNone(sent["homeroom"])
        self.assertEqual(result["published_courses"], ["math"])

    def test_four_pm_blocked_never_constructs_live_client(self) -> None:
        now = datetime(2026, 10, 23, 16, 0, tzinfo=ZoneInfo("America/New_York"))
        factory = mock.Mock(side_effect=AssertionError("live client should not be created"))
        with mock.patch.object(friday, "_weeks", return_value=(2, 2, 2, 3)), \
             mock.patch.object(friday, "load_settings", return_value={"automatic_rollover": True}), \
             mock.patch.object(rollover, "build_readiness", return_value={"ready": False, "blockers": ["Math not approved"]}):
            result = friday.scheduled_run(now=now, client_factory=factory)
        self.assertEqual(result["action"], "ROLLOVER_BLOCKED")
        self.assertEqual(result["canvas_writes"], 0)
        factory.assert_not_called()

    def test_launchagent_is_one_job_and_never_reuses_grade_check(self) -> None:
        path = Path("launchd/com.teacher-ai-workstation.canvas-friday.plist")
        text = path.read_text(encoding="utf-8")
        self.assertEqual(text.count("<key>StartCalendarInterval</key>"), 1)
        self.assertIn("<integer>13</integer>", text)
        self.assertIn("<integer>16</integer>", text)
        self.assertIn("--scheduled", text)
        self.assertNotIn("grade-check", text)


if __name__ == "__main__":
    unittest.main()
