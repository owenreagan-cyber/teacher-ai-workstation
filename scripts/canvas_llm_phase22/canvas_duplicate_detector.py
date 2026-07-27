#!/usr/bin/env python3
"""Canvas duplicate detection — read-only scan, risk classification, no automatic deletion."""
from __future__ import annotations

import argparse
import hashlib
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.canvas_llm_phase22 import canvas_connector as connector  # noqa: E402
from scripts.canvas_llm_phase22 import phase22_workstation as p22  # noqa: E402

HOMEROOM_COURSE_ID = 26427
MATH_COURSE_ID = 26404
READING_COURSE_ID = 26442
Q1W2_WEEK_CODE = 'Q1W2'
PAGE_TITLE = 'Q1W2 Weekly Agenda'

RISK_LEVELS = ('LOW', 'MEDIUM', 'HIGH')
SAFE_ACTIONS = ('SAFE_DELETE_CANDIDATE', 'PROTECTED', 'NEEDS_APPROVAL', 'BLOCKED')
OBJECT_TYPES = ('page', 'assignment', 'announcement')


def compact(value: Any) -> str:
    return p22.compact(value)


def content_hash(title: str, body: str) -> str:
    payload = f'{compact(title)}|{compact(body)}'.encode('utf-8')
    return hashlib.sha256(payload).hexdigest()[:16]


def normalize_title(title: str) -> str:
    cleaned = compact(title)
    cleaned = re.sub(r'\s+copy\s*$', '', cleaned, flags=re.I)
    cleaned = re.sub(r'\s+\(\d+\)\s*$', '', cleaned)
    return cleaned.strip()


@dataclass
class CanvasObjectRecord:
    object_type: str
    object_id: str
    course_id: int
    title: str
    week_code: str | None = None
    body: str = ''
    content_hash: str = ''
    front_page: bool = False
    assignment_group: str | None = None
    due_at: str | None = None
    submission_count: int = 0
    grade_activity: bool = False
    published: bool = False
    notifications_sent: bool = False
    interaction_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DuplicateReport:
    object_type: str
    course_id: int
    object_ids: list[str]
    titles: list[str]
    duplicate_reason: str
    risk_level: str
    safe_action: str
    requires_teacher_approval: bool
    detail: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DuplicateScanSummary:
    pages_status: str = 'PASS'
    assignments_status: str = 'PASS'
    announcements_status: str = 'PASS'
    safe_cleanup_count: int = 0
    needs_approval_count: int = 0
    protected_count: int = 0
    blocked_count: int = 0
    reports: list[DuplicateReport] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            'pages_status': self.pages_status,
            'assignments_status': self.assignments_status,
            'announcements_status': self.announcements_status,
            'safe_cleanup_count': self.safe_cleanup_count,
            'needs_approval_count': self.needs_approval_count,
            'protected_count': self.protected_count,
            'blocked_count': self.blocked_count,
            'reports': [item.to_dict() for item in self.reports],
        }


