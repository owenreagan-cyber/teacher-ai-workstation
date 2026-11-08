"""Route selected cos CLI commands through cosd when available."""
from __future__ import annotations

import json
import sys
from cos.cli import EXIT_OK, EXIT_USAGE, _emit_error, status_report
from cos.config import load_config
from cosd.client import CosdClient, CosdClientError, DaemonMode, daemon_mode_from_env


def _daemon_required_message() -> str:
    return "cosd is required (COS_USE_DAEMON=required) but is not available or authenticated"


def try_daemon_ask(args) -> int | None:
    mode = daemon_mode_from_env()
    if mode == DaemonMode.DISABLED:
        return None
    client = CosdClient()
    if not client.is_available():
        if mode == DaemonMode.REQUIRED:
            _emit_error(args.json, _daemon_required_message(), "unavailable")
            return EXIT_USAGE
        return None
    question = " ".join(args.question).strip()
    try:
        code, body = client.ask(question=question, session_id=args.session)
    except CosdClientError as exc:
        _emit_error(args.json, str(exc), exc.kind)
        return exc.exit_code
    if not body.get("ok"):
        _emit_error(args.json, body.get("error", "ask failed"), body.get("error_kind", "internal"))
        return code
    if args.json:
        body = {k: v for k, v in body.items() if k != "cosd"}
        print(json.dumps(body))
        return EXIT_OK
    print(body.get("text") or body.get("answer", ""))
    if body.get("session_warning"):
        print(f"cos: {body['session_warning']}", file=sys.stderr)
    return EXIT_OK


def try_daemon_status(args) -> int | None:
    mode = daemon_mode_from_env()
    if mode == DaemonMode.DISABLED:
        return None
    client = CosdClient()
    if not client.is_available():
        if mode == DaemonMode.REQUIRED:
            _emit_error(args.json, _daemon_required_message(), "unavailable")
            return EXIT_USAGE
        return None
    try:
        _, body = client.status()
    except CosdClientError as exc:
        _emit_error(args.json, str(exc), exc.kind)
        return exc.exit_code
    if args.json:
        report = {k: v for k, v in body.items() if k not in ("cosd", "task_counts")}
        report["via_daemon"] = True
        print(json.dumps(report))
        return EXIT_OK
    cfg = load_config()
    local = status_report(cfg)
    merged = {**local, **{k: v for k, v in body.items() if k in local or k in (
        "kill_switch", "kill_switch_reason", "model", "fallback_model", "ollama_reachable",
        "loaded_models", "audit", "version", "auto_search", "fixture",
    )}}
    state = f"STOPPED ({merged['kill_switch_reason']})" if merged.get("kill_switch") else "active"
    ollama = "reachable" if merged.get("ollama_reachable") else "unreachable"
    loaded = ", ".join(merged.get("loaded_models") or []) or "none"
    print(
        f"cos {merged.get('version')} · {state} · model {merged.get('model')} "
        f"(fallback {merged.get('fallback_model')}) · Ollama {ollama}, loaded: {loaded} "
        f"· audit {merged.get('audit')} · via cosd"
        + (" · FIXTURE MODE (synthetic data)" if merged.get("fixture") else "")
    )
    return EXIT_OK


def dispatch_daemon_command(args) -> int | None:
    func = getattr(args, "func", None)
    func_name = getattr(func, "__name__", "")
    if func_name == "cmd_ask":
        return try_daemon_ask(args)
    if func_name == "cmd_status":
        return try_daemon_status(args)
    return None
