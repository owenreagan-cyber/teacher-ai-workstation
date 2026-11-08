"""Lifecycle finalization must not promote a week without evidence.

The real Q2W5 manifest is only hashed. Successful and failed finalization
run inside temporary storage.
"""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.canvas_llm_deploy import ledger, lifecycle_reconciliation
from scripts.canvas_llm_intake import manifest as imf
from scripts.canvas_llm_storage import isolated_storage
from scripts.teacher_workstation import adapter

REAL_MANIFEST = Path(".local/canvas-llm/intake/2026-2027/q2/w5/intake-manifest.json")
REAL_DEPLOY = Path(".local/canvas-llm/deployments/2026-2027/q2/w5")
SOURCE = "source-hash"
FINGERPRINT = "plan-fingerprint"
COURSES = {
    "math": 26404,
    "reading_spelling": 26442,
    "language_arts": 28171,
    "science": 28166,
    "homeroom": 26429,
}


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _protected() -> tuple[str | None, list[str] | None]:
    """Hash the real week only when this machine has one. CI does not."""
    if not REAL_MANIFEST.exists() or not REAL_DEPLOY.exists():
        return None, None
    return _hash(REAL_MANIFEST), sorted(path.name for path in REAL_DEPLOY.iterdir())


def _manifest(**overrides) -> dict:
    manifest = imf.new_manifest(
        quarter=2, week=5, week_code="Q2W5",
        date_range={"start": "2026-11-09", "end": "2026-11-13"},
    )
    manifest["status"] = "READY_TO_PUBLISH"
    manifest["approval_state"] = "APPROVED"
    manifest["source_hash"] = SOURCE
    manifest["plan_fingerprint"] = FINGERPRINT
    manifest.update(overrides)
    return manifest


def _report(**overrides) -> dict:
    pages = [
        {"subject": subject, "course_id": course_id, "verified": True,
         "disposition": "PUBLISHED_VERIFIED"}
        for subject, course_id in COURSES.items()
    ]
    report = {
        "status": "PUBLISHED_VERIFIED",
        "source_hash": SOURCE,
        "plan_fingerprint": FINGERPRINT,
        "failures": [],
        "pages": pages,
        "homeroom": {"verified": True, "course_id": COURSES["homeroom"]},
        "weekly_announcements": [
            {"subject": subject, "title": f"{subject} update", "verified": True,
             "disposition": "SCHEDULED_VERIFIED"}
            for subject in ("math", "reading_spelling", "language_arts", "science")
        ],
        "assignments": [{"title": "Math classwork", "verified": True}],
        "homeroom_announcement": {"title": "Family", "verified": True},
        "homeroom_page_before_announcement": True,
    }
    report.update(overrides)
    return report


def _save(manifest: dict) -> None:
    imf.save_manifest(2, 5, manifest)


def _unchanged(before: str | None, names: list[str] | None) -> None:
    if before is None:
        return
    assert _protected()[0] == before
    assert sorted(path.name for path in REAL_DEPLOY.iterdir()) == names


def test_successful_and_failed_finalization_stay_in_temporary_storage():
    before, names = _protected()
    with isolated_storage() as root:
        _save(_manifest())
        result = ledger.finalize_published_verified(2, 5, _report())
        assert result["status"] == "PUBLISHED_VERIFIED", result
        saved = imf.load_manifest(2, 5)
        assert saved["status"] == "PUBLISHED_VERIFIED"
        assert saved["published_at"]
        assert saved["ready_to_publish"] is True
        assert len(saved["finalization_history"]) == 1
        ledger_path = Path(result["path"])
        assert str(root) in str(ledger_path)
        assert ledger_path.exists()
        assert not str(ledger_path).startswith(str(REAL_DEPLOY))

        failed = ledger.finalize_published_verified(2, 5, _report(source_hash="WRONG"))
        assert failed["status"] == "BLOCKED"
        assert saved["published_at"] == imf.load_manifest(2, 5)["published_at"]
        assert len(imf.load_manifest(2, 5)["finalization_history"]) == 1
    _unchanged(before, names)


