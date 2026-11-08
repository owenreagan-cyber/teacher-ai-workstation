"""Weekly release manager: one package, the existing publisher, no live Canvas."""
import hashlib
import json
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.canvas_llm_deploy import ledger as deploy_ledger
from scripts.canvas_llm_deploy import plan as deploy_plan
from scripts.canvas_llm_deploy import weekly_release
from scripts.canvas_llm_deploy.client import FakeDeployClient
from scripts.canvas_llm_intake import manifest as intake_manifest
from scripts.canvas_llm_rollover import homeroom, rollover
from scripts.canvas_llm_storage import isolated_storage

NY = ZoneInfo("America/New_York")
COURSES = {
    "math": 26404, "reading_spelling": 26442, "language_arts": 28171,
    "science": 28166, "homeroom": 26429,
}
LABELS = {
    "math": "Math", "reading_spelling": "Reading/Spelling",
    "language_arts": "Language Arts", "science": "Science",
}
SOURCE = "weekly-manager-source"
FINGERPRINT = "weekly-manager-fingerprint"


def _future_owner() -> str:
    selected = (datetime.now(NY) + timedelta(days=1)).replace(
        hour=0, minute=1, second=0, microsecond=0,
    )
    return selected.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _client():
    client = FakeDeployClient(courses={
        cid: {"id": cid, "name": name} for cid, name in {
            26404: "Math", 26442: "Reading/Spelling", 28171: "Language Arts",
            28166: "Science", 26429: "Homeroom",
        }.items()
    })
    client.assignment_groups[26404] = [{"id": "group-1", "name": "Classwork"}]
    return client


def _manifest(owner: str) -> dict:
    slug = "q2w3-october-26-30-2026"
    agendas = {}
    courses = []
    announcements = []
    for subject in ("math", "reading_spelling", "language_arts", "science"):
        body = f"<div>{LABELS[subject]} agenda</div>"
        digest = hashlib.sha256(body.encode()).hexdigest()
        agendas[subject] = digest
        courses.append({
            "subject": subject, "label": LABELS[subject], "course_id": COURSES[subject],
            "to_page_slug": slug, "front_page_action": "SET_FRONT_PAGE",
            "page_body": body, "to_page_hash": digest, "approved": True,
        })
        announcements.append({
            "subject": subject, "label": LABELS[subject], "course_id": COURSES[subject],
            "title": f"{LABELS[subject]} Canvas Weekly Update", "week_code": "Q2W3",
            "agenda_hash": digest, "page_agenda_hash": digest, "hash_consistent": True,
            "message": f"<p>{LABELS[subject]} agenda</p>",
            "delayed_post_at": owner, "action": "CREATE", "approved": True,
        })
    proposed = {"classMotto": {"motto": "Level Up Together."}}
    homeroom_hash = hashlib.sha256(homeroom.render_proposed(proposed).encode()).hexdigest()
    return {
        "from_week": "Q2W2", "to_week": "Q2W3",
        "source_hash": SOURCE, "plan_fingerprint": FINGERPRINT,
        "agenda_hash": deploy_plan.agenda_composite_hash("Q2W3", agendas),
        "scheduled_at": owner, "owner_publication_time": owner,
        "timezone": "America/New_York",
        "academic_courses": courses,
        "homeroom": {
            "course_id": 26429, "to_page_slug": slug, "front_page_action": "SET_FRONT_PAGE",
            "approved": True, "proposed_content_hash": homeroom_hash,
            "proposed_content": proposed,
        },
        "weekly_announcements": announcements,
        "assignments": [{
            "course": "math", "course_id": 26404, "title": "Math Lesson 41",
            "assignment_group": "Classwork", "points_possible": 100,
            "grading_type": "percent", "submission_types": ["on_paper"],
            "due_utc": "2026-10-27T03:59:00Z", "omit_from_final_grade": False,
            "approved": True, "action": "CREATE",
        }],
        "assessment_reminders": [{
            "subject": "math", "course_id": 26404, "title": "Math test reminder",
            "message": "<p>Math test.</p>", "assessment_date": "2026-10-29",
            "schedule_state": "FUTURE_SCHEDULED", "delayed_post_at": "2026-12-04T21:00:00Z",
            "approved": True, "action": "CREATE",
        }],
    }


