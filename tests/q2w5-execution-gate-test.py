"""Phase 3 execution-gate regressions.

These call the production gate, execute(), and the live announcement
normalizer. They use a temporary ledger and never touch Canvas.
"""
from __future__ import annotations

import copy
import hashlib
import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.canvas_llm_deploy import coordinator, ledger
from scripts.canvas_llm_deploy.client import (
    DeployClientError,
    FakeDeployClient,
    LiveDeployClient,
)
from scripts.canvas_llm_deploy.plan import plan_fingerprint
from scripts.canvas_llm_intake import manifest as intake_manifest
from scripts.canvas_llm_rollover import rollover

NOW = datetime(2026, 11, 7, 17, 32, tzinfo=timezone.utc)
FUTURE = "2026-11-13T21:00:00Z"
FUTURE_OFFSET = "2026-11-13T16:00:00-05:00"
PAST = "2026-11-01T21:00:00Z"
SOURCE = "authoritative-source-hash"
SLUG = "q2w5-november-9-13-2026"
COURSES = {
    "math": 26404,
    "reading_spelling": 26442,
    "language_arts": 28171,
    "science": 28166,
    "homeroom": 26429,
}
LABELS = {
    "math": "Math",
    "reading_spelling": "Reading/Spelling",
    "language_arts": "Language Arts",
    "science": "Science",
}


def _zero(client) -> None:
    counts = client._write_counts
    assert counts["PUT"] == 0, counts
    assert counts["POST"] == 0, counts
    assert counts["DELETE"] == 0, counts


def _seed_source(root: Path, source: str = SOURCE, fingerprint: str = "q2w5-plan") -> None:
    staging = root / "intake" / "q2w5"
    staging.mkdir(parents=True, exist_ok=True)
    (staging / "intake-manifest.json").write_text(
        json.dumps({
            "quarter": 2, "week": 5, "week_code": "Q2W5",
            "status": "READY_TO_PUBLISH", "approval_state": "APPROVED",
            "source_hash": source, "plan_fingerprint": fingerprint,
        }), encoding="utf-8"
    )


def _page(subject: str) -> dict:
    body = f'<div class="kl_wrapper_3"><h2>{LABELS[subject]}</h2><h3>Reminders</h3></div>'
    return {
        "subject": subject,
        "label": LABELS[subject],
        "course_id": COURSES[subject],
        "to_page_slug": SLUG,
        "front_page_action": "SET_FRONT_PAGE",
        "page_body": body,
        "to_page_hash": hashlib.sha256(body.encode()).hexdigest(),
        "approved": True,
    }


def _release(**overrides) -> dict:
    pages = [_page(subject) for subject in LABELS]
    announcements = [
        {
            "subject": subject,
            "label": LABELS[subject],
            "course_id": COURSES[subject],
            "title": f"{LABELS[subject]} Canvas Weekly Update",
            "week_code": "Q2W5",
            "message": f"<p>Good afternoon,</p><p>{LABELS[subject]} agenda</p><p>Mr. Reagan</p>",
            "delayed_post_at": FUTURE,
            "schedule_state": "FUTURE_SCHEDULED",
            "scheduled": True,
            "classification": "NEW",
            "action": "CREATE",
            "approved": True,
        }
        for subject in LABELS
    ]
    manifest = {
        "from_week": "Q2W4",
        "to_week": "Q2W5",
        "source_hash": SOURCE,
        "plan_fingerprint": "q2w5-plan",
        "owner_publication_time": FUTURE,
        "scheduled_at": FUTURE,
        "timezone": "America/New_York",
        "academic_courses": pages,
        "homeroom": {
            "course_id": COURSES["homeroom"],
            "to_page_slug": SLUG,
            "to_page_id": "page-26429-" + SLUG,
            "front_page_action": "SET_FRONT_PAGE",
            "proposed_content": {"classMotto": {"motto": "Level Up Together."}},
            "proposed_content_hash": "filled-below",
            "approved": True,
        },
        "weekly_announcements": announcements,
        "assignments": [],
        "assessment_reminders": [],
    }
    from scripts.canvas_llm_rollover import homeroom
    rendered = homeroom.render_proposed(manifest["homeroom"]["proposed_content"])
    manifest["homeroom"]["proposed_content_hash"] = hashlib.sha256(rendered.encode()).hexdigest()
    manifest.update(overrides)
    return manifest


