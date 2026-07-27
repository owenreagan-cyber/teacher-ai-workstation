#!/usr/bin/env python3
"""Thales-style Canvas HTML renderer for Q1W2 weekly agenda pages."""
from __future__ import annotations

import html
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.canvas_llm_phase22 import phase22_workstation as p22  # noqa: E402

BLUE = p22.BLUE
MAGENTA = p22.MAGENTA
DGRAY = p22.DGRAY
WHITE = p22.WHITE
DAY_BLOCK_IDS = p22.DAY_BLOCK_IDS
WEEKDAYS = p22.WEEKDAYS

Q1W2_WEEK_CODE = 'Q1W2'
Q1W2_PAGE_TITLE = 'Q1W2 Weekly Agenda'
Q1W2_SUBTITLE = 'Quarter 1, Week 2 | July 27-31, 2026'

Q1W2_DAYS: tuple[dict[str, object], ...] = (
    {
        'name': 'Monday',
        'in_class': ('Math: SM5: Lesson 2', 'Reading: RM4: Lesson 2', 'ELA: Chapter 1, Lesson 3', 'History: The American Revolution Chapter 8'),
        'at_home': ('SM5: Lesson 2 — #12-30 Even', 'RM4: Lesson 2 — Workbook and comprehension'),
    },
    {
        'name': 'Tuesday',
        'in_class': ('Math: SM5: Lesson 3', 'Reading: RM4: Lesson 3', 'Spelling: Spelling Practice'),
        'at_home': ('RM4: Lesson 3 — Workbook and comprehension',),
    },
    {
        'name': 'Wednesday',
        'in_class': ('Math: SM5: Lesson 4', 'Reading: RM4: Lesson 4', 'Science: Lesson 4'),
        'at_home': ('SM5: Lesson 4 — #11-29 Odds',),
    },
    {
        'name': 'Thursday',
        'in_class': ('Math: SM5: Lesson 5', 'Reading: RM4: Lesson 5', 'ELA: Chapter 1, Lesson 4'),
        'at_home': ('RM4: Lesson 5 — Workbook practice',),
    },
    {
        'name': 'Friday',
        'in_class': ('Spelling: RM4: Spelling Test 5', 'Reading: RM4: Lesson 5 review', 'Math: SM5: Lesson 5 review'),
        'at_home': ('Study for next week',),
    },
)


def render_q1w2_weekly_agenda_html() -> str:
    reminders = '<ul><li>Study for Friday\'s spelling test!</li></ul>'
    parts = [
        f'<div id="kl_wrapper_3" class="kl_circle_left kl_wrapper" style="border-style: none;">'
        f'<div id="kl_banner" class="">'
        f'<p style="color: {WHITE}; background-color: {BLUE}; text-align: center; margin: 0;">'
        f'<span style="font-size: 18pt;">&nbsp;Weekly Agenda</span><br>'
        f'<span style="font-size: 10pt;">{html.escape(Q1W2_SUBTITLE)}</span></p>'
        f'<h3 style="background-color: {MAGENTA}; color: {WHITE}; border: 0 !important;">Reminders &amp; Resources</h3>'
        f'<div style="width: 100%; padding-left: 15px;">{reminders}</div>',
    ]
    for idx, day in enumerate(Q1W2_DAYS):
        in_class = ''.join(f'<li>{html.escape(str(item))}</li>' for item in day['in_class'])
        at_home = ''.join(f'<li>{html.escape(str(item))}</li>' for item in day['at_home'])
        parts.append(
            f'<div id="{DAY_BLOCK_IDS[idx]}" class="">'
            f'<h3 style="color: {WHITE}; background-color: {BLUE}; margin-top: 15px; margin-bottom: 2px; border: 0 !important;">{day["name"]}</h3>'
            f'<div style="display: flex; width: 100%;">'
            f'<div style="width: 49%; padding-left: 15px;">'
            f'<h4 class="kl_solid_border" style="color: {WHITE}; background-color: {DGRAY}; padding-left: 10px; margin: 0; border: 0 !important;">In Class</h4>'
            f'<ul>{in_class}</ul></div>'
            f'<div style="width: 49%; padding-left: 15px;">'
            f'<h4 class="kl_solid_border" style="color: {WHITE}; background-color: {DGRAY}; padding-left: 10px; margin: 0; border: 0 !important;">At Home</h4>'
            f'<ul>{at_home}</ul></div></div></div>',
        )
    parts.append('</div></div>')
    body = ''.join(parts)
    assert 'Homework: None' not in body
    assert 'No Homework' not in body
    return body


def build_spelling_announcement_draft() -> dict[str, object]:
    body = (
        'Good morning, families!\n\n'
        'Our RM4: Spelling Test 5 is this Friday, July 31, 2026.\n\n'
        'Please review this week\'s spelling patterns before the assessment.\n\n'
        'Have a great week!\n\n'
        'Mr. Reagan'
    )
    return {
        'title': 'RM4: Spelling Test 5',
        'body': body,
        'preview_only': True,
        'published': False,
        'canvas_writes_allowed': False,
    }
