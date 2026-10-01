"""Deterministic fast path: answer a few exact questions from a tool, with no model call.

A question matches only if the WHOLE question (lowercased, apostrophes dropped,
other punctuation treated as spaces) fully matches one of the anchored patterns
below. A question that merely contains a keyword ("what time is my meeting")
does not match and goes to the agent loop unchanged.

On a match the tool runs through the same policy gate and executor as agent
tool calls. The gate decision is audited with subject=fast_path, the kill
switch is checked before the tool and again after it, and the request closes
with an answer record carrying model_ms=0, tool_ms, and total_ms. The answer
uses a fixed template and reports "Tools used: <tool> · fast path (no model)".
"""
from __future__ import annotations

import re
import time
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Callable

from cos.agent import AgentResult, Stopped
from cos.audit import text_digest
from cos.executor import run_tool
from cos.policy import PolicyGate
from cos.registry import Registry
from cos.tools.mac_status import one_line

WEEKDAYS = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
_NOW = r"(?: (?:now|right now|today))?"


def normalize(question: str) -> str:
    q = question.lower().replace("’", "'").replace("‘", "'").replace("'", "")
    q = re.sub(r"[^a-z0-9-]+", " ", q)
    return " ".join(q.split())


def _plural(n: int, word: str) -> str:
    return f"{n} {word}" if n == 1 else f"{n} {word}s"


def _long_date(d: date) -> str:
    return d.strftime("%A, %B ") + str(d.day)


# ----------------------------------------------------------------------------- templates

def _fmt_time(r: dict) -> str:
    if "error" in r:
        return f"The time is unavailable: {r['error']}."
    return f"It's {r['time']} on {r['display']}."


def _fmt_date(r: dict) -> str:
    if "error" in r:
        return f"The date is unavailable: {r['error']}."
    return f"Today is {r['display']}."


def _fmt_days_until(r: dict) -> str:
    if "error" in r or "days_until" not in r:
        return f"I couldn't work that out: {r.get('error', 'no result')}."
    du = r["days_until"]
    target = date.fromisoformat(du["date"])
    return (f"{_plural(du['days'], 'day')} until {_long_date(target)} "
            f"({_plural(du['school_days'], 'weekday')}, holidays not counted).")


def _fmt_weather(r: dict) -> str:
    if "error" in r:
        return f"Weather is unavailable: {r['error']}."
    return (f"Now {r.get('now_f')}°F and {r.get('conditions')} (feels like {r.get('feels_like_f')}°F). "
            f"Today: high {r.get('high_f')}°F, low {r.get('low_f')}°F, "
            f"{r.get('rain_chance_pct')}% chance of rain.")


def _fmt_mac(r: dict) -> str:
    return f"Mac: {one_line(r)}."


# ----------------------------------------------------------------------------- intents

@dataclass(frozen=True)
class Intent:
    name: str
    tool: str
    pattern: re.Pattern
    args: Callable[[re.Match, date], dict]
    render: Callable[[dict], str]


def _no_args(m, today):
    return {}


def _days_until_args(m, today):
    target = m.group("target")
    if target in WEEKDAYS:
        ahead = (WEEKDAYS.index(target) - today.weekday()) % 7 or 7  # next occurrence, never today
        return {"days_until": (today + timedelta(days=ahead)).isoformat()}
    return {"days_until": target}


def _p(body: str) -> re.Pattern:
    return re.compile(rf"(?:{body})")


INTENTS = (
    Intent("time", "time.now",
           _p(rf"what time is it{_NOW}|whats the time{_NOW}|what is the time{_NOW}|time|"
              r"the time|current time|whats the current time|what is the current time"),
           _no_args, _fmt_time),
    Intent("date", "time.now",
           _p(r"what day is it(?: today)?|what day is today|whats the date(?: today)?|"
              r"what is the date(?: today)?|whats todays date|what is todays date|todays date|"
              r"date|whats today|what is today"),
           _no_args, _fmt_date),
    Intent("days_until", "time.now",
           _p(r"(?:how many )?days (?:until|till|til|to|before) (?:next )?"
              rf"(?P<target>{'|'.join(WEEKDAYS)}|\d{{4}}-\d{{2}}-\d{{2}})"),
           _days_until_args, _fmt_days_until),
    Intent("weather", "weather.today",
           _p(r"whats the weather(?: like)?(?: today| now| outside)?|"
              r"what is the weather(?: like)?(?: today| now| outside)?|weather(?: today| now)?|"
              r"hows the weather(?: today)?|how is the weather(?: today)?|"
              r"is it going to rain(?: today)?|will it rain(?: today)?"),
           _no_args, _fmt_weather),
    Intent("mac", "mac.status",
           _p(r"hows my mac(?: doing)?|how is my mac(?: doing)?|mac status|my mac status|"
              r"whats my mac status|what is my mac status"),
           _no_args, _fmt_mac),
)


def match(question: str) -> tuple[Intent, re.Match] | None:
    q = normalize(question)
    for intent in INTENTS:
        m = intent.pattern.fullmatch(q)
        if m:
            return intent, m
    return None


class FastPath:
    def __init__(self, registry: Registry, gate: PolicyGate, clock, audit=None):
        self.registry = registry
        self.gate = gate
        self.clock = clock
        self.audit = audit or (lambda *a, **k: None)

    def answer(self, question: str, mode: str = "ask") -> AgentResult | None:
        """Return a fast-path answer, None if the question does not match, or raise Stopped."""
        hit = match(question)
        if hit is None:
            return None
        intent, m = hit
        started = time.monotonic()
        timing = {"tool_ms": 0}

        def close(kind, **fields):
            self.audit(kind, path="fast_path", intent=intent.name, model_ms=0,
                       tool_ms=timing["tool_ms"], total_ms=int((time.monotonic() - started) * 1000),
                       **fields)

        self.audit("request", mode=mode, path="fast_path", intent=intent.name,
                   prompt=text_digest(question), tools_offered=[intent.tool])
        args = intent.args(m, self.clock().date())
        decision = self.gate.decide(intent.tool, args, subject="fast_path")
        tool = self.registry.get(intent.tool)
        if not decision.allowed or tool is None:
            if decision.rule == "kill_switch":
                close("request_stopped", reason="kill_switch")
                raise Stopped("kill switch is set")
            close("answer", tools_used=[], denied=decision.rule)
            return AgentResult(f"I can't answer that right now ({decision.reason}).", [], None,
                               fast_path=True)
        tool_started = time.monotonic()
        result = run_tool(tool, args, decision, audit=self.audit)
        timing["tool_ms"] = int((time.monotonic() - tool_started) * 1000)
        if self.gate.kill_switch.is_set():
            close("request_stopped", reason="kill_switch")
            raise Stopped("kill switch was set during the fast-path tool call")
        text = intent.render(result)
        close("answer", tools_used=[tool.name], chars=len(text))
        return AgentResult(text, [tool.name], None, fast_path=True)
