"""Registered task-kind handlers (no shell, no unrestricted I/O)."""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Callable

from cosd.tasks import TaskRegistry

RecoveryPolicy = str  # safe_replay | checkpoint_resume | block_on_interrupt


@dataclass(frozen=True)
class HandlerSpec:
    kind: str
    timeout_s: float
    max_attempts: int
    recovery_policy: RecoveryPolicy
    retryable: bool
    input_schema: dict[str, str]
    execute: Callable[[dict[str, Any], dict[str, Any] | None], dict[str, Any]]


class ExecutionDenied(Exception):
    def __init__(self, reason: str, *, permanent: bool = False):
        super().__init__(reason)
        self.reason = reason
        self.permanent = permanent


def _noop_execute(payload: dict, _checkpoint: dict | None) -> dict:
    return {"ok": True, "message": "noop verified"}


def _calc_execute(payload: dict, checkpoint: dict | None) -> dict:
    op = payload.get("op")
    values = payload.get("values")
    if op != "add" or not isinstance(values, list) or not values:
        raise ExecutionDenied("calc requires op=add and numeric values", permanent=True)
    if not all(isinstance(v, (int, float)) for v in values):
        raise ExecutionDenied("values must be numbers", permanent=True)
    done = (checkpoint or {}).get("done", False)
    if payload.get("phased") and not done:
        return {
            "_checkpoint": {"checkpoint_key": "progress", "data": {"done": True, "partial": float(values[0])}},
            "partial": float(values[0]),
        }
    if checkpoint and checkpoint.get("partial") is not None:
        total = float(checkpoint["partial"]) + sum(float(v) for v in values[1:])
    else:
        total = sum(float(v) for v in values)
    return {"sum": total}


def _diagnostic_execute(_payload: dict, _checkpoint: dict | None, registry: TaskRegistry) -> dict:
    return {"task_counts": registry.get_task_counts(), "read_only": True}


class HandlerRegistry:
    def __init__(self, registry: TaskRegistry):
        self._registry = registry
        self._handlers: dict[str, HandlerSpec] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        reg = self._registry

        def diag(payload, cp):
            return _diagnostic_execute(payload, cp, reg)

        for spec in (
            HandlerSpec("noop", 5.0, 3, "safe_replay", True, {"optional": "object"}, _noop_execute),
            HandlerSpec("calc", 10.0, 3, "checkpoint_resume", True, {"op": "add", "values": "array"}, _calc_execute),
            HandlerSpec("diagnostic", 5.0, 2, "safe_replay", False, {}, diag),
        ):
            self._handlers[spec.kind] = spec

    def get(self, kind: str) -> HandlerSpec:
        if kind not in self._handlers:
            raise ExecutionDenied(f"unregistered handler: {kind}", permanent=True)
        return self._handlers[kind]

    def list_kinds(self) -> list[str]:
        return sorted(self._handlers)
