"""Validated Canvas Planner hash routes and loopback deep links."""
from __future__ import annotations

import re

BASE_URL = "http://127.0.0.1:4310/"
COURSES = ("math", "reading_spelling", "language_arts", "science", "history", "homeroom")
COURSE_STAGES = ("plan", "ai", "preview")

_WEEK = re.compile(r"^week/q([1-4])w([1-9][0-9]*)(?:/(.*))?$", re.IGNORECASE)


def normalize_route(route: str) -> str:
    """Return a canonical hash route or raise ``ValueError``.

    Accepted inputs are a bare route, a leading ``#``/``#/`` route, or one of
    this service's own loopback URLs. Foreign URLs and arbitrary fragments are
    rejected so the launcher cannot become a general URL opener.
    """
    value = str(route or "").strip()
    if value.startswith(BASE_URL):
        value = value[len(BASE_URL):]
    value = value.removeprefix("#").removeprefix("/")
    match = _WEEK.fullmatch(value)
    if not match:
        raise ValueError("route must be week/qNwN[/source|friday|course/(plan|ai|preview)]")
    quarter, week, tail = match.groups()
    base = f"week/q{quarter}w{week}"
    if not tail:
        return base
    parts = tail.lower().split("/")
    if parts in (["source"], ["friday"]):
        return f"{base}/{parts[0]}"
    if len(parts) == 2 and parts[0] in COURSES and parts[1] in COURSE_STAGES:
        return f"{base}/{parts[0]}/{parts[1]}"
    raise ValueError("invalid Canvas Planner stage or course")


def deep_link(week_code: str, *parts: str) -> str:
    route = "/".join(["week", week_code.lower(), *(str(p).lower() for p in parts if p)])
    return f"{BASE_URL}#{normalize_route(route)}"
