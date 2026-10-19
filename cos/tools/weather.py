"""weather.today: current conditions and the forecast from Open-Meteo for one of Owen's places.

Places come from config.json ("places", see cos/config.py): the optional
"place" argument is one of their keys (default home). Coordinates are rounded
to two decimals (~1 km) before leaving the Mac. Responses are cached for 30
minutes per place in the state directory. The result names the place ("place",
"place_key") so every answer can say where the weather is for.

The result keeps today's flat fields (now_f, high_f, low_f, rain_chance_pct,
conditions, ...) and adds is_day, sunrise, sunset, "tomorrow", "daily" (7 days,
today first, each labeled today / tomorrow / weekday), "hourly" (the next 12
hours from the current hour), and forecast_note, which states the last day
covered so the model can say it has nothing beyond it.
"""
from __future__ import annotations

import json
import urllib.parse
from datetime import date, datetime

from cos.config import Place, ensure_private_subdir, open_private, weather_places
from cos.registry import Tool

API = "https://api.open-meteo.com/v1/forecast"
FORECAST_DAYS = 7
FORECAST_HOURS = 12
CACHE_SECONDS = 30 * 60
KEYWORDS = ("weather", "rain", "raining", "temperature", "cold", "hot", "warm", "jacket",
            "umbrella", "forecast", "outside", "snow", "wind", "windy", "recess", "sunny", "storm")

WMO = {0: "clear", 1: "mostly clear", 2: "partly cloudy", 3: "overcast", 45: "fog", 48: "fog",
       51: "light drizzle", 53: "drizzle", 55: "heavy drizzle", 56: "freezing drizzle",
       57: "freezing drizzle", 61: "light rain", 63: "rain", 65: "heavy rain",
       66: "freezing rain", 67: "freezing rain", 71: "light snow", 73: "snow", 75: "heavy snow",
       77: "snow grains", 80: "light showers", 81: "showers", 82: "heavy showers",
       85: "snow showers", 86: "snow showers", 95: "thunderstorm", 96: "thunderstorm with hail",
       99: "thunderstorm with hail"}


def build_url(lat: float, lon: float) -> str:
    query = urllib.parse.urlencode({
        "latitude": f"{lat:.2f}", "longitude": f"{lon:.2f}",
        "current": "temperature_2m,apparent_temperature,weather_code,wind_speed_10m,is_day",
        "daily": ("temperature_2m_max,temperature_2m_min,precipitation_probability_max,weather_code,"
                  "sunrise,sunset"),
        "hourly": "temperature_2m,precipitation_probability,weather_code,is_day",
        "temperature_unit": "fahrenheit", "wind_speed_unit": "mph",
        "timezone": "auto", "forecast_days": FORECAST_DAYS, "forecast_hours": FORECAST_HOURS,
    })
    return f"{API}?{query}"


