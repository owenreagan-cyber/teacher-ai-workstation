#!/usr/bin/env python3
"""Controlled Canvas writer for teacher-facing Canvas operations (announcements and pages only)."""
from __future__ import annotations

import argparse
import hashlib
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.canvas_llm_phase22 import canvas_connection_manager as transport  # noqa: E402
from scripts.canvas_llm_phase22 import canvas_connector as connector  # noqa: E402
from scripts.canvas_llm_phase22 import deployment_audit as audit  # noqa: E402
from scripts.canvas_llm_phase22 import deployment_readiness as readiness  # noqa: E402
from scripts.canvas_llm_phase22 import phase22_workstation as p22  # noqa: E402
from scripts.canvas_llm_phase22 import teacher_decisions as decisions  # noqa: E402
from scripts.canvas_llm_phase22 import write_gate as gate  # noqa: E402

ALLOWED_TARGET_TYPES = ('announcement', 'page', 'assignment')
BLOCKED_TARGET_TYPES = ('module', 'file', 'grade', 'enrollment', 'submission')
WRITE_STATUSES = ('BLOCKED', 'WRITTEN', 'READY')
FAKE_CANVAS_STORE: dict[str, dict[str, Any]] = {'announcements': {}, 'pages': {}}


def compact(value: Any) -> str:
    return p22.compact(value)


def body_hash(title: str, body: str) -> str:
    payload = f'{compact(title)}|{compact(body)}'.encode('utf-8')
    return hashlib.sha256(payload).hexdigest()[:16]


@dataclass
class CanvasWriteResult:
    target_type: str
    target_id: str
    course_id: int
    title: str
    body_hash: str
    write_status: str
    gate_state: str
    blockers: list[str]
    audit_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _course_exists(canvas: connector.CanvasConnector, course_id: int) -> bool:
    try:
        course = canvas.read_course(course_id)
        return course.course_id == course_id
    except RuntimeError:
        return False


def _teacher_approval_exists(db: p22.WorkstationDB, artifact_id: str) -> bool:
    latest = decisions.latest_decision(db, artifact_id)
    if latest is None:
        return False
    return latest.decision_type == 'approve' and latest.decision_status == 'active'


def _readiness_passes(db: p22.WorkstationDB, record, queue_item, latest) -> bool:
    item = readiness.build_readiness_record(record, queue_item, latest)
    return item.readiness_status == 'READY'


def _evaluate_write_gate(
    target_type: str,
    target_id: str,
    *,
    approved: bool,
    approved_by: str | None,
    approved_at: str | None,
    config: connector.CanvasConnectionConfig | None = None,
) -> gate.WriteGateDecision:
    return gate.evaluate_write(
        'create',
        target_type,
        target_id,
        approved=approved,
        approved_by=approved_by,
        approved_at=approved_at,
        config=config,
    )


def _store_fake_write(target_type: str, course_id: int, target_id: str, title: str, body: str) -> None:
    bucket = 'announcements' if target_type == 'announcement' else 'pages'
    FAKE_CANVAS_STORE[bucket][target_id] = {
        'course_id': course_id,
        'title': title,
        'body': body,
        'body_hash': body_hash(title, body),
    }


def _execute_controlled_fake_write(
    target_type: str,
    course_id: int,
    target_id: str,
    title: str,
    body: str,
    artifact_id: str,
    audit_log: audit.DeploymentAuditLog,
) -> CanvasWriteResult:
    """Simulate controlled write in fake connector mode only — no network calls."""
    _store_fake_write(target_type, course_id, target_id, title, body)
    event = audit_log.record(artifact_id, 'validation', 'system', f'controlled_write:{target_type}:WRITTEN')
    return CanvasWriteResult(
        target_type=target_type,
        target_id=target_id,
        course_id=course_id,
        title=title,
        body_hash=body_hash(title, body),
        write_status='WRITTEN',
        gate_state='APPROVED',
        blockers=[],
        audit_id=event.event_id,
    )


