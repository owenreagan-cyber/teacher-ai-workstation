#!/usr/bin/env python3
"""Canvas verification for controlled teacher-facing Canvas operations."""
from __future__ import annotations

import argparse
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.canvas_llm_phase22 import canvas_connector as connector  # noqa: E402
from scripts.canvas_llm_phase22 import canvas_writer as writer  # noqa: E402
from scripts.canvas_llm_phase22 import phase22_workstation as p22  # noqa: E402

VERIFICATION_STATUSES = ('PASS', 'FAIL', 'BLOCKED', 'DRIFT_DETECTED')


def compact(value: Any) -> str:
    return p22.compact(value)


@dataclass
class VerificationCheck:
    name: str
    status: str
    detail: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class VerificationResult:
    target_type: str
    target_id: str
    course_id: int
    status: str
    checks: list[VerificationCheck] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload['checks'] = [check.to_dict() for check in self.checks]
        return payload


def _read_fake_store(target_type: str, target_id: str) -> dict[str, Any] | None:
    bucket = 'announcements' if target_type == 'announcement' else 'pages'
    return writer.FAKE_CANVAS_STORE.get(bucket, {}).get(target_id)


def verify_announcement(
    course_id: int,
    announcement_id: str,
    *,
    expected_title: str,
    expected_body_hash: str,
    config: connector.CanvasConnectionConfig | None = None,
) -> VerificationResult:
    """Verify a Canvas announcement exists and matches expected content."""
    cfg = config or connector.default_connection_config()
    checks: list[VerificationCheck] = []
    blockers: list[str] = []

    stored = _read_fake_store('announcement', announcement_id)
    if cfg.mode == 'fake' and stored:
        checks.append(VerificationCheck('exists', 'PASS', 'fake store entry found'))
        if stored.get('course_id') == course_id:
            checks.append(VerificationCheck('course_matches', 'PASS'))
        else:
            checks.append(VerificationCheck('course_matches', 'FAIL'))
            blockers.append('course_mismatch')
        actual_title = compact(stored.get('title') or '')
        if actual_title == compact(expected_title):
            checks.append(VerificationCheck('title_matches', 'PASS'))
        else:
            checks.append(VerificationCheck('title_matches', 'FAIL', f'expected={expected_title};actual={actual_title}'))
            blockers.append('title_mismatch')
        actual_hash = compact(stored.get('body_hash') or '')
        if actual_hash == compact(expected_body_hash):
            checks.append(VerificationCheck('content_hash_matches', 'PASS'))
        else:
            checks.append(VerificationCheck('content_hash_matches', 'FAIL'))
            blockers.append('content_hash_mismatch')
    else:
        canvas = connector.CanvasConnector(cfg)
        try:
            record = canvas.read_announcement(course_id, announcement_id)
            checks.append(VerificationCheck('exists', 'PASS'))
            if record.course_id == course_id:
                checks.append(VerificationCheck('course_matches', 'PASS'))
            else:
                checks.append(VerificationCheck('course_matches', 'FAIL'))
                blockers.append('course_mismatch')
            if compact(record.title) == compact(expected_title):
                checks.append(VerificationCheck('title_matches', 'PASS'))
            else:
                checks.append(VerificationCheck('title_matches', 'FAIL'))
                blockers.append('title_mismatch')
            checks.append(VerificationCheck('content_hash_matches', 'BLOCKED', 'read-only preview; hash not available'))
        except RuntimeError:
            checks.append(VerificationCheck('exists', 'FAIL'))
            blockers.append('not_found')

    status = 'PASS'
    if blockers:
        status = 'DRIFT_DETECTED' if 'title_mismatch' in blockers or 'content_hash_mismatch' in blockers else 'FAIL'
    elif any(check.status == 'BLOCKED' for check in checks):
        status = 'BLOCKED'

    return VerificationResult(
        target_type='announcement',
        target_id=announcement_id,
        course_id=course_id,
        status=status,
        checks=checks,
        blockers=blockers,
    )


