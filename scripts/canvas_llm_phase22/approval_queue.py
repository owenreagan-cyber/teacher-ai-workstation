#!/usr/bin/env python3
"""Read-only teacher approval queue derived from the Canvas LLM artifact registry."""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.canvas_llm_phase22 import artifact_registry as registry  # noqa: E402
from scripts.canvas_llm_phase22 import phase22_workstation as p22  # noqa: E402

QUEUE_STATUSES = ('READY', 'NEEDS_REVIEW', 'BLOCKED', 'STALE_APPROVAL')
PRIORITIES = ('HIGH', 'MEDIUM', 'LOW')
DECISION_TYPES = ('approve', 'reject', 'request_changes')
DECISION_STATUSES = ('pending', 'approved', 'rejected')
REASON_CODES = (
    'missing_teacher_input',
    'blocked_dependency',
    'approval_required',
    'approval_stale',
    'deployment_blocked',
    'validation_warning',
    'missing_verified_page_url',
)
DEPLOYMENT_BLOCKED = {'blocked_preview', 'blocked'}
QUEUE_SECTION_ORDER = ('READY', 'NEEDS_REVIEW', 'BLOCKED', 'STALE_APPROVAL')
QUEUE_SECTION_LABELS = {
    'READY': 'READY',
    'NEEDS_REVIEW': 'NEEDS REVIEW',
    'BLOCKED': 'BLOCKED',
    'STALE_APPROVAL': 'STALE APPROVAL',
}


def jd(value: Any) -> str:
    return registry.jd(value)


def compact(value: Any) -> str:
    return registry.compact(value)


