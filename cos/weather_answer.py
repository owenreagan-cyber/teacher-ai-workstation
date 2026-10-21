"""Weather answers written by code: no model on a weather turn.

parse(question, places) reads what Owen asked for from his words only: which named place
(home, work, a place name, "at school" for work) and which span (now, tomorrow, a weekday, this
weekend, the 5-day forecast, the next hours, tonight, next week, beyond the forecast, or the
past). A place Chief doesn't know gets the fixed "I only know Sims (home) and Clayton (work) so
far." and no request at all. render(request, result) formats weather.today's result. Every
weather answer starts with the place name, for example:

    Sims, NC — 61°F, overcast. High 61° · Low 47° · Rain 10%.

"what city is that" adds which saved place it is; "use my location" says Chief uses saved places,
not the Mac's location, and that they are changed in Settings (saved in config.json). The
jacket and umbrella notes are fixed thresholds, not judgment calls.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date

from cos.config import Place
from cos.intent import normalize

WEEKDAYS = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
JACKET_FEELS_LIKE_F = 60  # now: feels like below this -> jacket weather
JACKET_LOW_F = 55  # a day: low below this -> jacket weather in the morning
UMBRELLA_RAIN_PCT = 40
HOURLY_STEP = 3

_SPANS = (
    ("past", re.compile(r"\byesterday\b|\blast (?:night|week)\b|\bwas the weather\b|\bdid it rain\b")),
    ("beyond", re.compile(r"\ba week from\b|\bweeks? from (?:now|today)\b|\bin (?:two|three|four|2|3|4) weeks\b|"
                          r"\bnext month\b|\bin (?:[7-9]|[1-9]\d) days\b")),
    ("next_week", re.compile(r"\bnext week\b")),
    ("weekend", re.compile(r"\bweekend\b")),
    ("hourly", re.compile(r"\bhourly\b|\bhour by hour\b|\bby the hour\b|\bnext (?:few|couple of|\d+) hours\b|"
                          r"\bthis afternoon\b|\bthis evening\b|\blater(?: today| on)?\b|\bhours\b")),
    ("tonight", re.compile(r"\btonight\b|\bovernight\b")),
    ("tomorrow", re.compile(r"\btomorrow\b")),
    ("days5", re.compile(r"\b(?:5|five|7|seven)[ -]?day\b|\bthis week\b|\bweek ahead\b|\brest of the week\b|"
                         r"\bforecast\b(?!.*\b(?:today|high|low|now)\b)")),
)
_WEEKDAY = re.compile(r"\b(" + "|".join(WEEKDAYS) + r")s?\b")
_CITY = re.compile(r"\bwhat city\b|\bwhich city\b|\bthe city\b|\bwhat (?:place|town)\b|\bwhere is (?:that|this)\b")
_LOCATION = re.compile(r"\bmy location\b|\bcurrent location\b|\bwhere i am\b|\bwhere im\b|\blocation services\b|"
                       r"\bmy gps\b|\bmy mac s location\b")
_JACKET = re.compile(r"\bjackets?\b|\bcoats?\b|\bsweaters?\b|\bhoodies?\b|\bcold\b|\bchilly\b")
_UMBRELLA = re.compile(r"\bumbrellas?\b|\braincoats?\b")
# "in Raleigh", "forecast for Paris": a place word after "in", "near", or "around", or after "for"
# or "at" right behind a weather word, that isn't a time, school, or filler word.
_PLACE_AFTER = re.compile(r"\b(?:in|near|around) ([a-z][a-z-]*)|"
                          r"\b(?:weather|forecast|temperature|temp|rain|raining|snow|snowing) (?:for|at) ([a-z][a-z-]*)")
_NOT_A_PLACE = frozenset({
    "the", "a", "an", "my", "this", "that", "next", "today", "tonight", "tomorrow", "recess", "lunch",
    "dismissal", "morning", "afternoon", "evening", "night", "noon", "school", "class", "our",
    "least", "all", "case", "general", "detail", "advance", "time", "hours", "days", "weeks", "two",
    "three", "four", "five", "seven", "minutes", "pe", "carpool", "pickup", "drop", "arrival", "your",
    "it", "there", "here", "home", "work", "front", "summary", "short", "f", "fahrenheit", "celsius",
    "me", "us", "you", "them", "kids", "students", "town", "store",
    *WEEKDAYS, *(d + "s" for d in WEEKDAYS)}) | frozenset(str(n) for n in range(100))


@dataclass(frozen=True)
class Request:
    place: Place
    span: str  # now, tomorrow, day, weekend, days5, hourly, tonight, next_week, beyond, past
    weekday: str | None = None
    city_note: bool = False
    location_note: bool = False
    jacket: bool = False
    umbrella: bool = False


def _short_list(places: dict[str, Place]) -> str:
    items = [f"{p.short_name} ({k})" for k, p in places.items()]
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " and " + items[-1]


def unknown_place_answer(places: dict[str, Place]) -> str:
    return f"I only know {_short_list(places)} so far."


def _named_place(q: str, places: dict[str, Place]) -> Place | None:
    for key, place in places.items():
        names = {key, place.short_name.lower(), normalize(place.name)}
        if key == "work":
            names.add("school")
        if any(re.search(rf"\b{re.escape(n)}\b", q) for n in names if n):
            return place
    return None


def _unknown_place(q: str, places: dict[str, Place]) -> bool:
    known = {w for p in places.values() for w in normalize(p.name).split()} | set(places)
    for m in _PLACE_AFTER.finditer(q):
        word = m.group(1) or m.group(2)
        if word not in _NOT_A_PLACE and word not in known:
            return True
    return False


def parse(question: str, places: dict[str, Place], previous_question: str | None = None) -> Request | None:
    """The weather request in Owen's words, or None for a place Chief doesn't know. A follow-up
    that names no place keeps the place of Owen's previous message."""
    q = normalize(question)
    place = _named_place(q, places)
    if place is None and _unknown_place(q, places):
        return None
    if place is None and previous_question:
        place = _named_place(normalize(previous_question), places)
    if place is None:
        place = places.get("home") or next(iter(places.values()))
    span, weekday = "now", None
    for name, pattern in _SPANS:
        if pattern.search(q):
            span = name
            break
    else:
        m = _WEEKDAY.search(q)
        if m:
            span, weekday = "day", m.group(1)
    return Request(place, span, weekday, city_note=bool(_CITY.search(q)), location_note=bool(_LOCATION.search(q)),
                   jacket=bool(_JACKET.search(q)), umbrella=bool(_UMBRELLA.search(q)))


