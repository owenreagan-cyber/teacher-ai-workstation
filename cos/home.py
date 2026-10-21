"""cos home: one snapshot for the Today page of the Chief window (no model).

Sections: weather, calendar, reminders, mac, needs, builds, agents. Each carries
its own freshness:

  {"status": "current" | "updating" | "stale" | "unavailable",
   "generated_at": ISO time the data was fetched (or null), "interval_s": N,
   "reason": human text when status is not "current" (else null),
   "data": the section's fields (or null when nothing was ever fetched)}

needs comes from cos/needs.py. Its https links become link ids; the URLs are in the
top-level "resources", as in `cos ask`.

Cache first. The snapshot lives in cache/home.json in the state folder (0600).
`cos home --json --cached` reads only that file and runs nothing, so the window
paints at once; a section past its interval says "updating". `cos home --json`
refreshes only the sections that are due (each on its own interval, in
parallel, through the policy gate and executor like the brief), writes the cache,
and returns the snapshot. A source that fails keeps its last good data and turns
"stale" ("Couldn't refresh: ..."), or "unavailable" if it never worked: one
failing source never blanks the others. `--only mac,weather` limits a refresh.

Two refreshes never run at once (an flock on cache/home.lock); the second one
returns the cache as it is. While the kill switch is set nothing refreshes and
every section reports why.

The greeting and the date are never cached: they are computed from the clock on
every call (the window recomputes them too). Polling is quiet: no gate decision
or tool_result records; one home_refresh audit record per refresh that touched
anything besides the Mac (whose 30-second samples would flood the log).
"""
from __future__ import annotations

import fcntl
import json
import os
import re
import threading
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable

from cos.brief import greeting
from cos.config import ensure_private_subdir, open_private, weather_places
from cos.executor import run_tool

SECTIONS = ("weather", "calendar", "reminders", "mac", "needs", "builds", "agents")
INTERVALS = {"weather": 15 * 60, "calendar": 5 * 60, "reminders": 5 * 60, "mac": 30,
             "needs": 60, "builds": 10 * 60, "agents": 60}
STATUSES = ("current", "updating", "stale", "unavailable")
CACHE_NAME = "home.json"
MAX_BUILDS = 5
MAX_EVENTS = 12
MAX_REMINDERS = 8
REFRESH_TIMEOUT_S = 25
COURSE_CODE_RE = re.compile(r"^([A-Z][A-Z0-9]{1,6})(?::\s*|\s+[-–]\s+)(.+)$")
PR_SUBJECT_RE = re.compile(r"^Merge pull request #(\d+) from (\S+)")

# Mac health: "attention" when any of these is crossed.
MEMORY_LOW_PCT = 15
DISK_LOW_GB = 20
BATTERY_LOW_PCT = 20
CPU_HIGH_PCT = 90


class SourceError(Exception):
    """A source could not produce data; the message is shown to Owen (no trace)."""


@dataclass
class Source:
    name: str
    interval_s: int
    fetch: Callable[[], dict]


def _iso(dt: datetime) -> str:
    return dt.isoformat(timespec="seconds")


def _parse_iso(value) -> datetime | None:
    try:
        return datetime.fromisoformat(str(value))
    except ValueError:
        return None


def _clock(dt: datetime) -> str:
    return dt.strftime("%I:%M %p").lstrip("0")


# ----------------------------------------------------------------------------- shaping tool results

def _tool(registry, gate, name: str, args: dict | None = None) -> dict:
    args = args or {}
    decision = gate.decide(name, args, subject="home")
    tool = registry.get(name)
    if not decision.allowed or tool is None:
        raise SourceError("Chief is stopped" if decision.rule == "kill_switch" else f"not allowed ({decision.rule})")
    result = run_tool(tool, args, decision, audit=None)
    if "error" in result:
        raise SourceError(str(result["error"])[:200])
    return result