def _client() -> FakeDeployClient:
    courses = {cid: {"id": cid, "name": name} for name, cid in COURSES.items()}
    client = FakeDeployClient(courses=courses)
    for subject, cid in COURSES.items():
        if subject == "homeroom":
            client.seed_page(cid, "q2w4-old", title="Homeroom Q2W4", body="<p>old</p>", front_page=True)
        client.seed_page(cid, SLUG, title=f"Q2W5 {LABELS.get(subject, 'Homeroom')}", body="", front_page=False)
    return client


def _execute(manifest, client, *, now=NOW):
    return rollover.execute(
        2, 4, 2, 5, client=client, owner_confirmation="ROLLOVER Q2W5",
        manifest=manifest, now=now,
    )


def _blocked(manifest, *, now=NOW, mutate=None):
    original = copy.deepcopy(manifest)
    if mutate:
        mutate(manifest)
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        original_deploy = ledger.DEPLOY_ROOT
        original_staging = intake_manifest.staging_dir
        ledger.DEPLOY_ROOT = root / "deployments"
        intake_manifest.staging_dir = lambda q, w: root / "intake" / f"q{q}w{w}"
        _seed_source(root)
        client = _client()
        before = copy.deepcopy(manifest)
        try:
            try:
                result = _execute(manifest, client, now=now)
            except rollover.RolloverBlocked:
                result = {"lifecycle": "BLOCKED", "failures": ["RolloverBlocked"]}
        finally:
            ledger.DEPLOY_ROOT = original_deploy
            intake_manifest.staging_dir = original_staging
    assert result["lifecycle"] == "BLOCKED", result
    _zero(client)
    assert manifest == before
    assert manifest == original or mutate is not None
    return result


def test_past_future_label_writes_nothing():
    manifest = _release()
    manifest["assessment_reminders"] = [{
        "title": "Past", "course_id": COURSES["math"], "message": "<p>Past.</p>",
        "schedule_state": "FUTURE_SCHEDULED", "scheduled": True,
        "delayed_post_at": PAST, "approved": True, "content_status": "READY",
    }]
    result = _blocked(manifest)
    assert any("not in the future" in item for item in result["failures"])


def test_missing_delayed_future_label_writes_nothing():
    manifest = _release()
    manifest["assessment_reminders"] = [{
        "title": "Missing", "course_id": COURSES["math"], "message": "<p>x</p>",
        "schedule_state": "FUTURE_SCHEDULED", "scheduled": True,
        "delayed_post_at": None, "approved": True, "content_status": "READY",
    }]
    result = _blocked(manifest)
    assert any("without delayed_post_at" in item for item in result["failures"])


def test_naive_delayed_post_writes_nothing():
    manifest = _release()
    manifest["assessment_reminders"] = [{
        "title": "Naive", "course_id": COURSES["math"], "message": "<p>x</p>",
        "schedule_state": "FUTURE_SCHEDULED", "scheduled": True,
        "delayed_post_at": "2026-11-13T16:00:00", "approved": True, "content_status": "READY",
    }]
    result = _blocked(manifest)
    assert any("timezone" in item for item in result["failures"])


def test_missing_and_wrong_source_hash_write_nothing():
    missing = _release()
    missing.pop("source_hash")
    result = _blocked(missing)
    assert any("source hash is missing" in item for item in result["failures"])
    wrong = _release(source_hash="WRONG")
    result = _blocked(wrong)
    assert any("does not match the authoritative source" in item for item in result["failures"])


def test_missing_authoritative_snapshot_writes_nothing():
    manifest = _release()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        original_deploy = ledger.DEPLOY_ROOT
        original_staging = intake_manifest.staging_dir
        ledger.DEPLOY_ROOT = root / "deployments"
        intake_manifest.staging_dir = lambda q, w: root / "intake" / f"q{q}w{w}"
        client = _client()
        try:
            result = _execute(manifest, client)
        finally:
            ledger.DEPLOY_ROOT = original_deploy
            intake_manifest.staging_dir = original_staging
    assert result["lifecycle"] == "BLOCKED"
    assert any("authoritative source snapshot is missing" in item for item in result["failures"])
    _zero(client)


