"""Q2W5 canonical assessment integration (synthetic, local-only).

Covers the Math Test 8 semantic override, the combined Fact Test announcement,
the Shurley Chapter 7 two-notice pair, missed-window fail-closed scheduling,
and Canvas delayed-post readback. No Canvas writes and no school URLs.
"""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.canvas_llm_deploy.client import FakeDeployClient
from scripts.canvas_llm_deploy.coordinator import (
    _verify_announcement,
    announcement_readback_disposition,
)
from scripts.canvas_llm_deploy.plan import _reminder_plan_entry
from scripts.canvas_llm_intake import assessment_announcements as aa
from scripts.canvas_llm_intake import intake as intake_mod
from scripts.canvas_llm_intake import manifest as intake_manifest
from scripts.canvas_llm_intake import owner_decisions as od
from scripts.canvas_llm_intake.scheduling import HELD_SCHEDULED
from scripts.canvas_llm_phase3 import pacing_announcement as pa
from scripts.canvas_llm_phase3 import pacing_math as pm
from scripts.canvas_llm_phase3 import pacing_translation as pt
from scripts.canvas_llm_rollover import homeroom_weekly
from scripts.canvas_llm_rollover import release_plan

NOW = datetime(2026, 11, 7, 17, 32, tzinfo=timezone.utc)
POWER_URL = "https://canvas.example.test/courses/26404/files/6120836"
CHECKUP_URL = "https://canvas.example.test/files/6206413"
KEY_URL = "https://canvas.example.test/files/6206412"
REVIEW = [
    "Classify sentences with compound subject nouns, compound subject pronouns, understood subject pronouns, compound verbs, compound adjectives, adverbs, article adjectives, prepositions, possessive pronouns, adjectives, and objects of prepositions.",
    "Complete a noun chart and identify nouns as singular/plural and common/proper. Identify the simple subject and simple predicate of a sentence.",
    "List the abbreviations for the seven parts of speech we have learned so far.",
    "Review sentence types: S, SCS, SCV, CD, CX, and F.",
    "Write complex sentences, compound sentences, simple sentences with compound subjects, and simple sentences with compound verbs.",
    "Know the vocabulary words career and inquire.",
    "Review Classroom Practice worksheets 25-30.",
]


def _week() -> dict:
    subjects = {
        "Monday": ("46", "L54", "51", "7.5", "U2 Ch1 Notes"),
        "Tuesday": ("Test 8", "L55", "52", "Vet Day Reheasal", "U2 Ch2"),
        "Wednesday": ("Veteran's Day", "L56", "53", "Veteran's Day", "U2 Ch2"),
        "Thursday": ("47", "L57", "54", "7.6 Checkup", "U2 Ch3"),
        "Friday": ("48", "L58", "Test 55", "Ch. 7 Test", "U2 Ch4"),
    }
    dates = {
        "Monday": "2026-11-09",
        "Tuesday": "2026-11-10",
        "Wednesday": "2026-11-11",
        "Thursday": "2026-11-12",
        "Friday": "2026-11-13",
    }
    days = {}
    for day, (math, reading, spelling, language, science) in subjects.items():
        days[day] = {
            "date": dates[day],
            "subjects": {
                "math": {"raw": math},
                "reading": {"raw": reading},
                "spelling": {"raw": spelling},
                "language_arts": {"raw": language},
                "science": {"raw": science},
            },
        }
    return {
        "week": {"code": "Q2W5", "startDate": "2026-11-09", "endDate": "2026-11-13"},
        "days": days,
    }


def _decisions() -> list[dict]:
    return [
        {
            "decision_id": "semantic_interpretation|math|Tuesday|2026-11-10",
            "kind": "semantic_interpretation",
            "subject": "math",
            "day": "Tuesday",
            "date": "2026-11-10",
            "source_value": "Test 8",
            "owner_value": "WA8/FA8",
            "written_title": "Cumulative Test 8",
            "fact_title": "Fact Test 8",
            "fact_count": 40,
            "power_up": "C",
            "active": True,
            "resources": [{
                "role": "power_up",
                "file_id": 6120836,
                "display_name": "Power Up C.pdf",
                "url": POWER_URL,
                "verified": True,
                "source": "CANVAS_FILE_METADATA",
            }],
        },
        {
            "decision_id": "assessment_override|language_arts|Friday|2026-11-13",
            "kind": "assessment_override",
            "subject": "language_arts",
            "day": "Friday",
            "date": "2026-11-13",
            "source_value": "Ch. 7 Test",
            "owner_value": "Shurley English Chapter 7 Test",
            "assessment_title": "Shurley English Chapter 7 Test",
            "preparation": REVIEW,
            "active": True,
            "resources": [
                {
                    "role": "practice",
                    "file_id": 6206413,
                    "display_name": "Chapter 7 Checkup 30.pdf",
                    "label": "Shurley English Practice Resource 1",
                    "url": CHECKUP_URL,
                    "verified": True,
                },
                {
                    "role": "practice",
                    "file_id": 6206412,
                    "display_name": "Checkup 30 Key.pdf",
                    "label": "Shurley English Practice Resource 2",
                    "url": KEY_URL,
                    "verified": True,
                },
            ],
        },
    ]


