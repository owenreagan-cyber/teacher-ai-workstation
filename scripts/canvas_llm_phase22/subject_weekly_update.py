#!/usr/bin/env python3
"""Canonical subject Weekly Update Announcement builder (week-agnostic).

Implements the approved "one combined weekly announcement per active subject"
contract. Each active subject gets one announcement whose body is:

    greeting
    Week in Review
    Week Ahead
    schedule/agenda change (only when supported)
    transition sentence
    the EXACT current weekly agenda HTML from that course's front page
    closing

The embedded agenda is the ``kl_wrapper_3`` block extracted verbatim from the
front-page body, so the agenda shown to families is byte-identical to the agenda
on the page (no independent regeneration, no drift).

Read-only with respect to Canvas: this module only composes message strings and
classifies duplicate/drift states. It performs no network I/O and no writes.

Authority: ``docs/programs/canvas-llm/canonical-context-pack/
subject-weekly-update-announcement-contract.md``
"""
from __future__ import annotations

import argparse
from typing import Any

# Instructure-hosted FPK global assets shared by agenda pages and announcements.
CSS = (
    '<link rel="stylesheet" '
    'href="https://instructure-uploads.s3.amazonaws.com/account_111510000000000001/'
    'attachments/219636/canvas_global_app.css">'
)
JS = (
    '<script src="https://instructure-uploads.s3.amazonaws.com/'
    'account_111510000000000001/attachments/219635/canvas_global_app.js"></script>'
)

GREETING = "<p>Good afternoon,</p>"
CLOSING = "<p>Have a great weekend!</p><p>Mr. Reagan</p>"

# Canonical subject -> announcement title, transition label, and course id.
# Science is present but only announced when active (see quarter activation).
SUBJECTS: dict[str, dict[str, Any]] = {
    "math": {
        "title": "Math Canvas Weekly Update",
        "label": "Math",
        "course_id": 26404,
    },
    "reading_spelling": {
        "title": "Reading/Spelling Canvas Weekly Update",
        "label": "Reading/Spelling",
        "course_id": 26442,
    },
    "language_arts": {
        "title": "Language Arts Canvas Weekly Update",
        "label": "Language Arts",
        "course_id": 28171,
    },
    "history": {
        "title": "History Canvas Weekly Update",
        "label": "History",
        "course_id": 28165,
    },
    "science": {
        "title": "Science Canvas Weekly Update",
        "label": "Science",
        "course_id": 28166,
    },
}


def transition(subject_key: str) -> str:
    """The canonical transition sentence for a subject."""
    label = SUBJECTS[subject_key]["label"]
    return f"<p>The Canvas {label} page has been updated. Please see the upcoming week ahead.</p>"


def agenda_core(body: str) -> str:
    """Extract the ``kl_wrapper_3`` agenda block from a page/announcement body.

    The front-page body is ``CSS + kl_wrapper_3 + JS``; an announcement message is
    ``CSS + prose + kl_wrapper_3 + closing + JS``. In both cases the announcement
    must reuse exactly the ``kl_wrapper_3`` element so the embedded agenda cannot
    drift from the page. The block is extracted by balancing ``<div>`` / ``</div>``
    from the ``kl_wrapper_3`` opening tag, so trailing prose is never included.
    Returns the body unchanged when the marker is absent.
    """
    idx = body.find("kl_wrapper_3")
    if idx == -1:
        return body
    start = body.rfind("<div", 0, idx)
    if start == -1:
        return body
    depth = 0
    i = start
    n = len(body)
    while i < n:
        nxt_open = body.find("<div", i)
        nxt_close = body.find("</div>", i)
        if nxt_open == -1:
            nxt_open = n
        if nxt_close == -1:
            nxt_close = n
        if nxt_open < nxt_close:
            depth += 1
            i = nxt_open + len("<div")
        else:
            depth -= 1
            i = nxt_close + len("</div>")
            if depth == 0:
                return body[start:i]
    return body[start:]


def build_message(
    subject_key: str,
    week_in_review: str,
    week_ahead: str,
    agenda_html: str,
    schedule_change: str | None = None,
) -> str:
    """Compose the announcement message HTML for one subject.

    ``week_in_review`` / ``week_ahead`` / ``schedule_change`` are already-written
    parent-facing prose (any inline ``<strong>`` etc. is preserved verbatim).
    ``agenda_html`` is the full front-page body whose ``kl_wrapper_3`` block is
    embedded unchanged.
    """
    paragraphs = [
        GREETING,
        f"<p>{week_in_review}</p>",
        f"<p>{week_ahead}</p>",
    ]
    if schedule_change:
        paragraphs.append(f"<p>{schedule_change}</p>")
    paragraphs.append(transition(subject_key))
    prose = "".join(paragraphs)
    core = agenda_core(agenda_html)
    return CSS + prose + core + "\n" + CLOSING + JS