def test_page_approval_must_be_true():
    for value, label in (({"drop": True}, "missing"), (None, "null"), (False, "false")):
        manifest = _release()
        if isinstance(value, dict):
            manifest["academic_courses"][0].pop("approved")
        else:
            manifest["academic_courses"][0]["approved"] = value
        result = _blocked(manifest)
        assert any("approved is not true" in item for item in result["failures"]), label


def test_page_status_hash_and_identity_block():
    manifest = _release()
    manifest["academic_courses"][1]["status"] = "PENDING"
    assert any("PENDING" in item for item in _blocked(manifest)["failures"])
    manifest = _release()
    manifest["academic_courses"][2]["approval_state"] = "BLOCKED"
    assert any("BLOCKED" in item for item in _blocked(manifest)["failures"])
    manifest = _release()
    manifest["academic_courses"][0].pop("to_page_hash")
    assert any("approval hash is missing" in item for item in _blocked(manifest)["failures"])
    manifest = _release()
    manifest["academic_courses"][0]["current_hash"] = "different"
    assert any("does not match" in item for item in _blocked(manifest)["failures"])
    manifest = _release()
    manifest["academic_courses"][3]["page_id"] = "111"
    manifest["academic_courses"][3]["to_page_id"] = "222"
    assert any("page id changed" in item for item in _blocked(manifest)["failures"])
    manifest = _release()
    manifest["academic_courses"][0]["course_id"] = None
    assert any("course id is missing" in item for item in _blocked(manifest)["failures"])


def test_blocked_homeroom_prevents_academic_writes_and_is_not_rewritten():
    window_open = datetime(2026, 11, 1, 15, 0, tzinfo=timezone.utc)
    for state in ("BLOCKED", "OWNER_TIME_REQUIRED"):
        manifest = _release(weekly_announcements=[])
        family = {
            "title": "Family", "course_id": COURSES["homeroom"],
            "page_id": manifest["homeroom"]["to_page_id"],
            "schedule_state": state, "action": state if state == "BLOCKED" else "CREATE",
            "approval_state": "PENDING", "approved": False,
            "publication_dependency": "HOMEROOM_PAGE_PUBLISHED_AND_VERIFIED",
            "message": "<p>newsletter</p>",
        }
        manifest["homeroom_announcement"] = family
        result = _blocked(manifest, now=window_open)
        assert family["schedule_state"] == state
        assert family["action"] != "CREATE" or state == "OWNER_TIME_REQUIRED"
        assert result["lifecycle"] == "BLOCKED"


def test_homeroom_dependency_and_identity_block():
    manifest = _release(weekly_announcements=[])
    manifest["homeroom"].pop("approved")
    assert any("homeroom approved is not true" in item for item in _blocked(manifest)["failures"])
    manifest = _release(weekly_announcements=[])
    manifest["homeroom_announcement"] = {
        "title": "Family", "course_id": COURSES["homeroom"], "page_id": "999",
        "schedule_state": "FUTURE_SCHEDULED", "delayed_post_at": FUTURE,
        "approval_state": "APPROVED", "approved": True,
        "publication_dependency": "HOMEROOM_PAGE_PUBLISHED_AND_VERIFIED",
        "message": "<p>x</p>",
    }
    assert any("page id does not match" in item for item in _blocked(manifest)["failures"])
    manifest = _release(weekly_announcements=[])
    manifest["homeroom_announcement"] = {
        "title": "Family", "course_id": COURSES["homeroom"],
        "page_id": manifest["homeroom"]["to_page_id"],
        "schedule_state": "FUTURE_SCHEDULED", "delayed_post_at": FUTURE,
        "approval_state": "APPROVED", "approved": True,
        "publication_dependency": "MISSING", "message": "<p>x</p>",
    }
    assert any("page-first" in item for item in _blocked(manifest)["failures"])
    manifest = _release(weekly_announcements=[])
    manifest["homeroom_announcement"] = {
        "title": "Family", "course_id": COURSES["homeroom"],
        "page_id": manifest["homeroom"]["to_page_id"],
        "schedule_state": "FUTURE_SCHEDULED", "delayed_post_at": PAST,
        "approval_state": "APPROVED", "approved": True,
        "publication_dependency": "HOMEROOM_PAGE_PUBLISHED_AND_VERIFIED",
        "message": "<p>x</p>",
    }
    assert any("not in the future" in item for item in _blocked(manifest)["failures"])


