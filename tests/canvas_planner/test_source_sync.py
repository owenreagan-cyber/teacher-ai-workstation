"""Review-first source resync tests (fixture-only)."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts.canvas_llm_intake import intake, manifest, owner_overrides
from scripts.canvas_planner import source_sync
from scripts.canvas_planner.events import read_events


def _week(math_tuesday: str) -> dict:
    subjects = ("math", "reading", "spelling", "language_arts", "science", "history")
    days = {}
    for index, day in enumerate(("Monday", "Tuesday", "Wednesday", "Thursday", "Friday"), start=26):
        days[day] = {
            "date": f"2026-10-{index}",
            "subjects": {subject: {"raw": "", "blank": True} for subject in subjects},
        }
        days[day]["subjects"]["math"] = {"raw": math_tuesday if day == "Tuesday" else "L39", "blank": False}
    return {
        "schemaVersion": 1,
        "week": {"code": "Q2W3", "startDate": "2026-10-26", "endDate": "2026-10-30"},
        "days": days,
        "source": {"readTimestampUtc": "2026-10-21T12:00:00Z"},
    }


class SourceSyncTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.patch = mock.patch.object(manifest, "staging_dir", side_effect=lambda q, w: self.root / f"q{q}w{w}")
        self.patch.start()
        base = self.root / "q2w3"
        original = _week("L40")
        m = manifest.new_manifest(
            quarter=2, week=3, week_code="Q2W3",
            date_range={"start": "2026-10-26", "end": "2026-10-30"},
        )
        m["source_hash"] = intake._content_hash(original)
        m["source_retrieved_at"] = "2026-10-20T12:00:00Z"
        m["subjects"] = {s: {"state": "READY_FOR_REVIEW"} for s in ("math", "reading_spelling", "language_arts", "science")}
        manifest.save_manifest(2, 3, m)
        (base / "source").mkdir(parents=True)
        (base / "source/pacing-snapshot.json").write_text(json.dumps({"normalized": original}), encoding="utf-8")
        (base / "normalized").mkdir()
        (base / "normalized/week.json").write_text(json.dumps(original), encoding="utf-8")
        owner_overrides.upsert_override(
            2, 3, subject="math", day="Wednesday", source_value="Review",
            in_class=["Owner review"], at_home="Study", status="PLANNED",
        )

    def tearDown(self) -> None:
        self.patch.stop()
        self.tmp.cleanup()

    def test_proposal_lists_delta_impacts_kept_overrides_and_applies_nothing(self) -> None:
        before_snapshot = (self.root / "q2w3/source/pacing-snapshot.json").read_text()
        before_normalized = (self.root / "q2w3/normalized/week.json").read_text()
        proposal = source_sync.propose_from_normalized(
            2, 3, normalized=_week("L41"), source_metadata={"readTimestampUtc": "2026-10-21T12:00:00Z"}
        )
        self.assertEqual(proposal["status"], "PENDING_DECISION")
        self.assertEqual(proposal["changed_cells"][0]["before"], "L40")
        self.assertEqual(proposal["changed_cells"][0]["after"], "L41")
        self.assertIn("math assignments", proposal["changed_cells"][0]["affects"])
        self.assertEqual(proposal["kept_overrides"][0]["day"], "Wednesday")
        self.assertIn("science", proposal["unchanged_subjects"])
        self.assertEqual((self.root / "q2w3/source/pacing-snapshot.json").read_text(), before_snapshot)
        self.assertEqual((self.root / "q2w3/normalized/week.json").read_text(), before_normalized)
        self.assertEqual(read_events(self.root / "q2w3")[-1]["action"], "source_resync_proposed")

    def test_keep_resolves_action_and_preserves_packet_and_override(self) -> None:
        source_sync.propose_from_normalized(2, 3, normalized=_week("L41"))
        result = source_sync.decide(2, 3, decision="KEEP")
        self.assertEqual(result["decision"], "KEPT")
        self.assertEqual(json.loads((self.root / "q2w3/normalized/week.json").read_text())["days"]["Tuesday"]["subjects"]["math"]["raw"], "L40")
        self.assertEqual(owner_overrides.day_override(2, 3, "math", "Wednesday")["at_home"], "Study")

    def test_apply_uses_reviewed_normalized_data_and_preserves_override(self) -> None:
        source_sync.propose_from_normalized(2, 3, normalized=_week("L41"))
        with mock.patch.object(intake, "build_intake", return_value={"source_hash": "new", "week_code": "Q2W3"}) as build:
            result = source_sync.decide(2, 3, decision="APPLY")
        self.assertEqual(result["decision"], "APPLIED")
        kwargs = build.call_args.kwargs
        self.assertEqual(kwargs["normalized_override"]["days"]["Tuesday"]["subjects"]["math"]["raw"], "L41")
        self.assertFalse(kwargs["fresh"])
        self.assertEqual(owner_overrides.day_override(2, 3, "math", "Wednesday")["at_home"], "Study")


if __name__ == "__main__":
    unittest.main()
