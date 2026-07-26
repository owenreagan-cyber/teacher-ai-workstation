#!/usr/bin/env python3
"""Read-only artifact registry normalization layer for Canvas LLM C0-series artifacts."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.canvas_llm_phase22 import phase22_workstation as p22  # noqa: E402

SOURCE_TABLE = 'drafts'
SUPPORTED_KINDS = (
    'assignment',
    'announcement',
    'newsletter',
    'newsletter_update',
    'daily_brief',
)
DEPLOYMENT_ACTIVE = {'deployed', 'scheduled', 'partially_deployed', 'publishing', 'sent'}
CATEGORY_LABELS = {
    'assignment': 'Assignments',
    'announcement': 'Announcements',
    'newsletter': 'Homeroom Newsletter',
    'newsletter_update': 'Newsletter Update Announcement',
    'daily_brief': 'Daily Teacher Brief',
}


def jl(value: Any, default: Any = None) -> Any:
    return p22.jl(value, default)


def compact(value: Any) -> str:
    return p22.compact(value)


def jd(value: Any) -> str:
    return p22.jd(value)


def as_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    return bool(value)


def pick(obj: dict[str, Any], *keys: str, default: Any = None) -> Any:
    for key in keys:
        if key in obj and obj[key] is not None:
            return obj[key]
    return default


@dataclass
class ArtifactRegistryRecord:
    artifact_id: str
    artifact_kind: str
    source_table: str
    source_id: str
    weekly_plan_id: str | None = None
    subject: str | None = None
    title: str | None = None
    content_hash: str | None = None
    approval_state: str | None = None
    approval_revision: int | None = None
    approved: bool = False
    teacher_approval_required: bool = False
    preview_only: bool = False
    canvas_writes_allowed: bool = False
    email_sends_allowed: bool = False
    deployment_status: str | None = None
    needs_review: bool = False
    warnings: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    created_at: str | None = None
    updated_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def resolve_nested_artifact(draft_kind: str, payload: dict[str, Any]) -> dict[str, Any]:
    artifact_kind = compact(payload.get('artifactKind') or '')
    if draft_kind == 'assignment':
        return payload
    if draft_kind == 'daily_brief' or artifact_kind == 'daily_brief':
        return payload.get('dailyBriefDraft') or {}
    if artifact_kind == 'newsletter':
        return payload.get('newsletterDraft') or {}
    if artifact_kind == 'newsletter_update':
        return payload.get('announcementDraft') or {}
    if draft_kind == 'announcement':
        return payload.get('announcementDraft') or {}
    return {}


def resolve_artifact_kind(draft_kind: str, payload: dict[str, Any]) -> str | None:
    artifact_kind = compact(payload.get('artifactKind') or '')
    nested = resolve_nested_artifact(draft_kind, payload)
    nested_kind = compact(pick(nested, 'artifact_kind', 'artifactKind', default=''))
    if draft_kind == 'assignment':
        return 'assignment'
    if draft_kind == 'daily_brief' or artifact_kind == 'daily_brief' or nested_kind == 'daily_brief':
        return 'daily_brief'
    if artifact_kind == 'newsletter' or nested_kind == 'newsletter':
        return 'newsletter'
    if artifact_kind == 'newsletter_update' or nested_kind == 'newsletter_update':
        return 'newsletter_update'
    if draft_kind == 'announcement':
        return 'announcement'
    return None


def derive_content_hash(draft_row: dict[str, Any], nested: dict[str, Any]) -> str | None:
    explicit = pick(nested, 'content_hash', 'contentHash')
    if explicit:
        return compact(explicit)
    canonical = {
        'title': draft_row.get('title'),
        'body_text': draft_row.get('body_text'),
        'payload': nested,
    }
    return hashlib.sha256(jd(canonical).encode()).hexdigest()[:16]


def normalize_draft_row(draft_row: dict[str, Any]) -> ArtifactRegistryRecord | None:
    payload = jl(draft_row.get('payload') or '{}', {})
    artifact_kind = resolve_artifact_kind(draft_row.get('kind') or '', payload)
    if artifact_kind not in SUPPORTED_KINDS:
        return None

    nested = resolve_nested_artifact(draft_row.get('kind') or '', payload)
    warnings = list(pick(nested, 'warnings', default=[]) or [])
    blockers = list(pick(nested, 'blockers', default=[]) or [])

    approval_state = pick(nested, 'approval_state', 'approvalState', default='Draft')
    approval_revision = pick(nested, 'approval_revision', 'approvalRevision', default=0)
    approved = as_bool(pick(nested, 'approved', default=False))
    teacher_approval_required = as_bool(
        pick(nested, 'teacher_approval_required', 'teacherApprovalRequired', default=payload.get('teacherApprovalRequired')),
        default=True,
    )
    preview_only = as_bool(
        pick(nested, 'preview_only', 'previewOnly', default=payload.get('previewOnly')),
        default=True,
    )
    canvas_writes_allowed = as_bool(
        pick(nested, 'canvas_writes_allowed', 'canvasWritesAllowed', default=False),
        default=False,
    )
    email_sends_allowed = as_bool(
        pick(nested, 'email_sends_allowed', 'emailSendsAllowed', default=False),
        default=False,
    )
    deployment_status = compact(
        pick(
            nested,
            'deployment_status',
            'deploymentStatus',
            'delivery_status',
            'deliveryStatus',
            default='preview_only',
        )
        or 'preview_only'
    )
    needs_review = as_bool(pick(nested, 'needs_review', 'needsReview', default=False))

    return ArtifactRegistryRecord(
        artifact_id=compact(draft_row.get('id') or ''),
        artifact_kind=artifact_kind,
        source_table=SOURCE_TABLE,
        source_id=compact(draft_row.get('id') or ''),
        weekly_plan_id=compact(draft_row.get('weekly_plan_id') or '') or None,
        subject=compact(draft_row.get('subject') or '') or None,
        title=compact(draft_row.get('title') or '') or None,
        content_hash=derive_content_hash(draft_row, nested),
        approval_state=approval_state,
        approval_revision=int(approval_revision or 0),
        approved=approved,
        teacher_approval_required=teacher_approval_required,
        preview_only=preview_only,
        canvas_writes_allowed=canvas_writes_allowed,
        email_sends_allowed=email_sends_allowed,
        deployment_status=deployment_status or None,
        needs_review=needs_review,
        warnings=warnings,
        blockers=blockers,
        created_at=compact(draft_row.get('created_at') or '') or None,
        updated_at=compact(draft_row.get('updated_at') or '') or None,
    )


def normalize_draft_rows(draft_rows: list[dict[str, Any]]) -> list[ArtifactRegistryRecord]:
    records: list[ArtifactRegistryRecord] = []
    for row in draft_rows:
        record = normalize_draft_row(row)
        if record is not None:
            records.append(record)
    records.sort(key=lambda item: (item.artifact_kind, item.artifact_id))
    return records


def evaluate_artifact_health(record: ArtifactRegistryRecord) -> str:
    deployment_status = compact(record.deployment_status or '').lower()

    if record.approved and record.blockers:
        return 'BLOCK'

    if deployment_status in DEPLOYMENT_ACTIVE and not record.canvas_writes_allowed:
        return 'BLOCK'

    if record.blockers and deployment_status in {'blocked_preview', 'blocked'}:
        return 'BLOCK'

    if record.needs_review or record.warnings:
        return 'WARN'

    if compact(record.approval_state or '').lower() == 'draft' and record.teacher_approval_required and record.preview_only:
        return 'PASS'

    return 'PASS'


def summarize_registry(records: list[ArtifactRegistryRecord]) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for kind in SUPPORTED_KINDS:
        kind_records = [record for record in records if record.artifact_kind == kind]
        if not kind_records:
            continue
        health_counts = {'PASS': 0, 'WARN': 0, 'BLOCK': 0}
        for record in kind_records:
            health_counts[evaluate_artifact_health(record)] += 1
        blocked_messages: list[str] = []
        if kind == 'newsletter_update' and any(record.blockers for record in kind_records):
            blocked_messages.append('deployment unavailable without verified page')
        if kind == 'newsletter' and any(record.blockers for record in kind_records):
            blocked_messages.append('deployment unavailable without verified page')
        if kind == 'daily_brief' and all(not record.email_sends_allowed for record in kind_records):
            blocked_messages.append('delivery disabled')
        summary[kind] = {
            'count': len(kind_records),
            'health': health_counts,
            'blocked_messages': blocked_messages,
        }
    return summary


def load_registry_from_drafts(draft_rows: list[dict[str, Any]]) -> list[ArtifactRegistryRecord]:
    return normalize_draft_rows(draft_rows)


def load_registry_from_db(db: p22.WorkstationDB, weekly_plan_id: str | None = None) -> list[ArtifactRegistryRecord]:
    with db.connect() as conn:
        if weekly_plan_id:
            rows = [dict(row) for row in conn.execute('SELECT * FROM drafts WHERE weekly_plan_id=? ORDER BY kind, subject, title', (weekly_plan_id,))]
        else:
            rows = [dict(row) for row in conn.execute('SELECT * FROM drafts ORDER BY weekly_plan_id, kind, subject, title')]
    return load_registry_from_drafts(rows)


def registry_is_read_only() -> bool:
    source = Path(__file__).read_text()
    for match in re.finditer(r"execute\(\s*(['\"])(.*?)\1", source, re.S):
        sql = match.group(2).strip().upper()
        if sql.startswith('SELECT') or sql.startswith('PRAGMA'):
            continue
        if any(word in sql for word in ('INSERT', 'UPDATE', 'DELETE', 'REPLACE', 'DROP', 'ALTER')):
            return False
    return True


def print_health_report(records: list[ArtifactRegistryRecord]) -> None:
    print('Canvas LLM Artifact Health')
    print()
    summary = summarize_registry(records)
    display_order = ('assignment', 'announcement', 'newsletter', 'newsletter_update', 'daily_brief')
    for kind in display_order:
        if kind not in summary:
            continue
        info = summary[kind]
        print(CATEGORY_LABELS[kind])
        if info['health']['PASS']:
            label = 'artifact' if kind != 'daily_brief' else 'preview'
            suffix = 's' if info['health']['PASS'] != 1 else ''
            if kind == 'newsletter':
                print('PASS:')
                print(f"{info['health']['PASS']} monthly preview")
            elif kind == 'daily_brief':
                print('PASS:')
                print(f"{info['health']['PASS']} preview{suffix}")
            else:
                print('PASS:')
                print(f"{info['health']['PASS']} {label}{suffix}")
        if info['health']['WARN']:
            print('WARN:')
            print(f"{info['health']['WARN']} need review")
        for message in info['blocked_messages']:
            print('BLOCKED:')
            print(message)
        print()


def seed_demo_week(db: p22.WorkstationDB) -> str:
    week = p22.instructional_week_by_code('Q1W5')
    assert week is not None
    wid = db.create_week(week['startsOn'])
    week_data = db.get_week(wid)
    for subject_plan in week_data['subjects']:
        if subject_plan['subject'] != 'math':
            continue
        for index, day in enumerate(subject_plan['days']):
            fields = {'lesson': str(18 + index), 'title': f'Lesson {18 + index}'}
            if index == 1:
                fields = {'lesson': '', 'tests': '4', 'title': 'Written Assessment 4'}
            db.patch_table(
                'daily_subject_entries',
                day['id'],
                fields,
                day['version'],
            )
    db.generate_week(wid)
    return wid


def command_health_report(args: argparse.Namespace) -> int:
    db = p22.WorkstationDB(args.db)
    if not db.path.exists():
        db.migrate()
        db.seed_from_fixture()
        seed_demo_week(db)
    records = load_registry_from_db(db, args.weekly_plan_id)
    print_health_report(records)
    return 0


def command_self_test() -> int:
    temp_db = Path(p22.os.environ.get('ARTIFACT_REGISTRY_TEST_DB', f"{p22.os.environ.get('TMPDIR', '/tmp')}/artifact-registry-self-test.sqlite3"))
    if temp_db.exists():
        temp_db.unlink()
    db = p22.WorkstationDB(temp_db)
    db.migrate()
    db.seed_from_fixture()
    wid = seed_demo_week(db)

    before = [dict(row) for row in db.connect().execute('SELECT * FROM drafts WHERE weekly_plan_id=?', (wid,))]
    records = load_registry_from_db(db, wid)
    after = [dict(row) for row in db.connect().execute('SELECT * FROM drafts WHERE weekly_plan_id=?', (wid,))]

    assert before == after, 'registry read mutated draft rows'
    assert registry_is_read_only()
    assert all(record.source_table == SOURCE_TABLE for record in records)

    kinds = {record.artifact_kind for record in records}
    assert 'assignment' in kinds
    assert 'announcement' in kinds
    assert 'newsletter' in kinds
    assert 'newsletter_update' in kinds
    assert 'daily_brief' in kinds

    first = jd([record.to_dict() for record in records])
    second = jd([record.to_dict() for record in load_registry_from_db(db, wid)])
    assert first == second, 'registry output is not deterministic'

    draft_record = next(record for record in records if record.artifact_kind == 'assignment')
    assert evaluate_artifact_health(draft_record) == 'PASS'

    warn_record = ArtifactRegistryRecord(
        artifact_id='warn-demo',
        artifact_kind='announcement',
        source_table=SOURCE_TABLE,
        source_id='warn-demo',
        approval_state='Draft',
        teacher_approval_required=True,
        preview_only=True,
        needs_review=True,
        warnings=['coverage required'],
    )
    assert evaluate_artifact_health(warn_record) == 'WARN'

    block_record = ArtifactRegistryRecord(
        artifact_id='block-demo',
        artifact_kind='newsletter_update',
        source_table=SOURCE_TABLE,
        source_id='block-demo',
        approved=True,
        blockers=['verified page required'],
    )
    assert evaluate_artifact_health(block_record) == 'BLOCK'

    deploy_block = ArtifactRegistryRecord(
        artifact_id='deploy-block-demo',
        artifact_kind='announcement',
        source_table=SOURCE_TABLE,
        source_id='deploy-block-demo',
        deployment_status='deployed',
        canvas_writes_allowed=False,
    )
    assert evaluate_artifact_health(deploy_block) == 'BLOCK'

    tables = [row[0] for row in db.connect().execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
    assert 'artifact_registry' not in tables, 'duplicate artifact storage table must not exist'

    print('PASS artifact registry self-test')
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Canvas LLM read-only artifact registry adapter')
    parser.add_argument('--db', default=str(p22.DEFAULT_DB_PATH))
    sub = parser.add_subparsers(dest='cmd', required=True)
    report = sub.add_parser('health-report')
    report.add_argument('--weekly-plan-id')
    report.set_defaults(func=command_health_report)
    sub.add_parser('self-test').set_defaults(func=lambda _args: command_self_test())
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == '__main__':
    raise SystemExit(main())