def test_friday_window_without_owner_time_writes_nothing():
    manifest = _release(weekly_announcements=[])
    manifest["homeroom_announcement"] = {
        "title": "Family", "course_id": COURSES["homeroom"],
        "page_id": manifest["homeroom"]["to_page_id"],
        "schedule_state": "OWNER_TIME_REQUIRED", "action": "CREATE",
        "approval_state": "PENDING", "approved": False,
        "publication_dependency": "HOMEROOM_PAGE_PUBLISHED_AND_VERIFIED",
        "message": "<p>x</p>",
    }
    _blocked(manifest, now=datetime(2026, 11, 1, 15, 0, tzinfo=timezone.utc))
    closed = _release(weekly_announcements=[])
    closed["publication_time_required"] = True
    closed.pop("owner_publication_time", None)
    result = _blocked(closed, now=datetime(2026, 11, 8, 18, 0, tzinfo=timezone.utc))
    assert result["lifecycle"] == "BLOCKED"


def test_blocked_notice_weekly_and_assignment_write_nothing():
    notice = _release()
    notice["assessment_reminders"] = [{
        "title": "Blocked notice", "course_id": COURSES["language_arts"],
        "schedule_state": "BLOCKED", "action": "BLOCKED", "message": "<p>x</p>",
        "approved": True,
    }]
    _blocked(notice)
    weekly = _release()
    weekly["weekly_announcements"][0]["schedule_state"] = "BLOCKED"
    weekly["weekly_announcements"][0]["action"] = "BLOCKED"
    _blocked(weekly)
    assignment = _release(weekly_announcements=[])
    assignment["assignments"] = [{
        "title": "Blocked assignment", "course_id": COURSES["math"], "action": "BLOCKED",
    }]
    _blocked(assignment)


def test_stale_preflight_and_changed_owner_time_write_nothing():
    manifest = _release(weekly_announcements=[])
    manifest["plan_fingerprint"] = "approved-fingerprint"
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        original_deploy = ledger.DEPLOY_ROOT
        original_staging = intake_manifest.staging_dir
        ledger.DEPLOY_ROOT = root / "deployments"
        intake_manifest.staging_dir = lambda q, w: root / "intake" / f"q{q}w{w}"
        _seed_source(root)
        plan = {"weekly_announcements": [{"delayed_post_at": FUTURE, "title": "x"}]}
        ledger.write_preflight(2, 5, {
            "preflight_id": "pf", "created_at": NOW.isoformat(),
            "expires_at": "2099-01-01T00:00:00+00:00", "quarter": 2, "week": 5,
            "week_code": "Q2W5", "source_hash": SOURCE, "approval_snapshot_hash": "appr",
            "plan": plan, "ready": True, "canvas_writes": 0, "blockers": [],
        })
        client = _client()
        before = copy.deepcopy(manifest)
        try:
            result = _execute(manifest, client)
        finally:
            ledger.DEPLOY_ROOT = original_deploy
            intake_manifest.staging_dir = original_staging
    assert result["lifecycle"] == "BLOCKED"
    assert any("fingerprint" in item for item in result["failures"])
    _zero(client)
    assert manifest == before
    changed = _release(weekly_announcements=[])
    changed["owner_publication_time"] = "2026-11-12T21:00:00Z"
    changed["plan_fingerprint"] = plan_fingerprint({"weekly_announcements": [{"delayed_post_at": FUTURE}]})
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        original_deploy = ledger.DEPLOY_ROOT
        original_staging = intake_manifest.staging_dir
        ledger.DEPLOY_ROOT = root / "deployments"
        intake_manifest.staging_dir = lambda q, w: root / "intake" / f"q{q}w{w}"
        _seed_source(root)
        ledger.write_preflight(2, 5, {
            "preflight_id": "pf2", "created_at": NOW.isoformat(),
            "expires_at": "2099-01-01T00:00:00+00:00", "quarter": 2, "week": 5,
            "week_code": "Q2W5", "source_hash": SOURCE, "approval_snapshot_hash": "appr",
            "plan": {"weekly_announcements": [{"delayed_post_at": "2026-11-14T21:00:00Z"}]},
            "ready": True, "canvas_writes": 0, "blockers": [],
        })
        client = _client()
        try:
            result = _execute(changed, client)
        finally:
            ledger.DEPLOY_ROOT = original_deploy
            intake_manifest.staging_dir = original_staging
    assert result["lifecycle"] == "BLOCKED"
    _zero(client)


