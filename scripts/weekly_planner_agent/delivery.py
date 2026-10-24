"""Notification delivery abstraction for the Weekly Planner Agent.

Connects the existing ``notification_model`` drafts to a delivery contract
without coupling content to a specific email provider. Delivery sinks:

- ``preview`` — generate the notification, send nothing (status DRAFTED).
- ``local``  — write to a local outbox + record to a fake/local sink (QUEUED).
- ``email``  — real delivery adapter, DISABLED by default (FAILED if disabled).

A notification is NEVER marked DELIVERED simply because it was generated or
placed in the local outbox: DRAFTED and QUEUED are distinct from DELIVERED.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.canvas_planner.state_root import planner_root

from . import schedule_config
from .models import (
    NOTIFICATION_DELIVERED,
    NOTIFICATION_DRAFTED,
    NOTIFICATION_FAILED,
    NOTIFICATION_QUEUED,
    NOTIFICATION_SUPPRESSED,
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def outbox_path() -> Path:
    return planner_root() / "agent" / "notifications" / "outbox.jsonl"


def new_notification_id() -> str:
    return str(uuid.uuid4())


def idempotency_key(notification_type: str, *related_ids: str) -> str:
    """Stable idempotency key so repeated polls don't re-deliver the same event."""
    parts = [notification_type, *sorted(str(x) for x in related_ids if x)]
    return "|".join(parts)


def make_record(
    *,
    notification_type: str,
    subject: str,
    body: str,
    recipient: str | None = None,
    review_link: str | None = None,
    related_event_ids: list[str] | None = None,
    plan_version: str | None = None,
    actions: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "notification_id": new_notification_id(),
        "notification_type": notification_type,
        "recipient": recipient or "",
        "subject": subject,
        "body": body,
        "review_link": review_link or "",
        "actions": actions or [],
        "idempotency_key": idempotency_key(notification_type, *(related_event_ids or [])),
        "created_at": _now(),
        "status": NOTIFICATION_DRAFTED,
        "attempts": [],
        "error": None,
        "related_event_ids": list(related_event_ids or []),
        "plan_version": plan_version or "",
    }


def _append_outbox(record: dict[str, Any]) -> None:
    path = outbox_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def read_outbox() -> list[dict[str, Any]]:
    path = outbox_path()
    if not path.exists():
        return []
    out: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def already_delivered(key: str) -> bool:
    """True when a record with this idempotency key is QUEUED/DELIVERED."""
    for record in read_outbox():
        if record.get("idempotency_key") == key and record.get("status") in (
            NOTIFICATION_QUEUED, NOTIFICATION_DELIVERED,
        ):
            return True
    return False


class PreviewSink:
    """Send nothing; mark the record DRAFTED (generated, not delivered)."""

    mode = "preview"

    def deliver(self, record: dict[str, Any]) -> dict[str, Any]:
        record["status"] = NOTIFICATION_DRAFTED
        return record


class LocalSink:
    """Write to the local outbox + fake/local sink; mark QUEUED (not DELIVERED)."""

    mode = "local"

    def deliver(self, record: dict[str, Any]) -> dict[str, Any]:
        record["status"] = NOTIFICATION_QUEUED
        _append_outbox(record)
        return record


class EmailSink:
    """Real email delivery adapter. DISABLED by default and fail-closed."""

    mode = "email"

    def __init__(self, *, enabled: bool = False, recipient: str = "", from_address: str = "") -> None:
        self.enabled = bool(enabled)
        self.recipient = recipient
        self.from_address = from_address

    def deliver(self, record: dict[str, Any]) -> dict[str, Any]:
        if not self.enabled:
            record["status"] = NOTIFICATION_FAILED
            record["error"] = "EMAIL_DISABLED"
            return record
        if not record.get("recipient") and not self.recipient:
            record["status"] = NOTIFICATION_FAILED
            record["error"] = "RECIPIENT_MISSING"
            return record
        if not self.from_address:
            record["status"] = NOTIFICATION_FAILED
            record["error"] = "FROM_MISSING"
            return record
        # No real SMTP in this phase; a real adapter would be wired here behind
        # an explicit config gate. Until then, real delivery is never attempted.
        record["status"] = NOTIFICATION_FAILED
        record["error"] = "EMAIL_TRANSPORT_NOT_WIRED"
        return record


def build_sink(mode: str | None = None) -> Any:
    cfg = schedule_config.delivery_config()
    chosen = mode or cfg.get("mode") or "preview"
    if chosen == "local":
        return LocalSink()
    if chosen == "email":
        return EmailSink(
            enabled=bool(cfg.get("email_enabled")),
            recipient=str(cfg.get("email_recipient") or ""),
            from_address=str(cfg.get("email_from") or ""),
        )
    return PreviewSink()


def deliver(
    record: dict[str, Any],
    *,
    mode: str | None = None,
    sink: Any = None,
) -> dict[str, Any]:
    """Deliver a notification record through the selected sink.

    Idempotency: if this record's idempotency key has already been QUEUED/
    DELIVERED, the record is SUPPRESSED (no duplicate delivery).
    """
    key = record.get("idempotency_key")
    if key and already_delivered(key):
        record["status"] = NOTIFICATION_SUPPRESSED
        record["error"] = "DUPLICATE_SUPPRESSED"
        return record

    delivery_sink = sink if sink is not None else build_sink(mode)
    record["attempts"] = list(record.get("attempts") or [])
    record["attempts"].append({"at": _now(), "mode": getattr(delivery_sink, "mode", mode)})
    return delivery_sink.deliver(record)


def command_self_test() -> int:
    import tempfile
    from pathlib import Path

    global planner_root
    orig = planner_root
    tmp = Path(tempfile.mkdtemp())
    planner_root = lambda: tmp
    try:
        # preview sends nothing.
        rec = make_record(notification_type="assessment_date_changed",
                          subject="Math test date changed", body="body")
        out = deliver(rec, mode="preview")
        assert out["status"] == NOTIFICATION_DRAFTED
        # local records deterministically and stays QUEUED (not DELIVERED).
        rec2 = make_record(notification_type="assessment_date_changed",
                           subject="s", body="b")
        out2 = deliver(rec2, mode="local")
        assert out2["status"] == NOTIFICATION_QUEUED
        assert outbox_path().exists()
        # idempotency: same key again -> SUPPRESSED.
        rec3 = make_record(notification_type="assessment_date_changed",
                           subject="s", body="b")
        rec3["idempotency_key"] = rec2["idempotency_key"]
        out3 = deliver(rec3, mode="local")
        assert out3["status"] == NOTIFICATION_SUPPRESSED
        # email disabled by default -> FAILED (not delivered).
        rec4 = make_record(notification_type="pacing_changed",
                           subject="s", body="b", related_event_ids=["other"])
        out4 = deliver(rec4, mode="email")
        assert out4["status"] == NOTIFICATION_FAILED and out4["error"] == "EMAIL_DISABLED"
    finally:
        planner_root = orig
    print("PASS weekly-planner-agent delivery self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(command_self_test())