def _seed_pages(client, manifest):
    for course in manifest["academic_courses"]:
        client.seed_page(course["course_id"], course["to_page_slug"], title=course["label"], body="", front_page=False)
    client.seed_page(26429, "q2w2-old", title="Homeroom previous", body="<p>old</p>", front_page=True)
    client.seed_page(26429, manifest["homeroom"]["to_page_slug"], title="Homeroom", body="", front_page=False)


def _intake(root_week: Path):
    root_week.mkdir(parents=True, exist_ok=True)
    (root_week / "intake-manifest.json").write_text(json.dumps({
        "quarter": 2, "week": 3, "week_code": "Q2W3",
        "status": "READY_TO_PUBLISH", "approval_state": "APPROVED",
        "source_hash": SOURCE, "plan_fingerprint": FINGERPRINT,
    }), encoding="utf-8")


def test_discover_uses_the_instructional_calendar_and_break_gap():
    during_break = weekly_release.discover(
        today=date(2026, 9, 21), now=datetime(2026, 9, 21, 12, tzinfo=NY),
    )
    assert during_break["week_code"] == "Q2W1"
    assert during_break["selection"] == "next_instructional_week"
    assert during_break["instructional_break"]["start"] == "2026-09-19"
    assert during_break["instructional_break"]["end"] == "2026-10-11"
    assert during_break["friday_publication_valid"] is False
    assert during_break["publication"]["requires_owner_time"] is True
    assert "homeroom" in during_break["subjects"]
    after_friday = weekly_release.discover(
        today=date(2026, 10, 10), now=datetime(2026, 10, 10, 15, tzinfo=NY),
    )
    assert after_friday["week_code"] == "Q2W1"
    assert after_friday["friday_publication_valid"] is False
    weekend = weekly_release.discover(
        today=date(2026, 11, 7), now=datetime(2026, 11, 7, 22, tzinfo=NY),
    )
    assert weekend["week_code"] == "Q2W5"
    assert weekend["instructional_break"] is None


def test_review_keeps_assessment_dates_distinct_from_publication_time():
    owner = _future_owner()
    manifest = _manifest(owner)
    package = {
        "to_week": "Q2W5", "source_hash": SOURCE, "agenda_hash": "agenda-composite",
        "plan_fingerprint": FINGERPRINT, "publication_time": owner,
        "target": {"friday_publication_valid": False, "instructional_break": None},
        "artifacts": weekly_release._artifact_rows(manifest), "blockers": [], "warnings": [],
    }
    view = weekly_release.review_package(package)
    notice = next(row for row in view["artifacts"] if row["kind"] == "assessment_notice")
    assert notice["assessment_date"] == "2026-10-29"
    assert notice["delayed_post_at"] == "2026-12-04T21:00:00Z"
    assert notice["delayed_post_at"] != view["publication_time"]
    assert set(view["courses"]) == set(weekly_release.RELEASE_COURSES)


def test_missing_homeroom_is_blocked_and_not_invented():
    package = {
        "to_week": "Q2W5", "source_hash": SOURCE, "agenda_hash": "agenda",
        "plan_fingerprint": FINGERPRINT, "publication_time": _future_owner(),
        "target": {}, "warnings": [],
        "artifacts": weekly_release._artifact_rows({"homeroom": None}),
        "blockers": [],
    }
    view = weekly_release.review_package(package)
    row = next(item for item in view["artifacts"] if item["kind"] == "homeroom_page")
    assert row["action"] == "BLOCKED"
    assert view["counts"]["BLOCKED"] == 1
    assert "homeroom content is missing" in view["blockers"]


def test_reconciliation_classifies_without_writing():
    owner = _future_owner()
    manifest = _manifest(owner)
    manifest["to_week"] = "Q2W5"
    client = _client()
    _seed_pages(client, manifest)
    # Exact assignment already exists.
    manifest["assignments"][0]["action"] = "CREATE"
    client.assignments["existing"] = {
        "id": "existing", "course_id": 26404, "title": "Math Lesson 41",
        "due_at": "2026-10-27T03:59:00Z",
    }
    # Same-week announcement already carries the same agenda.
    first = manifest["weekly_announcements"][0]
    client.announcements["posted"] = {
        "id": "posted", "course_id": first["course_id"], "title": first["title"],
        "delayed_post_at": first["delayed_post_at"], "agenda_hash": first["agenda_hash"],
        "message": first["message"],
    }
    result = weekly_release.reconcile(manifest, client, quarter=2, week=5)
    assert client._write_counts["POST"] == 0 and client._write_counts["PUT"] == 0
    assignment = next(row for row in result["artifacts"] if row["kind"] == "assignment")
    announcement = next(row for row in result["artifacts"] if row["title"] == first["title"])
    assert assignment["action"] == "SKIP"
    assert announcement["action"] == "SKIP"


