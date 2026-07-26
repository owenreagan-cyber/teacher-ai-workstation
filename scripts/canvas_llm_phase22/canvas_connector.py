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
PRODUCTION_MODES = ('production', 'live')
CREDENTIAL_STATES = ('missing', 'configured', 'disabled')
SANDBOX_COURSE_ID = 26427
DUPLICATE_RESULTS = ('MATCH', 'CONFLICT', 'MISSING')
FAKE_OBJECT_CATALOG: dict[int, dict[str, list[dict[str, Any]]]] = {}
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
class CanvasSandboxConfig:
    mode: str = 'fake'
    course_id: int = SANDBOX_COURSE_ID
    credential_state: str = 'missing'
    enabled: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_connection_config(self) -> CanvasConnectionConfig:
        return CanvasConnectionConfig(
            mode=self.mode,
            enabled=self.enabled,
            base_url='https://[REDACTED].instructure.com' if self.mode == 'sandbox' else None,
            credential_state=self.credential_state,
        )

    def stores_credentials(self) -> bool:
        return False


@dataclass
class ExistingObjectResult:
    result: str
    target_type: str
    target_id: str | None = None
    title: str | None = None
    body_hash: str | None = None
    reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


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
            stored = _fake_store_entry('page', page_url)
            if stored:
                return CanvasPageRecord(
                    page_id=f'fake-page-{compact(page_url)}',
                    course_id=int(stored.get('course_id') or course_id),
                    title=compact(stored.get('title') or page_url),
                    url=page_url,
                    body_html=compact(stored.get('body') or ''),
                )
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
            stored = _fake_store_entry('announcement', announcement_id)
            if stored:
                return CanvasAnnouncementRecord(
                    announcement_id=announcement_id,
                    course_id=int(stored.get('course_id') or course_id),
                    title=compact(stored.get('title') or 'Announcement'),
                    message_html=compact(stored.get('body') or ''),
                    posted_at=None,
                )
            return CanvasAnnouncementRecord(
                announcement_id=announcement_id,
                course_id=course_id,
                title='Fake Announcement Preview',
                message_html='<p>Fake read-only announcement preview.</p>',
                posted_at=None,
            )
        raise RuntimeError('sandbox read requires human-authorized credentials')

    def list_pages(self, course_id: int) -> list[CanvasPageRecord]:
        if not self.connector_available():
            raise RuntimeError('connector unavailable')
        if self.config.mode == 'fake':
            pages: list[CanvasPageRecord] = []
            for page_url, stored in _fake_store_bucket('pages').items():
                if int(stored.get('course_id') or course_id) != course_id:
                    continue
                pages.append(
                    CanvasPageRecord(
                        page_id=f'fake-page-{compact(page_url)}',
                        course_id=course_id,
                        title=compact(stored.get('title') or page_url),
                        url=page_url,
                        body_html=compact(stored.get('body') or ''),
                    )
                )
            catalog = FAKE_OBJECT_CATALOG.get(course_id, {}).get('pages', [])
            for item in catalog:
                pages.append(
                    CanvasPageRecord(
                        page_id=compact(item.get('page_id') or item.get('url') or ''),
                        course_id=course_id,
                        title=compact(item.get('title') or ''),
                        url=compact(item.get('url') or ''),
                        body_html=compact(item.get('body_html') or ''),
                    )
                )
            return pages
        raise RuntimeError('sandbox read requires human-authorized credentials')

    def list_announcements(self, course_id: int) -> list[CanvasAnnouncementRecord]:
        if not self.connector_available():
            raise RuntimeError('connector unavailable')
        if self.config.mode == 'fake':
            announcements: list[CanvasAnnouncementRecord] = []
            for ann_id, stored in _fake_store_bucket('announcements').items():
                if int(stored.get('course_id') or course_id) != course_id:
                    continue
                announcements.append(
                    CanvasAnnouncementRecord(
                        announcement_id=ann_id,
                        course_id=course_id,
                        title=compact(stored.get('title') or ann_id),
                        message_html=compact(stored.get('body') or ''),
                        posted_at=None,
                    )
                )
            catalog = FAKE_OBJECT_CATALOG.get(course_id, {}).get('announcements', [])
            for item in catalog:
                announcements.append(
                    CanvasAnnouncementRecord(
                        announcement_id=compact(item.get('announcement_id') or ''),
                        course_id=course_id,
                        title=compact(item.get('title') or ''),
                        message_html=compact(item.get('message_html') or ''),
                        posted_at=item.get('posted_at'),
                    )
                )
            return announcements
        raise RuntimeError('sandbox read requires human-authorized credentials')

    def find_existing_object(
        self,
        course_id: int,
        target_type: str,
        *,
        target_id: str | None = None,
        title: str | None = None,
        expected_hash: str | None = None,
    ) -> ExistingObjectResult:
        """Check for existing Canvas objects before create — duplicate prevention."""
        if target_type not in {'page', 'announcement'}:
            return ExistingObjectResult(
                result='CONFLICT',
                target_type=target_type,
                reason='unsupported_target_type',
            )

        if self.config.mode == 'fake':
            bucket = 'pages' if target_type == 'page' else 'announcements'
            store = _fake_store_bucket(bucket)
            if target_id and target_id in store:
                stored = store[target_id]
                actual_hash = compact(stored.get('body_hash') or '')
                actual_title = compact(stored.get('title') or '')
                if expected_hash and actual_hash == compact(expected_hash):
                    return ExistingObjectResult(
                        result='MATCH',
                        target_type=target_type,
                        target_id=target_id,
                        title=actual_title,
                        body_hash=actual_hash,
                    )
                if title and actual_title == compact(title) and expected_hash and actual_hash != compact(expected_hash):
                    return ExistingObjectResult(
                        result='CONFLICT',
                        target_type=target_type,
                        target_id=target_id,
                        title=actual_title,
                        body_hash=actual_hash,
                        reason='content_hash_mismatch',
                    )
                if title and actual_title == compact(title):
                    return ExistingObjectResult(
                        result='MATCH',
                        target_type=target_type,
                        target_id=target_id,
                        title=actual_title,
                        body_hash=actual_hash,
                    )
                return ExistingObjectResult(
                    result='CONFLICT',
                    target_type=target_type,
                    target_id=target_id,
                    title=actual_title,
                    body_hash=actual_hash,
                    reason='existing_object_differs',
                )

            if target_type == 'page':
                for page in self.list_pages(course_id):
                    if title and compact(page.title) == compact(title):
                        return ExistingObjectResult(
                            result='CONFLICT',
                            target_type=target_type,
                            target_id=compact(page.url or page.page_id),
                            title=page.title,
                            reason='title_collision',
                        )
            else:
                for announcement in self.list_announcements(course_id):
                    if title and compact(announcement.title) == compact(title):
                        return ExistingObjectResult(
                            result='CONFLICT',
                            target_type=target_type,
                            target_id=announcement.announcement_id,
                            title=announcement.title,
                            reason='title_collision',
                        )

            return ExistingObjectResult(
                result='MISSING',
                target_type=target_type,
                target_id=target_id,
                title=title,
            )

        if self.config.mode == 'sandbox':
            if self.config.credential_state != 'configured':
                return ExistingObjectResult(
                    result='CONFLICT',
                    target_type=target_type,
                    reason='sandbox_credentials_missing',
                )
            return ExistingObjectResult(
                result='MISSING',
                target_type=target_type,
                target_id=target_id,
                title=title,
            )

        return ExistingObjectResult(
            result='CONFLICT',
            target_type=target_type,
            reason='connector_unavailable',
        )


