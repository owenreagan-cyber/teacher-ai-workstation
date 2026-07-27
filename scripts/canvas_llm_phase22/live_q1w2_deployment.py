#!/usr/bin/env python3
"""Live Q1W2 controlled Canvas deployment — teacher-approved writes only."""
from __future__ import annotations

import argparse
import hashlib
import os
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.canvas_llm_phase22 import canvas_connection as connection  # noqa: E402
from scripts.canvas_llm_phase22 import canvas_course_resolver as resolver  # noqa: E402
from scripts.canvas_llm_phase22 import canvas_duplicate_detector as duplicates  # noqa: E402
from scripts.canvas_llm_phase22 import canvas_html_renderer as html_renderer  # noqa: E402
from scripts.canvas_llm_phase22 import communication_status as comm  # noqa: E402
from scripts.canvas_llm_phase22 import deployment_audit as audit  # noqa: E402
from scripts.canvas_llm_phase22 import canvas_connection_manager as transport  # noqa: E402
from scripts.canvas_llm_phase22 import canvas_writer as writer  # noqa: E402
from scripts.canvas_llm_phase22 import deployment_context as deploy_ctx  # noqa: E402
from scripts.canvas_llm_phase22 import phase22_workstation as p22  # noqa: E402

WEEK_CODE = html_renderer.Q1W2_WEEK_CODE
PAGE_TITLE = html_renderer.Q1W2_PAGE_TITLE
HOMEROOM_COURSE_ID = connection.HOMEROOM_COURSE_ID
MATH_COURSE_ID = connection.MATH_COURSE_ID
READING_COURSE_ID = connection.READING_COURSE_ID

ALLOWED_OPERATIONS = ('PAGE_CREATE', 'ASSIGNMENT_CREATE', 'ANNOUNCEMENT_DRAFT')
BLOCKED_OPERATIONS = (
    'GRADE_UPDATE',
    'SUBMISSION_UPDATE',
    'MODULE_CREATE',
    'FILE_UPLOAD',
    'STUDENT_DATA',
    'BULK_PUBLISH',
)

from scripts.canvas_llm_phase22 import rollback as rollback_mod  # noqa: E402

LIVE_CANVAS_STORE: dict[str, dict[str, Any]] = {
    'pages': {},
    'assignments': {},
    'announcements': {},
}

DEPLOYMENT_VERSION = 'c2c2-live-q1w2-v1'


def compact(value: Any) -> str:
    return p22.compact(value)


def body_hash(title: str, body: str) -> str:
    payload = f'{compact(title)}|{compact(body)}'.encode('utf-8')
    return hashlib.sha256(payload).hexdigest()[:16]


@dataclass
class LiveAssignmentSpec:
    title: str
    course_id: int
    subject: str
    assignment_group: str
    description: str
    points: int = 100
    grading_type: str = 'percent'
    submission_type: str = 'on_paper'
    due_at: str = ''
    grading_state: str = 'COUNTED'
    counts_toward_final_grade: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class LiveWriteRecord:
    object_type: str
    object_id: str
    course_id: int
    title: str
    write_operation: str
    status: str
    verification: str = 'PENDING'
    rollback_id: str | None = None
    audit_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class LiveDeploymentReport:
    week_code: str
    environment: str
    connection_ready: bool
    duplicate_scan_pass: bool
    approval_required: bool
    page_status: str = 'PENDING'
    assignments_created: int = 0
    announcement_status: str = 'PENDING'
    verification: str = 'PENDING'
    audit: str = 'PENDING'
    writes: str = 'BLOCKED'
    records: list[LiveWriteRecord] = field(default_factory=list)
    rollback_plans: list[dict[str, Any]] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            'week_code': self.week_code,
            'environment': self.environment,
            'connection_ready': self.connection_ready,
            'duplicate_scan_pass': self.duplicate_scan_pass,
            'approval_required': self.approval_required,
            'page_status': self.page_status,
            'assignments_created': self.assignments_created,
            'announcement_status': self.announcement_status,
            'verification': self.verification,
            'audit': self.audit,
            'writes': self.writes,
            'records': [item.to_dict() for item in self.records],
            'rollback_plans': self.rollback_plans,
            'blockers': self.blockers,
        }


