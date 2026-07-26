#!/usr/bin/env python3
"""Weekly deployment center and preview for C1F — preview only, no execution."""
from __future__ import annotations

import argparse
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.canvas_llm_phase22 import phase22_workstation as p22  # noqa: E402

PREVIEW_OPERATIONS = ('CREATE', 'UPDATE', 'BLOCKED')
BLOCKED_ASSIGNMENT_REASON = 'Assignment publishing disabled'


def compact(value: Any) -> str:
    return p22.compact(value)


@dataclass
class DeploymentChange:
    operation: str
    target_type: str
    label: str
    artifact_id: str | None = None
    reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DeploymentPreview:
    preview_id: str
    week_code: str
    changes: list[DeploymentChange] = field(default_factory=list)
    artifact_count: int = 0
    approved_count: int = 0
    blocked_count: int = 0
    requires_teacher_action: bool = True
    created_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload['changes'] = [change.to_dict() for change in self.changes]
        return payload


class WeeklyDeploymentCenter:
    """Show all weekly Canvas changes as a deployment preview — no execution."""

    def build_preview(self, packet: dict[str, Any]) -> DeploymentPreview:
        return build_preview_from_packet(packet)

    def print_preview(self, preview: DeploymentPreview) -> None:
        print_preview_report(preview)


def _artifact_change(
    artifact: dict[str, Any],
    *,
    default_operation: str = 'CREATE',
) -> DeploymentChange | None:
    kind = compact(artifact.get('kind') or artifact.get('artifactKind') or '')
    title = compact(artifact.get('title') or artifact.get('label') or '')
    artifact_id = compact(artifact.get('artifactId') or artifact.get('id') or '')

    if kind == 'assignment':
        return DeploymentChange(
            operation='BLOCKED',
            target_type='assignment',
            label=title or 'Assignment',
            artifact_id=artifact_id or None,
            reason=BLOCKED_ASSIGNMENT_REASON,
        )

    if kind in {'page', 'agenda'}:
        label = title or 'Weekly Agenda Page'
        if 'agenda' in compact(artifact.get('subject') or '').lower() or kind == 'agenda':
            label = title or 'Weekly Agenda Page'
        operation = default_operation
        if artifact.get('existing'):
            operation = 'UPDATE'
        return DeploymentChange(
            operation=operation,
            target_type='page',
            label=label,
            artifact_id=artifact_id or None,
        )

    if kind in {'announcement', 'newsletter_update'}:
        return DeploymentChange(
            operation=default_operation if not artifact.get('existing') else 'UPDATE',
            target_type='announcement',
            label=title or 'Assessment Announcement',
            artifact_id=artifact_id or None,
        )

    if kind == 'newsletter':
        return DeploymentChange(
            operation='UPDATE' if artifact.get('existing') else 'CREATE',
            target_type='page',
            label=title or 'Newsletter Page',
            artifact_id=artifact_id or None,
        )

    return None


def build_preview_from_packet(packet: dict[str, Any]) -> DeploymentPreview:
    """Build deployment preview from a weekly content packet — no Canvas execution."""
    week_meta = packet.get('instructionalWeek') or {}
    week_code = p22.canonical_week_code(compact(week_meta.get('code') or packet.get('weekCode') or ''))
    approval_state = compact(packet.get('approvalState') or 'draft')
    approved = approval_state == 'approved'

    changes: list[DeploymentChange] = []
    artifacts = list(packet.get('artifacts') or [])

    if not artifacts:
        if packet.get('agenda'):
            artifacts.append({**packet['agenda'], 'kind': 'agenda'})
        for announcement in packet.get('announcements') or []:
            artifacts.append({**announcement, 'kind': 'announcement'})
        if packet.get('newsletter'):
            artifacts.append({**packet['newsletter'], 'kind': 'newsletter'})

    for artifact in artifacts:
        change = _artifact_change(artifact)
        if change:
            changes.append(change)

    if not any(change.label == 'Weekly Agenda Page' for change in changes):
        if packet.get('includeAgenda', True):
            changes.insert(
                0,
                DeploymentChange(
                    operation='CREATE',
                    target_type='page',
                    label='Weekly Agenda Page',
                ),
            )

    if not any('Announcement' in change.label for change in changes):
        for item in packet.get('announcements') or []:
            changes.append(
                DeploymentChange(
                    operation='CREATE',
                    target_type='announcement',
                    label=compact(item.get('title') or 'Math Assessment Announcement'),
                )
            )

    if packet.get('newsletter') and not any('Newsletter' in c.label for c in changes):
        changes.append(
            DeploymentChange(
                operation='UPDATE' if packet['newsletter'].get('existing') else 'CREATE',
                target_type='page',
                label=compact(packet['newsletter'].get('title') or 'Newsletter Page'),
            )
        )

    blocked_count = sum(1 for change in changes if change.operation == 'BLOCKED')
    approved_count = sum(1 for change in changes if change.operation != 'BLOCKED' and approved)
    preview_id = p22.stable_id('deploy-preview', week_code, len(changes), p22.now_utc())

    return DeploymentPreview(
        preview_id=preview_id,
        week_code=week_code,
        changes=changes,
        artifact_count=len(changes),
        approved_count=approved_count,
        blocked_count=blocked_count,
        requires_teacher_action=True,
        created_at=p22.now_utc(),
    )


def print_preview_report(preview: DeploymentPreview) -> None:
    print('Weekly Deployment Preview')
    print()
    print('Week:')
    print(preview.week_code)
    print()
    print('Changes:')
    print()
    for change in preview.changes:
        print(change.operation)
        print(change.label)
        if change.reason:
            print()
            print('Reason:')
            print(change.reason)
        print()


def preview_performs_no_execution() -> bool:
    source = Path(__file__).read_text().lower()
    marker = 'def preview_performs_no_execution'
    idx = source.find(marker)
    scan_source = source[:idx] if idx >= 0 else source
    forbidden = ('create_announcement', 'create_page', 'attempt_write', 'requests.post')
    return not any(token in scan_source for token in forbidden)


def command_self_test() -> int:
    packet = {
        'weekCode': 'Q1W5',
        'approvalState': 'approved',
        'instructionalWeek': {'code': 'Q1W5', 'startsOn': '2026-08-17'},
        'artifacts': [
            {'kind': 'agenda', 'title': 'Weekly Agenda Page'},
            {'kind': 'announcement', 'title': 'Math Assessment Announcement'},
            {'kind': 'newsletter', 'title': 'Newsletter Page', 'existing': True},
            {'kind': 'assignment', 'title': 'Math Lesson 18'},
        ],
    }
    center = WeeklyDeploymentCenter()
    preview = center.build_preview(packet)
    assert preview.week_code == 'Q1W5'
    assert preview.artifact_count >= 3
    assert preview.blocked_count >= 1
    assert preview.requires_teacher_action is True
    assert any(change.operation == 'BLOCKED' for change in preview.changes)
    assert any(change.operation == 'UPDATE' for change in preview.changes)
    assert preview_performs_no_execution()

    print('PASS weekly deployment center self-test')
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Canvas LLM weekly deployment center')
    sub = parser.add_subparsers(dest='cmd', required=True)
    sub.add_parser('self-test').set_defaults(func=lambda _args: command_self_test())
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == '__main__':
    raise SystemExit(main())
