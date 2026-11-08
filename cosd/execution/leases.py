"""Worker lease ownership."""
from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

LEASE_TTL_S = 30.0


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def _parse(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def new_worker_id() -> str:
    return secrets.token_hex(8)


def _expires_from_now() -> str:
    return (datetime.now(timezone.utc) + timedelta(seconds=LEASE_TTL_S)).isoformat(timespec="milliseconds")


def lease_expired(expires_at: str) -> bool:
    return datetime.now(timezone.utc) >= _parse(expires_at)


def acquire_lease(conn, *, task_id: str, worker_id: str, attempt_id: int) -> dict[str, Any]:
    existing = conn.execute(
        "SELECT * FROM worker_leases WHERE task_id = ? AND state = 'active'", (task_id,)
    ).fetchone()
    if existing and not lease_expired(existing["expires_at"]):
        raise RuntimeError("task already has active lease")
    if existing:
        conn.execute(
            "UPDATE worker_leases SET state = 'expired' WHERE lease_id = ?", (existing["lease_id"],)
        )
    now = _utc_now()
    exp = _expires_from_now()
    lease_id = secrets.token_hex(12)
    conn.execute(
        """INSERT INTO worker_leases(
            lease_id, task_id, worker_id, attempt_id, acquired_at, expires_at, heartbeat_at, state
        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'active')""",
        (lease_id, task_id, worker_id, attempt_id, now, exp, now),
    )
    return {"lease_id": lease_id, "worker_id": worker_id, "expires_at": exp}


def renew_lease(conn, *, lease_id: str, worker_id: str) -> None:
    row = conn.execute("SELECT * FROM worker_leases WHERE lease_id = ?", (lease_id,)).fetchone()
    if not row or row["state"] != "active" or row["worker_id"] != worker_id:
        raise RuntimeError("lease not owned by worker")
    now = _utc_now()
    conn.execute(
        "UPDATE worker_leases SET heartbeat_at = ?, expires_at = ? WHERE lease_id = ?",
        (now, _expires_from_now(), lease_id),
    )


def release_lease(conn, *, lease_id: str, worker_id: str, state: str = "released") -> None:
    row = conn.execute("SELECT * FROM worker_leases WHERE lease_id = ?", (lease_id,)).fetchone()
    if not row:
        return
    if row["worker_id"] != worker_id:
        raise RuntimeError("cannot release another worker's lease")
    conn.execute("UPDATE worker_leases SET state = ? WHERE lease_id = ?", (state, lease_id))


def expire_stale_leases(conn) -> list[str]:
    now = _utc_now()
    rows = conn.execute(
        "SELECT lease_id FROM worker_leases WHERE state = 'active' AND expires_at < ?", (now,)
    ).fetchall()
    ids = [r["lease_id"] for r in rows]
    for lid in ids:
        conn.execute("UPDATE worker_leases SET state = 'expired' WHERE lease_id = ?", (lid,))
    return ids