def find_weekly_update(
    announcements: list[dict[str, Any]],
    *,
    title: str,
    week_marker: str,
) -> list[dict[str, Any]]:
    """Return live announcements that represent the same subject+week update.

    ``week_marker`` is a substring unique to this week's agenda banner (e.g.
    ``"August 31\u2013September 4, 2026"``). A match is the canonical title OR the
    week marker appearing in the title/message.
    """
    title = (title or "").strip()
    week_marker = (week_marker or "").strip()
    matches: list[dict[str, Any]] = []
    for a in announcements:
        t = (a.get("title") or "").strip()
        m = a.get("message") or ""
        if (title and t == title) or (week_marker and (week_marker in t or week_marker in m)):
            matches.append(a)
    return matches


def classify_duplicate(
    announcements: list[dict[str, Any]],
    *,
    title: str,
    week_marker: str,
    expected_core: str | None = None,
) -> tuple[str, Any]:
    """Classify duplicate/drift state against a fresh announcement list.

    Returns ``(status, match_id)`` where status is one of:

    - ``ABSENT``         — no same-week update exists; safe to CREATE.
    - ``ALREADY_APPLIED``— an identical/correct same-week update exists.
    - ``DRIFT``          — a same-week update exists but its embedded agenda
                           differs from ``expected_core`` (surface for review,
                           do not create another).
    """
    found = find_weekly_update(announcements, title=title, week_marker=week_marker)
    if not found:
        return "ABSENT", None
    if len(found) > 1:
        return "DRIFT", [a.get("id") for a in found]
    match = found[0]
    if expected_core is not None and agenda_core(match.get("message") or "") != expected_core:
        return "DRIFT", match.get("id")
    return "ALREADY_APPLIED", match.get("id")


def command_self_test(_args: argparse.Namespace) -> int:
    fake_body = (
        CSS
        + "\n"
        + '<div id="kl_wrapper_3" class="kl_circle_left kl_wrapper" style="border-style: none;">'
        + "\n"
        + '<div id="kl_banner"><p>Quarter 1, Week 7 | August 31\u2013September 4, 2026</p></div>'
        + "\n"
        + "</div>"
        + "\n"
        + JS
    )
    core = agenda_core(fake_body)
    assert core.startswith('<div id="kl_wrapper_3"'), core
    assert "August 31\u2013September 4, 2026" in core
    assert "canvas_global_app.css" not in core
    assert "canvas_global_app.js" not in core

    msg = build_message(
        "math",
        "We had a great week in Math!",
        "Next week, we will continue with Lessons 21\u201325.",
        fake_body,
        schedule_change=None,
    )
    assert msg.startswith(CSS), "message must open with the global CSS"
    assert GREETING in msg
    assert "We had a great week in Math!" in msg
    assert "Next week, we will continue with Lessons 21\u201325." in msg
    assert "The Canvas Math page has been updated. Please see the upcoming week ahead." in msg
    assert core in msg, "embedded agenda must be byte-identical to the front-page core"
    assert CLOSING in msg
    assert msg.endswith(JS), "message must close with the global JS"

    anns: list[dict[str, Any]] = []
    assert classify_duplicate(anns, title="Math Canvas Weekly Update",
                              week_marker="August 31\u2013September 4, 2026",
                              expected_core=core) == ("ABSENT", None)

    same = [{"id": 1, "title": "Math Canvas Weekly Update", "message": CSS + core + JS}]
    assert classify_duplicate(same, title="Math Canvas Weekly Update",
                              week_marker="August 31\u2013September 4, 2026",
                              expected_core=core) == ("ALREADY_APPLIED", 1)

    drifted = [{"id": 2, "title": "Math Canvas Weekly Update",
                "message": CSS + '<div id="kl_wrapper_3"><p>old agenda</p></div>' + JS}]
    assert classify_duplicate(drifted, title="Math Canvas Weekly Update",
                              week_marker="August 31\u2013September 4, 2026",
                              expected_core=core) == ("DRIFT", 2)

    # History schedule-change prose composes in order (change before transition).
    hist = build_message(
        "history",
        "We had a great week in History!",
        "Next week, we will wrap up our World Mountains unit.",
        fake_body,
        schedule_change="One schedule change to note: the test was moved.",
    )
    assert hist.index("One schedule change to note") < hist.index("The Canvas History page has been updated")

    print("PASS subject weekly update self-test")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Subject Weekly Update Announcement builder")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("self-test").set_defaults(func=command_self_test)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
