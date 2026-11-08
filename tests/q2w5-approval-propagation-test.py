"""Approval reaches the plan items the prewrite gate checks. No Canvas and no real week."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.canvas_llm_deploy.client import FakeDeployClient
from scripts.canvas_llm_deploy.plan import build_plan
from scripts.canvas_llm_intake import approval, manifest as imf
from scripts.canvas_llm_rollover import manifest as rollover_manifest
from scripts.canvas_llm_rollover import rollover
from scripts.canvas_llm_rollover.schedule import resolve_publication_time
from scripts.canvas_llm_storage import isolated_storage
from scripts.canvas_planner.approval_bundle import current_bundle

NOW = datetime(2026, 11, 7, 22, 0, tzinfo=timezone.utc)
FUTURE = "2026-11-08T18:00:00Z"
SOURCE = "source-hash"
SUBJECTS = ["math", "reading_spelling", "language_arts", "science"]


def _packet():
    manifest = imf.new_manifest(
        quarter=2, week=5, week_code="Q2W5",
        date_range={"start": "2026-11-09", "end": "2026-11-13"},
    )
    manifest["source_hash"] = SOURCE
    manifest["status"] = "READY_FOR_REVIEW"
    imf.save_manifest(2, 5, manifest)
    staging = imf.staging_dir(2, 5)
    drafts = staging / "drafts"
    drafts.mkdir(parents=True, exist_ok=True)
    (drafts / "announcements.json").write_text(json.dumps([
        {"course": "Math", "title": "Math Canvas Weekly Update", "page_id": 798076, "message": "Math week"},
        {"course": "Reading/Spelling", "title": "Reading/Spelling Canvas Weekly Update", "page_id": 797993, "message": "Reading week"},
    ]), encoding="utf-8")
    (drafts / "assessment-reminders.json").write_text(json.dumps([
        {
            "course": "Reading/Spelling", "title": "Spelling Test 55 — Friday, November 13",
            "course_id": 26442, "subject": "reading_spelling", "assessment_date": "2026-11-13",
            "proposed_post_date": "2026-11-11", "delayed_post_at": "2026-11-11T21:00:00Z",
            "schedule_state": "FUTURE_SCHEDULED", "content_status": "READY",
            "duplicate_identity": "spell-55", "duplicate_status": "UNIQUE", "body": "Friday, November 13",
        },
        {
            "course": "Language Arts", "title": "Reminder — Shurley English Chapter 7 Test",
            "course_id": 28171, "subject": "language_arts", "assessment_date": "2026-11-13",
            "proposed_post_date": "2026-11-11", "delayed_post_at": "2026-11-11T21:00:00Z",
            "schedule_state": "FUTURE_SCHEDULED", "content_status": "READY",
            "duplicate_identity": "ch7", "duplicate_status": "UNIQUE", "body": "Friday, November 13",
        },
    ]), encoding="utf-8")
    (drafts / "assignments.json").write_text(json.dumps([
        {"course": "reading_spelling", "course_id": 26442, "title": "RM4: Spelling Test 55", "due_date": "2026-11-13"},
        {"course": "language_arts", "course_id": 28171, "title": "ELA4: Chapter 7 Test", "due_date": "2026-11-13"},
    ]), encoding="utf-8")
    (staging / "planner").mkdir(parents=True, exist_ok=True)
    (staging / "planner" / "owner-publication-times.json").write_text(json.dumps({
        "release": FUTURE,
        "notices": {},
    }), encoding="utf-8")


def _approve(subject, granularity, fingerprint):
    hashes = current_bundle(2, 5, subject)["hashes"]
    approval.approve_artifact(
        2, 5, subject, granularity,
        draft_hash=hashes[granularity], source_hash=SOURCE, subjects=SUBJECTS,
        plan_fingerprint=fingerprint, owner_publication_time=FUTURE,
        course_id={"math": 26404, "reading_spelling": 26442, "language_arts": 28171}[subject],
    )


def test_resolution_is_granular_and_fail_closed():
    record = {
        "state": "APPROVED", "draft_hash": "draft", "source_hash": SOURCE,
        "approved_at": "2026-11-08T00:00:00Z", "approved_by": "OWNER_UI",
        "plan_fingerprint": "finger", "owner_publication_time": FUTURE,
        "quarter": 2, "week": 5, "course_id": 26404, "school_year": "2026-2027",
    }
    ok = approval.resolve_artifact_approval(
        record, draft_hash="draft", source_hash=SOURCE, subject="math",
        granularity="announcement", quarter=2, week=5, course_id=26404,
        plan_fingerprint="finger", owner_publication_time=FUTURE,
    )
    assert ok["approved"] is True and ok["approval_state"] == "APPROVED"
    pending = approval.resolve_artifact_approval(
        {"state": "PENDING"}, draft_hash="draft", source_hash=SOURCE, subject="math",
        granularity="announcement", quarter=2, week=5,
    )
    assert pending["approved"] is False and pending["approval_state"] == "PENDING"
    other_course = approval.resolve_artifact_approval(
        record, draft_hash="draft", source_hash=SOURCE, subject="reading_spelling",
        granularity="announcement", quarter=2, week=5, course_id=26442,
        plan_fingerprint="finger", owner_publication_time=FUTURE,
    )
    assert other_course["approved"] is False
    other_week = approval.resolve_artifact_approval(
        record, draft_hash="draft", source_hash=SOURCE, subject="math",
        granularity="announcement", quarter=2, week=4, course_id=26404,
        plan_fingerprint="finger",
    )
    assert other_week["approved"] is False and other_week["approval_state"] == "BLOCKED"
    other_type = approval.resolve_artifact_approval(
        {**record, "granularity": "announcement"}, draft_hash="draft", source_hash=SOURCE,
        subject="math", granularity="assessment_reminder", quarter=2, week=5, course_id=26404,
        plan_fingerprint="finger",
    )
    assert other_type["approved"] is False
    assert approval.resolve_artifact_approval(
        record, draft_hash="other", source_hash=SOURCE, subject="math",
        granularity="announcement", quarter=2, week=5, course_id=26404, plan_fingerprint="finger",
    )["approved"] is False
    assert approval.resolve_artifact_approval(
        record, draft_hash="draft", source_hash=SOURCE, subject="math",
        granularity="announcement", quarter=2, week=5, course_id=26404, plan_fingerprint="other",
    )["approval_block"] == "plan fingerprint mismatch"
    assert approval.resolve_artifact_approval(
        None, draft_hash="draft", source_hash=SOURCE, subject="math",
        granularity="announcement", quarter=2, week=5,
    )["approval_block"] == "missing approval record"
    duplicate = approval.resolve_artifact_approval(
        [record, record], draft_hash="draft", source_hash=SOURCE, subject="math",
        granularity="announcement", quarter=2, week=5,
    )
    assert duplicate["approval_state"] == "BLOCKED"


def test_owner_time_distinguishes_weekly_posts_from_assessment_dates():
    try:
        resolve_publication_time("2026-11-09", now=NOW, owner_selected_at="2026-11-06T21:00:00Z")
        raise AssertionError("expired Friday publication time must be rejected")
    except ValueError:
        pass
    try:
        resolve_publication_time("2026-11-09", now=NOW, owner_selected_at="2026-11-08T18:00:00")
        raise AssertionError("naive owner time must be rejected")
    except ValueError:
        pass
    selected = resolve_publication_time("2026-11-09", now=NOW, owner_selected_at=FUTURE)
    assert selected["scheduled_at"] == FUTURE
    missed = resolve_publication_time("2026-11-09", now=NOW)
    assert missed["requires_owner_time"] is True and missed["scheduled_at"] is None


def test_plan_propagates_approval_without_moving_assessment_dates():
    with isolated_storage():
        _packet()
        _approve("reading_spelling", "assessment_reminder", "temporary")
        _approve("reading_spelling", "assignments", "temporary")
        _approve("language_arts", "assessment_reminder", "temporary")
        _approve("math", "announcement", "temporary")
        discovered = build_plan(2, 5, now=NOW)
        fingerprint = discovered["plan_fingerprint"]
        _approve("reading_spelling", "assessment_reminder", fingerprint)
        _approve("reading_spelling", "assignments", fingerprint)
        _approve("math", "announcement", fingerprint)
        plan = build_plan(2, 5, now=NOW)
        spell = next(item for item in plan["assessment_reminders"] if "Test 55" in item["title"])
        chapter = next(item for item in plan["assessment_reminders"] if "Chapter 7" in item["title"])
        assert spell["approved"] is True
        assert chapter["approved"] is False and chapter["approval_state"] == "PENDING"
        assert spell["assessment_date"] == "2026-11-13"
        assert spell["delayed_post_at"] == "2026-11-11T21:00:00Z"
        assert chapter["delayed_post_at"] == "2026-11-11T21:00:00Z"
        assignment = next(item for item in plan["assignments"] if item["title"] == "RM4: Spelling Test 55")
        assert assignment["due_date"] == "2026-11-13" and assignment["approved"] is True
        math = next(item for item in plan["weekly_announcements"] if item["subject"] == "math")
        assert math["approved"] is True and math["delayed_post_at"] == FUTURE
        assert "2026-11-06" not in str(math["delayed_post_at"])
        rolled = rollover_manifest.build_rollover_manifest(2, 4, 2, 5, now=NOW)
        rolled_math = next(item for item in rolled["weekly_announcements"] if item["subject"] == "math")
        assert rolled_math["approved"] is True and rolled_math["delayed_post_at"] == FUTURE
        rolled_science = next(item for item in rolled["weekly_announcements"] if item["subject"] == "science")
        assert rolled_science["approved"] is False
        changed = build_plan(2, 5, now=NOW, owner_publication_time="2026-11-09T18:00:00Z")
        assert changed["plan_fingerprint"] != plan["plan_fingerprint"]
        changed_math = next(item for item in changed["weekly_announcements"] if item["subject"] == "math")
        assert changed_math["approved"] is False
        changed_spell = next(item for item in changed["assessment_reminders"] if "Test 55" in item["title"])
        assert changed_spell["delayed_post_at"] == "2026-11-11T21:00:00Z"
        assert changed_spell["assessment_date"] == "2026-11-13"


def test_expired_weekly_time_is_not_copied_and_homeroom_notice_blocks():
    with isolated_storage():
        _packet()
        path = imf.staging_dir(2, 5) / "planner" / "owner-publication-times.json"
        path.write_text(json.dumps({"release": "2026-11-06T21:00:00Z", "notices": {}}), encoding="utf-8")
        rolled = rollover_manifest.build_rollover_manifest(2, 4, 2, 5, now=NOW)
        assert all(item.get("delayed_post_at") != "2026-11-06T21:00:00Z" for item in rolled["weekly_announcements"])
        assert all(item.get("schedule_state") == "OWNER_TIME_REQUIRED" for item in rolled["weekly_announcements"])
        blockers = rollover._prewrite_blockers(
            {
                "weekly_announcements": [{"subject": subject, "title": subject, "course_id": 1, "approved": True,
                                          "schedule_state": "FUTURE_SCHEDULED", "delayed_post_at": FUTURE,
                                          "action": "CREATE"} for subject in SUBJECTS],
                "academic_courses": [],
                "assessment_reminders": [],
                "assignments": [],
                "homeroom": {"mode": "homeroom_weekly_newsletter_html", "approved": True, "course_id": 26429,
                             "proposed_content_hash": "hash"},
            },
            None,
            now=NOW, quarter=2, week=5,
        )
        assert "homeroom announcement is missing" in blockers


def test_invalid_approval_does_not_write():
    with isolated_storage():
        _packet()
        before = (imf.staging_dir(2, 5) / "intake-manifest.json").read_bytes()
        client = FakeDeployClient(courses={26404: {"id": 26404, "name": "Math"}})
        result = rollover.execute(
            2, 4, 2, 5, client=client, owner_confirmation="ROLLOVER Q2W5",
            now=NOW,
            manifest={
                "from_week": "Q2W4", "to_week": "Q2W5", "source_hash": SOURCE,
                "scheduled_at": FUTURE, "timezone": "America/New_York",
                "publication_time_required": True, "owner_publication_time": FUTURE,
                "academic_courses": [],
                "weekly_announcements": [{
                    "subject": "math", "title": "Math Canvas Weekly Update", "course_id": 26404,
                    "approved": False, "approval_state": "PENDING", "action": "CREATE",
                    "schedule_state": "FUTURE_SCHEDULED", "delayed_post_at": FUTURE, "message": "x",
                }],
                "assignments": [], "assessment_reminders": [], "homeroom": {},
            },
        )
        assert result["lifecycle"] == "BLOCKED"
        assert client._write_counts["POST"] == 0 and client._write_counts["PUT"] == 0
        from scripts.canvas_llm_rollover import ledger as rollover_ledger
        from scripts.canvas_llm_deploy import ledger as deploy_ledger
        assert rollover_ledger.load_rollover_ledger(2, 5) is None
        assert deploy_ledger.load_ledger(2, 5) is None
        assert (imf.staging_dir(2, 5) / "intake-manifest.json").read_bytes() == before


def _run():
    failed = 0
    tests = [(name, fn) for name, fn in sorted(globals().items()) if name.startswith("test_") and callable(fn)]
    for name, fn in tests:
        try:
            fn()
            print(f"PASS {name}")
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"FAIL {name}: {type(exc).__name__}: {exc}")
    print(f"RESULT: {len(tests) - failed} passed, {failed} failed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    _run()