def test_math_semantic_override_preserves_source_and_splits_assessments():
    week = _week()
    before = intake_mod._content_hash(week)
    working, applied = od.apply_translation_working_copy(week, _decisions())
    assert week["days"]["Tuesday"]["subjects"]["math"]["raw"] == "Test 8"
    assert intake_mod._content_hash(week) == before
    assert working["days"]["Tuesday"]["subjects"]["math"]["raw"] == "WA8/FA8"
    assert applied[0]["applied"] is True
    report = pm.translate_math_week(working)
    report = intake_mod._apply_math_semantic_display(report, _decisions(), applied)
    titles = [item["title"] for item in report["assignments"]]
    assert titles == [
        "SM5: Lesson 46 Homework",
        "SM5: Written Assessment 8",
        "SM5: Fact Assessment 8",
        "SM5: Lesson 47 Classwork",
    ], titles
    by_title = {item["title"]: item for item in report["assignments"]}
    assert by_title["SM5: Lesson 46 Homework"]["due_date"] == "2026-11-09"
    assert by_title["SM5: Written Assessment 8"]["due_date"] == "2026-11-10"
    assert by_title["SM5: Written Assessment 8"]["assignment_group"] == "Written Assessments"
    assert by_title["SM5: Fact Assessment 8"]["assignment_group"] == "Fact Assessments"
    assert by_title["SM5: Lesson 47 Classwork"]["due_date"] == "2026-11-12"
    assert by_title["SM5: Lesson 47 Classwork"]["assignment_group"] == "Homework/Class Work"
    assert report["classwork_grade_day"] == "Thursday"
    assert report["days"]["Tuesday"]["in_class"] == ["Cumulative Test 8", "Fact Test 8"]
    assert "study guide" not in json.dumps(report).lower()


def test_language_arts_chapter_test_does_not_grade_checkup():
    report = pt.translate_subject_week(_week(), "language_arts")
    titles = [item["title"] for item in report["assignments"]]
    assert titles == ["ELA4: Chapter 7 Test"], titles
    assert report["assignments"][0]["due_date"] == "2026-11-13"
    assert not any("checkup" in title.lower() for title in titles)
    thursday = report["days"]["Thursday"]["lines"]
    assert thursday == ["7.6 Checkup"], thursday


