#!/usr/bin/env python3
"""Local-first teacher decision records derived from the Canvas LLM artifact registry."""
from __future__ import annotations

import argparse
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.canvas_llm_phase22 import artifact_registry as registry  # noqa: E402
from scripts.canvas_llm_phase22 import phase22_workstation as p22  # noqa: E402

DECISION_TYPES = ('approve', 'reject', 'request_changes', 'defer')
DECISION_STATUSES = ('active', 'superseded', 'invalidated')
DERIVED_STATES = (
    'APPROVED_BY_TEACHER',
    'READY_FOR_REVIEW',
    'CHANGES_REQUESTED',
    'REVIEW_REQUIRED',
)
REPORT_SECTION_ORDER = (
    ('APPROVED_BY_TEACHER', 'APPROVED'),
    ('READY_FOR_REVIEW', 'REVIEW REQUIRED'),
    ('REVIEW_REQUIRED', 'REVIEW REQUIRED'),
    ('CHANGES_REQUESTED', 'CHANGES REQUESTED'),
)
REPORT_SECTION_LABELS = {
    'APPROVED_BY_TEACHER': 'APPROVED',
    'READY_FOR_REVIEW': 'REVIEW REQUIRED',
    'REVIEW_REQUIRED': 'REVIEW REQUIRED',
    'CHANGES_REQUESTED': 'CHANGES REQUESTED',
    'INVALIDATED': 'INVALIDATED',
}


def jd(value: Any) -> str:
    return registry.jd(value)


def compact(value: Any) -> str:
    return registry.compact(value)


@dataclass
class TeacherDecisionRecord:
    decision_id: str
    artifact_id: str
    artifact_kind: str
    artifact_title: str | None
    decision_type: str
    decision_status: str
    teacher_display: str
    note: str | None
    artifact_content_hash: str | None
    artifact_revision: int | None
    created_at: str | None
    updated_at: str | None
    invalidates_on_revision: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def row_to_record(row: Any) -> TeacherDecisionRecord:
    return TeacherDecisionRecord(
        decision_id=row['id'],
        artifact_id=row['artifact_id'],
        artifact_kind=row['artifact_kind'],
        artifact_title=row['artifact_title'],
        decision_type=row['decision_type'],
        decision_status=row['decision_status'],
        teacher_display=row['teacher_display'],
        note=row['note'] or None,
        artifact_content_hash=row['artifact_content_hash'],
        artifact_revision=int(row['artifact_revision']),
        created_at=row['created_at'],
        updated_at=row['updated_at'],
        invalidates_on_revision=bool(row['invalidates_on_revision']),
    )


def decision_matches_record(record: registry.ArtifactRegistryRecord, decision: TeacherDecisionRecord) -> bool:
    current_hash = compact(record.content_hash or '')
    decision_hash = compact(decision.artifact_content_hash or '')
    if current_hash and decision_hash and current_hash != decision_hash:
        return False
    if decision.artifact_revision is not None and record.approval_revision is not None:
        if int(decision.artifact_revision) != int(record.approval_revision):
            return False
    return True


def derive_teacher_approval_state(
    record: registry.ArtifactRegistryRecord,
    latest: TeacherDecisionRecord | None,
) -> str:
    if latest is None:
        return 'READY_FOR_REVIEW'
    if latest.decision_status == 'invalidated' or not decision_matches_record(record, latest):
        return 'REVIEW_REQUIRED'
    if latest.decision_status == 'superseded':
        return 'READY_FOR_REVIEW'
    if latest.decision_type == 'approve' and latest.decision_status == 'active':
        return 'APPROVED_BY_TEACHER'
    if latest.decision_type in {'reject', 'request_changes'} and latest.decision_status == 'active':
        return 'CHANGES_REQUESTED'
    if latest.decision_type == 'defer':
        return 'READY_FOR_REVIEW'
    return 'REVIEW_REQUIRED'


