"""End-to-end rollover regression tests (idempotency, partial failure).

Plain-python runnable; hermetic (redirects the deployment ledger root to a
temporary directory; never touches real .local state or Canvas).
"""
import sys
from pathlib import Path

if str(Path(__file__).resolve().parents[2]) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import tempfile
import hashlib

from scripts.canvas_llm_deploy import ledger as deploy_ledger
from scripts.canvas_llm_deploy.client import FakeDeployClient
from scripts.canvas_llm_intake import manifest as intake_manifest
from scripts.canvas_llm_rollover import rollover, schedule

SLUG = "q2w3-october-26-30-2026"
SUBJECTS = ("math", "reading_spelling", "language_arts", "science")
LABELS = {"math": "Math", "reading_spelling": "Reading/Spelling",
          "language_arts": "Language Arts", "science": "Science"}
COURSES = {"math": 26404, "reading_spelling": 26442,
           "language_arts": 28171, "science": 28166, "homeroom": 26429}


def _manifest():
    from scripts.canvas_llm_rollover import homeroom
    proposed_homeroom = {"classMotto": {"motto": "Level Up Together."}}
    def page_body(subject):
        return f'<div class="kl_wrapper_3"><h2>{LABELS[subject]}</h2><h3>Reminders</h3></div>'
    academic = [
        {"subject": s, "label": LABELS[s], "course_id": COURSES[s],
         "to_page_slug": SLUG, "front_page_action": "SET_FRONT_PAGE",
         "page_body": page_body(s),
         "to_page_hash": hashlib.sha256(page_body(s).encode()).hexdigest(),
         "approved": True}
        for s in SUBJECTS
    ]
    anns = [
        {"subject": s, "label": LABELS[s], "course_id": COURSES[s],
         "title": f"{LABELS[s]} Canvas Weekly Update", "week_code": "Q2W3",
         "agenda_hash": "h", "page_agenda_hash": "h", "hash_consistent": True,
         "body_hash": "h", "message": f"<p>Good afternoon,</p><p>{LABELS[s]} agenda</p><p>Mr. Reagan</p>",
         "delayed_post_at": "2026-10-23T20:00:00Z", "classification": "NEW", "action": "CREATE"}
        for s in SUBJECTS
    ]
    return {
        "from_week": "Q2W2", "to_week": "Q2W3",
        "scheduled_at": "2026-10-23T20:00:00Z", "timezone": "America/New_York",
        "academic_courses": academic,
        "homeroom": {
            "course_id": 26429, "to_page_slug": SLUG, "front_page_action": "SET_FRONT_PAGE",
            "source_content_hash": "src",
            "proposed_content_hash": hashlib.sha256(
                homeroom.render_proposed(proposed_homeroom).encode()
            ).hexdigest(),
            "proposed_content": proposed_homeroom,
        },
        "weekly_announcements": anns,
        "assignments": [{
            "course": "math", "course_id": COURSES["math"], "title": "Math Lesson 41",
            "assignment_group": "Classwork", "points_possible": 100,
            "grading_type": "percent", "submission_types": ["on_paper"],
            "due_utc": "2026-10-27T03:59:00Z", "omit_from_final_grade": False,
        }],
        "assessment_reminders": [{
            "subject": "math", "course_id": COURSES["math"], "title": "Math test reminder",
            "message": "<p>Math test Monday.</p>",
        }],
    }


def _client(*, skip=None):
    skip = set(skip or [])
    courses = {cid: {"id": cid, "name": n} for cid, n in [
        (26404, "Math"), (26442, "Reading/Spelling"), (28171, "Language Arts"),
        (28166, "Science"), (26429, "Homeroom")]}
    c = FakeDeployClient(courses=courses)
    c.assignment_groups[COURSES["math"]] = [{"id": "group-1", "name": "Classwork"}]
    for s in SUBJECTS:
        if s in skip:
            continue
        c.seed_page(COURSES[s], SLUG, title=f"Q2W3 {LABELS[s]}", body="", front_page=False)
    # Homeroom: current front page (Q2W2) + upcoming page (Q2W3).
    c.seed_page(26429, "q2w2-old", title="Homeroom Q2W2", body="<p>old</p>", front_page=True)
    c.seed_page(26429, SLUG, title="Homeroom Q2W3", body="", front_page=False)
    return c