def verify_page(
    course_id: int,
    page_url: str,
    *,
    expected_title: str,
    expected_body_hash: str,
    config: connector.CanvasConnectionConfig | None = None,
) -> VerificationResult:
    """Verify a Canvas page exists and matches expected content."""
    cfg = config or connector.default_connection_config()
    checks: list[VerificationCheck] = []
    blockers: list[str] = []

    stored = _read_fake_store('page', page_url)
    if cfg.mode == 'fake' and stored:
        checks.append(VerificationCheck('exists', 'PASS', 'fake store entry found'))
        if stored.get('course_id') == course_id:
            checks.append(VerificationCheck('course_matches', 'PASS'))
        else:
            checks.append(VerificationCheck('course_matches', 'FAIL'))
            blockers.append('course_mismatch')
        actual_title = compact(stored.get('title') or '')
        if actual_title == compact(expected_title):
            checks.append(VerificationCheck('title_matches', 'PASS'))
        else:
            checks.append(VerificationCheck('title_matches', 'FAIL', f'expected={expected_title};actual={actual_title}'))
            blockers.append('title_mismatch')
        actual_hash = compact(stored.get('body_hash') or '')
        if actual_hash == compact(expected_body_hash):
            checks.append(VerificationCheck('content_hash_matches', 'PASS'))
        else:
            checks.append(VerificationCheck('content_hash_matches', 'FAIL'))
            blockers.append('content_hash_mismatch')
    else:
        canvas = connector.CanvasConnector(cfg)
        try:
            record = canvas.read_page(course_id, page_url)
            checks.append(VerificationCheck('exists', 'PASS'))
            if record.course_id == course_id:
                checks.append(VerificationCheck('course_matches', 'PASS'))
            else:
                checks.append(VerificationCheck('course_matches', 'FAIL'))
                blockers.append('course_mismatch')
            if compact(record.title) == compact(expected_title):
                checks.append(VerificationCheck('title_matches', 'PASS'))
            else:
                checks.append(VerificationCheck('title_matches', 'FAIL'))
                blockers.append('title_mismatch')
            checks.append(VerificationCheck('content_hash_matches', 'BLOCKED', 'read-only preview; hash not available'))
        except RuntimeError:
            checks.append(VerificationCheck('exists', 'FAIL'))
            blockers.append('not_found')

    status = 'PASS'
    if blockers:
        status = 'DRIFT_DETECTED' if 'title_mismatch' in blockers or 'content_hash_mismatch' in blockers else 'FAIL'
    elif any(check.status == 'BLOCKED' for check in checks):
        status = 'BLOCKED'

    return VerificationResult(
        target_type='page',
        target_id=page_url,
        course_id=course_id,
        status=status,
        checks=checks,
        blockers=blockers,
    )


def command_self_test() -> int:
    writer.FAKE_CANVAS_STORE['announcements'].clear()
    writer.FAKE_CANVAS_STORE['pages'].clear()

    title = 'Assessment Reminder'
    body = 'Reminder for Tuesday assessment'
    body_hash = writer.body_hash(title, body)
    writer.FAKE_CANVAS_STORE['announcements']['ann-test'] = {
        'course_id': connector.SANDBOX_COURSE_ID,
        'title': title,
        'body': body,
        'body_hash': body_hash,
    }

    ok = verify_announcement(
        connector.SANDBOX_COURSE_ID,
        'ann-test',
        expected_title=title,
        expected_body_hash=body_hash,
    )
    assert ok.status == 'PASS'

    drift = verify_announcement(
        connector.SANDBOX_COURSE_ID,
        'ann-test',
        expected_title='Wrong Title',
        expected_body_hash=body_hash,
    )
    assert drift.status == 'DRIFT_DETECTED'

    page_title = 'Week of August 17'
    page_body = '<p>Monday agenda</p>'
    page_hash = writer.body_hash(page_title, page_body)
    writer.FAKE_CANVAS_STORE['pages']['weekly-agenda'] = {
        'course_id': connector.SANDBOX_COURSE_ID,
        'title': page_title,
        'body': page_body,
        'body_hash': page_hash,
    }
    page_ok = verify_page(
        connector.SANDBOX_COURSE_ID,
        'weekly-agenda',
        expected_title=page_title,
        expected_body_hash=page_hash,
    )
    assert page_ok.status == 'PASS'

    print('PASS canvas verification self-test')
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Canvas LLM verification')
    sub = parser.add_subparsers(dest='cmd', required=True)
    sub.add_parser('self-test').set_defaults(func=lambda _args: command_self_test())
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == '__main__':
    raise SystemExit(main())