def sync_invalidations(db: p22.WorkstationDB, records: list[registry.ArtifactRegistryRecord]) -> int:
    by_id = {record.artifact_id: record for record in records}
    updated = 0
    now = p22.now_utc()
    with db.connect() as conn:
        rows = conn.execute(
            "SELECT * FROM teacher_decision_records WHERE decision_status='active' ORDER BY created_at DESC"
        ).fetchall()
        for row in rows:
            record = by_id.get(row['artifact_id'])
            if record is None:
                continue
            decision = row_to_record(row)
            if not decision_matches_record(record, decision):
                conn.execute(
                    "UPDATE teacher_decision_records SET decision_status='invalidated', updated_at=? WHERE id=?",
                    (now, row['id']),
                )
                updated += 1
        conn.commit()
    return updated


def supersede_active_decisions(db: p22.WorkstationDB, artifact_id: str) -> None:
    now = p22.now_utc()
    with db.connect() as conn:
        conn.execute(
            "UPDATE teacher_decision_records SET decision_status='superseded', updated_at=? WHERE artifact_id=? AND decision_status='active'",
            (now, artifact_id),
        )
        conn.commit()


def find_active_duplicate(
    db: p22.WorkstationDB,
    record: registry.ArtifactRegistryRecord,
    decision_type: str,
) -> TeacherDecisionRecord | None:
    with db.connect() as conn:
        row = conn.execute(
            """
            SELECT * FROM teacher_decision_records
            WHERE artifact_id=? AND decision_type=? AND decision_status='active'
              AND artifact_content_hash=? AND artifact_revision=?
            LIMIT 1
            """,
            (
                record.artifact_id,
                decision_type,
                compact(record.content_hash or ''),
                int(record.approval_revision or 0),
            ),
        ).fetchone()
    return row_to_record(row) if row else None


