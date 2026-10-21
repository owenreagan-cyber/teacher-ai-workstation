"""Plan editing, assignment coupling, history, and undo tests."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts.canvas_llm_intake import manifest
from scripts.canvas_planner.events import read_events
from scripts.teacher_workstation import mutate


def _write(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


class PlanEditTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.patch = mock.patch.object(manifest, "staging_dir", side_effect=lambda q, w: self.root / f"q{q}w{w}")
        self.patch.start()
        m = manifest.new_manifest(quarter=2, week=3, week_code="Q2W3",
                                  date_range={"start": "2026-10-26", "end": "2026-10-30"})
        m["source_hash"] = "source"
        manifest.save_manifest(2, 3, m)
        d = self.root / "q2w3"
        _write(d / "normalized/week.json", {"days": {"Monday": {"date": "2026-10-26"}}})
        _write(d / "drafts/assignments.json", [{
            "course": "math", "due_date": "2026-10-26", "title": "Old homework"
        }])
        _write(d / "drafts/announcements.json", [])
        _write(d / "drafts/assessment-reminders.json", [])
        (d / "drafts/math-page.html").write_text("<p>Math</p>", encoding="utf-8")

    def tearDown(self) -> None:
        self.patch.stop()
        self.tmp.cleanup()

    def test_edit_updates_assignment_records_history_and_can_undo(self) -> None:
        with mock.patch.object(mutate, "_regenerate", return_value={"ok": True}), \
                mock.patch("scripts.teacher_workstation.adapter._compute_draft_hashes", return_value={"math": {}}):
            result = mutate.apply_day_edit(
                quarter=2, week=3, subject="math", day="Monday",
                in_class=["Lesson 39"], at_home="Lesson 39 practice",
                status="PLANNED", source_hash="source",
            )
            assignment = json.loads((self.root / "q2w3/drafts/assignments.json").read_text())[0]
            self.assertEqual(assignment["title"], "Lesson 39 practice")
            self.assertEqual(assignment["source_reason"], "OWNER_OVERRIDE")
            self.assertEqual(result["override"]["in_class"], ["Lesson 39"])
            self.assertEqual(read_events(self.root / "q2w3")[-1]["action"], "plan_edit")
            undone = mutate.undo_last_plan_edit(quarter=2, week=3, source_hash="source")
            self.assertEqual(undone["subject"], "math")
            from scripts.canvas_llm_intake import owner_overrides
            self.assertIsNone(owner_overrides.day_override(2, 3, "math", "Monday"))
            self.assertEqual(read_events(self.root / "q2w3")[-1]["action"], "plan_edit_undone")


if __name__ == "__main__":
    unittest.main()
