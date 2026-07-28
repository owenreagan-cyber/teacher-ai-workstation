#!/usr/bin/env python3
"""Tests for Curriculum Production Engine lesson model."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scripts.curriculum_production.artifact_plan import ArtifactPlan  # noqa: E402
from scripts.curriculum_production.content_map import ContentMap, ContentPriority  # noqa: E402
from scripts.curriculum_production.lesson_model import LessonModel, ProductionStatus  # noqa: E402
from scripts.curriculum_production.lesson_sequence import get_sequence, load_sequence_catalog  # noqa: E402
from scripts.curriculum_production.models import CheckStatus  # noqa: E402
from scripts.curriculum_production.production_registry import ProductionRegistry  # noqa: E402
from scripts.curriculum_production.relationship_graph import RelationshipGraph, RelationshipType  # noqa: E402
from scripts.curriculum_production.validation import validate_lesson_model  # noqa: E402

FIXTURE = REPO_ROOT / "fixtures" / "curriculum-production" / "sample-lesson-package.json"


class LessonModelTests(unittest.TestCase):
    def test_sample_fixture_round_trip(self) -> None:
        raw = json.loads(FIXTURE.read_text(encoding="utf-8"))
        lesson = LessonModel.from_dict(raw["lesson"])
        self.assertEqual(lesson.lesson_id, "sample-g4-math-u1-l03")
        self.assertEqual(lesson.production_status, ProductionStatus.PLANNED)
        restored = LessonModel.from_dict(lesson.to_dict())
        self.assertEqual(restored.title, lesson.title)

    def test_required_fields_validation_pass(self) -> None:
        raw = json.loads(FIXTURE.read_text(encoding="utf-8"))
        lesson = LessonModel.from_dict(raw["lesson"])
        report = validate_lesson_model(lesson)
        self.assertEqual(report.final_status, CheckStatus.PASS)

    def test_instructional_sequence_catalog(self) -> None:
        catalog = load_sequence_catalog()
        self.assertIn("math", catalog)
        math = get_sequence("math")
        self.assertGreaterEqual(len(math.steps), 4)
        self.assertIn("Concrete", math.steps[0])

    def test_content_map_manual_priority(self) -> None:
        raw = json.loads(FIXTURE.read_text(encoding="utf-8"))
        content = ContentMap.from_dict(raw["content_map"])
        self.assertEqual(len(content.unclassified()), 1)
        content.items[1].priority = ContentPriority.SUPPORTING
        self.assertEqual(len(content.unclassified()), 0)

    def test_artifact_plan_scaffold(self) -> None:
        plan = ArtifactPlan.default_lesson_plan("demo-lesson", "math")
        self.assertEqual(len(plan.artifacts), 8)
        worksheet = plan.by_type("worksheet")[0]
        self.assertIn("guided_notes", worksheet.dependencies)
        self.assertEqual(worksheet.quality_gate, "worksheet-letter")

    def test_relationship_graph_required_edges(self) -> None:
        graph = RelationshipGraph.default_lesson_graph("demo-lesson")
        self.assertTrue(graph.has_edge("presentation", "guided_notes", RelationshipType.MATCHES))

    def test_production_registry_tracks_plan(self) -> None:
        raw = json.loads(FIXTURE.read_text(encoding="utf-8"))
        lesson = LessonModel.from_dict(raw["lesson"])
        plan = ArtifactPlan.default_lesson_plan(lesson.lesson_id, lesson.subject)
        registry = ProductionRegistry.from_plan(lesson, plan)
        record = registry.get(lesson.lesson_id)
        self.assertIsNotNone(record)
        assert record is not None
        self.assertEqual(len(record.artifacts), len(plan.artifacts))


if __name__ == "__main__":
    unittest.main(verbosity=2)
