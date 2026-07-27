#!/usr/bin/env python3
"""Canvas connection status — authentication and mapping validation without exposing secrets."""
from __future__ import annotations

import argparse
import os
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.canvas_llm_phase22 import canvas_connector as connector  # noqa: E402
from scripts.canvas_llm_phase22 import phase22_workstation as p22  # noqa: E402

HOMEROOM_COURSE_ID = 26427
MATH_COURSE_ID = 26404
READING_COURSE_ID = 26442
ELA_COURSE_ID = 26495
HISTORY_COURSE_ID = 26493
SCIENCE_COURSE_ID = 26496

COURSE_MAP = {
    'homeroom': HOMEROOM_COURSE_ID,
    'math': MATH_COURSE_ID,
    'reading': READING_COURSE_ID,
    'language-arts': ELA_COURSE_ID,
    'history': HISTORY_COURSE_ID,
    'science': SCIENCE_COURSE_ID,
}


def compact(value: Any) -> str:
    return p22.compact(value)


@dataclass
class CanvasConnectionStatus:
    authentication: str
    course_mapping: str
    reads: str
    writes: str
    environment: str
    mode: str
    blockers: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def ready_for_live(self) -> bool:
        return (
            self.authentication == 'PASS'
            and self.course_mapping == 'PASS'
            and self.reads == 'ENABLED'
            and self.writes == 'CONTROLLED'
        )


def _deployment_mode() -> str:
    return compact(os.environ.get('CANVAS_LLM_DEPLOYMENT_MODE') or 'controlled').lower()


def _token_configured() -> bool:
    return bool(compact(os.environ.get('CANVAS_TOKEN') or os.environ.get('CANVAS_API_TOKEN') or ''))


def _base_url_configured() -> bool:
    return bool(compact(os.environ.get('CANVAS_BASE_URL') or ''))


def _live_approved() -> bool:
    return compact(os.environ.get('CANVAS_LLM_LIVE_Q1W2_APPROVED') or '').lower() in {'1', 'true', 'yes'}


def load_canvas_environment() -> dict[str, str]:
    mode = _deployment_mode()
    if mode == 'live':
        mode_label = 'live'
    else:
        mode_label = compact(os.environ.get('CANVAS_LLM_MODE') or 'controlled_live')
    return {
        'mode': mode_label,
        'base_url': '[REDACTED]' if _base_url_configured() else 'missing',
        'approval': 'approved' if _live_approved() else 'pending',
    }


def controlled_live_connection_config() -> connector.CanvasConnectionConfig:
    return connector.CanvasConnectionConfig(
        mode='controlled_live',
        enabled=True,
        base_url='https://[REDACTED].instructure.com' if _token_configured() else None,
        credential_state='configured' if _token_configured() else 'missing',
        write_mode='controlled',
    )


def validate_course_mapping() -> tuple[str, list[str]]:
    blockers: list[str] = []
    expected = {
        'homeroom': HOMEROOM_COURSE_ID,
        'math': MATH_COURSE_ID,
        'reading': READING_COURSE_ID,
    }
    for subject, course_id in expected.items():
        if COURSE_MAP.get(subject) != course_id:
            blockers.append(f'mapping:{subject}')
    return ('PASS' if not blockers else 'FAIL'), blockers


def build_connection_status(*, test_mode: bool = False) -> CanvasConnectionStatus:
    blockers: list[str] = []
    env = load_canvas_environment()
    live_mode = _deployment_mode() == 'live'

    if live_mode and not test_mode and not _live_approved():
        authentication = 'FAIL'
        blockers.append('live_deployment_not_approved')
    elif test_mode or (_live_approved() and _token_configured() and (not live_mode or _base_url_configured())):
        authentication = 'PASS'
    elif _live_approved() and not _token_configured():
        authentication = 'FAIL'
        blockers.append('missing_canvas_token')
    elif live_mode and not _base_url_configured():
        authentication = 'FAIL'
        blockers.append('missing_canvas_base_url')
    else:
        authentication = 'FAIL'
        blockers.append('live_deployment_not_approved')

    mapping_status, mapping_blockers = validate_course_mapping()
    blockers.extend(mapping_blockers)

    writes = 'CONTROLLED' if authentication == 'PASS' and mapping_status == 'PASS' else 'BLOCKED'
    environment = 'Production Canvas'
    if live_mode:
        environment = 'LIVE' if authentication == 'PASS' else 'Blocked'
    elif authentication != 'PASS':
        environment = 'Blocked'
    return CanvasConnectionStatus(
        authentication=authentication,
        course_mapping=mapping_status,
        reads='ENABLED' if authentication == 'PASS' else 'DISABLED',
        writes=writes,
        environment=environment,
        mode=env['mode'],
        blockers=blockers,
    )


def test_authentication(*, test_mode: bool = False) -> bool:
    return build_connection_status(test_mode=test_mode).authentication == 'PASS'


def print_connection_status_report(*, test_mode: bool = False) -> None:
    status = build_connection_status(test_mode=test_mode)
    print('Canvas Connection')
    print()
    print('Authentication:')
    print(status.authentication)
    print()
    print('Course Mapping:')
    print(status.course_mapping)
    print()
    print('Reads:')
    print(status.reads)
    print()
    print('Writes:')
    print(status.writes)


def connection_has_no_network_writes() -> bool:
    source = Path(__file__).read_text().lower()
    marker = 'def connection_has_no_network_writes'
    idx = source.find(marker)
    scan_source = source[:idx] if idx >= 0 else source
    forbidden = ('requests.post', 'requests.put', 'requests.delete', 'urllib.request', 'httpx')
    return not any(token in scan_source for token in forbidden)


def command_status_report(_args: argparse.Namespace) -> int:
    test_mode = compact(os.environ.get('CANVAS_LLM_CONNECTION_TEST_MODE') or '').lower() in {'1', 'true', 'yes'}
    print_connection_status_report(test_mode=test_mode)
    return 0 if build_connection_status(test_mode=test_mode).ready_for_live or test_mode else 1


def command_self_test() -> int:
    status = build_connection_status(test_mode=True)
    assert status.authentication == 'PASS'
    assert status.course_mapping == 'PASS'
    assert status.reads == 'ENABLED'
    assert status.writes == 'CONTROLLED'
    mapping_status, blockers = validate_course_mapping()
    assert mapping_status == 'PASS'
    assert not blockers
    assert connection_has_no_network_writes()
    print('PASS canvas connection self-test')
    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Canvas connection status')
    sub = parser.add_subparsers(dest='cmd', required=True)
    sub.add_parser('status-report').set_defaults(func=command_status_report)
    sub.add_parser('self-test').set_defaults(func=lambda _args: command_self_test())
    args = parser.parse_args()
    raise SystemExit(args.func(args))
