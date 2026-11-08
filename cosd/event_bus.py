"""Bounded in-process event bus for cosd (SSE clients in P1b.2)."""
from __future__ import annotations

import itertools
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Callable, Deque

MAX_BUFFER = 256
MAX_SUBSCRIBERS = 8


@dataclass
class CosdEvent:
    id: int
    type: str
    ts: str
    task_id: str | None = None
    title: str | None = None
    detail: dict[str, Any] = field(default_factory=dict)

    def sse_payload(self) -> dict[str, Any]:
        out: dict[str, Any] = {"id": self.id, "type": self.type, "ts": self.ts}
        if self.task_id:
            out["task_id"] = self.task_id
        if self.title:
            out["title"] = self.title
        if self.detail:
            out["detail"] = self.detail
        return out


class EventBus:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._seq = itertools.count(1)
        self._buffer: Deque[CosdEvent] = deque(maxlen=MAX_BUFFER)
        self._subscribers: list[Callable[[CosdEvent], None]] = []

    def publish(
        self,
        event_type: str,
        *,
        task_id: str | None = None,
        title: str | None = None,
        detail: dict[str, Any] | None = None,
    ) -> CosdEvent:
        ev = CosdEvent(
            id=next(self._seq),
            type=event_type,
            ts=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            task_id=task_id,
            title=title,
            detail=detail or {},
        )
        with self._lock:
            self._buffer.append(ev)
            subs = list(self._subscribers)
        for fn in subs:
            try:
                fn(ev)
            except Exception:  # noqa: BLE001
                pass
        return ev

    def since(self, last_id: int) -> list[CosdEvent]:
        with self._lock:
            return [e for e in self._buffer if e.id > last_id]

    def subscribe(self, fn: Callable[[CosdEvent], None]) -> Callable[[], None]:
        with self._lock:
            if len(self._subscribers) >= MAX_SUBSCRIBERS:
                raise RuntimeError("too many event subscribers")
            self._subscribers.append(fn)

        def unsubscribe() -> None:
            with self._lock:
                try:
                    self._subscribers.remove(fn)
                except ValueError:
                    pass

        return unsubscribe

    def connection_event(self, kind: str, detail: str | None = None) -> None:
        self.publish(f"daemon.{kind}", detail={"message": detail} if detail else {})


_BUS: EventBus | None = None


def get_event_bus() -> EventBus:
    global _BUS
    if _BUS is None:
        _BUS = EventBus()
    return _BUS
