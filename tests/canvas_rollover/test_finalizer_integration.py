"""Rollover success requires an explicit publication finalizer result."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.canvas_llm_deploy import ledger as deploy_ledger
from scripts.canvas_llm_intake import manifest as intake_manifest
from scripts.canvas_llm_rollover import ledger as rollover_ledger
from scripts.canvas_llm_rollover import rollover, schedule
from scripts.teacher_workstation import adapter

SOURCE = "source-hash"
FINGERPRINT = "plan-fingerprint"


def _dirs(tmp: Path):
    intake_manifest.staging_dir = lambda q, w: tmp / "intake" / f"q{q}w{w}"
    deploy_ledger.DEPLOY_ROOT = tmp / "deployments"
    staging = tmp / "intake" / "q2w5"
    staging.mkdir(parents=True)
    return staging


def _manifest(**overrides):
    record = {
        "quarter": 2, "week": 5, "week_code": "Q2W5",
        "status": "READY_TO_PUBLISH", "approval_state": "APPROVED",
        "source_hash": SOURCE, "plan_fingerprint": FINGERPRINT,
    }
    record.update(overrides)
    return record


def _report():
    pages = [
        {"subject": subject, "course_id": 1, "page_id": 1, "verified": True,
         "disposition": "PUBLISHED_VERIFIED"}
        for subject in ("math", "reading_spelling", "language_arts", "science")
    ]
    return {
        "school_year": "2026-2027", "to_week": "Q2W5", "finished_at": "2026-11-08T05:01:00Z",
        "pages": pages,
        "homeroom": {"verified": True, "course_id": 26429},
        "weekly_announcements": [
            {"subject": "math", "title": "Math", "verified": True, "disposition": "SCHEDULED_VERIFIED"}
        ],
        "assignments": [{"title": "Work", "verified": True}],
        "assessment_reminders": [],
        "communication": {},
        "failures": [],
    }


def _save(staging: Path, manifest: dict):
    (staging / "intake-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")


def test_successful_finalizer_writes_rollover_only_after_agreement():
    import tempfile
    orig_deploy = deploy_ledger.DEPLOY_ROOT
    orig_staging = intake_manifest.staging_dir
    try:
        with tempfile.TemporaryDirectory() as tmp:
            staging = _dirs(Path(tmp))
            _save(staging, _manifest())
            calls = []
            real = deploy_ledger.finalize_published_verified

            def spy(quarter, week, report):
                calls.append(dict(report))
                return real(quarter, week, report)

            deploy_ledger.finalize_published_verified = spy
            try:
                result = rollover._finalize_five_course(
                    2, 5, _report(), {"source_hash": SOURCE, "plan_fingerprint": FINGERPRINT},
                )
            finally:
                deploy_ledger.finalize_published_verified = real
            assert result["lifecycle"] == schedule.PUBLISHED_VERIFIED, result
            assert calls[0]["source_hash"] == SOURCE
            assert calls[0]["plan_fingerprint"] == FINGERPRINT
            published = deploy_ledger.load_published_verified(2, 5)
            rollover_record = rollover_ledger.load_rollover_ledger(2, 5)
            assert published["status"] == "PUBLISHED_VERIFIED"
            assert rollover_record["lifecycle"] == schedule.PUBLISHED_VERIFIED
            assert intake_manifest.load_manifest(2, 5)["status"] == "PUBLISHED_VERIFIED"
    finally:
        deploy_ledger.DEPLOY_ROOT = orig_deploy
        intake_manifest.staging_dir = orig_staging


def test_wrong_missing_and_stale_fingerprints_block_before_success():
    import tempfile
    orig_deploy = deploy_ledger.DEPLOY_ROOT
    orig_staging = intake_manifest.staging_dir
    cases = (
        {"source_hash": "other", "plan_fingerprint": FINGERPRINT},
        {"source_hash": SOURCE, "plan_fingerprint": "other"},
        {"source_hash": SOURCE},
        {"source_hash": SOURCE, "plan_fingerprint": ""},
    )
    try:
        for plan in cases:
            with tempfile.TemporaryDirectory() as tmp:
                staging = _dirs(Path(tmp))
                before = _manifest()
                _save(staging, before)
                result = rollover._finalize_five_course(2, 5, _report(), plan)
                assert result["lifecycle"] == "FINALIZATION_BLOCKED", result
                assert result.get("already_complete") is False
                stored = rollover_ledger.load_rollover_ledger(2, 5)
                assert stored["lifecycle"] != schedule.PUBLISHED_VERIFIED
                assert deploy_ledger.load_published_verified(2, 5) is None
                assert intake_manifest.load_manifest(2, 5)["status"] == "READY_TO_PUBLISH"
    finally:
        deploy_ledger.DEPLOY_ROOT = orig_deploy
        intake_manifest.staging_dir = orig_staging


def test_finalizer_refusal_exception_and_missing_result_are_not_success():
    import tempfile
    orig_deploy = deploy_ledger.DEPLOY_ROOT
    orig_staging = intake_manifest.staging_dir
    real = deploy_ledger.finalize_published_verified
    outcomes = (
        lambda *_args, **_kwargs: {"status": "BLOCKED", "failures": ["readback failed"]},
        lambda *_args, **_kwargs: None,
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("ledger down")),
    )
    try:
        for outcome in outcomes:
            with tempfile.TemporaryDirectory() as tmp:
                staging = _dirs(Path(tmp))
                _save(staging, _manifest())
                deploy_ledger.finalize_published_verified = outcome
                result = rollover._finalize_five_course(
                    2, 5, _report(), {"source_hash": SOURCE, "plan_fingerprint": FINGERPRINT},
                )
                assert result["lifecycle"] == "FINALIZATION_BLOCKED", result
                assert result["lifecycle"] != schedule.PUBLISHED_VERIFIED
                assert adapter.latest_completed() is None
                assert intake_manifest.load_manifest(2, 5)["status"] == "READY_TO_PUBLISH"
    finally:
        deploy_ledger.finalize_published_verified = real
        deploy_ledger.DEPLOY_ROOT = orig_deploy
        intake_manifest.staging_dir = orig_staging


def test_rollover_write_failure_after_finalization_is_recoverable_without_republish():
    import tempfile
    orig_deploy = deploy_ledger.DEPLOY_ROOT
    orig_staging = intake_manifest.staging_dir
    orig_write = rollover_ledger.write_rollover_ledger
    try:
        with tempfile.TemporaryDirectory() as tmp:
            staging = _dirs(Path(tmp))
            _save(staging, _manifest())

            def fail_success(quarter, week, data):
                if data.get("lifecycle") == schedule.PUBLISHED_VERIFIED:
                    raise OSError("disk full")
                return orig_write(quarter, week, data)

            rollover_ledger.write_rollover_ledger = fail_success
            rollover.ledger.write_rollover_ledger = fail_success
            result = rollover._finalize_five_course(
                2, 5, _report(), {"source_hash": SOURCE, "plan_fingerprint": FINGERPRINT},
            )
            assert result["lifecycle"] == "PUBLICATION_VERIFIED_ROLLOVER_INCOMPLETE", result
            assert intake_manifest.load_manifest(2, 5)["status"] == "PUBLISHED_VERIFIED"
            rollover_ledger.write_rollover_ledger = orig_write
            rollover.ledger.write_rollover_ledger = orig_write
            recovered = rollover.execute(
                2, 4, 2, 5, client=object(), owner_confirmation="ROLLOVER Q2W5",
                manifest={"to_week": "Q2W5", "source_hash": SOURCE, "plan_fingerprint": FINGERPRINT},
            )
            assert recovered.get("rollover_recovered") is True
            assert recovered["lifecycle"] == schedule.PUBLISHED_VERIFIED
            again = rollover.execute(
                2, 4, 2, 5, client=object(), owner_confirmation="ROLLOVER Q2W5",
                manifest={"to_week": "Q2W5", "source_hash": SOURCE, "plan_fingerprint": FINGERPRINT},
            )
            assert again.get("already_complete") is True
    finally:
        rollover_ledger.write_rollover_ledger = orig_write
        rollover.ledger.write_rollover_ledger = orig_write
        deploy_ledger.DEPLOY_ROOT = orig_deploy
        intake_manifest.staging_dir = orig_staging


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