def _num(v):
    return round(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def _local(value) -> datetime | None:
    """Open-Meteo local time ("2026-10-01T07:13", timezone=auto) as a naive datetime."""
    try:
        return datetime.fromisoformat(str(value))
    except ValueError:
        return None


def _clock(value) -> str | None:
    dt = _local(value)
    return dt.strftime("%I:%M %p").lstrip("0") if dt else None


def _at(table: dict, key: str, i: int):
    values = table.get(key)
    return values[i] if isinstance(values, list) and i < len(values) else None


def _daily(daily: dict) -> list[dict]:
    days = []
    times = daily.get("time") if isinstance(daily.get("time"), list) else []
    for i, day in enumerate(times[:FORECAST_DAYS]):
        try:
            d = date.fromisoformat(str(day))
        except ValueError:
            continue
        label = "today" if i == 0 else "tomorrow" if i == 1 else d.strftime("%A")
        days.append({"date": d.isoformat(), "label": label, "weekday": d.strftime("%A"),
                     "high_f": _num(_at(daily, "temperature_2m_max", i)),
                     "low_f": _num(_at(daily, "temperature_2m_min", i)),
                     "rain_chance_pct": _num(_at(daily, "precipitation_probability_max", i)),
                     "conditions": WMO.get(_at(daily, "weather_code", i), "unknown"),
                     "sunrise": _clock(_at(daily, "sunrise", i)), "sunset": _clock(_at(daily, "sunset", i))})
    return days


def _hourly(hourly: dict, now_local) -> list[dict]:
    """The next FORECAST_HOURS hours, starting with the current hour."""
    start = now_local.replace(minute=0, second=0, microsecond=0) if now_local else None
    out = []
    times = hourly.get("time") if isinstance(hourly.get("time"), list) else []
    for i, t in enumerate(times):
        dt = _local(t)
        if dt is None or (start is not None and dt < start):
            continue
        is_day = _at(hourly, "is_day", i)
        out.append({"time": dt.strftime("%I %p").lstrip("0"), "temp_f": _num(_at(hourly, "temperature_2m", i)),
                    "rain_chance_pct": _num(_at(hourly, "precipitation_probability", i)),
                    "conditions": WMO.get(_at(hourly, "weather_code", i), "unknown"),
                    "is_day": bool(is_day) if is_day in (0, 1) else None})
        if len(out) == FORECAST_HOURS:
            break
    return out


def parse(data: dict) -> dict:
    cur, daily = data.get("current", {}), data.get("daily", {})
    hourly = data.get("hourly") if isinstance(data.get("hourly"), dict) else {}

    def first(key):
        values = daily.get(key) or [None]
        return values[0]

    num = _num
    days = _daily(daily)
    tomorrow = ({k: days[1][k] for k in ("date", "weekday", "high_f", "low_f", "rain_chance_pct", "conditions")}
                if len(days) > 1 else None)
    last = days[-1] if days else None
    note = (f"The forecast covers today through {last['weekday']}, {last['date']} ({len(days)} days). "
            "There is no forecast beyond that day." if last else "No daily forecast available.")
    is_day = cur.get("is_day")
    extra = {
        "is_day": bool(is_day) if is_day in (0, 1) else None,
        "sunrise": _clock(first("sunrise")),
        "sunset": _clock(first("sunset")),
        "tomorrow": tomorrow,
        "daily": days,
        "hourly": _hourly(hourly, _local(cur.get("time"))),
        "forecast_note": note,
    }
    return {**_flat(cur, first, num), **extra}


def _flat(cur, first, num) -> dict:
    return {
        "now_f": num(cur.get("temperature_2m")),
        "feels_like_f": num(cur.get("apparent_temperature")),
        "conditions": WMO.get(cur.get("weather_code"), "unknown"),
        "wind_mph": num(cur.get("wind_speed_10m")),
        "high_f": num(first("temperature_2m_max")),
        "low_f": num(first("temperature_2m_min")),
        "rain_chance_pct": num(first("precipitation_probability_max")),
        "day_conditions": WMO.get(first("weather_code"), "unknown"),
    }


def resolve_place(cfg, args: dict) -> tuple[Place | None, str | None]:
    """(place, None) for args["place"] (default home), or (None, error)."""
    places = weather_places(cfg)
    if not places:
        return None, ("weather location not configured: add \"places\" (or latitude and longitude) to "
                      f"{cfg.state_dir / 'config.json'}")
    key = args.get("place") or ("home" if "home" in places else next(iter(places)))
    place = places.get(key)
    if place is None:
        return None, f"unknown place {key!r}; known places: {', '.join(places)}"
    return place, None


def place_fields(place: Place) -> dict:
    return {"place": place.name, "place_key": place.key}


def today(ctx, args: dict) -> dict:
    cfg = ctx.config
    place, error = resolve_place(cfg, args)
    if error:
        return {"error": error}
    url = build_url(place.latitude, place.longitude)
    now = ctx.clock()
    cache_file = ensure_private_subdir("cache", cfg.state_dir) / f"weather-{place.key}.json"
    try:
        cached = json.loads(cache_file.read_text(encoding="utf-8"))
        age = now.timestamp() - cached["fetched_at"]
        if cached.get("url") == url and 0 <= age < CACHE_SECONDS:
            return {**cached["weather"], **place_fields(place), "cached": True}
    except (OSError, ValueError, KeyError, TypeError):
        pass
    raw = ctx.http("GET", url, headers={"User-Agent": "ChiefOfStaff/0.1 (local)"},
                   timeout=10, audit=ctx.audit)
    weather = parse(json.loads(raw))
    with open_private(cache_file, "w") as fh:
        json.dump({"fetched_at": now.timestamp(), "url": url, "weather": weather}, fh)
    return {**weather, **place_fields(place), "cached": False,
            "as_of": now.strftime("%I:%M %p").lstrip("0")}


def tools(ctx):
    keys = list(weather_places(ctx.config)) or ["home"]
    return [Tool(
        name="weather.today",
        description=("Weather at one of Owen's named places (default home): now (temperature, conditions, "
                     "wind, day or night), today's high/low and rain chance, sunrise and sunset, tomorrow, "
                     "a 7-day daily forecast, and the next 12 hours."),
        parameters={"type": "object", "properties": {
            "place": {"type": "string", "enum": keys, "description": "Which named place (default home)"},
        }, "additionalProperties": False},
        side_effect="none", data_class="P2", timeout_s=15,
        func=lambda args: today(ctx, args), keywords=KEYWORDS,
    )]
