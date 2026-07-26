#!/usr/bin/env python3
"""Canvas drift detection and deployment version tracking for C1H."""
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
from scripts.canvas_llm_phase22 import canvas_verification as verification  # noqa: E402
from scripts.canvas_llm_phase22 import canvas_writer as writer  # noqa: E402
from scripts.canvas_llm_phase22 import phase22_workstation as p22  # noqa: E402

DRIFT_TYPES = ('CONTENT_CHANGED', 'OBJECT_MISSING', 'WRONG_TARGET', 'STALE_VERSION')
DEPLOYMENT_VERSIONS: dict[str, list['CanvasDeploymentVersion']] = {}


def compact(value: Any) -> str:
    return p22.compact(value)


@dataclass
class CanvasDeploymentVersion:
    artifact_id: str
    content_hash: str
    canvas_object_id: str
    revision: int
    published_at: str | None = None
    verified_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CanvasDriftReport:
    artifact_id: str
    expected_hash: str
    actual_hash: str | None
    difference_type: str
    recommendation: str
    requires_teacher_approval: bool = True
    expected_title: str | None = None
    actual_title: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def record_deployment_version(version: CanvasDeploymentVersion) -> CanvasDeploymentVersion:
    history = DEPLOYMENT_VERSIONS.setdefault(version.artifact_id, [])
    history.append(version)
    return version


def latest_deployment_version(artifact_id: str) -> CanvasDeploymentVersion | None:
    history = DEPLOYMENT_VERSIONS.get(artifact_id) or []
    return history[-1] if history else None


def _classify_drift(
    *,
    exists: bool,
    title_match: bool,
    hash_match: bool,
    course_match: bool,
    expected_title: str,
    actual_title: str | None,
) -> tuple[str, str]:
    if not exists:
        return 'OBJECT_MISSING', 'Restore missing Canvas object'
    if not course_match:
        return 'WRONG_TARGET', 'Verify target course before republishing'
    if not title_match and expected_title and actual_title:
        return 'STALE_VERSION', f'Update Canvas page to {expected_title}'
    if not hash_match:
        return 'CONTENT_CHANGED', 'Review content changes and republish with approval'
    return 'CONTENT_CHANGED', 'Review detected differences'


def build_drift_report(
    artifact_id: str,
    *,
    target_type: str,
    target_id: str,
    course_id: int,
    expected_title: str,
    expected_hash: str,
    config: connector.CanvasConnectionConfig | None = None,
) -> CanvasDriftReport | None:
    cfg = config or connector.default_connection_config()
    canvas = connector.CanvasConnector(cfg)
    existing = canvas.find_existing_object(
        course_id,
        target_type,
        target_id=target_id,
        title=expected_title,
        expected_hash=expected_hash,
    )
    if existing.result == 'MISSING':
        return CanvasDriftReport(
            artifact_id=artifact_id,
            expected_hash=expected_hash,
            actual_hash=None,
            difference_type='OBJECT_MISSING',
            recommendation='Restore missing Canvas object',
            requires_teacher_approval=True,
            expected_title=expected_title,
            actual_title=None,
        )

    if target_type == 'announcement':
        result = verification.verify_announcement(
            course_id,
            target_id,
            expected_title=expected_title,
            expected_body_hash=expected_hash,
            config=config,
        )
    else:
        result = verification.verify_page(
            course_id,
            target_id,
            expected_title=expected_title,
            expected_body_hash=expected_hash,
            config=config,
        )

    if result.status == 'PASS':
        return None

    exists = any(check.name == 'exists' and check.status == 'PASS' for check in result.checks)
    title_match = any(check.name == 'title_matches' and check.status == 'PASS' for check in result.checks)
    hash_match = any(check.name == 'content_hash_matches' and check.status == 'PASS' for check in result.checks)
    course_match = any(check.name == 'course_matches' and check.status == 'PASS' for check in result.checks)

    actual_title = None
    actual_hash = None
    for check in result.checks:
        if check.name == 'title_matches' and check.status == 'FAIL' and check.detail:
            parts = check.detail.split(';actual=')
            if len(parts) == 2:
                actual_title = parts[1]
        if check.name == 'content_hash_matches' and check.status == 'FAIL':
            bucket = 'announcements' if target_type == 'announcement' else 'pages'
            stored = writer.FAKE_CANVAS_STORE.get(bucket, {}).get(target_id)
            if stored:
                actual_hash = compact(stored.get('body_hash') or '')

    difference_type, recommendation = _classify_drift(
        exists=exists,
        title_match=title_match,
        hash_match=hash_match,
        course_match=course_match,
        expected_title=expected_title,
        actual_title=actual_title,
    )

    return CanvasDriftReport(
        artifact_id=artifact_id,
        expected_hash=expected_hash,
        actual_hash=actual_hash,
        difference_type=difference_type,
        recommendation=recommendation,
        requires_teacher_approval=True,
        expected_title=expected_title,
        actual_title=actual_title,
    )