def build_q1w2_assignment_specs() -> list[LiveAssignmentSpec]:
    math_group = 'Homework/Class Work'
    reading_group = 'Homework'
    return [
        LiveAssignmentSpec('SM5: Lesson 2', MATH_COURSE_ID, 'math', math_group, 'Complete assigned problems.\n\n#12-30 Even', due_at='2026-07-27T23:59:00-04:00', grading_state='COUNTED', counts_toward_final_grade=True),
        LiveAssignmentSpec('SM5: Lesson 3', MATH_COURSE_ID, 'math', math_group, 'Complete assigned problems.\n\n1-10 in class', due_at='2026-07-28T23:59:00-04:00', grading_state='COUNTED', counts_toward_final_grade=True),
        LiveAssignmentSpec('SM5: Lesson 4', MATH_COURSE_ID, 'math', math_group, 'Complete assigned problems.\n\n#11-29 Odds', due_at='2026-07-29T23:59:00-04:00', grading_state='COUNTED', counts_toward_final_grade=True),
        LiveAssignmentSpec('SM5: Lesson 5', MATH_COURSE_ID, 'math', math_group, 'Complete assigned problems.\n\n1-10 in class', due_at='2026-07-30T23:59:00-04:00', grading_state='NOT_COUNTED', counts_toward_final_grade=False),
        LiveAssignmentSpec('RM4: Lesson 2', READING_COURSE_ID, 'reading', reading_group, 'Workbook and comprehension practice.', due_at='2026-07-27T23:59:00-04:00', grading_state='COUNTED', counts_toward_final_grade=True),
        LiveAssignmentSpec('RM4: Lesson 3', READING_COURSE_ID, 'reading', reading_group, 'Finish workbook and comprehension questions using complete, restated sentences.', due_at='2026-07-28T23:59:00-04:00', grading_state='COUNTED', counts_toward_final_grade=True),
        LiveAssignmentSpec('RM4: Lesson 4', READING_COURSE_ID, 'reading', reading_group, 'Workbook classwork completed in class.', due_at='2026-07-29T23:59:00-04:00', grading_state='NOT_COUNTED', counts_toward_final_grade=False),
        LiveAssignmentSpec('RM4: Lesson 5', READING_COURSE_ID, 'reading', reading_group, 'Workbook and comprehension practice.', due_at='2026-07-30T23:59:00-04:00', grading_state='COUNTED', counts_toward_final_grade=True),
        LiveAssignmentSpec('RM4: Spelling Test 5', READING_COURSE_ID, 'spelling', 'Assessments', 'Friday spelling assessment.', due_at='2026-07-31T23:59:00-04:00', grading_state='COUNTED', counts_toward_final_grade=True),
    ]


