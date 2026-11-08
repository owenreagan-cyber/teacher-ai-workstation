"""Guarded reversal of the false Q2W5 published lifecycle.

All mutation tests run inside :func:`isolated_storage` temporary trees. They
never depend on, read expectations from, or modify the real ``.local`` Q2W5
manifest bytes.
"""
from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.canvas_llm_deploy import ledger, lifecycle_reconciliation as rec
from scripts.canvas_llm_intake import manifest as imf
from scripts.canvas_llm_storage import canonical_intake_root, isolated_storage

REAL_MANIFEST = Path(".local/canvas-llm/intake/2026-2027/q2/w5/intake-manifest.json")
PUBLISHED_AT = rec.EXPECTED_PUBLISHED_AT
SOURCE = rec.EXPECTED_SOURCE_HASH


@dataclass(frozen=True)
class RealManifestSnapshot:
    """Read-only fingerprint of the developer's real manifest (if present)."""

    sha256: str
    payload: bytes


def _real_manifest_snapshot() -> RealManifestSnapshot | None:
    if not REAL_MANIFEST.exists():
        return None
    payload = REAL_MANIFEST.read_bytes()
    return RealManifestSnapshot(
        sha256=hashlib.sha256(payload).hexdigest(),
        payload=payload,
    )


def _assert_real_manifest_untouched(snapshot: RealManifestSnapshot | None) -> None:
    if snapshot is None:
        return
    assert REAL_MANIFEST.exists(), "real Q2W5 intake manifest disappeared"
    now = REAL_MANIFEST.read_bytes()
    assert hashlib.sha256(now).hexdigest() == snapshot.sha256, "real manifest SHA-256 changed"
    assert now == snapshot.payload, "real manifest bytes changed"


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


def _setup(manifest: dict) -> tuple[str, dict, bytes]:
    """Write isolated manifest; return (sha256, preview, exact file bytes)."""
    imf.save_manifest(2, 5, manifest)
    path = imf.staging_dir(2, 5) / "intake-manifest.json"
    original_bytes = path.read_bytes()
    digest = hashlib.sha256(original_bytes).hexdigest()
    preview = rec.build_preview(2, 5)
    return digest, preview, original_bytes


def test_exact_hash_dry_run_and_apply_preserve_history():
    snapshot = _real_manifest_snapshot()
    with isolated_storage():
        digest, preview, _ = _setup(_false_manifest())
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
        staging = imf.staging_dir(2, 5)
        assert canonical_intake_root() not in staging.parents
        assert staging.resolve() != REAL_MANIFEST.parent.resolve()
    _assert_real_manifest_untouched(snapshot)


def test_changed_hash_unexpected_ledger_and_wrong_source_block():
    snapshot = _real_manifest_snapshot()
    with isolated_storage():
        digest, preview, _ = _setup(_false_manifest())
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
        digest, preview, _ = _setup(_false_manifest(source_hash="changed-source"))
        wrong_source = rec.apply_correction(
            2, 5, preview=preview, expected_manifest_sha256=digest,
            expected_source_hash=SOURCE, apply=True,
        )
        assert wrong_source["status"] == "BLOCKED"
        assert any("source hash" in item for item in wrong_source["failures"])
    _assert_real_manifest_untouched(snapshot)


