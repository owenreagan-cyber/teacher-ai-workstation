#!/usr/bin/env python3
"""Weekly agenda publisher for C1B teacher-facing Canvas page operations."""
from __future__ import annotations

import argparse
import hashlib
import html
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.canvas_llm_phase22 import canvas_connector as connector  # noqa: E402
from scripts.canvas_llm_phase22 import canvas_verification as verification  # noqa: E402
from scripts.canvas_llm_phase22 import canvas_writer as writer  # noqa: E402
from scripts.canvas_llm_phase22 import deployment_audit as audit  # noqa: E402
from scripts.canvas_llm_phase22 import phase22_workstation as p22  # noqa: E402

DEPLOYMENT_STATUSES = ('draft', 'ready', 'blocked', 'written', 'verified')
WEEKDAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
SANDBOX_COURSE_ID = connector.SANDBOX_COURSE_ID
_PUBLISHED_PAGES: set[str] = set()


def compact(value: Any) -> str:
    return p22.compact(value)


def content_hash(title: str, body: str) -> str:
    payload = f'{compact(title)}|{compact(body)}'.encode('utf-8')
    return hashlib.sha256(payload).hexdigest()[:16]


@dataclass
class WeeklyAgendaPage:
    week_code: str
    title: str
    days: list[dict[str, Any]] = field(default_factory=list)
    assignments: list[str] = field(default_factory=list)
    assessments: list[str] = field(default_factory=list)
    reminders: list[str] = field(default_factory=list)
    schedule_summary: str | None = None
    content_hash: str | None = None
    approval_state: str = 'draft'
    deployment_status: str = 'draft'
    page_url: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _week_title(week_meta: dict[str, Any]) -> str:
    starts_on = compact(week_meta.get('startsOn') or '')
    if starts_on:
        return f'Week of {starts_on}'
    subtitle = compact(week_meta.get('displaySubtitle') or '')
    return f'Week of {subtitle}' if subtitle else 'Weekly Agenda'


def _render_day_section(day_name: str, day_data: dict[str, Any]) -> str:
    lines: list[str] = [f'<h3>{html.escape(day_name)}</h3>']
    for subject, items in day_data.get('subjects', {}).items():
        lines.append(f'<p><strong>{html.escape(subject.title())}:</strong></p><ul>')
        for item in items:
            lines.append(f'<li>{html.escape(compact(item))}</li>')
        lines.append('</ul>')
    if day_data.get('homework'):
        lines.append('<p><strong>Homework:</strong></p><ul>')
        for hw in day_data['homework']:
            lines.append(f'<li>{html.escape(compact(hw))}</li>')
        lines.append('</ul>')
    return ''.join(lines)


def render_agenda_html(page: WeeklyAgendaPage) -> str:
    """Generate teacher-friendly Canvas page HTML from a WeeklyAgendaPage."""
    parts = [f'<h2>{html.escape(page.title)}</h2>']
    if page.schedule_summary:
        parts.append(f'<p>{html.escape(page.schedule_summary)}</p>')
    if page.reminders:
        parts.append('<h3>Reminders</h3><ul>')
        for reminder in page.reminders:
            parts.append(f'<li>{html.escape(compact(reminder))}</li>')
        parts.append('</ul>')
    if page.assessments:
        parts.append('<h3>Assessments</h3><ul>')
        for assessment in page.assessments:
            parts.append(f'<li>{html.escape(compact(assessment))}</li>')
        parts.append('</ul>')
    for day in page.days:
        parts.append(_render_day_section(day.get('name', 'Day'), day))
    if page.assignments:
        parts.append('<h3>Assignments</h3><ul>')
        for assignment in page.assignments:
            parts.append(f'<li>{html.escape(compact(assignment))}</li>')
        parts.append('</ul>')
    return ''.join(parts)