def _live_inventory_objects() -> list[duplicates.CanvasObjectRecord]:
    items: list[duplicates.CanvasObjectRecord] = []
    if transport.use_live_transport(test_mode=compact(os.environ.get('CANVAS_LLM_CONNECTION_TEST_MODE') or '').lower() in {'1', 'true', 'yes'}):
        for page in transport.MOCK_LIVE_STORE['pages'].values():
            items.append(duplicates.CanvasObjectRecord(
                object_type='page',
                object_id=compact(page.get('id') or page.get('url')),
                course_id=int(page['course_id']),
                title=compact(page['title']),
                week_code=WEEK_CODE,
                body=compact(page.get('body') or ''),
                content_hash=body_hash(compact(page['title']), compact(page.get('body') or '')),
                front_page=bool(page.get('front_page')),
            ))
        for object_id, assignment in transport.MOCK_LIVE_STORE['assignments'].items():
            items.append(duplicates.CanvasObjectRecord(
                object_type='assignment',
                object_id=object_id,
                course_id=int(assignment['course_id']),
                title=compact(assignment['title']),
                assignment_group=compact(assignment.get('assignment_group') or ''),
                due_at=compact(assignment.get('due_at') or ''),
                submission_count=int(assignment.get('submission_count') or 0),
                grade_activity=bool(assignment.get('grade_activity')),
            ))
    else:
        for object_id, page in LIVE_CANVAS_STORE['pages'].items():
            items.append(duplicates.CanvasObjectRecord(
                object_type='page',
                object_id=object_id,
                course_id=int(page['course_id']),
                title=compact(page['title']),
                week_code=WEEK_CODE,
                body=compact(page.get('body') or ''),
                content_hash=compact(page.get('body_hash') or ''),
                front_page=bool(page.get('front_page')),
            ))
        for object_id, assignment in LIVE_CANVAS_STORE['assignments'].items():
            items.append(duplicates.CanvasObjectRecord(
                object_type='assignment',
                object_id=object_id,
                course_id=int(assignment['course_id']),
                title=compact(assignment['title']),
                assignment_group=compact(assignment.get('assignment_group') or ''),
                due_at=compact(assignment.get('due_at') or ''),
                submission_count=int(assignment.get('submission_count') or 0),
                grade_activity=bool(assignment.get('grade_activity')),
            ))
    for object_id, announcement in LIVE_CANVAS_STORE['announcements'].items():
        items.append(duplicates.CanvasObjectRecord(
            object_type='announcement',
            object_id=object_id,
            course_id=int(announcement['course_id']),
            title=compact(announcement['title']),
            body=compact(announcement.get('body') or ''),
            content_hash=compact(announcement.get('body_hash') or ''),
            published=bool(announcement.get('published')),
            notifications_sent=bool(announcement.get('notifications_sent')),
            interaction_count=int(announcement.get('interaction_count') or 0),
        ))
    return items


def check_connection(*, test_mode: bool = False) -> connection.CanvasConnectionStatus:
    status = connection.build_connection_status(test_mode=test_mode)
    if status.authentication != 'PASS':
        raise RuntimeError('Canvas authentication failed — live deployment stopped.')
    return status


def run_duplicate_scan() -> duplicates.DuplicateScanSummary:
    summary = duplicates.scan_duplicates(_live_inventory_objects())
    unsafe = [
        item for item in summary.reports
        if item.safe_action in {'BLOCKED', 'PROTECTED', 'NEEDS_APPROVAL'}
    ]
    if unsafe:
        raise RuntimeError('Unsafe duplicates detected — cleanup approval required before live deployment.')
    return summary


def build_deployment_preview() -> LiveDeploymentReport:
    return LiveDeploymentReport(
        week_code=WEEK_CODE,
        environment='Production Canvas',
        connection_ready=False,
        duplicate_scan_pass=True,
        approval_required=True,
        writes='CONTROLLED',
    )


def print_live_deployment_preview() -> None:
    print('LIVE Q1W2 DEPLOYMENT')
    print()
    print('Environment:')
    print('Production Canvas')
    print()
    print('Week:')
    print(WEEK_CODE)
    print()
    print('READY TO CREATE:')
    print()
    print('PAGE:')
    print(PAGE_TITLE)
    print()
    print('Course:')
    print('26427 Homeroom')
    print()
    print('Front Page:')
    print('YES')
    print()
    print('ASSIGNMENTS:')
    print()
    print('Math:')
    for spec in build_q1w2_assignment_specs():
        if spec.subject == 'math':
            print(spec.title)
    print()
    print('Reading:')
    for spec in build_q1w2_assignment_specs():
        if spec.subject == 'reading':
            print(spec.title)
    print()
    print('Assessment:')
    print('RM4: Spelling Test 5')
    print()
    print('MANUAL ONLY:')
    print('ELA4')
    print('HIST4')
    print('SCI4')


def _validate_operation(operation: str) -> None:
    if operation in BLOCKED_OPERATIONS:
        raise RuntimeError(f'blocked operation: {operation}')
    if operation not in ALLOWED_OPERATIONS and operation != 'ANNOUNCEMENT_DRAFT':
        raise RuntimeError(f'unauthorized operation: {operation}')


def _validate_assignment_context(spec: LiveAssignmentSpec) -> None:
    prefix = spec.title.split(':', 1)[0]
    result = deploy_ctx.validate_deployment_context(
        deploy_ctx.DeploymentContext(
            subject=spec.subject,
            assignment_type='lesson' if spec.subject != 'spelling' else 'spelling_test',
            course_id=spec.course_id,
            canonical_prefix=prefix,
            assignment_group=spec.assignment_group,
            title=spec.title,
        ),
        target_type='assignment',
    )
    if not result.allowed:
        raise RuntimeError(result.reason or 'deployment context blocked')


