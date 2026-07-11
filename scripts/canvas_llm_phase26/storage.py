from __future__ import annotations

import json
import os
import shutil
import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .models import compact

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LOCAL_ROOT = REPO_ROOT / ".local/canvas-llm/phase-26-unified-weekly-production"
FALLBACK_LOCAL_ROOT = Path(tempfile.gettempdir()) / "teacher-ai-workstation" / "canvas-llm" / "phase-26-unified-weekly-production"


def resolve_local_root() -> Path:
    root = Path(os.environ.get("PHASE26_LOCAL_ROOT") or DEFAULT_LOCAL_ROOT)
    try:
        root.mkdir(parents=True, exist_ok=True)
        probe = root / ".write-check"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        return root
    except Exception:
        fallback = FALLBACK_LOCAL_ROOT
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback


LOCAL_ROOT = resolve_local_root()
DB_PATH = LOCAL_ROOT / "workstation.db"
SCHEMA_VERSION = 1
DEFAULT_WEEK_CODE = "Q1W5"


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def connect(db_path: Path | None = None) -> sqlite3.Connection:
    path = Path(db_path or DB_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        try:
            conn = sqlite3.connect(path)
            conn.execute("PRAGMA quick_check")
            conn.close()
        except Exception:
            quarantine_db(path, "corrupt-db")
            if path.exists():
                path.unlink(missing_ok=True)
    try:
        conn = sqlite3.connect(path)
        conn.row_factory = sqlite3.Row
        ensure_schema(conn, path)
        return conn
    except sqlite3.OperationalError as exc:
        message = str(exc).lower()
        if "readonly" not in message:
            raise
        quarantine_db(path, "readonly-db")
        if path.exists():
            path.unlink(missing_ok=True)
        conn = sqlite3.connect(path)
        conn.row_factory = sqlite3.Row
        ensure_schema(conn, path)
        return conn


def quarantine_db(path: Path, reason: str) -> Path:
    stamp = now_utc().replace(":", "").replace("-", "")
    target_dir = LOCAL_ROOT / "quarantine" / stamp
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        target_dir = Path(tempfile.gettempdir()) / "teacher-ai-workstation" / "canvas-llm" / "phase-26-unified-weekly-production" / "quarantine" / stamp
        target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{path.stem}-{compact(reason)[:24]}.sqlite3"
    try:
        shutil.move(str(path), str(target))
    except Exception:
        if path.exists():
            shutil.copy2(path, target)
            path.unlink(missing_ok=True)
    return target


def backup_db(path: Path) -> Path:
    target_dir = LOCAL_ROOT / "backups"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{path.stem}-{now_utc().replace(':', '').replace('-', '')}.sqlite3"
    if path.exists():
        shutil.copy2(path, target)
    return target


def ensure_schema(conn: sqlite3.Connection, db_path: Path) -> None:
    current_version = int(conn.execute("PRAGMA user_version").fetchone()[0] or 0)
    if current_version < SCHEMA_VERSION and db_path.exists() and db_path.stat().st_size > 0:
        backup_db(db_path)
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS week_state (
            week_code TEXT PRIMARY KEY,
            selected_at TEXT NOT NULL,
            last_generated_at TEXT,
            packet_hash TEXT,
            source_mode TEXT NOT NULL DEFAULT 'demo',
            revision INTEGER NOT NULL DEFAULT 0,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS corrections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kind TEXT NOT NULL,
            week_code TEXT NOT NULL,
            subject TEXT NOT NULL,
            day TEXT NOT NULL,
            field TEXT NOT NULL,
            original_value TEXT,
            edited_value TEXT,
            reason TEXT,
            scope TEXT NOT NULL,
            source_rule TEXT,
            revision INTEGER NOT NULL,
            invalidates_approval INTEGER NOT NULL DEFAULT 1,
            payload_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS approvals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            week_code TEXT NOT NULL,
            scope TEXT NOT NULL,
            subject TEXT,
            status TEXT NOT NULL,
            approved_by TEXT NOT NULL,
            approved_at TEXT NOT NULL,
            packet_revision INTEGER NOT NULL,
            content_hash TEXT NOT NULL,
            active INTEGER NOT NULL DEFAULT 1,
            invalidated_at TEXT,
            invalidated_reason TEXT
        );
        CREATE TABLE IF NOT EXISTS revisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            week_code TEXT NOT NULL,
            revision INTEGER NOT NULL,
            kind TEXT NOT NULL,
            summary TEXT NOT NULL,
            created_at TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS exports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            week_code TEXT NOT NULL,
            export_path TEXT NOT NULL,
            created_at TEXT NOT NULL,
            package_hash TEXT NOT NULL,
            manifest_json TEXT NOT NULL
        );
        """
    )
    conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
    conn.commit()


def get_setting(conn: sqlite3.Connection, key: str, default: str = "") -> str:
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    return str(row["value"]) if row else default


def set_setting(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute(
        "INSERT INTO settings(key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, value),
    )
    conn.commit()


def get_selected_week_code(conn: sqlite3.Connection) -> str:
    return get_setting(conn, "selected_week_code", DEFAULT_WEEK_CODE)


def set_selected_week_code(conn: sqlite3.Connection, week_code: str) -> None:
    set_setting(conn, "selected_week_code", week_code)


def ensure_week_state(conn: sqlite3.Connection, week_code: str, source_mode: str = "demo") -> None:
    conn.execute(
        """
        INSERT INTO week_state(week_code, selected_at, last_generated_at, packet_hash, source_mode, revision, updated_at)
        VALUES (?, ?, NULL, NULL, ?, 0, ?)
        ON CONFLICT(week_code) DO UPDATE SET updated_at = excluded.updated_at
        """,
        (week_code, now_utc(), source_mode, now_utc()),
    )
    conn.commit()


def get_week_state(conn: sqlite3.Connection, week_code: str) -> dict[str, Any]:
    row = conn.execute("SELECT * FROM week_state WHERE week_code = ?", (week_code,)).fetchone()
    if not row:
        ensure_week_state(conn, week_code)
        row = conn.execute("SELECT * FROM week_state WHERE week_code = ?", (week_code,)).fetchone()
    return dict(row)


def touch_week_state(conn: sqlite3.Connection, week_code: str, packet_hash: str, source_mode: str) -> dict[str, Any]:
    current = get_week_state(conn, week_code)
    revision = int(current.get("revision") or 0) + 1
    conn.execute(
        """
        UPDATE week_state
        SET last_generated_at = ?, packet_hash = ?, source_mode = ?, revision = ?, updated_at = ?
        WHERE week_code = ?
        """,
        (now_utc(), packet_hash, source_mode, revision, now_utc(), week_code),
    )
    conn.commit()
    return get_week_state(conn, week_code)


def save_correction(conn: sqlite3.Connection, record: dict[str, Any]) -> dict[str, Any]:
    created_at = str(record.get("timestamp") or now_utc())
    payload_json = json.dumps(record, sort_keys=True, ensure_ascii=False)
    conn.execute(
        """
        INSERT INTO corrections(
            kind, week_code, subject, day, field, original_value, edited_value, reason, scope,
            source_rule, revision, invalidates_approval, payload_json, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            compact(record.get("kind") or "instructional").lower(),
            compact(record.get("weekCode")),
            compact(record.get("subject")),
            compact(record.get("day")),
            compact(record.get("field") or record.get("requiredResourceClass") or "value"),
            record.get("originalValue") or record.get("predictedValue") or record.get("predictedResourceId"),
            record.get("editedValue") or record.get("approvedValue") or record.get("approvedResourceId"),
            record.get("reason", ""),
            compact(record.get("scope") or record.get("correctionScope") or "this occurrence only"),
            record.get("sourceRule", ""),
            int(record.get("revision") or 1),
            1 if record.get("invalidatesApproval", True) else 0,
            payload_json,
            created_at,
        ),
    )
    conn.commit()
    kind = compact(record.get("kind") or "instructional").lower()
    if kind == "instructional":
        invalidate_approvals(conn, record.get("weekCode"), subject=record.get("subject"), reason="approval-invalidated-by-edit")
    elif kind == "resource":
        invalidate_approvals(conn, record.get("weekCode"), subject=record.get("subject"), reason="approval-invalidated-by-resource-change")
    return record


