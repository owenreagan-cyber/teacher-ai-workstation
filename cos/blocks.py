"""Response blocks: the rich form of an answer, built by code from tool results (never by the model).

`cos ask --json` returns "blocks" (a list) and "resources" (link id -> URL) next to the plain
"answer" text, which stays for the CLI, Raycast, and copying. docs/response-blocks.md is the
format. Block types:

  text             {"text"}                                   the answer prose, no URLs
  weather_now      {"place", "temp_f", "feels_like_f", "conditions", "is_day", "high_f",
                    "low_f", "rain_chance_pct", "wind_mph", "as_of"}
  forecast_hourly  {"place", "points": [{"time", "temp_f", "rain_chance_pct", "conditions", "is_day"}]}
  forecast_daily   {"place", "days": [{"date", "label", "high_f", "low_f", "rain_chance_pct", "conditions"}]}
  sources          {"items": [{"title", "site", "link_id"}]}   link_id is null when there is no https URL
  searched         {"query"}                                  the exact query sent
  suggestions      {"items": [{"label", "message"}]}          2-4 follow-ups; a button sends "message"
  notice           {"level": "info"|"warning", "text"}

No block string may contain a URL: links travel only as link ids, and a resource ({"id", "url"},
https only) is kept by the desktop main process, never the window. validate_blocks() rejects an
unknown type or a bad field (BlockError); the builders below only emit valid blocks.
"""
from __future__ import annotations

import hashlib
import re
import urllib.parse

BLOCK_TYPES = ("text", "weather_now", "forecast_hourly", "forecast_daily", "sources", "searched",
               "suggestions", "notice")
MAX_BLOCKS = 12
MAX_RESOURCES = 20
MAX_TEXT = 4000
LINK_ID_RE = re.compile(r"lnk-[0-9a-f]{16}")
URL_LIKE = re.compile(r"\b(?:https?|file|javascript):|\bwww\.[a-z0-9-]+\.", re.IGNORECASE)
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")


class BlockError(ValueError):
    pass


# ----------------------------------------------------------------------------- validation

def _str(v, where: str, cap: int = 200, empty: bool = False) -> str:
    if not isinstance(v, str) or len(v) > cap or (not empty and not v.strip()):
        raise BlockError(f"{where}: text of 1-{cap} characters")
    if URL_LIKE.search(v):
        raise BlockError(f"{where}: contains a URL")
    return v


def _opt_str(v, where: str, cap: int = 200):
    return None if v is None else _str(v, where, cap)


def _int(v, where: str, lo: int, hi: int):
    if v is None:
        return None
    if not isinstance(v, int) or isinstance(v, bool) or not lo <= v <= hi:
        raise BlockError(f"{where}: integer {lo}..{hi} or null")
    return v


def _opt_bool(v, where: str):
    if v is not None and not isinstance(v, bool):
        raise BlockError(f"{where}: true, false, or null")
    return v


def _exact(obj, fields: tuple[str, ...], where: str) -> dict:
    if not isinstance(obj, dict):
        raise BlockError(f"{where}: must be an object")
    extra = set(obj) - set(fields)
    missing = set(fields) - set(obj)
    if extra or missing:
        raise BlockError(f"{where}: fields {sorted(fields)} (extra {sorted(extra)}, missing {sorted(missing)})")
    return obj


def _list(v, where: str, lo: int, hi: int) -> list:
    if not isinstance(v, list) or not lo <= len(v) <= hi:
        raise BlockError(f"{where}: a list of {lo}-{hi} items")
    return v


def _temp(v, where):
    return _int(v, where, -100, 150)


def _pct(v, where):
    return _int(v, where, 0, 100)


