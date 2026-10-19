"""Scripted fake model: a deterministic stand-in for Ollama's /api/chat (test double).

Used only by fake_cos.py, which refuses to run outside fixture mode. It is not
part of cos and never ships. It plays a well-behaved model so that a fake run
checks the harness and cos's deterministic plumbing (router, gate, executor,
audit, sessions, kill switch) rather than model quality:

  - a request to send, post, delete, schedule, open, ... is refused, no tool;
  - otherwise it calls the offered tool its own whole-word keyword table
    matches (two when the question joins topics with "and"), once per turn;
  - after tool results it summarizes them as plain data (titles quoted as text;
    web search results by count and first domain only, never their text);
  - if no offered tool fits the question, it says it doesn't know;
  - personality plumbing: it greets Owen by name, and says what it can do, only when the
    system prompt carries cos/personality.md's section ahead of the tool rules.

The reply depends only on the request payload, so runs are reproducible.
"""
from __future__ import annotations

import json
import re
import urllib.parse

MODEL_NAME = "fake-scripted"

WRITE_INTENT = re.compile(
    r"^\s*(?:hey chief,?\s+)?(?:please\s+)?(?:(?:can|could|would|will) you\s+(?:please\s+)?)?"
    r"(?:send|email|e-mail|post|publish|delete|remove|erase|schedule|book|open|launch|text|"
    r"message|add|create|make|cancel|move|reschedule|mark|reply|respond|forward|turn on|"
    r"turn off|enable|disable|empty|shut down|restart|reboot|order|buy|purchase|print|change|"
    r"set|call|phone|submit|upload|share|archive|install|uninstall|update|rename|edit|write)\b",
    re.IGNORECASE)

# (wire name, keywords the fake looks for, most specific first)
PREFERENCE = (
    ("status_next_action", ("work on next", "next action", "focus", "priority", "priorities")),
    ("status_daily", ("daily status", "roadmap", "workstation status", "repo", "mission")),
    ("status_local_llm", ("local llm", "llm status")),
    ("reminders_due", ("remind", "reminder", "to-do", "todo", "task", "due", "overdue")),
    ("mac_status", ("battery", "disk", "memory", "ram", "storage", "uptime", "ollama", "mac",
                    "laptop", "computer", "charging")),
    ("weather_today", ("weather", "rain", "jacket", "umbrella", "wind", "forecast",
                       "temperature", "cold", "hot", "warm", "outside", "recess", "snow")),
    ("calendar_today", ("calendar", "meeting", "event", "schedule", "appointment", "busy",
                        "agenda", "free")),
    ("time_now", ("time", "date", "day", "days", "until", "weekday")),
)
DATE_RE = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")
GREETING_RE = re.compile(r"^\s*(?:hi|hello|hey|good (?:morning|afternoon|evening))\b[\s,!.]*(?:chief)?[\s!.]*$",
                         re.IGNORECASE)
CAN_DO_RE = re.compile(r"^\s*what can you do\b", re.IGNORECASE)


def _has_personality(messages) -> bool:
    """The personality section is in the system prompt, before the tool rules."""
    system = _text(messages[0]) if messages and messages[0].get("role") == "system" else ""
    p, rules = system.find("## Personality"), system.find("## Tool rules")
    return 0 <= p < rules


# A local-looking name that the fake /api/show reports as an Ollama cloud model (as a
# locally created alias of a cloud model would be), so cos's /api/show check can be exercised.
REMOTE_ALIASES = frozenset({"fake-remote-alias"})


def show(payload: dict) -> dict:
    """Stand-in for Ollama's /api/show: a local model's details, or remote ones for REMOTE_ALIASES."""
    if payload.get("model") in REMOTE_ALIASES:
        return {"remote_model": "gpt-oss:120b", "remote_host": "https://ollama.com:443",
                "details": {"format": "", "family": "gptoss"}}
    return {"details": {"format": "fake", "family": "fake-scripted", "parameter_size": "0",
                        "quantization_level": "none"}, "capabilities": ["completion", "tools"]}


