"""Durable pairing rate limiting (same SQLite database)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from ..models import DeviceError, utc_now


def _parse(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


class PairingRateLimiter:
    def __init__(self, db) -> None:
        self._db = db

    def consume(
        self,
        bucket: str,
        *,
        limit: int,
        window_seconds: int,
        now: datetime | None = None,
    ) -> None:
        if not bucket or len(bucket) > 128:
            raise DeviceError("invalid rate-limit bucket")
        if limit <= 0 or window_seconds <= 0:
            raise DeviceError("invalid rate-limit configuration")
        current = now or datetime.now(timezone.utc)
        stamp = current.astimezone(timezone.utc).isoformat(timespec="milliseconds")
        with self._db.transaction() as conn:
            row = conn.execute(
                "SELECT * FROM pairing_rate_limits WHERE bucket = ?", (bucket,)
            ).fetchone()
            blocked = _parse(row["blocked_until"]) if row else None
            if blocked is not None and blocked > current:
                raise DeviceError(
                    "too many pairing attempts; try again later",
                    kind="rate_limited",
                    http_status=429,
                )
            started = _parse(row["window_started_at"]) if row else None
            if row is None or started is None or current - started >= timedelta(seconds=window_seconds):
                conn.execute(
                    "INSERT INTO pairing_rate_limits(bucket, window_started_at, attempts, blocked_until) "
                    "VALUES (?, ?, 1, NULL) "
                    "ON CONFLICT(bucket) DO UPDATE SET window_started_at = excluded.window_started_at, "
                    "attempts = 1, blocked_until = NULL",
                    (bucket, stamp),
                )
                return
            attempts = int(row["attempts"]) + 1
            if attempts > limit:
                until = (current + timedelta(seconds=window_seconds)).astimezone(
                    timezone.utc
                ).isoformat(timespec="milliseconds")
                conn.execute(
                    "UPDATE pairing_rate_limits SET attempts = ?, blocked_until = ? WHERE bucket = ?",
                    (attempts, until, bucket),
                )
                raise DeviceError(
                    "too many pairing attempts; try again later",
                    kind="rate_limited",
                    http_status=429,
                )
            conn.execute(
                "UPDATE pairing_rate_limits SET attempts = ?, blocked_until = NULL WHERE bucket = ?",
                (attempts, bucket),
            )

    def reset(self, bucket: str) -> None:
        with self._db.transaction() as conn:
            conn.execute("DELETE FROM pairing_rate_limits WHERE bucket = ?", (bucket,))

    @staticmethod
    def now() -> str:
        return utc_now()