def list_corrections(conn: sqlite3.Connection, week_code: str | None = None, kind: str | None = None) -> list[dict[str, Any]]:
    query = "SELECT * FROM corrections"
    clauses: list[str] = []
    params: list[Any] = []
    if week_code:
        clauses.append("week_code = ?")
        params.append(week_code)
    if kind:
        clauses.append("kind = ?")
        params.append(compact(kind).lower())
    if clauses:
        query += " WHERE " + " AND ".join(clauses)
    query += " ORDER BY id ASC"
    return [dict(row) | {"payload": json.loads(row["payload_json"])} for row in conn.execute(query, params).fetchall()]


def export_phase24_correction_state(conn: sqlite3.Connection, week_code: str) -> dict[str, Any]:
    records = [
        {
            **row["payload"],
            "subject": row["subject"],
            "weekCode": row["week_code"],
            "day": row["day"],
            "predictedValue": row["original_value"],
            "approvedValue": row["edited_value"],
            "correctionScope": row["scope"],
            "timestamp": row["created_at"],
            "reason": row["reason"],
            "sourceRule": row["source_rule"],
            "revision": row["revision"],
        }
        for row in list_corrections(conn, week_code, "instructional")
    ]
    return {"weekCode": week_code, "status": "saved", "version": len(records), "records": records, "updatedAt": now_utc()}


def export_phase25_corrections(conn: sqlite3.Connection, week_code: str) -> dict[str, Any]:
    return {"version": len(list_corrections(conn, week_code, "resource")), "records": [row["payload"] for row in list_corrections(conn, week_code, "resource")]}