def test_four_assessment_notices_schedule_and_identity():
    notices = aa.draft_two_notice_announcements(
        od.apply_translation_working_copy(_week(), _decisions())[0],
        source_hash="src", decisions=_decisions(), now=NOW,
    )
    assert len(notices) == 4, [item["title"] for item in notices]
    assert {item["notice_type"] for item in notices} == {"FIRST_NOTICE", "REMINDER"}
    assert len({item["duplicate_identity"] for item in notices}) == 4
    assert all(item["approval_state"] == "PENDING" and item["preview_only"] for item in notices)
    assert all(item["timezone"] == "America/New_York" for item in notices)
    assert all(item["duplicate_status"] == "UNIQUE" for item in notices)
    again = aa.draft_two_notice_announcements(
        od.apply_translation_working_copy(_week(), _decisions())[0],
        source_hash="src", decisions=_decisions(), now=NOW,
    )
    assert [item["duplicate_identity"] for item in notices] == [item["duplicate_identity"] for item in again]

    math = [item for item in notices if item["family"] == "math_assessment"]
    assert len(math) == 2
    assert len({item["title"] for item in math}) == 2
    for item in math:
        assert item["course_id"] == 26404
        assert item["assessment_date"] == "2026-11-10"
        assert "40 multiplication facts" in item["body"]
        assert "Power Up C" in item["body"]
        assert POWER_URL in item["body"]
        assert "6120836" in json.dumps(item["fact_packet"])
        assert "study guide" not in item["body"].lower()
        assert item["draft_hash"] and item["source_hash"] == "src"
    assert {item["proposed_post_date"] for item in math} == {"2026-11-05", "2026-11-06"}
    assert all(item["schedule_state"] == "OWNER_TIME_REQUIRED" for item in math)
    assert all(item["delayed_post_at"] is None and item["scheduled"] is False for item in math)

    language = [item for item in notices if item["family"] == "language_arts_assessment"]
    assert len(language) == 2
    body = "\n".join(item["body"] for item in language)
    for phrase in (
        "compound subject nouns", "compound subject pronouns", "understood subject pronouns",
        "compound verbs", "compound adjectives", "article adjectives", "possessive pronouns",
        "objects of prepositions", "noun chart", "singular/plural", "common/proper",
        "simple subject", "simple predicate", "S, SCS, SCV, CD, CX, and F",
        "complex sentences", "compound sentences", "compound subjects", "career and inquire",
        "25-30",
    ):
        assert phrase in body, phrase
    assert CHECKUP_URL in body and KEY_URL in body
    assert "6206413" in json.dumps(language) and "6206412" in json.dumps(language)
    first = next(item for item in language if item["notice_type"] == "FIRST_NOTICE")
    reminder = next(item for item in language if item["notice_type"] == "REMINDER")
    assert first["proposed_post_date"] == "2026-11-06"
    assert first["schedule_state"] == "OWNER_TIME_REQUIRED"
    assert reminder["proposed_post_date"] == "2026-11-11"
    assert reminder["schedule_state"] == "FUTURE_SCHEDULED"
    assert reminder["delayed_post_at"] == "2026-11-11T21:00:00Z"
    assert reminder["scheduled"] is True

    cloned = json.loads(json.dumps(notices))
    cloned[1]["duplicate_identity"] = cloned[0]["duplicate_identity"]
    aa._mark_duplicate_identities(cloned)
    assert cloned[0]["duplicate_status"] == "AMBIGUOUS"
    assert cloned[0]["schedule_state"] == pa.BLOCKED

    past_plan = _reminder_plan_entry(
        math[0], label="Math", subject="math", week_code="Q2W5", date_range={},
    )
    assert past_plan["action"] == "BLOCKED" and past_plan["delayed_post_at"] is None
    future_plan = _reminder_plan_entry(
        reminder, label="Language Arts", subject="language_arts", week_code="Q2W5", date_range={},
    )
    assert future_plan["scheduled"] is True
    assert future_plan["delayed_post_at"] == "2026-11-11T21:00:00Z"
    assert future_plan["action"] == "CREATE"


def test_canvas_readback_does_not_call_scheduled_announcement_published():
    client = FakeDeployClient(courses={28171: {"id": 28171, "name": "Language Arts"}})
    created = client.create_announcement(
        28171, title="Reminder — Shurley English Chapter 7 Test",
        message="Chapter 7 Test Friday, November 13.",
        published=True, delayed_post_at="2026-11-11T21:00:00Z",
    )
    ok, detail, state = _verify_announcement(
        client, 28171, created["id"], title=created["title"], scheduled=True,
        delayed_post_at="2026-11-11T21:00:00Z", expect_agenda=False, counts={},
        expected_message=created["message"],
    )
    assert ok, detail
    assert state == HELD_SCHEDULED
    disposition = announcement_readback_disposition(scheduled=True, verified=ok, state=state)
    assert disposition == "SCHEDULED_VERIFIED"
    assert disposition != "PUBLISHED_VERIFIED"