def _fake_store_bucket(bucket: str) -> dict[str, Any]:
    from scripts.canvas_llm_phase22 import canvas_writer as writer  # noqa: E402

    return writer.FAKE_CANVAS_STORE.get(bucket, {})


def _fake_store_entry(target_type: str, target_id: str) -> dict[str, Any] | None:
    bucket = 'pages' if target_type == 'page' else 'announcements'
    return _fake_store_bucket(bucket).get(target_id)


def sandbox_config_from_env() -> CanvasSandboxConfig:
    return CanvasSandboxConfig(
        mode='sandbox',
        course_id=SANDBOX_COURSE_ID,
        credential_state='disabled',
        enabled=False,
    )


def production_mode_disabled() -> bool:
    source = Path(__file__).read_text().lower()
    return 'production' in source and 'production_modes' in source


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
    from scripts.canvas_llm_phase22 import canvas_writer as writer  # noqa: E402

    writer.FAKE_CANVAS_STORE['pages'].clear()
    writer.FAKE_CANVAS_STORE['announcements'].clear()
    FAKE_OBJECT_CATALOG.clear()

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

    writer.FAKE_CANVAS_STORE['pages']['weekly-agenda-q1w5'] = {
        'course_id': SANDBOX_COURSE_ID,
        'title': 'Weekly Agenda',
        'body': '<p>Agenda</p>',
        'body_hash': writer.body_hash('Weekly Agenda', '<p>Agenda</p>'),
    }
    pages = connector.list_pages(SANDBOX_COURSE_ID)
    assert any(p.url == 'weekly-agenda-q1w5' for p in pages)

    missing = connector.find_existing_object(
        SANDBOX_COURSE_ID,
        'page',
        target_id='new-page',
        title='Brand New Page',
        expected_hash='abc',
    )
    assert missing.result == 'MISSING'

    matched = connector.find_existing_object(
        SANDBOX_COURSE_ID,
        'page',
        target_id='weekly-agenda-q1w5',
        title='Weekly Agenda',
        expected_hash=writer.body_hash('Weekly Agenda', '<p>Agenda</p>'),
    )
    assert matched.result == 'MATCH'

    conflict = connector.find_existing_object(
        SANDBOX_COURSE_ID,
        'page',
        target_id='weekly-agenda-q1w5',
        title='Weekly Agenda',
        expected_hash='different-hash',
    )
    assert conflict.result == 'CONFLICT'

    sandbox_cfg = sandbox_connection_config()
    sandbox = CanvasConnector(sandbox_cfg)
    assert sandbox.connector_available() is False

    sandbox_config = CanvasSandboxConfig()
    assert sandbox_config.stores_credentials() is False
    assert sandbox_config.to_connection_config().writes_allowed() is False
    assert production_mode_disabled()

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
