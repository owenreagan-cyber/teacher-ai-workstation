#!/usr/bin/env python3
"""Communication readiness status — announcements, daily brief, morning email (status only)."""
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

COMMUNICATION_STATES = ('READY', 'PLANNED', 'DISABLED')

REQUIRED_ANNOUNCEMENT_ELEMENTS = (
    'greeting',
    'assessment_information',
    'friendly_closing',
)

BLOCKED_ANNOUNCEMENT_CONTENT = (
    'study guide',
    'practice word list',
    'answer key',
    'extra homework instructions',
)

SAMPLE_ANNOUNCEMENT = {
    'greeting': 'Good morning, families!',
    'assessment_information': 'Friday spelling test covers List 5 words.',
    'friendly_closing': 'Have a great week!',
    'body': (
        'Good morning, families!\n\n'
        'Friday spelling test covers List 5 words.\n\n'
        'Have a great week!'
    ),
}


def compact(value: Any) -> str:
    return p22.compact(value)


@dataclass
class CommunicationChannel:
    name: str
    state: str
    detail: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CommunicationStatusReport:
    canvas_announcements: CommunicationChannel
    daily_teacher_brief: CommunicationChannel
    morning_email: CommunicationChannel
    automatic_sending: CommunicationChannel
    template_validation: str = 'PASS'
    blocked_content_detected: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            'canvas_announcements': self.canvas_announcements.to_dict(),
            'daily_teacher_brief': self.daily_teacher_brief.to_dict(),
            'morning_email': self.morning_email.to_dict(),
            'automatic_sending': self.automatic_sending.to_dict(),
            'template_validation': self.template_validation,
            'blocked_content_detected': self.blocked_content_detected,
        }


def validate_announcement_template(payload: dict[str, Any]) -> tuple[bool, list[str]]:
    issues: list[str] = []
    body_blob = compact(payload.get('body') or '').lower()
    for element in REQUIRED_ANNOUNCEMENT_ELEMENTS:
        if element == 'greeting' and not compact(payload.get('greeting') or ''):
            issues.append('missing greeting')
        elif element == 'assessment_information' and 'assessment' not in body_blob and 'test' not in body_blob and 'spelling' not in body_blob:
            issues.append('missing assessment information')
        elif element == 'friendly_closing' and not compact(payload.get('friendly_closing') or ''):
            issues.append('missing friendly closing')
    for blocked in BLOCKED_ANNOUNCEMENT_CONTENT:
        if blocked in body_blob:
            issues.append(f'blocked content: {blocked}')
    return not issues, issues


def build_communication_status() -> CommunicationStatusReport:
    valid, _issues = validate_announcement_template(SAMPLE_ANNOUNCEMENT)
    return CommunicationStatusReport(
        canvas_announcements=CommunicationChannel(
            name='Canvas Announcements',
            state='READY',
            detail='Draft generation and template validation available; automatic publishing disabled.',
        ),
        daily_teacher_brief=CommunicationChannel(
            name='Daily Teacher Brief',
            state='READY',
            detail='Local preview generation available; no email transport.',
        ),
        morning_email=CommunicationChannel(
            name='Morning Email',
            state='PLANNED',
            detail='Status tracking only; morning email integration not activated.',
        ),
        automatic_sending=CommunicationChannel(
            name='Automatic Sending',
            state='DISABLED',
            detail='No automatic announcement publishing or email sending.',
        ),
        template_validation='PASS' if valid else 'FAIL',
        blocked_content_detected=False,
    )


def scan_for_blocked_content(text: str) -> list[str]:
    blob = compact(text).lower()
    found: list[str] = []
    for token in BLOCKED_ANNOUNCEMENT_CONTENT:
        if token in blob:
            found.append(token)
    return found


def communication_has_no_sends() -> bool:
    source = Path(__file__).read_text().lower()
    marker = 'def communication_has_no_sends'
    idx = source.find(marker)
    scan_source = source[:idx] if idx >= 0 else source
    forbidden = (
        'gmail',
        'smtp',
        'send_email',
        'requests.post',
        'canvas.instructure',
        'publish_announcement',
        'auto_publish',
    )
    return not any(token in scan_source for token in forbidden)


def print_communication_status_report() -> None:
    report = build_communication_status()
    print('Communication System')
    print()
    print('Canvas Announcements:')
    print(report.canvas_announcements.state)
    print()
    print('Daily Teacher Brief:')
    print(report.daily_teacher_brief.state)
    print()
    print('Morning Email:')
    print(report.morning_email.state)
    print()
    print('Automatic Sending:')
    print(report.automatic_sending.state)


def command_status_report(_args: argparse.Namespace) -> int:
    print_communication_status_report()
    return 0


def command_self_test() -> int:
    report = build_communication_status()
    assert report.canvas_announcements.state == 'READY'
    assert report.daily_teacher_brief.state == 'READY'
    assert report.morning_email.state == 'PLANNED'
    assert report.automatic_sending.state == 'DISABLED'
    assert report.template_validation == 'PASS'

    valid, issues = validate_announcement_template(SAMPLE_ANNOUNCEMENT)
    assert valid is True
    assert not issues

    blocked_body = 'Here is the study guide and answer key for homework.'
    blocked, blocked_issues = validate_announcement_template({'body': blocked_body})
    assert blocked is False
    assert any('study guide' in item for item in blocked_issues)

    assert scan_for_blocked_content('Practice word list attached') == ['practice word list']
    assert communication_has_no_sends()
    print('PASS communication status self-test')
    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Communication readiness status')
    sub = parser.add_subparsers(dest='cmd', required=True)
    sub.add_parser('status-report').set_defaults(func=command_status_report)
    sub.add_parser('self-test').set_defaults(func=lambda _args: command_self_test())
    args = parser.parse_args()
    raise SystemExit(args.func(args))