def test_weekly_release_hashes_homeroom_page_and_five_targets():
    week = _week()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        original = intake_manifest.staging_dir
        intake_manifest.staging_dir = lambda quarter, week_number: root / f"q{quarter}w{week_number}"
        try:
            summary = intake_mod.build_intake(
                quarter=2, week=5, normalized_override=week,
                source_meta_override={"readTimestampUtc": "2026-11-06T20:22:12+00:00"},
                page_lookup_override={
                    "math": {"status": "FOUND", "course_id": 26404, "page_id": 798076, "url": "q2w5"},
                    "reading_spelling": {"status": "FOUND", "course_id": 26442, "page_id": 797993, "url": "q2w5"},
                    "language_arts": {"status": "FOUND", "course_id": 28171, "page_id": 876756, "url": "q2w5"},
                    "science": {"status": "FOUND", "course_id": 28166, "page_id": 876778, "url": "q2w5"},
                },
                assignment_classifications={},
                decisions_override=_decisions(),
                now=NOW,
            )
            staged = root / "q2w5"
            assignments = json.loads((staged / "drafts" / "assignments.json").read_text())
            titles = [item["title"] for item in assignments]
            assert len(assignments) == 9, titles
            assert titles.count("ELA4: Chapter 7 Test") == 1
            assert not any("Checkup" in title for title in titles)
            announcements = json.loads((staged / "drafts" / "announcements.json").read_text())
            assert len(announcements) == 4
            for announcement in announcements:
                assert announcement["hash_consistent"] is True
                assert announcement["agenda_hash"] == announcement["page_agenda_hash"]
                subject = intake_mod._subject_key(announcement["course"])
                page_name = "reading-page.html" if subject == "reading_spelling" else f"{subject}-page.html"
                page_html = (staged / "drafts" / page_name).read_text(encoding="utf-8")
                assert announcement["agenda_hash"] == hashlib.sha256(page_html.encode("utf-8")).hexdigest()
            notices = json.loads((staged / "drafts" / "assessment-reminders.json").read_text())
            paired = [item for item in notices if item.get("notice_type") in ("FIRST_NOTICE", "REMINDER")]
            assert len(paired) == 4
            assert summary["ready_to_publish"] is False
            newsletter = "<div id='newsletter'>Veterans Day Concert Wednesday November 11, 9:00 AM, JH/HS Vikings Gym. Movie Night Friday November 13, 6:00–8:00 PM.</div>"
            (staged / "drafts" / "homeroom-page.html").write_text(newsletter, encoding="utf-8")
            homeroom_weekly.write_page_resolution(2, 5, {
                "week": "Q2W5", "course_id": 26429, "slug": "q2w5-november-9-13-2026",
                "page_id": 798096, "status": "FOUND",
            })
            family = homeroom_weekly.draft_family_announcement(2, 5, now=NOW)
            assert family["page_id"] == 798096
            assert family["contains_complete_newsletter_html"] is True
            assert newsletter in family["message"]
            assert family["schedule_state"] == "OWNER_TIME_REQUIRED"
            assert family["approval_state"] == "PENDING"
            assert family["publication_dependency"] == "HOMEROOM_PAGE_PUBLISHED_AND_VERIFIED"
            homeroom_weekly.write_family_announcement(2, 5, family)
            plan = release_plan.build_release_plan(2, 4, 2, 5, now=NOW)
            assert len(plan["front_page_targets"]) == 5
            assert {item["subject"] for item in plan["front_page_targets"]} == {
                "math", "reading_spelling", "language_arts", "science", "homeroom",
            }
            homeroom = next(item for item in plan["front_page_targets"] if item["subject"] == "homeroom")
            assert homeroom["page_id"] == 798096
            assert plan["homeroom_announcement"]["page_first"] is True
            assert plan["homeroom_announcement"]["contains_complete_newsletter_html"] is True
            assert plan["publication_time_required"] is True
            assert plan["scheduled_at"] is None
            assert plan["canvas_writes"] == 0 and plan["email_sends"] == 0
            assert week["days"]["Tuesday"]["subjects"]["math"]["raw"] == "Test 8"
        finally:
            intake_manifest.staging_dir = original


def test_semantic_mismatch_date_duplicate_and_inactive_fail_closed():
    week = _week()
    decisions = _decisions()
    drifted = json.loads(json.dumps(week))
    drifted["days"]["Tuesday"]["subjects"]["math"]["raw"] = "Lesson 99"
    _working, applied = od.apply_translation_working_copy(drifted, decisions)
    assert applied[0]["applied"] is False
    assert _working["days"]["Tuesday"]["subjects"]["math"]["raw"] == "Lesson 99"
    report = intake_mod._apply_math_semantic_display(
        pm.translate_math_week(_working), decisions, applied,
    )
    assert "Cumulative Test 8" not in report["days"]["Tuesday"]["in_class"]
    assert not any(item["title"].startswith("SM5: Written") for item in report["assignments"])
    assert od.semantic_publication_blockers(applied)

    wrong_date = json.loads(json.dumps(decisions))
    wrong_date[0]["date"] = "2026-11-09"
    _working, applied = od.apply_translation_working_copy(week, wrong_date)
    assert applied[0]["applied"] is False
    assert week["days"]["Tuesday"]["subjects"]["math"]["raw"] == "Test 8"

    duplicate = decisions + [dict(decisions[0], decision_id="semantic-duplicate")]
    _working, applied = od.apply_translation_working_copy(week, duplicate)
    assert all(record["applied"] is False for record in applied)
    assert _working["days"]["Tuesday"]["subjects"]["math"]["raw"] == "Test 8"

    inactive = json.loads(json.dumps(decisions))
    inactive[0]["active"] = False
    _working, applied = od.apply_translation_working_copy(week, inactive)
    assert applied == []
    assert _working["days"]["Tuesday"]["subjects"]["math"]["raw"] == "Test 8"

    other_week = json.loads(json.dumps(decisions))
    other_week[0]["week"] = "Q2W4"
    _working, applied = od.apply_translation_working_copy(week, other_week)
    assert applied[0]["applied"] is False


