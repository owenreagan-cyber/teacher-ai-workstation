"""Canvas weekly status contract tests (fixture-only, network denied)."""
from __future__ import annotations

import json
import socket
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

from scripts.canvas_planner.deep_links import deep_link, normalize_route
from scripts.canvas_planner.service import CanvasPlannerService


def _write(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


class StatusContractTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        week = self.root / "canvas-llm/intake/2026-2027/q2/w3"
        _write(week / "intake-manifest.json", {
            "quarter": 2, "week": 3, "week_code": "Q2W3",
            "date_range": {"start": "2026-10-26", "end": "2026-10-30"},
            "source_hash": "source", "source_retrieved_at": "2026-10-20T12:00:00Z",
            "generated_at": "2026-10-20T12:01:00Z",
            "status": "READY_FOR_REVIEW",
            "subjects": {s: {"state": "READY_FOR_REVIEW"} for s in ("math", "reading_spelling", "language_arts", "science")},
            "homeroom_approved": False,
        })
        approval = {s: {a: {"state": "APPROVED"} for a in ("page", "announcement", "assignments", "assessment_reminder")}
                    for s in ("math", "reading_spelling", "language_arts", "science")}
        approval["math"]["page"] = {"state": "PENDING", "invalidated_at": "2026-10-20T12:02:00Z"}
        _write(week / "approvals/approval-manifest.json", {"subjects": approval})
        _write(week / "questions/questions.json", [])
        _write(week / "drafts/assignments.json", [{"course": s} for s in approval])
        _write(week / "drafts/assessment-reminders.json", [])
        _write(week / "changes.json", {})
        _write(week / "planner/ai-review.json", {
            "created_at": "2026-10-20T12:02:00Z",
            "courses": {s: {"state": "PASS", "findings": []} for s in (*approval, "homeroom")},
        })
        self.service = CanvasPlannerService(self.root)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_shape_freshness_stable_ids_and_no_network(self) -> None:
        now = datetime(2026, 10, 21, 12, tzinfo=timezone.utc)
        with mock.patch.object(socket, "socket", side_effect=AssertionError("network attempted")):
            first = self.service.weekly_status(2, 3, now=now)
            second = self.service.weekly_status(2, 3, now=now)
        self.assertEqual(first["domain"], "canvas_weekly_planning")
        self.assertEqual(first["contract_version"], 1)
        self.assertEqual(first["generated_at"], "2026-10-21T12:00:00Z")
        self.assertEqual(first["week"]["code"], "Q2W3")
        self.assertEqual(first["week"]["rollover_at"], "2026-10-23T20:00:00Z")
        self.assertEqual([a["id"] for a in first["action_items"]], [a["id"] for a in second["action_items"]])
        self.assertTrue(all(a["created_at"] and a["updated_at"] for a in first["action_items"]))
        self.assertIn("#week/q2w3/", first["next_action"]["deep_link"])
        self.assertEqual(len(first["courses"]), 5)

    def test_source_change_precedes_approval(self) -> None:
        week = self.root / "canvas-llm/intake/2026-2027/q2/w3"
        _write(week / "changes.json", {"delta": {"changes": [
            {"subject": "math", "weekday": "Tuesday", "before": "L40", "after": "L41"}
        ]}})
        status = self.service.weekly_status(2, 3, now=datetime(2026, 10, 21, tzinfo=timezone.utc))
        self.assertEqual(status["next_action"]["title"], "Review pacing changes")
        self.assertTrue(status["next_action"]["deep_link"].endswith("/source"))

    def test_resolved_action_disappears(self) -> None:
        week = self.root / "canvas-llm/intake/2026-2027/q2/w3"
        _write(week / "changes.json", {"decision": "KEPT", "delta": {"changes": [
            {"subject": "math", "weekday": "Tuesday", "before": "L40", "after": "L41"}
        ]}})
        status = self.service.weekly_status(2, 3)
        self.assertFalse(any(a["id"].startswith("source-") for a in status["action_items"]))

    def test_missed_friday_deadline_exposes_publish_now_action(self) -> None:
        now = datetime(2026, 10, 23, 20, 0, tzinfo=timezone.utc)
        first = self.service.weekly_status(2, 3, now=now)
        second = self.service.weekly_status(2, 3, now=now)
        items = [a for a in first["action_items"] if a["id"] == "friday-readiness:q2w3"]
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["kind"], "decision")
        self.assertEqual(items[0]["title"], "Friday rollover didn't run — Publish now when ready")
        self.assertNotIn("math:page not approved", " ".join(item["title"] for item in first["action_items"]))
        self.assertTrue(items[0]["deep_link"].endswith("/friday"))
        self.assertEqual(items[0]["id"], next(
            a["id"] for a in second["action_items"] if a["id"].startswith("friday-readiness:")
        ))

    def test_homeroom_html_approval_marks_preview_approved(self) -> None:
        week = self.root / "canvas-llm/intake/2026-2027/q2/w3"
        import hashlib
        body = "<div>4th Grade Happenings</div><h2>Book Character Day</h2>"
        _write(week / "planner/homeroom-html-approval.json", {
            "kind": "rolling_newsletter_html",
            "course_id": 26429, "page_id": 798072,
            "page_slug": "class-4a-newsletter-x",
            "source_body_hash": "src",
            "approved_body_hash": hashlib.sha256(body.encode()).hexdigest(),
            "week": "Q2W3", "approved": True,
        })
        (week / "drafts/homeroom-page.html").write_text(body, encoding="utf-8")
        status = self.service.weekly_status(2, 3)
        homeroom = next(c for c in status["courses"] if c["id"] == "homeroom")
        self.assertEqual(homeroom["stages"]["preview"], "approved")
        self.assertFalse(any(a["course"] == "homeroom" for a in status["action_items"]))

    def test_deep_link_validation(self) -> None:
        self.assertEqual(normalize_route("#week/Q2W3/math/preview"), "week/q2w3/math/preview")
        self.assertEqual(deep_link("Q2W3", "source"), "http://127.0.0.1:4310/#week/q2w3/source")
        for bad in ("https://evil.example", "week/q2w3/math/deploy", "../etc/passwd"):
            with self.assertRaises(ValueError):
                normalize_route(bad)


if __name__ == "__main__":
    unittest.main()