def test_duplicate_assignment_and_changed_assignment_are_distinct():
    manifest = _manifest(_future_owner())
    manifest["to_week"] = "Q2W5"
    client = _client()
    client.assignments["one"] = {
        "id": "one", "course_id": 26404, "title": "Math Lesson 41", "due_at": "2026-10-27T03:59:00Z",
    }
    client.assignments["two"] = {
        "id": "two", "course_id": 26404, "title": "Math Lesson 41", "due_at": "2026-10-28T03:59:00Z",
    }
    duplicate = weekly_release.reconcile(manifest, client, quarter=2, week=5)
    assert next(row for row in duplicate["artifacts"] if row["kind"] == "assignment")["action"] == "BLOCKED"
    assert client._write_counts["POST"] == 0
    client.assignments.pop("two")
    manifest["assignments"][0]["action"] = "UPDATE"
    manifest["assignments"][0]["assignment_id"] = "one"
    manifest["assignments"][0]["due_utc"] = "2026-10-28T03:59:00Z"
    updated = weekly_release.reconcile(manifest, client, quarter=2, week=5)
    assert next(row for row in updated["artifacts"] if row["kind"] == "assignment")["action"] == "UPDATE"
    assert client._write_counts["POST"] == 0 and client._write_counts["PUT"] == 0


def test_approval_is_granular_and_a_changed_artifact_invalidates_it():
    owner = _future_owner()
    with isolated_storage():
        staging = intake_manifest.staging_dir(2, 5)
        drafts = staging / "drafts"
        drafts.mkdir(parents=True)
        for subject in ("math", "reading_spelling", "language_arts", "science"):
            name = "reading-page.html" if subject == "reading_spelling" else f"{subject}-page.html"
            (drafts / name).write_text(f"<p>{subject}</p>", encoding="utf-8")
        (drafts / "assignments.json").write_text(json.dumps([{
            "course": "math", "title": "Math Lesson 46", "due_at": "2026-11-09T03:59:00Z",
        }]), encoding="utf-8")
        (drafts / "announcements.json").write_text(json.dumps([{
            "course": "Math", "title": "Math Canvas Weekly Update", "message": "<p>Math</p>",
        }]), encoding="utf-8")
        (drafts / "assessment-reminders.json").write_text("[]", encoding="utf-8")
        html = "<p>Homeroom week</p>"
        (drafts / "homeroom-page.html").write_text(html, encoding="utf-8")
        page_hash = hashlib.sha256(html.encode()).hexdigest()
        (drafts / "homeroom-announcement.json").write_text(json.dumps({
            "title": "4th Grade Happenings - Week 5", "message": html,
            "course_id": 26429, "page_id": 798096, "page_slug": "q2w5-november-9-13-2026",
            "newsletter_html_hash": page_hash, "approval_state": "APPROVED", "approved": True,
            "action": "CREATE",
        }), encoding="utf-8")
        (staging / "planner").mkdir(exist_ok=True)
        (staging / "planner" / "homeroom-weekly-approval.json").write_text(json.dumps({
            "course_id": 26429, "page_id": 798096, "page_slug": "q2w5-november-9-13-2026",
            "approved": True, "approved_body_hash": page_hash, "status": "APPROVED",
        }), encoding="utf-8")
        (staging / "planner" / "homeroom-page-resolution.json").write_text(json.dumps({
            "course_id": 26429, "page_id": 798096, "slug": "q2w5-november-9-13-2026",
            "status": "FOUND",
        }), encoding="utf-8")
        intake_manifest.save_manifest(2, 5, {
            "quarter": 2, "week": 5, "week_code": "Q2W5",
            "status": "READY_FOR_REVIEW", "approval_state": "PENDING",
            "source_hash": SOURCE, "date_range": {"start": "2026-11-09", "end": "2026-11-13"},
            "history": [{"event": "created"}],
        })
        approved = weekly_release.approve_release(
            2, 5, confirmation="APPROVE Q2W5", owner_publication_time=owner,
            now=datetime.now(NY),
        )
        stored = intake_manifest.load_manifest(2, 5)
        assert approved["source_hash"] == SOURCE
        assert stored["approval_state"] == "APPROVED"
        assert stored["plan_fingerprint"] == approved["plan_fingerprint"]
        assert stored["history"] == [{"event": "created"}]
        (drafts / "math-page.html").write_text("<p>math changed</p>", encoding="utf-8")
        assert weekly_release.invalidate_changed_artifacts(2, 5) is True
        assert intake_manifest.load_manifest(2, 5)["approval_state"] == "PENDING"
        assert intake_manifest.load_manifest(2, 5)["ready_to_publish"] is False