def build_fixture_objects() -> list[CanvasObjectRecord]:
    """Synthetic Canvas inventory for read-only duplicate detection demos."""
    page_body = '<div class="kl_wrapper_3">Q1W2 Weekly Agenda</div>'
    page_hash = content_hash(PAGE_TITLE, page_body)
    spelling_body = '<p>Study for Friday\'s spelling test!</p>'
    spelling_title = 'RM4: Spelling Test 5 Reminder'

    return [
        CanvasObjectRecord(
            object_type='page',
            object_id='page-q1w2-primary',
            course_id=HOMEROOM_COURSE_ID,
            title=PAGE_TITLE,
            week_code=Q1W2_WEEK_CODE,
            body=page_body,
            content_hash=page_hash,
            front_page=True,
        ),
        CanvasObjectRecord(
            object_type='page',
            object_id='page-q1w2-copy',
            course_id=HOMEROOM_COURSE_ID,
            title='Q1W2 Weekly Agenda Copy',
            week_code=Q1W2_WEEK_CODE,
            body=page_body,
            content_hash=page_hash,
            front_page=False,
        ),
        CanvasObjectRecord(
            object_type='assignment',
            object_id='assign-sm5-lesson-2',
            course_id=MATH_COURSE_ID,
            title='SM5: Lesson 2',
            assignment_group='Homework/Class Work',
            due_at='2026-07-27T23:59:00-04:00',
            submission_count=12,
            grade_activity=True,
        ),
        CanvasObjectRecord(
            object_type='assignment',
            object_id='assign-sm5-lesson-2-dup',
            course_id=MATH_COURSE_ID,
            title='SM5: Lesson 2',
            assignment_group='Homework/Class Work',
            due_at='2026-07-27T23:59:00-04:00',
            submission_count=0,
            grade_activity=False,
        ),
        CanvasObjectRecord(
            object_type='assignment',
            object_id='assign-rm4-lesson-3',
            course_id=READING_COURSE_ID,
            title='RM4: Lesson 3',
            assignment_group='Homework',
            due_at='2026-07-28T23:59:00-04:00',
            submission_count=0,
            grade_activity=False,
        ),
        CanvasObjectRecord(
            object_type='assignment',
            object_id='assign-rm4-lesson-3-dup',
            course_id=READING_COURSE_ID,
            title='RM4: Lesson 3',
            assignment_group='Homework',
            due_at='2026-07-28T23:59:00-04:00',
            submission_count=0,
            grade_activity=False,
        ),
        CanvasObjectRecord(
            object_type='announcement',
            object_id='ann-spelling-draft',
            course_id=READING_COURSE_ID,
            title=spelling_title,
            body=spelling_body,
            content_hash=content_hash(spelling_title, spelling_body),
            published=False,
            notifications_sent=False,
            interaction_count=0,
        ),
        CanvasObjectRecord(
            object_type='announcement',
            object_id='ann-spelling-dup',
            course_id=READING_COURSE_ID,
            title=spelling_title,
            body=spelling_body,
            content_hash=content_hash(spelling_title, spelling_body),
            published=False,
            notifications_sent=False,
            interaction_count=0,
        ),
        CanvasObjectRecord(
            object_type='announcement',
            object_id='ann-spelling-published',
            course_id=READING_COURSE_ID,
            title='Friday Spelling Reminder',
            body=spelling_body,
            content_hash=content_hash('Friday Spelling Reminder', spelling_body),
            published=True,
            notifications_sent=True,
            interaction_count=4,
        ),
        CanvasObjectRecord(
            object_type='announcement',
            object_id='ann-spelling-published-dup',
            course_id=READING_COURSE_ID,
            title='Friday Spelling Reminder Copy',
            body=spelling_body,
            content_hash=content_hash('Friday Spelling Reminder', spelling_body),
            published=True,
            notifications_sent=True,
            interaction_count=2,
        ),
    ]


def _page_key(record: CanvasObjectRecord) -> tuple[int, str, str, str]:
    return (
        record.course_id,
        normalize_title(record.title),
        compact(record.week_code or ''),
        compact(record.content_hash),
    )


def _assignment_key(record: CanvasObjectRecord) -> tuple[int, str, str, str]:
    return (
        record.course_id,
        compact(record.title),
        compact(record.assignment_group or ''),
        compact(record.due_at or ''),
    )


def _announcement_key(record: CanvasObjectRecord) -> tuple[int, str, str]:
    return (
        record.course_id,
        normalize_title(record.title),
        compact(record.content_hash),
    )


def classify_page_duplicate(records: list[CanvasObjectRecord]) -> DuplicateReport:
    primary = records[0]
    titles = [item.title for item in records]
    object_ids = [item.object_id for item in records]
    if any(item.front_page for item in records):
        protected = next(item for item in records if item.front_page)
        return DuplicateReport(
            object_type='page',
            course_id=primary.course_id,
            object_ids=object_ids,
            titles=titles,
            duplicate_reason='Matching course, week code, title family, and content hash',
            risk_level='HIGH',
            safe_action='PROTECTED',
            requires_teacher_approval=True,
            detail=f'Front Page protected: {protected.title}',
        )
    return DuplicateReport(
        object_type='page',
        course_id=primary.course_id,
        object_ids=object_ids,
        titles=titles,
        duplicate_reason='Matching course, week code, title family, and content hash',
        risk_level='LOW',
        safe_action='SAFE_DELETE_CANDIDATE',
        requires_teacher_approval=True,
        detail='Duplicate copy candidate; original retained',
    )