def test_owner_time_propagates_and_invalid_times_stay_blocked():
    from scripts.canvas_llm_deploy.plan import _reminder_plan_entry, build_plan
    from scripts.canvas_llm_deploy import ledger as deploy_ledger
    from scripts.canvas_llm_deploy import preflight as preflight_mod
    from scripts.canvas_llm_deploy.coordinator import _plan_prewrite_blockers
    from scripts.canvas_llm_rollover import manifest as rollover_manifest

    week = _week()
    working, _applied = od.apply_translation_working_copy(week, _decisions())
    notices = aa.draft_two_notice_announcements(
        working, source_hash="src", decisions=_decisions(), now=NOW,
    )
    past = next(item for item in notices if item["notice_type"] == "FIRST_NOTICE" and item["family"] == "math_assessment")
    future = next(item for item in notices if item["schedule_state"] == "FUTURE_SCHEDULED")
    assert past["delayed_post_at"] is None
    policy_delay = future["delayed_post_at"]
    selected = "2026-11-12T21:00:00Z"
    timed = aa.draft_two_notice_announcements(
        working, source_hash="src", decisions=_decisions(), now=NOW,
        notice_times={past["duplicate_identity"]: selected},
    )
    updated = next(item for item in timed if item["duplicate_identity"] == past["duplicate_identity"])
    assert updated["schedule_state"] == "FUTURE_SCHEDULED"
    assert updated["delayed_post_at"] == selected
    still_future = next(item for item in timed if item["duplicate_identity"] == future["duplicate_identity"])
    assert still_future["delayed_post_at"] == policy_delay
    wrong = aa.draft_two_notice_announcements(
        working, source_hash="src", decisions=_decisions(), now=NOW,
        notice_times={"ann-does-not-exist": selected, past["duplicate_identity"]: "2026-11-07T21:00:00Z"},
    )
    blocked = next(item for item in wrong if item["duplicate_identity"] == past["duplicate_identity"])
    assert blocked["schedule_state"] == "BLOCKED"
    assert blocked["delayed_post_at"] is None

    entry = _reminder_plan_entry(
        past, label="Math", subject="math", week_code="Q2W5", date_range={},
        now=NOW, notice_times={past["duplicate_identity"]: selected},
    )
    assert entry["action"] == "CREATE" and entry["delayed_post_at"] == selected and entry["scheduled"] is True
    missing = _reminder_plan_entry(
        {"title": "Legacy reminder", "course_id": 26442, "assessment_date": "2026-11-10", "body": "x",
         "duplicate_identity": "legacy", "content_status": "READY"},
        label="Reading/Spelling", subject="reading_spelling", week_code="Q2W5", date_range={}, now=NOW,
    )
    assert missing["action"] == "BLOCKED" and missing["delayed_post_at"] is None
    assert _plan_prewrite_blockers({"assessment_reminders": [missing], "weekly_announcements": [], "assignments": [], "pages": []})

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        original = intake_manifest.staging_dir
        original_deploy = deploy_ledger.DEPLOY_ROOT
        intake_manifest.staging_dir = lambda quarter, week_number: root / f"q{quarter}w{week_number}"
        deploy_ledger.DEPLOY_ROOT = root / "deployments"
        try:
            summary = intake_mod.build_intake(
                quarter=2, week=5, normalized_override=week, decisions_override=_decisions(),
                now=NOW, notice_times={past["duplicate_identity"]: selected},
                owner_publication_time="2026-11-08T21:00:00Z",
                page_lookup_override={"math": {"page_id": 798076, "course_id": 26404, "status": "FOUND"}},
                assignment_classifications={},
            )
            from scripts.canvas_llm_intake import approval as ap
            ap.approve_artifact(
                2, 5, "math", "assessment_reminder",
                draft_hash=summary["draft_hashes"]["math"]["assessment_reminder"],
                source_hash=summary["source_hash"], subjects=summary["active_subjects"],
            )
            ap.approve_artifact(
                2, 5, "math", "announcement",
                draft_hash=summary["draft_hashes"]["math"]["announcement"],
                source_hash=summary["source_hash"], subjects=summary["active_subjects"],
            )
            staged = root / "q2w5"
            (staged / "planner").mkdir(parents=True, exist_ok=True)
            (staged / "planner" / "owner-publication-times.json").write_text(json.dumps({
                "release": "2026-11-08T21:00:00Z",
                "notices": {past["duplicate_identity"]: selected},
            }), encoding="utf-8")
            plan = build_plan(2, 5, now=NOW)
            math_notice = next(item for item in plan["assessment_reminders"] if item.get("duplicate_identity") == past["duplicate_identity"])
            assert math_notice["delayed_post_at"] == selected
            assert plan["owner_publication_time"] == "2026-11-08T21:00:00Z"
            record = preflight_mod.run_preflight(2, 5, client=None)
            assert record["plan"]["owner_publication_time"] == "2026-11-08T21:00:00Z"
            rolled = rollover_manifest.build_rollover_manifest(2, 4, 2, 5, now=NOW)
            assert rolled["owner_publication_time"] == "2026-11-08T21:00:00Z"
            assert any(item.get("delayed_post_at") == "2026-11-08T21:00:00Z" for item in rolled["weekly_announcements"])
            again = build_plan(2, 5, now=NOW)
            assert again["plan_fingerprint"] == plan["plan_fingerprint"]
        finally:
            intake_manifest.staging_dir = original
            deploy_ledger.DEPLOY_ROOT = original_deploy