def test_negative_finalization_does_not_advance_intake():
    before, names = _protected()
    cases = {
        "missing report": None,
        "missing approval": (_manifest(approval_state="PENDING"), _report()),
        "wrong source": (_manifest(), _report(source_hash="WRONG")),
        "wrong fingerprint": (_manifest(), _report(plan_fingerprint="OTHER")),
        "missing course": (_manifest(), _report(pages=[
            page for page in _report()["pages"] if page["subject"] != "science"
        ], homeroom={"verified": True})),
        "unverified page": (_manifest(), _report(pages=[
            {**page, "verified": False} if page["subject"] == "math" else page
            for page in _report()["pages"]
        ])),
        "unverified announcement": (_manifest(), _report(weekly_announcements=[
            {"subject": "math", "title": "Math", "verified": False}
        ])),
        "unverified assignment": (_manifest(), _report(assignments=[
            {"title": "Math", "verified": False}
        ])),
        "homeroom order": (_manifest(), _report(homeroom_page_before_announcement=False)),
    }
    with isolated_storage():
        for name, payload in cases.items():
            if payload is None:
                _save(_manifest())
                result = ledger.finalize_published_verified(2, 5, None)
            else:
                manifest, report = payload
                _save(manifest)
                result = ledger.finalize_published_verified(2, 5, report)
            assert result["status"] == "BLOCKED", name
            saved = imf.load_manifest(2, 5)
            assert saved["status"] == "READY_TO_PUBLISH", name
            assert saved.get("published_at") is None, name
            assert saved.get("finalization_history") in (None, []), name
    _unchanged(before, names)


def test_failed_ledger_write_and_corrupt_readback_do_not_advance():
    before, names = _protected()
    with isolated_storage():
        _save(_manifest())
        original = Path.write_text

        def fail_partial(self, text, *args, **kwargs):
            if str(self).endswith(".partial"):
                raise OSError("disk full")
            return original(self, text, *args, **kwargs)

        Path.write_text = fail_partial
        try:
            result = ledger.finalize_published_verified(2, 5, _report())
        finally:
            Path.write_text = original
        assert result["status"] == "BLOCKED"
        assert "write failed" in result["failures"][0]
        assert imf.load_manifest(2, 5)["status"] == "READY_TO_PUBLISH"

        original_read = ledger.read_json

        def corrupt(path):
            if str(path).endswith("published-verified-ledger.json"):
                return {"status": "CORRUPT"}
            return original_read(path)

        ledger.read_json = corrupt
        try:
            result = ledger.finalize_published_verified(2, 5, _report())
        finally:
            ledger.read_json = original_read
        assert result["status"] == "BLOCKED"
        assert imf.load_manifest(2, 5)["status"] == "READY_TO_PUBLISH"
        assert imf.load_manifest(2, 5).get("published_at") is None
    _unchanged(before, names)


def test_duplicate_finalization_does_not_rewrite_history():
    with isolated_storage():
        _save(_manifest())
        report = _report()
        first = ledger.finalize_published_verified(2, 5, report)
        published_at = imf.load_manifest(2, 5)["published_at"]
        history = list(imf.load_manifest(2, 5)["history"])
        second = ledger.finalize_published_verified(2, 5, report)
        saved = imf.load_manifest(2, 5)
        assert first["status"] == "PUBLISHED_VERIFIED"
        assert second.get("duplicate") is True
        assert saved["published_at"] == published_at
        assert saved["history"] == history
        assert len(saved["finalization_history"]) == 1
        changed = ledger.finalize_published_verified(2, 5, _report(plan_fingerprint="OTHER"))
        assert changed["status"] == "BLOCKED"
        assert imf.load_manifest(2, 5)["history"] == history


def test_split_storage_cannot_finalize_against_real_intake(tmp_path=None):
    before, _names = _protected()
    with tempfile.TemporaryDirectory() as tmp:
        original = ledger.DEPLOY_ROOT
        ledger.DEPLOY_ROOT = Path(tmp) / "deployments"
        try:
            result = ledger.finalize_published_verified(2, 5, _report())
        finally:
            ledger.DEPLOY_ROOT = original
    assert result["status"] == "BLOCKED"
    assert any("split" in item for item in result["failures"])
    assert _protected()[0] == before


def test_chief_of_staff_ignores_manifest_status_without_a_ledger():
    with isolated_storage():
        manifest = _manifest(status="PUBLISHED_VERIFIED", approval_state="PENDING", ready_to_publish=True)
        _save(manifest)
        assert adapter.latest_completed() is None
        manifest["approval_state"] = "APPROVED"
        _save(manifest)
        assert adapter.latest_completed() is None
        ledger.finalize_published_verified(2, 5, _report())
        # The manifest was already PUBLISHED_VERIFIED, so finalize blocks on the
        # predecessor check unless it is ready. Rebuild from ready and finalize.
        _save(_manifest())
        result = ledger.finalize_published_verified(2, 5, _report())
        assert result["status"] == "PUBLISHED_VERIFIED", result
        completed = adapter.latest_completed()
        assert completed is not None
        assert completed["source_hash"] == SOURCE
        assert completed["ledger"]["verified_at"] is None or "ledger" in completed


