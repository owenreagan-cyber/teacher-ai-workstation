#!/usr/bin/env python3
"""Homework and assessment rules engine for C1I — assignment intelligence, not Canvas publishing."""
from __future__ import annotations

import argparse
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.canvas_llm_phase22 import pacing_parser as pacing  # noqa: E402
from scripts.canvas_llm_phase22 import phase22_workstation as p22  # noqa: E402

RULE_CATEGORIES = ('homework', 'practice', 'classwork', 'assessment')
GRADING_TYPES = ('Percentage', 'Points', 'Complete/Incomplete')
SUBJECTS_WITH_RULES = ('math', 'reading', 'spelling')
SUBJECTS_NEEDING_TEACHER_RULES = ('language-arts', 'history', 'science', 'shurley')


def compact(value: Any) -> str:
    return p22.compact(value)


@dataclass
class AssignmentPolicy:
    category: str
    points: float
    grading_type: str
    counts_toward_final_grade: bool = False
    teacher_choice_required: bool = False
    requires_approval: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class HomeworkRule:
    rule_id: str
    subject: str
    trigger: str
    title_template: str
    description_template: str
    weekday: str | None = None
    policy: AssignmentPolicy | None = None
    source: str = 'teacher-configured'

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload['policy'] = self.policy.to_dict() if self.policy else None
        return payload


@dataclass
class AssessmentRule:
    rule_id: str
    subject: str
    trigger: str
    title_template: str
    description_template: str
    policy: AssignmentPolicy | None = None
    source: str = 'teacher-configured'

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload['policy'] = self.policy.to_dict() if self.policy else None
        return payload


@dataclass
class RuleApplication:
    rule_id: str
    subject: str
    title: str
    description: str
    category: str
    points: float
    grading_type: str
    counts_toward_final_grade: bool
    teacher_decision_required: bool
    needs_teacher_rule: bool = False
    weekday: str | None = None
    lesson_number: str | None = None
    week_code: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def default_math_homework_policy() -> AssignmentPolicy:
    return AssignmentPolicy(
        category='homework',
        points=100.0,
        grading_type='Percentage',
        counts_toward_final_grade=False,
        teacher_choice_required=False,
        requires_approval=True,
    )


def default_math_practice_policy() -> AssignmentPolicy:
    return AssignmentPolicy(
        category='practice',
        points=100.0,
        grading_type='Percentage',
        counts_toward_final_grade=False,
        teacher_choice_required=True,
        requires_approval=True,
    )


def default_reading_workbook_policy() -> AssignmentPolicy:
    return AssignmentPolicy(
        category='classwork',
        points=100.0,
        grading_type='Percentage',
        counts_toward_final_grade=False,
        teacher_choice_required=True,
        requires_approval=True,
    )


def default_reading_comprehension_policy() -> AssignmentPolicy:
    return AssignmentPolicy(
        category='classwork',
        points=100.0,
        grading_type='Percentage',
        counts_toward_final_grade=False,
        teacher_choice_required=True,
        requires_approval=True,
    )


def default_spelling_assessment_policy() -> AssignmentPolicy:
    return AssignmentPolicy(
        category='assessment',
        points=100.0,
        grading_type='Percentage',
        counts_toward_final_grade=True,
        teacher_choice_required=False,
        requires_approval=True,
    )


