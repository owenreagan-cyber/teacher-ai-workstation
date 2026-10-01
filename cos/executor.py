"""Executor: runs a tool the policy gate allowed, with a timeout and size cap.

Only called with a Decision whose allowed is True. Tools that shell out also
pass timeout_s to subprocess, so a timed-out worker thread does not linger.
"""
from __future__ import annotations

import json
import threading
import time

from cos.policy import Decision
from cos.registry import Tool

MAX_RESULT_CHARS = 6000


def run_tool(tool: Tool, args: dict, decision: Decision, audit=None) -> dict:
    if not decision.allowed:
        raise PermissionError("executor called without an allow decision")
    box: list = []

    def work():
        try:
            box.append(tool.func(args))
        except Exception as e:  # noqa: BLE001 - tool failures become results
            box.append({"error": f"{type(e).__name__}: {e}"[:300]})

    started = time.monotonic()
    worker = threading.Thread(target=work, daemon=True)
    worker.start()
    worker.join(tool.timeout_s)
    elapsed_ms = int((time.monotonic() - started) * 1000)
    result = box[0] if box else {"error": f"timed out after {tool.timeout_s}s"}
    if not isinstance(result, dict):
        result = {"error": "tool returned a non-object result"}
    ok = "error" not in result
    if audit is not None:
        audit("tool_result", tool=tool.name, ok=ok, ms=elapsed_ms,
              chars=len(json.dumps(result, default=str)))
    return result


def result_text(result: dict) -> str:
    text = json.dumps(result, ensure_ascii=False, default=str)
    if len(text) > MAX_RESULT_CHARS:
        text = text[:MAX_RESULT_CHARS] + "…[truncated]"
    return text
