"""weather.today: today's forecast from Open-Meteo for the configured lat/lon.

Coordinates come from config.json (Owen fills them in) and are rounded to
two decimals (~1 km) before leaving the Mac. Responses are cached for 30
minutes in the state directory.
"""
from __future__ import annotations

import json
import urllib.parse

from cos.config import ensure_private_subdir, open_private
from cos.registry import Tool

API = "https://api.open-meteo.com/v1/forecast"
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
        "current": "temperature_2m,apparent_temperature,weather_code,wind_speed_10m",
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max,weather_code",
        "temperature_unit": "fahrenheit", "wind_speed_unit": "mph",
        "timezone": "auto", "forecast_days": 1,
    })
    return f"{API}?{query}"


def parse(data: dict) -> dict:
    cur, daily = data.get("current", {}), data.get("daily", {})

    def first(key):
        values = daily.get(key) or [None]
        return values[0]

    def num(v):
        return round(v) if isinstance(v, (int, float)) else None

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


def today(ctx, args: dict) -> dict:
    cfg = ctx.config
    if cfg.latitude is None or cfg.longitude is None:
        return {"error": "weather location not configured: set latitude and longitude in "
                         f"{cfg.state_dir / 'config.json'}"}
    url = build_url(cfg.latitude, cfg.longitude)
    now = ctx.clock()
    cache_file = ensure_private_subdir("cache", cfg.state_dir) / "weather.json"
    try:
        cached = json.loads(cache_file.read_text(encoding="utf-8"))
        age = now.timestamp() - cached["fetched_at"]
        if cached.get("url") == url and 0 <= age < CACHE_SECONDS:
            return {**cached["weather"], "cached": True}
    except (OSError, ValueError, KeyError, TypeError):
        pass
    raw = ctx.http("GET", url, headers={"User-Agent": "ChiefOfStaff/0.1 (local)"},
                   timeout=10, audit=ctx.audit)
    weather = parse(json.loads(raw))
    with open_private(cache_file, "w") as fh:
        json.dump({"fetched_at": now.timestamp(), "url": url, "weather": weather}, fh)
    return {**weather, "cached": False,
            "as_of": now.strftime("%I:%M %p").lstrip("0")}


def tools(ctx):
    return [Tool(
        name="weather.today",
        description="Today's weather at Owen's configured location: now, high/low, rain chance, wind.",
        parameters={"type": "object", "properties": {}, "additionalProperties": False},
        side_effect="none", data_class="P2", timeout_s=15,
        func=lambda args: today(ctx, args), keywords=KEYWORDS,
    )]
