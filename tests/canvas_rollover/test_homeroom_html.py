"""Rolling-newsletter HTML approval bridge regression tests (plain-python).

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
from scripts.canvas_llm_rollover import homeroom_html, rollover, schedule

ROLLING_SLUG = "class-4a-newsletter-october-19-23-2026"
PAGE_ID = 798072
COURSE_ID = 26429
HTML = (
    '<div style="max-width: 900px;">'
    '<h1>4th Grade Happenings</h1>'
    '<h2>📚 Book Character Day — Friday, October 30</h2>'
    '<p>Book Character Day is Friday, October 30!</p>'
    '</div>'
)


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _tmp():
    orig_deploy = deploy_ledger.DEPLOY_ROOT
    orig_staging = intake_manifest.staging_dir
    tmp = tempfile.TemporaryDirectory()
    deploy_ledger.DEPLOY_ROOT = Path(tmp.name) / "deployments"
    intake_manifest.staging_dir = lambda q, w: Path(tmp.name) / "intake" / f"q{q}w{w}"
    return orig_deploy, orig_staging, tmp


def _record(*, body=HTML):
    homeroom_html.record_approval(
        2, 3, course_id=COURSE_ID, page_id=PAGE_ID, page_slug=ROLLING_SLUG,
        source_body_hash="src", approved_body_hash=_sha(body),
        week_code="Q2W3", body=body,
    )


def test_hash_binding():
    _record()
    ok, _ = homeroom_html.verify(2, 3, course_id=COURSE_ID, page_id=PAGE_ID, week_code="Q2W3")
    assert ok
    # B: one-byte body change invalidates.
    p = homeroom_html.html_path(2, 3)
    p.write_text(HTML + "x", encoding="utf-8")
    ok2, _ = homeroom_html.verify(2, 3, course_id=COURSE_ID, page_id=PAGE_ID, week_code="Q2W3")
    assert not ok2
    p.write_text(HTML, encoding="utf-8")
    ok3, _ = homeroom_html.verify(2, 3, course_id=COURSE_ID, page_id=PAGE_ID, week_code="Q2W3")
    assert ok3


def test_page_id_and_week_binding():
    _record()
    # C: page id change invalidates.
    ok, _ = homeroom_html.verify(2, 3, course_id=COURSE_ID, page_id=999999, week_code="Q2W3")
    assert not ok
    # week change invalidates.
    ok2, _ = homeroom_html.verify(2, 3, course_id=COURSE_ID, page_id=PAGE_ID, week_code="Q2W4")
    assert not ok2
    # course change invalidates.
    ok3, _ = homeroom_html.verify(2, 3, course_id=28171, page_id=PAGE_ID, week_code="Q2W3")
    assert not ok3


def test_manifest_routes_to_html_approval():
    orig_deploy, orig_staging, tmp = _tmp()
    try:
        _record()
        from scripts.canvas_llm_rollover import manifest as rm
        m = rm.build_rollover_manifest(2, 2, 2, 3)
        h = m["homeroom"]
        # D: rolling target is page 798072, not the weekly page slug.
        assert h["mode"] == "rolling_newsletter_html"
        assert h["to_page_id"] == PAGE_ID
        assert h["to_page_slug"] == ROLLING_SLUG
        assert h["approved"] is True
        # E: production body is HTML, not JSON.
        body = h["body"]
        assert body.strip().startswith("<div"), body[:40]
        assert "Book Character Day" in body
        assert h["proposed_content"] is None
        assert h["proposed_content_hash"] == _sha(HTML)
    finally:
        tmp.cleanup()
        deploy_ledger.DEPLOY_ROOT = orig_deploy
        intake_manifest.staging_dir = orig_staging


def test_manifest_falls_back_when_no_html_approval():
    orig_deploy, orig_staging, tmp = _tmp()
    try:
        from scripts.canvas_llm_rollover import manifest as rm
        m = rm.build_rollover_manifest(2, 2, 2, 3)
        h = m["homeroom"]
        # No HTML approval -> JSON proposal fallback (not approved).
        assert h.get("mode") != "rolling_newsletter_html"
        assert h["approved"] is False
    finally:
        tmp.cleanup()
        deploy_ledger.DEPLOY_ROOT = orig_deploy
        intake_manifest.staging_dir = orig_staging


def test_execute_writes_html_preserves_front_page_no_new_page():
    orig_deploy, orig_staging, tmp = _tmp()
    try:
        _record()
        c = FakeDeployClient(courses={COURSE_ID: {"id": COURSE_ID, "name": "Homeroom"}})
        c.seed_page(COURSE_ID, ROLLING_SLUG, title="Class 4A Newsletter",
                    body="<p>old</p>", front_page=True)
        # Make the seeded page id match the approved rolling page id.
        c.pages[(COURSE_ID, ROLLING_SLUG)]["page_id"] = PAGE_ID
        # A weekly agenda page that must NOT receive the newsletter.
        c.seed_page(COURSE_ID, "q2w3-october-26-30-2026", title="Q2W3", body="", front_page=False)

        m = {
            "from_week": "Q2W2", "to_week": "Q2W3",
            "scheduled_at": "2026-10-23T20:00:00Z", "timezone": "America/New_York",
            "academic_courses": [],
            "homeroom": {
                "course_id": COURSE_ID, "to_page_id": PAGE_ID,
                "to_page_slug": ROLLING_SLUG, "front_page_action": "SET_FRONT_PAGE",
                "source_content_hash": "src",
                "proposed_content_hash": _sha(HTML),
                "proposed_content": None,
                "body": HTML,
                "mode": "rolling_newsletter_html",
                "approved": True,
            },
            "weekly_announcements": [], "assignments": [], "assessment_reminders": [],
        }
        r = rollover.execute(2, 2, 2, 3, client=c, owner_confirmation="ROLLOVER Q2W3", manifest=m)
        assert r["lifecycle"] == schedule.PUBLISHED_VERIFIED, r.get("failures")
        assert r["homeroom"]["verified"] is True
        # F: body written to the rolling page is the HTML, not JSON.
        page = c.get_page(COURSE_ID, ROLLING_SLUG)
        assert page["body"].strip().startswith("<div")
        assert "Book Character Day" in page["body"]
        # G: rolling page remains front page; weekly page untouched.
        assert page["front_page"] is True
        weekly = c.get_page(COURSE_ID, "q2w3-october-26-30-2026")
        assert weekly["body"] == "" and weekly["front_page"] is False
        # No new page was created (still exactly the two seeded pages).
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