# ----------------------------------------------------------------------------- render

def _deg(v) -> str:
    return "?" if v is None else f"{v}°"


def _pct(v) -> str:
    return "?" if v is None else f"{v}%"


def _day_line(d: dict) -> str:
    return (f"high {_deg(d.get('high_f'))}, low {_deg(d.get('low_f'))}, {d.get('conditions')}. "
            f"Rain {_pct(d.get('rain_chance_pct'))}.")


def _long_date(iso: str) -> str:
    d = date.fromisoformat(iso)
    return d.strftime("%A, %B ") + str(d.day)


def _now(r: dict) -> str:
    return (f"{r.get('now_f')}°F, {r.get('conditions')}. High {_deg(r.get('high_f'))} · "
            f"Low {_deg(r.get('low_f'))} · Rain {_pct(r.get('rain_chance_pct'))}.")


def _jacket_now(r: dict) -> str:
    feels = r.get("feels_like_f")
    if feels is None:
        return ""
    return (f" Jacket weather: it feels like {feels}°F." if feels < JACKET_FEELS_LIKE_F
            else f" No jacket needed: it feels like {feels}°F.")


def _jacket_day(d: dict) -> str:
    low = d.get("low_f")
    if low is None:
        return ""
    return (f" Jacket weather in the morning (low {low}°)." if low < JACKET_LOW_F
            else f" Probably no jacket needed (low {low}°).")


def _umbrella(rain) -> str:
    if rain is None:
        return ""
    return " Bring an umbrella." if rain >= UMBRELLA_RAIN_PCT else " Umbrella probably not needed."