def _text(msg) -> str:
    return str(msg.get("content") or "")


def _last_user(messages) -> str:
    for msg in reversed(messages):
        if msg.get("role") == "user":
            return _text(msg)
    return ""


def _original_question(messages) -> str:
    """The user question of this turn, skipping cos's own retry/budget nudges."""
    for msg in reversed(messages):
        if msg.get("role") != "user":
            continue
        text = _text(msg)
        if text.startswith(("Your last tool call was malformed", "That tool is unavailable",
                            "Tool budget used up")):
            continue
        return text
    return ""


def _offered(tools) -> list[str]:
    names = []
    for t in tools or []:
        fn = t.get("function") if isinstance(t, dict) else None
        if isinstance(fn, dict) and isinstance(fn.get("name"), str):
            names.append(fn["name"])
    return names


def _picks(question: str, offered: list[str]) -> list[str]:
    """Offered tools the question is actually about (whole-word keyword match), best first.
    One tool, or two when the question joins topics with "and". Empty: none fits."""
    q = question.lower()
    hits = [wire for wire, words in PREFERENCE
            if wire in offered and any(re.search(r"\b" + re.escape(w), q) for w in words)]
    return hits[:2] if re.search(r"\band\b", q) else hits[:1]


def _summary(wire: str, data: dict) -> str:
    if "error" in data:
        return f"{wire.replace('_', '.', 1)} reported an error: {data['error']}"
    if wire == "calendar_today":
        events = data.get("events") or []
        if not events:
            return "Your calendar has nothing scheduled today."
        bits = [f"\"{e.get('title')}\" ({'all day' if e.get('all_day') else e.get('start')})"
                for e in events]
        return f"Today's calendar has {len(events)} events: " + "; ".join(bits) + ". That's today only."
    if wire == "reminders_due":
        items = data.get("reminders") or []
        if not items:
            return "No reminders are due."
        bits = [f"\"{r.get('title')}\" ({'overdue' if r.get('overdue') else 'due ' + str(r.get('due'))})"
                for r in items]
        return f"{len(items)} reminders are due: " + "; ".join(bits) + "."
    if wire == "weather_today":
        text = (f"Now {data.get('now_f')}°F and {data.get('conditions')}; today high {data.get('high_f')}°F, "
                f"low {data.get('low_f')}°F, {data.get('rain_chance_pct')}% chance of rain.")
        tm = data.get("tomorrow")
        if isinstance(tm, dict):
            text += (f" Tomorrow ({tm.get('weekday')}): high {tm.get('high_f')}°F, low {tm.get('low_f')}°F, "
                     f"{tm.get('rain_chance_pct')}% chance of rain.")
        if data.get("forecast_note"):
            text += f" {data['forecast_note']}"
        return text
    if wire == "time_now":
        du = data.get("days_until")
        if isinstance(du, dict):
            return (f"{du.get('days')} days until {du.get('date')} "
                    f"({du.get('school_days')} weekdays).")
        return f"It's {data.get('time')} on {data.get('display')}."
    if wire == "mac_status":
        return (f"Right now: battery {data.get('battery_pct')}%, memory {data.get('memory_free_pct')}% free, "
                f"disk {data.get('disk_free_gb')} GB free; loaded models: {data.get('ollama_loaded')}.")
    if wire == "web_search":
        results = data.get("results") or []
        if not results:
            return "The search found nothing useful."
        host = urllib.parse.urlsplit(str(results[0].get("url"))).hostname
        return (f"I found {len(results)} web results for that search. "
                f"The first one is from {host}.")
    if wire.startswith("status_"):
        lines = [l for l in str(data.get("output", "")).splitlines() if ":" in l][:8]
        return "The status report says: " + " | ".join(lines)
    return f"{wire} returned data."


