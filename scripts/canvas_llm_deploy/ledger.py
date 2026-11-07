"""Local deployment ledger + preflight records + backups (untracked, no secrets)."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.canvas_llm_intake import manifest as imf
from scripts.canvas_planner.state_root import deployment_root

DEPLOY_ROOT = deployment_root()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def deploy_dir(quarter: int, week: int) -> Path:
    from scripts.canvas_llm_storage import active_roots
    root = active_roots().deploy_root if active_roots() else DEPLOY_ROOT
    return root / "2026-2027" / f"q{quarter}" / f"w{week}"


def write_json(path: Path, data: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def write_preflight(quarter: int, week: int, preflight: dict[str, Any]) -> Path:
    return write_json(deploy_dir(quarter, week) / f"preflight-{preflight['preflight_id']}.json", preflight)


def load_preflight(quarter: int, week: int, preflight_id: str) -> dict[str, Any] | None:
    return read_json(deploy_dir(quarter, week) / f"preflight-{preflight_id}.json")


def write_ledger(quarter: int, week: int, ledger: dict[str, Any]) -> Path:
    return write_json(deploy_dir(quarter, week) / "deployment-ledger.json", ledger)


def load_ledger(quarter: int, week: int) -> dict[str, Any] | None:
    return read_json(deploy_dir(quarter, week) / "deployment-ledger.json")


def write_backup(quarter: int, week: int, name: str, data: dict[str, Any]) -> Path:
    return write_json(deploy_dir(quarter, week) / "backups" / f"{name}.json", data)


REQUIRED_COURSES = ("math", "reading_spelling", "language_arts", "science", "homeroom")
VERIFIED_DISPOSITIONS = {"PUBLISHED_VERIFIED", "SCHEDULED_VERIFIED", "ALREADY_EXISTS", "UPDATED_VERIFIED"}


def load_published_verified(quarter: int, week: int) -> dict[str, Any] | None:
    return read_json(deploy_dir(quarter, week) / "published-verified-ledger.json")


def _under(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def storage_split(quarter: int, week: int) -> bool:
    """True when one root is the real local tree and the other is not."""
    from scripts.canvas_llm_storage import canonical_deploy_root, canonical_intake_root
    intake = Path(imf.staging_dir(quarter, week))
    deploy = deploy_dir(quarter, week)
    return _under(intake, canonical_intake_root()) != _under(deploy, canonical_deploy_root())


def _blocked(failures: list[str]) -> dict[str, Any]:
    return {"status": "BLOCKED", "failures": failures, "path": None}


def validate_publication_evidence(
    report: dict[str, Any] | None,
    manifest: dict[str, Any] | None,
) -> list[str]:
    """Return every reason this report cannot finalize a week."""
    failures: list[str] = []
    if not isinstance(report, dict):
        return ["deployment report is missing"]
    if not isinstance(manifest, dict):
        return ["intake manifest is missing"]
    verified_flag = report.get("status") or report.get("deployment_state") or report.get("lifecycle")
    if verified_flag != "PUBLISHED_VERIFIED":
        failures.append("deployment report is not verified")
    if report.get("failures") or report.get("blockers"):
        failures.append("deployment report has outstanding blockers")
    if not report.get("source_hash"):
        failures.append("deployment source hash is missing")
    elif report.get("source_hash") != manifest.get("source_hash"):
        failures.append("deployment source hash does not match the intake manifest")
    if not report.get("plan_fingerprint"):
        failures.append("deployment plan fingerprint is missing")
    elif report.get("plan_fingerprint") != manifest.get("plan_fingerprint"):
        failures.append("deployment plan fingerprint does not match the intake manifest")
    if manifest.get("approval_state") != "APPROVED":
        failures.append("intake approval is not explicitly approved")
    if manifest.get("status") not in ("READY_TO_PUBLISH", "PUBLISHED_VERIFIED"):
        failures.append("intake status is not ready to publish")

    verified_subjects: set[str] = set()
    pages = report.get("pages")
    if not isinstance(pages, list):
        failures.append("page verification is missing")
    else:
        for page in pages:
            subject = page.get("subject")
            if page.get("verified") is not True:
                failures.append(f"page {subject} is not verified")
            else:
                verified_subjects.add(str(subject))
    homeroom = report.get("homeroom") if isinstance(report.get("homeroom"), dict) else None
    if homeroom and homeroom.get("verified") is True:
        verified_subjects.add("homeroom")
    missing = [course for course in REQUIRED_COURSES if course not in verified_subjects]
    if missing:
        failures.append("verified courses are missing " + ", ".join(missing))

    announcements = report.get("weekly_announcements")
    if not isinstance(announcements, list):
        failures.append("announcement verification is missing")
    else:
        for item in announcements:
            disposition = item.get("disposition")
            if item.get("verified") is not True or (
                disposition is not None and disposition not in VERIFIED_DISPOSITIONS
            ):
                failures.append(f"announcement {item.get('title') or item.get('subject')} is not verified")
    family = report.get("homeroom_announcement")
    if isinstance(family, dict):
        if not (homeroom and homeroom.get("verified") is True):
            failures.append("homeroom announcement was not verified after its page")
        if family.get("verified") is not True:
            failures.append("homeroom announcement is not verified")
        if report.get("homeroom_page_before_announcement") is not True:
            failures.append("homeroom page was not verified before its announcement")

    assignments = report.get("assignments")
    if not isinstance(assignments, list):
        failures.append("assignment verification is missing")
    else:
        for item in assignments:
            if item.get("verified") is not True:
                failures.append(f"assignment {item.get('title')} is not verified")
    return failures


def _commit_published_ledger(path: Path, report: dict[str, Any]) -> tuple[bool, str]:
    """Write the ledger atomically and require the canonical file to read back."""
    payload = json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    partial = path.with_name(path.name + ".partial")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        partial.write_text(payload, encoding="utf-8")
        if partial.read_text(encoding="utf-8") != payload:
            partial.unlink(missing_ok=True)
            return False, "partial ledger readback is corrupt"
        partial.replace(path)
        if not path.exists():
            return False, "published ledger is missing after write"
        if path.read_text(encoding="utf-8") != payload:
            return False, "published ledger readback is corrupt"
        loaded = read_json(path)
        if loaded != report:
            return False, "published ledger readback does not match the report"
        return True, ""
    except OSError as exc:
        partial.unlink(missing_ok=True)
        return False, f"published ledger write failed: {exc}"


def finalize_published_verified(quarter: int, week: int, report: dict[str, Any]) -> dict[str, Any]:
    """Finalize a verified deployment, then advance the intake manifest.

    Evidence is validated before any intake write. A failed ledger write or
    readback leaves the intake manifest untouched.
    """
    if storage_split(quarter, week):
        return _blocked(["storage roots are split between real intake data and another deployment root"])
    manifest = imf.load_manifest(quarter, week)
    before = json.loads(json.dumps(manifest)) if isinstance(manifest, dict) else None
    failures = validate_publication_evidence(report, manifest)
    if failures:
        return _blocked(failures)
    assert isinstance(manifest, dict)

    path = deploy_dir(quarter, week) / "published-verified-ledger.json"
    existing = read_json(path) if path.exists() else None
    if manifest.get("status") == "PUBLISHED_VERIFIED":
        if existing == report:
            return {"status": "PUBLISHED_VERIFIED", "failures": [], "path": str(path), "duplicate": True}
        return _blocked(["published ledger does not match the existing finalization"])

    stored, error = _commit_published_ledger(path, report)
    if not stored:
        if existing is None and path.exists():
            path.unlink(missing_ok=True)
        elif existing is not None:
            write_json(path, existing)
        return _blocked([error or "published ledger write failed"])

    confirmed = read_json(path)
    if confirmed != report:
        return _blocked(["published ledger was not readable after write"])

    published_at = _now()
    current = manifest.get("status")
    manifest["status"] = "PUBLISHED_VERIFIED"
    manifest["published_at"] = published_at
    manifest.setdefault("history", []).append({
        "from": current,
        "to": "PUBLISHED_VERIFIED",
        "at": published_at,
    })
    manifest["ready_to_publish"] = manifest.get("approval_state") == "APPROVED"
    manifest.setdefault("finalization_history", []).append({
        "at": published_at,
        "source_hash": report.get("source_hash"),
        "plan_fingerprint": report.get("plan_fingerprint"),
        "ledger": path.name,
    })
    imf.save_manifest(quarter, week, manifest)
    saved = imf.load_manifest(quarter, week)
    if not isinstance(saved, dict) or saved.get("status") != "PUBLISHED_VERIFIED":
        if before is not None:
            imf.save_manifest(quarter, week, before)
        return _blocked(["intake manifest did not persist the verified lifecycle"])
    return {"status": "PUBLISHED_VERIFIED", "failures": [], "path": str(path)}


def command_self_test() -> int:
    import tempfile

    orig = imf.staging_dir
    global DEPLOY_ROOT
    orig_root = DEPLOY_ROOT
    with tempfile.TemporaryDirectory() as tmp:
        # Point both staging + deploy roots at the temp dir.
        DEPLOY_ROOT = Path(tmp) / "deployments"
        # manifest staging_dir affects finalize; use a separate temp for manifest.
        imf.staging_dir = lambda q, w: Path(tmp) / "intake" / f"q{q}w{w}"
        try:
            pre = {"preflight_id": "pf123", "plan": {}}
            assert write_preflight(2, 3, pre).exists()
            assert load_preflight(2, 3, "pf123")["preflight_id"] == "pf123"
            write_ledger(2, 3, {"deployment_state": "DEPLOYING"})
            assert load_ledger(2, 3)["deployment_state"] == "DEPLOYING"
            write_backup(2, 3, "math-page-before", {"body": "x"})
            assert (deploy_dir(2, 3) / "backups" / "math-page-before.json").exists()
            m = imf.new_manifest(quarter=2, week=3, week_code="Q2W3",
                                 date_range={"start": "2026-10-26", "end": "2026-10-30"})
            m["status"] = "READY_TO_PUBLISH"
            imf.save_manifest(2, 3, m)
            refused = finalize_published_verified(2, 3, {"status": "PUBLISHED_VERIFIED"})
            assert refused["status"] == "BLOCKED"
            assert imf.load_manifest(2, 3)["status"] == "READY_TO_PUBLISH"
        finally:
            imf.staging_dir = orig
            DEPLOY_ROOT = orig_root
    print("PASS canvas-deploy ledger self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(command_self_test())
