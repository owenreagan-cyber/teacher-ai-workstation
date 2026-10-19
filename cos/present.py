"""Presenter: the blocks and resources for an answer, chosen by code (cos/blocks.py).

The model chooses meaning, cos chooses the blocks, the window chooses the look. present()
reads what the answering path recorded in AgentResult.extras (search results, the weather
result and which parts the answer covered, follow-ups to offer) and never reads model text
except the prose itself, which becomes a text block with every URL removed.
"""
from __future__ import annotations

from cos import blocks as B
from cos.config import weather_places

SEARCHED_SEP = "\n\nSearched: "

WEATHER_FOLLOW_UPS = (("now", "Now", "weather"), ("tomorrow", "Tomorrow", "weather tomorrow"),
                      ("hourly", "Hourly", "hourly forecast"), ("days5", "5-day forecast", "5 day forecast"),
                      ("weekend", "This weekend", "weather this weekend"))


def weather_suggestions(req, places) -> list[tuple[str, str]]:
    if req is None:
        return [(f"{p.short_name} weather", "weather" if k == "home" else f"weather at {k}")
                for k, p in list(places.items())[:3]]
    at = "" if req.place.key == "home" else f" at {req.place.key}"
    picks = [(label, msg + at) for span, label, msg in WEATHER_FOLLOW_UPS if span != req.span][:3]
    other = next((p for k, p in places.items() if k != req.place.key), None)
    if other is not None:
        picks.append((f"{other.short_name} weather", "weather" if other.key == "home" else f"weather at {other.key}"))
    return picks


def present(result, config) -> None:
    """Fill result.blocks and result.resources (both validated)."""
    ex = result.extras or {}
    out: list = []
    resources: list[dict] = []
    if "search" in ex:
        summary = result.answer.split(SEARCHED_SEP, 1)[0]
        if result.model is None and summary.startswith("Web results for"):
            summary = "Here are the top web results."
        out.append(B.text_block(summary))
        out.append(B.searched_block(result.search_query))
        src, resources = B.sources(ex["search"])
        out.append(src)
    else:
        out.append(B.text_block(result.answer.split(SEARCHED_SEP, 1)[0]))
    weather = ex.get("weather")
    if weather:
        r, shown, place = weather["result"], weather["shown"], weather["place"]
        if shown.get("now"):
            out.append(B.weather_now(r, place))
        if shown.get("hours"):
            out.append(B.forecast_hourly(shown["hours"], place))
        if shown.get("days"):
            out.append(B.forecast_daily(shown["days"], place))
    out += B.notice_blocks(result.notices)
    pairs = ex.get("suggestions")
    if pairs is None and "weather_request" in ex:
        pairs = weather_suggestions(ex["weather_request"], weather_places(config))
    if pairs:
        out.append(B.suggestions_block(pairs))
    result.blocks = B.keep_valid(out)
    result.resources = B.validate_resources(resources)
