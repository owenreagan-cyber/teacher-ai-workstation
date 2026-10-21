"""AI review and atomic course approval tests (fixture-only)."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts.canvas_llm_intake import manifest
from scripts.canvas_planner import ai_review, approval_bundle


def _write(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(value, str):
        path.write_text(value, encoding="utf-8")
    else:
        path.write_text(json.dumps(value), encoding="utf-8")


class FakeReviewer:
    model = "fake-reviewer-v1"

    def review(self, packet):
        return {
            "checks": [{"id": "plan_matches_sheet", "state": "PASS"}],
            "courses": {"math": {"state": "NEEDS_OWEN", "findings": [{
                "id": "math-reminder", "status": "NEEDS_OWEN",
                "title": "Math test has no reminder", "reason": "A reminder is missing.",
                "evidence": "sheet · Thursday · WA7",
            }]}},
        }


class AiApprovalTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.patch = mock.patch.object(manifest, "staging_dir", side_effect=lambda q, w: self.root / f"q{q}w{w}")
        self.patch.start()
        d = self.root / "q2w3"
        m = manifest.new_manifest(quarter=2, week=3, week_code="Q2W3",
                                  date_range={"start": "2026-10-26", "end": "2026-10-30"})
        m.update({"source_hash": "source", "subjects": {
            "math": {}, "reading_spelling": {}, "language_arts": {}, "science": {}
        }})
        manifest.save_manifest(2, 3, m)
        _write(d / "drafts/math-page.html", "<div>Math agenda v1</div>")
        _write(d / "drafts/assignments.json", [{"course": "math", "title": "Lesson 39"}])
        _write(d / "drafts/announcements.json", [{"course": "Math", "transition": "See the week."}])
        _write(d / "drafts/assessment-reminders.json", [])
        _write(d / "questions/questions.json", [])

    def tearDown(self) -> None:
        self.patch.stop()
        self.tmp.cleanup()

    def test_ai_findings_require_evidence_and_ai_cannot_write_packet(self) -> None:
        packet = {"math": {"lesson": "L39"}}
        manifest_before = (self.root / "q2w3/intake-manifest.json").read_text()
        result = ai_review.run(2, 3, reviewer=FakeReviewer(), packet=packet)
        self.assertEqual(result["model"], "fake-reviewer-v1")
        self.assertEqual(result["courses"]["math"]["findings"][0]["evidence"], "sheet · Thursday · WA7")
        self.assertEqual((self.root / "q2w3/intake-manifest.json").read_text(), manifest_before)

    def test_unavailable_is_never_pass(self) -> None:
        result = ai_review.unavailable(2, 3, reason="No eligible model entitlement")
        self.assertEqual(result["state"], "UNAVAILABLE")
        self.assertTrue(all(c["state"] == "UNAVAILABLE" for c in result["checks"]))

    def test_atomic_hash_approval_and_reapproval_diff(self) -> None:
        current = approval_bundle.current_bundle(2, 3, "math")
        approved = approval_bundle.approve_course(
            2, 3, course="math", expected_hashes=current["hashes"]
        )
        self.assertEqual(approved["state"], "APPROVED")
        data = json.loads((self.root / "q2w3/approvals/approval-manifest.json").read_text())
        self.assertTrue(all(rec["state"] in ("APPROVED", "NOT_REQUIRED")
                            for rec in data["subjects"]["math"].values()))
        _write(self.root / "q2w3/drafts/math-page.html", "<div>Math agenda v2</div>")
        diff = approval_bundle.reapproval_diff(2, 3, "math")
        self.assertTrue(diff["required"])
        self.assertEqual(diff["changes"][0]["artifact"], "page")
        self.assertIn("-\"<div>Math agenda v1</div>\"", diff["changes"][0]["diff"])
        with self.assertRaises(ValueError):
            approval_bundle.approve_course(2, 3, course="math", expected_hashes=current["hashes"])

    def test_unavailable_requires_explicit_confirmation_but_does_not_block_forever(self) -> None:
        ai_review.unavailable(2, 3, reason="offline")
        with self.assertRaises(ValueError):
            approval_bundle.approve_course(2, 3, course="math")
        result = approval_bundle.approve_course(2, 3, course="math", confirm_without_ai=True)
        self.assertEqual(result["state"], "APPROVED")


if __name__ == "__main__":
    unittest.main()
