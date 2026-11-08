"""Duplicate prevention for assignments, announcements, reminders, and pages."""
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.canvas_llm_deploy.artifact_identity import identity_record, same_course_and_week
from scripts.canvas_llm_deploy.client import FakeDeployClient
from scripts.canvas_llm_deploy.preflight import (
    classify_assessment_reminder,
    classify_weekly_announcement,
)
from scripts.canvas_llm_intake import manifest as intake_manifest
from scripts.canvas_llm_rollover import rollover
from scripts.canvas_llm_storage import isolated_storage


def test_weekly_announcement_identity_is_week_and_course_specific():
    proposed = {
        "title": "Math Canvas Weekly Update", "week_code": "Q2W5",
        "course_id": 26404, "delayed_post_at": "2026-11-08T05:01:00Z", "agenda_hash": "new",
    }
    prior = {"title": proposed["title"], "week_code": "Q2W4", "course_id": 26404, "agenda_hash": "old"}
    other_course = {"title": proposed["title"], "week_code": "Q2W5", "course_id": 26442, "agenda_hash": "new"}
    assert classify_weekly_announcement(proposed, [prior, other_course]) == "PRIOR_WEEK_SAME_TITLE"
    exact = {**proposed}
    assert classify_weekly_announcement(proposed, [exact]) == "EXACT_MATCH"
    changed = {**proposed, "agenda_hash": "edited"}
    assert classify_weekly_announcement(proposed, [changed]) == "BODY_CHANGED_SAME_WEEK"
    assert classify_weekly_announcement(proposed, [exact, {**exact, "id": "2"}]) == "AMBIGUOUS"


def test_reminder_is_not_the_first_notice_or_another_course():
    reminder = {
        "title": "Reminder — Spelling Test 55", "course_id": 26442,
        "notice_role": "reminder", "type": "spelling",
        "message": "Spelling Test 55", "assessment_date": "2026-11-13",
    }
    first = {
        "title": "Spelling Test 55", "course_id": 26442, "notice_role": "first",
        "message": "Spelling Test 55 is Friday",
    }
    other = {**first, "course_id": 28171, "notice_role": "reminder", "title": "Reminder — Spelling Test 55"}
    assert classify_assessment_reminder(reminder, [first, other]) == "NEW"
    scheduled = {**reminder, "message": reminder["message"]}
    assert classify_assessment_reminder(reminder, [scheduled]) == "EXACT_MATCH"
    assert classify_assessment_reminder(reminder, [scheduled, {**scheduled, "id": "b"}]) == "AMBIGUOUS"


def test_assignment_conflicting_identity_blocks_before_create():
    manifest = {
        "from_week": "Q2W4", "to_week": "Q2W5", "source_hash": "source",
        "plan_fingerprint": "fp", "scheduled_at": "2026-11-08T05:01:00Z",
        "timezone": "America/New_York", "academic_courses": [], "homeroom": None,
        "weekly_announcements": [], "assessment_reminders": [],
        "assignments": [{
            "course": "math", "course_id": 26404, "title": "Written Assessment 8",
            "assessment_identity": "math-wa-8", "assignment_group": "Classwork",
            "due_utc": "2026-11-11T03:59:00Z", "action": "CREATE", "approved": True,
            "points_possible": 100, "grading_type": "percent", "submission_types": ["on_paper"],
        }],
    }
    client = FakeDeployClient(courses={26404: {"id": 26404, "name": "Math"}})
    client.assignment_groups[26404] = [{"id": "g", "name": "Classwork"}]
    client.assignments["a"] = {"id": "a", "course_id": 26404, "title": "Written Assessment 8", "assessment_identity": "math-wa-8", "due_at": "2026-11-11T03:59:00Z"}
    client.assignments["b"] = {"id": "b", "course_id": 26404, "title": "WA 8 copy", "assessment_identity": "math-wa-8", "due_at": "2026-11-11T03:59:00Z"}
    result = rollover.run_preflight(2, 4, 2, 5, client, manifest_override=manifest)
    assert result["ready"] is False
    assert any("conflicting Canvas IDs" in item for item in result["blockers"])
    assert client._write_counts["POST"] == 0
    assert manifest["assignments"][0]["action"] == "BLOCKED"


