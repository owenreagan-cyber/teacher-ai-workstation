#!/usr/bin/env python3
"""Deployment readiness gate for Canvas LLM artifacts."""
from __future__ import annotations

import argparse
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.canvas_llm_phase22 import approval_queue as queue  # noqa: E402
from scripts.canvas_llm_phase22 import artifact_registry as registry  # noqa: E402
from scripts.canvas_llm_phase22 import canvas_connector as connector  # noqa: E402
from scripts.canvas_llm_phase22 import deployment_audit as audit  # noqa: E402
from scripts.canvas_llm_phase22 import phase22_workstation as p22  # noqa: E402
from scripts.canvas_llm_phase22 import rollback as rollback_mod  # noqa: E402
from scripts.canvas_llm_phase22 import teacher_decisions as decisions  # noqa: E402

READINESS_STATUSES = ('READY', 'NEEDS_REVIEW', 'BLOCKED', 'NOT_ELIGIBLE')
SANDBOX_COURSE_ID = connector.SANDBOX_COURSE_ID


def compact(value: Any) -> str:
    return p22.compact(value)


def jd(value: Any) -> str:
    return registry.jd(value)


@dataclass
class DeploymentReadinessRecord:
    deployment_id: str
    artifact_id: str
    artifact_kind: str
    artifact_title: str | None
    target_system: str
    target_course: str | None
    operation_type: str
    approval_status: str
    health_status: str
    validation_status: str
    teacher_decision_status: str
    readiness_status: str
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    rollback_plan: str | None = None
    created_at: str | None = None
    updated_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def derive_validation_status(record: registry.ArtifactRegistryRecord) -> tuple[str, list[str], list[str]]:
    health = registry.evaluate_artifact_health(record)
    warnings = list(record.warnings)
    blockers = list(record.blockers)
    if health == 'BLOCK':
        return 'FAIL', warnings, blockers or ['validation_failed']
    if health == 'WARN' or record.needs_review:
        return 'WARN', warnings, blockers
    return 'PASS', warnings, blockers


def derive_health_status(record: registry.ArtifactRegistryRecord) -> str:
    health = registry.evaluate_artifact_health(record)
    if health == 'BLOCK':
        return 'FAIL'
    if health == 'WARN':
        return 'WARN'
    return 'PASS'


def derive_approval_status(
    record: registry.ArtifactRegistryRecord,
    queue_item: queue.ApprovalQueueItem,
) -> str:
    if queue_item.queue_status == 'STALE_APPROVAL':
        return 'FAIL'
    if queue_item.queue_status == 'BLOCKED':
        return 'FAIL'
    if queue_item.queue_status == 'NEEDS_REVIEW':
        return 'WARN'
    return 'PASS'


def derive_teacher_decision_status(
    record: registry.ArtifactRegistryRecord,
    latest: decisions.TeacherDecisionRecord | None,
) -> str:
    derived = decisions.derive_teacher_approval_state(record, latest)
    if derived == 'APPROVED_BY_TEACHER':
        return 'PASS'
    if derived in {'CHANGES_REQUESTED', 'REVIEW_REQUIRED'}:
        return 'FAIL'
    return 'WARN'


def derive_readiness_status(
    *,
    artifact_exists: bool,
    validation_status: str,
    health_status: str,
    approval_status: str,
    teacher_decision_status: str,
    connector_available: bool,
    warnings: list[str],
    blockers: list[str],
    rollback_complete: bool,
    owner_decision_missing: bool = False,
) -> tuple[str, list[str], list[str]]:
    local_blockers = list(blockers)
    local_warnings = list(warnings)

    if not artifact_exists:
        return 'NOT_ELIGIBLE', local_blockers + ['missing_artifact'], local_warnings

    if validation_status == 'FAIL' or health_status == 'FAIL':
        if 'validation_failed' not in local_blockers and validation_status == 'FAIL':
            local_blockers.append('validation_failed')
        return 'BLOCKED', local_blockers, local_warnings

    if approval_status == 'FAIL':
        if 'missing_approval' not in local_blockers:
            local_blockers.append('missing_approval')
        return 'BLOCKED', local_blockers, local_warnings

    if teacher_decision_status == 'FAIL':
        if 'missing_teacher_decision' not in local_blockers:
            local_blockers.append('missing_teacher_decision')
        return 'BLOCKED', local_blockers, local_warnings

    if not rollback_complete:
        local_blockers.append('missing_rollback_plan')
        return 'BLOCKED', local_blockers, local_warnings

    if not connector_available:
        local_blockers.append('connector_disabled')
        return 'BLOCKED', local_blockers, local_warnings

    if owner_decision_missing or local_warnings or validation_status == 'WARN' or approval_status == 'WARN' or teacher_decision_status == 'WARN':
        if owner_decision_missing and 'owner_decision_missing' not in local_warnings:
            local_warnings.append('owner_decision_missing')
        return 'NEEDS_REVIEW', local_blockers, local_warnings

    if teacher_decision_status == 'PASS' and approval_status == 'PASS' and validation_status == 'PASS' and health_status == 'PASS' and connector_available:
        return 'READY', local_blockers, local_warnings

    return 'NOT_ELIGIBLE', local_blockers, local_warnings


