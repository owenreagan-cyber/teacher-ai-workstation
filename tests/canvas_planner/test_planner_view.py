"""Planner view-model and exact-preview tests (fixture-only)."""
from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

from scripts.canvas_llm_intake import manifest
from scripts.canvas_planner.service import CanvasPlannerService


def _write(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(value, str):
        path.write_text(value, encoding="utf-8")
    else:
        path.write_text(json.dumps(value), encoding="utf-8")


class PlannerViewTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.week_dir = self.root / "canvas-llm/intake/2026-2027/q2/w3"
        self.patch = mock.patch.object(manifest, "staging_dir", side_effect=lambda q, w: self.week_dir)
        self.patch.start()
        subjects = ("math", "reading_spelling", "language_arts", "science")
        _write(self.week_dir / "intake-manifest.json", {
            "quarter": 2, "week": 3, "week_code": "Q2W3",
            "date_range": {"start": "2026-10-26", "end": "2026-10-30"},
            "pacing_source": "Fixture pacing", "pacing_tab": "4A - Fixture",
            "source_hash": "source", "source_retrieved_at": "2026-10-20T12:00:00Z",
            "generated_at": "2026-10-20T12:00:00Z", "status": "READY_FOR_REVIEW",
            "subjects": {subject: {"state": "READY_FOR_REVIEW"} for subject in subjects},
        })
        days = {}
        for index, day in enumerate(("Monday", "Tuesday", "Wednesday", "Thursday", "Friday"), start=26):
            days[day] = {"date": f"2026-10-{index}", "subjects": {
                "math": {"raw": "L39"}, "reading": {"raw": "46"}, "spelling": {"raw": "41"},
                "language_arts": {"raw": "Ch 5"}, "science": {"raw": "Electricity"},
            }}
        _write(self.week_dir / "normalized/week.json", {"days": days})
        _write(self.week_dir / "source/pacing-snapshot.json", {"spreadsheet_id": "fixture", "normalized": {"days": days}})
        for subject, filename in (("math", "math-page.html"), ("reading_spelling", "reading-page.html"),
                                  ("language_arts", "language_arts-page.html"), ("science", "science-page.html")):
            _write(self.week_dir / "drafts" / filename, f"<div>{subject} exact agenda</div>")
        _write(self.week_dir / "drafts/assignments.json", [{
            "course": "math", "title": "Lesson 39", "assignment_group": "Homework", "due_date": "2026-10-26"
        }])
        _write(self.week_dir / "drafts/announcements.json", [
            {"course": name, "greeting": "Good afternoon,", "transition": "See the exact agenda."}
            for name in ("Math", "Reading/Spelling", "Language Arts", "Science")
        ])
        _write(self.week_dir / "drafts/assessment-reminders.json", [])
        _write(self.week_dir / "questions/questions.json", [])
        _write(self.week_dir / "approvals/approval-manifest.json", {"subjects": {
            subject: {artifact: {"state": "PENDING"} for artifact in ("page", "announcement", "assignments", "assessment_reminder")}
            for subject in subjects
        }})

    def tearDown(self) -> None:
        self.patch.stop()
        self.tmp.cleanup()

    def test_all_five_courses_and_exact_agenda_shared_with_announcement(self) -> None:
        data = CanvasPlannerService(self.root).planner_week(
            2, 3, now=datetime(2026, 10, 21, tzinfo=timezone.utc)
        )
        self.assertEqual([c["id"] for c in data["courses"]],
                         ["math", "reading_spelling", "language_arts", "science", "homeroom"])
        math = data["courses"][0]
        self.assertEqual(math["page_html"], "<div>math exact agenda</div>")
        self.assertIn(math["page_html"], math["announcement"]["exact_html"])
        self.assertEqual(math["days"][0]["assignments"][0]["title"], "Lesson 39")
        self.assertEqual(data["settings"]["state_root"], str(self.root))

    def test_static_ui_has_only_stage_destinations_and_sandboxed_previews(self) -> None:
        app = Path("apps/teacher-workstation/app.js").read_text(encoding="utf-8")
        index = Path("apps/teacher-workstation/index.html").read_text(encoding="utf-8")
        for label in ("1 · Source", "2 · Plan", "3 · AI review", "4 · Preview & approve", "5 · Friday"):
            self.assertIn(label, app)
        self.assertNotIn("{ id: 'assignments'", app)
        self.assertNotIn("{ id: 'deploy'", app)
        self.assertIn('class="preview-frame" data-preview="page" sandbox', app)
        self.assertIn("Nothing goes to Canvas until Friday 4 PM", index)


if __name__ == "__main__":
    unittest.main()