@dataclass
class ApprovalQueueItem:
    artifact_id: str
    artifact_kind: str
    title: str | None
    subject: str | None
    approval_state: str | None
    approval_revision: int | None
    content_hash: str | None
    needs_review: bool
    warnings: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    queue_status: str = 'READY'
    priority: str = 'LOW'
    reason_codes: list[str] = field(default_factory=list)
    created_at: str | None = None
    updated_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TeacherDecision:
    """Future-ready decision schema. Not persisted in C0R."""

    decision_id: str
    artifact_id: str
    decision_type: str
    status: str
    teacher_note: str | None = None
    created_at: str | None = None
    created_by: str | None = None
    invalidates_on_revision: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def validate_teacher_decision_shape(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required = ('decision_id', 'artifact_id', 'decision_type', 'status')
    for key in required:
        if not compact(data.get(key) or ''):
            errors.append(f'missing required field: {key}')
    decision_type = compact(data.get('decision_type') or '')
    if decision_type and decision_type not in DECISION_TYPES:
        errors.append(f'invalid decision_type: {decision_type}')
    status = compact(data.get('status') or '')
    if status and status not in DECISION_STATUSES:
        errors.append(f'invalid status: {status}')
    if 'invalidates_on_revision' in data and not isinstance(data['invalidates_on_revision'], bool):
        errors.append('invalidates_on_revision must be boolean')
    return errors


def is_stale_approval(
    record: registry.ArtifactRegistryRecord,
    approval_snapshots: dict[str, dict[str, Any]] | None = None,
) -> bool:
    snapshots = approval_snapshots or {}
    snapshot = snapshots.get(record.artifact_id) or {}
    approved_hash = compact(snapshot.get('content_hash') or snapshot.get('contentHash') or '')
    current_hash = compact(record.content_hash or '')
    approved_revision = snapshot.get('approval_revision', snapshot.get('approvalRevision'))
    if approved_hash and current_hash and approved_hash != current_hash:
        return True
    if approved_revision is not None and record.approval_revision is not None:
        if int(approved_revision) != int(record.approval_revision):
            return True
    return False


def derive_reason_codes(
    record: registry.ArtifactRegistryRecord,
    queue_status: str,
) -> list[str]:
    codes: list[str] = []
    if queue_status == 'STALE_APPROVAL':
        codes.append('approval_stale')
    if queue_status == 'BLOCKED':
        if record.blockers:
            if record.artifact_kind == 'newsletter_update':
                codes.append('missing_verified_page_url')
            codes.append('blocked_dependency')
        deployment_status = compact(record.deployment_status or '').lower()
        if deployment_status in DEPLOYMENT_BLOCKED:
            codes.append('deployment_blocked')
    if queue_status == 'NEEDS_REVIEW':
        if record.needs_review:
            codes.append('missing_teacher_input')
        if record.warnings:
            codes.append('validation_warning')
    if queue_status == 'READY' and record.teacher_approval_required:
        codes.append('approval_required')
    return list(dict.fromkeys(code for code in codes if code in REASON_CODES or code))


def derive_priority(queue_status: str, reason_codes: list[str]) -> str:
    if queue_status in {'STALE_APPROVAL', 'BLOCKED'}:
        return 'HIGH'
    if queue_status == 'NEEDS_REVIEW':
        return 'MEDIUM'
    return 'LOW'


def derive_queue_status(
    record: registry.ArtifactRegistryRecord,
    approval_snapshots: dict[str, dict[str, Any]] | None = None,
) -> str:
    if is_stale_approval(record, approval_snapshots):
        return 'STALE_APPROVAL'
    if record.blockers:
        return 'BLOCKED'
    deployment_status = compact(record.deployment_status or '').lower()
    if deployment_status in DEPLOYMENT_BLOCKED and record.artifact_kind == 'newsletter_update':
        return 'BLOCKED'
    if record.needs_review or record.warnings:
        return 'NEEDS_REVIEW'
    if record.teacher_approval_required and record.preview_only:
        return 'READY'
    return 'READY'


def build_queue_item(
    record: registry.ArtifactRegistryRecord,
    approval_snapshots: dict[str, dict[str, Any]] | None = None,
) -> ApprovalQueueItem:
    queue_status = derive_queue_status(record, approval_snapshots)
    reason_codes = derive_reason_codes(record, queue_status)
    return ApprovalQueueItem(
        artifact_id=record.artifact_id,
        artifact_kind=record.artifact_kind,
        title=record.title,
        subject=record.subject,
        approval_state=record.approval_state,
        approval_revision=record.approval_revision,
        content_hash=record.content_hash,
        needs_review=record.needs_review,
        warnings=list(record.warnings),
        blockers=list(record.blockers),
        queue_status=queue_status,
        priority=derive_priority(queue_status, reason_codes),
        reason_codes=reason_codes,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


def build_queue_from_registry(
    records: list[registry.ArtifactRegistryRecord],
    approval_snapshots: dict[str, dict[str, Any]] | None = None,
) -> list[ApprovalQueueItem]:
    items = [build_queue_item(record, approval_snapshots) for record in records]
    items.sort(key=lambda item: (QUEUE_SECTION_ORDER.index(item.queue_status), item.priority, item.title or '', item.artifact_id))
    return items


def load_queue_from_db(
    db: p22.WorkstationDB,
    weekly_plan_id: str | None = None,
    approval_snapshots: dict[str, dict[str, Any]] | None = None,
) -> list[ApprovalQueueItem]:
    records = registry.load_registry_from_db(db, weekly_plan_id)
    return build_queue_from_registry(records, approval_snapshots)


def queue_is_read_only() -> bool:
    source = Path(__file__).read_text()
    for match in re.finditer(r"execute\(\s*(['\"])(.*?)\1", source, re.S):
        sql = match.group(2).strip().upper()
        if sql.startswith('SELECT') or sql.startswith('PRAGMA'):
            continue
        if any(word in sql for word in ('INSERT', 'UPDATE', 'DELETE', 'REPLACE', 'DROP', 'ALTER')):
            return False
    return True


def format_queue_title(item: ApprovalQueueItem) -> str:
    return compact(item.title or item.artifact_id)


def print_queue_report(items: list[ApprovalQueueItem]) -> None:
    print('Canvas LLM Approval Queue')
    print()
    grouped: dict[str, list[ApprovalQueueItem]] = {status: [] for status in QUEUE_SECTION_ORDER}
    for item in items:
        grouped[item.queue_status].append(item)
    for status in QUEUE_SECTION_ORDER:
        section_items = grouped[status]
        if not section_items:
            continue
        label = QUEUE_SECTION_LABELS[status]
        print(label)
        print('-' * len(label))
        suffix = 's' if len(section_items) != 1 else ''
        print(f'{len(section_items)} artifact{suffix}')
        print()
        for item in section_items:
            print(f'- {format_queue_title(item)}')
        print()


def command_queue_report(args: argparse.Namespace) -> int:
    db = p22.WorkstationDB(args.db)
    if not db.path.exists():
        db.migrate()
        db.seed_from_fixture()
        registry.seed_demo_week(db)
    items = load_queue_from_db(db, args.weekly_plan_id)
    print_queue_report(items)
    return 0


def command_self_test() -> int:
    temp_db = Path(p22.os.environ.get('APPROVAL_QUEUE_TEST_DB', f"{p22.os.environ.get('TMPDIR', '/tmp')}/approval-queue-self-test.sqlite3"))
    if temp_db.exists():
        temp_db.unlink()
    db = p22.WorkstationDB(temp_db)
    db.migrate()
    db.seed_from_fixture()
    wid = registry.seed_demo_week(db)

    before = [dict(row) for row in db.connect().execute('SELECT * FROM drafts WHERE weekly_plan_id=?', (wid,))]
    records = registry.load_registry_from_db(db, wid)
    items = build_queue_from_registry(records)
    after = [dict(row) for row in db.connect().execute('SELECT * FROM drafts WHERE weekly_plan_id=?', (wid,))]

    assert before == after, 'approval queue read mutated draft rows'
    assert queue_is_read_only()
    assert registry.registry_is_read_only()

    kinds = {item.artifact_kind for item in items}
    assert 'assignment' in kinds
    assert 'announcement' in kinds
    assert 'newsletter' in kinds
    assert 'daily_brief' in kinds

    tables = [row[0] for row in db.connect().execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
    assert 'approval_queue' not in tables
    assert 'teacher_decisions' not in tables

    ready_items = [item for item in items if item.queue_status == 'READY']
    assert ready_items, 'READY queue state must exist'

    blocked_update = next(item for item in items if item.artifact_kind == 'newsletter_update')
    assert blocked_update.queue_status == 'BLOCKED'
    assert 'missing_verified_page_url' in blocked_update.reason_codes

    daily_brief = next(item for item in items if item.artifact_kind == 'daily_brief')
    assert daily_brief.queue_status == 'READY'

    review_record = registry.ArtifactRegistryRecord(
        artifact_id='review-demo',
        artifact_kind='announcement',
        source_table=registry.SOURCE_TABLE,
        source_id='review-demo',
        title='RM4 Spelling Test coverage missing',
        approval_state='Draft',
        teacher_approval_required=True,
        preview_only=True,
        needs_review=True,
        warnings=['coverage missing'],
    )
    review_item = build_queue_item(review_record)
    assert review_item.queue_status == 'NEEDS_REVIEW'
    assert 'validation_warning' in review_item.reason_codes or 'missing_teacher_input' in review_item.reason_codes

    stale_record = registry.ArtifactRegistryRecord(
        artifact_id='stale-demo',
        artifact_kind='assignment',
        source_table=registry.SOURCE_TABLE,
        source_id='stale-demo',
        title='Stale Assignment',
        approval_state='Approved',
        approval_revision=2,
        content_hash='xyz789',
        approved=True,
        teacher_approval_required=True,
        preview_only=True,
    )
    stale_item = build_queue_item(
        stale_record,
        approval_snapshots={'stale-demo': {'content_hash': 'abc123', 'approval_revision': 1}},
    )
    assert stale_item.queue_status == 'STALE_APPROVAL'
    assert 'approval_stale' in stale_item.reason_codes

    decision_errors = validate_teacher_decision_shape(
        {
            'decision_id': 'dec-1',
            'artifact_id': 'art-1',
            'decision_type': 'approve',
            'status': 'pending',
            'invalidates_on_revision': True,
        }
    )
    assert decision_errors == []

    invalid_errors = validate_teacher_decision_shape({'decision_id': '', 'artifact_id': 'art-1', 'decision_type': 'bad', 'status': 'pending'})
    assert invalid_errors

    encoded_once = jd([item.to_dict() for item in items])
    encoded_twice = jd([item.to_dict() for item in build_queue_from_registry(records)])
    assert encoded_once == encoded_twice, 'approval queue must be deterministic'

    print('PASS approval queue self-test')
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Canvas LLM read-only approval queue')
    parser.add_argument('--db', default=str(p22.DEFAULT_DB_PATH))
    sub = parser.add_subparsers(dest='cmd', required=True)
    report = sub.add_parser('queue-report')
    report.add_argument('--weekly-plan-id')
    report.set_defaults(func=command_queue_report)
    sub.add_parser('self-test').set_defaults(func=lambda _args: command_self_test())
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == '__main__':
    raise SystemExit(main())