def _future() -> str:
    selected = (datetime.now(ZoneInfo("America/New_York")) + timedelta(days=1)).replace(
        hour=0, minute=1, second=0, microsecond=0,
    )
    return selected.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def test_changed_due_date_does_not_create_a_second_assignment():
    manifest = {
        "from_week": "Q2W2", "to_week": "Q2W3", "source_hash": "source", "plan_fingerprint": "fp",
        "scheduled_at": _future(), "owner_publication_time": _future(), "timezone": "America/New_York",
        "academic_courses": [], "weekly_announcements": [], "assessment_reminders": [],
        "assignments": [{
            "course": "math", "course_id": 26404, "title": "Math Lesson 46",
            "assignment_group": "Classwork", "points_possible": 100,
            "grading_type": "percent", "submission_types": ["on_paper"],
            "due_utc": "2026-11-12T03:59:00Z", "action": "CREATE", "approved": True,
        }],
    }
    with isolated_storage():
        intake_manifest.save_manifest(2, 3, {
            "quarter": 2, "week": 3, "status": "READY_TO_PUBLISH", "approval_state": "APPROVED",
            "source_hash": "source", "plan_fingerprint": "fp",
        })
        client = FakeDeployClient(courses={26404: {"id": 26404, "name": "Math"}})
        client.assignments["old"] = {
            "id": "old", "course_id": 26404, "title": "Math Lesson 46",
            "due_at": "2026-11-10T03:59:00Z", "points_possible": 100,
            "grading_type": "percent", "submission_types": ["on_paper"], "published": True,
        }
        report = rollover.execute(
            2, 2, 2, 3, client=client, owner_confirmation="ROLLOVER Q2W3",
            now=datetime.now(timezone.utc), manifest=manifest,
        )
        assert any("refusing to duplicate" in item for item in report.get("failures") or [])
        assert client._write_counts["POST"] == 0
        assert len(client.assignments) == 1


def test_ambiguous_announcement_is_not_created():
    owner = _future()
    manifest = {
        "from_week": "Q2W2", "to_week": "Q2W3", "source_hash": "source", "plan_fingerprint": "fp",
        "scheduled_at": owner, "owner_publication_time": owner, "timezone": "America/New_York",
        "academic_courses": [], "assignments": [], "assessment_reminders": [],
        "weekly_announcements": [{
            "subject": "math", "course_id": 26404, "title": "Math Canvas Weekly Update",
            "message": "<p>Math</p>", "classification": "AMBIGUOUS", "action": "BLOCKED",
            "approved": True,
        }],
    }
    with isolated_storage():
        intake_manifest.save_manifest(2, 3, {
            "quarter": 2, "week": 3, "status": "READY_TO_PUBLISH", "approval_state": "APPROVED",
            "source_hash": "source", "plan_fingerprint": "fp",
        })
        client = FakeDeployClient(courses={26404: {"id": 26404, "name": "Math"}})
        report = rollover.execute(
            2, 2, 2, 3, client=client, owner_confirmation="ROLLOVER Q2W3",
            now=datetime.now(timezone.utc), manifest=manifest,
        )
        assert report["lifecycle"] != "PUBLISHED_VERIFIED"
        assert any("blocked" in item.lower() or "ambiguous" in item.lower() for item in report.get("failures") or [])
        assert client._write_counts["POST"] == 0


def test_identity_record_keeps_course_and_week_apart():
    math = identity_record({
        "course_id": 26404, "week_code": "Q2W5", "title": "Lesson 46",
        "assessment_identity": "math-46", "assessment_date": "2026-11-10",
        "delayed_post_at": "2026-11-08T05:01:00Z",
    }, artifact_type="assignment")
    reading = {**math, "course_id": 26442, "week": "Q2W4"}
    assert math["course_id"] == 26404
    assert math["artifact_type"] == "assignment"
    assert same_course_and_week(math, reading) is False
    assert "canvas_id" not in math


def _run():
    fns = [(name, fn) for name, fn in sorted(globals().items()) if name.startswith("test_") and callable(fn)]
    failed = 0
    for name, fn in fns:
        try:
            fn()
            print(f"PASS {name}")
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"FAIL {name}: {type(exc).__name__}: {exc}")
    print(f"RESULT: {len(fns) - failed} passed, {failed} failed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    _run()
