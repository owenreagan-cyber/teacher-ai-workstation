"""What Chief can and can't do, as one registry. Every fixed answer about capabilities comes from
here and from config, never from the model.

  answer_for("local_files") / answer_for("mail") / answer_for("mail_send")
      the not-built-yet answers (no tool, no model, no web search)
  capabilities_answer(registry, config)
      "what can you do?": what works (only tools that are registered), what is connected, what
      is not built yet, and where settings live (config.json in the state folder: there is no
      settings screen, so Chief never names one or a menu path)
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

NOT_BUILT = {
    "local_files": "I can't search files on your Mac yet. That's coming in a later build.",
    "mail": "Mail isn't connected yet, so I can't see your inbox.",
    "mail_send": "Mail isn't connected yet, so I can't send email.",
}
NOT_YET = "Not built yet: searching files on your Mac, and mail. I can't send, create, change, or delete anything."


@dataclass(frozen=True)
class Capability:
    tools: tuple[str, ...]  # shown only when every one of these tools is registered
    can: str
    connected: str | None = None


def _weather_where(config) -> str:
    if getattr(config, "latitude", None) is None or getattr(config, "longitude", None) is None:
        return "the weather (once a location is set in config.json)"
    return "the weather and forecast for your configured location"


def _registry(config) -> tuple[Capability, ...]:
    return (
        Capability(("time.now",), "tell the time and date, and count the days until a date"),
        Capability(("weather.today",), "give " + _weather_where(config), "weather from Open-Meteo"),
        Capability(("calendar.today",), "read today's calendar",
                   "macOS Calendar and Reminders (read-only)"),
        Capability(("reminders.due",), "read the reminders that are due"),
        Capability(("mac.status",), "check your Mac's battery, memory, disk, and loaded models"),
        Capability(("time.now", "weather.today", "calendar.today", "reminders.due", "mac.status"),
                   "put together the daily brief (type \"brief\")"),
        Capability(("status.next_action",), "read the workstation's next-action report"),
        Capability(("web.search",), "search the web when you type \"search …\"",
                   "Brave web search (it needs its API key in the Keychain)"),
    )


def answer_for(label: str) -> str:
    return NOT_BUILT[label]


def _home_relative(path: Path) -> str:
    home = Path.home()
    try:
        return "~/" + str(Path(path).relative_to(home))
    except ValueError:
        return str(path)


def capabilities_answer(registry, config) -> str:
    live = [c for c in _registry(config) if all(registry.get(t) is not None for t in c.tools)]
    can = "; ".join(c.can for c in live)
    connected = [c.connected for c in live if c.connected]
    connected.append(f"the local model {config.model} on this Mac")
    lines = [f"I can {can}.",
             "Connected: " + ", ".join(connected) + ".",
             NOT_YET,
             "Settings: there's no settings screen yet. Settings live in config.json in the Chief state "
             f"folder ({_home_relative(config.state_dir)})."]
    return "\n".join(lines)
