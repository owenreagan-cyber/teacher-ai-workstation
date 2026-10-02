"""Fixture mode: synthetic tool data for the certification harness (evals/).

Turned on by COS_FIXTURE_DIR. config.load_config() refuses to start unless
COS_STATE_DIR is also set and is not the real state directory, so fixture mode
cannot run against Owen's real state. In fixture mode:

  - every audit record carries fixture: true (cli.build_runtime);
  - `cos status` reports fixture: true;
  - the clock is fixed by clock.json;
  - each tool reads its fixture file instead of running a command or making a
    request. A registered tool with no fixture reader returns an error rather
    than running, so a new tool cannot reach the Mac until it gets a reader;
  - the tool context's command runner refuses every call and its HTTP function
    refuses (and audits) every request, as a second line of defense.

The model client is unchanged: local Ollama only.

Fixture directory layout (all synthetic):
  clock.json       {"now": "2026-10-01T14:30:00-04:00"}  (timezone required)
  weather.json     an Open-Meteo forecast response
  mac.json         mac.status result fields (battery_pct, memory_free_pct, ...)
  calendar.json    EventKit helper output: {"status": "ok", "events": [...]}
  reminders.json   EventKit helper output: {"status": "ok", "reminders": [...]}
  status/<name>.txt  output of the wrapped status command for status.<name>
  search.json      a Brave web search response, returned for every web.search query.
                   Its presence stands for "API key stored": without it web.search
                   reports "web search not set up". The real web.search code still
                   builds the request, checks it against the egress allowlist, and
                   writes the egress_request audit record; only the transport and
                   the Keychain read are replaced.
A missing or unreadable file makes that tool return an error result.
"""
from __future__ import annotations

import json
import urllib.parse
from dataclasses import replace
from datetime import datetime
from pathlib import Path

from cos import egress
from cos.config import Config, ConfigError
from cos.registry import Registry
from cos.tools import ToolContext, build_registry, calendar, reminders, status_scripts, weather, web_search
from cos.tools.time_tool import fmt_time

STATUS_FLAGS = {name: flag for name, flag, _desc, _kws in status_scripts.SCRIPTS}


class FixtureError(Exception):
    """A real command or request was attempted in fixture mode."""


def load_clock(fixture_dir: Path):
    try:
        data = json.loads((fixture_dir / "clock.json").read_text(encoding="utf-8"))
        now = datetime.fromisoformat(data["now"])
    except (OSError, ValueError, KeyError, TypeError) as e:
        raise ConfigError(f"fixture clock.json unreadable: {type(e).__name__}")
    if now.tzinfo is None:
        raise ConfigError("fixture clock.json 'now' must include a timezone offset")
    return lambda: now


def _refuse_run(argv, timeout=None, cwd=None):
    raise FixtureError("fixture mode: commands are never run")


def _refuse_http(audit):
    def http(method, url, **kwargs):
        if audit is not None:
            try:
                host = urllib.parse.urlsplit(url).hostname or "?"
            except ValueError:
                host = "?"
            audit("egress_denied", url_host=host, reason="fixture mode: tool requests are never made")
        raise egress.EgressDenied("fixture mode: tool requests are never made")
    return http


def _read_json(fixture_dir: Path, name: str) -> dict:
    try:
        data = json.loads((fixture_dir / name).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {"error": f"fixture {name} not present"}
    except (OSError, ValueError) as e:
        return {"error": f"fixture {name} unreadable ({type(e).__name__})"}
    if not isinstance(data, dict):
        return {"error": f"fixture {name} is not a JSON object"}
    return data


def _weather(ctx, fixture_dir):
    def func(args):
        data = _read_json(fixture_dir, "weather.json")
        if "error" in data:
            return data
        return {**weather.parse(data), "cached": False, "as_of": fmt_time(ctx.clock())}
    return func


def _mac(fixture_dir):
    return lambda args: _read_json(fixture_dir, "mac.json")


def _helper(ctx, fixture_dir, name, result):
    def func(args):
        data = _read_json(fixture_dir, name)
        if "error" in data:
            return data
        if data.get("status", "ok") != "ok":
            return {"error": f"EventKit access {data.get('status')} (fixture)"}
        return result(ctx, data)
    return func


def _status(fixture_dir, tool_name):
    flag = STATUS_FLAGS[tool_name]
    path = fixture_dir / "status" / f"{tool_name.split('.', 1)[1]}.txt"

    def func(args):
        try:
            output = path.read_text(encoding="utf-8")
        except OSError:
            return {"error": f"fixture status/{path.name} not present"}
        return status_scripts.status_result(flag, 0, output)
    return func


def _search(ctx, fixture_dir):
    path = fixture_dir / "search.json"

    def http(method, url, headers=None, timeout=None, audit=None):
        dest = egress.check_url(url)  # the real allowlist still applies
        if dest[1] != web_search.BRAVE.host:
            raise egress.EgressDenied(f"fixture mode: unexpected search host {dest[1]}")
        try:
            return path.read_bytes()
        except OSError as e:
            raise egress.EgressError(f"fixture search.json unreadable ({type(e).__name__})")

    def key():
        return "fixture-key" if path.exists() else None

    return lambda args: web_search.search(ctx, args, key_source=key, http=http)


def _missing(tool_name):
    return lambda args: {"error": f"{tool_name} has no fixture reader (fixture mode)"}


def _reader(tool, ctx, fixture_dir):
    if tool.name == "time.now":
        return tool.func  # pure: reads only ctx.clock, which is the fixture clock
    if tool.name == "weather.today":
        return _weather(ctx, fixture_dir)
    if tool.name == "mac.status":
        return _mac(fixture_dir)
    if tool.name == "calendar.today":
        return _helper(ctx, fixture_dir, "calendar.json", calendar.events_result)
    if tool.name == "reminders.due":
        return _helper(ctx, fixture_dir, "reminders.json", reminders.reminders_result)
    if tool.name in STATUS_FLAGS:
        return _status(fixture_dir, tool.name)
    if tool.name == "web.search":
        return _search(ctx, fixture_dir)
    return _missing(tool.name)


def fixture_context(config: Config, audit=None) -> ToolContext:
    return ToolContext(config=config, clock=load_clock(config.fixture_dir), run=_refuse_run,
                       http=_refuse_http(audit), audit=audit,
                       eventkit_app=Path("/nonexistent/cos-fixture-mode/EventKitReader.app"),
                       loaded_models=None)


def build_fixture_registry(ctx: ToolContext) -> Registry:
    """The real registry (same names, schemas, keywords, side effects) with every
    tool's function replaced by its fixture reader."""
    real = build_registry(ctx)
    registry = Registry()
    for tool in real.all():
        registry.register(replace(tool, func=_reader(tool, ctx, ctx.config.fixture_dir)))
    for name, reason in real.disabled.items():
        registry.disable(name, reason)
    return registry