def _write_identity(staging: Path, *, page_id=798096, slug="q2w5-november-9-13-2026",
                    course_id=26429, approved=False, approved_hash=None, announcement_page_id=798096,
                    announcement_slug="q2w5-november-9-13-2026", announcement_course=26429,
                    action="CREATE", schedule_state="FUTURE_SCHEDULED", block_reason=None):
    html = "<p>Homeroom week</p>"
    current = hashlib.sha256(html.encode()).hexdigest()
    drafts = staging / "drafts"
    drafts.mkdir(parents=True, exist_ok=True)
    (drafts / "homeroom-page.html").write_text(html, encoding="utf-8")
    (drafts / "homeroom-announcement.json").write_text(json.dumps({
        "title": "4th Grade Happenings - Week 5", "message": html,
        "course_id": announcement_course, "page_id": announcement_page_id,
        "page_slug": announcement_slug, "newsletter_html_hash": current,
        "approval_state": "PENDING", "action": action, "schedule_state": schedule_state,
        "block_reason": block_reason,
    }), encoding="utf-8")
    planner = staging / "planner"
    planner.mkdir(exist_ok=True)
    (planner / "homeroom-page-resolution.json").write_text(json.dumps({
        "course_id": course_id, "page_id": page_id, "slug": slug, "status": "FOUND",
    }), encoding="utf-8")
    approval_path = planner / "homeroom-weekly-approval.json"
    if approved_hash is not None:
        approval_path.write_text(json.dumps({
            "course_id": course_id, "page_id": page_id, "page_slug": slug,
            "approved": approved, "approved_body_hash": approved_hash,
            "status": "APPROVED" if approved else "PENDING_OWNER_APPROVAL",
        }), encoding="utf-8")
    elif approval_path.exists():
        approval_path.unlink()
    return current


def test_homeroom_identity_uses_resolution_slug_and_current_hash():
    with isolated_storage():
        staging = intake_manifest.staging_dir(2, 5)
        current = _write_identity(staging)
        identity = weekly_release.resolve_homeroom_identity(2, 5)
        assert identity["course_id"] == 26429
        assert identity["page_id"] == 798096
        assert identity["page_slug"] == "q2w5-november-9-13-2026"
        assert identity["page_hash"] == current
        stale = "c3cb881258c1bc7cba3e9a3d3f8969a18c522505661b5388ace82d33853e7c85"
        _write_identity(staging, approved=False, approved_hash=stale)
        pending = weekly_release.resolve_homeroom_identity(2, 5)
        assert pending["page_hash"] == current
        assert pending["page_hash"] != stale


