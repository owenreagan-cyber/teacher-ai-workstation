#!/usr/bin/env python3
"""Pacing parser for C1I — convert weekly pacing into structured instructional plans."""
from __future__ import annotations

import argparse
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.canvas_llm_phase22 import phase22_workstation as p22  # noqa: E402

WEEKDAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']


def compact(value: Any) -> str:
    return p22.compact(value)


@dataclass
class SubjectLessonEntry:
    weekday: str
    entry_date: str
    lesson: str | None = None
    test: str | None = None
    title: str | None = None
    notes: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SubjectPlan:
    subject: str
    lessons: list[SubjectLessonEntry] = field(default_factory=list)
    lesson_range: str | None = None
    assessments: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload['lessons'] = [lesson.to_dict() for lesson in self.lessons]
        return payload


@dataclass
class WeeklyInstructionalPlan:
    week_code: str
    date_range: str
    subject_plans: list[SubjectPlan] = field(default_factory=list)
    lessons: dict[str, list[str]] = field(default_factory=dict)
    assessments: dict[str, list[str]] = field(default_factory=list)
    special_notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            'week_code': self.week_code,
            'date_range': self.date_range,
            'subject_plans': [plan.to_dict() for plan in self.subject_plans],
            'lessons': self.lessons,
            'assessments': self.assessments,
            'special_notes': self.special_notes,
        }


def _lesson_numbers(entries: list[SubjectLessonEntry]) -> list[str]:
    numbers: list[str] = []
    for entry in entries:
        if entry.lesson and str(entry.lesson).isdigit():
            numbers.append(str(entry.lesson))
    return numbers


def _lesson_range(numbers: list[str]) -> str | None:
    if not numbers:
        return None
    ints = sorted({int(n) for n in numbers})
    if len(ints) == 1:
        return f'Lesson {ints[0]}'
    return f'Lessons {ints[0]}-{ints[-1]}'


def parse_rows_to_plan(
    week_meta: dict[str, Any],
    rows: list[dict[str, Any]],
) -> WeeklyInstructionalPlan:
    """Parse daily subject rows into a WeeklyInstructionalPlan."""
    week_code = p22.canonical_week_code(compact(week_meta.get('code') or ''))
    starts = compact(week_meta.get('startsOn') or '')
    ends = compact(week_meta.get('endsOn') or '')
    date_range = f'{starts} to {ends}' if starts and ends else starts or week_code

    subject_plans: list[SubjectPlan] = []
    lessons: dict[str, list[str]] = {}
    assessments: dict[str, list[str]] = {}
    special_notes: list[str] = []

    subjects = sorted({compact(r.get('subject') or '') for r in rows if compact(r.get('subject') or '')})
    for subject in subjects:
        subject_rows = [r for r in rows if compact(r.get('subject') or '') == subject]
        if not subject_rows:
            continue
        entries: list[SubjectLessonEntry] = []
        subject_assessments: list[str] = []
        for row in subject_rows:
            lesson = compact(row.get('lesson') or '') or None
            test = compact(row.get('tests') or '') or None
            entry = SubjectLessonEntry(
                weekday=compact(row.get('weekday') or ''),
                entry_date=compact(row.get('entry_date') or ''),
                lesson=lesson,
                test=test,
                title=compact(row.get('title') or '') or None,
                notes=compact(row.get('notes') or '') or None,
            )
            entries.append(entry)
            if test and str(test).isdigit():
                if subject == 'spelling':
                    subject_assessments.append(f'Spelling Test {test}')
                elif subject == 'math':
                    subject_assessments.append(f'Written Assessment {test}')
                else:
                    subject_assessments.append(f'{subject.title()} Assessment {test}')
            if compact(row.get('notes') or ''):
                special_notes.append(f'{subject}: {compact(row.get("notes"))}')

        lesson_nums = _lesson_numbers(entries)
        lessons[subject] = lesson_nums
        if subject_assessments:
            assessments[subject] = subject_assessments

        subject_plans.append(
            SubjectPlan(
                subject=subject,
                lessons=entries,
                lesson_range=_lesson_range(lesson_nums),
                assessments=subject_assessments,
            )
        )

    return WeeklyInstructionalPlan(
        week_code=week_code,
        date_range=date_range,
        subject_plans=subject_plans,
        lessons=lessons,
        assessments=assessments,
        special_notes=special_notes,
    )


def parse_week_from_db(db: p22.WorkstationDB, weekly_plan_id: str) -> WeeklyInstructionalPlan:
    """Parse a weekly plan from the Phase 22 workstation database."""
    with db.connect() as conn:
        plan = conn.execute('SELECT payload,starts_on FROM weekly_plans WHERE id=?', (weekly_plan_id,)).fetchone()
        rows = [dict(r) for r in conn.execute(
            'SELECT * FROM daily_subject_entries WHERE weekly_plan_id=? ORDER BY entry_date,subject',
            (weekly_plan_id,),
        )]
    payload = p22.jl(plan['payload'], {})
    iw = payload.get('instructionalWeek') or p22.instructional_week_by_starts_on(plan['starts_on']) or {}
    active_rows = [r for r in rows if p22.subject_active_for_quarter(r.get('subject'), iw)]
    return parse_rows_to_plan(iw, active_rows)


def command_self_test() -> int:
    week_meta = {'code': 'Q1W2', 'startsOn': '2026-08-10', 'endsOn': '2026-08-14', 'quarter': 1, 'week': 2}
    rows = [
        {'subject': 'math', 'weekday': 'Monday', 'entry_date': '2026-08-10', 'lesson': '2', 'tests': '', 'title': 'Lesson 2', 'notes': ''},
        {'subject': 'math', 'weekday': 'Tuesday', 'entry_date': '2026-08-11', 'lesson': '3', 'tests': '', 'title': 'Lesson 3', 'notes': ''},
        {'subject': 'math', 'weekday': 'Wednesday', 'entry_date': '2026-08-12', 'lesson': '4', 'tests': '', 'title': 'Lesson 4', 'notes': ''},
        {'subject': 'math', 'weekday': 'Thursday', 'entry_date': '2026-08-13', 'lesson': '5', 'tests': '', 'title': 'Lesson 5', 'notes': ''},
        {'subject': 'math', 'weekday': 'Friday', 'entry_date': '2026-08-14', 'lesson': '6', 'tests': '', 'title': 'Lesson 6', 'notes': ''},
        {'subject': 'reading', 'weekday': 'Monday', 'entry_date': '2026-08-10', 'lesson': '2', 'tests': '', 'title': 'Lesson 2', 'notes': ''},
        {'subject': 'reading', 'weekday': 'Tuesday', 'entry_date': '2026-08-11', 'lesson': '3', 'tests': '', 'title': 'Lesson 3', 'notes': ''},
        {'subject': 'spelling', 'weekday': 'Friday', 'entry_date': '2026-08-14', 'lesson': '', 'tests': '5', 'title': 'Spelling Test 5', 'notes': ''},
    ]
    plan = parse_rows_to_plan(week_meta, rows)
    assert plan.week_code == 'Q1W2'
    assert plan.lessons['math'] == ['2', '3', '4', '5', '6']
    assert 'Spelling Test 5' in plan.assessments.get('spelling', [])
    math_plan = next(p for p in plan.subject_plans if p.subject == 'math')
    assert math_plan.lesson_range == 'Lessons 2-6'

    print('PASS pacing parser self-test')
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Canvas LLM pacing parser')
    sub = parser.add_subparsers(dest='cmd', required=True)
    sub.add_parser('self-test').set_defaults(func=lambda _args: command_self_test())
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == '__main__':
    raise SystemExit(main())