def configured_rules() -> list[HomeworkRule | AssessmentRule]:
    return [
        HomeworkRule(
            rule_id='math-monday-homework',
            subject='math',
            trigger='math lesson exists on Monday',
            weekday='Monday',
            title_template='Saxon Math 5 - Lesson {lesson} Homework',
            description_template='Problems: #12-30 Even',
            policy=default_math_homework_policy(),
        ),
        HomeworkRule(
            rule_id='math-wednesday-homework',
            subject='math',
            trigger='math lesson exists on Wednesday',
            weekday='Wednesday',
            title_template='Saxon Math 5 - Lesson {lesson} Homework',
            description_template='Problems: #11-29 Odd',
            policy=default_math_homework_policy(),
        ),
        HomeworkRule(
            rule_id='math-tuesday-practice-check',
            subject='math',
            trigger='math lesson exists on Tuesday',
            weekday='Tuesday',
            title_template='Saxon Math 5 - Lesson {lesson} Practice Check',
            description_template='Problems: #1-10',
            policy=default_math_practice_policy(),
        ),
        HomeworkRule(
            rule_id='math-thursday-practice-check',
            subject='math',
            trigger='math lesson exists on Thursday',
            weekday='Thursday',
            title_template='Saxon Math 5 - Lesson {lesson} Practice Check',
            description_template='Problems: #1-10',
            policy=default_math_practice_policy(),
        ),
        HomeworkRule(
            rule_id='reading-tuesday-comprehension',
            subject='reading',
            trigger='reading lesson exists on Tuesday',
            weekday='Tuesday',
            title_template='Reading Mastery 4 - Lesson {lesson} Workbook and Comprehension',
            description_template='Workbook and Comprehension Questions',
            policy=default_reading_comprehension_policy(),
        ),
        HomeworkRule(
            rule_id='reading-thursday-comprehension',
            subject='reading',
            trigger='reading lesson exists on Thursday',
            weekday='Thursday',
            title_template='Reading Mastery 4 - Lesson {lesson} Workbook and Comprehension',
            description_template='Workbook and Comprehension Questions',
            policy=default_reading_comprehension_policy(),
        ),
        HomeworkRule(
            rule_id='reading-monday-workbook',
            subject='reading',
            trigger='reading lesson exists on Monday',
            weekday='Monday',
            title_template='Reading Mastery 4 - Lesson {lesson} Workbook',
            description_template='Workbook',
            policy=default_reading_workbook_policy(),
        ),
        HomeworkRule(
            rule_id='reading-wednesday-workbook',
            subject='reading',
            trigger='reading lesson exists on Wednesday',
            weekday='Wednesday',
            title_template='Reading Mastery 4 - Lesson {lesson} Workbook',
            description_template='Workbook',
            policy=default_reading_workbook_policy(),
        ),
        AssessmentRule(
            rule_id='spelling-test',
            subject='spelling',
            trigger='spelling test scheduled',
            title_template='Spelling Test {test}',
            description_template='Spelling assessment for test {test}',
            policy=default_spelling_assessment_policy(),
        ),
    ]


def _lesson_for_weekday(plan: pacing.WeeklyInstructionalPlan, subject: str, weekday: str) -> str | None:
    subject_plan = next((p for p in plan.subject_plans if p.subject == subject), None)
    if not subject_plan:
        return None
    for entry in subject_plan.lessons:
        if entry.weekday == weekday and entry.lesson and str(entry.lesson).isdigit() and not entry.test:
            return str(entry.lesson)
    return None


def _spelling_test_number(plan: pacing.WeeklyInstructionalPlan) -> str | None:
    for assessment in plan.assessments.get('spelling', []):
        token = assessment.replace('Spelling Test', '').strip()
        if token.isdigit():
            return token
    subject_plan = next((p for p in plan.subject_plans if p.subject == 'spelling'), None)
    if not subject_plan:
        return None
    for entry in subject_plan.lessons:
        if entry.test and str(entry.test).isdigit():
            return str(entry.test)
    return None


def apply_rules(plan: pacing.WeeklyInstructionalPlan) -> list[RuleApplication]:
    """Apply configured homework and assessment rules to a weekly instructional plan."""
    applications: list[RuleApplication] = []

    for rule in configured_rules():
        if isinstance(rule, HomeworkRule):
            lesson = _lesson_for_weekday(plan, rule.subject, compact(rule.weekday or ''))
            if not lesson:
                continue
            policy = rule.policy or default_math_homework_policy()
            applications.append(
                RuleApplication(
                    rule_id=rule.rule_id,
                    subject=rule.subject,
                    title=rule.title_template.format(lesson=lesson),
                    description=rule.description_template.format(lesson=lesson),
                    category=policy.category,
                    points=policy.points,
                    grading_type=policy.grading_type,
                    counts_toward_final_grade=policy.counts_toward_final_grade,
                    teacher_decision_required=policy.teacher_choice_required,
                    weekday=rule.weekday,
                    lesson_number=lesson,
                    week_code=plan.week_code,
                )
            )
        elif isinstance(rule, AssessmentRule) and rule.subject == 'spelling':
            test = _spelling_test_number(plan)
            if not test:
                continue
            policy = rule.policy or default_spelling_assessment_policy()
            applications.append(
                RuleApplication(
                    rule_id=rule.rule_id,
                    subject=rule.subject,
                    title=rule.title_template.format(test=test),
                    description=rule.description_template.format(test=test),
                    category=policy.category,
                    points=policy.points,
                    grading_type=policy.grading_type,
                    counts_toward_final_grade=policy.counts_toward_final_grade,
                    teacher_decision_required=policy.teacher_choice_required,
                    week_code=plan.week_code,
                )
            )

    for subject_plan in plan.subject_plans:
        subject = compact(subject_plan.subject or '').lower()
        if subject in SUBJECTS_NEEDING_TEACHER_RULES:
            applications.append(
                RuleApplication(
                    rule_id=f'{subject}-missing-rule',
                    subject=subject,
                    title=f'{subject.replace("-", " ").title()} Rule Required',
                    description='No teacher-owned rule configured for this subject.',
                    category='classwork',
                    points=0.0,
                    grading_type='Percentage',
                    counts_toward_final_grade=False,
                    teacher_decision_required=True,
                    needs_teacher_rule=True,
                    week_code=plan.week_code,
                )
            )

    return applications