def test_offset_equivalent_future_timestamp_is_accepted_by_parser():
    parsed = rollover._parse_aware_instant(FUTURE)
    offset = rollover._parse_aware_instant(FUTURE_OFFSET)
    assert parsed == offset
    assert rollover._future_schedule_blocker(
        {"schedule_state": "FUTURE_SCHEDULED", "delayed_post_at": FUTURE_OFFSET},
        now=NOW, label="notice",
    ) is None


class NormalizingClient(FakeDeployClient):
    """Runs the production normalizer on every announcement read."""

    def get_announcement(self, course_id, topic_id):
        raw = self.announcements.get(str(topic_id))
        if raw is None:
            raise DeployClientError(f"announcement not found: {topic_id}")
        normalized = LiveDeployClient._norm_announcement(object.__new__(LiveDeployClient), dict(raw))
        self._write_counts["GET"] += 1
        return normalized


def _verify(raw, *, title="T", message="<p>Hello.</p>", delayed=FUTURE, scheduled=True, course=28171):
    client = NormalizingClient(courses={course: {"id": course, "name": "Language Arts"}})
    client.announcements["topic-1"] = {"id": "topic-1", **raw}
    counts = {"GET": 0}
    ok, detail, state = coordinator._verify_announcement(
        client, course, "topic-1", title=title, scheduled=scheduled,
        delayed_post_at=delayed, expect_agenda=False, counts=counts,
        expected_message=message,
    )
    disposition = coordinator.announcement_readback_disposition(
        scheduled=scheduled, verified=ok, state=state,
    )
    return ok, state, disposition, detail


def test_live_normalizer_readback_matrix():
    message = "<p>Hello.</p>"
    base = {
        "course_id": 28171, "title": "T", "message": message, "published": True,
        "delayed_post_at": FUTURE, "posted_at": None, "extra": "dropped",
    }
    ok, state, disposition, detail = _verify(base)
    assert ok and state == "HELD_SCHEDULED" and disposition == "SCHEDULED_VERIFIED", detail
    ok, state, disposition, _detail = _verify({**base, "delayed_post_at": FUTURE_OFFSET}, delayed=FUTURE)
    assert ok and disposition == "SCHEDULED_VERIFIED"
    assert disposition != "PUBLISHED_VERIFIED"
    ok, _state, disposition, _detail = _verify({**base, "course_id": None})
    assert ok is False and disposition != "PUBLISHED_VERIFIED"
    ok, _state, disposition, _detail = _verify({**base, "course_id": 26404})
    assert ok is False and disposition != "PUBLISHED_VERIFIED"
    ok, _state, disposition, _detail = _verify(base, title="Other")
    assert ok is False
    ok, _state, disposition, _detail = _verify(base, message="<p>Other.</p>")
    assert ok is False
    ok, _state, disposition, _detail = _verify({**base, "delayed_post_at": None}, delayed=FUTURE)
    assert ok is False and disposition != "PUBLISHED_VERIFIED"
    ok, _state, disposition, _detail = _verify(
        {**base, "delayed_post_at": PAST, "posted_at": PAST}, delayed=FUTURE,
    )
    assert ok is False and disposition != "PUBLISHED_VERIFIED"
    published = {
        "course_id": 28171, "title": "T", "message": message, "published": True,
        "delayed_post_at": None, "posted_at": "2026-11-07T18:00:00Z",
    }
    ok, state, disposition, detail = _verify(published, delayed=None, scheduled=False)
    assert ok and state == "POSTED" and disposition == "PUBLISHED_VERIFIED", detail