def test_reconciliation_preview_is_not_applied():
    with isolated_storage():
        manifest = _manifest(
            status="PUBLISHED_VERIFIED",
            approval_state="PENDING",
            ready_to_publish=True,
            published_at="2026-11-07T19:00:06.341854+00:00",
        )
        manifest["history"] = [{
            "from": "READY_FOR_REVIEW",
            "to": "PUBLISHED_VERIFIED",
            "at": "2026-11-07T18:59:12.263534+00:00",
        }]
        _save(manifest)
        preview = lifecycle_reconciliation.build_preview(2, 5)
        assert preview["applied"] is False
        assert preview["existing_state"]["status"] == "PUBLISHED_VERIFIED"
        assert preview["existing_state"]["approval_state"] == "PENDING"
        assert "published-verified-ledger.json" in preview["missing_evidence"]
        assert preview["proposed_corrected_lifecycle"]["status"] == "READY_FOR_REVIEW"
        assert preview["proposed_corrected_lifecycle"]["ready_to_publish"] is False
        assert imf.load_manifest(2, 5)["status"] == "PUBLISHED_VERIFIED"


def test_advance_status_cannot_enter_published_verified():
    before, _names = _protected()
    manifest = _manifest(status="SOURCE_FETCHED", approval_state="PENDING", ready_to_publish=False)
    imf.advance_status(manifest, "NORMALIZED")
    imf.advance_status(manifest, "DRAFTED")
    imf.advance_status(manifest, "READY_FOR_REVIEW")
    assert manifest["status"] == "READY_FOR_REVIEW"
    history = list(manifest["history"])
    try:
        imf.advance_status(manifest, "PUBLISHED_VERIFIED")
        raise AssertionError("direct publication must be rejected")
    except ValueError as exc:
        assert "PUBLISHED_VERIFIED" in str(exc)
    assert manifest["status"] == "READY_FOR_REVIEW"
    assert manifest["history"] == history
    manifest["status"] = "READY_TO_PUBLISH"
    manifest["approval_state"] = "PENDING"
    try:
        imf.advance_status(manifest, "PUBLISHED_VERIFIED")
        raise AssertionError("pending approval must not publish through advance_status")
    except ValueError:
        pass
    assert manifest["status"] == "READY_TO_PUBLISH"
    with isolated_storage():
        _save(_manifest(approval_state="PENDING"))
        missing_approval = ledger.finalize_published_verified(2, 5, _report())
        assert missing_approval["status"] == "BLOCKED"
        partial = _report(pages=[page for page in _report()["pages"] if page["subject"] != "science"])
        _save(_manifest())
        assert ledger.finalize_published_verified(2, 5, partial)["status"] == "BLOCKED"
        assert ledger.finalize_published_verified(2, 5, _report(source_hash="WRONG"))["status"] == "BLOCKED"
        assert ledger.finalize_published_verified(2, 5, _report(plan_fingerprint="WRONG"))["status"] == "BLOCKED"
        assert not (ledger.deploy_dir(2, 5) / "published-verified-ledger.json").exists()
        result = ledger.finalize_published_verified(2, 5, _report())
        assert result["status"] == "PUBLISHED_VERIFIED", result
        again = ledger.finalize_published_verified(2, 5, _report())
        assert again.get("duplicate") is True
    with isolated_storage():
        false_manifest = _manifest(
            status="PUBLISHED_VERIFIED",
            approval_state="PENDING",
            ready_to_publish=True,
            published_at="2026-11-07T19:00:06.341854+00:00",
            source_hash="c49c65883fdf8a77331e0994fbe087d47ab8f7294e3c51bd73d336fe79b12341",
        )
        false_manifest["history"] = [{
            "from": "READY_FOR_REVIEW",
            "to": "PUBLISHED_VERIFIED",
            "at": "2026-11-07T18:59:12.263534+00:00",
        }]
        imf.save_manifest(2, 5, false_manifest)
        path = imf.staging_dir(2, 5) / "intake-manifest.json"
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        preview = lifecycle_reconciliation.build_preview(2, 5)
        corrected = lifecycle_reconciliation.apply_correction(
            2, 5, preview=preview, expected_manifest_sha256=digest,
            expected_source_hash=false_manifest["source_hash"], apply=True,
        )
        assert corrected["status"] == "APPLIED", corrected
        assert imf.load_manifest(2, 5)["status"] == "READY_FOR_REVIEW"
    assert _protected()[0] == before


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
