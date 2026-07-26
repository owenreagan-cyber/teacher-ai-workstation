#!/usr/bin/env python3
"""Deployment planner for approved Canvas LLM artifacts. Execution remains disabled."""
from __future__ import annotations

import argparse
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.canvas_llm_phase22 import artifact_registry as registry  # noqa: E402
from scripts.canvas_llm_phase22 import canvas_connector as connector  # noqa: E402
from scripts.canvas_llm_phase22 import deployment_readiness as readiness  # noqa: E402
from scripts.canvas_llm_phase22 import phase22_workstation as p22  # noqa: E402
from scripts.canvas_llm_phase22 import rollback as rollback_mod  # noqa: E402

PLAN_STATES = ('DRAFT', 'READY', 'BLOCKED', 'EXECUTED')
SANDBOX_COURSE_ID = connector.SANDBOX_COURSE_ID


def compact(value: Any) -> str:
    return p22.compact(value)


@dataclass
class DeploymentPlan:
    plan_id: str
    artifact_id: str
    operation: str
    target: dict[str, Any]
    preflight_checks: list[str]
    rollback_steps: list[str]
    execution_state: str = 'DRAFT'

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def target_for_record(record: registry.ArtifactRegistryRecord) -> dict[str, Any]:
    return {
        'system': 'canvas',
        'course_id': SANDBOX_COURSE_ID,
        'course_label': 'Sandbox Course',
        'artifact_kind': record.artifact_kind,
        'artifact_title': record.title,
    }


def build_deployment_plan(
    record: registry.ArtifactRegistryRecord,
    readiness_record: readiness.DeploymentReadinessRecord,
    rollback_plan: rollback_mod.RollbackPlan,
) -> DeploymentPlan:
    operation = rollback_mod.operation_for_artifact_kind(record.artifact_kind)
    plan_id = p22.stable_id('deployment-plan', record.artifact_id, operation)
    preflight = [
        f'validation:{readiness_record.validation_status}',
        f'health:{readiness_record.health_status}',
        f'approval:{readiness_record.approval_status}',
        f'teacher_decision:{readiness_record.teacher_decision_status}',
        f'readiness:{readiness_record.readiness_status}',
        'execution:disabled',
    ]
    execution_state = 'BLOCKED'
    if readiness_record.readiness_status == 'READY':
        execution_state = 'READY'
    elif readiness_record.readiness_status in {'NEEDS_REVIEW', 'NOT_ELIGIBLE'}:
        execution_state = 'DRAFT'
    return DeploymentPlan(
        plan_id=plan_id,
        artifact_id=record.artifact_id,
        operation=operation,
        target=target_for_record(record),
        preflight_checks=preflight,
        rollback_steps=list(rollback_plan.verification_steps),
        execution_state=execution_state,
    )


def build_sandbox_deployment_packet(
    record: registry.ArtifactRegistryRecord,
    readiness_record: readiness.DeploymentReadinessRecord,
    plan: DeploymentPlan,
) -> dict[str, Any]:
    return {
        'packet_type': 'Sandbox Deployment Packet',
        'artifact': {
            'artifact_id': record.artifact_id,
            'artifact_kind': record.artifact_kind,
            'artifact_title': record.title or record.artifact_id,
        },
        'target': plan.target,
        'operation': 'Create Announcement' if record.artifact_kind == 'announcement' else plan.operation.replace('_', ' ').title(),
        'preflight': 'PASS' if readiness_record.validation_status == 'PASS' and readiness_record.health_status == 'PASS' else readiness_record.readiness_status,
        'approval': 'PASS' if readiness_record.approval_status == 'PASS' else readiness_record.approval_status,
        'connector': 'BLOCKED' if not connector.CanvasConnector().connector_available() or readiness_record.readiness_status != 'READY' else 'READY',
        'result': 'READY FOR HUMAN-AUTHORIZED TEST' if readiness_record.readiness_status == 'READY' else 'BLOCKED',
        'plan_id': plan.plan_id,
        'execution_state': plan.execution_state,
    }


def print_deployment_plan_status_report(plans: list[DeploymentPlan]) -> None:
    print('Deployment Plan')
    print()
    ready = sum(1 for plan in plans if plan.execution_state == 'READY')
    blocked = sum(1 for plan in plans if plan.execution_state == 'BLOCKED')
    draft = sum(1 for plan in plans if plan.execution_state == 'DRAFT')
    print('Ready:')
    print(ready)
    print()
    print('Blocked:')
    print(blocked)
    print()
    print('Draft:')
    print(draft)


def command_status_report(args: argparse.Namespace) -> int:
    db = p22.WorkstationDB(args.db)
    if not db.path.exists():
        db.migrate()
        db.seed_from_fixture()
        registry.seed_demo_week(db)
    records = registry.load_registry_from_db(db, args.weekly_plan_id)
    readiness_records = readiness.build_readiness_records(db, records)
    plans = []
    for item in readiness_records:
        record = next(r for r in records if r.artifact_id == item.artifact_id)
        rollback_plan = rollback_mod.generate_rollback_plan(item.deployment_id, record.artifact_id, record.artifact_kind)
        plans.append(build_deployment_plan(record, item, rollback_plan))
    print_deployment_plan_status_report(plans)
    return 0


def command_self_test() -> int:
    record = registry.ArtifactRegistryRecord(
        artifact_id='packet-demo',
        artifact_kind='announcement',
        source_table=registry.SOURCE_TABLE,
        source_id='packet-demo',
        title='SM5 Assessment Announcement',
        approval_state='Approved',
        teacher_approval_required=True,
        preview_only=True,
    )
    readiness_record = readiness.DeploymentReadinessRecord(
        deployment_id='dep-packet-demo',
        artifact_id=record.artifact_id,
        artifact_kind=record.artifact_kind,
        artifact_title=record.title,
        target_system='canvas',
        target_course='Sandbox Course',
        operation_type='create_announcement',
        approval_status='PASS',
        health_status='PASS',
        validation_status='PASS',
        teacher_decision_status='PASS',
        readiness_status='READY',
        blockers=[],
        warnings=[],
        rollback_plan='rollback-plan-demo',
        created_at='2026-07-25T00:00:00Z',
        updated_at='2026-07-25T00:00:00Z',
    )
    rollback_plan = rollback_mod.generate_rollback_plan(readiness_record.deployment_id, record.artifact_id, record.artifact_kind)
    plan = build_deployment_plan(record, readiness_record, rollback_plan)
    assert plan.execution_state in PLAN_STATES
    assert plan.execution_state != 'EXECUTED'

    packet = build_sandbox_deployment_packet(record, readiness_record, plan)
    assert packet['artifact']['artifact_title'] == 'SM5 Assessment Announcement'
    assert packet['target']['course_label'] == 'Sandbox Course'
    assert packet['connector'] in {'BLOCKED', 'READY'}

    print('PASS deployment planner self-test')
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Canvas LLM deployment planner')
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
