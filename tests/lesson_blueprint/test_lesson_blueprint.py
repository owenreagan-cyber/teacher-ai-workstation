#!/usr/bin/env python3
"""Tests for Lesson Specification & Blueprint System."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scripts.curriculum_production.models import CheckStatus  # noqa: E402
from scripts.lesson_blueprint.blueprint_approval import BlueprintApprovalState, BlueprintApprovalWorkflow  # noqa: E402
from scripts.lesson_blueprint.fixture_builder import ensure_all_fixtures  # noqa: E402
from scripts.lesson_blueprint.fixture_loader import build_blueprint_from_fixture  # noqa: E402
from scripts.lesson_blueprint.review_packet import render_review_packet_markdown  # noqa: E402

FIXTURES = REPO_ROOT / "fixtures" / "lesson-blueprint"


class LessonBlueprintTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        ensure_all_fixtures(FIXTURES)

    def test_pass_well_formed_blueprint(self) -> None:
        blueprint = build_blueprint_from_fixture(FIXTURES / "passing" / "well-formed-blueprint.json")
        self.assertIn(blueprint.consistency_report.final_status, {CheckStatus.PASS, CheckStatus.WARN})
        self.assertIn(blueprint.blueprint_validation.final_status, {CheckStatus.PASS, CheckStatus.WARN})
        self.assertIn("presentation", blueprint.blueprints)
        self.assertIn("Lesson Blueprint Status", blueprint.reports["lesson_blueprint_status"])

    def test_review_packet_markdown(self) -> None:
        from scripts.curriculum_production.fixture_loader import build_from_fixture, load_package_fixture
        from scripts.lesson_blueprint.review_packet import build_review_packet

        package_path = REPO_ROOT / "fixtures/curriculum-production/passing/math-lesson-package.json"
        package_input = load_package_fixture(package_path)
        package = build_from_fixture(package_path)
        packet = build_review_packet(package, package_input.content_map)
        text = render_review_packet_markdown(packet)
        self.assertIn("# Lesson Review Packet", text)
        self.assertIn("## Objective", text)

    def test_warn_duplicate_terminology(self) -> None:
        blueprint = build_blueprint_from_fixture(FIXTURES / "warning" / "duplicate-terminology.json")
        self.assertEqual(blueprint.blueprint_validation.final_status, CheckStatus.WARN)

    def test_fail_broken_registry(self) -> None:
        blueprint = build_blueprint_from_fixture(FIXTURES / "failing" / "broken-registry.json")
        self.assertEqual(blueprint.consistency_report.final_status, CheckStatus.FAIL)

    def test_warn_vocabulary_mismatch(self) -> None:
        blueprint = build_blueprint_from_fixture(FIXTURES / "warning" / "vocabulary-mismatch.json")
        self.assertEqual(blueprint.consistency_report.final_status, CheckStatus.WARN)

    def test_warn_unused_critical(self) -> None:
        blueprint = build_blueprint_from_fixture(FIXTURES / "warning" / "unused-critical-content.json")
        self.assertEqual(blueprint.consistency_report.final_status, CheckStatus.WARN)

    def test_warn_budget_exceeded(self) -> None:
        blueprint = build_blueprint_from_fixture(FIXTURES / "warning" / "budget-exceeded.json")
        self.assertEqual(blueprint.blueprint_validation.final_status, CheckStatus.WARN)

    def test_fail_broken_dependency(self) -> None:
        blueprint = build_blueprint_from_fixture(FIXTURES / "failing" / "broken-dependency.json")
        self.assertEqual(blueprint.consistency_report.final_status, CheckStatus.FAIL)

    def test_fail_missing_blueprint(self) -> None:
        blueprint = build_blueprint_from_fixture(FIXTURES / "failing" / "missing-blueprint.json")
        self.assertEqual(blueprint.blueprint_validation.final_status, CheckStatus.FAIL)

    def test_fail_missing_sections(self) -> None:
        blueprint = build_blueprint_from_fixture(FIXTURES / "failing" / "missing-sections.json")
        self.assertEqual(blueprint.blueprint_validation.final_status, CheckStatus.FAIL)

    def test_locked_prevents_mutation(self) -> None:
        workflow = BlueprintApprovalWorkflow(state=BlueprintApprovalState.LOCKED)
        with self.assertRaises(ValueError):
            workflow.transition(BlueprintApprovalState.DRAFT, user="teacher")


if __name__ == "__main__":
    unittest.main(verbosity=2)
