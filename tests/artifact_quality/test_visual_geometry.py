#!/usr/bin/env python3
"""Phase 2 visual geometry tests for Instructional Artifact Quality System."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifact_quality.fixture_builder import ensure_all_fixtures  # noqa: E402
from scripts.artifact_quality.models import CheckStatus  # noqa: E402
from scripts.artifact_quality.profiles import load_profile  # noqa: E402
from scripts.artifact_quality.run_preflight import run_preflight  # noqa: E402
from scripts.artifact_quality.visual_geometry import (  # noqa: E402
    _estimate_background_luminance,
    analyze_page_visual,
    compute_drawing_coverage,
    compute_text_coverage,
    compute_visible_ink,
    generate_contact_sheet,
)
import fitz  # noqa: E402
from PIL import Image  # noqa: E402

FIXTURES = REPO_ROOT / "fixtures" / "artifact-quality"
RUNNER = REPO_ROOT / "scripts" / "artifact_quality" / "run_preflight.py"
LOCAL_ROOT = REPO_ROOT / ".local" / "artifact-quality"


class VisualGeometryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        ensure_all_fixtures(FIXTURES)

    def test_profile_visual_defaults(self) -> None:
        profile = load_profile("worksheet-letter")
        self.assertEqual(profile.visual_geometry.analysis_dpi, 96)
        self.assertEqual(profile.visual_geometry.writing_space_range, (25.0, 60.0))
        notes = load_profile("guided-notes-letter")
        self.assertEqual(notes.visual_geometry.writing_space_range, (20.0, 45.0))

    def test_background_luminance(self) -> None:
        img = Image.new("RGB", (100, 100), (255, 255, 255))
        self.assertGreater(_estimate_background_luminance(img), 250.0)
        img2 = Image.new("RGB", (100, 100), (30, 30, 30))
        self.assertLess(_estimate_background_luminance(img2), 50.0)

    def test_worksheet_not_zero_visual_use(self) -> None:
        profile = load_profile("worksheet-letter")
        doc = fitz.open(FIXTURES / "passing" / "worksheet-letter.pdf")
        page = doc[0]
        text_cov = compute_text_coverage(page, profile)
        draw_cov = compute_drawing_coverage(page, profile)
        metrics, _, _, _ = analyze_page_visual(page, 1, profile)
        doc.close()
        self.assertGreater(text_cov, 0.0)
        self.assertGreater(draw_cov, 0.0)
        self.assertGreater(metrics.visible_ink_percent, 3.0)
        combined = max(metrics.visible_ink_percent, draw_cov, metrics.writing_space_percent)
        self.assertGreater(combined, 10.0)

    def test_diagram_page_visible_ink(self) -> None:
        profile = load_profile("worksheet-letter")
        doc = fitz.open(FIXTURES / "passing" / "diagram-minimal-text.pdf")
        metrics, _, _, _ = analyze_page_visual(doc[0], 1, profile)
        doc.close()
        self.assertLess(metrics.text_coverage_percent, 15.0)
        self.assertGreater(metrics.drawing_coverage_percent, 0.0)
        self.assertGreater(metrics.visible_ink_percent, 0.5)

    def test_bottom_whitespace_fixture(self) -> None:
        report = run_preflight(
            profile_name="worksheet-letter",
            input_path=FIXTURES / "warning" / "bottom-gap.pdf",
        )
        self.assertEqual(report.final_status, CheckStatus.WARN)
        metrics = report.page_metrics[0]
        self.assertGreater(metrics["bottom_whitespace_inches"], 1.0)

    def test_dense_worksheet_warn(self) -> None:
        report = run_preflight(
            profile_name="worksheet-letter",
            input_path=FIXTURES / "warning" / "dense-worksheet.pdf",
        )
        self.assertEqual(report.final_status, CheckStatus.WARN)
        balance_msgs = [c.message for c in report.checks if "page balance" in c.message.lower()]
        self.assertTrue(balance_msgs)

    def test_fail_geometry_exit_code(self) -> None:
        report = run_preflight(
            profile_name="worksheet-letter",
            input_path=FIXTURES / "failing" / "unsafe-edge.pdf",
        )
        self.assertEqual(report.final_status, CheckStatus.FAIL)
        self.assertEqual(report.exit_code(), 1)

    def test_annotated_and_contact_sheet(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            report = run_preflight(
                profile_name="guided-notes-letter",
                input_path=FIXTURES / "passing" / "guided-notes-two-page.pdf",
                output_dir=out,
                render=True,
                annotate=True,
                contact_sheet=True,
                json_output=True,
            )
            self.assertTrue(any(out.joinpath("annotated").glob("*.png")))
            self.assertTrue((out / "preview-contact-sheet.png").is_file())
            data = json.loads((out / "report.json").read_text())
            self.assertIn("page_metrics", data)
            self.assertIn("annotated_render_paths", data)
            self.assertIn("contact_sheet_paths", data)

    def test_visual_compare(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            report = run_preflight(
                profile_name="teacher-key-letter",
                input_path=FIXTURES / "passing" / "guided-notes-two-page.pdf",
                student_path=FIXTURES / "passing" / "guided-notes-two-page.pdf",
                teacher_path=FIXTURES / "warning" / "layout-shift-key.pdf",
                output_dir=out,
                visual_compare=True,
            )
            compare_dir = out / "visual-compare"
            self.assertTrue(compare_dir.is_dir())
            self.assertTrue(any(compare_dir.glob("*-diff.png")))
            warn_msgs = [c for c in report.checks if c.status == CheckStatus.WARN]
            self.assertTrue(warn_msgs)

    def test_multipage_memory_safe(self) -> None:
        report = run_preflight(
            profile_name="worksheet-letter",
            input_path=FIXTURES / "passing" / "multipage-five.pdf",
        )
        self.assertEqual(len(report.page_metrics), 5)

    def test_output_stays_under_local(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            run_preflight(
                profile_name="worksheet-letter",
                input_path=FIXTURES / "passing" / "worksheet-letter.pdf",
                output_dir=out,
                render=True,
                json_output=True,
            )
            for path in out.rglob("*"):
                if path.is_file():
                    self.assertTrue(str(path).startswith(str(out)))

    def test_cli_new_flags(self) -> None:
        proc = subprocess.run([sys.executable, str(RUNNER), "--help"], capture_output=True, text=True, check=False)
        self.assertEqual(proc.returncode, 0)
        for flag in ("--annotate", "--contact-sheet", "--visual-compare", "--analysis-dpi"):
            self.assertIn(flag, proc.stdout)

    def test_json_page_metrics_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            run_preflight(
                profile_name="worksheet-letter",
                input_path=FIXTURES / "passing" / "worksheet-letter.pdf",
                output_dir=out,
                json_output=True,
            )
            data = json.loads((out / "report.json").read_text())
            pm = data["page_metrics"][0]
            for key in (
                "text_coverage_percent",
                "drawing_coverage_percent",
                "visible_ink_percent",
                "writing_space_percent",
                "bottom_whitespace_inches",
                "safe_margin_state",
                "page_balance",
            ):
                self.assertIn(key, pm)

    def test_quality_score_present(self) -> None:
        report = run_preflight(
            profile_name="worksheet-letter",
            input_path=FIXTURES / "passing" / "worksheet-letter.pdf",
        )
        self.assertIsNotNone(report.quality_score)
        self.assertEqual(report.quality_score["instructional_status"], "Manual Review Required")

    def test_visible_ink_on_synthetic(self) -> None:
        img = Image.new("RGB", (200, 200), (255, 255, 255))
        for x in range(40, 160):
            img.putpixel((x, 100), (0, 0, 0))
        profile = load_profile("worksheet-letter")
        pct, mask = compute_visible_ink(img, profile.visual_geometry)
        self.assertGreater(pct, 0.2)
        self.assertGreater(sum(sum(row) for row in mask), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
