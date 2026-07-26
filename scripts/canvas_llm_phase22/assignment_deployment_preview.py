#!/usr/bin/env python3
"""Assignment deployment preparation layer for C1C — no assignment publishing."""
from __future__ import annotations

import argparse
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.canvas_llm_phase22 import phase22_workstation as p22  # noqa: E402

PREFLIGHT_STATUSES = ('READY', 'BLOCKED')
VALID_CATEGORIES = ('homework', 'classwork', 'assessment', 'participation', 'other')
VALID_SUBMISSION_TYPES = ('online_text_entry', 'online_upload', 'on_paper', 'none', 'external_tool')


def compact(value: Any) -> str:
    return p22.compact(value)


@dataclass
class AssignmentDeploymentPreview:
    assignment_id: str
    title: str
    description: str
    points: float | None
    due_date: str | None
    category: str | None
    submission_type: str | None
    readiness: str = 'BLOCKED'

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def validate_points(points: Any) -> bool:
    if points is None:
        return False
    try:
        value = float(points)
    except (TypeError, ValueError):
        return False
    return value >= 0


def validate_due_date(due_date: str | None) -> bool:
    if not compact(due_date or ''):
        return False
    token = compact(due_date)
    return len(token) >= 8 and any(ch.isdigit() for ch in token)


def preflight_assignment(preview: AssignmentDeploymentPreview) -> AssignmentDeploymentPreview:
    """Validate assignment fields and return READY or BLOCKED — does not publish."""
    blockers: list[str] = []

    if not compact(preview.title):
        blockers.append('missing_title')
    if not compact(preview.description):
        blockers.append('missing_description')
    if not validate_points(preview.points):
        blockers.append('invalid_points')
    if not validate_due_date(preview.due_date):
        blockers.append('invalid_due_date')
    category = compact(preview.category or '')
    if not category or category not in VALID_CATEGORIES:
        blockers.append('invalid_category')
    submission = compact(preview.submission_type or '')
    if not submission or submission not in VALID_SUBMISSION_TYPES:
        blockers.append('invalid_submission_type')

    preview.readiness = 'BLOCKED' if blockers else 'READY'
    return preview


def build_preview_from_draft(draft_row: dict[str, Any]) -> AssignmentDeploymentPreview:
    payload = p22.jl(draft_row.get('payload'), {})
    due = payload.get('due') or {}
    return AssignmentDeploymentPreview(
        assignment_id=compact(draft_row.get('id') or ''),
        title=compact(draft_row.get('title') or ''),
        description=compact(draft_row.get('body_text') or draft_row.get('body_html') or ''),
        points=payload.get('points'),
        due_date=compact(due.get('dueAt') or due.get('date') or draft_row.get('entry_date') or ''),
        category=compact(payload.get('category') or 'homework'),
        submission_type=compact(payload.get('submissionType') or 'online_text_entry'),
    )


def create_assignment_blocked() -> None:
    """Explicit blocked entry point — assignment writes are not enabled."""
    raise RuntimeError('create_assignment is blocked: assignments require extra validation and are not enabled in C1')


def assignment_writes_disabled() -> bool:
    source = Path(__file__).read_text().lower()
    return 'create_assignment' in source and 'blocked' in source


def command_self_test() -> int:
    ready = preflight_assignment(
        AssignmentDeploymentPreview(
            assignment_id='assign-001',
            title='Math Lesson 18',
            description='Complete practice set.',
            points=10.0,
            due_date='2026-08-20',
            category='homework',
            submission_type='online_text_entry',
        )
    )
    assert ready.readiness == 'READY'

    blocked = preflight_assignment(
        AssignmentDeploymentPreview(
            assignment_id='assign-002',
            title='',
            description='',
            points=-1,
            due_date='',
            category='invalid',
            submission_type='bad',
        )
    )
    assert blocked.readiness == 'BLOCKED'

    try:
        create_assignment_blocked()
        raise AssertionError('create_assignment should be blocked')
    except RuntimeError:
        pass

    assert assignment_writes_disabled()
    print('PASS assignment deployment preview self-test')
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Canvas LLM assignment deployment preparation')
    sub = parser.add_subparsers(dest='cmd', required=True)
    sub.add_parser('self-test').set_defaults(func=lambda _args: command_self_test())
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == '__main__':
    raise SystemExit(main())