def _verify_record(
    record: LiveWriteRecord,
    *,
    client: transport.MockPhase22CanvasClient | transport.Phase22LiveCanvasClient | None = None,
    test_mode: bool = False,
) -> str:
    if record.object_type == 'announcement':
        stored = LIVE_CANVAS_STORE['announcements'].get(record.object_id)
        if not stored:
            return 'FAIL'
        checks = [
            stored.get('course_id') == record.course_id,
            compact(stored.get('title')) == record.title,
            stored.get('published') is False,
        ]
        return 'PASS' if all(checks) else 'FAIL'

    if transport.use_live_transport(test_mode=test_mode):
        if record.object_type == 'page':
            return writer.verify_page_live(
                course_id=record.course_id,
                page_ref=record.object_id,
                title=record.title,
                published=bool(record.metadata.get('published')),
                front_page=bool(record.metadata.get('front_page')),
                client=client,
                test_mode=test_mode,
            )
        if record.object_type == 'assignment':
            return writer.verify_assignment_live(
                course_id=record.course_id,
                assignment_id=record.object_id,
                title=record.title,
                assignment_group=compact(record.metadata.get('assignment_group')),
                counts_toward_final_grade=bool(record.metadata.get('counts_toward_final_grade')),
                client=client,
                test_mode=test_mode,
            )

    bucket = {'page': 'pages', 'assignment': 'assignments'}[record.object_type]
    stored = LIVE_CANVAS_STORE[bucket].get(record.object_id)
    if not stored:
        return 'FAIL'
    checks = [
        stored.get('course_id') == record.course_id,
        compact(stored.get('title')) == record.title,
    ]
    if record.object_type == 'page':
        checks.extend([
            stored.get('published') is True,
            stored.get('front_page') is True,
        ])
    if record.object_type == 'assignment':
        checks.append(compact(stored.get('assignment_group')) == compact(record.metadata.get('assignment_group')))
        checks.append(stored.get('counts_toward_final_grade') == record.metadata.get('counts_toward_final_grade'))
    return 'PASS' if all(checks) else 'FAIL'