def weather_data(result: dict) -> dict:
    days = [{k: d.get(k) for k in ("date", "label", "high_f", "low_f", "rain_chance_pct", "conditions")}
            for d in result.get("daily", []) if isinstance(d, dict)][:7]
    return {"place": result.get("place"), "temp_f": result.get("now_f"), "feels_like_f": result.get("feels_like_f"),
            "conditions": result.get("conditions"), "is_day": result.get("is_day"),
            "high_f": result.get("high_f"), "low_f": result.get("low_f"),
            "rain_chance_pct": result.get("rain_chance_pct"), "wind_mph": result.get("wind_mph"), "days": days}


def course_chip(title: str) -> tuple[str | None, str]:
    """("SM5", "Lesson 42") for "SM5: Lesson 42"; (None, title) when there is no course code."""
    m = COURSE_CODE_RE.match(title)
    return (m.group(1), m.group(2).strip()) if m else (None, title)


def calendar_data(result: dict) -> dict:
    events = []
    for ev in result.get("events", [])[:MAX_EVENTS]:
        if not isinstance(ev, dict):
            continue
        code, title = course_chip(str(ev.get("title") or "(no title)"))
        events.append({"title": title, "course": code, "all_day": bool(ev.get("all_day")),
                       "start": ev.get("start"), "end": ev.get("end"), "start_iso": ev.get("start_iso")})
    return {"count": len(result.get("events", [])), "events": events}


def _plural(n: int, word: str) -> str:
    return f"{n} {word}" if n == 1 else f"{n} {word}s"


def reminders_data(result: dict) -> dict:
    items = [r for r in result.get("reminders", []) if isinstance(r, dict)]
    overdue = sum(1 for r in items if r.get("overdue"))
    line = "No reminders due" if not items else (
        _plural(len(items), "reminder") + " due" + (f" ({overdue} overdue)" if overdue else ""))
    return {"count": len(items), "overdue": overdue, "line": line,
            "items": [{"title": r.get("title"), "due": r.get("due"), "overdue": bool(r.get("overdue"))}
                      for r in items[:MAX_REMINDERS]]}


def mac_data(result: dict) -> dict:
    loaded = result.get("ollama_loaded")
    data = {
        "memory_free_pct": result.get("memory_free_pct"),
        "cpu_load_pct": result.get("cpu_load_pct"),
        "disk_free_gb": result.get("disk_free_gb"),
        "disk_total_gb": result.get("disk_total_gb"),
        "battery_pct": result.get("battery_pct"),
        "battery_state": result.get("battery_state"),
        "power_source": result.get("power_source"),
        "uptime": result.get("uptime"),
        "loaded_models": [str(m) for m in loaded] if isinstance(loaded, list) else None,
    }
    attention = []
    if isinstance(data["memory_free_pct"], int) and data["memory_free_pct"] < MEMORY_LOW_PCT:
        attention.append(f"Memory is low ({data['memory_free_pct']}% free)")
    if isinstance(data["cpu_load_pct"], int) and data["cpu_load_pct"] >= CPU_HIGH_PCT:
        attention.append(f"CPU is busy ({data['cpu_load_pct']}% load)")
    if isinstance(data["disk_free_gb"], int) and data["disk_free_gb"] < DISK_LOW_GB:
        attention.append(f"Disk is nearly full ({data['disk_free_gb']} GB free)")
    if (isinstance(data["battery_pct"], int) and data["battery_pct"] < BATTERY_LOW_PCT
            and data["power_source"] != "AC power"):
        attention.append(f"Battery is low ({data['battery_pct']}%)")
    data["health"] = "attention" if attention else "healthy"
    data["attention"] = attention
    return data


def parse_merges(text: str) -> list[dict]:
    """`git log --merges --format=%h%x1f%s%x1f%b%x1f%cI%x1e` output -> build rows. A GitHub merge
    commit's title is the PR title (the first body line), with its number."""
    out = []
    for record in text.split("\x1e"):
        parts = record.strip("\n").split("\x1f")
        if len(parts) < 4 or not parts[0].strip():
            continue
        ref, subject, body, when = (p.strip() for p in parts[:4])
        m = PR_SUBJECT_RE.match(subject)
        first_body = next((l.strip() for l in body.splitlines() if l.strip()), "")
        title = first_body if m and first_body else subject
        out.append({"title": title[:120], "ref": ref[:12], "pr": int(m.group(1)) if m else None,
                    "merged_at": when or None})
    return out[:MAX_BUILDS]