def scan_drift_reports(
    items: list[dict[str, Any]],
    *,
    config: connector.CanvasConnectionConfig | None = None,
) -> list[CanvasDriftReport]:
    reports: list[CanvasDriftReport] = []
    for item in items:
        report = build_drift_report(
            compact(item.get('artifact_id') or ''),
            target_type=compact(item.get('target_type') or 'page'),
            target_id=compact(item.get('target_id') or ''),
            course_id=int(item.get('course_id') or connector.SANDBOX_COURSE_ID),
            expected_title=compact(item.get('expected_title') or ''),
            expected_hash=compact(item.get('expected_hash') or item.get('expected_body_hash') or ''),
            config=config,
        )
        if report:
            reports.append(report)
    return reports


def drift_has_no_auto_repair() -> bool:
    source = Path(__file__).read_text().lower()
    marker = 'def drift_has_no_auto_repair'
    idx = source.find(marker)
    scan_source = source[:idx] if idx >= 0 else source
    forbidden = ('auto_repair', 'auto_fix', 'self_heal')
    return not any(token in scan_source for token in forbidden)


def command_self_test() -> int:
    writer.FAKE_CANVAS_STORE['pages'].clear()
    DEPLOYMENT_VERSIONS.clear()

    expected_title = 'August Newsletter'
    actual_title = 'July Newsletter'
    body = '<p>Newsletter</p>'
    target_id = 'newsletter-aug'
    expected_hash = writer.body_hash(expected_title, body)
    writer.FAKE_CANVAS_STORE['pages'][target_id] = {
        'course_id': connector.SANDBOX_COURSE_ID,
        'title': actual_title,
        'body': body,
        'body_hash': writer.body_hash(actual_title, body),
    }

    stale = build_drift_report(
        'artifact-newsletter',
        target_type='page',
        target_id=target_id,
        course_id=connector.SANDBOX_COURSE_ID,
        expected_title=expected_title,
        expected_hash=expected_hash,
    )
    assert stale is not None
    assert stale.difference_type == 'STALE_VERSION'
    assert stale.requires_teacher_approval is True

    missing = build_drift_report(
        'artifact-missing',
        target_type='page',
        target_id='missing-page',
        course_id=connector.SANDBOX_COURSE_ID,
        expected_title='Weekly Agenda',
        expected_hash=writer.body_hash('Weekly Agenda', '<p>agenda</p>'),
    )
    assert missing is not None
    assert missing.difference_type == 'OBJECT_MISSING'

    version = record_deployment_version(
        CanvasDeploymentVersion(
            artifact_id='artifact-newsletter',
            content_hash=expected_hash,
            canvas_object_id=target_id,
            revision=1,
            published_at=p22.now_utc(),
            verified_at=p22.now_utc(),
        )
    )
    assert latest_deployment_version('artifact-newsletter') == version

    assert drift_has_no_auto_repair()
    print('PASS canvas drift self-test')
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Canvas LLM drift detection')
    sub = parser.add_subparsers(dest='cmd', required=True)
    sub.add_parser('self-test').set_defaults(func=lambda _args: command_self_test())
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == '__main__':
    raise SystemExit(main())