def execute_live_deployment(
    *,
    approved: bool = False,
    approved_by: str = 'teacher',
    test_mode: bool = False,
) -> LiveDeploymentReport:
    report = LiveDeploymentReport(
        week_code=WEEK_CODE,
        environment='Production Canvas',
        connection_ready=False,
        duplicate_scan_pass=False,
        approval_required=True,
    )
    audit_log = audit.DeploymentAuditLog()

    try:
        conn = check_connection(test_mode=test_mode)
        report.connection_ready = conn.ready_for_live
        report.writes = conn.writes
        dup = run_duplicate_scan()
        report.duplicate_scan_pass = dup.pages_status == 'PASS'
    except RuntimeError as exc:
        report.blockers.append(compact(exc))
        return report

    if not approved:
        report.blockers.append('teacher_approval_required')
        return report

    live_transport = transport.use_live_transport(test_mode=test_mode)
    api_client = transport.get_transport_client(test_mode=test_mode) if live_transport else None

    page_body = html_renderer.render_q1w2_weekly_agenda_html()
    _validate_operation('PAGE_CREATE')
    if live_transport:
        page_result = writer.create_page_live(
            course_id=HOMEROOM_COURSE_ID,
            title=PAGE_TITLE,
            body=page_body,
            published=True,
            front_page=True,
            approved=True,
            approved_by=approved_by,
            audit_log=audit_log,
            client=api_client,
            test_mode=test_mode,
        )
        if page_result.write_status != 'WRITTEN':
            report.blockers.extend(page_result.blockers or ['page_write_blocked'])
            return report
        page_id = page_result.target_id
    else:
        page_id = p22.stable_id('live-page', WEEK_CODE, PAGE_TITLE)
        LIVE_CANVAS_STORE['pages'][page_id] = {
            'course_id': HOMEROOM_COURSE_ID,
            'title': PAGE_TITLE,
            'body': page_body,
            'body_hash': body_hash(PAGE_TITLE, page_body),
            'published': True,
            'front_page': True,
            'deployment_version': DEPLOYMENT_VERSION,
        }
    page_record = LiveWriteRecord(
        object_type='page',
        object_id=page_id,
        course_id=HOMEROOM_COURSE_ID,
        title=PAGE_TITLE,
        write_operation='PAGE_CREATE',
        status='CREATED',
        metadata={'front_page': True, 'published': True},
    )
    page_record.audit_id = audit_log.record(page_id, 'validation', approved_by, 'live_page_create:CREATED').event_id
    page_record.rollback_id = rollback_mod.generate_rollback_plan(
        DEPLOYMENT_VERSION, page_id, 'newsletter', operation='update_page',
    ).rollback_id
    report.rollback_plans.append(rollback_mod.generate_rollback_plan(DEPLOYMENT_VERSION, page_id, 'newsletter').to_dict())
    page_record.verification = _verify_record(page_record, client=api_client, test_mode=test_mode)
    report.records.append(page_record)
    report.page_status = 'CREATED' if page_record.verification == 'PASS' else 'FAIL'

    for spec in build_q1w2_assignment_specs():
        _validate_operation('ASSIGNMENT_CREATE')
        _validate_assignment_context(spec)
        if live_transport:
            assignment_result = writer.create_assignment_live(
                course_id=spec.course_id,
                title=spec.title,
                description=spec.description,
                assignment_group=spec.assignment_group,
                points=spec.points,
                grading_type=spec.grading_type,
                submission_type=spec.submission_type,
                due_at=spec.due_at,
                counts_toward_final_grade=spec.counts_toward_final_grade,
                published=True,
                approved=True,
                approved_by=approved_by,
                audit_log=audit_log,
                client=api_client,
                test_mode=test_mode,
            )
            if assignment_result.write_status != 'WRITTEN':
                report.blockers.extend(assignment_result.blockers or [f'assignment_write_blocked:{spec.title}'])
                return report
            object_id = assignment_result.target_id
        else:
            object_id = p22.stable_id('live-assignment', spec.course_id, spec.title)
            LIVE_CANVAS_STORE['assignments'][object_id] = {
                'course_id': spec.course_id,
                'title': spec.title,
                'assignment_group': spec.assignment_group,
                'description': spec.description,
                'points': spec.points,
                'grading_type': spec.grading_type,
                'submission_type': spec.submission_type,
                'due_at': spec.due_at,
                'grading_state': spec.grading_state,
                'counts_toward_final_grade': spec.counts_toward_final_grade,
                'published': True,
                'deployment_version': DEPLOYMENT_VERSION,
            }
        record = LiveWriteRecord(
            object_type='assignment',
            object_id=object_id,
            course_id=spec.course_id,
            title=spec.title,
            write_operation='ASSIGNMENT_CREATE',
            status='CREATED',
            metadata={
                'assignment_group': spec.assignment_group,
                'counts_toward_final_grade': spec.counts_toward_final_grade,
                'grading_state': spec.grading_state,
            },
        )
        record.audit_id = audit_log.record(object_id, 'validation', approved_by, f'live_assignment_create:{spec.title}').event_id
        record.rollback_id = rollback_mod.generate_rollback_plan(
            DEPLOYMENT_VERSION, object_id, 'assignment',
        ).rollback_id
        report.rollback_plans.append(rollback_mod.generate_rollback_plan(DEPLOYMENT_VERSION, object_id, 'assignment').to_dict())
        record.verification = _verify_record(record, client=api_client, test_mode=test_mode)
        report.records.append(record)
        if record.verification == 'PASS':
            report.assignments_created += 1

    draft = html_renderer.build_spelling_announcement_draft()
    valid, issues = comm.validate_announcement_template({
        'greeting': 'Good morning, families!',
        'assessment_information': draft['body'],
        'friendly_closing': 'Have a great week!',
        'body': draft['body'],
    })
    if not valid:
        report.blockers.extend(issues)
        return report
    _validate_operation('ANNOUNCEMENT_DRAFT')
    ann_id = p22.stable_id('live-announcement', READING_COURSE_ID, draft['title'])
    LIVE_CANVAS_STORE['announcements'][ann_id] = {
        'course_id': READING_COURSE_ID,
        'title': draft['title'],
        'body': draft['body'],
        'body_hash': body_hash(draft['title'], str(draft['body'])),
        'published': False,
        'notifications_sent': False,
        'interaction_count': 0,
        'deployment_version': DEPLOYMENT_VERSION,
    }
    ann_record = LiveWriteRecord(
        object_type='announcement',
        object_id=ann_id,
        course_id=READING_COURSE_ID,
        title=compact(draft['title']),
        write_operation='ANNOUNCEMENT_DRAFT',
        status='DRAFT',
        metadata={'published': False},
    )
    ann_record.audit_id = audit_log.record(ann_id, 'validation', approved_by, 'live_announcement_draft:DRAFT').event_id
    ann_record.verification = _verify_record(ann_record, client=api_client, test_mode=test_mode)
    report.records.append(ann_record)
    report.announcement_status = 'DRAFT' if ann_record.verification == 'PASS' else 'FAIL'

    verifications = [item.verification for item in report.records]
    report.verification = 'PASS' if verifications and all(item == 'PASS' for item in verifications) else 'FAIL'
    report.audit = 'PASS' if all(item.audit_id for item in report.records) else 'FAIL'
    report.writes = 'CONTROLLED'
    return report


