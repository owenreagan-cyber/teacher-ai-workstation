#!/usr/bin/env python3
"""Canvas launch wrapper — GET-only preflight and guarded corrective deployment.

Entrypoint for ``bin/canvas-launch``.

- ``--preflight <week-code>``: fresh live GET only, zero writes, prints the
  proposed action list plus duplicate/drift results.
- ``--approve <week-code>``: set teacher approval on the manifest (zero Canvas
  writes).
- ``--unapprove <week-code>``: clear teacher approval on the manifest (zero
  Canvas writes).
- ``<week-code>`` (normal launch): requires explicit teacher approval in the
  manifest. Without approval it blocks immediately (no live GET, no writes).
  When approved it runs the guarded sequence:
  fresh live preflight -> backup -> duplicate/drift check -> approved manifest
  only -> apply -> live verification.

Seeded weekly pages are update-in-place only; this launcher never recreates an
existing page.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.canvas_llm_phase22 import canvas_credentials as credentials  # noqa: E402

MANIFESTS: dict[str, Path] = {
    "Q1W5": REPO_ROOT / ".local" / "canvas-llm" / "q1w5-audit" / "q1w5-corrective-manifest.json",
}

BACKUP_DIR = REPO_ROOT / ".local" / "canvas-llm" / "backups"

NEW_YORK_TZ = ZoneInfo("America/New_York")

# Actions that touch Canvas at all (write-bearing). LEAVE requires no write.
WRITE_ACTIONS = ("CREATE", "UPDATE", "REMOVE", "PUBLISH")
CREATE_ONLY = ("CREATE",)
UNSUPPORTED_WRITE_ACTIONS = ("PUBLISH",)


class LaunchError(RuntimeError):
    """Raised when a launch precondition fails (never contains a token)."""


def manifest_path(week_code: str) -> Path:
    path = MANIFESTS.get(week_code.upper())
    if path is None:
        raise LaunchError(f"no manifest registered for week-code {week_code}")
    return path


def load_manifest(week_code: str) -> dict[str, Any]:
    path = manifest_path(week_code)
    if not path.exists():
        raise LaunchError(f"no manifest registered for week-code {week_code}")
    return json.loads(path.read_text())


def manifest_approved(manifest: dict[str, Any]) -> bool:
    approval = manifest.get("approval") or {}
    approved = bool(approval.get("teacherApproved"))
    by = (approval.get("approvedBy") or "").strip()
    return approved and bool(by)


def _actions(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    return list(manifest.get("actions") or [])


def _fetch_live_inventory(*, test_mode: bool = False) -> dict[str, Any]:
    """Fresh live GET of all canonical courses. Read-only; self-contained module."""
    if test_mode:
        return _fake_inventory()
    from scripts.canvas_llm_phase22 import canvas_live_inventory as inventory

    return inventory.fetch_live_inventory()


def _fake_inventory() -> dict[str, Any]:
    """Build a preflight-compatible inventory from the fake transport store."""
    from scripts.canvas_llm_phase22 import canvas_connection_manager as transport

    courses: dict[str, dict[str, Any]] = {}
    for item in transport.transport_inventory_objects():
        cid = str(item.get("course_id"))
        bucket = courses.setdefault(cid, {"pages": [], "assignments": [], "announcements": []})
        object_type = item.get("object_type")
        if object_type == "page":
            bucket["pages"].append(
                {
                    "page_id": item.get("id"),
                    "url": item.get("url"),
                    "title": item.get("title"),
                    "published": item.get("published"),
                    "body": item.get("body"),
                }
            )
        elif object_type == "assignment":
            bucket["assignments"].append(
                {
                    "id": item.get("id"),
                    "name": item.get("name") or item.get("title"),
                    "due_at": item.get("due_at"),
                    "published": item.get("published"),
                    "omit_from_final_grade": item.get("omit_from_final_grade"),
                }
            )
        elif object_type == "announcement":
            bucket["announcements"].append(
                {
                    "id": item.get("id"),
                    "title": item.get("title"),
                    "message": item.get("message"),
                    "published": item.get("published"),
                }
            )
    return {"courses": courses}


def _course_inventory(inventory: dict[str, Any], course_id: int) -> dict[str, Any]:
    return (inventory.get("courses") or {}).get(str(course_id)) or {}


def _objects(inventory: dict[str, Any], course_id: int, object_type: str) -> list[dict[str, Any]]:
    course = _course_inventory(inventory, course_id)
    if object_type == "page":
        return list(course.get("pages") or [])
    if object_type == "assignment":
        return list(course.get("assignments") or [])
    if object_type == "announcement":
        return list(course.get("announcements") or [])
    return []


def _title_of(obj: dict[str, Any], object_type: str) -> str:
    if object_type == "assignment":
        return str(obj.get("name") or obj.get("title") or "").strip()
    return str(obj.get("title") or "").strip()


def _id_of(obj: dict[str, Any], object_type: str) -> Any:
    if object_type == "page":
        return obj.get("page_id")
    return obj.get("id")


def _find_by_id(objects: list[dict[str, Any]], object_type: str, object_id: Any) -> dict[str, Any] | None:
    target = str(object_id)
    for obj in objects:
        if str(_id_of(obj, object_type)) == target:
            return obj
    return None


def _match_existing(objects: list[dict[str, Any]], object_type: str, existing: str) -> list[dict[str, Any]]:
    """Match a manifest `existing` reference. Pages reference their URL slug; others their title/id."""
    ref = existing.strip()
    if object_type == "page":
        return [
            obj for obj in objects
            if (obj.get("url") or "").strip() == ref
            or _title_of(obj, "page") == ref
            or str(obj.get("page_id") or "") == ref
        ]
    if object_type == "assignment":
        return [
            obj for obj in objects
            if _title_of(obj, "assignment") == ref
            or str(obj.get("id") or "") == ref
        ]
    return [obj for obj in objects if _title_of(obj, object_type) == ref]


def _exact_title_matches(objects: list[dict[str, Any]], object_type: str, title: str) -> list[dict[str, Any]]:
    target = title.strip()
    return [obj for obj in objects if _title_of(obj, object_type) == target]


def _norm(text: Any) -> str:
    return " ".join(str(text or "").split())


def _locate(
    objects: list[dict[str, Any]],
    object_type: str,
    existing_id: Any,
    existing: str,
) -> tuple[dict[str, Any] | None, bool]:
    """Locate the live object referenced by existing_id (preferred) or existing title/slug.

    Returns ``(found, multiple)``. ``multiple`` is True when an id-less reference
    matches more than one live object (duplicate).
    """
    if existing_id is not None:
        return _find_by_id(objects, object_type, existing_id), False
    if existing:
        matches = _match_existing(objects, object_type, existing)
        if len(matches) == 1:
            return matches[0], False
        if len(matches) > 1:
            return None, True
    return None, False


def _analyze_update(
    action: dict[str, Any],
    objects: list[dict[str, Any]],
    object_type: str,
    existing_id: Any,
    existing: str,
    resulting: str,
    result: dict[str, Any],
) -> dict[str, Any]:
    """Determine whether an UPDATE is pending or already in the desired final state."""
    found: dict[str, Any] | None = None
    if existing_id is not None:
        found = _find_by_id(objects, object_type, existing_id)
    if found is None and existing:
        by_existing = _match_existing(objects, object_type, existing)
        if len(by_existing) == 1:
            found = by_existing[0]
        elif len(by_existing) > 1:
            result["blocker"] = "DUPLICATE"
            result["status"] = "PENDING"
            return result
    if found is None and resulting and resulting != existing:
        by_resulting = _exact_title_matches(objects, object_type, resulting)
        if len(by_resulting) == 1:
            found = by_resulting[0]

    if found is None:
        result["blocker"] = "DRIFT"
        result["status"] = "PENDING"
        return result

    live_title = _title_of(found, object_type)
    result["matches"] = 1
    result["live_title"] = live_title

    rename = bool(resulting and resulting != existing)
    if rename and live_title == resulting:
        title_ok = True  # rename already applied
    elif rename and live_title == existing:
        title_ok = False  # rename still pending
    elif not rename:
        title_ok = True  # no title change requested
    else:
        result["drift_title"] = live_title
        result["blocker"] = "DRIFT"
        result["status"] = "PENDING"
        return result

    already_applied = title_ok

    omit = action.get("omit_from_final_grade")
    if omit is not None:
        live_omit = found.get("omit_from_final_grade")
        if live_omit is None or bool(live_omit) != bool(omit):
            already_applied = False

    published = action.get("published")
    if published is not None and found.get("published") != published:
        already_applied = False

    body = action.get("body")
    if body is not None:
        live_body = found.get("body")
        if live_body is None or _norm(live_body) != _norm(body):
            already_applied = False

    message = action.get("message")
    if message is not None:
        live_message = found.get("message")
        if live_message is None or _norm(live_message) != _norm(message):
            already_applied = False

    result["status"] = "ALREADY_APPLIED" if already_applied else "PENDING"
    return result


def analyze_action(action: dict[str, Any], inventory: dict[str, Any]) -> dict[str, Any]:
    """Return a per-action check result: status, matches, and any blocker."""
    object_type = action.get("object_type")
    course_id = action.get("course_id")
    act = action.get("action")
    objects = _objects(inventory, course_id, object_type)
    existing_id = action.get("existing_id")
    existing = (action.get("existing") or "").strip()
    resulting = (action.get("resulting_title") or "").strip()

    result: dict[str, Any] = {"action": act, "object_type": object_type, "blocker": None, "status": "PENDING"}

    if act == "CREATE":
        matches = _exact_title_matches(objects, object_type, resulting)
        result["matches"] = len(matches)
        if len(matches) > 1:
            result["blocker"] = "DUPLICATE"
        elif len(matches) == 1:
            result["reuse_id"] = _id_of(matches[0], object_type)
            result["status"] = "ALREADY_APPLIED"
        return result

    if act == "REMOVE":
        found, multiple = _locate(objects, object_type, existing_id, existing)
        result["matches"] = 0 if found is None else 1
        if multiple:
            result["blocker"] = "DUPLICATE"
        elif found is None:
            result["status"] = "ALREADY_REMOVED"
        return result

    if act == "UPDATE":
        return _analyze_update(action, objects, object_type, existing_id, existing, resulting, result)

    if act in ("LEAVE", "ALREADY_APPLIED", "ALREADY_REMOVED"):
        result["status"] = act
    return result


def run_preflight(week_code: str, inventory: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    """Analyze the manifest against a live inventory (read-only)."""
    manifest = load_manifest(week_code)
    rows: list[dict[str, Any]] = []
    blockers: list[str] = []
    for action in _actions(manifest):
        check = analyze_action(action, inventory)
        rows.append({**action, "check": check})
        if check["blocker"]:
            blockers.append(
                f"{action.get('course')} {action.get('object_type')} "
                f"'{action.get('existing') or action.get('resulting_title')}': {check['blocker']}"
            )
    return rows, blockers


def print_preflight_report(week_code: str, rows: list[dict[str, Any]], blockers: list[str]) -> None:
    print("Q1W5 CORRECTIVE DEPLOYMENT PREVIEW" if week_code == "Q1W5" else f"{week_code} DEPLOYMENT PREVIEW")
    print()
    for row in rows:
        check = row.get("check") or {}
        title = row.get("existing") or row.get("resulting_title") or "(new)"
        status = check.get("status") or row.get("action")
        flag = check.get("blocker") or ""
        suffix = f" [{flag}]" if flag else f" [{status}]"
        print(
            f"{row.get('course')} | {row.get('object_type')} | {row.get('action')} | "
            f"{title} | -> {row.get('resulting_title')} | {row.get('timing') or '-'}{suffix}"
        )
    print()

    def _status(rows_: list[dict[str, Any]]) -> str:
        return (rows_.get("check") or {}).get("status") or rows_.get("action")

    already_applied = [r for r in rows if _status(r) == "ALREADY_APPLIED"]
    already_removed = [r for r in rows if _status(r) == "ALREADY_REMOVED"]
    pending_writes = [
        r for r in rows
        if r.get("action") in WRITE_ACTIONS and _status(r) == "PENDING"
    ]

    print(f"ALREADY APPLIED: {len(already_applied)}")
    for r in already_applied:
        print(f"  {r.get('course')} {r.get('object_type')} '{r.get('existing') or r.get('resulting_title')}'")
    print(f"ALREADY REMOVED: {len(already_removed)}")
    for r in already_removed:
        print(f"  {r.get('course')} {r.get('object_type')} '{r.get('existing') or r.get('resulting_title')}'")
    print(f"REMAINING WRITE ACTIONS: {len(pending_writes)}")
    for r in pending_writes:
        group = r.get("assignment_group")
        group_suffix = f" [group: {group}]" if group else ""
        print(
            f"  {r.get('course')} {r.get('object_type')} {r.get('action')} "
            f"'{r.get('existing') or r.get('resulting_title')}'{group_suffix}"
        )
    print()
    print(f"WRITES PERFORMED: 0 (proposed write actions: {len(pending_writes)})")
    print(f"BLOCKERS: {len(blockers)}")
    for blocker in blockers:
        print(f"  {blocker}")


def command_preflight(week_code: str) -> int:
    credentials.load_credentials()
    inventory = _fetch_live_inventory()
    rows, blockers = run_preflight(week_code, inventory)
    print_preflight_report(week_code, rows, blockers)
    return 0


def _write_backup(week_code: str, inventory: dict[str, Any], backup_dir: Path | None = None) -> Path:
    target_dir = backup_dir or BACKUP_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = target_dir / f"{week_code.lower()}-{stamp}.json"
    path.write_text(json.dumps(inventory, indent=2) + "\n")
    return path


def _new_title(row: dict[str, Any]) -> str | None:
    existing = (row.get("existing") or "").strip()
    resulting = (row.get("resulting_title") or "").strip()
    if resulting and resulting != existing:
        return resulting
    return None


def _apply_approved(
    rows: list[dict[str, Any]],
    *,
    test_mode: bool = False,
    client: Any = None,
) -> int:
    """Apply approved, write-bearing actions through the guarded live writer.

    CREATE delegates to the live writer for assignments/announcements only;
    page CREATE is forbidden (weekly pages are update-in-place). UPDATE/REMOVE
    delegate to the new transport-backed update/delete writer functions.
    """
    from scripts.canvas_llm_phase22 import canvas_writer as writer

    writes = 0
    for row in rows:
        act = row.get("action")
        object_type = row.get("object_type")
        course_id = row.get("course_id")
        check_status = (row.get("check") or {}).get("status")
        if check_status in ("ALREADY_APPLIED", "ALREADY_REMOVED"):
            print(f"NO-OP ({check_status}): {row.get('course')} {object_type} "
                  f"'{row.get('existing') or row.get('resulting_title')}'")
            continue
        if act not in WRITE_ACTIONS:
            continue
        if act in UNSUPPORTED_WRITE_ACTIONS:
            print(f"BLOCKED (unsupported action {act}): {row.get('course')} "
                  f"{object_type} '{row.get('existing') or row.get('resulting_title')}'")
            continue

        res: writer.CanvasWriteResult | None = None

        if object_type == "page" and act == "CREATE":
            print(f"BLOCKED: page creation is forbidden (pages are update-in-place only): "
                  f"{row.get('resulting_title')}")
            continue

        if object_type == "assignment":
            if act == "CREATE":
                res = writer.create_assignment_live(
                    course_id=course_id,
                    title=row.get("resulting_title"),
                    description=row.get("description") or "",
                    assignment_group=row.get("assignment_group") or "Homework/Class Work",
                    due_at=row.get("due_at") or "",
                    counts_toward_final_grade=not bool(row.get("omit_from_final_grade", False)),
                    approved=True,
                    test_mode=test_mode,
                    client=client,
                )
            elif act == "UPDATE":
                new_title = _new_title(row)
                omit = row.get("omit_from_final_grade")
                due = row.get("due_at") or None
                published = row.get("published")
                if new_title is None and omit is None and due is None and published is None:
                    print(f"SKIPPED (no payload fields): {row.get('course')} assignment "
                          f"'{row.get('existing')}'")
                    continue
                res = writer.update_assignment_live(
                    course_id=course_id,
                    assignment_id=str(row.get("existing_id")),
                    title=row.get("existing") or row.get("resulting_title"),
                    new_title=new_title,
                    due_at=due,
                    omit_from_final_grade=omit,
                    published=published,
                    approved=True,
                    test_mode=test_mode,
                    client=client,
                )
            elif act == "REMOVE":
                res = writer.delete_assignment_live(
                    course_id=course_id,
                    assignment_id=str(row.get("existing_id")),
                    title=row.get("existing") or "",
                    approved=True,
                    test_mode=test_mode,
                    client=client,
                )

        elif object_type == "announcement":
            if act == "CREATE":
                res = writer.create_announcement_live(
                    course_id=course_id,
                    title=row.get("resulting_title"),
                    message=row.get("message") or "",
                    published=row.get("published") if row.get("published") is not None else True,
                    delayed_post_at=row.get("delayed_post_at"),
                    approved=True,
                    test_mode=test_mode,
                    client=client,
                )
            elif act == "UPDATE":
                new_title = _new_title(row)
                message = row.get("message")
                published = row.get("published")
                if new_title is None and message is None and published is None:
                    print(f"SKIPPED (no payload fields): {row.get('course')} announcement "
                          f"'{row.get('existing')}'")
                    continue
                res = writer.update_announcement_live(
                    course_id=course_id,
                    topic_id=str(row.get("existing_id")),
                    title=row.get("existing") or row.get("resulting_title"),
                    new_title=new_title,
                    message=message,
                    published=published,
                    approved=True,
                    test_mode=test_mode,
                    client=client,
                )
            elif act == "REMOVE":
                res = writer.delete_announcement_live(
                    course_id=course_id,
                    topic_id=str(row.get("existing_id")),
                    title=row.get("existing") or "",
                    approved=True,
                    test_mode=test_mode,
                    client=client,
                )

        elif object_type == "page" and act == "UPDATE":
            new_title = _new_title(row)
            body = row.get("body")
            published = row.get("published")
            if new_title is None and body is None and published is None:
                print(f"SKIPPED (no payload fields): {row.get('course')} page "
                      f"'{row.get('existing') or row.get('resulting_title')}'")
                continue
            res = writer.update_page_live(
                course_id=course_id,
                page_ref=row.get("existing") or row.get("resulting_title"),
                title=row.get("resulting_title") or row.get("existing") or "",
                new_title=new_title,
                body=body,
                published=published,
                approved=True,
                test_mode=test_mode,
                client=client,
            )

        if res is None:
            res = writer.CanvasWriteResult(
                target_type=object_type,
                target_id="",
                course_id=course_id,
                title=row.get("resulting_title"),
                body_hash="",
                write_status="BLOCKED",
                gate_state="BLOCKED",
                blockers=["unsupported_write"],
            )

        if getattr(res, "write_status", "BLOCKED") == "WRITTEN":
            writes += 1
            print(f"WRITTEN: {row.get('course')} {object_type} {row.get('resulting_title')}")
        else:
            print(f"BLOCKED: {row.get('course')} {object_type} {row.get('resulting_title')} "
                  f"({', '.join(getattr(res, 'blockers', []) or ['blocked'])})")
    return writes


def _build_live_client() -> Any:
    """Instantiate the real Canvas client after approval + credentials are confirmed.

    Reads only os.environ; performs no network I/O. Raises RuntimeError if
    credentials are absent (mirrors require_live_prerequisites' missing-cred gate).
    """
    from scripts.canvas_llm_phase22 import canvas_connection_manager as transport

    return transport.Phase22LiveCanvasClient.from_env()


def command_launch(week_code: str, *, test_mode: bool = False) -> int:
    manifest = load_manifest(week_code)
    if not manifest_approved(manifest):
        print(f"BLOCKED: manifest for {week_code} is not teacher-approved.")
        print("Set approval.teacherApproved=true and approval.approvedBy in the manifest.")
        print("WRITES PERFORMED: 0")
        return 1

    live_client = None
    if not test_mode:
        try:
            credentials.load_credentials()
        except credentials.CredentialError as exc:
            print(f"BLOCKED: {exc}")
            print("WRITES PERFORMED: 0")
            return 1
        try:
            live_client = _build_live_client()
        except RuntimeError as exc:
            print(f"BLOCKED: {exc}")
            print("WRITES PERFORMED: 0")
            return 1

    inventory = _fetch_live_inventory(test_mode=test_mode)
    rows, blockers = run_preflight(week_code, inventory)
    if blockers:
        print_preflight_report(week_code, rows, blockers)
        print("STOPPED: duplicate/drift detected; no writes performed.")
        print("WRITES PERFORMED: 0")
        return 1

    try:
        backup_path = _write_backup(week_code, inventory)
    except OSError as exc:
        print(f"BLOCKED: backup failed before write: {exc}")
        print("WRITES PERFORMED: 0")
        return 1
    print(f"Backup written: {backup_path}")

    # Re-check drift between the preflight snapshot and the moment of write.
    fresh = _fetch_live_inventory(test_mode=test_mode)
    _, recheck_blockers = run_preflight(week_code, fresh)
    if recheck_blockers:
        print("STOPPED: drift detected between preflight and write; no writes performed.")
        for blocker in recheck_blockers:
            print(f"  {blocker}")
        print("WRITES PERFORMED: 0")
        return 1

    writes = _apply_approved(rows, test_mode=test_mode, client=live_client)
    print(f"WRITES PERFORMED: {writes}")
    return 0


def _now_new_york_iso() -> str:
    return datetime.now(NEW_YORK_TZ).isoformat()


def _write_manifest_backup(path: Path, backup_dir: Path | None = None) -> Path:
    """Copy the current manifest bytes before any approval mutation."""
    target_dir = backup_dir or BACKUP_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = target_dir / f"approval-{path.stem}-{stamp}.json"
    backup.write_text(path.read_text())
    return backup


def _atomic_write_json(path: Path, data: dict[str, Any]) -> None:
    """Serialize, validate the payload round-trips, then atomically replace the file."""
    text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    json.loads(text)  # validate before touching the original
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=f"{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as fh:
            fh.write(text)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def set_approval(
    week_code: str,
    *,
    approved: bool,
    backup_dir: Path | None = None,
) -> tuple[dict[str, Any], Path]:
    """Set (or clear) teacher approval on a manifest. Read-modify-write only.

    Loads the manifest (raising on malformed JSON), backs up the original bytes,
    replaces the approval block, then writes atomically. No Canvas interaction.
    """
    path = manifest_path(week_code)
    if not path.exists():
        raise LaunchError(f"manifest not found: {path}")
    manifest = json.loads(path.read_text())  # raises JSONDecodeError if malformed

    backup = _write_manifest_backup(path, backup_dir=backup_dir)

    if approved:
        approval: dict[str, Any] = {
            "teacherApproved": True,
            "approvedBy": "Owen Reagan",
            "approvedAt": _now_new_york_iso(),
        }
    else:
        approval = {
            "teacherApproved": False,
            "approvedBy": None,
            "approvedAt": None,
        }
    manifest["approval"] = approval
    _atomic_write_json(path, manifest)
    return approval, backup


def command_approve(week_code: str) -> int:
    try:
        approval, backup = set_approval(week_code, approved=True)
    except (json.JSONDecodeError, LaunchError) as exc:
        print(f"BLOCKED: {exc}")
        return 1
    print(f"Backup written: {backup}")
    print("Approval:")
    print(json.dumps(approval, indent=2))
    return 0


def command_unapprove(week_code: str) -> int:
    try:
        approval, backup = set_approval(week_code, approved=False)
    except (json.JSONDecodeError, LaunchError) as exc:
        print(f"BLOCKED: {exc}")
        return 1
    print(f"Backup written: {backup}")
    print("Approval cleared:")
    print(json.dumps(approval, indent=2))
    return 0


def command_self_test() -> int:
    manifest = load_manifest("Q1W5")
    assert manifest.get("weekCode") == "Q1W5"

    # Manifest must never recreate a seeded page.
    page_creates = [
        a for a in _actions(manifest)
        if a.get("object_type") == "page" and a.get("action") == "CREATE"
    ]
    assert not page_creates, "manifest must never recreate pages"

    # Approval-gate logic is hermetic (never depends on the real manifest's
    # current approval state, which a teacher may legitimately toggle).
    assert manifest_approved({"approval": {"teacherApproved": True, "approvedBy": "Owen Reagan"}}) is True
    assert manifest_approved({"approval": {"teacherApproved": False, "approvedBy": None}}) is False
    assert manifest_approved({"approval": {"teacherApproved": True, "approvedBy": ""}}) is False

    # Launch must block without approval, independent of real manifest state.
    from unittest import mock

    unapproved = {
        "weekCode": "Q1W5",
        "approval": {"teacherApproved": False, "approvedBy": None},
        "actions": [],
    }
    with mock.patch.object(sys.modules[__name__], "load_manifest", return_value=unapproved):
        assert command_launch("Q1W5") == 1

    # Synthetic inventory exercises duplicate/drift detection offline.
    inventory: dict[str, Any] = {
        "courses": {
            "26404": {
                "pages": [],
                "assignments": [
                    {"id": 1027213, "name": "SM5: Lesson 15"},
                    {"id": 1027212, "name": "SM5: Lesson 14"},
                ],
                "announcements": [],
            },
            "26442": {
                "pages": [],
                "assignments": [],
                "announcements": [],
            },
        }
    }
    rows, blockers = run_preflight("Q1W5", inventory)
    assert blockers, "expected drift blockers against synthetic inventory"
    dup = analyze_action(
        {
            "course": "Math",
            "course_id": 26404,
            "object_type": "assignment",
            "existing": None,
            "existing_id": None,
            "action": "CREATE",
            "resulting_title": "SM5: Lesson 15",
        },
        inventory,
    )
    assert dup["matches"] == 1, "expected duplicate match for existing title"

    # Resumability: already-renamed UPDATE, absent REMOVE, and existing CREATE
    # are reconciled without a write or a drift blocker.
    res_inv: dict[str, Any] = {
        "courses": {
            "26404": {
                "pages": [],
                "assignments": [{"id": 1027216, "name": "SM5: Written Assessment 2"}],
                "announcements": [],
            },
        }
    }
    renamed = analyze_action(
        {
            "course": "Math", "course_id": 26404, "object_type": "assignment",
            "existing": "SM5: Math Test 2", "existing_id": 1027216,
            "action": "UPDATE", "resulting_title": "SM5: Written Assessment 2",
        },
        res_inv,
    )
    assert renamed["status"] == "ALREADY_APPLIED", renamed
    removed = analyze_action(
        {
            "course": "Math", "course_id": 26404, "object_type": "assignment",
            "existing": "SM5: Lesson 17", "existing_id": 1027215,
            "action": "REMOVE", "resulting_title": "(removed)",
        },
        res_inv,
    )
    assert removed["status"] == "ALREADY_REMOVED", removed
    created = analyze_action(
        {
            "course": "Math", "course_id": 26404, "object_type": "assignment",
            "action": "CREATE", "resulting_title": "SM5: Written Assessment 2",
        },
        res_inv,
    )
    assert created["status"] == "ALREADY_APPLIED", created

    print("PASS canvas launcher self-test")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Canvas launch wrapper")
    parser.add_argument("--preflight", action="store_true", help="GET-only preview; zero writes")
    parser.add_argument("--approve", action="store_true", help="set teacher approval on the manifest; zero Canvas writes")
    parser.add_argument("--unapprove", action="store_true", help="clear teacher approval on the manifest; zero Canvas writes")
    parser.add_argument("week_code", nargs="?", default=None, help="week code, e.g. Q1W5")
    args = parser.parse_args(argv)
    if not args.week_code:
        parser.error("week-code required (e.g. Q1W5)")
    week_code = args.week_code.upper()
    if week_code == "SELF-TEST":
        return command_self_test()
    if args.approve:
        return command_approve(week_code)
    if args.unapprove:
        return command_unapprove(week_code)
    if args.preflight:
        return command_preflight(week_code)
    return command_launch(week_code)


if __name__ == "__main__":
    raise SystemExit(main())
