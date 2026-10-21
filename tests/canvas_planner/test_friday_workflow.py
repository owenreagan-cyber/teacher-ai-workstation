"""Friday scheduler and single-publisher tests (fixtures/fakes only)."""
from __future__ import annotations

import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from unittest import mock
from zoneinfo import ZoneInfo

from scripts.canvas_llm_rollover import rollover
from scripts.canvas_llm_deploy import cli as deploy_cli
from scripts.canvas_planner import friday
from scripts.teacher_workstation import deploy


class FridayWorkflowTest(unittest.TestCase):
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