def build_readiness_record(
    record: registry.ArtifactRegistryRecord,
    queue_item: queue.ApprovalQueueItem,
    latest_decision: decisions.TeacherDecisionRecord | None,
    *,
    config: connector.CanvasConnectionConfig | None = None,
    audit_log: audit.DeploymentAuditLog | None = None,
) -> DeploymentReadinessRecord:
    cfg = config or connector.default_connection_config()
    canvas = connector.CanvasConnector(cfg)
    now = p22.now_utc()
    deployment_id = p22.stable_id('deployment-readiness', record.artifact_id, record.content_hash, record.approval_revision)

    validation_status, warnings, blockers = derive_validation_status(record)
    health_status = derive_health_status(record)
    approval_status = derive_approval_status(record, queue_item)
    teacher_decision_status = derive_teacher_decision_status(record, latest_decision)

    rollback_plan = rollback_mod.generate_rollback_plan(deployment_id, record.artifact_id, record.artifact_kind)
    rollback_complete = rollback_plan.is_complete()

    owner_decision_missing = teacher_decision_status != 'PASS' and record.teacher_approval_required

    readiness_status, blockers, warnings = derive_readiness_status(
        artifact_exists=bool(record.artifact_id),
        validation_status=validation_status,
        health_status=health_status,
        approval_status=approval_status,
        teacher_decision_status=teacher_decision_status,
        connector_available=canvas.connector_available(),
        warnings=warnings,
        blockers=blockers,
        rollback_complete=rollback_complete,
        owner_decision_missing=owner_decision_missing,
    )

    log = audit_log or audit.GLOBAL_AUDIT_LOG
    log.record(record.artifact_id, 'validation', 'system', validation_status)
    log.record(record.artifact_id, 'approval', 'system', approval_status)
    log.record(record.artifact_id, 'readiness_check', 'system', readiness_status)

    return DeploymentReadinessRecord(
        deployment_id=deployment_id,
        artifact_id=record.artifact_id,
        artifact_kind=record.artifact_kind,
        artifact_title=record.title,
        target_system='canvas',
        target_course='Sandbox Course' if record.artifact_kind != 'daily_brief' else None,
        operation_type=rollback_mod.operation_for_artifact_kind(record.artifact_kind),
        approval_status=approval_status,
        health_status=health_status,
        validation_status=validation_status,
        teacher_decision_status=teacher_decision_status,
        readiness_status=readiness_status,
        blockers=blockers,
        warnings=warnings,
        rollback_plan=rollback_plan.rollback_id,
        created_at=now,
        updated_at=now,
    )


def build_readiness_records(
    db: p22.WorkstationDB,
    records: list[registry.ArtifactRegistryRecord],
    *,
    config: connector.CanvasConnectionConfig | None = None,
    audit_log: audit.DeploymentAuditLog | None = None,
) -> list[DeploymentReadinessRecord]:
    decisions.sync_invalidations(db, records)
    snapshots = decisions.build_approval_snapshots(db, records)
    queue_items = queue.build_queue_from_registry(records, snapshots)
    queue_by_id = {item.artifact_id: item for item in queue_items}
    readiness_records: list[DeploymentReadinessRecord] = []
    for record in records:
        latest = decisions.latest_decision(db, record.artifact_id)
        readiness_records.append(
            build_readiness_record(
                record,
                queue_by_id[record.artifact_id],
                latest,
                config=config,
                audit_log=audit_log,
            )
        )
    readiness_records.sort(key=lambda item: (item.readiness_status, item.artifact_kind, item.artifact_title or '', item.artifact_id))
    return readiness_records


def print_readiness_status_report(records: list[DeploymentReadinessRecord]) -> None:
    print('Deployment Readiness')
    print()
    ready = sum(1 for item in records if item.readiness_status == 'READY')
    blocked = sum(1 for item in records if item.readiness_status == 'BLOCKED')
    needs_review = sum(1 for item in records if item.readiness_status == 'NEEDS_REVIEW')
    not_eligible = sum(1 for item in records if item.readiness_status == 'NOT_ELIGIBLE')
    print('Ready:')
    print(ready)
    print()
    print('Blocked:')
    print(blocked)
    print()
    print('Needs review:')
    print(needs_review)
    print()
    print('Not eligible:')
    print(not_eligible)