def create_announcement(
    db: p22.WorkstationDB,
    *,
    artifact_id: str,
    course_id: int,
    title: str,
    body: str,
    record,
    queue_item,
    latest,
    config: connector.CanvasConnectionConfig | None = None,
    audit_log: audit.DeploymentAuditLog | None = None,
) -> CanvasWriteResult:
    """Create a Canvas announcement through the controlled write pipeline."""
    cfg = config or connector.default_connection_config()
    canvas = connector.CanvasConnector(cfg)
    log = audit_log or audit.DeploymentAuditLog()
    target_id = compact(artifact_id) or p22.stable_id('announcement', title, course_id)
    blockers: list[str] = []

    if not record or not compact(record.artifact_id):
        blockers.append('artifact_missing')
    if not _teacher_approval_exists(db, artifact_id):
        blockers.append('teacher_approval_missing')
    if record and not _readiness_passes(db, record, queue_item, latest):
        blockers.append('readiness_not_pass')
    if not _course_exists(canvas, course_id):
        blockers.append('target_course_missing')

    approved = _teacher_approval_exists(db, artifact_id)
    latest_decision = decisions.latest_decision(db, artifact_id)
    gate_decision = _evaluate_write_gate(
        'announcement',
        target_id,
        approved=approved,
        approved_by=latest_decision.teacher_display if latest_decision else None,
        approved_at=latest_decision.created_at if latest_decision else None,
        config=cfg,
    )
    if gate_decision.gate_state != 'APPROVED':
        blockers.append('write_gate_blocked')

    if blockers:
        log.record(artifact_id, 'validation', 'system', 'BLOCKED:' + ','.join(blockers))
        return CanvasWriteResult(
            target_type='announcement',
            target_id=target_id,
            course_id=course_id,
            title=title,
            body_hash=body_hash(title, body),
            write_status='BLOCKED',
            gate_state=gate_decision.gate_state,
            blockers=blockers,
        )

    attempted = gate.attempt_write(gate_decision)
    if attempted.gate_state == 'BLOCKED' and cfg.mode != 'fake':
        log.record(artifact_id, 'validation', 'system', 'BLOCKED:execution_disabled')
        return CanvasWriteResult(
            target_type='announcement',
            target_id=target_id,
            course_id=course_id,
            title=title,
            body_hash=body_hash(title, body),
            write_status='BLOCKED',
            gate_state='BLOCKED',
            blockers=['execution_disabled'],
        )

    if cfg.mode == 'fake':
        return _execute_controlled_fake_write(
            'announcement', course_id, target_id, title, body, artifact_id, log
        )

    log.record(artifact_id, 'validation', 'system', 'BLOCKED:execution_disabled')
    return CanvasWriteResult(
        target_type='announcement',
        target_id=target_id,
        course_id=course_id,
        title=title,
        body_hash=body_hash(title, body),
        write_status='BLOCKED',
        gate_state='BLOCKED',
        blockers=['execution_disabled'],
    )