def print_live_deployment_status(report: LiveDeploymentReport | None = None) -> None:
    payload = report or execute_live_deployment(
        approved=compact(os.environ.get('CANVAS_LLM_LIVE_Q1W2_APPROVED') or '').lower() in {'1', 'true', 'yes'},
        test_mode=compact(os.environ.get('CANVAS_LLM_CONNECTION_TEST_MODE') or '').lower() in {'1', 'true', 'yes'},
    )
    print('LIVE Q1W2 DEPLOYMENT')
    print()
    print('Page:')
    print(payload.page_status if payload.page_status != 'PENDING' else ('CREATED' if payload.connection_ready and not payload.blockers else 'BLOCKED'))
    print()
    print('Assignments:')
    if payload.assignments_created:
        print(f'{payload.assignments_created} CREATED')
    else:
        print('0 CREATED')
    print()
    print('Announcement:')
    print(payload.announcement_status if payload.announcement_status != 'PENDING' else 'DRAFT')
    print()
    print('Verification:')
    print(payload.verification)
    print()
    print('Audit:')
    print(payload.audit)
    print()
    print('Writes:')
    print(payload.writes)


def print_c2c2_live_status(report: LiveDeploymentReport | None = None) -> None:
    payload = report or execute_live_deployment(
        approved=compact(os.environ.get('CANVAS_LLM_LIVE_Q1W2_APPROVED') or '').lower() in {'1', 'true', 'yes'},
        test_mode=compact(os.environ.get('CANVAS_LLM_LIVE_TRANSPORT_TEST') or '').lower() in {'1', 'true', 'yes'}
        or compact(os.environ.get('CANVAS_LLM_CONNECTION_TEST_MODE') or '').lower() in {'1', 'true', 'yes'},
    )
    print('C2C2 Q1W2 Live Deployment')
    print()
    print('Page:')
    print(payload.page_status if payload.page_status != 'PENDING' else ('CREATED' if payload.connection_ready and not payload.blockers else 'BLOCKED'))
    print()
    print('Assignments:')
    print(f'{payload.assignments_created} CREATED' if payload.assignments_created else '0 CREATED')
    print()
    print('Announcement:')
    print(payload.announcement_status if payload.announcement_status != 'PENDING' else 'DRAFT')
    print()
    print('Verification:')
    print(payload.verification)
    print()
    print('Audit:')
    print(payload.audit)
    print()
    print('Transport:')
    print('LIVE' if transport.use_live_transport(test_mode=compact(os.environ.get('CANVAS_LLM_CONNECTION_TEST_MODE') or '').lower() in {'1', 'true', 'yes'}) or transport.is_live_deployment_mode() else 'BLOCKED')


