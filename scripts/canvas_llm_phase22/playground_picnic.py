#!/usr/bin/env python3
"""Canonical Playground Picnic communication helpers for Homeroom.

Newsletter section + reminder announcements reuse the existing Canvas-hosted
Final Flyer.pdf (file id 6185432). No duplicate media uploads.

See ``docs/programs/canvas-llm/canonical-context-pack/newsletter-homeroom-contract.md``
§ Playground Picnic when documented.
"""
from __future__ import annotations

CSS = (
    '<link rel="stylesheet" '
    'href="https://instructure-uploads.s3.amazonaws.com/account_111510000000000001/'
    'attachments/219636/canvas_global_app.css">'
)
JS = (
    '<script src="https://instructure-uploads.s3.amazonaws.com/'
    'account_111510000000000001/attachments/219635/canvas_global_app.js"></script>'
)

HOMEROOM_COURSE_ID = 26429
FLYER_FILE_ID = 6185432
STALE_FLYER_FILE_ID = 6185178  # deleted playground picnic.pdf — repair only
FLYER_DISPLAY_NAME = "Final Flyer.pdf"
FLYER_PREVIEW_URL = (
    f"https://thalesacademy.instructure.com/courses/{HOMEROOM_COURSE_ID}"
    f"/files/{FLYER_FILE_ID}/preview"
)

APPROVED_PICNIC_COPY = (
    "Families are invited to join us for a picnic lunch on the playground as we "
    "celebrate all of the students' hard work this track. Please bring lunch for "
    "you and your family, along with a lawn chair or blanket and your favorite "
    "outdoor game."
)

LEGACY_PICNIC_COPY_BLOCK = (
    '    <p style="margin: 10px 0 0;">Families are invited to join us on the playground '
    'for lunch together as we celebrate all of the students\' hard work this track!</p>\n'
    '    <ul style="margin: 10px 0 0; padding-left: 22px;">\n'
    '      <li>Please <strong>bring lunch for you and your family</strong></li>\n'
    '      <li>Bring a lawn chair or blanket</li>\n'
    '      <li>Bring your favorite outdoor game</li>\n'
    '    </ul>'
)

SECTION_MARKER = "Fourth Grade Playground Picnic"
PLAYFUL_NOTE = (
    "And if you happen to bring an extra cookie, nugget, or Alani for Mr. Reagan... "
    "I certainly won't complain. \U0001F604"
)

REMINDERS: tuple[dict[str, str], ...] = (
    {
        "title": "Fourth Grade Playground Picnic - Friday, September 18",
        "delayed_post_at": "2026-09-04T20:00:00Z",  # Fri Sept 4, 4:00 PM ET
        "paragraphs": [
            "Good afternoon,",
            "We are excited to invite our fourth grade families to join us for a "
            "<strong>Playground Picnic on Friday, September 18 from 12:15\u201312:50 PM</strong>.",
            "We will enjoy lunch together on the playground as we celebrate all of the "
            "students' hard work this track!",
            "<strong>Please bring lunch for you and your family</strong>, along with a lawn "
            "chair or blanket and your favorite outdoor game.",
            "And if you happen to bring an extra cookie, nugget, or Alani for Mr. Reagan... "
            "I certainly won't complain. \U0001F604",
            "Please see the Playground Picnic flyer below for the event details.",
            "__FLYER__",
            "We hope you can join us! \U0001F9FA",
            "Best,",
            "Owen Reagan",
        ],
    },
    {
        "title": "Playground Picnic Next Friday",
        "delayed_post_at": "2026-09-11T20:00:00Z",  # Fri Sept 11, 4:00 PM ET
        "paragraphs": [
            "Good afternoon,",
            "Just a reminder that our <strong>Fourth Grade Playground Picnic is next Friday, "
            "September 18 from 12:15\u201312:50 PM</strong>.",
            "Families are invited to bring lunch and join us on the playground as we "
            "celebrate all of the students' hard work this track.",
            "Please bring lunch for you and your family, a lawn chair or blanket, and your "
            "favorite outdoor game.",
            "And yes, an extra cookie, nugget, or Alani for Mr. Reagan is always welcome. \U0001F604",
            "__FLYER__",
            "We hope to see you there! \U0001F9FA",
            "Best,",
            "Owen Reagan",
        ],
    },
    {
        "title": "Playground Picnic This Friday",
        "delayed_post_at": "2026-09-16T20:00:00Z",  # Wed Sept 16, 4:00 PM ET
        "paragraphs": [
            "Good afternoon,",
            "Our <strong>Fourth Grade Playground Picnic is this Friday, September 18 from "
            "12:15\u201312:50 PM</strong> on the playground!",
            "Please remember to bring lunch for you and your family, along with a lawn "
            "chair or blanket and your favorite outdoor game.",
            "We are looking forward to celebrating a great track together!",
            "And if an extra cookie, nugget, or Alani happens to make its way to Mr. Reagan, "
            "I won't be upset. \U0001F604",
            "__FLYER__",
            "We hope you can join us! \U0001F9FA",
            "Best,",
            "Owen Reagan",
        ],
    },
)


def render_flyer_embed(*, iframe_height: str = "700px") -> str:
    """Embed the existing Canvas-hosted Playground Picnic PDF (no duplicate upload)."""
    return (
        f'<p style="margin: 14px 0 0;">'
        f'<iframe style="width: 100%; height: {iframe_height}; border: 0;" '
        f'src="{FLYER_PREVIEW_URL}" title="Playground Picnic flyer"></iframe></p>'
    )