def test_wrong_or_missing_homeroom_identity_blocks_before_approval_writes():
    cases = (
        {"page_id": 1},
        {"course_id": 999},
        {"slug": "wrong-slug"},
        {"page_id": None},
        {"approved": True, "approved_hash": "c3cb881258c1bc7cba3e9a3d3f8969a18c522505661b5388ace82d33853e7c85"},
    )
    with isolated_storage():
        staging = intake_manifest.staging_dir(2, 5)
        for case in cases:
            kwargs = {"page_id": 798096, "slug": "q2w5-november-9-13-2026", "course_id": 26429}
            kwargs.update(case)
            if kwargs["page_id"] is None:
                _write_identity(staging)
                record = json.loads((staging / "planner" / "homeroom-page-resolution.json").read_text())
                record["page_id"] = None
                (staging / "planner" / "homeroom-page-resolution.json").write_text(json.dumps(record), encoding="utf-8")
            else:
                _write_identity(staging, **kwargs)
            try:
                weekly_release.resolve_homeroom_identity(2, 5)
                raise AssertionError(case)
            except weekly_release.ReleaseBlocked:
                pass
        intake_manifest.save_manifest(2, 5, {
            "quarter": 2, "week": 5, "week_code": "Q2W5", "status": "READY_FOR_REVIEW",
            "approval_state": "PENDING", "source_hash": SOURCE,
            "date_range": {"start": "2026-11-09", "end": "2026-11-13"},
        })
        current = hashlib.sha256(b"<p>Homeroom week</p>").hexdigest()
        _write_identity(
            staging, approved=True, approved_hash=current,
            action="BLOCKED", schedule_state="BLOCKED", block_reason="duplicate family announcement",
        )
        family = json.loads((staging / "drafts" / "homeroom-announcement.json").read_text())
        family["approval_state"] = "APPROVED"
        family["approved"] = True
        (staging / "drafts" / "homeroom-announcement.json").write_text(json.dumps(family), encoding="utf-8")
        try:
            weekly_release.approve_release(
                2, 5, confirmation="APPROVE Q2W5", owner_publication_time=_future_owner(),
                now=datetime.now(NY),
            )
            raise AssertionError("blocked announcement was approved")
        except weekly_release.ReleaseBlocked as exc:
            assert "family announcement" in str(exc)
        assert intake_manifest.load_manifest(2, 5)["approval_state"] == "PENDING"


def test_blocked_family_announcement_is_a_package_blocker_until_owner_time():
    home = {"course_id": 26429, "proposed_content_hash": "hash", "body": "<p>Homeroom week</p>"}
    rows = weekly_release._artifact_rows({
        "homeroom": home,
        "homeroom_announcement": {
            "course_id": 26429, "title": "4th Grade Happenings - Week 5",
            "action": "BLOCKED", "schedule_state": "OWNER_TIME_REQUIRED",
            "page_id": 798096, "page_slug": "q2w5-november-9-13-2026",
        },
    })
    assert weekly_release.package_blockers(rows) == [weekly_release.OWNER_TIME_BLOCK]
    resolved = weekly_release._artifact_rows({
        "homeroom": home,
        "homeroom_announcement": {
            "course_id": 26429, "title": "4th Grade Happenings - Week 5",
            "action": "BLOCKED", "schedule_state": "OWNER_TIME_REQUIRED",
        },
        "assignments": [{"course": "math", "title": "Math", "action": "BLOCKED", "block_reason": "duplicate title"}],
    })
    blockers = weekly_release.package_blockers(resolved, owner_publication_time=_future_owner())
    assert weekly_release.OWNER_TIME_BLOCK in blockers
    assert "duplicate title" in blockers or any("assignment" in item for item in blockers)
    assert all(row["action"] != "CREATE" or row["kind"] != "family_announcement" for row in resolved)


def test_invalid_owner_time_writes_nothing_and_blocked_packages_cannot_be_approved():
    with isolated_storage():
        staging = intake_manifest.staging_dir(2, 5)
        _write_identity(staging, approved=True, approved_hash=hashlib.sha256(b"<p>Homeroom week</p>").hexdigest())
        family = json.loads((staging / "drafts" / "homeroom-announcement.json").read_text())
        family["approval_state"] = "APPROVED"
        family["approved"] = True
        (staging / "drafts" / "homeroom-announcement.json").write_text(json.dumps(family), encoding="utf-8")
        intake_manifest.save_manifest(2, 5, {
            "quarter": 2, "week": 5, "week_code": "Q2W5", "status": "READY_FOR_REVIEW",
            "approval_state": "PENDING", "source_hash": SOURCE,
            "date_range": {"start": "2026-11-09", "end": "2026-11-13"},
        })
        before = (staging / "approvals" / "approval-manifest.json").exists()
        for bad in ("PASTE_ACTUAL_TIMESTAMP_HERE", "", "2026-11-08T00:01:00", "2020-01-01T00:01:00Z", "not-a-time"):
            try:
                weekly_release.approve_release(
                    2, 5, confirmation="APPROVE Q2W5", owner_publication_time=bad,
                    now=datetime.now(NY),
                )
                raise AssertionError(bad)
            except weekly_release.ReleaseBlocked:
                pass
        assert (staging / "approvals" / "approval-manifest.json").exists() is before
        assert intake_manifest.load_manifest(2, 5)["approval_state"] == "PENDING"
        assert not (staging / "planner" / "live-transport-authorization.json").exists()
        family["action"] = "BLOCKED"
        family["block_reason"] = "duplicate family announcement"
        (staging / "drafts" / "homeroom-announcement.json").write_text(json.dumps(family), encoding="utf-8")
        try:
            weekly_release.approve_release(
                2, 5, confirmation="APPROVE Q2W5", owner_publication_time=_future_owner(),
                now=datetime.now(NY),
            )
            raise AssertionError("blocked package was approved")
        except weekly_release.ReleaseBlocked as exc:
            assert "BLOCKED" in str(exc)
        assert intake_manifest.load_manifest(2, 5)["status"] == "READY_FOR_REVIEW"


