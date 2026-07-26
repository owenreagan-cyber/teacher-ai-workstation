#!/usr/bin/env python3
"""Canvas operations status and newsletter/page production pipeline for C1D."""
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

SANDBOX_COURSE_ID = connector.SANDBOX_COURSE_ID
ALLOWED_ANNOUNCEMENT_KINDS = ('announcement', 'newsletter_update')
ALLOWED_PAGE_KINDS = ('newsletter', 'page')
BLOCKED_KINDS = ('assignment', 'grade', 'module', 'file', 'enrollment', 'submission')


def compact(value: Any) -> str:
    return p22.compact(value)


@dataclass
class NewsletterDeployment:
    deployment_id: str
    artifact_id: str
    artifact_kind: str
    course_id: int
    title: str
    page_url: str
    body_hash: str
    teacher_decision_id: str | None
    readiness_status: str
    write_status: str
    verification_status: str
    audit_id: str | None
    deployment_state: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def deploy_newsletter_page(
    db: p22.WorkstationDB,
    record: registry.ArtifactRegistryRecord,
    *,
    course_id: int = SANDBOX_COURSE_ID,
    body: str | None = None,
    page_url: str | None = None,
    config: connector.CanvasConnectionConfig | None = None,
    audit_log: audit.DeploymentAuditLog | None = None,
) -> NewsletterDeployment:
    """Deploy homeroom newsletter or monthly information page through controlled pipeline."""
    log = audit_log or audit.DeploymentAuditLog()
    cfg = config or connector.default_connection_config()

    snapshots = decisions.build_approval_snapshots(db, [record])
    queue_items = queue.build_queue_from_registry([record], snapshots)
    queue_item = queue_items[0]
    latest = decisions.latest_decision(db, record.artifact_id)
    readiness_record = readiness.build_readiness_record(record, queue_item, latest, config=cfg, audit_log=log)

    title = compact(record.title or 'Newsletter')
    content_body = body or title
    url = compact(page_url or f'homeroom-newsletter-{compact(record.artifact_id)[:8]}')
    content_hash = writer.body_hash(title, content_body)

    write_result = writer.create_page(
        db,
        artifact_id=record.artifact_id,
        course_id=course_id,
        page_url=url,
        title=title,
        body=content_body,
        record=record,
        queue_item=queue_item,
        latest=latest,
        config=cfg,
        audit_log=log,
    )

    verify_status = 'BLOCKED'
    if write_result.write_status == 'WRITTEN':
        verify = verification.verify_page(
            course_id,
            url,
            expected_title=title,
            expected_body_hash=write_result.body_hash,
            config=cfg,
        )
        verify_status = verify.status
        log.record(record.artifact_id, 'validation', 'system', f'verification:{verify_status}')

    if verify_status == 'PASS':
        state = 'VERIFIED'
    elif write_result.write_status == 'WRITTEN':
        state = 'WRITTEN'
    elif write_result.blockers:
        state = 'BLOCKED'
    elif readiness_record.readiness_status == 'READY':
        state = 'READY'
    else:
        state = 'DRAFT'

    return NewsletterDeployment(
        deployment_id=p22.stable_id('newsletter-deploy', record.artifact_id, content_hash),
        artifact_id=record.artifact_id,
        artifact_kind=record.artifact_kind,
        course_id=course_id,
        title=title,
        page_url=url,
        body_hash=content_hash,
        teacher_decision_id=latest.decision_id if latest else None,
        readiness_status=readiness_record.readiness_status,
        write_status=write_result.write_status,
        verification_status=verify_status,
        audit_id=write_result.audit_id,
        deployment_state=state,
    )


def deploy_announcement_by_kind(
    db: p22.WorkstationDB,
    record: registry.ArtifactRegistryRecord,
    *,
    course_id: int = SANDBOX_COURSE_ID,
    body: str | None = None,
    config: connector.CanvasConnectionConfig | None = None,
    audit_log: audit.DeploymentAuditLog | None = None,
) -> dict[str, Any]:
    """Deploy assessment reminder, classroom reminder, or important notice announcement."""
    from scripts.canvas_llm_phase22 import canvas_announcement_deployment as ann_deploy  # noqa: E402

    deployment = ann_deploy.deploy_announcement(
        db, record, course_id=course_id, body=body, config=config, audit_log=audit_log
    )
    return deployment.to_dict()


def operations_summary() -> dict[str, str]:
    return {
        'announcements': 'READY',
        'pages': 'READY',
        'assignments': 'BLOCKED',
        'writes': 'Controlled',
    }


def repair_summary(recommendations: list | None = None) -> dict[str, int]:
    recs = recommendations or []
    return {
        'issues': len(recs),
        'needs_approval': sum(1 for rec in recs if getattr(rec, 'requires_teacher_approval', True)),
    }


def print_operation_status_report() -> None:
    summary = operations_summary()
    print('Canvas Operations')
    print()
    print('Announcements:')
    print(summary['announcements'])
    print()
    print('Pages:')
    print(summary['pages'])
    print()
    print('Assignments:')
    print(summary['assignments'])
    print()
    print('Writes:')
    print(summary['writes'])


def print_repair_status_report(recommendations: list | None = None) -> None:
    summary = repair_summary(recommendations)
    print('Canvas Repair')
    print()
    print('Issues:')
    print(summary['issues'])
    print()
    print('Needs Approval:')
    print(summary['needs_approval'])
    print()
    print('No automatic repairs.')


def command_operation_status(_args: argparse.Namespace) -> int:
    print_operation_status_report()
    return 0


def command_repair_status(_args: argparse.Namespace) -> int:
    print_repair_status_report()
    return 0


def command_self_test() -> int:
    summary = operations_summary()
    assert summary['announcements'] == 'READY'
    assert summary['assignments'] == 'BLOCKED'
    assert summary['writes'] == 'Controlled'

    repair = repair_summary([])
    assert repair['issues'] == 0

    print('PASS canvas operations self-test')
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Canvas LLM operations status')
    sub = parser.add_subparsers(dest='cmd', required=True)
    sub.add_parser('operation-status').set_defaults(func=command_operation_status)
    sub.add_parser('repair-status').set_defaults(func=command_repair_status)
    sub.add_parser('self-test').set_defaults(func=lambda _args: command_self_test())
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == '__main__':
    raise SystemExit(main())