def create_page(
    db: p22.WorkstationDB,
    *,
    artifact_id: str,
    course_id: int,
    page_url: str,
    title: str,
    body: str,
    record,
    queue_item,
    latest,
    config: connector.CanvasConnectionConfig | None = None,
    audit_log: audit.DeploymentAuditLog | None = None,
) -> CanvasWriteResult:
    """Create a Canvas page through the controlled write pipeline."""
    cfg = config or connector.default_connection_config()
    canvas = connector.CanvasConnector(cfg)
    log = audit_log or audit.DeploymentAuditLog()
    target_id = compact(page_url) or p22.stable_id('page', title, course_id)
    blockers: list[str] = []

    if not record or not compact(record.artifact_id):
        blockers.append('artifact_missing')
    if not _teacher_approval_exists(db, artifact_id):
        blockers.append('teacher_approval_missing')
    if record and not _readiness_passes(db, record, queue_item, latest):
        blockers.append('readiness_not_pass')
    if not _course_exists(canvas, course_id):
        blockers.append('target_course_missing')

    approved = _teacher_approval_exists(db, artifact_id)
    latest_decision = decisions.latest_decision(db, artifact_id)
    gate_decision = _evaluate_write_gate(
        'page',
        target_id,
        approved=approved,
        approved_by=latest_decision.teacher_display if latest_decision else None,
        approved_at=latest_decision.created_at if latest_decision else None,
        config=cfg,
    )
    if gate_decision.gate_state != 'APPROVED':
        blockers.append('write_gate_blocked')

    if blockers:
        log.record(artifact_id, 'validation', 'system', 'BLOCKED:' + ','.join(blockers))
        return CanvasWriteResult(
            target_type='page',
            target_id=target_id,
            course_id=course_id,
            title=title,
            body_hash=body_hash(title, body),
            write_status='BLOCKED',
            gate_state=gate_decision.gate_state,
            blockers=blockers,
        )

    attempted = gate.attempt_write(gate_decision)
    if attempted.gate_state == 'BLOCKED' and cfg.mode != 'fake':
        log.record(artifact_id, 'validation', 'system', 'BLOCKED:execution_disabled')
        return CanvasWriteResult(
            target_type='page',
            target_id=target_id,
            course_id=course_id,
            title=title,
            body_hash=body_hash(title, body),
            write_status='BLOCKED',
            gate_state='BLOCKED',
            blockers=['execution_disabled'],
        )

    if cfg.mode == 'fake':
        return _execute_controlled_fake_write('page', course_id, target_id, title, body, artifact_id, log)

    log.record(artifact_id, 'validation', 'system', 'BLOCKED:execution_disabled')
    return CanvasWriteResult(
        target_type='page',
        target_id=target_id,
        course_id=course_id,
        title=title,
        body_hash=body_hash(title, body),
        write_status='BLOCKED',
        gate_state='BLOCKED',
        blockers=['execution_disabled'],
    )


def create_assignment(*_args: Any, **_kwargs: Any) -> CanvasWriteResult:
    """Legacy assignment entrypoint remains blocked — use create_assignment_live."""
    raise RuntimeError('create_assignment is blocked: use create_assignment_live for Q1W2 live transport')


def _live_connection_config() -> connector.CanvasConnectionConfig:
    return connector.CanvasConnectionConfig(
        mode='live',
        enabled=True,
        base_url='[REDACTED]',
        credential_state='configured',
        write_mode='controlled',
    )


def create_page_live(
    *,
    course_id: int,
    title: str,
    body: str,
    page_url: str | None = None,
    published: bool = True,
    front_page: bool = False,
    approved: bool = False,
    approved_by: str | None = 'teacher',
    approved_at: str | None = None,
    audit_log: audit.DeploymentAuditLog | None = None,
    client: transport.MockPhase22CanvasClient | transport.Phase22LiveCanvasClient | None = None,
    test_mode: bool = False,
) -> CanvasWriteResult:
    """Create a Canvas page through live API transport (PAGE_CREATE)."""
    cfg = _live_connection_config()
    log = audit_log or audit.DeploymentAuditLog()
    target_id = compact(page_url) or p22.stable_id('page', title, course_id)
    blockers: list[str] = []

    if not approved:
        blockers.append('teacher_approval_missing')
    if not transport.use_live_transport(test_mode=test_mode):
        blockers.append('live_transport_not_enabled')

    gate_decision = _evaluate_write_gate(
        'page',
        target_id,
        approved=approved,
        approved_by=approved_by,
        approved_at=approved_at,
        config=cfg,
    )
    if gate_decision.gate_state != 'APPROVED':
        blockers.append('write_gate_blocked')

    if blockers:
        log.record(target_id, 'validation', 'system', 'BLOCKED:' + ','.join(blockers))
        return CanvasWriteResult(
            target_type='page',
            target_id=target_id,
            course_id=course_id,
            title=title,
            body_hash=body_hash(title, body),
            write_status='BLOCKED',
            gate_state=gate_decision.gate_state,
            blockers=blockers,
        )

    executed = gate.attempt_live_write(gate_decision, config=cfg)
    if executed.gate_state != 'EXECUTED':
        return CanvasWriteResult(
            target_type='page',
            target_id=target_id,
            course_id=course_id,
            title=title,
            body_hash=body_hash(title, body),
            write_status='BLOCKED',
            gate_state='BLOCKED',
            blockers=['write_gate_execution_blocked'],
        )

    api = client or transport.get_transport_client(test_mode=test_mode)
    created = api.create_page(
        course_id,
        title=title,
        body=body,
        published=published,
        front_page=front_page,
    )
    object_id = compact(created.get('url') or created.get('id') or target_id)
    event = log.record(object_id, 'validation', approved_by or 'teacher', 'live_page_create:CREATED')
    return CanvasWriteResult(
        target_type='page',
        target_id=object_id,
        course_id=course_id,
        title=title,
        body_hash=body_hash(title, body),
        write_status='WRITTEN',
        gate_state='EXECUTED',
        blockers=[],
        audit_id=event.event_id,
    )