# The router's model fallback (cos/intent.py): a request with a JSON "format" asks for one label.
# The fake labels public-fact questions web_lookup and everything else general.
WEB_FACT_RE = re.compile(r"\b(?:play|plays|game|games|score|won|win|news|price|president|capital|population|"
                         r"tallest|biggest|who is|who was|when was|how old is|what year)\b", re.IGNORECASE)


def classify(payload: dict) -> dict:
    messages = payload.get("messages") or []
    text = _last_user(messages).rsplit("Message to sort: ", 1)[-1]
    label = "web_lookup" if WEB_FACT_RE.search(text) else "general"
    return {"role": "assistant", "content": json.dumps({"label": label})}


def rewrite(payload: dict) -> dict:
    """The follow-up search rewrite (cos/search_query.py): swap the previous search's team or topic
    ("the ny rangers") for the follow-up's ("the islanders"), using only Owen's words."""
    text = _last_user(payload.get("messages") or [])
    prev = re.search(r"Previous search: (.*)", text)
    follow = re.search(r"Follow-up: (.*)", text)
    prev_q = prev.group(1).strip() if prev else ""
    core = re.sub(r"^(?:and|what about|how about)\s+", "", (follow.group(1) if follow else "").strip(),
                  flags=re.IGNORECASE).rstrip("?!. ")
    m = re.search(r"\bthe (.+?) (play|plays|playing|game|score)\b", prev_q, re.IGNORECASE)
    query = (prev_q[:m.start(1)] + re.sub(r"^the\s+", "", core, flags=re.IGNORECASE) + prev_q[m.end(1):]
             if m and core else f"{prev_q} {core}".strip())
    return {"role": "assistant", "content": json.dumps({"query": query})}


def reply(payload: dict) -> dict:
    """The assistant message for one /api/chat request."""
    fmt = payload.get("format")
    if isinstance(fmt, dict) and "query" in (fmt.get("properties") or {}):
        return rewrite(payload)
    if fmt is not None:
        return classify(payload)
    messages = payload.get("messages") or []
    offered = _offered(payload.get("tools"))
    last = messages[-1] if messages else {}
    question = _original_question(messages)

    if last.get("role") == "tool":
        parts = []
        for msg in reversed(messages):
            if msg.get("role") != "tool":
                break
            text = re.sub(r"^<untrusted_search_results>\n|\n</untrusted_search_results>$", "", _text(msg))
            try:
                data = json.loads(text)
            except ValueError:
                data = {"error": "unreadable tool result"}
            if not isinstance(data, dict):
                data = {"error": "unexpected tool result"}
            parts.append(_summary(str(msg.get("tool_name")), data))
        return {"role": "assistant", "content": " ".join(reversed(parts))}

    if _last_user(messages).startswith(("Tool budget used up", "That tool is unavailable")):
        return {"role": "assistant", "content": "I couldn't finish that with my tools."}

    if GREETING_RE.match(question):
        return {"role": "assistant", "content":
                "Hi Owen. What do you need?" if _has_personality(messages) else "Hello."}

    if CAN_DO_RE.match(question):
        return {"role": "assistant", "content":
                ("I can read the time, weather, Mac status, calendar, and reminders, and search the web "
                 "when you type \"search …\". I can't send or change anything.")
                if _has_personality(messages) else "I don't know."}

    if WRITE_INTENT.search(question):
        return {"role": "assistant", "content":
                "I can't do that yet: I'm read-only right now, so I can't send, post, change, "
                "or delete anything. You could do it yourself."}

    picks = _picks(question, offered)
    if picks:
        calls = []
        for wire in picks:
            args = {}
            m = DATE_RE.search(question)
            if wire == "time_now" and m:
                args["days_until"] = m.group(1)
            calls.append({"function": {"name": wire, "arguments": args}})
        return {"role": "assistant", "content": "", "tool_calls": calls}

    return {"role": "assistant", "content":
            "I don't know. I don't have a tool or any information for that."}