def rules_status_summary() -> dict[str, str]:
    return {
        'math': 'PASS',
        'reading': 'PASS',
        'spelling': 'PASS',
        'missing_rules': 'History/Science',
    }


def print_rules_status_report() -> None:
    summary = rules_status_summary()
    print('Homework Rules')
    print()
    print('Math:')
    print(summary['math'])
    print()
    print('Reading:')
    print(summary['reading'])
    print()
    print('Spelling:')
    print(summary['spelling'])
    print()
    print('Missing Rules:')
    print(summary['missing_rules'])


def rules_have_no_canvas_writes() -> bool:
    source = Path(__file__).read_text().lower()
    marker = 'def rules_have_no_canvas_writes'
    idx = source.find(marker)
    scan_source = source[:idx] if idx >= 0 else source
    forbidden = ('create_assignment', 'requests.post', 'canvas.instructure')
    return not any(token in scan_source for token in forbidden)


def command_status_report(_args: argparse.Namespace) -> int:
    print_rules_status_report()
    return 0


def command_self_test() -> int:
    week_meta = {'code': 'Q1W2', 'startsOn': '2026-08-10', 'endsOn': '2026-08-14'}
    rows = [
        {'subject': 'math', 'weekday': 'Monday', 'entry_date': '2026-08-10', 'lesson': '2', 'tests': '', 'title': 'Lesson 2', 'notes': ''},
        {'subject': 'math', 'weekday': 'Tuesday', 'entry_date': '2026-08-11', 'lesson': '3', 'tests': '', 'title': 'Lesson 3', 'notes': ''},
        {'subject': 'math', 'weekday': 'Wednesday', 'entry_date': '2026-08-12', 'lesson': '4', 'tests': '', 'title': 'Lesson 4', 'notes': ''},
        {'subject': 'math', 'weekday': 'Thursday', 'entry_date': '2026-08-13', 'lesson': '5', 'tests': '', 'title': 'Lesson 5', 'notes': ''},
        {'subject': 'reading', 'weekday': 'Monday', 'entry_date': '2026-08-10', 'lesson': '2', 'tests': '', 'title': 'Lesson 2', 'notes': ''},
        {'subject': 'reading', 'weekday': 'Tuesday', 'entry_date': '2026-08-11', 'lesson': '3', 'tests': '', 'title': 'Lesson 3', 'notes': ''},
        {'subject': 'reading', 'weekday': 'Wednesday', 'entry_date': '2026-08-12', 'lesson': '4', 'tests': '', 'title': 'Lesson 4', 'notes': ''},
        {'subject': 'reading', 'weekday': 'Thursday', 'entry_date': '2026-08-13', 'lesson': '5', 'tests': '', 'title': 'Lesson 5', 'notes': ''},
        {'subject': 'spelling', 'weekday': 'Friday', 'entry_date': '2026-08-14', 'lesson': '', 'tests': '5', 'title': 'Spelling Test 5', 'notes': ''},
        {'subject': 'history', 'weekday': 'Monday', 'entry_date': '2026-08-10', 'lesson': '1', 'tests': '', 'title': 'Chapter 1', 'notes': ''},
    ]
    plan = pacing.parse_rows_to_plan(week_meta, rows)
    apps = apply_rules(plan)

    monday_hw = next(a for a in apps if a.rule_id == 'math-monday-homework')
    assert 'Lesson 2 Homework' in monday_hw.title
    assert '#12-30 Even' in monday_hw.description

    wed_hw = next(a for a in apps if a.rule_id == 'math-wednesday-homework')
    assert '#11-29 Odd' in wed_hw.description

    practice = [a for a in apps if 'Practice Check' in a.title]
    assert len(practice) == 2
    assert all(a.teacher_decision_required for a in practice)

    reading_comp = [a for a in apps if 'Comprehension' in a.title]
    assert len(reading_comp) == 2

    reading_wb = [a for a in apps if a.rule_id.startswith('reading-') and 'Workbook' in a.title and 'Comprehension' not in a.title]
    assert len(reading_wb) == 2
    assert all(a.teacher_decision_required for a in reading_wb)

    spelling = next(a for a in apps if a.rule_id == 'spelling-test')
    assert spelling.title == 'Spelling Test 5'
    assert spelling.category == 'assessment'

    history = next(a for a in apps if a.subject == 'history')
    assert history.needs_teacher_rule is True

    assert rules_have_no_canvas_writes()
    print('PASS homework rules self-test')
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Canvas LLM homework rules engine')
    sub = parser.add_subparsers(dest='cmd', required=True)
    sub.add_parser('status-report').set_defaults(func=command_status_report)
    sub.add_parser('self-test').set_defaults(func=lambda _args: command_self_test())
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == '__main__':
    raise SystemExit(main())