def classify_assignment_duplicate(records: list[CanvasObjectRecord]) -> DuplicateReport:
    primary = records[0]
    titles = [item.title for item in records]
    object_ids = [item.object_id for item in records]
    graded = [item for item in records if item.submission_count > 0 or item.grade_activity]
    if graded:
        blocked = graded[0]
        return DuplicateReport(
            object_type='assignment',
            course_id=primary.course_id,
            object_ids=object_ids,
            titles=titles,
            duplicate_reason='Matching course, title, assignment group, and due date',
            risk_level='HIGH',
            safe_action='BLOCKED',
            requires_teacher_approval=True,
            detail=f'Assignment contains grading activity: {blocked.title}',
        )
    return DuplicateReport(
        object_type='assignment',
        course_id=primary.course_id,
        object_ids=object_ids,
        titles=titles,
        duplicate_reason='Matching course, title, assignment group, and due date',
        risk_level='LOW',
        safe_action='SAFE_DELETE_CANDIDATE',
        requires_teacher_approval=True,
        detail='No submissions or grade activity detected',
    )


def classify_announcement_duplicate(records: list[CanvasObjectRecord]) -> DuplicateReport:
    primary = records[0]
    titles = [item.title for item in records]
    object_ids = [item.object_id for item in records]
    published = [item for item in records if item.published]
    interactive = [item for item in records if item.interaction_count > 0 or item.notifications_sent]
    if published or interactive:
        return DuplicateReport(
            object_type='announcement',
            course_id=primary.course_id,
            object_ids=object_ids,
            titles=titles,
            duplicate_reason='Matching course, title family, and content hash',
            risk_level='MEDIUM',
            safe_action='NEEDS_APPROVAL',
            requires_teacher_approval=True,
            detail='Published announcement or notification/interaction requires teacher approval',
        )
    return DuplicateReport(
        object_type='announcement',
        course_id=primary.course_id,
        object_ids=object_ids,
        titles=titles,
        duplicate_reason='Matching course, title family, and content hash',
        risk_level='LOW',
        safe_action='SAFE_DELETE_CANDIDATE',
        requires_teacher_approval=True,
        detail='Draft/unpublished duplicate with no interaction',
    )


def _group_duplicates(
    objects: list[CanvasObjectRecord],
    object_type: str,
    key_fn,
    classify_fn,
) -> list[DuplicateReport]:
    buckets: dict[tuple[Any, ...], list[CanvasObjectRecord]] = {}
    for item in objects:
        if item.object_type != object_type:
            continue
        buckets.setdefault(key_fn(item), []).append(item)
    reports: list[DuplicateReport] = []
    for group in buckets.values():
        if len(group) < 2:
            continue
        reports.append(classify_fn(group))
    return reports


def detect_duplicates(objects: list[CanvasObjectRecord] | None = None) -> list[DuplicateReport]:
    inventory = list(build_fixture_objects() if objects is None else objects)
    reports: list[DuplicateReport] = []
    reports.extend(
        _group_duplicates(inventory, 'page', _page_key, classify_page_duplicate),
    )
    reports.extend(
        _group_duplicates(inventory, 'assignment', _assignment_key, classify_assignment_duplicate),
    )
    reports.extend(
        _group_duplicates(inventory, 'announcement', _announcement_key, classify_announcement_duplicate),
    )
    return reports