def build_agenda_from_packet(packet: dict[str, Any]) -> WeeklyAgendaPage:
    """Build a WeeklyAgendaPage from a weekly content packet."""
    week_meta = packet.get('instructionalWeek') or {}
    week_code = p22.canonical_week_code(compact(week_meta.get('code') or packet.get('weekCode') or ''))
    days: list[dict[str, Any]] = []
    assignments: list[str] = []
    assessments: list[str] = []
    reminders: list[str] = list(packet.get('reminders') or [])

    for day_name in WEEKDAYS:
        day_entry = next((d for d in packet.get('days', []) if compact(d.get('weekday')) == day_name), None)
        if not day_entry:
            continue
        subjects: dict[str, list[str]] = {}
        homework: list[str] = []
        for subject_block in day_entry.get('subjects', []):
            subject = compact(subject_block.get('subject') or 'subject')
            in_class = compact(subject_block.get('inClass') or subject_block.get('lesson') or '')
            if in_class:
                subjects.setdefault(subject, []).append(in_class)
            hw = compact(subject_block.get('homework') or subject_block.get('atHome') or '')
            if hw:
                homework.append(f'{subject.title()}: {hw}')
            if subject_block.get('assessment'):
                assessments.append(f'{day_name}: {compact(subject_block["assessment"])}')
            if subject_block.get('assignment'):
                assignments.append(compact(subject_block['assignment']))
        days.append({'name': day_name, 'subjects': subjects, 'homework': homework})

    title = _week_title(week_meta)
    body = render_agenda_html(WeeklyAgendaPage(week_code=week_code, title=title, days=days, assignments=assignments, assessments=assessments, reminders=reminders))
    page_url = f'weekly-agenda-{week_code.lower()}'

    return WeeklyAgendaPage(
        week_code=week_code,
        title=title,
        days=days,
        assignments=assignments,
        assessments=assessments,
        reminders=reminders,
        schedule_summary=compact(week_meta.get('displaySubtitle') or ''),
        content_hash=content_hash(title, body),
        approval_state=compact(packet.get('approvalState') or 'draft'),
        deployment_status='draft',
        page_url=page_url,
    )


def build_agenda_from_db(db: p22.WorkstationDB, weekly_plan_id: str, subject_key: str = 'math') -> WeeklyAgendaPage:
    """Build agenda page from Phase 22 workstation database."""
    with db.connect() as conn:
        plan = conn.execute('SELECT payload,starts_on FROM weekly_plans WHERE id=?', (weekly_plan_id,)).fetchone()
        rows = [dict(r) for r in conn.execute(
            'SELECT * FROM daily_subject_entries WHERE weekly_plan_id=? ORDER BY entry_date,subject',
            (weekly_plan_id,),
        )]
    payload = p22.jl(plan['payload'], {})
    iw = payload.get('instructionalWeek') or p22.instructional_week_by_starts_on(plan['starts_on']) or {}
    groups = {'math': ['math'], 'reading-spelling': ['reading', 'spelling']}
    subs = groups.get(subject_key, ['math'])
    active_rows = [r for r in rows if r['subject'] in subs and p22.subject_active_for_quarter(r['subject'], iw)]
    body_html = p22.render_agenda_html(iw, active_rows)
    week_code = p22.canonical_week_code(compact(iw.get('code') or ''))
    title = _week_title(iw)
    page_url = f'{subject_key}-agenda-{week_code.lower()}'

    days: list[dict[str, Any]] = []
    for wd in WEEKDAYS:
        day_rows = [r for r in active_rows if r['weekday'] == wd]
        subjects: dict[str, list[str]] = {}
        homework: list[str] = []
        for row in day_rows:
            fields = p22.agenda_fields_for_row(row, iw)
            subj = compact(row.get('subject') or '')
            in_class = compact(fields.get('in_class') or '')
            if in_class:
                subjects.setdefault(subj, []).append(in_class)
            hw = compact(fields.get('at_home') or '')
            if hw:
                homework.append(f'{subj.title()}: {hw}')
        days.append({'name': wd, 'subjects': subjects, 'homework': homework})

    assessments = [
        compact(a.get('bullet') or '')
        for a in p22.collect_assessments_from_rows(active_rows, plan['starts_on'], iw)
        if compact(a.get('bullet') or '')
    ]

    return WeeklyAgendaPage(
        week_code=week_code,
        title=title,
        days=days,
        assignments=[],
        assessments=assessments,
        reminders=[],
        schedule_summary=compact(iw.get('displaySubtitle') or ''),
        content_hash=content_hash(title, body_html),
        approval_state='draft',
        deployment_status='draft',
        page_url=page_url,
    )


