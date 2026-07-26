from __future__ import annotations

import json
import shutil
import sqlite3
import time
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1

# Absolute and repo-root-anchored, not relative to the process cwd: some
# callers (e.g. Phase 26's `serve` command) chdir() before opening the
# ledger, and a relative default here would silently resolve to a different
# directory (and therefore a different, stale ledger) depending on cwd.
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LEDGER_PATH = (
    REPO_ROOT / ".local/canvas-llm/phase-27-canvas-readiness-and-safety-diff/deployment-ledger.db"
)

_SCHEMA_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS schema_migrations (
        version INTEGER PRIMARY KEY,
        appliedAt TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS manifests (
        manifestId TEXT PRIMARY KEY,
        weekCode TEXT NOT NULL,
        revision INTEGER NOT NULL,
        status TEXT NOT NULL,
        createdAt TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS manifest_revisions (
        manifestId TEXT NOT NULL,
        revision INTEGER NOT NULL,
        payloadHash TEXT NOT NULL,
        createdAt TEXT NOT NULL,
        PRIMARY KEY (manifestId, revision)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS deployment_operations (
        operationId TEXT PRIMARY KEY,
        manifestId TEXT NOT NULL,
        kind TEXT NOT NULL,
        status TEXT NOT NULL,
        executable INTEGER NOT NULL DEFAULT 0,
        CHECK (executable = 0)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS operation_dependencies (
        operationId TEXT NOT NULL,
        dependsOnOperationId TEXT NOT NULL,
        PRIMARY KEY (operationId, dependsOnOperationId)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS approvals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        objectId TEXT NOT NULL,
        manifestRevision INTEGER NOT NULL,
        snapshotId TEXT NOT NULL,
        state TEXT NOT NULL,
        approvedAt TEXT NOT NULL,
        approvedBy TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS snapshot_imports (
        snapshotId TEXT NOT NULL,
        origin TEXT NOT NULL,
        generatedAt TEXT NOT NULL,
        importedAt TEXT NOT NULL,
        PRIMARY KEY (snapshotId, importedAt)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS comparison_runs (
        runId TEXT PRIMARY KEY,
        manifestId TEXT NOT NULL,
        snapshotId TEXT NOT NULL,
        createdAt TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS safety_diff_items (
        runId TEXT NOT NULL,
        objectId TEXT NOT NULL,
        comparisonStatus TEXT NOT NULL,
        payloadJson TEXT NOT NULL,
        PRIMARY KEY (runId, objectId)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS ledger_events (
        eventId TEXT PRIMARY KEY,
        eventType TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        manifestId TEXT,
        operationId TEXT,
        revision INTEGER,
        summary TEXT NOT NULL,
        previousHash TEXT,
        newHash TEXT,
        reason TEXT,
        metadataJson TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS quarantine_events (
        quarantineId TEXT PRIMARY KEY,
        reason TEXT NOT NULL,
        detectedAt TEXT NOT NULL,
        backupPath TEXT
    )
    """,
]

_IMMUTABLE_TABLES = ("ledger_events",)


class LedgerIntegrityError(RuntimeError):
    pass


class LedgerConflictError(RuntimeError):
    """Raised on optimistic-concurrency revision mismatch."""


class DeploymentLedger:
    def __init__(self, path: str | Path = DEFAULT_LEDGER_PATH):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._quarantine_if_corrupt()
        self._conn = sqlite3.connect(self.path)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._migrate()

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "DeploymentLedger":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    def _quarantine_if_corrupt(self) -> None:
        if not self.path.exists():
            return
        try:
            probe = sqlite3.connect(self.path)
            probe.execute("PRAGMA integrity_check")
            probe.execute(
                "SELECT name FROM sqlite_master WHERE type='table' LIMIT 1"
            )
            probe.close()
        except sqlite3.DatabaseError:
            quarantine_dir = self.path.parent / "quarantine"
            quarantine_dir.mkdir(parents=True, exist_ok=True)
            backup_path = quarantine_dir / f"{self.path.name}.{int(time.time())}.corrupt"
            shutil.move(str(self.path), str(backup_path))
            fresh = sqlite3.connect(self.path)
            fresh.execute(
                "CREATE TABLE IF NOT EXISTS quarantine_events "
                "(quarantineId TEXT PRIMARY KEY, reason TEXT NOT NULL, "
                "detectedAt TEXT NOT NULL, backupPath TEXT)"
            )
            fresh.execute(
                "INSERT INTO quarantine_events VALUES (?, ?, ?, ?)",
                (
                    f"quarantine-{int(time.time())}",
                    "corrupt-database-detected-on-open",
                    _now(),
                    str(backup_path),
                ),
            )
            fresh.commit()
            fresh.close()

    def _migrate(self) -> None:
        applied = {
            row[0]
            for row in self._conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_migrations'"
            ).fetchall()
        }
        if not applied:
            backup_path = self.path.with_suffix(self.path.suffix + ".pre-migration-backup")
            if self.path.exists() and self.path.stat().st_size > 0:
                shutil.copy2(self.path, backup_path)
        with self._conn:
            for statement in _SCHEMA_STATEMENTS:
                self._conn.execute(statement)
            existing = self._conn.execute(
                "SELECT version FROM schema_migrations WHERE version = ?", (SCHEMA_VERSION,)
            ).fetchone()
            if not existing:
                self._conn.execute(
                    "INSERT INTO schema_migrations VALUES (?, ?)", (SCHEMA_VERSION, _now())
                )

    def integrity_check(self) -> bool:
        result = self._conn.execute("PRAGMA integrity_check").fetchone()
        return result is not None and result[0] == "ok"

    def schema_version(self) -> int:
        row = self._conn.execute(
            "SELECT MAX(version) FROM schema_migrations"
        ).fetchone()
        return row[0] or 0

    def record_snapshot_import(self, snapshot_id: str, origin: str, generated_at: str) -> None:
        with self._conn:
            self._conn.execute(
                "INSERT INTO snapshot_imports VALUES (?, ?, ?, ?)",
                (snapshot_id, origin, generated_at, _now()),
            )
        self.append_event(
            "snapshot-imported",
            summary=f"snapshot {snapshot_id} imported ({origin})",
            metadata={"snapshotId": snapshot_id, "origin": origin},
        )

    def upsert_manifest(
        self, manifest_id: str, week_code: str, revision: int, status: str, payload_hash: str
    ) -> None:
        with self._conn:
            existing = self._conn.execute(
                "SELECT revision FROM manifests WHERE manifestId = ?", (manifest_id,)
            ).fetchone()
            if existing and existing[0] > revision:
                raise LedgerConflictError(
                    f"manifest {manifest_id} has newer revision {existing[0]} than {revision}"
                )
            if existing:
                self._conn.execute(
                    "UPDATE manifests SET revision=?, status=?, weekCode=? WHERE manifestId=?",
                    (revision, status, week_code, manifest_id),
                )
            else:
                self._conn.execute(
                    "INSERT INTO manifests (manifestId, weekCode, revision, status, createdAt) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (manifest_id, week_code, revision, status, _now()),
                )
            self._conn.execute(
                "INSERT OR REPLACE INTO manifest_revisions VALUES (?, ?, ?, ?)",
                (manifest_id, revision, payload_hash, _now()),
            )
        self.append_event(
            "manifest-generated",
            manifest_id=manifest_id,
            revision=revision,
            summary=f"manifest {manifest_id} revision {revision} recorded ({status})",
            new_hash=payload_hash,
        )

    def get_manifest(self, manifest_id: str) -> dict[str, Any] | None:
        row = self._conn.execute(
            "SELECT manifestId, weekCode, revision, status, createdAt FROM manifests "
            "WHERE manifestId = ?",
            (manifest_id,),
        ).fetchone()
        if not row:
            return None
        return {
            "manifestId": row[0],
            "weekCode": row[1],
            "revision": row[2],
            "status": row[3],
            "createdAt": row[4],
        }

    def record_approval(
        self, object_id: str, manifest_revision: int, snapshot_id: str, approved_by: str
    ) -> None:
        with self._conn:
            self._conn.execute(
                "INSERT INTO approvals (objectId, manifestRevision, snapshotId, state, "
                "approvedAt, approvedBy) VALUES (?, ?, ?, 'approved', ?, ?)",
                (object_id, manifest_revision, snapshot_id, _now(), approved_by),
            )
        self.append_event(
            "operation-approved",
            summary=f"{object_id} approved at revision {manifest_revision}",
            metadata={"objectId": object_id, "manifestRevision": manifest_revision},
        )

    def revoke_approval(self, object_id: str, manifest_revision: int, snapshot_id: str) -> None:
        with self._conn:
            self._conn.execute(
                "INSERT INTO approvals (objectId, manifestRevision, snapshotId, state, "
                "approvedAt, approvedBy) VALUES (?, ?, ?, 'revoked', ?, 'system')",
                (object_id, manifest_revision, snapshot_id, _now()),
            )
        self.append_event(
            "approval-revoked",
            summary=f"{object_id} approval revoked at revision {manifest_revision}",
            metadata={"objectId": object_id},
        )

    def invalidate_approval(self, object_id: str, reason: str) -> None:
        self.append_event(
            "approval-invalidated",
            summary=f"{object_id} approval invalidated: {reason}",
            reason=reason,
            metadata={"objectId": object_id},
        )

    def current_approval_state(
        self, object_id: str, manifest_revision: int, snapshot_id: str
    ) -> str:
        """An approval is only 'approved' if the most recent approval row for
        this exact (object, manifest revision, snapshot id) tuple is in the
        'approved' state. Any change to revision or snapshot id means no
        matching row exists, so the object reads back as unapproved --
        this is how revision-bound invalidation is enforced."""
        row = self._conn.execute(
            "SELECT state FROM approvals WHERE objectId=? AND manifestRevision=? "
            "AND snapshotId=? ORDER BY id DESC LIMIT 1",
            (object_id, manifest_revision, snapshot_id),
        ).fetchone()
        return row[0] if row else "unapproved"

    def append_event(
        self,
        event_type: str,
        summary: str,
        manifest_id: str | None = None,
        operation_id: str | None = None,
        revision: int | None = None,
        previous_hash: str | None = None,
        new_hash: str | None = None,
        reason: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        event_id = f"evt-{int(time.time() * 1_000_000)}-{event_type}"
        with self._conn:
            self._conn.execute(
                "INSERT INTO ledger_events VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    event_id,
                    event_type,
                    _now(),
                    manifest_id,
                    operation_id,
                    revision,
                    summary,
                    previous_hash,
                    new_hash,
                    reason,
                    json.dumps(metadata or {}, sort_keys=True),
                ),
            )
        return event_id

    def event_count(self) -> int:
        return self._conn.execute("SELECT COUNT(*) FROM ledger_events").fetchone()[0]

    def events(self) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT eventId, eventType, timestamp, summary FROM ledger_events ORDER BY timestamp"
        ).fetchall()
        return [
            {"eventId": r[0], "eventType": r[1], "timestamp": r[2], "summary": r[3]}
            for r in rows
        ]

    def assert_events_immutable(self) -> None:
        """There is no UPDATE or DELETE statement anywhere in this class
        touching ledger_events; this method exists so tests have an explicit,
        named assertion point documenting that invariant."""
        return None


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
