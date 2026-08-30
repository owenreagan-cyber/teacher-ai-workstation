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

from scripts.canvas_llm_phase22 import curriculum_rules as curriculum  # noqa: E402
from scripts.canvas_llm_phase22 import pacing_parser as pacing  # noqa: E402
from scripts.canvas_llm_phase22 import phase22_workstation as p22  # noqa: E402

RULE_CATEGORIES = ('homework', 'practice', 'classwork', 'assessment', 'in_class')
GRADING_TYPES = ('Percentage', 'Points', 'Complete/Incomplete')
SUBJECTS_WITH_RULES = curriculum.SUBJECTS_WITH_RULES
SUBJECTS_NEEDING_TEACHER_RULES = curriculum.SUBJECTS_NEEDING_TEACHER_RULES
MANUAL_SUBJECTS = curriculum.MANUAL_SUBJECTS


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
    entry_type: str = 'assignment'
    unit: str | None = None
    chapter: str | None = None
    lesson: str | None = None
    reason: str | None = None
    homework_enabled: bool = True
    canvas_assignment_enabled: bool = False

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


def _policy_from_grading_policy(grading_policy: dict[str, Any]) -> AssignmentPolicy:
    return AssignmentPolicy(
        category=compact(grading_policy.get('category') or 'homework'),
        points=float(grading_policy.get('points') or 100),
        grading_type=compact(grading_policy.get('grading_type') or 'Percentage'),
        counts_toward_final_grade=bool(grading_policy.get('counts_toward_final_grade', False)),
        teacher_choice_required=bool(grading_policy.get('teacher_choice_required', False)),
        requires_approval=bool(grading_policy.get('requires_approval', True)),
    )


def _trigger_summary(trigger: dict[str, Any]) -> str:
    subject = compact(trigger.get('subject') or '')
    days = trigger.get('days') or []
    if trigger.get('requires_test'):
        return f'{subject} test scheduled'
    if days:
        return f'{subject} lesson exists on {", ".join(days)}'
    return f'{subject} rule trigger'


def _weekday_from_trigger(trigger: dict[str, Any]) -> str | None:
    days = trigger.get('days') or []
    return compact(days[0]) if len(days) == 1 else None


def curriculum_rule_to_engine_rule(rule: curriculum.CurriculumRule) -> HomeworkRule | AssessmentRule:
    policy = _policy_from_grading_policy(rule.grading_policy)
    trigger = _trigger_summary(rule.trigger)
    if rule.rule_type == 'assessment':
        return AssessmentRule(
            rule_id=rule.rule_id,
            subject=rule.subject,
            trigger=trigger,
            title_template=rule.title_template,
            description_template=rule.description_template,
            policy=policy,
            source='curriculum-rule-library',
        )
    return HomeworkRule(
        rule_id=rule.rule_id,
        subject=rule.subject,
        trigger=trigger,
        weekday=_weekday_from_trigger(rule.trigger),
        title_template=rule.title_template,
        description_template=rule.description_template,
        policy=policy,
        source='curriculum-rule-library',
    )


def configured_rules(library: curriculum.CurriculumRuleLibrary | None = None) -> list[HomeworkRule | AssessmentRule]:
    return [curriculum_rule_to_engine_rule(rule) for rule in curriculum.effective_rules(library)]


def _subject_rows_for_plan(plan: pacing.WeeklyInstructionalPlan, subject: str) -> list[pacing.SubjectLessonEntry]:
    subject_plan = next((p for p in plan.subject_plans if p.subject == subject), None)
    if not subject_plan:
        return []
    return subject_plan.lessons


def _manual_row_payload(entry: pacing.SubjectLessonEntry, subject: str) -> dict[str, Any]:
    return {
        'subject': subject,
        'weekday': entry.weekday,
        'entry_date': entry.entry_date,
        'lesson': entry.lesson or '',
        'title': entry.title or '',
        'notes': entry.notes or '',
        'unit': entry.unit or '',
        'chapter': entry.chapter or '',
    }


def _in_class_application_from_entry(
    entry: curriculum.InClassEntry,
    *,
    rule_id: str,
    weekday: str | None = None,
) -> RuleApplication:
    return RuleApplication(
        rule_id=rule_id,
        subject=entry.subject,
        title=curriculum.SUBJECT_DISPLAY.get(entry.subject, entry.subject.title()),
        description=entry.summary_text(),
        category='in_class',
        points=0.0,
        grading_type='Percentage',
        counts_toward_final_grade=False,
        teacher_decision_required=False,
        weekday=weekday,
        week_code=entry.week_code,
        entry_type='in_class',
        unit=entry.unit,
        chapter=entry.chapter,
        lesson=entry.lesson,
        reason=entry.reason,
        homework_enabled=False,
        canvas_assignment_enabled=False,
    )


def apply_manual_subject_rules(
    plan: pacing.WeeklyInstructionalPlan,
    library: curriculum.CurriculumRuleLibrary,
) -> list[RuleApplication]:
    applications: list[RuleApplication] = []
    for subject in MANUAL_SUBJECTS:
        behavior = library.behavior_for_subject(subject)
        if behavior is None or not behavior.is_manual or not behavior.classroom_activity_enabled:
            continue
        for entry in _subject_rows_for_plan(plan, subject):
            row = _manual_row_payload(entry, subject)
            try:
                reference = curriculum.parse_curriculum_reference(row, behavior.reference_type)
            except ValueError:
                continue
            if not curriculum.validate_curriculum_reference(reference):
                continue
            in_class = curriculum.build_in_class_entry(
                subject,
                reference,
                weekday=entry.weekday,
                entry_date=entry.entry_date,
                week_code=plan.week_code,
            )
            applications.append(
                _in_class_application_from_entry(
                    in_class,
                    rule_id=f'{subject}-in-class',
                    weekday=entry.weekday,
                )
            )
    return applications


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


def apply_rules(
    plan: pacing.WeeklyInstructionalPlan,
    library: curriculum.CurriculumRuleLibrary | None = None,
) -> list[RuleApplication]:
    """Apply curriculum profile rules to a weekly instructional plan."""
    library = library or curriculum.load_library()
    applications: list[RuleApplication] = []

    for rule in configured_rules(library):
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

    applications.extend(apply_manual_subject_rules(plan, library))

    for subject_plan in plan.subject_plans:
        subject = compact(subject_plan.subject or '').lower()
        if subject in library.subjects_needing_teacher_rules:
            applications.append(
                RuleApplication(
                    rule_id=f'{subject}-missing-rule',
                    subject=subject,
                    title=f'{subject.replace("-", " ").title()} Rule Required',
                    description='Teacher rule required.',
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


def rules_status_summary(library: curriculum.CurriculumRuleLibrary | None = None) -> dict[str, str]:
    summary = curriculum.curriculum_rules_status_summary(library)
    return {
        'math': summary['math'],
        'reading': summary['reading'],
        'spelling': summary['spelling'],
        'missing_rules': 'Language Arts',
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
        {'subject': 'history', 'weekday': 'Monday', 'entry_date': '2026-08-10', 'lesson': '8', 'tests': '', 'title': 'Chapter 8', 'notes': '', 'unit': 'The American Revolution', 'chapter': '8'},
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
    assert history.entry_type == 'in_class'
    assert history.homework_enabled is False
    assert history.canvas_assignment_enabled is False
    assert 'The American Revolution' in history.description
    assert not any(a.category == 'homework' and a.subject in MANUAL_SUBJECTS for a in apps)

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