def test_repeated_approval_is_idempotent_and_a_new_owner_time_invalidates_it():
    owner = _future_owner()
    with isolated_storage():
        staging = intake_manifest.staging_dir(2, 5)
        drafts = staging / "drafts"
        drafts.mkdir(parents=True)
        for subject in ("math", "reading_spelling", "language_arts", "science"):
            name = "reading-page.html" if subject == "reading_spelling" else f"{subject}-page.html"
            (drafts / name).write_text(f"<p>{subject}</p>", encoding="utf-8")
        (drafts / "assignments.json").write_text("[]", encoding="utf-8")
        (drafts / "announcements.json").write_text("[]", encoding="utf-8")
        (drafts / "assessment-reminders.json").write_text("[]", encoding="utf-8")
        current = _write_identity(staging, approved=True, approved_hash=hashlib.sha256(b"<p>Homeroom week</p>").hexdigest())
        family = json.loads((drafts / "homeroom-announcement.json").read_text())
        family.update({"approval_state": "APPROVED", "approved": True, "action": "CREATE", "newsletter_html_hash": current})
        (drafts / "homeroom-announcement.json").write_text(json.dumps(family), encoding="utf-8")
        intake_manifest.save_manifest(2, 5, {
            "quarter": 2, "week": 5, "week_code": "Q2W5", "status": "READY_FOR_REVIEW",
            "approval_state": "PENDING", "source_hash": SOURCE,
            "date_range": {"start": "2026-11-09", "end": "2026-11-13"}, "history": [],
        })
        first = weekly_release.approve_release(2, 5, confirmation="APPROVE Q2W5", owner_publication_time=owner, now=datetime.now(NY))
        again = weekly_release.approve_release(2, 5, confirmation="APPROVE Q2W5", owner_publication_time=owner, now=datetime.now(NY))
        assert again.get("idempotent") is True
        assert again["plan_fingerprint"] == first["plan_fingerprint"]
        later = (datetime.now(NY) + timedelta(days=2)).replace(hour=0, minute=1, second=0, microsecond=0)
        later_value = later.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        assert weekly_release.invalidate_changed_artifacts(2, 5, owner_publication_time=later_value) is True
        assert intake_manifest.load_manifest(2, 5)["approval_state"] == "PENDING"
        intake = intake_manifest.load_manifest(2, 5)
        intake["plan_fingerprint"] = "stale-fingerprint"
        intake_manifest.save_manifest(2, 5, intake)
        try:
            weekly_release.approve_release(2, 5, confirmation="APPROVE Q2W5", owner_publication_time=owner, now=datetime.now(NY))
            raise AssertionError("stale fingerprint was approved")
        except weekly_release.ReleaseBlocked as exc:
            assert "fingerprint" in str(exc)


def test_publish_reaches_verified_and_rerun_writes_nothing():
    owner = _future_owner()
    manifest = _manifest(owner)
    with isolated_storage() as root:
        _intake(root / "intake" / "2026-2027" / "q2" / "w3")
        client = _client()
        _seed_pages(client, manifest)
        report = weekly_release.publish_release(
            2, 3, client=client, confirmation="ROLLOVER Q2W3",
            now=datetime.now(NY), manifest=manifest,
        )
        assert report["lifecycle"] == "PUBLISHED_VERIFIED", report.get("failures")
        assert report["state"] == weekly_release.FULLY_COMPLETED
        assert report["chief_of_staff"]["week_code"] == "Q2W3"
        posts = client._write_counts["POST"]
        puts = client._write_counts["PUT"]
        again = weekly_release.publish_release(
            2, 3, client=client, confirmation="ROLLOVER Q2W3",
            now=datetime.now(NY), manifest=manifest,
        )
        assert again["already_complete"] is True
        assert client._write_counts["POST"] == posts
        assert client._write_counts["PUT"] == puts


