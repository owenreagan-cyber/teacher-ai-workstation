#!/usr/bin/env python3
"""Read-only Canvas connector for Canvas LLM operational readiness (fake/sandbox modes)."""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.canvas_llm_phase22 import phase22_workstation as p22  # noqa: E402

CONNECTOR_MODES = ('fake', 'sandbox')
CREDENTIAL_STATES = ('missing', 'configured', 'disabled')
SANDBOX_COURSE_ID = 26427
REDACT_PATTERNS = (
    re.compile(r'Bearer\s+\S+', re.I),
    re.compile(r'authorization:\s*\S+', re.I),
    re.compile(r'token[=:]\s*\S+', re.I),
    re.compile(r'access_token[=:]\s*\S+', re.I),
)


def compact(value: Any) -> str:
    return p22.compact(value)


def redact_log(message: str) -> str:
    redacted = message
    for pattern in REDACT_PATTERNS:
        redacted = pattern.sub('[REDACTED]', redacted)
    return redacted


@dataclass
class CanvasConnectionConfig:
    mode: str = 'fake'
    enabled: bool = True
    base_url: str | None = None
    credential_state: str = 'missing'

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def writes_allowed(self) -> bool:
        return False


@dataclass
class CanvasCourseRecord:
    course_id: int
    name: str
    course_code: str | None = None
    workflow_state: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CanvasPageRecord:
    page_id: str
    course_id: int
    title: str
    url: str | None = None
    body_html: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CanvasAssignmentRecord:
    assignment_id: str
    course_id: int
    title: str
    due_at: str | None = None
    published: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CanvasAnnouncementRecord:
    announcement_id: str
    course_id: int
    title: str
    message_html: str | None = None
    posted_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class CanvasConnector:
    """Read-only connector. Writes are permanently disabled."""

    def __init__(self, config: CanvasConnectionConfig | None = None) -> None:
        self.config = config or default_connection_config()

    def connector_available(self) -> bool:
        if not self.config.enabled:
            return False
        if self.config.mode == 'fake':
            return True
        if self.config.mode == 'sandbox':
            return self.config.credential_state == 'configured'
        return False

    def read_course(self, course_id: int) -> CanvasCourseRecord:
        if not self.connector_available():
            raise RuntimeError('connector unavailable')
        if self.config.mode == 'fake':
            return CanvasCourseRecord(
                course_id=course_id,
                name='Demo Sandbox Course',
                course_code='SANDBOX-DEMO',
                workflow_state='available',
            )
        raise RuntimeError('sandbox read requires human-authorized credentials')

    def read_page(self, course_id: int, page_url: str) -> CanvasPageRecord:
        if not self.connector_available():
            raise RuntimeError('connector unavailable')
        if self.config.mode == 'fake':
            return CanvasPageRecord(
                page_id=f'fake-page-{compact(page_url)}',
                course_id=course_id,
                title='Weekly Agenda Preview',
                url=page_url,
                body_html='<p>Fake read-only page preview.</p>',
            )
        raise RuntimeError('sandbox read requires human-authorized credentials')

    def read_assignment(self, course_id: int, assignment_id: str) -> CanvasAssignmentRecord:
        if not self.connector_available():
            raise RuntimeError('connector unavailable')
        if self.config.mode == 'fake':
            return CanvasAssignmentRecord(
                assignment_id=assignment_id,
                course_id=course_id,
                title='Fake Assignment Preview',
                due_at=None,
                published=False,
            )
        raise RuntimeError('sandbox read requires human-authorized credentials')

    def read_announcement(self, course_id: int, announcement_id: str) -> CanvasAnnouncementRecord:
        if not self.connector_available():
            raise RuntimeError('connector unavailable')
        if self.config.mode == 'fake':
            return CanvasAnnouncementRecord(
                announcement_id=announcement_id,
                course_id=course_id,
                title='Fake Announcement Preview',
                message_html='<p>Fake read-only announcement preview.</p>',
                posted_at=None,
            )
        raise RuntimeError('sandbox read requires human-authorized credentials')


def default_connection_config() -> CanvasConnectionConfig:
    return CanvasConnectionConfig(
        mode='fake',
        enabled=True,
        base_url=None,
        credential_state='missing',
    )


def sandbox_connection_config() -> CanvasConnectionConfig:
    return CanvasConnectionConfig(
        mode='sandbox',
        enabled=False,
        base_url='https://[REDACTED].instructure.com',
        credential_state='disabled',
    )


def print_connector_status_report(config: CanvasConnectionConfig | None = None) -> None:
    cfg = config or default_connection_config()
    print('Canvas Connector')
    print()
    print('Mode:')
    print(cfg.mode)
    print()
    print('Writes:')
    print('disabled')


def connector_has_no_writes() -> bool:
    source = Path(__file__).read_text().lower()
    # Ignore this helper's own pattern list when scanning for write calls.
    marker = 'def connector_has_no_writes'
    idx = source.find(marker)
    scan_source = source[:idx] if idx >= 0 else source
    forbidden = ('requests.post', 'requests.put', 'requests.delete', 'urllib.request.urlopen')
    return not any(token in scan_source for token in forbidden)


def command_status_report(_args: argparse.Namespace) -> int:
    print_connector_status_report()
    return 0


def command_self_test() -> int:
    cfg = default_connection_config()
    connector = CanvasConnector(cfg)
    assert connector.config.writes_allowed() is False
    assert connector.connector_available() is True

    course = connector.read_course(SANDBOX_COURSE_ID)
    assert course.course_id == SANDBOX_COURSE_ID
    page = connector.read_page(SANDBOX_COURSE_ID, 'weekly-agenda')
    assert page.course_id == SANDBOX_COURSE_ID
    assignment = connector.read_assignment(SANDBOX_COURSE_ID, 'assign-001')
    assert assignment.published is False
    announcement = connector.read_announcement(SANDBOX_COURSE_ID, 'ann-001')
    assert announcement.course_id == SANDBOX_COURSE_ID

    sandbox_cfg = sandbox_connection_config()
    sandbox = CanvasConnector(sandbox_cfg)
    assert sandbox.connector_available() is False

    sample = 'Authorization: Bearer secret-token-12345 token=abc'
    redacted = redact_log(sample)
    assert 'secret-token' not in redacted
    assert 'Bearer secret' not in redacted

    assert connector_has_no_writes()
    assert 'token' not in cfg.to_dict()
    print('PASS canvas connector self-test')
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Canvas LLM read-only Canvas connector')
    sub = parser.add_subparsers(dest='cmd', required=True)
    sub.add_parser('status-report').set_defaults(func=command_status_report)
    sub.add_parser('self-test').set_defaults(func=lambda _args: command_self_test())
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == '__main__':
    raise SystemExit(main())