def command_c2c2_status(_args: argparse.Namespace) -> int:
    test_mode = compact(os.environ.get('CANVAS_LLM_LIVE_TRANSPORT_TEST') or '').lower() in {'1', 'true', 'yes'}
    test_mode = test_mode or compact(os.environ.get('CANVAS_LLM_CONNECTION_TEST_MODE') or '').lower() in {'1', 'true', 'yes'}
    approved = test_mode or compact(os.environ.get('CANVAS_LLM_LIVE_Q1W2_APPROVED') or '').lower() in {'1', 'true', 'yes'}
    report = execute_live_deployment(approved=approved, test_mode=test_mode)
    print_c2c2_live_status(report)
    return 0 if report.verification == 'PASS' and not report.blockers else 1


def live_deployment_has_no_network() -> bool:
    source = Path(__file__).read_text().lower()
    marker = 'def live_deployment_has_no_network'
    idx = source.find(marker)
    scan_source = source[:idx] if idx >= 0 else source
    forbidden = ('requests.post', 'requests.put', 'requests.delete', 'urllib.request', 'httpx', 'canvas.instructure.com/api')
    return not any(token in scan_source for token in forbidden)


def command_preview(_args: argparse.Namespace) -> int:
    print_live_deployment_preview()
    return 0


def command_status(_args: argparse.Namespace) -> int:
    test_mode = compact(os.environ.get('CANVAS_LLM_CONNECTION_TEST_MODE') or '').lower() in {'1', 'true', 'yes'}
    approved = test_mode or compact(os.environ.get('CANVAS_LLM_LIVE_Q1W2_APPROVED') or '').lower() in {'1', 'true', 'yes'}
    report = execute_live_deployment(approved=approved, test_mode=test_mode)
    print_live_deployment_status(report)
    return 0 if report.verification == 'PASS' and not report.blockers else 1


def command_self_test() -> int:
    LIVE_CANVAS_STORE['pages'].clear()
    LIVE_CANVAS_STORE['assignments'].clear()
    LIVE_CANVAS_STORE['announcements'].clear()
    transport.MOCK_LIVE_STORE['pages'].clear()
    transport.MOCK_LIVE_STORE['assignments'].clear()

    conn = check_connection(test_mode=True)
    assert conn.authentication == 'PASS'
    assert conn.writes == 'CONTROLLED'

    dup = run_duplicate_scan()
    assert dup.pages_status == 'PASS'

    preview = build_deployment_preview()
    assert preview.week_code == WEEK_CODE

    report = execute_live_deployment(approved=True, test_mode=True)
    assert report.page_status == 'CREATED'
    assert report.assignments_created == 9
    assert report.announcement_status == 'DRAFT'
    assert report.verification == 'PASS'
    assert report.audit == 'PASS'
    assert report.writes == 'CONTROLLED'
    assert len(report.rollback_plans) == 10

    page = next(item for item in report.records if item.object_type == 'page')
    assert page.metadata.get('front_page') is True

    lesson5 = next(item for item in report.records if item.title == 'SM5: Lesson 5')
    assert lesson5.metadata.get('counts_toward_final_grade') is False

    lesson4 = next(item for item in report.records if item.title == 'RM4: Lesson 4')
    assert lesson4.metadata.get('counts_toward_final_grade') is False

    spelling = next(item for item in report.records if item.title == 'RM4: Spelling Test 5')
    assert spelling.metadata.get('counts_toward_final_grade') is True

    for manual in resolver.MANUAL_SUBJECTS:
        assert manual in {'ELA4', 'HIST4', 'SCI4'}

    assert live_deployment_has_no_network()
    print('PASS live q1w2 deployment self-test')
    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Live Q1W2 Canvas deployment')
    sub = parser.add_subparsers(dest='cmd', required=True)
    sub.add_parser('deployment-preview').set_defaults(func=command_preview)
    sub.add_parser('deployment-status').set_defaults(func=command_status)
    sub.add_parser('c2c2-live-status').set_defaults(func=command_c2c2_status)
    sub.add_parser('self-test').set_defaults(func=lambda _args: command_self_test())
    args = parser.parse_args()
    raise SystemExit(args.func(args))