def render_picnic_section(*, include_flyer: bool = True) -> str:
    """Render the approved Homeroom newsletter Playground Picnic section."""
    flyer = render_flyer_embed() if include_flyer else ""
    return (
        '  <div style="background: #f0fdf4; border: 1px solid #86efac; border-radius: 16px; '
        'padding: 22px; margin-bottom: 22px;">\n'
        '    <h2 style="margin: 0 0 12px; color: #15803d; font-size: 23px;">'
        '\U0001F9FA Fourth Grade Playground Picnic \u2014 Friday, September 18</h2>\n'
        '    <p style="margin: 0;"><strong>12:15\u201312:50 PM \u00b7 Playground</strong></p>\n'
        f'    <p style="margin: 10px 0 0;">{APPROVED_PICNIC_COPY}</p>\n'
        f'    <p style="margin: 10px 0 0;">{PLAYFUL_NOTE}</p>\n'
        f'{flyer}\n'
        '  </div>'
    )


def repair_flyer_references(body: str) -> str:
    """Replace stale deleted flyer id/URLs with the authoritative Final Flyer asset."""
    if str(STALE_FLYER_FILE_ID) not in body:
        return body
    return body.replace(str(STALE_FLYER_FILE_ID), str(FLYER_FILE_ID))


def repair_picnic_copy(body: str) -> str:
    """Upgrade legacy bullet-list picnic copy to the approved paragraph form."""
    if LEGACY_PICNIC_COPY_BLOCK not in body:
        return body
    approved = f'    <p style="margin: 10px 0 0;">{APPROVED_PICNIC_COPY}</p>'
    return body.replace(LEGACY_PICNIC_COPY_BLOCK, approved, 1)


def repair_picnic_content(body: str) -> str:
    """Repair flyer references and picnic copy in one pass (idempotent)."""
    body = repair_flyer_references(body)
    body = repair_picnic_copy(body)
    return body


def has_picnic_section(body: str) -> bool:
    return SECTION_MARKER in body and str(FLYER_FILE_ID) in body


def add_picnic_section(body: str) -> str:
    """Insert the picnic section after the Picture Day callout (idempotent)."""
    if has_picnic_section(body):
        return body
    anchor = (
        '    <p style="margin: 10px 0 0;"><strong>Make-Up Picture Day:</strong> '
        'Tuesday, October 20</p>\n  </div>'
    )
    if anchor not in body:
        raise ValueError("Picture Day callout anchor not found for picnic insertion")
    section = render_picnic_section()
    return body.replace(anchor, anchor + "\n\n" + section, 1)


def remove_picnic_section(body: str) -> str:
    """Remove the picnic section (for newsletters after September 18)."""
    marker = '\U0001F9FA Fourth Grade Playground Picnic'
    start = body.find(
        '  <div style="background: #f0fdf4; border: 1px solid #86efac; border-radius: 16px;'
    )
    if start < 0 or marker not in body[start : start + 400]:
        if marker not in body:
            return body
        raise ValueError("picnic section marker found but opening div anchor missing")
    # Balanced div removal
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
                end = i
                # swallow trailing blank line
                if body[end : end + 2] == "\n\n":
                    end += 2
                elif body[end : end + 1] == "\n":
                    end += 1
                return body[:start] + body[end:]
    raise ValueError("unbalanced picnic section div")


def build_reminder_message(paragraphs: list[str]) -> str:
    parts: list[str] = []
    for p in paragraphs:
        if p == "__FLYER__":
            parts.append(render_flyer_embed())
        else:
            parts.append(f"<p>{p}</p>")
    return CSS + "".join(parts) + JS


def command_self_test() -> int:
    body = "<div>" + render_picnic_section() + "</div>"
    assert has_picnic_section(body)
    assert FLYER_PREVIEW_URL in body
    assert PLAYFUL_NOTE in body
    assert "12:15\u201312:50 PM" in body

    host = (
        '  <div style="background: #fff7ed; border: 1px solid #fed7aa; border-radius: 16px; '
        'padding: 22px; margin-bottom: 22px;">\n'
        '    <p style="margin: 10px 0 0;"><strong>Make-Up Picture Day:</strong> '
        'Tuesday, October 20</p>\n  </div>\n\n'
        '  <div style="margin-bottom: 22px;"><h2>September Birthdays</h2></div>'
    )
    updated = add_picnic_section(host)
    assert has_picnic_section(updated)
    assert updated.count(SECTION_MARKER) == 1
    assert add_picnic_section(updated) == updated

    stripped = remove_picnic_section(updated)
    assert not has_picnic_section(stripped)

    msg = build_reminder_message(REMINDERS[0]["paragraphs"])
    assert FLYER_PREVIEW_URL in msg
    assert "Playground Picnic" in msg
    assert str(FLYER_FILE_ID) == "6185432"
    assert len(REMINDERS) == 3

    stale = '<iframe src="https://thalesacademy.instructure.com/courses/26429/files/6185178/preview"></iframe>'
    fixed = repair_flyer_references(stale)
    assert "6185178" not in fixed
    assert "6185432" in fixed

    sample = f"<div>\n{LEGACY_PICNIC_COPY_BLOCK}\n</div>"
    repaired = repair_picnic_copy(sample)
    assert APPROVED_PICNIC_COPY in repaired
    assert "Bring a lawn chair or blanket</li>" not in repaired

    print("PASS playground picnic self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(command_self_test())
