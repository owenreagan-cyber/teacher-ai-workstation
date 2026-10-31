"""Weekly Homeroom newsletter page regression tests (plain python).

Hermetic: redirects the intake staging + deployment ledger roots to temporary
directories; never touches real .local state or Canvas.
"""
import sys
from pathlib import Path

if str(Path(__file__).resolve().parents[2]) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import hashlib
import tempfile

from scripts.canvas_llm_deploy import ledger as deploy_ledger
from scripts.canvas_llm_deploy.client import FakeDeployClient
from scripts.canvas_llm_intake import manifest as intake_manifest
from scripts.canvas_llm_rollover import homeroom_weekly, rollover, schedule

COURSE_ID = 26429
PAGE_ID = 798094
SLUG = "q2w4-november-2-6-2026"
WEEK = "Q2W4"
HTML = '<div style="max-width: 900px;"><h1>4th Grade Happenings</h1><h2>🍂 November Birthdays 🎉</h2></div>'


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _tmp():
    orig_deploy = deploy_ledger.DEPLOY_ROOT
    orig_staging = intake_manifest.staging_dir
    tmp = tempfile.TemporaryDirectory()
    deploy_ledger.DEPLOY_ROOT = Path(tmp.name) / "deployments"
    intake_manifest.staging_dir = lambda q, w: Path(tmp.name) / "intake" / f"q{q}w{w}"
    return orig_deploy, orig_staging, tmp


def _page_record():
    return {
        "schemaVersion": 1, "week": WEEK, "course_id": COURSE_ID,
        "slug": SLUG, "page_id": PAGE_ID, "title": "Q2W4 - November 2–6, 2026",
        "front_page": False, "published": True, "status": "FOUND",
        "method": "LIVE_GET",
    }


def _record(*, body=HTML):
    homeroom_weekly.write_page_resolution(2, 4, _page_record())
    return homeroom_weekly.record_approval(
        2, 4, page_id=PAGE_ID, page_slug=SLUG, week_code_value=WEEK,
        source_body_hash="src", approved_body_hash=_sha(body), body=body,
    )


def test_hash_binding():
    orig_deploy, orig_staging, tmp = _tmp()
    try:
        _record()
        ok, _ = homeroom_weekly.verify(2, 4)
        assert ok
        homeroom_weekly.html_path(2, 4).write_text(HTML + "x", encoding="utf-8")
        ok2, _ = homeroom_weekly.verify(2, 4)
        assert not ok2
    finally:
        tmp.cleanup()
        deploy_ledger.DEPLOY_ROOT = orig_deploy
        intake_manifest.staging_dir = orig_staging


def test_page_id_and_week_binding():
    orig_deploy, orig_staging, tmp = _tmp()
    try:
        _record()
        # Wrong week cannot verify.
        ok, _ = homeroom_weekly.verify_at(
            intake_manifest.staging_dir(2, 4), course_id=COURSE_ID, week_code_value="Q2W5",
        )
        assert not ok
        # Wrong course cannot verify.
        ok2, _ = homeroom_weekly.verify_at(
            intake_manifest.staging_dir(2, 4), course_id=28171, week_code_value=WEEK,
        )
        assert not ok2
    finally:
        tmp.cleanup()
        deploy_ledger.DEPLOY_ROOT = orig_deploy
        intake_manifest.staging_dir = orig_staging


def test_manifest_routes_to_weekly_approval():
    orig_deploy, orig_staging, tmp = _tmp()
    try:
        _record()
        from scripts.canvas_llm_rollover import manifest as rm
        m = rm.build_rollover_manifest(2, 3, 2, 4)
        h = m["homeroom"]
        assert h["mode"] == homeroom_weekly.KIND
        assert h["to_page_id"] == PAGE_ID
        assert h["to_page_slug"] == SLUG
        assert h["approved"] is True
        assert h["body"] == HTML
        assert h["proposed_content_hash"] == _sha(HTML)
    finally:
        tmp.cleanup()
        deploy_ledger.DEPLOY_ROOT = orig_deploy
        intake_manifest.staging_dir = orig_staging


def test_manifest_unapproved_without_weekly_approval():
    orig_deploy, orig_staging, tmp = _tmp()
    try:
        from scripts.canvas_llm_rollover import manifest as rm
        m = rm.build_rollover_manifest(2, 3, 2, 4)
        h = m["homeroom"]
        assert h["mode"] == homeroom_weekly.KIND
        assert h["approved"] is False
        assert h["to_page_id"] is None
    finally:
        tmp.cleanup()
        deploy_ledger.DEPLOY_ROOT = orig_deploy
        intake_manifest.staging_dir = orig_staging


def test_execute_updates_existing_weekly_page_not_rolling_page():
    orig_deploy, orig_staging, tmp = _tmp()
    try:
        c = FakeDeployClient(courses={COURSE_ID: {"id": COURSE_ID, "name": "Homeroom"}})
        weekly = c.seed_page(COURSE_ID, SLUG, title="Q2W4 - November 2–6, 2026",
                             body="<p>old</p>", front_page=False)
        weekly["page_id"] = PAGE_ID
        rolling = c.seed_page(COURSE_ID, "class-4a-newsletter-october-19-23-2026",
                              title="Class 4A Newsletter", body="<p>rolling</p>", front_page=True)
        m = {
            "from_week": "Q2W3", "to_week": "Q2W4",
            "scheduled_at": "2026-10-30T20:00:00Z", "timezone": "America/New_York",
            "academic_courses": [],
            "homeroom": {
                "course_id": COURSE_ID, "to_page_id": PAGE_ID,
                "to_page_slug": SLUG, "front_page_action": "SET_FRONT_PAGE",
                "source_content_hash": "src",
                "proposed_content_hash": _sha(HTML),
                "body": HTML,
                "mode": homeroom_weekly.KIND,
                "approved": True,
            },
            "weekly_announcements": [], "assignments": [], "assessment_reminders": [],
        }
        r = rollover.execute(2, 3, 2, 4, client=c, owner_confirmation="ROLLOVER Q2W4", manifest=m)
        assert r["lifecycle"] == schedule.PUBLISHED_VERIFIED, r.get("failures")
        assert r["homeroom"]["verified"] is True
        page = c.get_page(COURSE_ID, SLUG)
        assert page["body"].strip().startswith("<div")
        assert page["front_page"] is True
        # Retired rolling page is untouched and no new page created.
        rolling_now = c.get_page(COURSE_ID, "class-4a-newsletter-october-19-23-2026")
        assert rolling_now["body"] == "<p>rolling</p>"
        assert rolling_now["front_page"] is False
        assert len(c.pages) == 2
    finally:
        tmp.cleanup()
        deploy_ledger.DEPLOY_ROOT = orig_deploy
        intake_manifest.staging_dir = orig_staging


def _run():
    fns = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    failed = 0
    for name, fn in fns:
        try:
            fn()
            print(f"PASS {name}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"FAIL {name}: {e}")
    print(f"RESULT: {len(fns) - failed} passed, {failed} failed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    _run()