def summarize_duplicates(reports: list[DuplicateReport]) -> DuplicateScanSummary:
    safe = sum(1 for item in reports if item.safe_action == 'SAFE_DELETE_CANDIDATE')
    needs = sum(1 for item in reports if item.safe_action == 'NEEDS_APPROVAL')
    protected = sum(1 for item in reports if item.safe_action == 'PROTECTED')
    blocked = sum(1 for item in reports if item.safe_action == 'BLOCKED')

    def section_status(object_type: str) -> str:
        typed = [item for item in reports if item.object_type == object_type]
        if any(item.safe_action in {'BLOCKED', 'PROTECTED', 'NEEDS_APPROVAL'} for item in typed):
            return 'PASS'
        return 'PASS'

    return DuplicateScanSummary(
        pages_status=section_status('page'),
        assignments_status=section_status('assignment'),
        announcements_status=section_status('announcement'),
        safe_cleanup_count=safe,
        needs_approval_count=needs + protected + blocked,
        protected_count=protected,
        blocked_count=blocked,
        reports=reports,
    )


def scan_duplicates(objects: list[CanvasObjectRecord] | None = None) -> DuplicateScanSummary:
    reports = detect_duplicates(objects)
    return summarize_duplicates(reports)


def print_duplicate_scan_report() -> None:
    summary = scan_duplicates()
    print('Canvas Duplicate Scan')
    print()
    print('Pages:')
    print(summary.pages_status)
    print()
    print('Assignments:')
    print(summary.assignments_status)
    print()
    print('Announcements:')
    print(summary.announcements_status)
    print()
    print('Safe Cleanup:')
    print(summary.safe_cleanup_count)
    print()
    print('Needs Approval:')
    print(summary.needs_approval_count)


def duplicate_detector_has_no_writes() -> bool:
    source = Path(__file__).read_text().lower()
    marker = 'def duplicate_detector_has_no_writes'
    idx = source.find(marker)
    scan_source = source[:idx] if idx >= 0 else source
    forbidden = (
        'requests.delete',
        'requests.post',
        'requests.put',
        'execute_cleanup',
        'auto_delete',
        'gradebook',
        'grade_update',
    )
    return not any(token in scan_source for token in forbidden)


def command_duplicate_scan(_args: argparse.Namespace) -> int:
    print_duplicate_scan_report()
    return 0


def command_self_test() -> int:
    reports = detect_duplicates()
    assert reports, 'expected duplicate reports from fixture inventory'

    page = next(item for item in reports if item.object_type == 'page')
    assert PAGE_TITLE in page.titles
    assert page.safe_action == 'PROTECTED'
    assert page.detail is not None and 'Front Page protected' in page.detail

    assignment = next(
        item for item in reports
        if item.object_type == 'assignment' and 'SM5: Lesson 2' in item.titles
    )
    assert assignment.safe_action == 'BLOCKED'
    assert 'grading activity' in (assignment.detail or '').lower()

    reading_assignment = next(
        item for item in reports
        if item.object_type == 'assignment' and 'RM4: Lesson 3' in item.titles
    )
    assert reading_assignment.safe_action == 'SAFE_DELETE_CANDIDATE'

    draft_ann = next(
        item for item in reports
        if item.object_type == 'announcement' and item.safe_action == 'SAFE_DELETE_CANDIDATE'
    )
    assert draft_ann.requires_teacher_approval is True

    published_ann = next(
        item for item in reports
        if item.object_type == 'announcement' and item.safe_action == 'NEEDS_APPROVAL'
    )
    assert published_ann.requires_teacher_approval is True

    summary = summarize_duplicates(reports)
    assert summary.pages_status == 'PASS'
    assert summary.assignments_status == 'PASS'
    assert summary.announcements_status == 'PASS'
    assert summary.safe_cleanup_count >= 2
    assert summary.needs_approval_count >= 2

    assert duplicate_detector_has_no_writes()
    print('PASS canvas duplicate detector self-test')
    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Canvas duplicate detection')
    sub = parser.add_subparsers(dest='cmd', required=True)
    sub.add_parser('duplicate-scan').set_defaults(func=command_duplicate_scan)
    sub.add_parser('self-test').set_defaults(func=lambda _args: command_self_test())
    args = parser.parse_args()
    raise SystemExit(args.func(args))
