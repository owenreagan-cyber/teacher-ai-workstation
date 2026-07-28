#!/usr/bin/env python3
"""Focused preflight tests for Instructional Artifact Quality System."""
from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifact_quality.fixture_builder import ensure_all_fixtures  # noqa: E402
from scripts.artifact_quality.models import CheckStatus  # noqa: E402
from scripts.artifact_quality.profiles import load_profile, list_profiles  # noqa: E402
from scripts.artifact_quality.run_preflight import run_preflight  # noqa: E402


FIXTURES = REPO_ROOT / "fixtures" / "artifact-quality"
RUNNER = REPO_ROOT / "scripts" / "artifact_quality" / "run_preflight.py"


class ArtifactQualityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        ensure_all_fixtures(FIXTURES)

    def test_profiles_load(self) -> None:
        names = list_profiles()
        self.assertIn("worksheet-letter", names)
        profile = load_profile("worksheet-letter")
        self.assertEqual(profile.paper.width_points, 612)

    def test_passing_worksheet(self) -> None:
        report = run_preflight(
            profile_name="worksheet-letter",
            input_path=FIXTURES / "passing" / "worksheet-letter.pdf",
        )
        self.assertEqual(report.final_status, CheckStatus.PASS)

    def test_passing_worksheet_with_subject_warns(self) -> None:
        report = run_preflight(
            profile_name="worksheet-letter",
            input_path=FIXTURES / "passing" / "worksheet-letter.pdf",
            subject="math",
        )
        self.assertEqual(report.final_status, CheckStatus.WARN)

    def test_warning_low_utilization(self) -> None:
        report = run_preflight(
            profile_name="worksheet-letter",
            input_path=FIXTURES / "warning" / "low-utilization.pdf",
        )
        self.assertEqual(report.final_status, CheckStatus.WARN)
        self.assertEqual(report.exit_code(strict=False), 0)
        self.assertEqual(report.exit_code(strict=True), 2)

    def test_fail_a4(self) -> None:
        report = run_preflight(
            profile_name="worksheet-letter",
            input_path=FIXTURES / "failing" / "a4-page.pdf",
        )
        self.assertEqual(report.final_status, CheckStatus.FAIL)
        self.assertEqual(report.exit_code(), 1)

    def test_fail_placeholder(self) -> None:
        report = run_preflight(
            profile_name="worksheet-letter",
            input_path=FIXTURES / "failing" / "placeholder.pdf",
        )
        self.assertEqual(report.final_status, CheckStatus.FAIL)

    def test_student_key_comparison_pass(self) -> None:
        report = run_preflight(
            profile_name="teacher-key-letter",
            input_path=FIXTURES / "passing" / "guided-notes-two-page.pdf",
            subject="shurley",
            student_path=FIXTURES / "passing" / "guided-notes-two-page.pdf",
            teacher_path=FIXTURES / "passing" / "teacher-key-two-page.pdf",
        )
        self.assertIn(report.final_status, {CheckStatus.PASS, CheckStatus.WARN})

    def test_html_pass_and_fail(self) -> None:
        ok = run_preflight(profile_name="worksheet-letter", input_path=FIXTURES / "passing" / "printable.html")
        self.assertIn(ok.final_status, {CheckStatus.PASS, CheckStatus.WARN})
        bad = run_preflight(profile_name="worksheet-letter", input_path=FIXTURES / "failing" / "html-no-print.html")
        self.assertEqual(bad.final_status, CheckStatus.FAIL)

    def test_docx_and_pptx(self) -> None:
        docx = run_preflight(profile_name="guided-notes-letter", input_path=FIXTURES / "passing" / "guided-notes.docx")
        self.assertIn(docx.final_status, {CheckStatus.PASS, CheckStatus.WARN})
        pptx = run_preflight(profile_name="projector-slides", input_path=FIXTURES / "passing" / "projector.pptx")
        self.assertIn(pptx.final_status, {CheckStatus.PASS, CheckStatus.WARN})
        bad = run_preflight(profile_name="projector-slides", input_path=FIXTURES / "failing" / "pptx-out-of-bounds.pptx")
        self.assertEqual(bad.final_status, CheckStatus.FAIL)

    def test_cli_help(self) -> None:
        proc = subprocess.run([sys.executable, str(RUNNER), "--help"], capture_output=True, text=True, check=False)
        self.assertEqual(proc.returncode, 0)
        self.assertIn("--profile", proc.stdout)

    def test_cli_fail_fixture_nonzero(self) -> None:
        proc = subprocess.run(
            [
                sys.executable,
                str(RUNNER),
                "--profile",
                "worksheet-letter",
                "--input",
                str(FIXTURES / "failing" / "a4-page.pdf"),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 1)
        self.assertIn("FINAL STATUS: FAIL", proc.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
