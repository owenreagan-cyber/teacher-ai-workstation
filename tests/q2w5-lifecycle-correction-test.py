"""Guarded reversal of the false Q2W5 published lifecycle.

Tests use temporary storage. They do not apply the real correction.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.canvas_llm_deploy import ledger, lifecycle_reconciliation as rec
from scripts.canvas_llm_intake import manifest as imf
from scripts.canvas_llm_storage import isolated_storage

REAL_MANIFEST = Path(".local/canvas-llm/intake/2026-2027/q2/w5/intake-manifest.json")
CURRENT_REAL_MANIFEST_SHA256 = "0c4c71396440b43105baa4affc856ed16856fa66ac23f01c7619b38885ddb751"
PUBLISHED_AT = rec.EXPECTED_PUBLISHED_AT
SOURCE = rec.EXPECTED_SOURCE_HASH


def _real_hash() -> str:
    return hashlib.sha256(REAL_MANIFEST.read_bytes()).hexdigest()


def _false_manifest(**overrides) -> dict:
    manifest = imf.new_manifest(
        quarter=2, week=5, week_code="Q2W5",
        date_range={"start": "2026-11-09", "end": "2026-11-13"},
    )
    manifest["status"] = "PUBLISHED_VERIFIED"
    manifest["approval_state"] = "PENDING"
    manifest["ready_to_publish"] = True
    manifest["published_at"] = PUBLISHED_AT
    manifest["source_hash"] = SOURCE
    manifest["history"] = [
        {"from": "SOURCE_FETCHED", "to": "NORMALIZED", "at": "2026-11-07T18:19:29.943708+00:00"},
        {"from": "NORMALIZED", "to": "DRAFTED", "at": "2026-11-07T18:19:29.953917+00:00"},
        {"from": "DRAFTED", "to": "READY_FOR_REVIEW", "at": "2026-11-07T18:19:29.953922+00:00"},
        {"from": "READY_FOR_REVIEW", "to": "PUBLISHED_VERIFIED", "at": "2026-11-07T18:59:12.263534+00:00"},
    ]
    manifest.update(overrides)
    return manifest


def _setup(manifest: dict) -> tuple[str, dict]:
    imf.save_manifest(2, 5, manifest)
    path = imf.staging_dir(2, 5) / "intake-manifest.json"
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    preview = rec.build_preview(2, 5)
    return digest, preview


def test_exact_hash_dry_run_and_apply_preserve_history():
    before = _real_hash()
    with isolated_storage():
        digest, preview = _setup(_false_manifest())
        history = list(imf.load_manifest(2, 5)["history"])
        dry = rec.apply_correction(
            2, 5, preview=preview, expected_manifest_sha256=digest,
            expected_source_hash=SOURCE, apply=False,
        )
        assert dry["status"] == "DRY_RUN", dry
        assert imf.load_manifest(2, 5)["status"] == "PUBLISHED_VERIFIED"
        result = rec.apply_correction(
            2, 5, preview=preview, expected_manifest_sha256=digest,
            expected_source_hash=SOURCE, apply=True,
        )
        saved = imf.load_manifest(2, 5)
        assert result["status"] == "APPLIED", result
        assert saved["status"] == "READY_FOR_REVIEW"
        assert saved["approval_state"] == "PENDING"
        assert saved["ready_to_publish"] is False
        assert saved["published_at"] is None
        assert saved["source_hash"] == SOURCE
        assert saved["history"] == history
        record = saved["lifecycle_corrections"][0]
        assert record["original_published_at"] == PUBLISHED_AT
        assert record["prior_manifest_sha256"] == digest
        assert record["source_hash"] == SOURCE
        assert record["from_status"] == "PUBLISHED_VERIFIED"
        assert record["to_status"] == "READY_FOR_REVIEW"
        assert record["evidence"]["missing_evidence"] == list(rec.LEDGER_NAMES)
        assert record["evidence"]["false_transition"]["from"] == "READY_FOR_REVIEW"
        assert record["evidence"]["false_transition"]["to"] == "PUBLISHED_VERIFIED"
        for name in rec.LEDGER_NAMES:
            assert not (ledger.deploy_dir(2, 5) / name).exists()
    assert _real_hash() == before


def test_changed_hash_unexpected_ledger_and_wrong_source_block():
    before = _real_hash()
    with isolated_storage():
        digest, preview = _setup(_false_manifest())
        changed = rec.apply_correction(
            2, 5, preview=preview, expected_manifest_sha256="0" * 64,
            expected_source_hash=SOURCE, apply=True,
        )
        assert changed["status"] == "BLOCKED"
        assert imf.load_manifest(2, 5)["status"] == "PUBLISHED_VERIFIED"
        (ledger.deploy_dir(2, 5) / "deployment-ledger.json").parent.mkdir(parents=True, exist_ok=True)
        (ledger.deploy_dir(2, 5) / "deployment-ledger.json").write_text("{}\n", encoding="utf-8")
        unexpected = rec.apply_correction(
            2, 5, preview=preview, expected_manifest_sha256=digest,
            expected_source_hash=SOURCE, apply=True,
        )
        assert unexpected["status"] == "BLOCKED"
        assert any("unexpected ledger" in item for item in unexpected["failures"])
        (ledger.deploy_dir(2, 5) / "deployment-ledger.json").unlink()
        _setup(_false_manifest(source_hash="changed-source"))
        digest, preview = _setup(_false_manifest(source_hash="changed-source"))
        wrong_source = rec.apply_correction(
            2, 5, preview=preview, expected_manifest_sha256=digest,
            expected_source_hash=SOURCE, apply=True,
        )
        assert wrong_source["status"] == "BLOCKED"
        assert any("source hash" in item for item in wrong_source["failures"])
    assert _real_hash() == before


def test_missing_preview_evidence_wrong_state_and_nonpending_approval_block():
    before = _real_hash()
    with isolated_storage():
        digest, preview = _setup(_false_manifest())
        preview["missing_evidence"] = ["plan_fingerprint"]
        missing = rec.apply_correction(
            2, 5, preview=preview, expected_manifest_sha256=digest,
            expected_source_hash=SOURCE, apply=True,
        )
        assert missing["status"] == "BLOCKED"
        assert any("missing deployment evidence" in item for item in missing["failures"])
        digest, preview = _setup(_false_manifest(status="DRAFTED", ready_to_publish=False, published_at=None))
        wrong_state = rec.apply_correction(
            2, 5, preview=preview, expected_manifest_sha256=digest,
            expected_source_hash=SOURCE, apply=True,
        )
        assert wrong_state["status"] == "BLOCKED"
        assert any("not PUBLISHED_VERIFIED" in item for item in wrong_state["failures"])
        digest, preview = _setup(_false_manifest(approval_state="APPROVED"))
        approved = rec.apply_correction(
            2, 5, preview=preview, expected_manifest_sha256=digest,
            expected_source_hash=SOURCE, apply=True,
        )
        assert approved["status"] == "BLOCKED"
        assert any("not PENDING" in item for item in approved["failures"])
        assert imf.load_manifest(2, 5)["approval_state"] == "APPROVED"
    assert _real_hash() == before


def test_atomic_write_and_readback_failures_restore_the_manifest():
    before = _real_hash()
    with isolated_storage():
        digest, preview = _setup(_false_manifest())
        path = imf.staging_dir(2, 5) / "intake-manifest.json"
        original_bytes = path.read_bytes()
        original_write = Path.write_text

        def fail_partial(self, text, *args, **kwargs):
            if str(self).endswith(".partial"):
                raise OSError("disk full")
            return original_write(self, text, *args, **kwargs)

        Path.write_text = fail_partial
        try:
            failed = rec.apply_correction(
                2, 5, preview=preview, expected_manifest_sha256=digest,
                expected_source_hash=SOURCE, apply=True,
            )
        finally:
            Path.write_text = original_write
        assert failed["status"] == "BLOCKED"
        assert path.read_bytes() == original_bytes

        original_read = Path.read_text

        def corrupt_final(self, *args, **kwargs):
            if self.name == "intake-manifest.json":
                return "CORRUPT"
            return original_read(self, *args, **kwargs)

        Path.read_text = corrupt_final
        try:
            readback = rec.apply_correction(
                2, 5, preview=preview, expected_manifest_sha256=digest,
                expected_source_hash=SOURCE, apply=True,
            )
        finally:
            Path.read_text = original_read
        assert readback["status"] == "BLOCKED"
        assert path.read_bytes() == original_bytes
        assert json.loads(path.read_bytes().decode("utf-8"))["history"] == json.loads(
            original_bytes.decode("utf-8")
        )["history"]
        assert not path.with_name(path.name + ".partial").exists()
        assert not path.with_name(path.name + ".restore").exists()
    assert _real_hash() == before


def test_repeated_application_is_idempotent():
    before = _real_hash()
    with isolated_storage():
        digest, preview = _setup(_false_manifest())
        first = rec.apply_correction(
            2, 5, preview=preview, expected_manifest_sha256=digest,
            expected_source_hash=SOURCE, apply=True,
        )
        assert first["status"] == "APPLIED"
        path = imf.staging_dir(2, 5) / "intake-manifest.json"
        after = path.read_bytes()
        second = rec.apply_correction(
            2, 5, preview=preview, expected_manifest_sha256=digest,
            expected_source_hash=SOURCE, apply=True,
        )
        assert second["status"] == "ALREADY_APPLIED"
        assert path.read_bytes() == after
        saved = imf.load_manifest(2, 5)
        assert len(saved["lifecycle_corrections"]) == 1
        assert saved["history"] == json.loads(after.decode("utf-8"))["history"]
        assert len(saved["history"]) == 4
    assert before == CURRENT_REAL_MANIFEST_SHA256
    assert _real_hash() == before


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
