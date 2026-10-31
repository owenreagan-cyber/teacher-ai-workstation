"""Assignment CREATE/UPDATE/SKIP/BLOCKED execution tests.

Hermetic: fake Canvas store + temporary deployment ledger. No Canvas I/O.
"""
import sys
from pathlib import Path

if str(Path(__file__).resolve().parents[2]) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import tempfile

from scripts.canvas_llm_deploy import ledger as deploy_ledger
from scripts.canvas_llm_deploy.client import FakeDeployClient
from scripts.canvas_llm_intake import manifest as intake_manifest
from scripts.canvas_llm_rollover import ledger as rollover_ledger
from scripts.canvas_llm_rollover import rollover, schedule

MATH = 26404
ELA = 28171


def _base_manifest(assignments):
    return {
        "from_week": "Q2W3", "to_week": "Q2W4",
        "scheduled_at": "2026-10-30T20:00:00Z", "timezone": "America/New_York",
        "academic_courses": [], "homeroom": None,
        "weekly_announcements": [], "assessment_reminders": [],
        "assignments": assignments,
    }


def _update(title, assignment_id, due_utc, *, subject="language_arts", cid=ELA):
    return {
        "course": subject, "course_id": cid, "title": title,
        "assignment_group": "Classwork", "points_possible": 100,
        "grading_type": "percent", "submission_types": ["on_paper"],
        "due_utc": due_utc, "omit_from_final_grade": False,
        "action": "UPDATE", "assignment_id": assignment_id,
        "corrections": {"due_at": {"actual": "2026-10-30T03:59:00Z", "required": due_utc}},
    }


def _create(title, due_utc, *, subject="math", cid=MATH):
    return {
        "course": subject, "course_id": cid, "title": title,
        "assignment_group": "Classwork", "points_possible": 100,
        "grading_type": "percent", "submission_types": ["on_paper"],
        "due_utc": due_utc, "omit_from_final_grade": False, "action": "CREATE",
    }


def _client(*, with_updates=True):
    c = FakeDeployClient(courses={MATH: {"id": MATH}, ELA: {"id": ELA}})
    c.assignment_groups[MATH] = [{"id": "math-group", "name": "Classwork"}]
    c.assignment_groups[ELA] = [{"id": "ela-classwork", "name": "Classwork"}]
    c.assignment_groups[26442] = [{"id": "reading-group", "name": "Classwork"}]
    c.assignment_groups[28166] = [{"id": "science-group", "name": "Classwork"}]
    if with_updates:
        c.assignments["1052514"] = {
            "id": "1052514", "course_id": ELA, "name": "Classroom Practice 26",
            "assignment_group_id": "ela-classwork", "points_possible": 100,
            "grading_type": "percent", "submission_types": ["on_paper"],
            "due_at": "2026-10-30T03:59:00Z", "omit_from_final_grade": False,
            "published": True,
        }
        c.assignments["1052515"] = {
            "id": "1052515", "course_id": ELA, "name": "Classroom Practice 27",
            "assignment_group_id": "ela-classwork", "points_possible": 100,
            "grading_type": "percent", "submission_types": ["on_paper"],
            "due_at": "2026-10-31T03:59:00Z", "omit_from_final_grade": False,
            "published": True,
        }
    return c


def _tmp_ledger():
    orig = deploy_ledger.DEPLOY_ROOT
    orig_staging = intake_manifest.staging_dir
    tmp = tempfile.TemporaryDirectory()
    deploy_ledger.DEPLOY_ROOT = Path(tmp.name) / "deployments"
    intake_manifest.staging_dir = lambda q, w: Path(tmp.name) / "intake" / f"q{q}w{w}"
    return orig, orig_staging, tmp


