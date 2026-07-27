#!/usr/bin/env python3
"""Canvas course routing resolver for Q1W2 live deployment."""
from __future__ import annotations

import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.canvas_llm_phase22 import canvas_connection as connection  # noqa: E402
from scripts.canvas_llm_phase22 import phase22_workstation as p22  # noqa: E402

MANUAL_SUBJECTS = ('ELA4', 'HIST4', 'SCI4')


def compact(value: Any) -> str:
    return p22.compact(value)


@dataclass
class CourseRoute:
    subject: str
    course_id: int
    prefix: str
    allowed: bool
    status: str = 'ACTIVE'

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


ROUTES = {
    'math': CourseRoute('math', connection.MATH_COURSE_ID, 'SM5', True),
    'reading': CourseRoute('reading', connection.READING_COURSE_ID, 'RM4', True),
    'spelling': CourseRoute('spelling', connection.READING_COURSE_ID, 'RM4', True),
    'homeroom': CourseRoute('homeroom', connection.HOMEROOM_COURSE_ID, '', True),
    'language-arts': CourseRoute('language-arts', connection.ELA_COURSE_ID, 'ELA4', False, 'MANUAL'),
    'history': CourseRoute('history', connection.HISTORY_COURSE_ID, 'HIST4', False, 'MANUAL'),
    'science': CourseRoute('science', connection.SCIENCE_COURSE_ID, 'SCI4', False, 'MANUAL'),
}


def resolve_route(subject: str, assignment_type: str = 'lesson') -> CourseRoute:
    key = compact(subject).lower()
    if key not in ROUTES:
        raise KeyError(f'unknown subject route: {subject}')
    return ROUTES[key]


def print_routing_status_report() -> None:
    print('Canvas Course Routing')
    print()
    for subject in ('math', 'reading', 'homeroom', 'language-arts', 'history', 'science'):
        route = resolve_route(subject)
        print(f'{subject}: {route.course_id} ({route.prefix or "n/a"}) — {route.status}')
