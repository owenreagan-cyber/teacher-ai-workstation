#!/usr/bin/env python3
"""Tests for Grade 4 profile catalog loading."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifact_quality.grade_4_profiles import (  # noqa: E402
    list_grade_4_profiles,
    load_grade_4_profile,
)
from scripts.artifact_quality.profiles import load_profile, list_profiles  # noqa: E402


class Grade4ProfileTests(unittest.TestCase):
    def test_catalog_lists_profiles(self) -> None:
        keys = list_grade_4_profiles()
        for key in ("grade_4_worksheet", "grade_4_guided_notes", "grade_4_quiz", "grade_4_teacher_key"):
            self.assertIn(key, keys)

    def test_worksheet_writing_space_range(self) -> None:
        p = load_grade_4_profile("grade_4_worksheet")
        self.assertEqual(p.visual_geometry.writing_space_range, (25.0, 60.0))
        self.assertEqual(p.educational_layout.min_body_font_pt, 14.0)

    def test_guided_notes_range(self) -> None:
        p = load_grade_4_profile("grade_4_guided_notes")
        self.assertEqual(p.visual_geometry.writing_space_range, (20.0, 45.0))

    def test_quiz_range(self) -> None:
        p = load_grade_4_profile("grade_4_quiz")
        self.assertEqual(p.visual_geometry.writing_space_range, (10.0, 30.0))

    def test_teacher_key_requirements(self) -> None:
        p = load_grade_4_profile("grade_4_teacher_key")
        self.assertTrue(p.requirements.teacher_key_must_match_page_count)
        self.assertEqual(p.visual_geometry.writing_space_range, (5.0, 20.0))

    def test_load_via_profile_name(self) -> None:
        p = load_profile("grade_4_worksheet")
        self.assertIn("Worksheet", p.name)

    def test_colon_syntax(self) -> None:
        p = load_profile("grade_4_profiles:grade_4_quiz")
        self.assertEqual(p.visual_geometry.writing_space_range, (10.0, 30.0))

    def test_list_profiles_includes_grade_4(self) -> None:
        names = list_profiles()
        self.assertIn("grade_4_worksheet", names)
        self.assertIn("worksheet-letter", names)


if __name__ == "__main__":
    unittest.main(verbosity=2)
