#!/usr/bin/env python3
"""Canonical Homeroom newsletter birthday-section builder.

Implements the approved "one birthday student = one birthday tile" standard for
the rolling Homeroom newsletter. Pure generation + targeted replacement; no
Canvas I/O and no writes.

Rules (see ``docs/programs/canvas-llm/canonical-context-pack/
newsletter-homeroom-contract.md`` § Birthday tiles):

- one individual birthday tile per student;
- first name only unless Owen explicitly says otherwise;
- the exact known birthday date;
- a soft rotating color palette so each tile can carry a different light tint;
- strong text contrast, current polished family-newsletter style;
- responsive ``display:flex; flex-wrap:wrap`` layout;
- omit the entire birthday section when no birthdays are supplied for a period;
- never invent birthdays (callers must pass an explicit ``students`` list).
"""
from __future__ import annotations

from typing import Iterable

# Soft rotating treatments: (background, border, name accent, emoji).
# The first three match Owen's approved September 2026 pattern verbatim.
TILE_TREATMENTS: tuple[tuple[str, str, str, str], ...] = (
    ("#fff0f5", "#f4b6cf", "#c51062", "\U0001F382\U0001F389"),  # pink  🎂🎉
    ("#eef7ff", "#a9d2ef", "#0065a7", "\U0001F388\U0001F382"),  # blue  🎈🎂
    ("#fff6e8", "#f4cf96", "#b65a00", "\U0001F389\U0001F388"),  # amber 🎉🎈
    ("#ecfdf5", "#a7e3c8", "#0f7b5f", "\U0001F381\U0001F382"),  # green 🎁🎂
    ("#f5f3ff", "#c4b5fd", "#6d28d9", "\U0001F38a\U0001F388"),  # violet 🎊🎈
    ("#f0f9ff", "#bae6fd", "#0369a1", "\U0001F382\U0001F388"),  # sky   🎂🎈
)

DEFAULT_HEADING_COLOR = "#a21caf"


def render_birthday_tile(first_name: str, date: str, treatment_index: int) -> str:
    """Render one student tile with the treatment at ``treatment_index`` (rotates)."""
    bg, border, accent, emoji = TILE_TREATMENTS[treatment_index % len(TILE_TREATMENTS)]
    return (
        f'<div style="flex: 1 1 30%; min-width: 220px; background-color: {bg}; '
        f'border: 1px solid {border}; border-radius: 18px; padding: 24px; '
        f'text-align: center;">'
        f'<div style="font-size: 32px; margin-bottom: 8px;">{emoji}</div>'
        f'<div style="font-size: 22px; font-weight: bold; color: {accent};">{first_name}</div>'
        f'<div style="font-size: 18px; color: #333333; margin-top: 6px;">{date}</div>'
        f'</div>'
    )


def render_birthday_section(
    month_label: str,
    students: Iterable[tuple[str, str]],
    *,
    heading_color: str = DEFAULT_HEADING_COLOR,
) -> str:
    """Render the full birthday section (header + tile container).

    ``students`` is an ordered iterable of ``(first_name, date)``. Returns an
    empty string when there are no birthdays for the period (section omitted).
    """
    students = list(students)
    if not students:
        return ""
    tiles = "".join(
        render_birthday_tile(first_name, date, i)
        for i, (first_name, date) in enumerate(students)
    )
    header = (
        f'<h2 style="margin: 0 0 16px; color: {heading_color}; font-size: 23px;">'
        f'\U0001F382 {month_label} Birthdays \U0001F389</h2>'
    )
    container = (
        f'<div style="display: flex; gap: 18px; flex-wrap: wrap;">{tiles}</div>'
    )
    return f'<div style="margin-bottom: 22px;">\n    {header}\n    {container}\n  </div>'


def _balanced_div_end(body: str, start: int) -> int:
    """Return the index just past the matching ``</div>`` for the ``<div`` at ``start``."""
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
                return i
    return n


def replace_birthday_section(
    body: str,
    month_label: str,
    students: Iterable[tuple[str, str]],
    *,
    heading_color: str = DEFAULT_HEADING_COLOR,
) -> str:
    """Replace the existing single-card birthday section with the tile layout.

    Anchors on the ``"{month_label} Birthdays"`` heading, walks back to the
    enclosing flex container, removes it via balanced ``<div>`` matching, and
    substitutes the canonical tile section. The old "Happy Birthday to ..."
    sentence is dropped — the tiles carry the names and dates themselves.
    Raises ``ValueError`` if the anchors are not found (caller must reconcile).
    """
    heading = f"{month_label} Birthdays"
    heading_idx = body.find(heading)
    if heading_idx < 0:
        raise ValueError(f"birthday heading {heading!r} not found")
    card_idx = body.rfind('<div style="flex: 1 1 260px', 0, heading_idx)
    container_idx = body.rfind(
        '<div style="display: flex; flex-wrap: wrap; gap: 14px;', 0,
        card_idx if card_idx > 0 else heading_idx,
    )
    if container_idx < 0:
        raise ValueError("birthday flex container not found")
    end = _balanced_div_end(body, container_idx)
    new_section = render_birthday_section(month_label, students, heading_color=heading_color)
    return body[:container_idx] + new_section + body[end:]


def command_self_test() -> int:
    students = [("Ava", "September 4"), ("Timothy", "September 16"), ("Charlotte", "September 17")]

    section = render_birthday_section("September", students)
    assert "Ava" in section and "Timothy" in section and "Charlotte" in section
    assert "September 4" in section and "September 16" in section and "September 17" in section
    assert "flex-wrap: wrap" in section
    assert "Happy Birthday to" not in section
    assert section.count("min-width: 220px") == 3

    # Distinct rotating tints for the first three tiles.
    assert "#fff0f5" in section and "#eef7ff" in section and "#fff6e8" in section
    assert "#c51062" in section and "#0065a7" in section and "#b65a00" in section

    # Empty students -> omit the section entirely.
    assert render_birthday_section("September", []) == ""

    # Replacement drops the sentence card and swaps in tiles.
    old = (
        '  <div style="display: flex; flex-wrap: wrap; gap: 14px; margin-bottom: 22px;">\n'
        '    <div style="flex: 1 1 260px; background: linear-gradient(90deg, #fdf2f8, #faf5ff); border: 1px solid #f5d0fe; border-radius: 16px; padding: 22px; text-align: center;">\n'
        '        <div style="font-size: 34px;">\U0001F382 \U0001F389</div>\n'
        '        <h2 style="margin: 5px 0 12px; color: #a21caf; font-size: 23px;">September Birthdays</h2>\n'
        '        <p style="margin: 0; font-size: 17px;"><strong>Happy Birthday to Ava on September 4, Timothy on September 16, and Charlotte on September 17!</strong></p>\n'
        '    </div>\n'
        '</div>\n'
    )
    new = replace_birthday_section(old, "September", students)
    assert "Happy Birthday to" not in new
    assert "September Birthdays" in new
    assert new.count("min-width: 220px") == 3

    print("PASS homeroom birthday tiles self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(command_self_test())
