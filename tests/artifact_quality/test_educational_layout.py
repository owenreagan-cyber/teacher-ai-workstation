#!/usr/bin/env python3
"""Phase 3 educational layout tests for Instructional Artifact Quality System."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifact_quality.educational_layout import (  # noqa: E402
    analyze_pdf_educational_layout,
    format_instructional_layout_section,
)
from scripts.artifact_quality.fixture_builder import ensure_all_fixtures  # noqa: E402
from scripts.artifact_quality.models import CheckStatus  # noqa: E402
from scripts.artifact_quality.profiles import load_profile  # noqa: E402
from scripts.artifact_quality.run_preflight import run_preflight  # noqa: E402
import fitz  # noqa: E402

FIXTURES = REPO_ROOT / "fixtures" / "artifact-quality"


class EducationalLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        ensure_all_fixtures(FIXTURES)

    def test_profile_educational_defaults(self) -> None:
        profile = load_profile("worksheet-letter")
        self.assertGreaterEqual(profile.educational_layout.min_body_font_pt, 12.0)
        self.assertGreater(profile.educational_layout.max_paragraph_chars, 100)

    def test_passing_worksheet_educational(self) -> None:
        report = run_preflight(
            profile_name="worksheet-letter",
            input_path=FIXTURES / "passing" / "worksheet-letter.pdf",
        )
        self.assertIsNotNone(report.educational_layout)
        cats = report.educational_layout["categories"]
        self.assertEqual(cats.get("Manual Review"), "REQUIRED")
        self.assertIn(report.final_status, {CheckStatus.PASS, CheckStatus.WARN})

    def test_passing_guided_notes_educational(self) -> None:
        report = run_preflight(
            profile_name="guided-notes-letter",
            input_path=FIXTURES / "passing" / "guided-notes-two-page.pdf",
        )
        self.assertIsNotNone(report.educational_layout)
        self.assertIn("Typography", report.educational_layout["categories"])

    def test_passing_slides_educational(self) -> None:
        report = run_preflight(
            profile_name="projector-slides",
            input_path=FIXTURES / "passing" / "projector.pptx",
        )
        self.assertIsNotNone(report.educational_layout)
        self.assertIn("Presentation Visibility", report.educational_layout["categories"])

    def test_warn_tiny_font(self) -> None:
        report = run_preflight(
            profile_name="worksheet-letter",
            input_path=FIXTURES / "warning" / "edu-tiny-font.pdf",
        )
        self.assertEqual(report.final_status, CheckStatus.WARN)
        msgs = " ".join(c.message for c in report.checks)
        self.assertIn("unusually small", msgs.lower())

    def test_warn_huge_paragraph(self) -> None:
        report = run_preflight(
            profile_name="worksheet-letter",
            input_path=FIXTURES / "warning" / "edu-huge-paragraph.pdf",
            subject="reading",
        )
        self.assertEqual(report.final_status, CheckStatus.WARN)
        edu = report.educational_layout["categories"]
        self.assertIn(edu.get("Text Density"), {"WARN", "FAIL"})

    def test_warn_dense_slide(self) -> None:
        report = run_preflight(
            profile_name="projector-slides",
            input_path=FIXTURES / "warning" / "edu-dense-slide.pptx",
        )
        self.assertEqual(report.final_status, CheckStatus.WARN)
        self.assertIn("bullet", " ".join(c.message.lower() for c in report.checks))

    def test_warn_crowded_shurley(self) -> None:
        report = run_preflight(
            profile_name="worksheet-letter",
            input_path=FIXTURES / "warning" / "edu-crowded-shurley.pdf",
            subject="shurley",
        )
        self.assertEqual(report.final_status, CheckStatus.WARN)

    def test_instructional_layout_section_format(self) -> None:
        profile = load_profile("worksheet-letter")
        doc = fitz.open(FIXTURES / "passing" / "worksheet-letter.pdf")
        layout = analyze_pdf_educational_layout(doc, profile, None, [])
        doc.close()
        text = format_instructional_layout_section(layout)
        self.assertIn("Instructional Layout", text)
        self.assertIn("Manual Review: REQUIRED", text)

    def test_educational_score_separate(self) -> None:
        report = run_preflight(
            profile_name="worksheet-letter",
            input_path=FIXTURES / "passing" / "worksheet-letter.pdf",
        )
        self.assertIn("educational_layout_score", report.quality_score)
        self.assertEqual(report.quality_score["instructional_approval"], "Manual Review Required")

    def test_json_educational_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            run_preflight(
                profile_name="worksheet-letter",
                input_path=FIXTURES / "passing" / "worksheet-letter.pdf",
                output_dir=out,
                json_output=True,
            )
            data = json.loads((out / "report.json").read_text())
            self.assertIn("educational_layout", data)
            self.assertIn("categories", data["educational_layout"])

    def test_fail_not_from_education_heuristics(self) -> None:
        report = run_preflight(
            profile_name="worksheet-letter",
            input_path=FIXTURES / "failing" / "a4-page.pdf",
        )
        self.assertEqual(report.final_status, CheckStatus.FAIL)
        edu_fails = [
            c for c in report.checks
            if c.status == CheckStatus.FAIL and "educational" in c.message.lower()
        ]
        self.assertEqual(edu_fails, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
