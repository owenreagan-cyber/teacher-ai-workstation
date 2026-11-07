"""Guarded reversal of a false PUBLISHED_VERIFIED intake lifecycle.

Dry-run is the default. ``apply_correction(..., apply=True)`` is the only
writer, and it writes the intake manifest only. It does not create ledgers,
approve artifacts, or call Canvas.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.canvas_llm_deploy import ledger
from scripts.canvas_llm_intake import manifest as imf
from scripts.canvas_llm_rollover import ledger as rollover_ledger


def _history(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for item in manifest.get("history") or []:
        if isinstance(item, dict):
            rows.append({"from": item.get("from"), "to": item.get("to"), "at": item.get("at")})
    return rows


def build_preview(quarter: int, week: int) -> dict[str, Any]:
    """Describe the current lifecycle and the evidence that is actually present."""
    manifest = imf.load_manifest(quarter, week) or {}
    published = ledger.load_published_verified(quarter, week)
    deployment = ledger.load_ledger(quarter, week)
    rollover = rollover_ledger.load_rollover_ledger(quarter, week)
    deploy_path = ledger.deploy_dir(quarter, week)
    evidence = sorted(path.name for path in deploy_path.iterdir()) if deploy_path.exists() else []
    history = _history(manifest)
    false_transition = next(
        (item for item in history if item.get("to") == "PUBLISHED_VERIFIED"),
        None,
    )
    proposed = (false_transition or {}).get("from") or "READY_FOR_REVIEW"
    missing = []
    if not isinstance(published, dict):
        missing.append("published-verified-ledger.json")
    if not isinstance(deployment, dict):
        missing.append("deployment-ledger.json")
    if not isinstance(rollover, dict):
        missing.append("rollover-ledger.json")
    if manifest.get("approval_state") != "APPROVED":
        missing.append("explicit approval_state APPROVED")
    if not manifest.get("plan_fingerprint"):
        missing.append("plan_fingerprint")
    return {
        "quarter": quarter,
        "week": week,
        "week_code": manifest.get("week_code"),
        "existing_state": {
            "status": manifest.get("status"),
            "approval_state": manifest.get("approval_state"),
            "ready_to_publish": manifest.get("ready_to_publish"),
            "published_at": manifest.get("published_at"),
            "source_hash": manifest.get("source_hash"),
            "plan_fingerprint": manifest.get("plan_fingerprint"),
            "history": history,
        },
        "available_evidence": evidence,
        "missing_evidence": missing,
        "published_ledger_present": isinstance(published, dict),
        "deployment_ledger_present": isinstance(deployment, dict),
        "rollover_ledger_present": isinstance(rollover, dict),
        "proposed_corrected_lifecycle": {
            "status": proposed,
            "approval_state": manifest.get("approval_state"),
            "ready_to_publish": False,
            "published_at": None,
        },
        "original_published_at": manifest.get("published_at"),
        "false_transition": false_transition,
        "reason": (
            "finalize_published_verified() advanced the intake manifest during "
            "rollover.execute() without a surviving verified deployment ledger. "
            "The status history records the transition, and a later call overwrote "
            "published_at without appending another history entry. Approval remained PENDING."
        ),
        "required_verification_before_correction": [
            "Confirm no Canvas objects were created for this week.",
            "Confirm published-verified-ledger.json is still absent.",
            "Keep the existing status history; do not delete the false transition.",
            "Set status back to the prior history state and ready_to_publish false.",
            "Leave approval_state PENDING until the owner approves the current artifacts.",
            "Recompute the manifest hash after the correction and compare it with this preview.",
        ],
        "applied": False,
    }


EXPECTED_MANIFEST_SHA256 = "a004caca02b840e71103c2f1f5c6a24b02d1cc40a396c4df70412010c2db2f04"
EXPECTED_SOURCE_HASH = "c49c65883fdf8a77331e0994fbe087d47ab8f7294e3c51bd73d336fe79b12341"
EXPECTED_PUBLISHED_AT = "2026-11-07T19:00:06.341854+00:00"
EXPECTED_PRIOR_STATUS = "READY_FOR_REVIEW"
FALSE_STATUS = "PUBLISHED_VERIFIED"
PREVIEW_PATH = Path(".local/canvas-llm/lifecycle-reconciliation/q2w5-published-verified-preview.json")
LEDGER_NAMES = (
    "published-verified-ledger.json",
    "deployment-ledger.json",
    "rollover-ledger.json",
)


def _manifest_path(quarter: int, week: int) -> Path:
    return imf.staging_dir(quarter, week) / "intake-manifest.json"


def _file_sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _blocked(failures: list[str]) -> dict[str, Any]:
    return {"status": "BLOCKED", "applied": False, "failures": failures}


def _ledger_paths(quarter: int, week: int) -> dict[str, Path]:
    directory = ledger.deploy_dir(quarter, week)
    return {name: directory / name for name in LEDGER_NAMES}


def _present_ledgers(quarter: int, week: int) -> list[str]:
    return [name for name, path in _ledger_paths(quarter, week).items() if path.exists()]


def _already_corrected(manifest: dict[str, Any], *, expected_manifest_sha256: str, expected_source_hash: str) -> bool:
    if manifest.get("status") != EXPECTED_PRIOR_STATUS:
        return False
    if manifest.get("approval_state") != "PENDING":
        return False
    if manifest.get("ready_to_publish") is not False:
        return False
    if manifest.get("published_at") is not None:
        return False
    if manifest.get("source_hash") != expected_source_hash:
        return False
    corrections = manifest.get("lifecycle_corrections") or []
    return any(
        isinstance(item, dict)
        and item.get("prior_manifest_sha256") == expected_manifest_sha256
        and item.get("original_published_at") == EXPECTED_PUBLISHED_AT
        and item.get("source_hash") == expected_source_hash
        and item.get("to_status") == EXPECTED_PRIOR_STATUS
        for item in corrections
    )


def _preview_failures(preview: dict[str, Any], manifest: dict[str, Any], quarter: int, week: int) -> list[str]:
    failures: list[str] = []
    state = preview.get("existing_state") if isinstance(preview.get("existing_state"), dict) else {}
    expected_state = {
        "status": manifest.get("status"),
        "approval_state": manifest.get("approval_state"),
        "ready_to_publish": manifest.get("ready_to_publish"),
        "published_at": manifest.get("published_at"),
        "source_hash": manifest.get("source_hash"),
        "plan_fingerprint": manifest.get("plan_fingerprint"),
        "history": _history(manifest),
    }
    if state != expected_state:
        failures.append("reconciliation preview does not match the current manifest")
    directory = ledger.deploy_dir(quarter, week)
    evidence = sorted(path.name for path in directory.iterdir()) if directory.exists() else []
    if preview.get("available_evidence") != evidence:
        failures.append("reconciliation preview does not match the current evidence")
    missing = preview.get("missing_evidence") or []
    if any(name not in missing for name in LEDGER_NAMES):
        failures.append("reconciliation preview does not record the missing deployment evidence")
    if preview.get("published_ledger_present") or preview.get("deployment_ledger_present") or preview.get("rollover_ledger_present"):
        failures.append("reconciliation preview reports a ledger that must be absent")
    proposed = preview.get("proposed_corrected_lifecycle") or {}
    if proposed.get("status") != EXPECTED_PRIOR_STATUS or proposed.get("approval_state") != "PENDING":
        failures.append("reconciliation preview proposes an unexpected lifecycle")
    if proposed.get("ready_to_publish") is not False or proposed.get("published_at") is not None:
        failures.append("reconciliation preview proposes an unexpected publication state")
    if preview.get("applied") is not False:
        failures.append("reconciliation preview is already marked applied")
    transition = preview.get("false_transition") or {}
    if transition.get("from") != EXPECTED_PRIOR_STATUS or transition.get("to") != FALSE_STATUS:
        failures.append("reconciliation preview does not record the false lifecycle transition")
    if preview.get("original_published_at") != manifest.get("published_at"):
        failures.append("reconciliation preview does not match the original published_at")
    return failures


def _preconditions(manifest: dict[str, Any], *, expected_source_hash: str) -> list[str]:
    failures: list[str] = []
    if manifest.get("status") != FALSE_STATUS:
        failures.append("lifecycle status is not PUBLISHED_VERIFIED")
    if manifest.get("approval_state") != "PENDING":
        failures.append("approval_state is not PENDING")
    if manifest.get("ready_to_publish") is not True:
        failures.append("ready_to_publish is not true")
    if manifest.get("source_hash") != expected_source_hash:
        failures.append("source hash does not match the expected source")
    if manifest.get("published_at") != EXPECTED_PUBLISHED_AT:
        failures.append("published_at does not match the original false publication timestamp")
    history = _history(manifest)
    if not any(item.get("from") == EXPECTED_PRIOR_STATUS and item.get("to") == FALSE_STATUS for item in history):
        failures.append("history does not contain the false lifecycle transition")
    return failures


def _correction_record(manifest: dict[str, Any], preview: dict[str, Any], *, expected_manifest_sha256: str) -> dict[str, Any]:
    return {
        "action": "FALSE_PUBLISHED_VERIFIED_REVERSAL",
        "at": datetime.now(timezone.utc).isoformat(),
        "from_status": FALSE_STATUS,
        "to_status": EXPECTED_PRIOR_STATUS,
        "original_published_at": manifest.get("published_at"),
        "prior_manifest_sha256": expected_manifest_sha256,
        "source_hash": manifest.get("source_hash"),
        "reason": preview.get("reason"),
        "evidence": {
            "false_transition": preview.get("false_transition"),
            "missing_evidence": [name for name in LEDGER_NAMES],
            "available_evidence": list(preview.get("available_evidence") or []),
        },
    }


def _restore_original(path: Path, original: bytes) -> str | None:
    """Put the original bytes back with a replace, and say so if that fails."""
    recovery = path.with_name(path.name + ".restore")
    try:
        recovery.write_bytes(original)
        if recovery.read_bytes() != original:
            recovery.unlink(missing_ok=True)
            return "manifest restoration readback failed"
        recovery.replace(path)
        if not path.exists() or path.read_bytes() != original:
            return "manifest restoration did not match the original bytes"
        return None
    except OSError as exc:
        recovery.unlink(missing_ok=True)
        return f"manifest restoration failed: {exc}"


def _replace_manifest(path: Path, payload: str, original: bytes) -> tuple[bool, str]:
    partial = path.with_name(path.name + ".partial")
    try:
        partial.write_text(payload, encoding="utf-8")
        if partial.read_text(encoding="utf-8") != payload:
            partial.unlink(missing_ok=True)
            return False, "partial manifest readback is corrupt"
        partial.replace(path)
        if not path.exists() or path.read_text(encoding="utf-8") != payload:
            restored = _restore_original(path, original)
            if restored:
                return False, "manifest readback is corrupt; " + restored
            return False, "manifest readback is corrupt"
        return True, ""
    except OSError as exc:
        partial.unlink(missing_ok=True)
        if not path.exists() or path.read_bytes() != original:
            restored = _restore_original(path, original)
            if restored:
                return False, f"manifest write failed: {exc}; {restored}"
        return False, f"manifest write failed: {exc}"


def apply_correction(
    quarter: int,
    week: int,
    *,
    preview: dict[str, Any],
    expected_manifest_sha256: str,
    expected_source_hash: str,
    apply: bool = False,
) -> dict[str, Any]:
    """Reverse a false published lifecycle, or report the plan without writing.

    ``apply`` defaults to dry-run. A second successful call is idempotent and
    does not write again.
    """
    path = _manifest_path(quarter, week)
    original = path.read_bytes() if path.exists() else None
    digest = hashlib.sha256(original).hexdigest() if original is not None else None
    manifest = json.loads(original.decode("utf-8")) if original is not None else None
    if not isinstance(manifest, dict):
        return _blocked(["intake manifest is missing"])
    present = _present_ledgers(quarter, week)
    if present:
        return _blocked(["unexpected ledger is present: " + ", ".join(present)])
    if _already_corrected(manifest, expected_manifest_sha256=expected_manifest_sha256, expected_source_hash=expected_source_hash):
        return {
            "status": "ALREADY_APPLIED",
            "applied": False,
            "duplicate": True,
            "manifest_sha256": digest,
        }
    if digest != expected_manifest_sha256:
        return _blocked(["manifest hash does not match the expected manifest"])
    failures = _preconditions(manifest, expected_source_hash=expected_source_hash)
    failures.extend(_preview_failures(preview, manifest, quarter, week))
    if failures:
        return _blocked(failures)
    corrected = json.loads(original.decode("utf-8"))
    history = list(corrected.get("history") or [])
    record = _correction_record(corrected, preview, expected_manifest_sha256=expected_manifest_sha256)
    corrected["status"] = EXPECTED_PRIOR_STATUS
    corrected["approval_state"] = "PENDING"
    corrected["ready_to_publish"] = False
    corrected["published_at"] = None
    corrected["history"] = history
    corrected.setdefault("lifecycle_corrections", []).append(record)
    if not apply:
        return {
            "status": "DRY_RUN",
            "applied": False,
            "failures": [],
            "would_set": {
                "status": EXPECTED_PRIOR_STATUS,
                "approval_state": "PENDING",
                "ready_to_publish": False,
                "published_at": None,
                "original_published_at": EXPECTED_PUBLISHED_AT,
            },
        }
    if path.read_bytes() != original:
        return _blocked(["manifest hash changed before the correction was written"])
    payload = json.dumps(corrected, indent=2, ensure_ascii=False) + "\n"
    stored, error = _replace_manifest(path, payload, original)
    if not stored:
        return _blocked([error or "manifest write failed"])
    try:
        readback = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        restored = _restore_original(path, original)
        failure = f"corrected manifest could not be read back: {exc}"
        if restored:
            failure = failure + "; " + restored
        return _blocked([failure])
    if readback.get("status") != EXPECTED_PRIOR_STATUS or readback.get("published_at") is not None:
        restored = _restore_original(path, original)
        failure = "corrected manifest readback does not match the requested lifecycle"
        if restored:
            failure = failure + "; " + restored
        return _blocked([failure])
    if readback.get("history") != history or readback.get("approval_state") != "PENDING":
        restored = _restore_original(path, original)
        failure = "corrected manifest did not preserve history or pending approval"
        if restored:
            failure = failure + "; " + restored
        return _blocked([failure])
    if readback.get("source_hash") != expected_source_hash:
        restored = _restore_original(path, original)
        failure = "source hash changed during correction"
        if restored:
            failure = failure + "; " + restored
        return _blocked([failure])
    return {
        "status": "APPLIED",
        "applied": True,
        "failures": [],
        "manifest_sha256": _file_sha256(path),
        "original_published_at": EXPECTED_PUBLISHED_AT,
    }


def main(argv: list[str] | None = None) -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Review or apply the Q2W5 false lifecycle correction.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true", help="validate the correction and write nothing")
    mode.add_argument("--apply", action="store_true", help="apply the correction to the Q2W5 intake manifest")
    args = parser.parse_args(argv)
    preview = json.loads(PREVIEW_PATH.read_text(encoding="utf-8"))
    result = apply_correction(
        int(preview.get("quarter") or 2),
        int(preview.get("week") or 5),
        preview=preview,
        expected_manifest_sha256=EXPECTED_MANIFEST_SHA256,
        expected_source_hash=EXPECTED_SOURCE_HASH,
        apply=bool(args.apply),
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["status"] in {"DRY_RUN", "APPLIED", "ALREADY_APPLIED"} else 1


def write_preview(path: Path, preview: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(preview, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


if __name__ == "__main__":
    raise SystemExit(main())
