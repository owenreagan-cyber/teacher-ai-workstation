"""Shared request handlers for cos CLI and cosd HTTP API."""
from __future__ import annotations

import time
from datetime import datetime

from cos.agent import Stopped
from cos.cli import (
    EXIT_INTERNAL,
    EXIT_MODEL,
    EXIT_OK,
    EXIT_STOPPED,
    EXIT_USAGE,
    make_responder,
    status_report,
)
from cos.model import CloudModelRefused, ModelError
from cos.sessions import (
    SessionReadError,
    TurnError,
    append_turn,
    check_session_id,
    history_messages,
    read_turns,
)


def run_ask(
    rt,
    *,
    question: str,
    session_id: str | None = None,
) -> tuple[int, dict]:
    """Run one ask through the existing responder, session, and audit path."""
    question = (question or "").strip()
    if not question:
        return EXIT_USAGE, {"ok": False, "error": "ask needs a question", "error_kind": "usage"}
    if session_id is not None:
        try:
            check_session_id(session_id)
        except Exception as e:  # noqa: BLE001 — SessionIdError
            return EXIT_USAGE, {"ok": False, "error": str(e), "error_kind": "usage"}
    try:
        turns = read_turns(rt.config.state_dir, session_id) if session_id else []
        history = history_messages(turns) if session_id else None
        started = time.monotonic()
        result = make_responder(rt).answer(
            question,
            previous=turns[-1] if turns else None,
            history=history,
            mode="ask",
        )
        total_ms = int((time.monotonic() - started) * 1000)
    except Stopped:
        return EXIT_STOPPED, {
            "ok": False,
            "error": f"stopped by kill switch ({rt.kill_switch.reason()}); run cos resume",
            "error_kind": "stopped",
        }
    except ModelError as e:
        return EXIT_MODEL, {
            "ok": False,
            "error": f"local model unavailable: {e}",
            "error_kind": "model_unavailable",
        }
    except CloudModelRefused as e:
        return EXIT_INTERNAL, {"ok": False, "error": str(e), "error_kind": "internal"}
    except SessionReadError as e:
        return EXIT_INTERNAL, {"ok": False, "error": str(e), "error_kind": "internal"}
    except Exception as e:  # noqa: BLE001
        return EXIT_INTERNAL, {
            "ok": False,
            "error": f"internal error ({type(e).__name__})",
            "error_kind": "internal",
        }
    stamp = datetime.now().astimezone().isoformat(timespec="seconds")
    session_warning = None
    if session_id:
        try:
            append_turn(
                rt.config.state_dir,
                session_id,
                {
                    "ts": stamp,
                    "question": question,
                    "answer": result.answer,
                    "tools_used": result.tools_used,
                    "fast_path": result.fast_path,
                    "model": result.model,
                    "notices": result.notices,
                    "total_ms": total_ms,
                    "intent": result.intent,
                    "search_query": result.search_query,
                    "blocks": result.blocks,
                    "resources": result.resources,
                },
            )
        except TurnError as e:
            session_warning = f"turn not recorded in session ({e})"
    body = {
        **result.as_json(),
        "ok": True,
        "text": result.text(),
        "session_id": session_id,
        "ts": stamp,
        "total_ms": total_ms,
    }
    if session_warning:
        body["session_warning"] = session_warning
    return EXIT_OK, body


def run_status(cfg) -> dict:
    """Read-only status snapshot (same as cos status --json)."""
    report = status_report(cfg)
    report["service"] = "cos"
    return report
