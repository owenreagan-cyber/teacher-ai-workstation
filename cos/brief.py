"""cos brief: a deterministic daily brief (no model), at most 15 lines.

Tools run through the same policy gate and executor as the agent, so the
kill switch and deny rules apply. format_brief() is pure for testing.
"""
from __future__ import annotations

from cos.executor import run_tool
from cos.tools.mac_status import one_line

MAX_LINES = 15
LINE_WIDTH = 120
MAX_EVENTS = 4
MAX_REMINDERS = 3
STATUS_PREFIXES = (
    ("status.next_action", "Recommended daily focus:"),
    ("status.next_action", "Roadmap immediate mission heading:"),
    ("status.daily", "Canvas LLM:"),
)
BRIEF_TOOLS = ("time.now", "weather.today", "calendar.today", "reminders.due", "mac.status",
               "status.daily", "status.next_action")


def _clip(line: str) -> str:
    return line if len(line) <= LINE_WIDTH else line[:LINE_WIDTH - 1] + "…"


def _weather_line(w: dict) -> str:
    if "error" in w:
        return f"Weather: unavailable ({w['error']})"
    bits = [f"{w.get('now_f')}°F {w.get('conditions')}"]
    if w.get("high_f") is not None:
        bits.append(f"H {w['high_f']} / L {w.get('low_f')}")
    if w.get("rain_chance_pct") is not None:
        bits.append(f"rain {w['rain_chance_pct']}%")
    return "Weather: " + " · ".join(bits)


def _calendar_lines(c: dict) -> list[str]:
    if "error" in c:
        return [f"Calendar: unavailable ({c['error']})"]
    events = c.get("events", [])
    if not events:
        return ["Calendar: nothing scheduled"]
    shown = events[:MAX_EVENTS]
    more = f", showing {len(shown)}" if len(events) > len(shown) else ""
    lines = [f"Calendar ({len(events)}{more}):"]
    for ev in shown:
        when = "all day" if ev.get("all_day") else (ev.get("start") or "?")
        lines.append(f"  {when:>8}  {ev.get('title')}")
    return lines


def _reminder_lines(r: dict) -> list[str]:
    if "error" in r:
        return [f"Reminders: unavailable ({r['error']})"]
    items = r.get("reminders", [])
    if not items:
        return ["Reminders: none due"]
    shown = items[:MAX_REMINDERS]
    more = f", showing {len(shown)}" if len(items) > len(shown) else ""
    lines = [f"Reminders due ({len(items)}{more}):"]
    for it in shown:
        tag = f"overdue since {it['due']}" if it.get("overdue") else f"due {it.get('due') or 'today'}"
        lines.append(f"  - {it.get('title')} ({tag})")
    return lines


def _status_lines(results: dict) -> list[str]:
    picked = []
    for tool, prefix in STATUS_PREFIXES:
        out = results.get(tool, {}).get("output", "")
        for line in out.splitlines():
            if line.startswith(prefix):
                picked.append("  " + line)
                break
    errors = [t for t in ("status.daily", "status.next_action") if "error" in results.get(t, {})]
    if errors:
        picked.append("  (unavailable: " + ", ".join(errors) + ")")
    return ["Status:", *picked] if picked else ["Status: no highlights"]


def format_brief(results: dict) -> list[str]:
    t = results.get("time.now", {})
    header = f"Daily Brief — {t.get('display', 'date unknown')}"
    mac = results.get("mac.status", {})
    mac_line = "Mac: " + (f"unavailable ({mac['error']})" if "error" in mac else one_line(mac))
    lines = [header,
             _weather_line(results.get("weather.today", {"error": "not run"})),
             *_calendar_lines(results.get("calendar.today", {"error": "not run"})),
             *_reminder_lines(results.get("reminders.due", {"error": "not run"})),
             mac_line]
    status = _status_lines(results)
    room = MAX_LINES - len(lines)
    if len(status) > room:
        status = status[:room - 1] + [status[-1]] if status[-1].startswith("  (unavailable") else status[:room]
    return [_clip(l) for l in lines + status]


def gather(registry, gate, audit=None) -> dict:
    results = {}
    for name in BRIEF_TOOLS:
        decision = gate.decide(name, {})
        tool = registry.get(name)
        if not decision.allowed or tool is None:
            results[name] = {"error": f"denied: {decision.reason}"}
            continue
        results[name] = run_tool(tool, {}, decision, audit=audit)
    return results