def test_blocked_direct_execution_performs_zero_canvas_writes():
    from scripts.canvas_llm_deploy.client import FakeDeployClient
    from scripts.canvas_llm_rollover import rollover

    def _run(manifest):
        client = FakeDeployClient(courses={
            26404: {"id": 26404, "name": "Math"},
            26429: {"id": 26429, "name": "Homeroom"},
            28171: {"id": 28171, "name": "Language Arts"},
        })
        client.seed_page(26404, "q2w5", title="Q2W5", body="<div id='kl_wrapper_3'>x</div>", front_page=False)
        try:
            result = rollover.execute(
                2, 4, 2, 5, client=client, owner_confirmation="ROLLOVER Q2W5", manifest=manifest,
                now=NOW,
            )
        except rollover.RolloverBlocked:
            result = {"lifecycle": "BLOCKED"}
        assert client._write_counts["PUT"] == 0, result
        assert client._write_counts["POST"] == 0, result
        assert result["lifecycle"] == "BLOCKED"

    base = {
        "from_week": "Q2W4", "to_week": "Q2W5", "scheduled_at": "2026-11-08T21:00:00Z",
        "timezone": "America/New_York", "academic_courses": [{
            "subject": "math", "course_id": 26404, "label": "Math", "approved": True,
            "to_page_slug": "q2w5", "page_body": "<div id='kl_wrapper_3'>x</div><p>Reminders</p>",
            "to_page_hash": "unused",
        }], "homeroom": {"approved": True, "to_page_id": 798096, "course_id": 26429, "to_page_slug": "q2w5"},
        "weekly_announcements": [], "assignments": [], "assessment_reminders": [],
    }
    cases = [
        {**base, "assessment_reminders": [{"title": "Math", "course_id": 26404, "schedule_state": "OWNER_TIME_REQUIRED", "message": "x"}]},
        {**base, "homeroom_announcement": {"title": "News", "course_id": 26429, "page_id": 798096, "schedule_state": "OWNER_TIME_REQUIRED", "approval_state": "PENDING", "publication_dependency": "HOMEROOM_PAGE_PUBLISHED_AND_VERIFIED", "message": "x"}},
        {**base, "weekly_announcements": [{"title": "Math Canvas Weekly Update", "course_id": 26404, "schedule_state": "BLOCKED", "message": "x"}]},
        {**base, "assignments": [{"title": "SM5", "course_id": None, "action": "BLOCKED"}]},
        {**base, "academic_courses": [{**base["academic_courses"][0], "approved": False}]},
        {**base, "publication_time_required": True, "owner_publication_time": None},
        {**base, "assessment_reminders": [{"title": "Dup", "course_id": 26404, "duplicate_status": "AMBIGUOUS", "message": "x", "content_status": "READY"}]},
        {**base, "assessment_reminders": [{"title": "Resource", "course_id": 26404, "content_status": "PARTIAL", "message": "x"}]},
        {**base, "homeroom_announcement": {"title": "News", "course_id": 26429, "page_id": 1, "schedule_state": "FUTURE_SCHEDULED", "delayed_post_at": "2026-11-08T21:00:00Z", "approval_state": "APPROVED", "publication_dependency": "MISSING", "message": "<p>x</p>"}},
    ]
    for manifest in cases:
        _run(manifest)