def _twelve_actions():
    return [
        _update("Classroom Practice 26", "1052514", "2026-11-03T04:59:00Z"),
        _update("Classroom Practice 27", "1052515", "2026-11-05T04:59:00Z"),
        _create("SM5: Lesson 41 Homework", "2026-11-03T04:59:00Z"),
        _create("SM5: Lesson 42 Classwork", "2026-11-04T04:59:00Z"),
        _create("SM5: Lesson 43 Homework", "2026-11-05T04:59:00Z"),
        _create("RM4: Monday Workbook Classwork — Lesson 50", "2026-11-03T04:59:00Z",
                subject="reading_spelling", cid=26442),
        _create("RM4: Mastery Test 5", "2026-11-04T04:59:00Z",
                subject="reading_spelling", cid=26442),
        _create("RM4: Fluency Checkout 5", "2026-11-04T04:59:00Z",
                subject="reading_spelling", cid=26442),
        _create("RM4: Thursday Comprehension Questions — Lesson 52", "2026-11-06T04:59:00Z",
                subject="reading_spelling", cid=26442),
        _create("RM4: Spelling Test 50", "2026-11-07T04:59:00Z",
                subject="reading_spelling", cid=26442),
        _create("Science: Energy Transformations Unit Test", "2026-11-06T04:59:00Z",
                subject="science", cid=28166),
    ]


def _run(c, assignments, *, confirm="ROLLOVER Q2W4"):
    return rollover.execute(2, 3, 2, 4, client=c, owner_confirmation=confirm,
                            manifest=_base_manifest(assignments))


def test_existing_wrong_due_updates_in_place():
    orig, orig_staging, tmp = _tmp_ledger()
    try:
        c = _client()
        r = _run(c, [_update("Classroom Practice 26", "1052514", "2026-11-03T04:59:00Z")])
        assert r["lifecycle"] == schedule.PUBLISHED_VERIFIED, r.get("failures")
        assert r["assignments"][0]["disposition"] == "UPDATED_VERIFIED"
        assert c.get_assignment(ELA, "1052514")["due_at"] == "2026-11-03T04:59:00Z"
        assert len([a for a in c.assignments.values()
                    if a["course_id"] == ELA and a["name"] == "Classroom Practice 26"]) == 1
    finally:
        tmp.cleanup(); deploy_ledger.DEPLOY_ROOT = orig
        intake_manifest.staging_dir = orig_staging


def test_cp26_updates_1052514_only():
    orig, orig_staging, tmp = _tmp_ledger()
    try:
        c = _client()
        r = _run(c, [_update("Classroom Practice 26", "1052514", "2026-11-03T04:59:00Z")])
        assert r["assignments"][0]["assignment_id"] == "1052514"
        assert c.get_assignment(ELA, "1052515")["due_at"] == "2026-10-31T03:59:00Z"
    finally:
        tmp.cleanup(); deploy_ledger.DEPLOY_ROOT = orig
        intake_manifest.staging_dir = orig_staging


def test_cp27_updates_1052515_only():
    orig, orig_staging, tmp = _tmp_ledger()
    try:
        c = _client()
        r = _run(c, [_update("Classroom Practice 27", "1052515", "2026-11-05T04:59:00Z")])
        assert r["assignments"][0]["assignment_id"] == "1052515"
        assert c.get_assignment(ELA, "1052515")["due_at"] == "2026-11-05T04:59:00Z"
        assert c.get_assignment(ELA, "1052514")["due_at"] == "2026-10-30T03:59:00Z"
    finally:
        tmp.cleanup(); deploy_ledger.DEPLOY_ROOT = orig
        intake_manifest.staging_dir = orig_staging


def test_update_never_creates_duplicate():
    orig, orig_staging, tmp = _tmp_ledger()
    try:
        c = _client()
        before = len(c.assignments)
        r = _run(c, [_update("Classroom Practice 26", "1052514", "2026-11-03T04:59:00Z")])
        assert r["lifecycle"] == schedule.PUBLISHED_VERIFIED
        assert len(c.assignments) == before
        assert c._write_counts["POST"] == 0
        assert c._write_counts["PUT"] == 1
    finally:
        tmp.cleanup(); deploy_ledger.DEPLOY_ROOT = orig
        intake_manifest.staging_dir = orig_staging