def builds_from_git(ctx) -> dict:
    fmt = "%h%x1f%s%x1f%b%x1f%cI%x1e"
    for ref in ("refs/heads/main", "refs/remotes/origin/main"):
        res = ctx.run(["/usr/bin/git", "-C", str(ctx.config.repo_root), "log", ref, "--merges",
                       f"-n{MAX_BUILDS}", f"--format={fmt}"], timeout=5)
        if res.returncode == 0:
            return {"branch": "main", "items": parse_merges(res.stdout)}
    raise SourceError("main branch not found in the repo")


def builds_from_fixture(fixture_dir: Path) -> dict:
    try:
        data = json.loads((fixture_dir / "builds.json").read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise SourceError("fixture builds.json not present")
    except (OSError, ValueError) as e:
        raise SourceError(f"fixture builds.json unreadable ({type(e).__name__})")
    items = data.get("items") if isinstance(data, dict) else None
    if not isinstance(items, list):
        raise SourceError("fixture builds.json has no items list")
    return {"branch": "main", "items": items[:MAX_BUILDS]}


def default_sources(rt) -> list[Source]:
    """The real sources, from a cli.Runtime (fixture mode uses fixture readers throughout)."""
    from cos import needs

    reg, gate, ctx = rt.registry, rt.gate, rt.ctx

    def builds():
        return builds_from_fixture(rt.config.fixture_dir) if rt.config.fixture_dir else builds_from_git(ctx)

    def needs_source():
        got = needs.gather(rt.config, ctx, ctx.clock())
        return {"items": got["items"], "resources": got["resources"]}

    return [
        Source("weather", INTERVALS["weather"], lambda: weather_data(_tool(reg, gate, "weather.today"))),
        Source("calendar", INTERVALS["calendar"], lambda: calendar_data(_tool(reg, gate, "calendar.today"))),
        Source("reminders", INTERVALS["reminders"], lambda: reminders_data(_tool(reg, gate, "reminders.due"))),
        Source("mac", INTERVALS["mac"], lambda: mac_data(_tool(reg, gate, "mac.status"))),
        Source("needs", INTERVALS["needs"], needs_source),
        Source("builds", INTERVALS["builds"], builds),
        Source("agents", INTERVALS["agents"], lambda: {"available": False, "items": []}),
    ]


# ----------------------------------------------------------------------------- cache and freshness

def cache_path(state_dir: Path) -> Path:
    return ensure_private_subdir("cache", state_dir) / CACHE_NAME


def read_cache(state_dir: Path) -> dict:
    """{section: {"generated_at", "data", "error", "error_at"}}; {} when missing or damaged."""
    try:
        data = json.loads(cache_path(state_dir).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    sections = data.get("sections") if isinstance(data, dict) else None
    if not isinstance(sections, dict):
        return {}
    return {k: v for k, v in sections.items() if k in SECTIONS and isinstance(v, dict)}


def write_cache(state_dir: Path, sections: dict) -> None:
    path = cache_path(state_dir)
    tmp = path.with_name(f".{CACHE_NAME}.{os.getpid()}.tmp")
    with open_private(tmp, "w") as fh:
        json.dump({"version": 1, "sections": sections}, fh)
    os.replace(tmp, path)


def section_view(name: str, entry: dict | None, now: datetime, *, stopped: bool, pending: bool) -> dict:
    """The public form of one section. pending: a refresh is due but this call does not run it."""
    interval = INTERVALS[name]
    entry = entry or {}
    generated = _parse_iso(entry.get("generated_at"))
    data = entry.get("data") if isinstance(entry.get("data"), dict) else None
    error = entry.get("error")
    age = (now - generated).total_seconds() if generated else None
    due = age is None or age >= interval or age < 0
    last = f"last checked {_clock(generated.astimezone(now.tzinfo))}" if generated else None
    if data is None:
        if stopped:
            status, reason = "unavailable", "Chief is stopped"
        elif error and not pending:
            status, reason = "unavailable", str(error)
        else:
            status, reason = "updating", "Checking for the first time"
    elif stopped and due:
        status, reason = "stale", f"Chief is stopped · {last}"
    elif error and due:
        status, reason = "stale", f"Couldn't refresh: {error} · {last}"
    elif due and pending:
        status, reason = "updating", f"Refreshing · {last}"
    elif due:
        status, reason = "stale", f"Stale · {last}"
    else:
        status, reason = "current", None
    return {"status": status, "generated_at": _iso(generated) if generated else None,
            "interval_s": interval, "reason": reason, "data": data}


def is_due(entry: dict | None, name: str, now: datetime) -> bool:
    generated = _parse_iso((entry or {}).get("generated_at"))
    if generated is None:
        return True
    age = (now - generated).total_seconds()
    return age < 0 or age >= INTERVALS[name]


def refresh(sources: list[Source], cache: dict, now: datetime, names: set[str]) -> list[str]:
    """Fetch the named sources in parallel; update cache in place. Returns the names refreshed ok."""
    results: dict[str, tuple[dict | None, str | None]] = {}

    def work(src: Source):
        try:
            data = src.fetch()
            if not isinstance(data, dict):
                raise SourceError("unexpected result")
            results[src.name] = (data, None)
        except SourceError as e:
            results[src.name] = (None, str(e) or "unavailable")
        except Exception as e:  # noqa: BLE001 - one failing source never blanks the others
            results[src.name] = (None, f"{type(e).__name__}")

    threads = [threading.Thread(target=work, args=(s,), daemon=True) for s in sources if s.name in names]
    for t in threads:
        t.start()
    for t in threads:
        t.join(REFRESH_TIMEOUT_S)
    ok = []
    for src in sources:
        if src.name not in names:
            continue
        data, error = results.get(src.name, (None, "timed out"))
        entry = dict(cache.get(src.name) or {})
        if data is not None:
            entry.update({"generated_at": _iso(now), "data": data, "error": None})
            ok.append(src.name)
        else:
            entry.update({"error": error, "error_at": _iso(now)})
        cache[src.name] = entry
    return ok


def snapshot(state_dir: Path, sources: list[Source], now: datetime, *, place: str | None,
             cached_only: bool = False, only: set[str] | None = None, stopped: bool = False,
             audit=None) -> dict:
    """The home snapshot (see the module docstring)."""
    wanted = set(only or SECTIONS) & set(SECTIONS)
    refreshed: list[str] = []
    lock_path = ensure_private_subdir("cache", state_dir) / "home.lock"
    busy = False
    with open_private(lock_path, "a") as lock:
        cache = read_cache(state_dir)
        if not cached_only and not stopped:
            try:
                fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError:
                busy = True
            if not busy:
                cache = read_cache(state_dir)  # re-read under the lock
                due = {n for n in wanted if is_due(cache.get(n), n, now)}
                if due:
                    refreshed = refresh(sources, cache, now, due)
                    write_cache(state_dir, cache)
                    if audit is not None and due - {"mac"}:
                        audit("home_refresh", sections=sorted(due), ok=sorted(refreshed))
    def pending(name: str) -> bool:  # due, but this call does not refresh it
        return cached_only or busy or name not in wanted

    views = {name: section_view(name, cache.get(name), now, stopped=stopped, pending=pending(name))
             for name in SECTIONS}
    # Needs' https links travel as link ids; their URLs go in "resources" (main process only).
    needs = views["needs"]["data"]
    resources = []
    if needs is not None:
        resources = needs.get("resources") or []
        views["needs"]["data"] = {"items": needs.get("items") or []}
    return {
        "ok": True,
        "generated_at": _iso(now),
        "greeting": greeting(now),
        "date": now.strftime("%A, %B ") + str(now.day),
        "place": place,
        "stopped": stopped,
        **views,
        "resources": resources,
    }


def home_place(config) -> str | None:
    places = weather_places(config)
    home = places.get("home") or next(iter(places.values()), None)
    return home.name if home else None
