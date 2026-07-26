#!/usr/bin/env python3
"""Canvas repair detection foundation for C1D — drift detection without automatic repair."""
from __future__ import annotations

import argparse
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.canvas_llm_phase22 import canvas_connector as connector  # noqa: E402
from scripts.canvas_llm_phase22 import canvas_verification as verification  # noqa: E402
from scripts.canvas_llm_phase22 import canvas_writer as writer  # noqa: E402
from scripts.canvas_llm_phase22 import phase22_workstation as p22  # noqa: E402

REPAIR_ACTIONS = ('review_and_redeploy', 'request_teacher_approval', 'manual_correction')


def compact(value: Any) -> str:
    return p22.compact(value)


@dataclass
class RepairRecommendation:
    artifact_id: str
    issue: str
    recommended_action: str
    requires_teacher_approval: bool = True
    expected_title: str | None = None
    actual_title: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def detect_announcement_drift(
    artifact_id: str,
    course_id: int,
    announcement_id: str,
    *,
    expected_title: str,
    expected_body_hash: str,
    config: connector.CanvasConnectionConfig | None = None,
) -> RepairRecommendation | None:
    result = verification.verify_announcement(
        course_id,
        announcement_id,
        expected_title=expected_title,
        expected_body_hash=expected_body_hash,
        config=config,
    )
    if result.status != 'DRIFT_DETECTED':
        return None
    actual_title = None
    for check in result.checks:
        if check.name == 'title_matches' and check.status == 'FAIL' and check.detail:
            parts = check.detail.split(';actual=')
            if len(parts) == 2:
                actual_title = parts[1]
    return RepairRecommendation(
        artifact_id=artifact_id,
        issue='DRIFT DETECTED: title mismatch',
        recommended_action='review_and_redeploy',
        requires_teacher_approval=True,
        expected_title=expected_title,
        actual_title=actual_title,
    )


def detect_page_drift(
    artifact_id: str,
    course_id: int,
    page_url: str,
    *,
    expected_title: str,
    expected_body_hash: str,
    config: connector.CanvasConnectionConfig | None = None,
) -> RepairRecommendation | None:
    result = verification.verify_page(
        course_id,
        page_url,
        expected_title=expected_title,
        expected_body_hash=expected_body_hash,
        config=config,
    )
    if result.status != 'DRIFT_DETECTED':
        return None
    actual_title = None
    for check in result.checks:
        if check.name == 'title_matches' and check.status == 'FAIL' and check.detail:
            parts = check.detail.split(';actual=')
            if len(parts) == 2:
                actual_title = parts[1]
    return RepairRecommendation(
        artifact_id=artifact_id,
        issue='DRIFT DETECTED: title mismatch',
        recommended_action='request_teacher_approval',
        requires_teacher_approval=True,
        expected_title=expected_title,
        actual_title=actual_title,
    )


def scan_for_drift(
    items: list[dict[str, Any]],
    *,
    config: connector.CanvasConnectionConfig | None = None,
) -> list[RepairRecommendation]:
    """Scan expected Canvas objects for drift — never auto-repairs."""
    recommendations: list[RepairRecommendation] = []
    for item in items:
        target_type = compact(item.get('target_type') or '')
        artifact_id = compact(item.get('artifact_id') or '')
        course_id = int(item.get('course_id') or connector.SANDBOX_COURSE_ID)
        expected_title = compact(item.get('expected_title') or '')
        expected_hash = compact(item.get('expected_body_hash') or '')
        target_id = compact(item.get('target_id') or '')

        if target_type == 'announcement':
            rec = detect_announcement_drift(
                artifact_id, course_id, target_id,
                expected_title=expected_title,
                expected_body_hash=expected_hash,
                config=config,
            )
        elif target_type == 'page':
            rec = detect_page_drift(
                artifact_id, course_id, target_id,
                expected_title=expected_title,
                expected_body_hash=expected_hash,
                config=config,
            )
        else:
            continue
        if rec:
            recommendations.append(rec)
    return recommendations


def repair_has_no_auto_fix() -> bool:
    source = Path(__file__).read_text().lower()
    marker = 'def repair_has_no_auto_fix'
    idx = source.find(marker)
    scan_source = source[:idx] if idx >= 0 else source
    forbidden = ('auto_repair', 'auto_fix', 'self_heal')
    return not any(token in scan_source for token in forbidden)


def command_self_test() -> int:
    writer.FAKE_CANVAS_STORE['pages'].clear()

    expected = 'August Newsletter'
    actual = 'July Newsletter'
    body = '<p>Newsletter content</p>'
    body_hash = writer.body_hash(actual, body)
    writer.FAKE_CANVAS_STORE['pages']['homeroom-newsletter'] = {
        'course_id': connector.SANDBOX_COURSE_ID,
        'title': actual,
        'body': body,
        'body_hash': body_hash,
    }

    rec = detect_page_drift(
        'artifact-newsletter-001',
        connector.SANDBOX_COURSE_ID,
        'homeroom-newsletter',
        expected_title=expected,
        expected_body_hash=writer.body_hash(expected, body),
    )
    assert rec is not None
    assert 'DRIFT DETECTED' in rec.issue
    assert rec.requires_teacher_approval is True
    assert rec.actual_title == actual

    items = scan_for_drift([
        {
            'target_type': 'page',
            'artifact_id': 'artifact-newsletter-001',
            'course_id': connector.SANDBOX_COURSE_ID,
            'target_id': 'homeroom-newsletter',
            'expected_title': expected,
            'expected_body_hash': writer.body_hash(expected, body),
        },
    ])
    assert len(items) == 1
    assert repair_has_no_auto_fix()

    print('PASS canvas repair self-test')
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Canvas LLM repair detection')
    sub = parser.add_subparsers(dest='cmd', required=True)
    sub.add_parser('self-test').set_defaults(func=lambda _args: command_self_test())
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == '__main__':
    raise SystemExit(main())