def _find_day(days: list[dict], weekday: str) -> dict | None:
    return next((d for d in days if str(d.get("weekday", "")).lower() == weekday), None)


def _through(days: list[dict]) -> str:
    return _long_date(days[-1]["date"]) if days else "today"


def render(req: Request, r: dict, places: dict[str, Place]) -> tuple[str, dict]:
    """(answer, shown) for weather.today's result r. shown says which forecast parts the answer
    covers ({"now": bool, "days": [...], "hours": [...]}), for the rich blocks."""
    name = r.get("place") or req.place.name
    if "error" in r:
        return f"Weather is unavailable for {name}: {r['error']}.", {"now": False, "days": [], "hours": []}
    days = [d for d in r.get("daily") or [] if isinstance(d, dict)]
    hours = [h for h in r.get("hourly") or [] if isinstance(h, dict)]
    shown = {"now": False, "days": [], "hours": []}
    span = req.span
    if span == "day" and days and days[0].get("weekday", "").lower() == req.weekday:
        span = "now"  # "on Thursday", asked on a Thursday
    if span == "now":
        body = _now(r) + (_jacket_now(r) if req.jacket else "") + (_umbrella(r.get("rain_chance_pct")) if req.umbrella else "")
        shown["now"] = True
    elif span in ("tomorrow", "day"):
        d = days[1] if span == "tomorrow" and len(days) > 1 else _find_day(days[1:], req.weekday or "")
        if d is None:
            body = f"I only have a 7-day forecast, through {_through(days)}."
        else:
            label = f"Tomorrow ({d['weekday']})" if span == "tomorrow" else d["weekday"]
            body = (f"{label}: {_day_line(d)}" + (_jacket_day(d) if req.jacket else "")
                    + (_umbrella(d.get("rain_chance_pct")) if req.umbrella else ""))
            shown["days"] = [d]
    elif span == "weekend":
        weekend = [d for d in days if d.get("weekday") in ("Saturday", "Sunday")]
        if not weekend:
            body = f"I only have a 7-day forecast, through {_through(days)}."
        else:
            body = "This weekend: " + " · ".join(f"{d['weekday']}: {_day_line(d)}" for d in weekend)
            shown["days"] = weekend
    elif span == "days5":
        five = days[:5]
        body = "5-day forecast:\n" + "\n".join(
            f"{'Today' if i == 0 else 'Tomorrow' if i == 1 else d['weekday']}: {_day_line(d)}" for i, d in enumerate(five))
        shown["days"] = five
    elif span in ("hourly", "tonight"):
        picked = hours[::HOURLY_STEP] or hours
        rain = [h.get("rain_chance_pct") for h in hours if h.get("rain_chance_pct") is not None]
        steps = " · ".join(f"{h.get('time')} {_deg(h.get('temp_f'))}" for h in picked)
        rain_text = f" Rain up to {max(rain)}%." if rain else ""
        lead = f"Tonight: low {_deg(r.get('low_f'))}. Next hours: " if span == "tonight" else f"Next {len(hours)} hours: "
        body = lead + steps + "." + rain_text
        shown["hours"] = hours
    elif span == "next_week":
        monday = next((i for i, d in enumerate(days) if i > 0 and d.get("weekday") == "Monday"), None)
        have = days[monday:] if monday is not None else []
        body = f"I only have a forecast through {_through(days)}."
        if have:
            body += " " + " · ".join(f"{d['weekday']}: {_day_line(d)}" for d in have)
            shown["days"] = have
    elif span == "beyond":
        body = f"I only have a 7-day forecast, through {_through(days)}. There's no forecast beyond that."
    else:  # past
        body = f"I don't have past weather, only today and the next 6 days. Now: {_now(r)}"
        shown["now"] = True
    text = f"{name} — {body}"
    if req.city_note:
        text += f" That's {req.place.name}, your saved {req.place.key} place."
    if req.location_note:
        text += (f" I use your saved places, not your Mac's location: {_short_list(places)}. "
                 "Change them under Weather places in Settings; they're saved in config.json in the "
                 "Chief state folder.")
    return text, shown