def test_coordinator_readback_rejects_wrong_announcement_and_accepts_scheduled():
    from scripts.canvas_llm_deploy.client import DeployClientError, FakeDeployClient
    from scripts.canvas_llm_deploy import coordinator, ledger
    from scripts.canvas_llm_deploy.plan import plan_fingerprint

    message = "<p>Chapter 7 on Friday.</p>"
    delayed = "2026-11-11T21:00:00Z"
    client = FakeDeployClient(courses={28171: {"id": 28171, "name": "Language Arts", "workflow_state": "available"}})
    created = client.create_announcement(
        28171, title="Reminder — Shurley English Chapter 7 Test", message=message,
        published=True, delayed_post_at=delayed,
    )
    ok, detail, state = coordinator._verify_announcement(
        client, 28171, created["id"], title=created["title"], scheduled=True,
        delayed_post_at="2026-11-11T16:00:00-05:00", expect_agenda=False, counts={},
        expected_message=message,
    )
    assert ok and state == "HELD_SCHEDULED", detail
    assert coordinator.announcement_readback_disposition(scheduled=True, verified=True, state=state) == "SCHEDULED_VERIFIED"
    bad_course = FakeDeployClient(courses={28171: {"id": 28171}})
    other = bad_course.create_announcement(28171, title="T", message=message, delayed_post_at=delayed)
    stored = bad_course.announcements[other["id"]]
    stored["course_id"] = 26404
    try:
        coordinator._verify_announcement(
            bad_course, 28171, other["id"], title="T", scheduled=True, delayed_post_at=delayed,
            expect_agenda=False, counts={}, expected_message=message,
        )
        raise AssertionError("wrong course must not verify")
    except DeployClientError:
        pass
    stored["course_id"] = None
    try:
        coordinator._verify_announcement(
            bad_course, 28171, other["id"], title="T", scheduled=True, delayed_post_at=delayed,
            expect_agenda=False, counts={}, expected_message=message,
        )
        raise AssertionError("missing course id must not verify")
    except DeployClientError:
        pass
    stored["course_id"] = 28171
    ok, _detail, _state = coordinator._verify_announcement(
        bad_course, 28171, other["id"], title="Other", scheduled=True, delayed_post_at=delayed,
        expect_agenda=False, counts={}, expected_message=message,
    )
    assert ok is False
    ok, _detail, _state = coordinator._verify_announcement(
        bad_course, 28171, other["id"], title="T", scheduled=True, delayed_post_at=delayed,
        expect_agenda=False, counts={}, expected_message="different",
    )
    assert ok is False
    ok, _detail, _state = coordinator._verify_announcement(
        bad_course, 28171, other["id"], title="T", scheduled=True, delayed_post_at=None,
        expect_agenda=False, counts={}, expected_message=message,
    )
    assert ok is False
    ok, _detail, _state = coordinator._verify_announcement(
        bad_course, 28171, other["id"], title="T", scheduled=True, delayed_post_at="2026-11-12T21:00:00Z",
        expect_agenda=False, counts={}, expected_message=message,
    )
    assert ok is False

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        original_deploy = ledger.DEPLOY_ROOT
        original_staging = intake_manifest.staging_dir
        ledger.DEPLOY_ROOT = root / "deployments"
        intake_manifest.staging_dir = lambda q, w: root / f"q{q}w{w}"
        try:
            plan = {
                "quarter": 2, "week": 5, "week_code": "Q2W5", "slug": "q2w5",
                "date_range": {"start": "2026-11-09", "end": "2026-11-13"},
                "status": "READY_TO_PUBLISH", "ready_to_publish": True, "publish_blockers": [],
                "source_hash": "src", "approval_snapshot_hash": "appr",
                "pages": [], "assignments": [], "deletes": [], "untouched": {},
                "weekly_announcements": [],
                "assessment_reminders": [{
                    "title": "Reminder — Shurley English Chapter 7 Test", "course_id": 28171,
                    "message": message, "scheduled": True, "delayed_post_at": delayed,
                    "schedule_state": "FUTURE_SCHEDULED", "action": "CREATE", "content_status": "READY",
                }],
                "counts": {},
            }
            plan["plan_fingerprint"] = plan_fingerprint(plan)
            blocked = dict(plan)
            blocked["assessment_reminders"] = [dict(plan["assessment_reminders"][0], action="BLOCKED", schedule_state="OWNER_TIME_REQUIRED", scheduled=False, delayed_post_at=None)]
            ledger.write_preflight(2, 5, {
                "preflight_id": "pf", "created_at": "2026-11-07T00:00:00+00:00",
                "expires_at": "2099-01-01T00:00:00+00:00", "quarter": 2, "week": 5,
                "week_code": "Q2W5", "source_hash": "src", "approval_snapshot_hash": "appr",
                "plan": blocked, "live": {}, "warnings": [], "blockers": [], "ready": True,
                "canvas_writes": 0,
            })
            from scripts.canvas_llm_intake import manifest as mf
            record = mf.new_manifest(quarter=2, week=5, week_code="Q2W5", date_range=plan["date_range"])
            record["status"] = "READY_TO_PUBLISH"
            record["source_hash"] = "src"
            mf.save_manifest(2, 5, record)
            deploy_client = FakeDeployClient(courses={28171: {"id": 28171, "name": "Language Arts", "workflow_state": "available"}})
            from scripts.canvas_llm_deploy import plan as plan_mod
            original_build = plan_mod.build_plan
            plan_mod.build_plan = lambda *args, **kwargs: blocked
            try:
                result = coordinator.deploy(
                    2, 5, preflight_id="pf", expected_source_hash="src",
                    expected_approval_snapshot_hash="appr", owner_confirmation="DEPLOY Q2W5",
                    client=deploy_client,
                )
            finally:
                plan_mod.build_plan = original_build
            assert result["deployment_state"] == "BLOCKED"
            assert deploy_client._write_counts["POST"] == 0
            assert deploy_client._write_counts["PUT"] == 0
        finally:
            ledger.DEPLOY_ROOT = original_deploy
            intake_manifest.staging_dir = original_staging