def test_correct_assignment_skips():
    orig, orig_staging, tmp = _tmp_ledger()
    try:
        c = _client()
        c.assignments["1052514"]["due_at"] = "2026-11-03T04:59:00Z"
        r = _run(c, [_update("Classroom Practice 26", "1052514", "2026-11-03T04:59:00Z")])
        assert r["lifecycle"] == schedule.PUBLISHED_VERIFIED
        assert r["assignments"][0]["disposition"] == "ALREADY_EXISTS"
        assert c._write_counts["PUT"] == 0
    finally:
        tmp.cleanup(); deploy_ledger.DEPLOY_ROOT = orig
        intake_manifest.staging_dir = orig_staging


def test_multiple_exact_title_matches_block():
    orig, orig_staging, tmp = _tmp_ledger()
    try:
        c = _client()
        c.assignments["copy-26"] = dict(c.assignments["1052514"], id="copy-26")
        r = _run(c, [_update("Classroom Practice 26", "1052514", "2026-11-03T04:59:00Z")])
        assert r["lifecycle"] == schedule.BLOCKED
        assert any("share this exact title" in f for f in r["failures"])
        assert c._write_counts["PUT"] == 0
    finally:
        tmp.cleanup(); deploy_ledger.DEPLOY_ROOT = orig
        intake_manifest.staging_dir = orig_staging


def test_missing_assignment_id_blocks():
    orig, orig_staging, tmp = _tmp_ledger()
    try:
        c = _client()
        action = _update("Classroom Practice 26", "1052514", "2026-11-03T04:59:00Z")
        action["assignment_id"] = None
        r = _run(c, [action])
        assert r["lifecycle"] == schedule.BLOCKED
        assert any("missing approved Canvas ID" in f for f in r["failures"])
    finally:
        tmp.cleanup(); deploy_ledger.DEPLOY_ROOT = orig
        intake_manifest.staging_dir = orig_staging


def test_wrong_approved_id_blocks():
    orig, orig_staging, tmp = _tmp_ledger()
    try:
        c = _client()
        r = _run(c, [_update("Classroom Practice 26", "9999999", "2026-11-03T04:59:00Z")])
        assert r["lifecycle"] == schedule.BLOCKED
        assert any("!= approved ID" in f for f in r["failures"])
        assert c._write_counts["PUT"] == 0
    finally:
        tmp.cleanup(); deploy_ledger.DEPLOY_ROOT = orig
        intake_manifest.staging_dir = orig_staging


def test_update_readback_mismatch_blocks():
    orig, orig_staging, tmp = _tmp_ledger()
    try:
        c = _client()

        def noop_update(course_id, assignment_id, **kwargs):
            c._write_counts["PUT"] += 1
            return c.get_assignment(course_id, assignment_id)

        c.update_assignment = noop_update  # type: ignore[assignment]
        r = _run(c, [_update("Classroom Practice 26", "1052514", "2026-11-03T04:59:00Z")])
        assert r["lifecycle"] == schedule.BLOCKED
        assert any("readback mismatch" in f for f in r["failures"])
        assert c._write_counts["PUT"] == 1
    finally:
        tmp.cleanup(); deploy_ledger.DEPLOY_ROOT = orig
        intake_manifest.staging_dir = orig_staging


def test_uncertain_write_never_retried():
    orig, orig_staging, tmp = _tmp_ledger()
    try:
        c = _client()
        calls = {"n": 0}

        def uncertain(course_id, assignment_id, **kwargs):
            calls["n"] += 1
            raise TimeoutError("socket timeout after send")

        c.update_assignment = uncertain  # type: ignore[assignment]
        r = _run(c, [_update("Classroom Practice 26", "1052514", "2026-11-03T04:59:00Z")])
        assert r["lifecycle"] == schedule.BLOCKED
        assert calls["n"] == 1
    finally:
        tmp.cleanup(); deploy_ledger.DEPLOY_ROOT = orig
        intake_manifest.staging_dir = orig_staging