def test_coordinator_past_future_label_and_uncertain_write_do_not_retry():
    message = "<p>Chapter 7 on Friday.</p>"
    plan = {
        "quarter": 2, "week": 5, "week_code": "Q2W5", "slug": "q2w5",
        "date_range": {"start": "2026-11-09", "end": "2026-11-13"},
        "status": "READY_TO_PUBLISH", "ready_to_publish": True, "publish_blockers": [],
        "source_hash": "src", "approval_snapshot_hash": "appr",
        "pages": [], "assignments": [], "deletes": [], "untouched": {},
        "weekly_announcements": [], "counts": {},
        "assessment_reminders": [{
            "title": "Reminder", "course_id": 28171, "message": message,
            "scheduled": True, "delayed_post_at": PAST, "schedule_state": "FUTURE_SCHEDULED",
            "action": "CREATE", "content_status": "READY", "approved": True,
        }],
    }
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        original_deploy = ledger.DEPLOY_ROOT
        original_staging = intake_manifest.staging_dir
        ledger.DEPLOY_ROOT = root / "deployments"
        intake_manifest.staging_dir = lambda q, w: root / f"q{q}w{w}"
        from scripts.canvas_llm_deploy import plan as plan_mod
        original_build = plan_mod.build_plan
        plan_mod.build_plan = lambda *args, **kwargs: plan
        try:
            record = intake_manifest.new_manifest(
                quarter=2, week=5, week_code="Q2W5", date_range=plan["date_range"],
            )
            record["status"] = "READY_TO_PUBLISH"
            record["source_hash"] = "src"
            intake_manifest.save_manifest(2, 5, record)
            ledger.write_preflight(2, 5, {
                "preflight_id": "pf", "created_at": NOW.isoformat(),
                "expires_at": "2099-01-01T00:00:00+00:00", "quarter": 2, "week": 5,
                "week_code": "Q2W5", "source_hash": "src", "approval_snapshot_hash": "appr",
                "plan": plan, "ready": True, "canvas_writes": 0, "blockers": [],
            })
            client = NormalizingClient(courses={28171: {"id": 28171, "name": "Language Arts"}})
            result = coordinator.deploy(
                2, 5, preflight_id="pf", expected_source_hash="src",
                expected_approval_snapshot_hash="appr", owner_confirmation="DEPLOY Q2W5",
                client=client, now=NOW,
            )
            assert result["deployment_state"] == "BLOCKED", result
            _zero(client)
        finally:
            plan_mod.build_plan = original_build
            ledger.DEPLOY_ROOT = original_deploy
            intake_manifest.staging_dir = original_staging

    future_plan = copy.deepcopy(plan)
    future_plan["assessment_reminders"][0]["delayed_post_at"] = FUTURE
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        original_deploy = ledger.DEPLOY_ROOT
        original_staging = intake_manifest.staging_dir
        ledger.DEPLOY_ROOT = root / "deployments"
        intake_manifest.staging_dir = lambda q, w: root / f"q{q}w{w}"
        from scripts.canvas_llm_deploy import plan as plan_mod
        original_build = plan_mod.build_plan
        plan_mod.build_plan = lambda *args, **kwargs: future_plan
        try:
            record = intake_manifest.new_manifest(
                quarter=2, week=5, week_code="Q2W5", date_range=future_plan["date_range"],
            )
            record["status"] = "READY_TO_PUBLISH"
            record["source_hash"] = "src"
            intake_manifest.save_manifest(2, 5, record)
            ledger.write_preflight(2, 5, {
                "preflight_id": "pf", "created_at": NOW.isoformat(),
                "expires_at": "2099-01-01T00:00:00+00:00", "quarter": 2, "week": 5,
                "week_code": "Q2W5", "source_hash": "src", "approval_snapshot_hash": "appr",
                "plan": future_plan, "ready": True, "canvas_writes": 0, "blockers": [],
            })

            class Uncertain(NormalizingClient):
                def get_announcement(self, course_id, topic_id):
                    raw = dict(self.announcements[str(topic_id)])
                    raw.pop("course_id", None)
                    normalized = LiveDeployClient._norm_announcement(
                        object.__new__(LiveDeployClient), raw,
                    )
                    self._write_counts["GET"] += 1
                    if normalized.get("course_id") != course_id:
                        raise DeployClientError("course id missing after normalization")
                    return normalized

            client = Uncertain(courses={28171: {"id": 28171, "name": "Language Arts"}})
            result = coordinator.deploy(
                2, 5, preflight_id="pf", expected_source_hash="src",
                expected_approval_snapshot_hash="appr", owner_confirmation="DEPLOY Q2W5",
                client=client, now=NOW,
            )
            assert result["deployment_state"] != "PUBLISHED_VERIFIED"
            assert client._write_counts["POST"] == 1
            assert client._write_counts["PUT"] == 0
            assert client._write_counts["DELETE"] == 0
        finally:
            plan_mod.build_plan = original_build
            ledger.DEPLOY_ROOT = original_deploy
            intake_manifest.staging_dir = original_staging


