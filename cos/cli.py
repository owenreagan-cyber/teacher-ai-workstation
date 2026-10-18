"""cos: the Chief of Staff command line (M1, read-only, local models only).

  cos ask [--session ID] [--json] "question"
                                one-shot answer; --session adds prior turns of that
                                session as history and appends the new turn
  cos history --session ID [--json]   turns of a session (read-only)
  cos status [--json]           kill switch, models, Ollama, audit (read-only, no model call)
  cos warm [--json]             load the configured model and keep it loaded (keep_alive)
  cos chat                      multi-turn; history saved in the state directory
  cos brief [--json]            deterministic daily brief (no model); --json adds the
                                home card's structured fields ("card")
  cos stop [reason] / resume    kill switch
  cos tools                     registered tools and their modes
  cos audit verify              check the audit hash chain
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass
from datetime import datetime

from cos import VERSION, egress, fixture
from cos.agent import Agent, Stopped, build_system_prompt
from cos.audit import AuditLog, verify
from cos.brief import format_brief, gather, home_card
from cos.config import (CloudModelError, Config, ConfigError, ensure_private_subdir, load_config,
                        open_private)
from cos.executor import run_tool
from cos.fastpath import FastPath
from cos.memory import load_identity, load_memory, load_personality
from cos.model import CloudModelRefused, ModelClient, ModelError, ModelRefused
from cos.policy import KillSwitch, PolicyGate
from cos.registry import Registry
from cos.sessions import (SessionIdError, SessionReadError, TurnError, append_turn, check_session_id,
                          history_messages, read_session, read_turns)
from cos.tools import ToolContext, build_registry

EXIT_OK, EXIT_INTERNAL, EXIT_USAGE, EXIT_STOPPED, EXIT_MODEL = 0, 1, 2, 3, 4
CHAT_CONTEXT_MESSAGES = 12
STATUS_TIMEOUT_S = 2


@dataclass
class Runtime:
    config: Config
    audit: AuditLog
    kill_switch: KillSwitch
    model: ModelClient
    registry: Registry
    gate: PolicyGate
    ctx: ToolContext


def build_runtime() -> Runtime:
    cfg = load_config()
    audit = AuditLog(cfg.audit_path, extra={"fixture": True} if cfg.fixture_dir else None)
    kill_switch = KillSwitch(cfg.state_dir)
    model = ModelClient(cfg.ollama_url, cfg.model, cfg.fallback_model, cfg.model_timeout_s, audit=audit,
                        think=cfg.model_think, num_ctx=cfg.model_num_ctx,
                        keep_alive=cfg.model_keep_alive)
    if cfg.fixture_dir:
        ctx = fixture.fixture_context(cfg, audit=audit)
        registry = fixture.build_fixture_registry(ctx)
    else:
        ctx = ToolContext(config=cfg, audit=audit, loaded_models=model.loaded_models)
        registry = build_registry(ctx)
    gate = PolicyGate(registry, kill_switch, audit=audit)
    return Runtime(cfg, audit, kill_switch, model, registry, gate, ctx)


def make_fastpath(rt: Runtime) -> FastPath:
    def summarize(question, result, timing):  # the agent (and its memory files) only when searching
        return make_agent(rt).answer_from_search(question, result, timing)
    return FastPath(rt.registry, rt.gate, rt.ctx.clock, audit=rt.audit, summarize=summarize)


def loaded_models(rt: Runtime) -> list[str] | None:
    """Models loaded right now (ollama ps, via mac.status through the gate), or None if unknown."""
    decision = rt.gate.decide("mac.status", {}, subject="guard")
    tool = rt.registry.get("mac.status")
    if not decision.allowed or tool is None:
        return None
    loaded = run_tool(tool, {}, decision, audit=rt.audit).get("ollama_loaded")
    return [str(m) for m in loaded] if isinstance(loaded, list) else None


def make_agent(rt: Runtime) -> Agent:
    memory, _ = load_memory(rt.config.repo_root)
    prompt = build_system_prompt(load_identity(), memory, load_personality())
    return Agent(rt.model, rt.registry, rt.gate, prompt, audit=rt.audit,
                 loaded_models=lambda: loaded_models(rt))


def _emit_error(as_json: bool, message: str, kind: str) -> None:
    """kind is one of: usage, stopped, model_unavailable, internal."""
    if as_json:
        print(json.dumps({"ok": False, "error": message, "error_kind": kind}))
    else:
        print(f"cos: {message}", file=sys.stderr)


def _now_stamp() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def cmd_ask(rt: Runtime, args) -> int:
    question = " ".join(args.question).strip()
    if not question:
        _emit_error(args.json, "ask needs a question", "usage")
        return EXIT_USAGE
    session_id = args.session
    try:
        history = history_messages(read_turns(rt.config.state_dir, session_id)) if session_id else None
        started = time.monotonic()
        result = (make_fastpath(rt).answer(question, mode="ask")
                  or make_agent(rt).run(question, history=history, mode="ask"))
        total_ms = int((time.monotonic() - started) * 1000)
    except Stopped:
        _emit_error(args.json, f"stopped by kill switch ({rt.kill_switch.reason()}); run cos resume",
                    "stopped")
        return EXIT_STOPPED
    except ModelError as e:
        _emit_error(args.json, f"local model unavailable: {e}", "model_unavailable")
        return EXIT_MODEL
    except CloudModelRefused as e:
        _emit_error(args.json, str(e), "internal")
        return EXIT_INTERNAL
    except SessionReadError as e:
        _emit_error(args.json, str(e), "internal")
        return EXIT_INTERNAL
    except Exception as e:  # noqa: BLE001 - JSON callers get data, not a traceback
        if not args.json:
            raise
        _emit_error(True, f"internal error ({type(e).__name__})", "internal")
        return EXIT_INTERNAL
    stamp = _now_stamp()
    if session_id:
        try:
            append_turn(rt.config.state_dir, session_id, {
                "ts": stamp, "question": question, "answer": result.answer,
                "tools_used": result.tools_used, "fast_path": result.fast_path, "model": result.model,
                "notices": result.notices, "total_ms": total_ms})
        except TurnError as e:
            print(f"cos: turn not recorded in session ({e})", file=sys.stderr)
    if args.json:
        print(json.dumps({**result.as_json(), "session_id": session_id, "ts": stamp,
                          "total_ms": total_ms}))
    else:
        print(result.text())
    return EXIT_OK


def cmd_chat(rt: Runtime, args) -> int:
    agent = make_agent(rt)
    fastpath = make_fastpath(rt)
    hist_dir = ensure_private_subdir("history", rt.config.state_dir)
    hist_path = hist_dir / f"chat-{datetime.now():%Y%m%d-%H%M%S}.jsonl"
    history: list[dict] = []
    print("Chief of Staff chat (local model). Type /exit or Ctrl-D to quit.")
    with open_private(hist_path, "a") as log:
        while True:
            try:
                line = input("you> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if line in ("/exit", "/quit"):
                break
            if not line:
                continue
            try:
                result = (fastpath.answer(line, mode="chat")
                          or agent.run(line, history=history[-CHAT_CONTEXT_MESSAGES:], mode="chat"))
            except Stopped:
                print("Stopped by kill switch; run cos resume.")
                return EXIT_STOPPED
            except ModelError as e:
                print(f"Local model unavailable: {e}")
                continue
            except CloudModelRefused as e:
                print(f"Refused: {e}")
                return EXIT_INTERNAL
            print(f"chief> {result.text()}\n")
            stamp = datetime.now().astimezone().isoformat(timespec="seconds")
            for role, content in (("user", line), ("assistant", result.answer)):
                history.append({"role": role, "content": content})
                log.write(json.dumps({"ts": stamp, "role": role, "content": content,
                                      **({"tools_used": result.tools_used} if role == "assistant" else {})}) + "\n")
            log.flush()
    print(f"History saved: {hist_path}")
    return EXIT_OK


def cmd_brief(rt: Runtime, args) -> int:
    if rt.kill_switch.is_set():
        _emit_error(args.json, f"stopped by kill switch ({rt.kill_switch.reason()}); run cos resume",
                    "stopped")
        return EXIT_STOPPED
    started = time.monotonic()
    timing = {"tool_ms": 0}
    rt.audit("request", mode="brief")
    results = gather(rt.registry, rt.gate, audit=rt.audit, timing=timing)
    total_ms = int((time.monotonic() - started) * 1000)
    if rt.kill_switch.is_set():
        # Set while the brief was being gathered: show nothing from it.
        rt.audit("request_stopped", mode="brief", reason="kill_switch", model_ms=0,
                 tool_ms=timing["tool_ms"], total_ms=total_ms)
        _emit_error(args.json, f"stopped by kill switch ({rt.kill_switch.reason()}); run cos resume",
                    "stopped")
        return EXIT_STOPPED
    lines = format_brief(results)
    rt.audit("answer", mode="brief", model_ms=0, tool_ms=timing["tool_ms"],
             total_ms=total_ms, lines=len(lines))
    if args.json:
        print(json.dumps({"ok": True, "lines": lines, "card": home_card(results, rt.ctx.clock())}))
    else:
        print("\n".join(lines))
    return EXIT_OK


def cmd_stop(rt: Runtime, args) -> int:
    reason = " ".join(args.reason)
    rt.kill_switch.stop(reason)
    rt.audit("kill_switch", action="stop", reason=reason)
    print("Kill switch set. Every model and tool call is denied until: cos resume")
    return EXIT_OK


def cmd_resume(rt: Runtime, args) -> int:
    cleared = rt.kill_switch.resume()
    rt.audit("kill_switch", action="resume", was_set=cleared)
    print("Kill switch cleared." if cleared else "Kill switch was not set.")
    return EXIT_OK


def cmd_tools(rt: Runtime, args) -> int:
    for t in rt.registry.all():
        print(f"{t.name:<20} side_effect={t.side_effect:<5} data_class={t.data_class} "
              f"timeout={t.timeout_s:g}s  {t.description}")
    for name, reason in sorted(rt.registry.disabled.items()):
        print(f"{name:<20} DISABLED  {reason}")
    state = "STOPPED (kill switch set)" if rt.kill_switch.is_set() else "active"
    print(f"\n{len(rt.registry.all())} tools · mode: read-only · model: {rt.config.model} "
          f"(fallback {rt.config.fallback_model}) at {rt.model.base_url} · {state}"
          + (" · FIXTURE MODE (synthetic data)" if rt.config.fixture_dir else ""))
    return EXIT_OK


def cmd_history(cfg: Config, args) -> int:
    """Read-only: no audit record, nothing created.

    --json prints the array of valid turns on stdout (unchanged shape) and one JSON
    note on stderr, {"skipped_lines": N}, counting lines that were not valid turns.
    A session path that is a directory, a symlink, or unreadable gets the same refusal
    as ask (error_kind "internal", exit 1), never a traceback."""
    try:
        turns, skipped = read_session(cfg.state_dir, args.session)
    except SessionReadError as e:
        _emit_error(args.json, str(e), "internal")
        return EXIT_INTERNAL
    if args.json:
        print(json.dumps(turns))
        print(json.dumps({"skipped_lines": skipped}), file=sys.stderr)
        return EXIT_OK
    if skipped:
        print(f"cos: skipped {skipped} invalid line(s) in session {args.session}", file=sys.stderr)
    for t in turns:
        print(f"[{t['ts']}] you> {t['question']}\nchief> {t['answer']}\n")
    return EXIT_OK


def status_report(cfg: Config, http=None) -> dict:
    """Read-only health snapshot. No model call and no audit write (surfaces poll this)."""
    http = http or egress.request
    kill_switch = KillSwitch(cfg.state_dir)
    stopped = kill_switch.is_set()
    try:
        client = ModelClient(cfg.ollama_url, cfg.model, cfg.fallback_model, http=http)
        loaded, reachable = client.loaded_models(timeout_s=STATUS_TIMEOUT_S), True
    except Exception:  # noqa: BLE001 - any failure means "not reachable"
        loaded, reachable = [], False
    audit_status = verify(cfg.audit_path).status
    extra = {"fixture": True} if cfg.fixture_dir else {}  # key present only in fixture mode
    return {
        "ok": True,
        "kill_switch": stopped,
        "kill_switch_reason": kill_switch.reason() if stopped else None,
        "model": cfg.model,
        "fallback_model": cfg.fallback_model,
        "ollama_reachable": reachable,
        "loaded_models": loaded,
        "audit": {"ok": "ok", "uninitialized": "empty", "fail": "fail"}[audit_status],
        "version": VERSION,
        **extra,
    }


def cmd_status(cfg: Config, args) -> int:
    report = status_report(cfg)
    if args.json:
        print(json.dumps(report))
        return EXIT_OK
    state = f"STOPPED ({report['kill_switch_reason']})" if report["kill_switch"] else "active"
    ollama = "reachable" if report["ollama_reachable"] else "unreachable"
    loaded = ", ".join(report["loaded_models"]) or "none"
    print(f"cos {report['version']} · {state} · model {report['model']} "
          f"(fallback {report['fallback_model']}) · Ollama {ollama}, loaded: {loaded} "
          f"· audit {report['audit']}"
          + (" · FIXTURE MODE (synthetic data)" if report.get("fixture") else ""))
    return EXIT_OK


def cmd_warm(rt: Runtime, args) -> int:
    """Load the configured model with the configured keep_alive (one empty-prompt request,
    one model_warm audit record). Refused while the kill switch is set."""
    if rt.kill_switch.is_set():
        _emit_error(args.json, f"stopped by kill switch ({rt.kill_switch.reason()}); run cos resume",
                    "stopped")
        return EXIT_STOPPED
    try:
        result = rt.model.warm()
    except ModelError as e:
        _emit_error(args.json, f"local model unavailable: {e}", "model_unavailable")
        return EXIT_MODEL
    except CloudModelRefused as e:
        _emit_error(args.json, str(e), "internal")
        return EXIT_INTERNAL
    report = {"ok": True, "model": rt.config.model, "loaded": result["loaded"],
              "keep_alive": rt.model.keep_alive, "load_ms": result["load_ms"]}
    if args.json:
        print(json.dumps(report))
    else:
        state = "loaded" if report["loaded"] else "not loaded"
        print(f"{report['model']}: {state} (keep_alive {report['keep_alive']}, {report['load_ms']} ms)")
    return EXIT_OK


def cmd_audit(rt: Runtime, args) -> int:
    result = verify(rt.config.audit_path)
    label = {"ok": "OK", "uninitialized": "EMPTY", "fail": "FAIL"}[result.status]
    print(f"{label}: {result.message} — {rt.config.audit_path}")
    return EXIT_OK if result.ok else 1


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="cos", description="Chief of Staff (M1: local, read-only)")
    p.add_argument("--version", action="version", version=f"cos {VERSION}")
    sub = p.add_subparsers(dest="command", required=True)
    ask = sub.add_parser("ask", help="one-shot question")
    ask.add_argument("--json", action="store_true", help="machine output for Raycast")
    ask.add_argument("--session", help="session id ([a-z0-9-]{1,40})")
    ask.add_argument("question", nargs="*")
    ask.set_defaults(func=cmd_ask)
    history = sub.add_parser("history", help="turns of a session (read-only)")
    history.add_argument("--session", required=True, help="session id ([a-z0-9-]{1,40})")
    history.add_argument("--json", action="store_true")
    history.set_defaults(func=cmd_history, config_only=True)
    status = sub.add_parser("status", help="health snapshot (read-only, no model call)")
    status.add_argument("--json", action="store_true")
    status.set_defaults(func=cmd_status, config_only=True)
    warm = sub.add_parser("warm", help="load the configured model and keep it loaded")
    warm.add_argument("--json", action="store_true")
    warm.set_defaults(func=cmd_warm)
    sub.add_parser("chat", help="multi-turn chat").set_defaults(func=cmd_chat)
    brief = sub.add_parser("brief", help="daily brief")
    brief.add_argument("--json", action="store_true")
    brief.set_defaults(func=cmd_brief)
    stop = sub.add_parser("stop", help="set the kill switch")
    stop.add_argument("reason", nargs="*")
    stop.set_defaults(func=cmd_stop)
    sub.add_parser("resume", help="clear the kill switch").set_defaults(func=cmd_resume)
    sub.add_parser("tools", help="list registered tools").set_defaults(func=cmd_tools)
    audit = sub.add_parser("audit", help="audit log commands")
    audit.add_argument("action", choices=["verify"])
    audit.set_defaults(func=cmd_audit)
    return p


def main(argv: list[str]) -> int:
    if sys.version_info < (3, 12):
        print("cos: Python 3.12+ required", file=sys.stderr)
        return EXIT_USAGE
    args = parser().parse_args(argv)
    as_json = getattr(args, "json", False)
    if getattr(args, "session", None) is not None:
        try:
            check_session_id(args.session)
        except SessionIdError as e:
            _emit_error(as_json, str(e), "usage")
            return EXIT_USAGE
    try:
        if getattr(args, "config_only", False):
            return args.func(load_config(), args)
        rt = build_runtime()
    except CloudModelError as e:
        AuditLog(e.state_dir / "audit.jsonl", extra={"fixture": True} if e.fixture else None)(
            "model_refused", model=e.model, field=e.field_name, reason="cloud model name in config")
        _emit_error(as_json, str(e), "internal")
        return EXIT_INTERNAL
    except (ConfigError, ModelRefused) as e:
        _emit_error(as_json, str(e), "usage")
        return EXIT_USAGE
    return args.func(rt, args)
