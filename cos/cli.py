"""cos: the Chief of Staff command line (M1, read-only, local models only).

  cos ask [--json] "question"   one-shot answer
  cos chat                      multi-turn; history saved in the state directory
  cos brief [--json]            deterministic daily brief (no model)
  cos stop [reason] / resume    kill switch
  cos tools                     registered tools and their modes
  cos audit verify              check the audit hash chain
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime

from cos import VERSION
from cos.agent import Agent, Stopped, build_system_prompt
from cos.audit import AuditLog, verify
from cos.brief import format_brief, gather
from cos.config import Config, ConfigError, ensure_private_subdir, load_config, open_private
from cos.memory import load_identity, load_memory
from cos.model import ModelClient, ModelError, ModelRefused
from cos.policy import KillSwitch, PolicyGate
from cos.registry import Registry
from cos.tools import ToolContext, build_registry

EXIT_OK, EXIT_USAGE, EXIT_STOPPED, EXIT_MODEL = 0, 2, 3, 4
CHAT_CONTEXT_MESSAGES = 12


@dataclass
class Runtime:
    config: Config
    audit: AuditLog
    kill_switch: KillSwitch
    model: ModelClient
    registry: Registry
    gate: PolicyGate


def build_runtime() -> Runtime:
    cfg = load_config()
    audit = AuditLog(cfg.audit_path)
    kill_switch = KillSwitch(cfg.state_dir)
    model = ModelClient(cfg.ollama_url, cfg.model, cfg.fallback_model, cfg.model_timeout_s, audit=audit)
    ctx = ToolContext(config=cfg, audit=audit, loaded_models=model.loaded_models)
    registry = build_registry(ctx)
    return Runtime(cfg, audit, kill_switch, model, registry, PolicyGate(registry, kill_switch, audit=audit))


def make_agent(rt: Runtime) -> Agent:
    memory, _ = load_memory(rt.config.repo_root)
    now = datetime.now().astimezone()
    now_text = now.strftime("%A, %B ") + str(now.day) + now.strftime(", %Y, %I:%M %p").replace(" 0", " ")
    prompt = build_system_prompt(load_identity(), memory, now_text)
    return Agent(rt.model, rt.registry, rt.gate, prompt, audit=rt.audit)


def _emit_error(as_json: bool, message: str) -> None:
    if as_json:
        print(json.dumps({"ok": False, "error": message}))
    else:
        print(f"cos: {message}", file=sys.stderr)


def cmd_ask(rt: Runtime, args) -> int:
    question = " ".join(args.question).strip()
    if not question:
        _emit_error(args.json, "ask needs a question")
        return EXIT_USAGE
    try:
        result = make_agent(rt).run(question, mode="ask")
    except Stopped:
        _emit_error(args.json, f"stopped by kill switch ({rt.kill_switch.reason()}); run cos resume")
        return EXIT_STOPPED
    except ModelError as e:
        _emit_error(args.json, f"local model unavailable: {e}")
        return EXIT_MODEL
    print(json.dumps(result.as_json()) if args.json else result.text())
    return EXIT_OK


def cmd_chat(rt: Runtime, args) -> int:
    agent = make_agent(rt)
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
                result = agent.run(line, history=history[-CHAT_CONTEXT_MESSAGES:], mode="chat")
            except Stopped:
                print("Stopped by kill switch; run cos resume.")
                return EXIT_STOPPED
            except ModelError as e:
                print(f"Local model unavailable: {e}")
                continue
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
        _emit_error(args.json, f"stopped by kill switch ({rt.kill_switch.reason()}); run cos resume")
        return EXIT_STOPPED
    rt.audit("request", mode="brief")
    lines = format_brief(gather(rt.registry, rt.gate, audit=rt.audit))
    print(json.dumps({"ok": True, "lines": lines}) if args.json else "\n".join(lines))
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
    state = "STOPPED (kill switch set)" if rt.kill_switch.is_set() else "active"
    print(f"\n{len(rt.registry.all())} tools · mode: read-only · model: {rt.config.model} "
          f"(fallback {rt.config.fallback_model}) at {rt.model.base_url} · {state}")
    return EXIT_OK


def cmd_audit(rt: Runtime, args) -> int:
    ok, n, message = verify(rt.config.audit_path)
    print(f"{'OK' if ok else 'FAIL'}: {message} — {rt.config.audit_path}")
    return EXIT_OK if ok else 1


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="cos", description="Chief of Staff (M1: local, read-only)")
    p.add_argument("--version", action="version", version=f"cos {VERSION}")
    sub = p.add_subparsers(dest="command", required=True)
    ask = sub.add_parser("ask", help="one-shot question")
    ask.add_argument("--json", action="store_true", help="machine output for Raycast")
    ask.add_argument("question", nargs="*")
    ask.set_defaults(func=cmd_ask)
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
    try:
        rt = build_runtime()
    except (ConfigError, ModelRefused) as e:
        _emit_error(as_json, str(e))
        return EXIT_USAGE
    return args.func(rt, args)