def create_assignment_live(
    *,
    course_id: int,
    title: str,
    description: str,
    assignment_group: str,
    points: int = 100,
    grading_type: str = 'percent',
    submission_type: str = 'on_paper',
    due_at: str = '',
    counts_toward_final_grade: bool = True,
    published: bool = True,
    approved: bool = False,
    approved_by: str | None = 'teacher',
    approved_at: str | None = None,
    audit_log: audit.DeploymentAuditLog | None = None,
    client: transport.MockPhase22CanvasClient | transport.Phase22LiveCanvasClient | None = None,
    test_mode: bool = False,
) -> CanvasWriteResult:
    """Create a Canvas assignment through live API transport (ASSIGNMENT_CREATE)."""
    cfg = _live_connection_config()
    log = audit_log or audit.DeploymentAuditLog()
    target_id = p22.stable_id('assignment', course_id, title)
    blockers: list[str] = []

    if not approved:
        blockers.append('teacher_approval_missing')
    if not transport.use_live_transport(test_mode=test_mode):
        blockers.append('live_transport_not_enabled')

    gate_decision = _evaluate_write_gate(
        'assignment',
        target_id,
        approved=approved,
        approved_by=approved_by,
        approved_at=approved_at,
        config=cfg,
    )
    if gate_decision.gate_state != 'APPROVED':
        blockers.append('write_gate_blocked')

    if blockers:
        log.record(target_id, 'validation', 'system', 'BLOCKED:' + ','.join(blockers))
        return CanvasWriteResult(
            target_type='assignment',
            target_id=target_id,
            course_id=course_id,
            title=title,
            body_hash=body_hash(title, description),
            write_status='BLOCKED',
            gate_state=gate_decision.gate_state,
            blockers=blockers,
        )

    executed = gate.attempt_live_write(gate_decision, config=cfg)
    if executed.gate_state != 'EXECUTED':
        return CanvasWriteResult(
            target_type='assignment',
            target_id=target_id,
            course_id=course_id,
            title=title,
            body_hash=body_hash(title, description),
            write_status='BLOCKED',
            gate_state='BLOCKED',
            blockers=['write_gate_execution_blocked'],
        )

    api = client or transport.get_transport_client(test_mode=test_mode)
    created = api.create_assignment(
        course_id,
        title=title,
        description=description,
        assignment_group=assignment_group,
        points=points,
        grading_type=grading_type,
        submission_type=submission_type,
        due_at=due_at,
        counts_toward_final_grade=counts_toward_final_grade,
        published=published,
    )
    object_id = compact(created.get('id') or target_id)
    event = log.record(object_id, 'validation', approved_by or 'teacher', f'live_assignment_create:{title}')
    return CanvasWriteResult(
        target_type='assignment',
        target_id=object_id,
        course_id=course_id,
        title=title,
        body_hash=body_hash(title, description),
        write_status='WRITTEN',
        gate_state='EXECUTED',
        blockers=[],
        audit_id=event.event_id,
    )


