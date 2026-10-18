"""cos brief: a deterministic daily brief (no model), at most 15 lines.

Tools run through the same policy gate and executor as the agent, so the
kill switch and deny rules apply. format_brief() is pure for testing.

home_card() builds the desktop home card from the same tool results, also
pure and deterministic: a time-of-day greeting, the date, the next event and
today's event count, reminders due and overdue, and a one-line weather
summary. Each part carries a status ("ok", "empty", "unavailable") and display
text, so a surface shows it without parsing brief lines. An unavailable part
says only "Calendar unavailable" (etc.), never the underlying error.
"""
from __future__ import annotations

import time
from datetime import datetime

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
LEGACY_LABEL = "Workstation status (legacy):"
BRIEF_TOOLS = ("time.now", "weather.today", "calendar.today", "reminders.due", "mac.status",
               "status.daily", "status.next_action")
OWNER_NAME = "Owen"


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
    """Lines copied verbatim from the legacy bin/chief-of-staff status output, labeled."""
    picked = []
    for tool, prefix in STATUS_PREFIXES:
        out = results.get(tool, {}).get("output", "")
        for line in out.splitlines():
            if line.startswith(prefix):
                picked.append(f"{LEGACY_LABEL} {line}")
                break
    errors = [t for t in ("status.daily", "status.next_action") if "error" in results.get(t, {})]
    if errors:
        picked.append(f"{LEGACY_LABEL} unavailable ({', '.join(errors)})")
    return picked or [f"{LEGACY_LABEL} no highlights"]


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
        status = status[:room - 1] + [status[-1]] if " unavailable (" in status[-1] else status[:room]
    return [_clip(l) for l in lines + status]


def _plural(n: int, word: str) -> str:
    return f"{n} {word}" if n == 1 else f"{n} {word}s"


def greeting(now: datetime) -> str:
    part = "morning" if 5 <= now.hour < 12 else "afternoon" if 12 <= now.hour < 17 else "evening"
    return f"Good {part}, {OWNER_NAME}"


def _start(ev: dict) -> datetime | None:
    try:
        return datetime.fromisoformat(str(ev.get("start_iso")).replace("Z", "+00:00"))
    except ValueError:
        return None


def _card_calendar(c: dict, now: datetime) -> dict:
    if "error" in c:
        return {"status": "unavailable", "count": 0, "next": None, "text": "Calendar unavailable"}
    events = [e for e in c.get("events", []) if isinstance(e, dict)]
    if not events:
        return {"status": "empty", "count": 0, "next": None, "text": "Nothing scheduled"}
    upcoming = sorted(((s, e) for e in events if not e.get("all_day")
                       for s in [_start(e)] if s is not None and s >= now), key=lambda se: se[0])
    count = _plural(len(events), "event") + " today"
    if not upcoming:
        return {"status": "ok", "count": len(events), "next": None, "text": f"No more events · {count}"}
    ev = upcoming[0][1]
    nxt = {"title": str(ev.get("title") or "(no title)"), "start": ev.get("start")}
    return {"status": "ok", "count": len(events), "next": nxt,
            "text": f"Next: {nxt['start']} {nxt['title']} · {count}"}


def _card_reminders(r: dict) -> dict:
    if "error" in r:
        return {"status": "unavailable", "due": 0, "overdue": 0, "text": "Reminders unavailable"}
    items = [it for it in r.get("reminders", []) if isinstance(it, dict)]
    overdue = sum(1 for it in items if it.get("overdue"))
    if not items:
        return {"status": "empty", "due": 0, "overdue": 0, "text": "No reminders due"}
    text = _plural(len(items), "reminder") + " due" + (f" ({overdue} overdue)" if overdue else "")
    return {"status": "ok", "due": len(items), "overdue": overdue, "text": text}


def _card_weather(w: dict) -> dict:
    if "error" in w:
        return {"status": "unavailable", "text": "Weather unavailable"}
    return {"status": "ok", "text": _weather_line(w).removeprefix("Weather: ")}


def home_card(results: dict, now: datetime) -> dict:
    """The home card for the desktop shell (deterministic, no model)."""
    return {
        "greeting": greeting(now),
        "date": now.strftime("%A, %B ") + str(now.day),
        "date_iso": now.date().isoformat(),
        "calendar": _card_calendar(results.get("calendar.today", {"error": "not run"}), now),
        "reminders": _card_reminders(results.get("reminders.due", {"error": "not run"})),
        "weather": _card_weather(results.get("weather.today", {"error": "not run"})),
    }


def gather(registry, gate, audit=None, timing: dict | None = None) -> dict:
    results = {}
    for name in BRIEF_TOOLS:
        decision = gate.decide(name, {})
        tool = registry.get(name)
        if not decision.allowed or tool is None:
            results[name] = {"error": f"denied: {decision.reason}"}
            continue
        started = time.monotonic()
        results[name] = run_tool(tool, {}, decision, audit=audit)
        if timing is not None:
            timing["tool_ms"] = timing.get("tool_ms", 0) + int((time.monotonic() - started) * 1000)
    return results