def test_create_actions_still_create():
    orig, orig_staging, tmp = _tmp_ledger()
    try:
        c = _client()
        actions = [a for a in _twelve_actions() if a["action"] == "CREATE"]
        r = _run(c, actions)
        assert r["lifecycle"] == schedule.PUBLISHED_VERIFIED, r.get("failures")
        assert c._write_counts["POST"] == 9
        assert all(item["disposition"] == "PUBLISHED_VERIFIED" for item in r["assignments"])
    finally:
        tmp.cleanup(); deploy_ledger.DEPLOY_ROOT = orig
        intake_manifest.staging_dir = orig_staging


def test_full_q2w4_deployment_idempotent():
    orig, orig_staging, tmp = _tmp_ledger()
    try:
        c = _client()
        actions = _twelve_actions()
        r1 = _run(c, actions)
        assert r1["lifecycle"] == schedule.PUBLISHED_VERIFIED, r1.get("failures")
        assert c._write_counts["PUT"] == 2
        assert c._write_counts["POST"] == 9

        rollover_ledger.rollover_ledger_path(2, 4).unlink()
        before = (c._write_counts["PUT"], c._write_counts["POST"])
        r2 = _run(c, actions)
        assert r2["lifecycle"] == schedule.PUBLISHED_VERIFIED, r2.get("failures")
        assert (c._write_counts["PUT"], c._write_counts["POST"]) == before
        assert all(item["disposition"] == "ALREADY_EXISTS" for item in r2["assignments"])
    finally:
        tmp.cleanup(); deploy_ledger.DEPLOY_ROOT = orig
        intake_manifest.staging_dir = orig_staging


def test_existing_title_with_wrong_due_blocks_create():
    orig, orig_staging, tmp = _tmp_ledger()
    try:
        c = _client()
        action = _create("SM5: Lesson 41 Homework", "2026-11-03T04:59:00Z")
        c.assignments["existing"] = {
            "id": "existing", "course_id": MATH, "name": "SM5: Lesson 41 Homework",
            "assignment_group_id": "math-group", "points_possible": 100,
            "grading_type": "percent", "submission_types": ["on_paper"],
            "due_at": "2026-11-09T04:59:00Z", "omit_from_final_grade": False,
            "published": True,
        }
        r = _run(c, [action])
        assert r["lifecycle"] == schedule.BLOCKED
        assert any("refusing to duplicate" in f for f in r["failures"])
        assert c._write_counts["POST"] == 0
    finally:
        tmp.cleanup(); deploy_ledger.DEPLOY_ROOT = orig
        intake_manifest.staging_dir = orig_staging


def test_reminder_idempotent_after_canvas_wraps_message():
    orig, orig_staging, tmp = _tmp_ledger()
    try:
        c = _client(with_updates=False)
        body = "<p>Fluency Checkout 5 is Tuesday.</p>"
        css = '<link rel="stylesheet" href="https://instructure-uploads/canvas_global_app.css">'
        js = '<script src="https://instructure-uploads/canvas_global_app.js"></script>'
        c.announcements["topic-1"] = {
            "id": "topic-1", "course_id": 26442,
            "title": "Fluency Checkout 5 — Tuesday, November 3",
            "message": f"{css}{body}{js}", "published": True,
            "delayed_post_at": None, "posted_at": "now",
        }
        m = _base_manifest([])
        m["assessment_reminders"] = [{
            "subject": "reading_spelling", "course_id": 26442,
            "title": "Fluency Checkout 5 — Tuesday, November 3",
            "message": body, "classification": "NEW",
        }]
        r = rollover.execute(2, 3, 2, 4, client=c, owner_confirmation="ROLLOVER Q2W4", manifest=m)
        assert r["lifecycle"] == schedule.PUBLISHED_VERIFIED, r.get("failures")
        assert r["assessment_reminders"][0]["disposition"] == "ALREADY_EXISTS"
        assert c._write_counts["POST"] == 0
    finally:
        tmp.cleanup(); deploy_ledger.DEPLOY_ROOT = orig
        intake_manifest.staging_dir = orig_staging


def _run_tests():
    fns = [(n, f) for n, f in sorted(globals().items())
           if n.startswith("test_") and callable(f)]
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
    _run_tests()