class WeeklyAgendaPublisher:
    """Turn weekly plan content into a Canvas page artifact and deploy when approved."""

    def __init__(
        self,
        db: p22.WorkstationDB,
        *,
        config: connector.CanvasConnectionConfig | None = None,
        audit_log: audit.DeploymentAuditLog | None = None,
    ) -> None:
        self.db = db
        self.config = config or connector.default_connection_config()
        self.audit_log = audit_log or audit.DeploymentAuditLog()

    def generate_page(self, weekly_plan_id: str, subject_key: str = 'math') -> WeeklyAgendaPage:
        return build_agenda_from_db(self.db, weekly_plan_id, subject_key)

    def page_already_published(self, page: WeeklyAgendaPage) -> bool:
        key = compact(page.page_url or '')
        return key in _PUBLISHED_PAGES

    def deploy_page(
        self,
        page: WeeklyAgendaPage,
        *,
        artifact_id: str,
        course_id: int = SANDBOX_COURSE_ID,
        record=None,
        queue_item=None,
        latest=None,
    ) -> WeeklyAgendaPage:
        if self.page_already_published(page):
            page.deployment_status = 'blocked'
            self.audit_log.record(artifact_id, 'validation', 'system', 'BLOCKED:duplicate_page')
            return page

        body = render_agenda_html(page)
        result = writer.create_page(
            self.db,
            artifact_id=artifact_id,
            course_id=course_id,
            page_url=compact(page.page_url or ''),
            title=page.title,
            body=body,
            record=record,
            queue_item=queue_item,
            latest=latest,
            config=self.config,
            audit_log=self.audit_log,
        )

        if result.write_status == 'WRITTEN':
            verify = verification.verify_page(
                course_id,
                compact(page.page_url or ''),
                expected_title=page.title,
                expected_body_hash=result.body_hash,
                config=self.config,
            )
            page.deployment_status = 'verified' if verify.status == 'PASS' else 'written'
            _PUBLISHED_PAGES.add(compact(page.page_url or ''))
        else:
            page.deployment_status = 'blocked'

        return page


def agenda_has_no_student_data(page: WeeklyAgendaPage) -> bool:
    payload = page.to_dict()
    return p22.no_sensitive_payload(payload)


def command_self_test() -> int:
    _PUBLISHED_PAGES.clear()
    writer.FAKE_CANVAS_STORE['pages'].clear()

    packet = {
        'weekCode': 'Q1W5',
        'approvalState': 'approved',
        'instructionalWeek': {'code': 'Q1W5', 'startsOn': '2026-08-17', 'displaySubtitle': 'Quarter 1, Week 5'},
        'reminders': ['Bring headphones on Wednesday'],
        'days': [
            {
                'weekday': 'Monday',
                'subjects': [
                    {'subject': 'math', 'inClass': 'Lesson 18', 'homework': 'Saxon Math'},
                    {'subject': 'reading', 'inClass': 'Lesson 50'},
                ],
            },
            {
                'weekday': 'Tuesday',
                'subjects': [
                    {'subject': 'math', 'inClass': 'Lesson 19', 'homework': 'Saxon Math'},
                ],
            },
        ],
    }
    page = build_agenda_from_packet(packet)
    assert page.week_code == 'Q1W5'
    assert 'August' in page.title or '2026' in page.title
    html_body = render_agenda_html(page)
    assert 'Monday' in html_body
    assert 'Lesson 18' in html_body
    assert 'Saxon Math' in html_body
    assert agenda_has_no_student_data(page)

    publisher = WeeklyAgendaPublisher(p22.WorkstationDB(':memory:'))
    assert not publisher.page_already_published(page)
    _PUBLISHED_PAGES.add(compact(page.page_url or ''))
    assert publisher.page_already_published(page)

    print('PASS weekly agenda publisher self-test')
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Canvas LLM weekly agenda publisher')
    sub = parser.add_subparsers(dest='cmd', required=True)
    sub.add_parser('self-test').set_defaults(func=lambda _args: command_self_test())
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == '__main__':
    raise SystemExit(main())
