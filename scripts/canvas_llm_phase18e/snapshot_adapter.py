"""Read-only live Canvas snapshot adapter (Phase 18E, optional).

This module connects Phase 18D snapshot contracts to the *existing* approved
read-only Canvas infrastructure. It introduces no second HTTP client, no raw
``requests``, no account crawl, and no mutation methods.

The connector is injected by the caller (typically the Phase 22 read-only
``CanvasConnector``) rather than imported here, so this module stays pure and
never transitively loads the writer or any mutation transport.
"""

from __future__ import annotations

from typing import Any, Protocol

from scripts.canvas_llm_phase18d.contracts import CanvasSnapshot, DeploymentIntent, SnapshotObject
from scripts.canvas_llm_phase27.canonicalize import canonical_hash

# Keys that must never be persisted from a live read payload.
_CREDENTIAL_KEYS = ("token", "access_token", "authorization", "api_key", "secret", "password")


class ReadOnlyCanvasClient(Protocol):
    """Duck-typed read-only Canvas client (no mutation methods)."""

    def read_page(self, course_id: int, page_ref: str) -> Any: ...
    def read_assignment(self, course_id: int, assignment_id: str) -> Any: ...
    def read_announcement(self, course_id: int, announcement_id: str) -> Any: ...


def _to_dict(record: Any) -> dict[str, Any]:
    """Convert a connector record/dataclass/dict to a plain dict, dropping secrets."""
    if isinstance(record, dict):
        raw = record
    elif hasattr(record, "to_dict") and callable(record.to_dict):
        raw = record.to_dict()
    else:
        raw = {k: getattr(record, k) for k in dir(record) if not k.startswith("_")}
    return {k: v for k, v in raw.items() if k.lower() not in _CREDENTIAL_KEYS}


def _content_hash(title: str, extra: Any = None) -> str:
    return canonical_hash({"title": title, "extra": extra})


def _read_object(connector: ReadOnlyCanvasClient, intent: DeploymentIntent, course_id: int) -> SnapshotObject | None:
    """Read exactly one object for an intent's logical target; None if absent."""
    locator = intent.target_locator
    if intent.object_type == "agenda_page":
        d = _to_dict(connector.read_page(course_id, locator))
        title = str(d.get("title") or "")
        body = str(d.get("body_html") or d.get("body") or "")
        return SnapshotObject(
            object_id=str(d.get("page_id") or d.get("object_id") or f"page-{locator}"),
            object_type="agenda_page",
            course=intent.course,
            locator=locator,
            title=title,
            current_state={
                "course_id": str(d.get("course_id") or course_id),
                "title": title,
                "body": body,
                "published": d.get("published"),
                "front_page": d.get("front_page"),
            },
            content_hash=_content_hash(title, body),
            managed=False,
            baseline_hash="",
        )
    if intent.object_type == "assignment":
        d = _to_dict(connector.read_assignment(course_id, locator))
        title = str(d.get("title") or d.get("name") or "")
        return SnapshotObject(
            object_id=str(d.get("assignment_id") or d.get("object_id") or f"assignment-{locator}"),
            object_type="assignment",
            course=intent.course,
            locator=locator,
            title=title,
            current_state={
                "course_id": str(d.get("course_id") or course_id),
                "title": title,
                "due_at": d.get("due_at"),
                "published": d.get("published"),
                "submission_type": d.get("submission_type"),
            },
            content_hash=_content_hash(title, d.get("due_at")),
            managed=False,
            baseline_hash="",
        )
    if intent.object_type == "announcement":
        d = _to_dict(connector.read_announcement(course_id, locator))
        title = str(d.get("title") or "")
        body = str(d.get("message_html") or d.get("body") or "")
        return SnapshotObject(
            object_id=str(d.get("announcement_id") or d.get("object_id") or f"announcement-{locator}"),
            object_type="announcement",
            course=intent.course,
            locator=locator,
            title=title,
            current_state={
                "course_id": str(d.get("course_id") or course_id),
                "title": title,
                "body": body,
            },
            content_hash=_content_hash(title, body),
            managed=False,
            baseline_hash="",
        )
    return None


def capture_snapshot(
    connector: ReadOnlyCanvasClient,
    *,
    week_code: str,
    intents: list[DeploymentIntent],
    course_ids: dict[str, int],
    managed_locators: set[str] | None = None,
) -> CanvasSnapshot:
    """Fetch only the necessary objects for the given intents (no account crawl).

    Partial fetch, malformed result, or read failure are surfaced as
    ``fetch_errors`` / ``read_failure`` so the affected scope blocks downstream.
    """
    managed = managed_locators or set()
    objects: list[SnapshotObject] = []
    fetch_errors: list[str] = []
    read_failure = False
    read_failure_reason = ""

    for intent in intents:
        course_id = course_ids.get(intent.course)
        if not course_id:
            fetch_errors.append(intent.course)
            continue
        try:
            obj = _read_object(connector, intent, course_id)
            if obj is None:
                continue
            if intent.target_locator in managed:
                obj.managed = True
                obj.baseline_hash = obj.content_hash
            objects.append(obj)
        except Exception as exc:  # fail closed on any read failure
            fetch_errors.append(intent.course)
            read_failure = True
            read_failure_reason = f"read failed for {intent.course}/{intent.object_type}: {exc}"

    return CanvasSnapshot(
        week_code=week_code,
        snapshot_id="snapshot-live-" + canonical_hash([week_code, [i.id for i in intents]])[:16],
        objects=objects,
        fetch_errors=sorted(set(fetch_errors)),
        read_failure=read_failure,
        read_failure_reason=read_failure_reason,
    )


__all__ = [
    "ReadOnlyCanvasClient",
    "capture_snapshot",
]