def record_decision(
    db: p22.WorkstationDB,
    record: registry.ArtifactRegistryRecord,
    decision_type: str,
    *,
    teacher_display: str = 'Teacher',
    note: str | None = None,
) -> TeacherDecisionRecord:
    if decision_type not in DECISION_TYPES:
        raise ValueError(f'unsupported decision_type: {decision_type}')
    sync_invalidations(db, [record])
    duplicate = find_active_duplicate(db, record, decision_type)
    if duplicate:
        return duplicate
    supersede_active_decisions(db, record.artifact_id)
    now = p22.now_utc()
    decision_id = p22.stable_id(
        'teacher-decision',
        record.artifact_id,
        decision_type,
        record.content_hash,
        record.approval_revision,
        now,
    )
    with db.connect() as conn:
        conn.execute(
            """
            INSERT INTO teacher_decision_records(
              id, artifact_id, artifact_kind, artifact_title, decision_type, decision_status,
              artifact_content_hash, artifact_revision, teacher_display, note,
              invalidates_on_revision, created_at, updated_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                decision_id,
                record.artifact_id,
                record.artifact_kind,
                compact(record.title or record.artifact_id),
                decision_type,
                'active',
                compact(record.content_hash or ''),
                int(record.approval_revision or 0),
                compact(teacher_display or 'Teacher'),
                compact(note or ''),
                1,
                now,
                now,
            ),
        )
        conn.commit()
        row = conn.execute('SELECT * FROM teacher_decision_records WHERE id=?', (decision_id,)).fetchone()
    return row_to_record(row)


def list_decision_history(db: p22.WorkstationDB, artifact_id: str) -> list[TeacherDecisionRecord]:
    with db.connect() as conn:
        rows = conn.execute(
            'SELECT * FROM teacher_decision_records WHERE artifact_id=? ORDER BY created_at ASC, id ASC',
            (artifact_id,),
        ).fetchall()
    return [row_to_record(row) for row in rows]


def latest_decision(db: p22.WorkstationDB, artifact_id: str) -> TeacherDecisionRecord | None:
    with db.connect() as conn:
        row = conn.execute(
            'SELECT * FROM teacher_decision_records WHERE artifact_id=? ORDER BY created_at DESC, id DESC LIMIT 1',
            (artifact_id,),
        ).fetchone()
    return row_to_record(row) if row else None


def build_approval_snapshots(
    db: p22.WorkstationDB,
    records: list[registry.ArtifactRegistryRecord],
) -> dict[str, dict[str, Any]]:
    snapshots: dict[str, dict[str, Any]] = {}
    for record in records:
        decision = latest_decision(db, record.artifact_id)
        if decision and decision.decision_type == 'approve' and decision.decision_status == 'active':
            snapshots[record.artifact_id] = {
                'content_hash': decision.artifact_content_hash,
                'approval_revision': decision.artifact_revision,
            }
    return snapshots


def summarize_derived_states(
    records: list[registry.ArtifactRegistryRecord],
    db: p22.WorkstationDB,
) -> dict[str, list[dict[str, Any]]]:
    sync_invalidations(db, records)
    grouped: dict[str, list[dict[str, Any]]] = {
        'APPROVED_BY_TEACHER': [],
        'READY_FOR_REVIEW': [],
        'REVIEW_REQUIRED': [],
        'CHANGES_REQUESTED': [],
        'INVALIDATED': [],
    }
    for record in records:
        latest = latest_decision(db, record.artifact_id)
        derived = derive_teacher_approval_state(record, latest)
        entry = {
            'artifact_id': record.artifact_id,
            'artifact_kind': record.artifact_kind,
            'title': record.title,
            'derived_state': derived,
            'latest_decision': latest.to_dict() if latest else None,
        }
        if derived == 'APPROVED_BY_TEACHER':
            grouped['APPROVED_BY_TEACHER'].append(entry)
        elif derived == 'CHANGES_REQUESTED':
            grouped['CHANGES_REQUESTED'].append(entry)
        elif derived == 'REVIEW_REQUIRED':
            grouped['REVIEW_REQUIRED'].append(entry)
        else:
            grouped['READY_FOR_REVIEW'].append(entry)
        if any(item.decision_status == 'invalidated' for item in list_decision_history(db, record.artifact_id)):
            grouped['INVALIDATED'].append(entry)
    return grouped


def format_history_event(decision: TeacherDecisionRecord) -> str:
    created = compact(decision.created_at or '')[:10] or 'unknown-date'
    if decision.decision_status == 'invalidated':
        return f'{created}\nContent changed\nApproval invalidated'
    label = decision.decision_type.replace('_', ' ').title()
    return f'{created}\n{label}\n{decision.teacher_display}'


def print_decision_status_report(records: list[registry.ArtifactRegistryRecord], db: p22.WorkstationDB) -> None:
    grouped = summarize_derived_states(records, db)
    print('Teacher Decisions')
    print()
    review_count = len(grouped['READY_FOR_REVIEW']) + len(grouped['REVIEW_REQUIRED'])
    sections = [
        ('APPROVED_BY_TEACHER', grouped['APPROVED_BY_TEACHER']),
        ('REVIEW_REQUIRED', grouped['READY_FOR_REVIEW'] + grouped['REVIEW_REQUIRED']),
        ('CHANGES_REQUESTED', grouped['CHANGES_REQUESTED']),
        ('INVALIDATED', grouped['INVALIDATED']),
    ]
    for key, items in sections:
        if key == 'REVIEW_REQUIRED' and review_count == 0:
            continue
        if not items:
            continue
        label = REPORT_SECTION_LABELS[key]
        print(label)
        print('-' * len(label))
        count = review_count if key == 'REVIEW_REQUIRED' else len(items)
        suffix = 's' if count != 1 else ''
        print(f'{count} artifact{suffix}')
        print()


def command_decision_report(args: argparse.Namespace) -> int:
    db = p22.WorkstationDB(args.db)
    db.migrate()
    with db.connect() as conn:
        has_plans = conn.execute('SELECT 1 FROM weekly_plans LIMIT 1').fetchone()
    if not has_plans:
        db.seed_from_fixture()
        registry.seed_demo_week(db)
    records = registry.load_registry_from_db(db, args.weekly_plan_id)
    print_decision_status_report(records, db)
    return 0


def command_self_test() -> int:
    temp_db = Path(p22.os.environ.get('TEACHER_DECISIONS_TEST_DB', f"{p22.os.environ.get('TMPDIR', '/tmp')}/teacher-decisions-self-test.sqlite3"))
    if temp_db.exists():
        temp_db.unlink()
    db = p22.WorkstationDB(temp_db)
    db.migrate()
    db.seed_from_fixture()
    wid = registry.seed_demo_week(db)

    before = [dict(row) for row in db.connect().execute('SELECT * FROM drafts WHERE weekly_plan_id=?', (wid,))]
    records = registry.load_registry_from_db(db, wid)
    assert records, 'registry must provide artifacts'

    assignment = next(item for item in records if item.artifact_kind == 'assignment')
    announcement = next(item for item in records if item.artifact_kind == 'announcement' and item.subject != p22.HOMEROOM_NEWSLETTER_SUBJECT)
    newsletter = next(item for item in records if item.artifact_kind == 'newsletter')
    daily_brief = next(item for item in records if item.artifact_kind == 'daily_brief')

    approved_assignment = record_decision(db, assignment, 'approve')
    assert approved_assignment.decision_status == 'active'
    assert derive_teacher_approval_state(assignment, approved_assignment) == 'APPROVED_BY_TEACHER'

    approved_announcement = record_decision(db, announcement, 'approve')
    approved_newsletter = record_decision(db, newsletter, 'approve')
    approved_brief = record_decision(db, daily_brief, 'approve')
    assert approved_announcement.artifact_kind == 'announcement'
    assert approved_newsletter.artifact_kind == 'newsletter'
    assert approved_brief.artifact_kind == 'daily_brief'

    duplicate = record_decision(db, assignment, 'approve')
    assert duplicate.decision_id == approved_assignment.decision_id

    history = list_decision_history(db, newsletter.artifact_id)
    assert len(history) >= 1

    edited_newsletter = registry.ArtifactRegistryRecord(**{**newsletter.to_dict(), 'content_hash': 'edited-hash-001', 'approval_revision': int(newsletter.approval_revision or 0) + 1})
    sync_invalidations(db, [edited_newsletter])
    invalidated = latest_decision(db, newsletter.artifact_id)
    assert invalidated is not None
    assert invalidated.decision_status == 'invalidated'
    assert derive_teacher_approval_state(edited_newsletter, invalidated) == 'REVIEW_REQUIRED'

    reapproved = record_decision(db, edited_newsletter, 'approve')
    assert reapproved.decision_status == 'active'
    assert len(list_decision_history(db, newsletter.artifact_id)) >= 2

    revised_assignment = registry.ArtifactRegistryRecord(
        **{**assignment.to_dict(), 'approval_revision': int(assignment.approval_revision or 0) + 1}
    )
    sync_invalidations(db, [revised_assignment])
    latest = latest_decision(db, assignment.artifact_id)
    assert latest is not None
    assert latest.decision_status == 'invalidated'

    rejected = record_decision(db, announcement, 'reject', note='Needs coverage details')
    assert derive_teacher_approval_state(announcement, rejected) == 'CHANGES_REQUESTED'

    defer_brief = record_decision(db, daily_brief, 'defer', note='Review later')
    assert derive_teacher_approval_state(daily_brief, defer_brief) == 'READY_FOR_REVIEW'

    after = [dict(row) for row in db.connect().execute('SELECT * FROM drafts WHERE weekly_plan_id=?', (wid,))]
    assert before == after, 'teacher decisions must not mutate draft artifacts'

    tables = [row[0] for row in db.connect().execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
    assert 'teacher_decision_records' in tables

    print('PASS teacher decisions self-test')
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Canvas LLM teacher decision records')
    parser.add_argument('--db', default=str(p22.DEFAULT_DB_PATH))
    sub = parser.add_subparsers(dest='cmd', required=True)
    report = sub.add_parser('decision-report')
    report.add_argument('--weekly-plan-id')
    report.set_defaults(func=command_decision_report)
    sub.add_parser('self-test').set_defaults(func=lambda _args: command_self_test())
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == '__main__':
    raise SystemExit(main())