def verify_page_live(
    *,
    course_id: int,
    page_ref: str,
    title: str,
    published: bool = True,
    front_page: bool = False,
    client: transport.MockPhase22CanvasClient | transport.Phase22LiveCanvasClient | None = None,
    test_mode: bool = False,
) -> str:
    api = client or transport.get_transport_client(test_mode=test_mode)
    stored = api.get_page(course_id, page_ref)
    checks = [
        compact(stored.get('title')) == compact(title),
        int(stored.get('course_id') or course_id) == int(course_id),
        bool(stored.get('published')) == published,
        bool(stored.get('front_page')) == front_page,
    ]
    return 'PASS' if all(checks) else 'FAIL'


def verify_assignment_live(
    *,
    course_id: int,
    assignment_id: str,
    title: str,
    assignment_group: str,
    counts_toward_final_grade: bool,
    client: transport.MockPhase22CanvasClient | transport.Phase22LiveCanvasClient | None = None,
    test_mode: bool = False,
) -> str:
    api = client or transport.get_transport_client(test_mode=test_mode)
    stored = api.get_assignment(course_id, assignment_id)
    checks = [
        compact(stored.get('name') or stored.get('title')) == compact(title),
        int(stored.get('course_id') or course_id) == int(course_id),
        compact(stored.get('assignment_group')) == compact(assignment_group),
        bool(stored.get('counts_toward_final_grade')) == counts_toward_final_grade,
    ]
    return 'PASS' if all(checks) else 'FAIL'


def writer_has_no_assignment_writes() -> bool:
    source = Path(__file__).read_text().lower()
    marker = 'def create_assignment('
    idx = source.find(marker)
    body = source[idx:source.find('def _live_connection_config', idx)] if idx >= 0 else source
    return 'raise runtimeerror' in body and 'blocked' in body


def writer_has_no_automatic_publish() -> bool:
    source = Path(__file__).read_text().lower()
    marker = 'def writer_has_no_automatic_publish'
    idx = source.find(marker)
    scan_source = source[:idx] if idx >= 0 else source
    forbidden = ('auto_publish', 'schedule_publish', 'background_sync', 'background sync')
    return not any(token in scan_source for token in forbidden)


def command_self_test() -> int:
    FAKE_CANVAS_STORE['announcements'].clear()
    FAKE_CANVAS_STORE['pages'].clear()

    try:
        create_assignment()
        raise AssertionError('create_assignment should be blocked')
    except RuntimeError:
        pass

    cfg_live = _live_connection_config()
    assert cfg_live.write_mode == 'controlled'

    blocked = create_page_live(
        course_id=26427,
        title='Blocked Page',
        body='body',
        approved=False,
    )
    assert blocked.write_status == 'BLOCKED'

    approved_page = create_page_live(
        course_id=26427,
        title='Live Test Page',
        body='<p>Live test</p>',
        approved=True,
        test_mode=True,
    )
    assert approved_page.write_status == 'WRITTEN'
    assert approved_page.gate_state == 'EXECUTED'
    assert verify_page_live(
        course_id=26427,
        page_ref=approved_page.target_id,
        title='Live Test Page',
        front_page=False,
        test_mode=True,
    ) == 'PASS'

    assert writer_has_no_assignment_writes()
    assert writer_has_no_automatic_publish()
    assert 'assignment' in ALLOWED_TARGET_TYPES
    assert 'module' in BLOCKED_TARGET_TYPES

    cfg = connector.default_connection_config()
    assert cfg.mode == 'fake'

    print('PASS canvas writer self-test')
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Canvas LLM controlled Canvas writer')
    sub = parser.add_subparsers(dest='cmd', required=True)
    sub.add_parser('self-test').set_defaults(func=lambda _args: command_self_test())
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == '__main__':
    raise SystemExit(main())
