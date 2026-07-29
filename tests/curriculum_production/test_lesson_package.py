#!/usr/bin/env python3
"""Phase 5 manual curriculum intake and lesson package workflow tests."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scripts.curriculum_production.approval_workflow import ApprovalWorkflow, WorkflowState  # noqa: E402
from scripts.curriculum_production.content_map import ContentPriority  # noqa: E402
from scripts.curriculum_production.curriculum_intake import CurriculumIntake  # noqa: E402
from scripts.curriculum_production.fixture_builder import ensure_all_fixtures  # noqa: E402
from scripts.curriculum_production.fixture_loader import build_from_fixture, load_package_fixture  # noqa: E402
from scripts.curriculum_production.models import CheckStatus  # noqa: E402
from scripts.curriculum_production.workflow import build_lesson_package  # noqa: E402

FIXTURES = REPO_ROOT / "fixtures" / "curriculum-production"


class LessonPackageWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        ensure_all_fixtures(FIXTURES)

    def test_pass_math_package(self) -> None:
        package = build_from_fixture(FIXTURES / "passing" / "math-lesson-package.json")
        self.assertIn(package.validation_summary.final_status, {CheckStatus.PASS, CheckStatus.WARN})
        self.assertIn("Lesson Package Status", package.status_report)
        self.assertGreater(len(package.artifact_plan.artifacts), 0)

    def test_pass_shurley_and_history(self) -> None:
        for name in ("shurley-lesson-package.json", "history-lesson-package.json"):
            package = build_from_fixture(FIXTURES / "passing" / name)
            self.assertNotEqual(package.validation_summary.final_status, CheckStatus.FAIL)

    def test_warn_missing_objective(self) -> None:
        package = build_from_fixture(FIXTURES / "warning" / "missing-objective.json")
        self.assertEqual(package.validation_summary.final_status, CheckStatus.FAIL)

    def test_warn_critical_unlinked(self) -> None:
        package = build_from_fixture(FIXTURES / "warning" / "critical-unlinked.json")
        self.assertEqual(package.validation_summary.final_status, CheckStatus.FAIL)

    def test_warn_assessment_missing(self) -> None:
        package = build_from_fixture(FIXTURES / "warning" / "assessment-missing.json")
        self.assertEqual(package.validation_summary.final_status, CheckStatus.WARN)

    def test_warn_too_many_supporting(self) -> None:
        package = build_from_fixture(FIXTURES / "warning" / "too-many-supporting.json")
        self.assertEqual(package.validation_summary.final_status, CheckStatus.WARN)

    def test_fail_invalid_intake(self) -> None:
        package = build_from_fixture(FIXTURES / "failing" / "invalid-intake.json")
        self.assertEqual(package.validation_summary.final_status, CheckStatus.FAIL)

    def test_fail_broken_graph(self) -> None:
        package = build_from_fixture(FIXTURES / "failing" / "broken-graph.json")
        self.assertEqual(package.validation_summary.final_status, CheckStatus.FAIL)

    def test_manual_priority_assignment(self) -> None:
        package_input = load_package_fixture(FIXTURES / "passing" / "math-lesson-package.json")
        item = package_input.content_map.items[0]
        item.priority = ContentPriority.HIGH_PRIORITY
        item.supports_objective = True
        package = build_lesson_package(package_input)
        self.assertNotEqual(package.validation_summary.final_status, CheckStatus.FAIL)

    def test_approval_transition_blocks_approved_to_draft(self) -> None:
        workflow = ApprovalWorkflow(state=WorkflowState.APPROVED)
        with self.assertRaises(ValueError):
            workflow.transition(WorkflowState.DRAFT, user="teacher")

    def test_approval_override_to_draft(self) -> None:
        workflow = ApprovalWorkflow(state=WorkflowState.APPROVED)
        record = workflow.transition(WorkflowState.DRAFT, user="teacher", override=True, note="Reopen")
        self.assertEqual(record.to_state, WorkflowState.DRAFT)

    def test_registry_completion_percent(self) -> None:
        package = build_from_fixture(FIXTURES / "passing" / "math-lesson-package.json")
        record = package.registry.get(package.lesson_id)
        self.assertIsNotNone(record)
        assert record is not None
        self.assertGreater(record.completion_percent, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