def validate_block(b) -> dict:
    t = b.get("type") if isinstance(b, dict) else None
    if t not in BLOCK_TYPES:
        raise BlockError(f"unknown block type {t!r}")
    if t == "text":
        _exact(b, ("type", "text"), t)
        _str(b["text"], "text.text", MAX_TEXT)
    elif t == "weather_now":
        _exact(b, ("type", "place", "temp_f", "feels_like_f", "conditions", "is_day", "high_f", "low_f",
                   "rain_chance_pct", "wind_mph", "as_of"), t)
        _str(b["place"], "weather_now.place", 100)
        _str(b["conditions"], "weather_now.conditions", 60)
        for k in ("temp_f", "feels_like_f", "high_f", "low_f"):
            _temp(b[k], f"weather_now.{k}")
        _pct(b["rain_chance_pct"], "weather_now.rain_chance_pct")
        _int(b["wind_mph"], "weather_now.wind_mph", 0, 300)
        _opt_bool(b["is_day"], "weather_now.is_day")
        _opt_str(b["as_of"], "weather_now.as_of", 20)
    elif t == "forecast_hourly":
        _exact(b, ("type", "place", "points"), t)
        _str(b["place"], "forecast_hourly.place", 100)
        for i, p in enumerate(_list(b["points"], "forecast_hourly.points", 1, 24)):
            w = f"forecast_hourly.points[{i}]"
            _exact(p, ("time", "temp_f", "rain_chance_pct", "conditions", "is_day"), w)
            _str(p["time"], f"{w}.time", 20)
            _temp(p["temp_f"], f"{w}.temp_f")
            _pct(p["rain_chance_pct"], f"{w}.rain_chance_pct")
            _str(p["conditions"], f"{w}.conditions", 60)
            _opt_bool(p["is_day"], f"{w}.is_day")
    elif t == "forecast_daily":
        _exact(b, ("type", "place", "days"), t)
        _str(b["place"], "forecast_daily.place", 100)
        for i, d in enumerate(_list(b["days"], "forecast_daily.days", 1, 7)):
            w = f"forecast_daily.days[{i}]"
            _exact(d, ("date", "label", "high_f", "low_f", "rain_chance_pct", "conditions"), w)
            if not isinstance(d["date"], str) or not DATE_RE.fullmatch(d["date"]):
                raise BlockError(f"{w}.date: YYYY-MM-DD")
            _str(d["label"], f"{w}.label", 20)
            _temp(d["high_f"], f"{w}.high_f")
            _temp(d["low_f"], f"{w}.low_f")
            _pct(d["rain_chance_pct"], f"{w}.rain_chance_pct")
            _str(d["conditions"], f"{w}.conditions", 60)
    elif t == "sources":
        _exact(b, ("type", "items"), t)
        for i, it in enumerate(_list(b["items"], "sources.items", 1, 5)):
            w = f"sources.items[{i}]"
            _exact(it, ("title", "site", "link_id"), w)
            _str(it["title"], f"{w}.title")
            _str(it["site"], f"{w}.site", 100)
            if it["link_id"] is not None and not (isinstance(it["link_id"], str)
                                                  and LINK_ID_RE.fullmatch(it["link_id"])):
                raise BlockError(f"{w}.link_id: lnk-<16 hex> or null")
    elif t == "searched":
        _exact(b, ("type", "query"), t)
        _str(b["query"], "searched.query")
    elif t == "suggestions":
        _exact(b, ("type", "items"), t)
        for i, it in enumerate(_list(b["items"], "suggestions.items", 2, 4)):
            w = f"suggestions.items[{i}]"
            _exact(it, ("label", "message"), w)
            _str(it["label"], f"{w}.label", 60)
            _str(it["message"], f"{w}.message", 300)
    else:  # notice
        _exact(b, ("type", "level", "text"), t)
        if b["level"] not in ("info", "warning"):
            raise BlockError("notice.level: info or warning")
        _str(b["text"], "notice.text", 500)
    return b


def validate_blocks(blocks) -> list[dict]:
    for i, b in enumerate(_list(blocks, "blocks", 0, MAX_BLOCKS)):
        try:
            validate_block(b)
        except BlockError as e:
            raise BlockError(f"blocks[{i}]: {e}")
    return blocks


def https_url(url) -> str | None:
    if not isinstance(url, str) or len(url) > 2000 or re.search(r"[\s\x00-\x1f\x7f]", url):
        return None
    try:
        parts = urllib.parse.urlsplit(url)
    except ValueError:
        return None
    if parts.scheme != "https" or not parts.hostname or parts.username or parts.password:
        return None
    return url


def validate_resources(resources) -> list[dict]:
    for i, r in enumerate(_list(resources, "resources", 0, MAX_RESOURCES)):
        _exact(r, ("id", "url"), f"resources[{i}]")
        if not isinstance(r["id"], str) or not LINK_ID_RE.fullmatch(r["id"]):
            raise BlockError(f"resources[{i}].id: lnk-<16 hex>")
        if https_url(r["url"]) is None:
            raise BlockError(f"resources[{i}].url: an https URL")
    return resources