def test_complete_five_course_fake_deployment_schedules_without_publishing():
    manifest = _release()
    rendered_hash = manifest["homeroom"]["proposed_content_hash"]
    family_message = f"<p>Family newsletter</p><!--{rendered_hash}-->"
    manifest["homeroom_announcement"] = {
        "title": "4th Grade Family Update",
        "course_id": COURSES["homeroom"],
        "page_id": manifest["homeroom"]["to_page_id"],
        "schedule_state": "FUTURE_SCHEDULED",
        "scheduled": True,
        "delayed_post_at": FUTURE_OFFSET,
        "approval_state": "APPROVED",
        "approved": True,
        "action": "CREATE",
        "publication_dependency": "HOMEROOM_PAGE_PUBLISHED_AND_VERIFIED",
        "contains_complete_newsletter_html": True,
        "message": family_message,
    }
    manifest["owner_publication_time"] = FUTURE
    manifest["assessment_reminders"] = [{
        "title": "Spelling Test 55", "course_id": COURSES["reading_spelling"],
        "subject": "reading_spelling", "message": "<p>Spelling Test 55.</p>",
        "schedule_state": "FUTURE_SCHEDULED", "scheduled": True,
        "delayed_post_at": FUTURE, "approved": True, "content_status": "READY",
        "action": "CREATE",
    }]
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        original_deploy = ledger.DEPLOY_ROOT
        original_staging = intake_manifest.staging_dir
        ledger.DEPLOY_ROOT = root / "deployments"
        intake_manifest.staging_dir = lambda q, w: root / "intake" / f"q{q}w{w}"
        _seed_source(root)
        client = _client()
        order = []
        original_update = client.update_page
        original_create = client.create_announcement

        def update_page(*args, **kwargs):
            order.append(("page", args[0]))
            return original_update(*args, **kwargs)

        def create_announcement(*args, **kwargs):
            order.append(("announcement", args[0], kwargs.get("title")))
            return original_create(*args, **kwargs)

        client.update_page = update_page
        client.create_announcement = create_announcement
        try:
            result = _execute(manifest, client)
        finally:
            ledger.DEPLOY_ROOT = original_deploy
            intake_manifest.staging_dir = original_staging
    assert result["lifecycle"] == "PUBLISHED_VERIFIED", result.get("failures")
    assert {page["subject"] for page in result["pages"]} == set(LABELS)
    assert result["homeroom"]["verified"] is True
    homeroom_page = next(index for index, item in enumerate(order) if item[0] == "page" and item[1] == COURSES["homeroom"])
    family = next(index for index, item in enumerate(order) if item[0] == "announcement" and item[1] == COURSES["homeroom"])
    assert homeroom_page < family
    assert result["homeroom_announcement"]["disposition"] == "SCHEDULED_VERIFIED"
    for record in result["weekly_announcements"]:
        assert record["disposition"] == "SCHEDULED_VERIFIED"
        assert record["disposition"] != "PUBLISHED_VERIFIED"
    assert result["assessment_reminders"][0]["disposition"] == "SCHEDULED_VERIFIED"


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