def _tmp_ledger():
    orig = deploy_ledger.DEPLOY_ROOT
    orig_staging = intake_manifest.staging_dir
    tmp = tempfile.TemporaryDirectory()
    deploy_ledger.DEPLOY_ROOT = Path(tmp.name) / "deployments"
    intake_manifest.staging_dir = lambda q, w: Path(tmp.name) / "intake" / f"q{q}w{w}"
    return orig, orig_staging, tmp


def test_happy_path_published_verified():
    orig, orig_staging, tmp = _tmp_ledger()
    try:
        c = _client()
        r = rollover.execute(2, 2, 2, 3, client=c, owner_confirmation="ROLLOVER Q2W3",
                             manifest=_manifest())
        assert r["lifecycle"] == schedule.PUBLISHED_VERIFIED, r.get("failures")
        # Academic front pages flipped.
        assert len(r["academic_front_pages"]) == 4
        for rec in r["academic_front_pages"]:
            assert rec["verified"] is True
        # Homeroom: body copied + front page set + old page intact.
        assert r["homeroom"]["verified"] is True
        assert c.get_page(26429, SLUG)["front_page"] is True
        old = c.get_page(26429, "q2w2-old")
        assert old["body"] == "<p>old</p>" and old["front_page"] is False
        # Announcements created + held scheduled.
        assert len(r["weekly_announcements"]) == 4
        for rec in r["weekly_announcements"]:
            assert rec["state"] == "HELD_SCHEDULED"
        assert r["pages"] and all(item["verified"] for item in r["pages"])
        assert r["assignments"][0]["verified"] is True
        assert r["assessment_reminders"][0]["verified"] is True
        assert c.get_page(COURSES["math"], SLUG)["body"] == _manifest()["academic_courses"][0]["page_body"]
    finally:
        tmp.cleanup()
        deploy_ledger.DEPLOY_ROOT = orig
        intake_manifest.staging_dir = orig_staging


def test_idempotent_rerun_skips():
    orig, orig_staging, tmp = _tmp_ledger()
    try:
        c = _client()
        m = _manifest()
        r1 = rollover.execute(2, 2, 2, 3, client=c, owner_confirmation="ROLLOVER Q2W3", manifest=m)
        assert r1["lifecycle"] == schedule.PUBLISHED_VERIFIED
        r2 = rollover.execute(2, 2, 2, 3, client=c, owner_confirmation="ROLLOVER Q2W3", manifest=m)
        assert r2.get("already_complete") is True
    finally:
        tmp.cleanup()
        deploy_ledger.DEPLOY_ROOT = orig
        intake_manifest.staging_dir = orig_staging


def test_partial_failure_blocks():
    orig, orig_staging, tmp = _tmp_ledger()
    try:
        c = _client(skip={"science"})
        r = rollover.execute(2, 2, 2, 3, client=c, owner_confirmation="ROLLOVER Q2W3",
                             manifest=_manifest())
        assert r["lifecycle"] == schedule.BLOCKED
        assert any("science" in f for f in r["failures"])
        assert "recovery" in r
    finally:
        tmp.cleanup()
        deploy_ledger.DEPLOY_ROOT = orig
        intake_manifest.staging_dir = orig_staging


def test_confirmation_gate_blocks():
    orig, orig_staging, tmp = _tmp_ledger()
    try:
        c = _client()
        try:
            rollover.execute(2, 2, 2, 3, client=c, owner_confirmation="DEPLOY Q2W3",
                             manifest=_manifest())
            raise AssertionError("expected RolloverBlocked")
        except rollover.RolloverBlocked:
            pass
    finally:
        tmp.cleanup()
        deploy_ledger.DEPLOY_ROOT = orig
        intake_manifest.staging_dir = orig_staging


def _run():
    import sys
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