def test_partial_publication_and_finalizer_refusal_are_not_complete():
    owner = _future_owner()
    manifest = _manifest(owner)
    with isolated_storage() as root:
        _intake(root / "intake" / "2026-2027" / "q2" / "w3")
        client = _client()
        _seed_pages(client, manifest)
        original_update = client.update_page
        def fail_science(course_id, page_ref, **kwargs):
            if course_id == 28166:
                raise RuntimeError("injected canvas write failure")
            return original_update(course_id, page_ref, **kwargs)
        client.update_page = fail_science
        partial = weekly_release.publish_release(
            2, 3, client=client, confirmation="ROLLOVER Q2W3",
            now=datetime.now(NY), manifest=manifest,
        )
        assert partial["lifecycle"] != "PUBLISHED_VERIFIED"
        assert partial["state"] == weekly_release.PARTIALLY_PUBLISHED
    with isolated_storage() as root:
        _intake(root / "intake" / "2026-2027" / "q2" / "w3")
        client = _client()
        _seed_pages(client, manifest)
        original = rollover.deploy_ledger.finalize_published_verified
        rollover.deploy_ledger.finalize_published_verified = (
            lambda *args, **kwargs: {"status": "BLOCKED", "failures": ["injected finalizer refusal"]}
        )
        try:
            refused = weekly_release.publish_release(
                2, 3, client=client, confirmation="ROLLOVER Q2W3",
                now=datetime.now(NY), manifest=manifest,
            )
        finally:
            rollover.deploy_ledger.finalize_published_verified = original
        assert refused["lifecycle"] == "FINALIZATION_BLOCKED"
        assert deploy_ledger.load_published_verified(2, 3) is None


def test_rollover_incomplete_recovers_without_canvas_writes():
    with isolated_storage() as root:
        staging = root / "intake" / "2026-2027" / "q2" / "w3"
        _intake(staging)
        intake = intake_manifest.load_manifest(2, 3)
        intake["status"] = "PUBLISHED_VERIFIED"
        intake_manifest.save_manifest(2, 3, intake)
        deploy_ledger.write_json(deploy_ledger.deploy_dir(2, 3) / "published-verified-ledger.json", {
            "status": "PUBLISHED_VERIFIED", "source_hash": SOURCE, "plan_fingerprint": FINGERPRINT,
        })
        client = _client()
        report = weekly_release.publish_release(
            2, 3, client=client, confirmation="ROLLOVER Q2W3", now=datetime.now(NY),
        )
        assert report["lifecycle"] == "PUBLISHED_VERIFIED"
        assert report["canvas_writes"] == 0
        assert client._write_counts["POST"] == 0 and client._write_counts["PUT"] == 0
        assert weekly_release.release_state(2, 3)["state"] == weekly_release.FULLY_COMPLETED


def test_wrong_source_hash_blocks_before_transport():
    owner = _future_owner()
    manifest = _manifest(owner)
    manifest["source_hash"] = manifest["agenda_hash"]
    with isolated_storage() as root:
        _intake(root / "intake" / "2026-2027" / "q2" / "w3")
        client = _client()
        try:
            weekly_release.publish_release(
                2, 3, client=client, confirmation="ROLLOVER Q2W3",
                now=datetime.now(NY), manifest=manifest,
            )
            raise AssertionError("source mismatch was accepted")
        except weekly_release.ReleaseBlocked as exc:
            assert "source hash" in str(exc)
        assert client._write_counts["POST"] == 0 and client._write_counts["PUT"] == 0


def test_cli_publish_without_production_does_not_call_canvas():
    from io import StringIO
    from contextlib import redirect_stdout
    with redirect_stdout(StringIO()):
        code = weekly_release.main(["--publish", "--week", "q2w5"])
    assert code == 2


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
