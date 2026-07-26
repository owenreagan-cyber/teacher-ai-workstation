#!/usr/bin/env python3
"""Canvas announcement deployment flow for C1A teacher-facing Canvas operations."""
from __future__ import annotations

import argparse
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.canvas_llm_phase22 import approval_queue as queue  # noqa: E402
from scripts.canvas_llm_phase22 import artifact_registry as registry  # noqa: E402
from scripts.canvas_llm_phase22 import canvas_connector as connector  # noqa: E402
from scripts.canvas_llm_phase22 import canvas_verification as verification  # noqa: E402
from scripts.canvas_llm_phase22 import canvas_writer as writer  # noqa: E402
from scripts.canvas_llm_phase22 import deployment_audit as audit  # noqa: E402
from scripts.canvas_llm_phase22 import deployment_readiness as readiness  # noqa: E402
from scripts.canvas_llm_phase22 import phase22_workstation as p22  # noqa: E402
from scripts.canvas_llm_phase22 import teacher_decisions as decisions  # noqa: E402

DEPLOYMENT_STATES = ('DRAFT', 'READY', 'BLOCKED', 'WRITTEN', 'VERIFIED', 'ROLLED_BACK')
SANDBOX_COURSE_ID = connector.SANDBOX_COURSE_ID


def compact(value: Any) -> str:
    return p22.compact(value)


@dataclass
class CanvasAnnouncementDeployment:
    deployment_id: str
    artifact_id: str
    course_id: int
    title: str
    body_hash: str
    approval_state: str
    teacher_decision_id: str | None
    readiness_status: str
    write_status: str
    verification_status: str
    audit_id: str | None
    deployment_state: str = 'DRAFT'

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def derive_deployment_state(
    *,
    readiness_status: str,
    write_status: str,
    verification_status: str,
    blockers: list[str],
) -> str:
    if verification_status == 'PASS':
        return 'VERIFIED'
    if write_status == 'WRITTEN':
        return 'WRITTEN'
    if blockers:
        return 'BLOCKED'
    if readiness_status == 'READY':
        return 'READY'
    return 'DRAFT'


def deploy_announcement(
    db: p22.WorkstationDB,
    record: registry.ArtifactRegistryRecord,
    *,
    course_id: int = SANDBOX_COURSE_ID,
    body: str | None = None,
    config: connector.CanvasConnectionConfig | None = None,
    audit_log: audit.DeploymentAuditLog | None = None,
) -> CanvasAnnouncementDeployment:
    """Run the full announcement deployment pipeline."""
    log = audit_log or audit.DeploymentAuditLog()
    cfg = config or connector.default_connection_config()

    snapshots = decisions.build_approval_snapshots(db, [record])
    queue_items = queue.build_queue_from_registry([record], snapshots)
    queue_item = queue_items[0]
    latest = decisions.latest_decision(db, record.artifact_id)

    readiness_record = readiness.build_readiness_record(record, queue_item, latest, config=cfg, audit_log=log)
    approval_state = decisions.derive_teacher_approval_state(record, latest)
    title = compact(record.title or 'Announcement')
    content_body = body or title
    content_hash = writer.body_hash(title, content_body)

    write_result = writer.create_announcement(
        db,
        artifact_id=record.artifact_id,
        course_id=course_id,
        title=title,
        body=content_body,
        record=record,
        queue_item=queue_item,
        latest=latest,
        config=cfg,
        audit_log=log,
    )

    verify_result = verification.VerificationResult(
        target_type='announcement',
        target_id=write_result.target_id,
        course_id=course_id,
        status='BLOCKED',
        checks=[],
        blockers=['not_written'],
    )
    if write_result.write_status == 'WRITTEN':
        verify_result = verification.verify_announcement(
            course_id,
            write_result.target_id,
            expected_title=title,
            expected_body_hash=write_result.body_hash,
            config=cfg,
        )
        log.record(record.artifact_id, 'validation', 'system', f'verification:{verify_result.status}')

    blockers = list(write_result.blockers)
    if verify_result.status == 'FAIL':
        blockers.append('verification_failed')

    deployment_state = derive_deployment_state(
        readiness_status=readiness_record.readiness_status,
        write_status=write_result.write_status,
        verification_status=verify_result.status,
        blockers=blockers,
    )

    return CanvasAnnouncementDeployment(
        deployment_id=p22.stable_id('ann-deploy', record.artifact_id, content_hash),
        artifact_id=record.artifact_id,
        course_id=course_id,
        title=title,
        body_hash=content_hash,
        approval_state=approval_state,
        teacher_decision_id=latest.decision_id if latest else None,
        readiness_status=readiness_record.readiness_status,
        write_status=write_result.write_status,
        verification_status=verify_result.status,
        audit_id=write_result.audit_id,
        deployment_state=deployment_state,
    )


def command_self_test() -> int:
    import tempfile

    from scripts.canvas_llm_phase22 import artifact_registry as reg  # noqa: E402
    from scripts.canvas_llm_phase22 import canvas_writer as cw  # noqa: E402

    cw.FAKE_CANVAS_STORE['announcements'].clear()
    with tempfile.NamedTemporaryFile(suffix='.sqlite3', delete=False) as tmp:
        db_path = Path(tmp.name)
    db = p22.WorkstationDB(db_path)
    db.migrate()
    db.seed_from_fixture()
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

    records = reg.load_registry_from_db(db, wid)
    announcements = [r for r in records if r.artifact_kind == 'announcement']
    assert announcements, 'expected at least one announcement artifact'
    announcement = announcements[0]

    blocked = deploy_announcement(db, announcement)
    assert blocked.deployment_state == 'BLOCKED'
    assert blocked.write_status == 'BLOCKED'

    decisions.record_decision(db, announcement, 'approve', teacher_display='Teacher', note='approved for test')

    deployed = deploy_announcement(db, announcement, body='Assessment reminder for Tuesday')
    assert deployed.write_status == 'WRITTEN'
    assert deployed.deployment_state in {'WRITTEN', 'VERIFIED'}
    assert deployed.teacher_decision_id is not None

    db_path.unlink(missing_ok=True)
    print('PASS canvas announcement deployment self-test')
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Canvas LLM announcement deployment flow')
    sub = parser.add_subparsers(dest='cmd', required=True)
    sub.add_parser('self-test').set_defaults(func=lambda _args: command_self_test())
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == '__main__':
    raise SystemExit(main())