def save_approval(
    conn: sqlite3.Connection,
    week_code: str,
    scope: str,
    subject: str | None,
    status: str,
    approved_by: str = "local-owner",
    packet_revision: int = 0,
    content_hash: str = "",
) -> dict[str, Any]:
    conn.execute(
        """
        INSERT INTO approvals(week_code, scope, subject, status, approved_by, approved_at, packet_revision, content_hash, active)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
        """,
        (week_code, scope, subject, status, approved_by, now_utc(), packet_revision, content_hash),
    )
    conn.commit()
    return {"weekCode": week_code, "scope": scope, "subject": subject, "status": status, "approvedBy": approved_by, "approvedAt": now_utc(), "packetRevision": packet_revision, "contentHash": content_hash, "active": True}


def invalidate_approvals(conn: sqlite3.Connection, week_code: str | None, subject: str | None = None, reason: str = "approval-invalidated-by-edit") -> None:
    if not week_code:
        return
    params: list[Any] = [now_utc(), reason, week_code]
    subject_clause = ""
    if subject:
        subject_clause = " AND (subject = ? OR scope = 'full-week')"
        params.append(subject)
    conn.execute(
        f"UPDATE approvals SET active = 0, invalidated_at = ?, invalidated_reason = ? WHERE week_code = ?{subject_clause} AND active = 1",
        params,
    )
    conn.commit()


def list_approvals(conn: sqlite3.Connection, week_code: str | None = None) -> list[dict[str, Any]]:
    query = "SELECT * FROM approvals"
    params: list[Any] = []
    if week_code:
        query += " WHERE week_code = ?"
        params.append(week_code)
    query += " ORDER BY id ASC"
    return [dict(row) for row in conn.execute(query, params).fetchall()]


def active_approvals(conn: sqlite3.Connection, week_code: str) -> list[dict[str, Any]]:
    return [row for row in list_approvals(conn, week_code) if int(row["active"]) == 1]


def record_revision(conn: sqlite3.Connection, week_code: str, kind: str, summary: str, payload: dict[str, Any]) -> dict[str, Any]:
    existing = conn.execute("SELECT COALESCE(MAX(revision), 0) AS revision FROM revisions WHERE week_code = ?", (week_code,)).fetchone()
    revision = int(existing["revision"] or 0) + 1
    record = {
        "weekCode": week_code,
        "revision": revision,
        "kind": kind,
        "summary": summary,
        "createdAt": now_utc(),
        "payload": payload,
    }
    conn.execute(
        "INSERT INTO revisions(week_code, revision, kind, summary, created_at, payload_json) VALUES (?, ?, ?, ?, ?, ?)",
        (week_code, revision, kind, summary, record["createdAt"], json.dumps(payload, sort_keys=True, ensure_ascii=False)),
    )
    conn.commit()
    return record


def list_revisions(conn: sqlite3.Connection, week_code: str) -> list[dict[str, Any]]:
    rows = conn.execute("SELECT * FROM revisions WHERE week_code = ? ORDER BY revision ASC", (week_code,)).fetchall()
    return [
        {
            "weekCode": row["week_code"],
            "revision": row["revision"],
            "kind": row["kind"],
            "summary": row["summary"],
            "createdAt": row["created_at"],
            "payload": json.loads(row["payload_json"]),
        }
        for row in rows
    ]


def record_export(conn: sqlite3.Connection, week_code: str, export_path: str, package_hash: str, manifest: dict[str, Any]) -> dict[str, Any]:
    conn.execute(
        "INSERT INTO exports(week_code, export_path, created_at, package_hash, manifest_json) VALUES (?, ?, ?, ?, ?)",
        (week_code, export_path, now_utc(), package_hash, json.dumps(manifest, sort_keys=True, ensure_ascii=False)),
    )
    conn.commit()
    return {"weekCode": week_code, "exportPath": export_path, "createdAt": now_utc(), "packageHash": package_hash, "manifest": manifest}


def list_exports(conn: sqlite3.Connection, week_code: str) -> list[dict[str, Any]]:
    rows = conn.execute("SELECT * FROM exports WHERE week_code = ? ORDER BY id ASC", (week_code,)).fetchall()
    return [
        {
            "weekCode": row["week_code"],
            "exportPath": row["export_path"],
            "createdAt": row["created_at"],
            "packageHash": row["package_hash"],
            "manifest": json.loads(row["manifest_json"]),
        }
        for row in rows
    ]


def state_summary(conn: sqlite3.Connection, week_code: str) -> dict[str, Any]:
    week_state = get_week_state(conn, week_code)
    return {
        "weekState": week_state,
        "correctionCount": len(list_corrections(conn, week_code)),
        "approvalCount": len(list_approvals(conn, week_code)),
        "revisionCount": len(list_revisions(conn, week_code)),
        "exportCount": len(list_exports(conn, week_code)),
    }