def test_missing_preview_evidence_wrong_state_and_nonpending_approval_block():
    snapshot = _real_manifest_snapshot()
    with isolated_storage():
        digest, preview, _ = _setup(_false_manifest())
        preview["missing_evidence"] = ["plan_fingerprint"]
        missing = rec.apply_correction(
            2, 5, preview=preview, expected_manifest_sha256=digest,
            expected_source_hash=SOURCE, apply=True,
        )
        assert missing["status"] == "BLOCKED"
        assert any("missing deployment evidence" in item for item in missing["failures"])
        digest, preview, _ = _setup(_false_manifest(status="DRAFTED", ready_to_publish=False, published_at=None))
        wrong_state = rec.apply_correction(
            2, 5, preview=preview, expected_manifest_sha256=digest,
            expected_source_hash=SOURCE, apply=True,
        )
        assert wrong_state["status"] == "BLOCKED"
        assert any("not PUBLISHED_VERIFIED" in item for item in wrong_state["failures"])
        digest, preview, _ = _setup(_false_manifest(approval_state="APPROVED"))
        approved = rec.apply_correction(
            2, 5, preview=preview, expected_manifest_sha256=digest,
            expected_source_hash=SOURCE, apply=True,
        )
        assert approved["status"] == "BLOCKED"
        assert any("not PENDING" in item for item in approved["failures"])
        assert imf.load_manifest(2, 5)["approval_state"] == "APPROVED"
    _assert_real_manifest_untouched(snapshot)


def test_atomic_write_and_readback_failures_restore_the_manifest():
    snapshot = _real_manifest_snapshot()
    with isolated_storage():
        digest, preview, original_bytes = _setup(_false_manifest())
        path = imf.staging_dir(2, 5) / "intake-manifest.json"
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
    _assert_real_manifest_untouched(snapshot)


def test_repeated_application_is_idempotent():
    snapshot = _real_manifest_snapshot()
    with isolated_storage():
        digest, preview, fixture_bytes = _setup(_false_manifest())
        assert digest == hashlib.sha256(fixture_bytes).hexdigest()
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
    _assert_real_manifest_untouched(snapshot)


def test_isolated_storage_never_writes_canonical_intake_tree():
    snapshot = _real_manifest_snapshot()
    canonical_bytes = REAL_MANIFEST.read_bytes() if REAL_MANIFEST.exists() else None
    with isolated_storage() as tmp:
        digest, preview, _ = _setup(_false_manifest())
        isolated_path = imf.staging_dir(2, 5) / "intake-manifest.json"
        assert tmp in isolated_path.parents
        assert isolated_path != REAL_MANIFEST
        rec.apply_correction(
            2, 5, preview=preview, expected_manifest_sha256=digest,
            expected_source_hash=SOURCE, apply=True,
        )
        assert imf.load_manifest(2, 5)["status"] == "READY_FOR_REVIEW"
    if canonical_bytes is not None:
        assert REAL_MANIFEST.read_bytes() == canonical_bytes
    _assert_real_manifest_untouched(snapshot)


def verify_real_q2w5_manifest_readonly() -> dict[str, object]:
    """Optional read-only integrity probe for the developer ``.local`` manifest.

    Not part of the default unit suite and never mutates storage.
    """
    if not REAL_MANIFEST.exists():
        return {"present": False}
    payload = REAL_MANIFEST.read_bytes()
    data = json.loads(payload.decode("utf-8"))
    return {
        "present": True,
        "path": str(REAL_MANIFEST),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "status": data.get("status"),
        "approval_state": data.get("approval_state"),
        "published_at": data.get("published_at"),
        "source_hash": data.get("source_hash"),
        "history_len": len(data.get("history") or []),
        "lifecycle_corrections_len": len(data.get("lifecycle_corrections") or []),
    }


def _run():
    suite_snapshot = _real_manifest_snapshot()
    failed = 0
    tests = [(name, fn) for name, fn in sorted(globals().items()) if name.startswith("test_") and callable(fn)]
    for name, fn in tests:
        try:
            fn()
            print(f"PASS {name}")
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"FAIL {name}: {type(exc).__name__}: {exc}")
    _assert_real_manifest_untouched(suite_snapshot)
    print(f"RESULT: {len(tests) - failed} passed, {failed} failed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    if "--verify-production" in sys.argv:
        report = verify_real_q2w5_manifest_readonly()
        print(json.dumps(report, indent=2, sort_keys=True))
        raise SystemExit(0)
    _run()