# ----------------------------------------------------------------------------- builders

def link_id(url: str) -> str:
    return "lnk-" + hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]


def _no_urls(text: str, cap: int) -> str:
    from cos.guards import strip_urls
    out = strip_urls(str(text or ""), ())[0].strip()
    out = URL_LIKE.sub("", out).strip()  # anything URL-like that is not a full URL
    return out[:cap - 1].rstrip() + "…" if len(out) > cap else out


def text_block(text: str) -> dict | None:
    t = _no_urls(text, MAX_TEXT)
    return {"type": "text", "text": t} if t else None


def notice_blocks(notices: list[str]) -> list[dict]:
    out = []
    for n in notices:
        t = _no_urls(n, 500)
        if t:
            level = "warning" if re.search(r"unavailable|limit|stopped|couldn'?t", t, re.IGNORECASE) else "info"
            out.append({"type": "notice", "level": level, "text": t})
    return out


def suggestions_block(pairs) -> dict | None:
    items = [{"label": _no_urls(label, 60), "message": _no_urls(msg, 300)} for label, msg in pairs][:4]
    items = [it for it in items if it["label"] and it["message"]]
    return {"type": "suggestions", "items": items} if len(items) >= 2 else None


def searched_block(query: str) -> dict | None:
    q = str(query or "").strip()
    return {"type": "searched", "query": q} if q and not URL_LIKE.search(q) and len(q) <= 200 else None


def sources(results: list[dict]) -> tuple[dict | None, list[dict]]:
    """(sources block, resources) for search results. Only https URLs become links."""
    items, resources = [], []
    for r in results[:5]:
        url = https_url(r.get("url"))
        site = (urllib.parse.urlsplit(str(r.get("url") or "")).hostname or "").removeprefix("www.")
        title = _no_urls(r.get("title"), 200) or site or "Result"
        lid = link_id(url) if url else None
        if url and lid not in {x["id"] for x in resources}:
            resources.append({"id": lid, "url": url})
        items.append({"title": title, "site": _no_urls(site, 100) or "web", "link_id": lid})
    return ({"type": "sources", "items": items} if items else None), resources


def weather_now(r: dict, place: str) -> dict:
    return {"type": "weather_now", "place": _no_urls(place, 100) or "Home",
            "temp_f": r.get("now_f"), "feels_like_f": r.get("feels_like_f"),
            "conditions": _no_urls(r.get("conditions") or "unknown", 60) or "unknown",
            "is_day": r.get("is_day") if isinstance(r.get("is_day"), bool) else None,
            "high_f": r.get("high_f"), "low_f": r.get("low_f"), "rain_chance_pct": r.get("rain_chance_pct"),
            "wind_mph": r.get("wind_mph"), "as_of": _no_urls(r.get("as_of") or "", 20) or None}


def forecast_daily(days: list[dict], place: str) -> dict | None:
    rows = [{"date": d["date"], "label": str(d.get("label") or d.get("weekday"))[:20],
             "high_f": d.get("high_f"), "low_f": d.get("low_f"), "rain_chance_pct": d.get("rain_chance_pct"),
             "conditions": str(d.get("conditions") or "unknown")[:60]} for d in days[:7] if d.get("date")]
    return {"type": "forecast_daily", "place": _no_urls(place, 100) or "Home", "days": rows} if rows else None


def forecast_hourly(hours: list[dict], place: str) -> dict | None:
    pts = [{"time": str(h.get("time"))[:20], "temp_f": h.get("temp_f"), "rain_chance_pct": h.get("rain_chance_pct"),
            "conditions": str(h.get("conditions") or "unknown")[:60],
            "is_day": h.get("is_day") if isinstance(h.get("is_day"), bool) else None} for h in hours[:24]]
    return {"type": "forecast_hourly", "place": _no_urls(place, 100) or "Home", "points": pts} if pts else None


def keep_valid(blocks: list) -> list[dict]:
    """The blocks that validate (a builder bug drops one block, never the answer)."""
    out = []
    for b in blocks:
        if b is None:
            continue
        try:
            out.append(validate_block(b))
        except BlockError:
            continue
    return out[:MAX_BLOCKS]