def command_status_report(args: argparse.Namespace) -> int:
    db = p22.WorkstationDB(args.db)
    if not db.path.exists():
        db.migrate()
        db.seed_from_fixture()
        registry.seed_demo_week(db)
    records = registry.load_registry_from_db(db, args.weekly_plan_id)
    readiness_records = build_readiness_records(db, records)
    print_readiness_status_report(readiness_records)
    return 0


def command_self_test() -> int:
    temp_db = Path(p22.os.environ.get('DEPLOYMENT_READINESS_TEST_DB', f"{p22.os.environ.get('TMPDIR', '/tmp')}/deployment-readiness-self-test.sqlite3"))
    if temp_db.exists():
        temp_db.unlink()
    db = p22.WorkstationDB(temp_db)
    db.migrate()
    db.seed_from_fixture()
    wid = registry.seed_demo_week(db)

    before = [dict(row) for row in db.connect().execute('SELECT * FROM drafts WHERE weekly_plan_id=?', (wid,))]
    records = registry.load_registry_from_db(db, wid)
    audit_log = audit.DeploymentAuditLog()

    assignment = next(item for item in records if item.artifact_kind == 'assignment')
    announcement = next(item for item in records if item.artifact_kind == 'announcement' and item.subject != p22.HOMEROOM_NEWSLETTER_SUBJECT)

    decisions.record_decision(db, assignment, 'approve')
    decisions.record_decision(db, announcement, 'approve')

    readiness_records = build_readiness_records(db, records, audit_log=audit_log)
    after = [dict(row) for row in db.connect().execute('SELECT * FROM drafts WHERE weekly_plan_id=?', (wid,))]
    assert before == after, 'readiness evaluation must not mutate drafts'

    ready_items = [item for item in readiness_records if item.readiness_status == 'READY']
    assert ready_items, 'approved artifacts should reach READY in fake connector mode'

    blocked_record = registry.ArtifactRegistryRecord(
        artifact_id='blocked-demo',
        artifact_kind='newsletter_update',
        source_table=registry.SOURCE_TABLE,
        source_id='blocked-demo',
        title='Blocked Update',
        blockers=['verified page required'],
        teacher_approval_required=True,
        preview_only=True,
    )
    blocked_queue = queue.build_queue_item(blocked_record)
    blocked_readiness = build_readiness_record(blocked_record, blocked_queue, None, audit_log=audit_log)
    assert blocked_readiness.readiness_status == 'BLOCKED'

    missing_approval_record = registry.ArtifactRegistryRecord(
        artifact_id='missing-approval-demo',
        artifact_kind='announcement',
        source_table=registry.SOURCE_TABLE,
        source_id='missing-approval-demo',
        title='Missing Approval',
        teacher_approval_required=True,
        preview_only=True,
    )
    missing_queue = queue.build_queue_item(missing_approval_record)
    missing_readiness = build_readiness_record(missing_approval_record, missing_queue, None, audit_log=audit_log)
    assert missing_readiness.readiness_status in {'BLOCKED', 'NEEDS_REVIEW'}

    invalid_record = registry.ArtifactRegistryRecord(
        artifact_id='invalid-demo',
        artifact_kind='announcement',
        source_table=registry.SOURCE_TABLE,
        source_id='invalid-demo',
        title='Invalid Artifact',
        approved=True,
        blockers=['invalid content'],
    )
    invalid_queue = queue.build_queue_item(invalid_record)
    invalid_readiness = build_readiness_record(invalid_record, invalid_queue, None, audit_log=audit_log)
    assert invalid_readiness.readiness_status == 'BLOCKED'
    assert invalid_readiness.validation_status == 'FAIL'

    incomplete_rollback = rollback_mod.RollbackPlan(
        rollback_id='',
        deployment_id='dep-x',
        operation='create_announcement',
        created_state='',
        restore_action='',
        verification_steps=[],
    )
    assert incomplete_rollback.is_complete() is False

    disabled_cfg = connector.sandbox_connection_config()
    disabled_readiness = build_readiness_records(db, records, config=disabled_cfg, audit_log=audit_log)
    assert all(item.readiness_status == 'BLOCKED' for item in disabled_readiness)

    assert audit_log.count() > 0
    assert audit.audit_has_no_deployment_events(audit_log)

    print('PASS deployment readiness self-test')
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Canvas LLM deployment readiness gate')
    parser.add_argument('--db', default=str(p22.DEFAULT_DB_PATH))
    sub = parser.add_subparsers(dest='cmd', required=True)
    report = sub.add_parser('status-report')
    report.add_argument('--weekly-plan-id')
    report.set_defaults(func=command_status_report)
    sub.add_parser('self-test').set_defaults(func=lambda _args: command_self_test())
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == '__main__':
    raise SystemExit(main())
