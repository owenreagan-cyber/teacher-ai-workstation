"""Q2W4 final content-readiness acceptance tests (deterministic, local-only).

Two layers:

* synthetic unit fixtures for the reusable rules (bare Math lessons, Reading
  classwork/homework/test days, Shurley ``7.4 CP 27``, repeated CP27, Science
  owner override, assessment-announcement duplication, missing birthday source,
  missed Friday release timestamp, next instructional week after a break);
* the ACTUAL staged Q2W4 package under ``.local/canvas-llm/intake/.../q2/w4``.

The local layer never prints student data. It is required when
``TAW_REQUIRE_Q2W4_STAGING=1`` and otherwise reports SKIP.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.canvas_llm_intake import assessment_announcements as aa
from scripts.canvas_llm_intake import intake as intake_mod
from scripts.canvas_llm_intake import owner_decisions as od
from scripts.canvas_llm_intake import policies as pol
from scripts.canvas_llm_intake import reminders as rem
from scripts.canvas_llm_phase3 import pacing_math as pm
from scripts.canvas_llm_phase3 import pacing_reading as prd
from scripts.canvas_llm_phase3 import pacing_translation as pt
from scripts.canvas_llm_rollover import homeroom_newsletter as hn
from scripts.canvas_llm_rollover import release_plan, schedule

Q2W4_DIR = Path(".local/canvas-llm/intake/2026-2027/q2/w4")
SHA = lambda text: hashlib.sha256(text.encode("utf-8")).hexdigest()


def _read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- #
# Synthetic reusable-rule fixtures
# --------------------------------------------------------------------------- #


def test_bare_math_lessons_41_45():
    for n in range(41, 46):
        parsed = pm.parse_math_tokens(str(n))
        assert parsed["tokens"][0]["kind"] == "lesson", parsed
        assert parsed["tokens"][0]["translation"] == f"Lesson {n}", parsed


def test_reading_classwork_homework_and_test_days():
    classwork = prd.reading_day_plan("L50", "Monday", "2026-11-02", prd.load_config())
    assert classwork["in_class"] == ["Lesson 50", "Workbook"]
    assert classwork["at_home"] and "front and back" in classwork["at_home"][0]

    homework = prd.reading_day_plan("L52", "Thursday", "2026-11-05", prd.load_config())
    assert any("Reading Workbook" in item for item in homework["at_home"])
    assert any("comprehension questions" in item for item in homework["at_home"])

    test_day = prd.reading_day_plan("RMT+FCO", "Tuesday", "2026-11-03", prd.load_config())
    assert test_day["at_home"] is None

    friday = prd.reading_day_plan("L53", "Friday", "2026-11-06", prd.load_config())
    assert friday["at_home"] is None


def test_shurley_74_cp27_and_repeated_cp27():
    cell = pt.translate_shurley_cell("7.4 CP 27")
    assert cell["lines"] == ["Chapter 7, Lesson 4", "Classroom Practice 27"], cell

    week = {
        "week": {"code": "Q2W4", "startDate": "2026-11-02", "endDate": "2026-11-06"},
        "days": {
            "Monday": {"date": "2026-11-02", "subjects": {"language_arts": {"raw": "Ch 7 L2 + CP26"}}},
            "Tuesday": {"date": "2026-11-03", "subjects": {"language_arts": {"raw": "Ch.7 L3 CP27"}}},
            "Wednesday": {"date": "2026-11-04", "subjects": {"language_arts": {"raw": "Ch.7 L3 CP27"}}},
            "Thursday": {"date": "2026-11-05", "subjects": {"language_arts": {"raw": "7.4"}}},
            "Friday": {"date": "2026-11-06", "subjects": {"language_arts": {"raw": "7.4 CP 27"}}},
        },
    }
    report = pt.translate_subject_week(week, "language_arts")
    cp27 = [a for a in report["assignments"] if a["title"] == "Classroom Practice 27"]
    assert len(cp27) == 1, cp27
    assert cp27[0]["due_date"] == "2026-11-04"
    assert all(day.get("at_home") is None for day in report["days"].values())


def _q2w4_synthetic_week():
    return {
        "week": {"code": "Q2W4", "startDate": "2026-11-02", "endDate": "2026-11-06"},
        "unitContext": {"science": None},
        "days": {
            "Monday": {"date": "2026-11-02", "subjects": {"reading": {"raw": "L50"}, "spelling": {"raw": "46"}, "science": {"raw": "F&M Ch. 7"}}},
            "Tuesday": {"date": "2026-11-03", "subjects": {"reading": {"raw": "RMT 5+ CO 5"}, "spelling": {"raw": "47"}, "science": {"raw": "F&M Ch. 7"}}},
            "Wednesday": {"date": "2026-11-04", "subjects": {"reading": {"raw": "L51"}, "spelling": {"raw": "48"}, "science": {"raw": "Review"}}},
            "Thursday": {"date": "2026-11-05", "subjects": {"reading": {"raw": "L52"}, "spelling": {"raw": "49"}, "science": {"raw": "Test"}}},
            "Friday": {"date": "2026-11-06", "subjects": {"reading": {"raw": "L53"}, "spelling": {"raw": "test 50"}, "science": {"raw": "U2 Ch1 Renewable / Nonrenewable"}}},
        },
    }


def _science_override():
    return {
        "decision_id": "assessment_override|science|Thursday|2026-11-05",
        "kind": "assessment_override",
        "subject": "science",
        "day": "Thursday",
        "date": "2026-11-05",
        "source_value": "Test",
        "owner_value": "Energy Transformations Unit Test",
        "reason": "explicit Owen instruction",
        "acknowledgement": "canonical unit config may be stale",
        "open_book": True,
        "open_notes": True,
        "active": True,
    }


def test_science_owner_override_and_single_assignment():
    week = _q2w4_synthetic_week()
    override = _science_override()
    proposal = aa.science_assignment_proposal(week, override)
    assert proposal and proposal["title"] == "Science: Energy Transformations Unit Test"
    assert proposal["assignment_group"] == "Assignments"
    assert proposal["due_date"] == "2026-11-05"
    assert proposal["omit_from_final_grade"] is False
    assert "Open Book / Open Notes" in proposal["description"]
    # No override -> no speculative Science assignment.
    assert aa.science_assignment_proposal(week, None) is None


def test_four_assessment_announcements_no_duplicates():
    items = aa.draft_assessment_announcements(
        _q2w4_synthetic_week(), source_hash="src", decisions=[_science_override()],
    )
    assert len(items) == 4, [i["title"] for i in items]
    assert len({i["title"] for i in items}) == 4
    assert len({i["duplicate_identity"] for i in items}) == 4
    assert all(i["preview_only"] and i["approval_state"] == "PENDING" for i in items)

    mastery = next(i for i in items if i["type"] == "reading_mastery_test")
    assert "Cat That Walked" not in mastery["body"]
    assert "Reading Workbook pages" in mastery["body"]
    assert "reread the stories" in mastery["body"]
    assert mastery["content_status"] == "READY"
    assert mastery["blocked_sections"] == []

    fluency = next(i for i in items if i["type"] == "fluency_checkout")
    assert "100 words" in fluency["body"] and "2 errors" in fluency["body"]
    assert "page 17" not in fluency["body"].lower()

    spelling = next(i for i in items if i["type"] == "spelling_test")
    assert "through Lesson 50" in spelling["body"]
    assert "current spelling list" not in spelling["body"]

    science = next(i for i in items if i["type"] == "science_unit_test")
    assert science["provenance"]["source_value"] == "Test"
    assert science["provenance"]["owner_value"] == "Energy Transformations Unit Test"


def test_birthday_authorization_and_private_source():
    from scripts.canvas_llm_rollover import birthdays as bday

    plan = hn.load_plan()
    birthdays = plan["monthlyBirthdays"]
    assert birthdays["status"] == "OWNER_APPROVED_PRIVATE_ROSTER"
    assert birthdays["entries"] == []
    auth = bday.load_authorization()
    assert auth["status"] == "OWNER_APPROVED"
    assert auth["classLabel"] == "4-A"
    roster = bday.load_roster()
    assert len(roster) == 21
    assert len(bday.birthdays_in_month(11, roster=roster)) == 1
    assert len(bday.roster_version(roster)) == 64
    # Private roster is gitignored; no values are committed.
    import subprocess
    result = subprocess.run(
        ["git", "check-ignore", auth["privateRosterPath"]],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    assert plan["monthlyBirthdays"]["entries"] == []


def test_missed_friday_release_timestamp_requires_owner_time():
    plan = release_plan.build_release_plan(
        2, 3, 2, 4, now=datetime(2026, 10, 30, 21, 0, tzinfo=timezone.utc),
    )
    assert plan["publication_time_required"] is True
    assert plan["scheduled_at"] is None
    assert plan["canonical_scheduled_at"] == "2026-10-30T20:00:00Z"
    assert plan["canvas_writes"] == 0 and plan["email_sends"] == 0


def test_next_instructional_week_after_break():
    from scripts.canvas_llm_intake import week_resolution as wr

    assert wr.next_week(today=date(2026, 11, 20)) == (2, 7)  # skip Thanksgiving
    assert wr.next_week(today=date(2026, 12, 18)) == (3, 1)  # skip winter track-out
    q2w7 = schedule.instructional_rollover_meta("2026-11-30")
    assert q2w7["rollover_day"] == "2026-11-20", q2w7
    assert q2w7["scheduled_at"] == "2026-11-20T21:00:00Z", q2w7


# --------------------------------------------------------------------------- #
# Actual staged Q2W4 package
# --------------------------------------------------------------------------- #


def _require_staging():
    if not Q2W4_DIR.exists():
        if os.environ.get("TAW_REQUIRE_Q2W4_STAGING") == "1":
            raise AssertionError(f"required Q2W4 staging missing: {Q2W4_DIR}")
        print("SKIP actual Q2W4 staging not present")
        return False
    return True


def test_actual_source_snapshot_unchanged():
    if not _require_staging():
        return
    source = _read(Q2W4_DIR / "source" / "pacing-snapshot.json")
    normalized = _read(Q2W4_DIR / "normalized" / "week.json")
    assert source["hash"] == "04bf0411b6656c13767b72279b6dbccff9979c9025c8318bff376e51df2bd57d"
    # Original source cells are preserved verbatim (owner override is separate).
    assert normalized["days"]["Thursday"]["subjects"]["science"]["raw"] == "Test"
    assert (Q2W4_DIR / "owner-decisions.json").exists()


def test_actual_assignments_universal_settings():
    if not _require_staging():
        return
    assignments = _read(Q2W4_DIR / "drafts" / "assignments.json")
    assert len(assignments) == 11, [a["title"] for a in assignments]
    for a in assignments:
        assert a["points_possible"] == 100, a
        assert a["grading_type"] == "percent", a
        assert a["submission_types"] == "on_paper", a
        assert a["omit_from_final_grade"] is False, a
        assert a["assignment_group"], a
        assert a["due_date"], a
        assert a["due_time"] == "11:59 PM"
        assert a["timezone"] == "America/New_York"

    cp27 = [a for a in assignments if a["title"] == "Classroom Practice 27"]
    assert len(cp27) == 1 and cp27[0]["due_date"] == "2026-11-04", cp27
    cp26 = [a for a in assignments if a["title"] == "Classroom Practice 26"]
    assert len(cp26) == 1 and cp26[0]["due_date"] == "2026-11-02", cp26
    la_cfg = json.loads((ROOT / "config/curriculum/canvas/pacing-translation-rules-2026-2027.json").read_text())
    cp_meta = la_cfg["subjects"]["language_arts"]["classroomPractice"]["assignment"]
    assert cp_meta["deduplication"]
    assert cp_meta["dueDatePolicy"]["multiDayPreferredWeekday"] == "Wednesday"
    assert "dueDate" not in la_cfg["subjects"]["language_arts"]["assignmentPolicy"]["chapterTest"]
    assert "deduplication" not in la_cfg["subjects"]["language_arts"]["assignmentPolicy"]["chapterTest"]

    science = [a for a in assignments if a["course"] == "science"]
    assert len(science) == 1, science
    assert science[0]["title"] == "Science: Energy Transformations Unit Test"
    assert science[0]["assignment_group"] == "Assignments"
    assert science[0]["due_date"] == "2026-11-05"
    assert "Open Book / Open Notes" in science[0]["description"]
    assert not any("Force and Motion" in a["title"] for a in science)


def test_actual_agenda_reminders_and_hash_consistency():
    if not _require_staging():
        return
    pages = {
        "Math": "math-page.html",
        "Reading/Spelling": "reading-page.html",
        "Language Arts": "language_arts-page.html",
        "Science": "science-page.html",
    }
    announcements = {a["course"]: a for a in _read(Q2W4_DIR / "drafts" / "announcements.json")}
    assert len(announcements) == 4
    for label, filename in pages.items():
        html = (Q2W4_DIR / "drafts" / filename).read_text(encoding="utf-8")
        digest = SHA(html)
        ann = announcements[label]
        assert ann["agenda_hash"] == digest, (label, ann["agenda_hash"], digest)
        assert ann["page_agenda_hash"] == digest, (label, ann["page_agenda_hash"], digest)
        assert ann["hash_consistent"] is True
        assert ann["message_hash"]
        # The full exact agenda HTML is embedded, not a URL or summary.
        from scripts.canvas_llm_deploy.plan import compose_announcement_body
        body = compose_announcement_body(ann, html)
        assert html in body, label
        assert ann["message_hash"] == SHA(body), label
        assert body.startswith("<p>Good afternoon,</p>"), label
        assert "Mr. Reagan" in body, label
        assert "October" not in body, label

    assert "This week we will continue working through Lessons 41\u201345." in (
        Q2W4_DIR / "drafts" / "math-page.html").read_text(encoding="utf-8")
    assert "This week we will continue working in Chapter 7." in (
        Q2W4_DIR / "drafts" / "language_arts-page.html").read_text(encoding="utf-8")
    science_html = (Q2W4_DIR / "drafts" / "science-page.html").read_text(encoding="utf-8")
    assert "Energy Transformations Unit Test \u2014 Thursday, November 5" in science_html
    assert "Open Book / Open Notes." in science_html


def test_actual_four_assessment_announcements():
    if not _require_staging():
        return
    items = _read(Q2W4_DIR / "drafts" / "assessment-reminders.json")
    assert len(items) == 4, [i["title"] for i in items]
    titles = " | ".join(i["title"] for i in items)
    for needed in ("Reading Mastery Test 5", "Fluency Checkout 5", "Spelling Test 50",
                   "Science: Energy Transformations Unit Test"):
        assert needed in titles, titles
    assert len({i["duplicate_identity"] for i in items}) == 4
    assert len({i["draft_hash"] for i in items}) == 4
    for i in items:
        assert i["requires_teacher_approval"] is True
        assert i["approval_state"] == "PENDING"
        assert i["preview_only"] is True
        assert i["course_id"] in (26442, 28166)
        assert i["assessment_date"]
        assert "October" not in i["body"], i["title"]

    spelling = next(i for i in items if i["type"] == "spelling_test")
    assert "through Lesson 50" in spelling["body"]
    assert "current spelling list" not in spelling["body"]

    science = next(i for i in items if i["type"] == "science_unit_test")
    assert science["provenance"]["source_value"] == "Test"
    assert science["provenance"]["owner_value"] == "Energy Transformations Unit Test"

    mastery = next(i for i in items if i["type"] == "reading_mastery_test")
    assert "Cat That Walked" not in mastery["body"]
    assert "Reading Workbook pages" in mastery["body"]
    assert mastery["content_status"] == "READY"
    assert mastery["blocked_sections"] == []


def test_actual_homeroom_newsletter_and_drafts():
    if not _require_staging():
        return
    html = (Q2W4_DIR / "drafts" / "homeroom-page.html").read_text(encoding="utf-8")
    assert "Track 2, Week 4 \u00b7 November 2\u20136, 2026" in html
    assert "Progress Reports" in html and "Veterans Day Performance" in html
    assert "FRIDAY, NOVEMBER 6" in html and "WEDNESDAY, NOVEMBER 11" in html
    assert "Friday, November 6" in html
    assert "Thursday, November 6" not in html
    for stale in ("October", "Book Character Day", "Picture Retakes", "Track 2, Week 3"):
        assert stale not in html, stale
    assert hn.BIRTHDAY_SECTION_START in html
    assert "November Birthdays" in html
    assert hn.BIRTHDAY_SHOUTOUT_START not in html  # Nov 20 is later in the month
    from scripts.canvas_llm_rollover import birthdays as bday
    roster = bday.load_roster()
    november = bday.birthdays_in_month(11, roster=roster)
    assert len(november) == 1
    assert november[0].name in html  # actual value checked at runtime, never printed

    for name in ("homeroom-announcement.json", "homeroom-email-draft.json", "homeroom-message-draft.json"):
        draft = _read(Q2W4_DIR / "drafts" / name)
        assert draft["send_status"] == "NOT_SENT", draft
        assert draft["approval_state"] == "PENDING", draft
        assert draft["preview_only"] is True, draft
    email = _read(Q2W4_DIR / "drafts" / "homeroom-email-draft.json")
    assert email["to"] is None and email["recipient_status"] == "OWNER_MUST_SUPPLY_RECIPIENT"
    message = _read(Q2W4_DIR / "drafts" / "homeroom-message-draft.json")
    assert message["recipients"] == [] and message["recipient_status"] == "OWNER_MUST_SUPPLY_RECIPIENTS"

    report = _read(Q2W4_DIR / "planner" / "homeroom-monthly-report.json")
    assert report["birthdays"]["status"] == "OWNER_APPROVED_PRIVATE_ROSTER"
    assert report["birthdays"]["entries_committed"] is False
    assert report["birthdays"]["november_count"] == 1
    assert report["canvas_writes"] == 0 and report["email_sends"] == 0
    assert report["architecture"] == "weekly_homeroom_page"
    assert report["page_resolution"]["method"] == "LIVE_GET"
    assert report["page_resolution"]["course_id"] == 26429
    assert report["page_resolution"]["page_id"] == 798094
    assert report["page_resolution"]["front_page"] is False
    assert report["weekly_approval"]["status"] == "PENDING_OWNER_APPROVAL"
    assert report["weekly_approval"]["approved"] is False
    assert report["q2w5_page_resolution"]["page_id"] == 798096
    assert report["q2w5_page_resolution"]["status"] == "FOUND"
    assert report["q2w5_page_resolution"]["content_status"] == "PENDING_WEEK_CONTENT"
    assert report["birthday_candidates"]["status"] == "SUPERSEDED_BY_OWNER_APPROVED_ROSTER"
    committed_plan = _read(ROOT / "config/curriculum/canvas/homeroom-newsletter-november-2026-plan.json")
    assert committed_plan["monthlyBirthdays"]["entries"] == []


def test_actual_homeroom_newsletter_structure_and_privacy():
    if not _require_staging():
        return
    html = (Q2W4_DIR / "drafts" / "homeroom-page.html").read_text(encoding="utf-8")
    # Theme/layout invariants: balanced divs, canonical wrapper, required sections.
    assert html.count("<div") == html.count("</div>"), (
        html.count("<div"), html.count("</div>"))
    assert "4th Grade Happenings" in html
    for section in ("Important Dates", "Behavior Tracker", "Carpool Reminders",
                    "Family Quick Links", "Questions? Start with Mr. Reagan",
                    "A Note from Mr. Reagan"):
        assert section in html, section
    # Privacy: authorized birthday section is present, but no roster values were
    # copied into the committed plan and no weekly shoutout exists for Q2W4.
    assert hn.BIRTHDAY_SECTION_START in html
    assert hn.BIRTHDAY_SHOUTOUT_START not in html
    assert "November Birthdays" in html
    report = _read(Q2W4_DIR / "planner" / "homeroom-monthly-report.json")
    assert report["birthdays"]["status"] == "OWNER_APPROVED_PRIVATE_ROSTER"
    assert report["birthdays"]["entries_committed"] is False
    assert report["birthdays"]["roster_version"]
    # No credentials/tokens are present.
    for secret in ("password", "access_token", "refresh_token", "client_secret"):
        assert secret not in html.lower(), secret


def test_actual_release_plan_five_targets_and_no_writes():
    if not _require_staging():
        return
    plan = _read(Q2W4_DIR / "planner" / "rollover-release-plan.json")
    assert len(plan["front_page_targets"]) == 5, plan["front_page_targets"]
    assert {t["subject"] for t in plan["front_page_targets"]} == {
        "math", "reading_spelling", "language_arts", "science", "homeroom"
    }
    assert all(t["course_id"] for t in plan["front_page_targets"])
    assert all(t["page_id"] for t in plan["front_page_targets"])
    homeroom = next(t for t in plan["front_page_targets"] if t["subject"] == "homeroom")
    assert homeroom["page_id"] == 798094
    assert homeroom["page_slug"] == "q2w4-november-2-6-2026"
    assert homeroom["page_resolution_method"] == "LIVE_GET"
    assert plan["publication_time_required"] is True
    assert plan["scheduled_at"] is None
    assert plan["status"] == "OWNER_PUBLICATION_TIME_REQUIRED"
    assert plan["canvas_writes"] == 0 and plan["email_sends"] == 0
    assert plan["content_warnings"] == [], plan["content_warnings"]
    recon = plan["assignment_reconciliation"]
    assert recon["bundle_status"] == "READY_FOR_APPROVAL", recon
    assert recon["counts"]["UPDATE_REQUIRED"] == 2, recon
    assert recon["counts"]["CREATE_REQUIRED"] == 9, recon
    assert recon["counts"]["DUPLICATE"] == 0 and recon["counts"]["UNVERIFIED"] == 0, recon
    assert recon["execution_ready"] is False, recon
    assert any("Classroom Practice 26" in item for item in recon["pending_actions"])
    assert any("Classroom Practice 27" in item for item in recon["pending_actions"])


def test_actual_no_study_guide_references_anywhere():
    if not _require_staging():
        return
    texts = {}
    for filename in ("math-page.html", "reading-page.html",
                     "language_arts-page.html", "science-page.html",
                     "homeroom-page.html"):
        texts[filename] = (Q2W4_DIR / "drafts" / filename).read_text(encoding="utf-8")
    for filename in ("assignments.json", "announcements.json",
                     "assessment-reminders.json", "homeroom-announcement.json",
                     "homeroom-email-draft.json", "homeroom-message-draft.json"):
        texts[filename] = (Q2W4_DIR / "drafts" / filename).read_text(encoding="utf-8")
    assert pol.audit_student_facing_texts(texts) == [], pol.audit_student_facing_texts(texts)

    # The guard rejects both promises and negative disclaimers.
    assert pol.find_study_guide_references("A study guide will be provided.")
    assert pol.find_study_guide_references("No study guide will be provided.")
    assert pol.find_study_guide_references("See the review guide.")
    assert pol.find_study_guide_references("Review your Reading Workbook pages.") == []


def test_assignment_reconciliation_classifications():
    from scripts.canvas_llm_deploy.client import FakeDeployClient
    from scripts.canvas_llm_intake import assignment_reconciliation as ar

    client = FakeDeployClient(courses={28171: {"id": 28171, "name": "Language Arts"}})
    client.assignment_groups[28171] = [{"id": "g1", "name": "Classwork"}]
    # MATCH
    match = client.seed_assignment(28171, "Classroom Practice 10", assignment_group="Classwork")
    match.update({"due_at": "2026-11-04T04:59:00Z", "submitted": True, "published": True})
    # UPDATE_REQUIRED
    update = client.seed_assignment(28171, "Classroom Practice 11", assignment_group="Classwork")
    update.update({"due_at": "2026-10-30T03:59:00Z", "published": True})
    # DUPLICATE
    client.seed_assignment(28171, "Classroom Practice 12", assignment_group="Classwork")
    client.seed_assignment(28171, "Classroom Practice 12", assignment_group="Classwork")
    # UNVERIFIED (missing omit_from_final_grade)
    unverified = client.seed_assignment(28171, "Classroom Practice 13", assignment_group="Classwork")
    unverified.update({"due_at": "2026-11-04T04:59:00Z", "published": True})
    unverified.pop("omit_from_final_grade", None)

    def proposal(title, due):
        return {
            "course": "language_arts", "course_id": 28171, "title": title,
            "assignment_group": "Classwork", "due_date": due,
            "points_possible": 100, "grading_type": "percent",
            "submission_types": "on_paper", "omit_from_final_grade": False,
        }

    report = ar.reconcile(2, 4, client=client, proposals=[
        proposal("Classroom Practice 10", "2026-11-03"),
        proposal("Classroom Practice 11", "2026-11-04"),
        proposal("Classroom Practice 12", "2026-11-04"),
        proposal("Classroom Practice 13", "2026-11-03"),
        proposal("Classroom Practice 14", "2026-11-04"),
    ])
    assert report["counts"]["MATCH"] == 1, report["counts"]
    assert report["counts"]["UPDATE_REQUIRED"] == 1, report["counts"]
    assert report["counts"]["DUPLICATE"] == 1, report["counts"]
    assert report["counts"]["UNVERIFIED"] == 1, report["counts"]
    assert report["counts"]["CREATE_REQUIRED"] == 1, report["counts"]
    assert report["bundle_status"] == "BLOCKED", report
    assert report["canvas_writes"] == 0


def test_actual_approvals_bound_to_current_hashes():
    if not _require_staging():
        return
    approvals = _read(Q2W4_DIR / "approvals" / "approval-manifest.json")
    states = []
    for subject, entry in approvals["subjects"].items():
        for granularity, record in entry.items():
            state = record["state"]
            assert state in ("PENDING", "APPROVED", "NOT_REQUIRED"), (subject, granularity, record)
            if state == "APPROVED":
                assert record.get("draft_hash"), (subject, granularity, record)
                assert record.get("source_hash"), (subject, granularity, record)
            states.append(state)
    manifest = _read(Q2W4_DIR / "intake-manifest.json")
    all_approved = all(state in ("APPROVED", "NOT_REQUIRED") for state in states)
    assert manifest["ready_to_publish"] is all_approved
    assert manifest["assignment_count"] == 11
    assert manifest["assessment_reminder_count"] == 4


def test_actual_artifact_hashes_match_current_content():
    if not _require_staging():
        return
    from scripts.canvas_planner.approval_bundle import current_bundle

    record = _read(Q2W4_DIR / "planner" / "artifact-hashes.json")
    manifest = _read(Q2W4_DIR / "intake-manifest.json")
    assert record["source_hash"] == manifest["source_hash"]
    for subject in ("math", "reading_spelling", "language_arts", "science"):
        current = current_bundle(2, 4, subject)
        assert record["artifacts"][subject]["hashes"] == current["hashes"], subject
        assert record["artifacts"][subject]["source_hash"] == manifest["source_hash"]
    homeroom_html = (Q2W4_DIR / "drafts" / "homeroom-page.html").read_text(encoding="utf-8")
    assert record["homeroom"]["hashes"]["page"] == SHA(homeroom_html)
    assert record["homeroom"]["architecture"] == "weekly_homeroom_page"
    assert record["homeroom"]["roster_version"]
    assert record["homeroom"]["weekly_approval"]["approved"] is False


# --------------------------------------------------------------------------- #


def _run():
    fns = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    failed = 0
    for name, fn in fns:
        try:
            fn()
            print(f"PASS {name}")
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"FAIL {name}: {exc}")
    print(f"RESULT: {len(fns) - failed} passed, {failed} failed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    _run()
