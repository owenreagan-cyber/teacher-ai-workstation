#!/usr/bin/env python3
"""Tests for Curriculum Production Engine validation and status reporting."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scripts.curriculum_production.artifact_plan import ArtifactPlan  # noqa: E402
from scripts.curriculum_production.content_map import ContentMap  # noqa: E402
from scripts.curriculum_production.lesson_model import LessonModel  # noqa: E402
from scripts.curriculum_production.models import CheckStatus  # noqa: E402
from scripts.curriculum_production.production_registry import ProductionRegistry  # noqa: E402
from scripts.curriculum_production.relationship_graph import RelationshipGraph, RelationshipType  # noqa: E402
from scripts.curriculum_production.validation import (  # noqa: E402
    validate_artifact_plan,
    validate_content_map,
    validate_lesson_package,
    validate_relationship_graph,
    validate_registry,
    validate_sequence_catalog,
)

FIXTURE = REPO_ROOT / "fixtures" / "curriculum-production" / "sample-lesson-package.json"


def _sample_package() -> tuple[LessonModel, ContentMap, ArtifactPlan, RelationshipGraph, ProductionRegistry]:
    raw = json.loads(FIXTURE.read_text(encoding="utf-8"))
    lesson = LessonModel.from_dict(raw["lesson"])
    content = ContentMap.from_dict(raw["content_map"])
    plan = ArtifactPlan.default_lesson_plan(lesson.lesson_id, lesson.subject)
    graph = RelationshipGraph.default_lesson_graph(lesson.lesson_id)
    registry = ProductionRegistry.from_plan(lesson, plan)
    return lesson, content, plan, graph, registry


class ValidationTests(unittest.TestCase):
    def test_sequence_catalog_pass(self) -> None:
        report = validate_sequence_catalog()
        self.assertEqual(report.final_status, CheckStatus.PASS)

    def test_content_map_warns_on_unclassified(self) -> None:
        _, content, _, _, _ = _sample_package()
        report = validate_content_map(content)
        self.assertEqual(report.final_status, CheckStatus.WARN)

    def test_relationship_graph_pass(self) -> None:
        graph = RelationshipGraph.default_lesson_graph("demo")
        report = validate_relationship_graph(graph)
        self.assertEqual(report.final_status, CheckStatus.PASS)

    def test_relationship_graph_fail_missing_edge(self) -> None:
        graph = RelationshipGraph(lesson_id="demo")
        report = validate_relationship_graph(graph)
        self.assertEqual(report.final_status, CheckStatus.FAIL)

    def test_artifact_plan_pass(self) -> None:
        _, _, plan, _, _ = _sample_package()
        report = validate_artifact_plan(plan)
        self.assertIn(report.final_status, {CheckStatus.PASS, CheckStatus.WARN})

    def test_registry_pass(self) -> None:
        _, _, plan, _, registry = _sample_package()
        report = validate_registry(registry, plan)
        self.assertEqual(report.final_status, CheckStatus.PASS)

    def test_lesson_package_warn_with_unclassified_content(self) -> None:
        lesson, content, plan, graph, registry = _sample_package()
        report = validate_lesson_package(
            lesson=lesson,
            content_map=content,
            plan=plan,
            graph=graph,
            registry=registry,
        )
        self.assertEqual(report.final_status, CheckStatus.WARN)

    def test_lesson_package_pass_when_content_classified(self) -> None:
        lesson, content, plan, graph, registry = _sample_package()
        for item in content.items:
            if item.priority is None:
                from scripts.curriculum_production.content_map import ContentPriority

                item.priority = ContentPriority.SUPPORTING
        report = validate_lesson_package(
            lesson=lesson,
            content_map=content,
            plan=plan,
            graph=graph,
            registry=registry,
        )
        self.assertEqual(report.final_status, CheckStatus.PASS)


if __name__ == "__main__":
    unittest.main(verbosity=2)