def test_newsletter_renders_one_birthday_section_and_current_movie_night():
    from scripts.canvas_llm_rollover import homeroom_newsletter as hn
    source = (
        '<div><span>Track 2, Week 4 · November 2–6, 2026</span>'
        '<p style="font-size: 16px; margin: 10px 0 0;">We are looking forward to a great week.</p>'
        '<div><h2>📅 Important Dates</h2><div></div></div>'
        f'{hn.BIRTHDAY_SECTION_START}<div style="margin-bottom: 22px;"><h2>🍂 November Birthdays 🎉</h2><div>One</div></div>{hn.BIRTHDAY_SECTION_END}'
        '<div style="margin-bottom: 22px;"><h2>🍂 November Birthdays 🎉</h2><div>Duplicate</div></div>'
        '<div style="flex: 1 1 250px; background: #FBEFEF;"><div style="font-size: 28px;">🎬</div>'
        '<h3>Family Movie Night — November 6</h3><p>6:00–8:00 PM</p></div>'
        '<div><h2>⭐ Behavior Tracker</h2><p>Keep this evergreen section.</p></div></div>'
    )
    plan = hn.load_plan()
    plan = json.loads(json.dumps(plan))
    plan["week"] = {
        "code": "Q2W5", "startDate": "2026-11-09", "endDate": "2026-11-13",
        "badge": "Track 2, Week 5 · November 9–13, 2026",
        "intro": "We are looking forward to the Veterans Day Concert and Movie Night.",
    }
    plan["importantDates"] = [
        {"date_label": "FRIDAY, NOVEMBER 13", "event": "Movie Night (Rescheduled)", "time": "6:00–8:00 PM", "highlight": True},
        {"date_label": "WEDNESDAY, NOVEMBER 11", "event": "Veterans Day Concert — JH/HS Vikings Gym", "time": "9:00 AM", "highlight": True},
    ]
    plan["removeSections"] = []
    plan["replacements"] = {}
    from scripts.canvas_llm_rollover import birthdays as bday
    rendered = hn.build_from_plan(source, plan, roster=[bday.Birthday("Example Student", 11, 20)])
    assert rendered.count("November Birthdays") == 1
    assert "Family Movie Night — November 6" not in rendered
    assert "Movie Night (Rescheduled)" in rendered
    assert "FRIDAY, NOVEMBER 13" in rendered
    assert "Veterans Day Concert — JH/HS Vikings Gym" in rendered
    assert "9:00 AM" in rendered
    assert "Behavior Tracker" in rendered
    assert rendered.count(hn.BIRTHDAY_SECTION_START) == 1


def _run():
    failed = 0
    tests = [(name, fn) for name, fn in sorted(globals().items()) if name.startswith("test_") and callable(fn)]
    for name, fn in tests:
        try:
            fn()
            print(f"PASS {name}")
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"FAIL {name}: {exc}")
    print(f"RESULT: {len(tests) - failed} passed, {failed} failed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    _run()
