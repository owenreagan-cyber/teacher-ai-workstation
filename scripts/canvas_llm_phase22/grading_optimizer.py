#!/usr/bin/env python3
"""Grading balance optimizer for C1L1 — planning intelligence only, no Canvas writes."""
from __future__ import annotations

import argparse
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.canvas_llm_phase22 import assignment_draft_generator as drafts  # noqa: E402
from scripts.canvas_llm_phase22 import homework_rules as rules  # noqa: E402
from scripts.canvas_llm_phase22 import pacing_parser as pacing  # noqa: E402
from scripts.canvas_llm_phase22 import phase22_workstation as p22  # noqa: E402

GRADING_MODES = ('FIXED_COUNTED', 'TEACHER_SELECTED_DAY', 'MANUAL')
NORMAL_WEEK_TARGET = 3
FULL_WEEK_DAYS = 5
WEEKDAYS = pacing.WEEKDAYS

MATH_CLASSWORK_DAYS = ('Tuesday', 'Thursday')
READING_CLASSWORK_DAYS = ('Monday', 'Wednesday')

RULE_GRADING_MODE: dict[str, str] = {
    'math-monday-homework': 'FIXED_COUNTED',
    'math-wednesday-homework': 'FIXED_COUNTED',
    'math-tuesday-practice-check': 'TEACHER_SELECTED_DAY',
    'math-thursday-practice-check': 'TEACHER_SELECTED_DAY',
    'reading-tuesday-comprehension': 'FIXED_COUNTED',
    'reading-thursday-comprehension': 'FIXED_COUNTED',
    'reading-monday-workbook': 'TEACHER_SELECTED_DAY',
    'reading-wednesday-workbook': 'TEACHER_SELECTED_DAY',
    'spelling-test': 'FIXED_COUNTED',
}

MATH_RECOMMENDED_RULES = (
    'math-monday-homework',
    'math-tuesday-practice-check',
    'math-wednesday-homework',
)
MATH_DEFERRED_RULES = ('math-thursday-practice-check',)

READING_RECOMMENDED_RULES = (
    'reading-tuesday-comprehension',
    'reading-wednesday-workbook',
    'reading-thursday-comprehension',
)
READING_DEFERRED_RULES = ('reading-monday-workbook',)

Q1W2_WEEK_META: dict[str, Any] = {
    'code': 'Q1W2',
    'startsOn': '2026-07-27',
    'endsOn': '2026-07-31',
    'quarter': 1,
    'week': 2,
    'displaySubtitle': 'Quarter 1, Week 2 | July 27-31, 2026',
}

Q1W2_INPUT_ROWS: list[dict[str, Any]] = [
    {'subject': 'math', 'weekday': 'Monday', 'entry_date': '2026-07-27', 'lesson': '2', 'tests': '', 'title': 'Lesson 2', 'notes': ''},
    {'subject': 'math', 'weekday': 'Tuesday', 'entry_date': '2026-07-28', 'lesson': '3', 'tests': '', 'title': 'Lesson 3', 'notes': ''},
    {'subject': 'math', 'weekday': 'Wednesday', 'entry_date': '2026-07-29', 'lesson': '4', 'tests': '', 'title': 'Lesson 4', 'notes': ''},
    {'subject': 'math', 'weekday': 'Thursday', 'entry_date': '2026-07-30', 'lesson': '5', 'tests': '', 'title': 'Lesson 5', 'notes': ''},
    {'subject': 'math', 'weekday': 'Friday', 'entry_date': '2026-07-31', 'lesson': '6', 'tests': '', 'title': 'Lesson 6', 'notes': ''},
    {'subject': 'reading', 'weekday': 'Monday', 'entry_date': '2026-07-27', 'lesson': '2', 'tests': '', 'title': 'Lesson 2', 'notes': ''},
    {'subject': 'reading', 'weekday': 'Tuesday', 'entry_date': '2026-07-28', 'lesson': '3', 'tests': '', 'title': 'Lesson 3', 'notes': ''},
    {'subject': 'reading', 'weekday': 'Wednesday', 'entry_date': '2026-07-29', 'lesson': '4', 'tests': '', 'title': 'Lesson 4', 'notes': ''},
    {'subject': 'reading', 'weekday': 'Thursday', 'entry_date': '2026-07-30', 'lesson': '5', 'tests': '', 'title': 'Lesson 5', 'notes': ''},
    {'subject': 'reading', 'weekday': 'Friday', 'entry_date': '2026-07-31', 'lesson': '6', 'tests': '', 'title': 'Lesson 6', 'notes': ''},
    {'subject': 'spelling', 'weekday': 'Friday', 'entry_date': '2026-07-31', 'lesson': '', 'tests': '5', 'title': 'Spelling Test 5', 'notes': ''},
]

_OVERRIDE_STORE: dict[str, 'GradingOverride'] = {}


def compact(value: Any) -> str:
    return p22.compact(value)


@dataclass
class GradeItem:
    rule_id: str
    subject: str
    title: str
    weekday: str | None
    grading_mode: str
    category: str
    is_assessment: bool = False
    assignment_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class GradingOptimizationResult:
    subject: str
    week_code: str
    instructional_days: int
    required_grade_count: int
    available_grade_items: list[str] = field(default_factory=list)
    recommended_grade_items: list[str] = field(default_factory=list)
    deferred_items: list[str] = field(default_factory=list)
    assessment_conflicts: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    teacher_override_required: bool = False
    reasoning: str = ''
    grading_mode: str = 'FIXED_COUNTED'
    status: str = 'READY'

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class GradingOverride:
    override_id: str
    subject: str
    week_code: str
    assignment_id: str
    recommended_choice: str
    teacher_choice: str
    reason: str
    created_at: str
    reverted_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class WeeklyGradingPlan:
    week_code: str
    instructional_days: int
    subject_results: list[GradingOptimizationResult] = field(default_factory=list)
    assessments: list[str] = field(default_factory=list)
    teacher_decisions: list[dict[str, Any]] = field(default_factory=list)
    short_week: bool = False
    assessment_conflict: bool = False

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload['subject_results'] = [item.to_dict() for item in self.subject_results]
        return payload


def _instructional_day_count(plan: pacing.WeeklyInstructionalPlan) -> int:
    days: set[str] = set()
    for subject_plan in plan.subject_plans:
        for entry in subject_plan.lessons:
            if entry.weekday:
                days.add(entry.weekday)
    return len(days)


def _application_to_grade_item(app: rules.RuleApplication) -> GradeItem:
    mode = RULE_GRADING_MODE.get(app.rule_id, 'FIXED_COUNTED')
    draft = drafts.application_to_draft(app)
    return GradeItem(
        rule_id=app.rule_id,
        subject=app.subject,
        title=app.title,
        weekday=app.weekday,
        grading_mode=mode,
        category=app.category,
        is_assessment=app.category == 'assessment',
        assignment_id=draft.artifact_id,
    )


def _grade_items_for_subject(
    applications: list[rules.RuleApplication],
    subject: str,
) -> list[GradeItem]:
    return [
        _application_to_grade_item(app)
        for app in applications
        if app.subject == subject and not app.needs_teacher_rule
    ]


def _assessment_days(plan: pacing.WeeklyInstructionalPlan, applications: list[rules.RuleApplication]) -> list[str]:
    days: list[str] = []
    for app in applications:
        if app.category == 'assessment':
            for subject_plan in plan.subject_plans:
                if subject_plan.subject != app.subject:
                    continue
                for entry in subject_plan.lessons:
                    if entry.test:
                        days.append(entry.weekday)
    return days


def _label_for_item(item: GradeItem) -> str:
    if 'Homework' in item.title:
        return item.title.replace('Saxon Math 5 - ', '').replace('Reading Mastery 4 - ', '')
    if 'Practice Check' in item.title:
        return f'{item.weekday} Classwork'
    if 'Workbook and Comprehension' in item.title:
        return item.title.replace('Reading Mastery 4 - ', '')
    if 'Workbook' in item.title and 'Comprehension' not in item.title:
        return f'{item.weekday} Workbook'
    return item.title


def optimize_math(
    items: list[GradeItem],
    *,
    week_code: str,
    instructional_days: int,
    assessment_days: list[str],
) -> GradingOptimizationResult:
    available = [_label_for_item(i) for i in items]
    by_rule = {item.rule_id: item for item in items}
    warnings: list[str] = []
    assessment_conflicts: list[str] = []
    teacher_override_required = False
    reasoning_parts: list[str] = []

    if instructional_days < FULL_WEEK_DAYS:
        teacher_override_required = True
        warnings.append('Short week detected.')
        warnings.append('Do not automatically reduce grades.')
        reasoning_parts.append(
            f'Short week: {instructional_days} instructional days; teacher approval required.'
        )

    recommended_items = [
        _label_for_item(by_rule[rule_id])
        for rule_id in MATH_RECOMMENDED_RULES
        if rule_id in by_rule
    ]
    deferred_items = [
        _label_for_item(by_rule[rule_id])
        for rule_id in MATH_DEFERRED_RULES
        if rule_id in by_rule
    ]

    for day in assessment_days:
        thursday = by_rule.get('math-thursday-practice-check')
        if thursday and thursday.weekday == day:
            assessment_conflicts.append(f'Avoid grading {day} classwork near assessment load.')
            if _label_for_item(thursday) in recommended_items:
                recommended_items = [i for i in recommended_items if i != _label_for_item(thursday)]
                if _label_for_item(thursday) not in deferred_items:
                    deferred_items.append(_label_for_item(thursday))

    if not assessment_conflicts and len(recommended_items) == NORMAL_WEEK_TARGET:
        reasoning_parts.append('Three evenly distributed grades: Monday homework, Tuesday classwork, Wednesday homework.')
        reasoning_parts.append('Thursday classwork deferred to avoid grading overload.')

    status = 'TEACHER REVIEW REQUIRED' if teacher_override_required else 'READY'
    if instructional_days < FULL_WEEK_DAYS and len(recommended_items) > instructional_days:
        warnings.append(f'Required: {NORMAL_WEEK_TARGET}')
        warnings.append(f'Available: {instructional_days}')

    return GradingOptimizationResult(
        subject='math',
        week_code=week_code,
        instructional_days=instructional_days,
        required_grade_count=NORMAL_WEEK_TARGET,
        available_grade_items=available,
        recommended_grade_items=recommended_items,
        deferred_items=deferred_items,
        assessment_conflicts=assessment_conflicts,
        warnings=warnings,
        teacher_override_required=teacher_override_required,
        reasoning=' '.join(reasoning_parts),
        grading_mode='TEACHER_SELECTED_DAY',
        status=status,
    )


def optimize_reading(
    items: list[GradeItem],
    *,
    week_code: str,
    instructional_days: int,
    assessment_days: list[str],
) -> GradingOptimizationResult:
    available = [_label_for_item(i) for i in items]
    by_rule = {item.rule_id: item for item in items}
    warnings: list[str] = []
    assessment_conflicts: list[str] = []
    teacher_override_required = False
    reasoning_parts: list[str] = []

    if instructional_days < FULL_WEEK_DAYS:
        teacher_override_required = True
        warnings.append('Short week detected.')
        warnings.append('Do not automatically reduce grades.')

    recommended_items = [
        _label_for_item(by_rule[rule_id])
        for rule_id in READING_RECOMMENDED_RULES
        if rule_id in by_rule
    ]
    deferred_items = [
        _label_for_item(by_rule[rule_id])
        for rule_id in READING_DEFERRED_RULES
        if rule_id in by_rule
    ]

    for day in assessment_days:
        for item in items:
            if item.weekday == day and not item.is_assessment:
                assessment_conflicts.append(f'Avoid additional {day} graded reading items near assessment.')
                label = _label_for_item(item)
                if label in recommended_items:
                    recommended_items = [i for i in recommended_items if i != label]
                    if label not in deferred_items:
                        deferred_items.append(label)

    if len(recommended_items) == NORMAL_WEEK_TARGET:
        reasoning_parts.append(
            'Tuesday homework, Wednesday workbook, Thursday homework for balanced reading grades.'
        )
        reasoning_parts.append('Remaining workbook deferred.')

    status = 'TEACHER REVIEW REQUIRED' if teacher_override_required else 'READY'

    return GradingOptimizationResult(
        subject='reading',
        week_code=week_code,
        instructional_days=instructional_days,
        required_grade_count=NORMAL_WEEK_TARGET,
        available_grade_items=available,
        recommended_grade_items=recommended_items,
        deferred_items=deferred_items,
        assessment_conflicts=assessment_conflicts,
        warnings=warnings,
        teacher_override_required=teacher_override_required,
        reasoning=' '.join(reasoning_parts),
        grading_mode='TEACHER_SELECTED_DAY',
        status=status,
    )


def optimize_spelling(
    items: list[GradeItem],
    *,
    week_code: str,
    instructional_days: int,
    assessment_days: list[str],
) -> GradingOptimizationResult:
    available = [_label_for_item(i) for i in items]
    recommended = available[:]
    warnings: list[str] = []
    if 'Friday' in assessment_days:
        warnings.append('Friday assessment recognized; avoid additional Friday graded items.')
    return GradingOptimizationResult(
        subject='spelling',
        week_code=week_code,
        instructional_days=instructional_days,
        required_grade_count=len(recommended),
        available_grade_items=available,
        recommended_grade_items=recommended,
        deferred_items=[],
        assessment_conflicts=[],
        warnings=warnings,
        teacher_override_required=False,
        reasoning='Assessments count automatically.',
        grading_mode='FIXED_COUNTED',
        status='READY',
    )


def build_teacher_decisions(
    math_result: GradingOptimizationResult,
    reading_result: GradingOptimizationResult,
    applications: list[rules.RuleApplication],
) -> list[dict[str, Any]]:
    decisions: list[dict[str, Any]] = []
    by_rule = {app.rule_id: app for app in applications}

    math_tuesday = by_rule.get('math-tuesday-practice-check')
    math_thursday = by_rule.get('math-thursday-practice-check')
    if math_tuesday and math_thursday:
        draft_tue = drafts.application_to_draft(math_tuesday)
        decisions.append({
            'subject': 'math',
            'prompt': 'Which day is recorded for Math Classwork?',
            'recommended_choice': 'Tuesday Classwork',
            'alternate_choice': 'Thursday Classwork',
            'recommended_rule_id': 'math-tuesday-practice-check',
            'alternate_rule_id': 'math-thursday-practice-check',
            'assignment_id': draft_tue.artifact_id,
            'automatic_selection': False,
        })

    reading_mon = by_rule.get('reading-monday-workbook')
    reading_wed = by_rule.get('reading-wednesday-workbook')
    if reading_mon and reading_wed:
        draft_wed = drafts.application_to_draft(reading_wed)
        decisions.append({
            'subject': 'reading',
            'prompt': 'Which day is recorded for Reading Workbook classwork?',
            'recommended_choice': 'Wednesday Workbook',
            'alternate_choice': 'Monday Workbook',
            'recommended_rule_id': 'reading-wednesday-workbook',
            'alternate_rule_id': 'reading-monday-workbook',
            'assignment_id': draft_wed.artifact_id,
            'automatic_selection': False,
        })

    return decisions


def optimize_week(
    plan: pacing.WeeklyInstructionalPlan,
    applications: list[rules.RuleApplication] | None = None,
) -> WeeklyGradingPlan:
    applications = applications or rules.apply_rules(plan)
    instructional_days = _instructional_day_count(plan)
    assessment_days = _assessment_days(plan, applications)
    short_week = instructional_days < FULL_WEEK_DAYS

    math_items = _grade_items_for_subject(applications, 'math')
    reading_items = _grade_items_for_subject(applications, 'reading')
    spelling_items = _grade_items_for_subject(applications, 'spelling')

    math_result = optimize_math(
        math_items,
        week_code=plan.week_code,
        instructional_days=instructional_days,
        assessment_days=assessment_days,
    )
    reading_result = optimize_reading(
        reading_items,
        week_code=plan.week_code,
        instructional_days=instructional_days,
        assessment_days=assessment_days,
    )
    spelling_result = optimize_spelling(
        spelling_items,
        week_code=plan.week_code,
        instructional_days=instructional_days,
        assessment_days=assessment_days,
    )

    teacher_decisions = build_teacher_decisions(math_result, reading_result, applications)
    assessments = [_label_for_item(i) for i in spelling_items]

    return WeeklyGradingPlan(
        week_code=plan.week_code,
        instructional_days=instructional_days,
        subject_results=[math_result, reading_result, spelling_result],
        assessments=assessments,
        teacher_decisions=teacher_decisions,
        short_week=short_week,
        assessment_conflict=bool(
            assessment_days and (math_result.assessment_conflicts or reading_result.assessment_conflicts)
        ),
    )


def build_q1w2_grading_plan() -> WeeklyGradingPlan:
    plan = pacing.parse_rows_to_plan(Q1W2_WEEK_META, Q1W2_INPUT_ROWS)
    return optimize_week(plan)


def create_grading_override(
    *,
    subject: str,
    week_code: str,
    assignment_id: str,
    recommended_choice: str,
    teacher_choice: str,
    reason: str,
) -> GradingOverride:
    override_id = p22.stable_id('grading-override', subject, week_code, assignment_id, teacher_choice)
    override = GradingOverride(
        override_id=override_id,
        subject=compact(subject),
        week_code=compact(week_code),
        assignment_id=compact(assignment_id),
        recommended_choice=compact(recommended_choice),
        teacher_choice=compact(teacher_choice),
        reason=compact(reason),
        created_at=p22.now_utc(),
    )
    _OVERRIDE_STORE[override_id] = override
    return override


def get_grading_override(override_id: str) -> GradingOverride | None:
    override = _OVERRIDE_STORE.get(compact(override_id))
    if override and override.reverted_at:
        return None
    return override


def list_grading_overrides(*, week_code: str | None = None, subject: str | None = None) -> list[GradingOverride]:
    results: list[GradingOverride] = []
    for override in _OVERRIDE_STORE.values():
        if override.reverted_at:
            continue
        if week_code and override.week_code != compact(week_code):
            continue
        if subject and override.subject != compact(subject):
            continue
        results.append(override)
    return results


def revert_grading_override(override_id: str) -> GradingOverride | None:
    override = _OVERRIDE_STORE.get(compact(override_id))
    if override is None:
        return None
    override.reverted_at = p22.now_utc()
    return override


def grading_optimization_dashboard_summary(plan: WeeklyGradingPlan | None = None) -> dict[str, list[str]]:
    plan = plan or build_q1w2_grading_plan()
    ready: list[str] = []
    needs_review: list[str] = []
    for result in plan.subject_results:
        if result.subject in {'math', 'reading'}:
            label = result.subject.title()
            if result.status == 'READY':
                ready.append(label)
            else:
                needs_review.append(label)
    if plan.short_week and 'Short week' not in needs_review:
        needs_review.append('Short week')
    if plan.assessment_conflict and 'Assessment conflict' not in needs_review:
        needs_review.append('Assessment conflict')
    return {'ready': ready, 'needs_review': needs_review}


def print_grading_optimization_preview_report(plan: WeeklyGradingPlan | None = None) -> None:
    plan = plan or build_q1w2_grading_plan()
    math_result = next(r for r in plan.subject_results if r.subject == 'math')
    reading_result = next(r for r in plan.subject_results if r.subject == 'reading')

    print('Grading Optimization Preview')
    print()
    print('Week:')
    print(plan.week_code)
    print()
    print('Math:')
    print(f'{len(math_result.recommended_grade_items)} recommended grades')
    print()
    print('Reading:')
    print(f'{len(reading_result.recommended_grade_items)} recommended grades')
    print()
    print('Assessments:')
    print(len(plan.assessments))
    print()
    print('Teacher Decisions:')
    print(len(plan.teacher_decisions))
    print()
    print('No Canvas writes performed.')


def print_q1w2_grading_plan_report(plan: WeeklyGradingPlan | None = None) -> None:
    plan = plan or build_q1w2_grading_plan()
    print('Q1W2 Grading Plan')
    print()
    for result in plan.subject_results:
        if result.subject == 'spelling':
            print('Spelling:')
            for item in result.recommended_grade_items:
                print(f'✓ {item}')
            print()
            continue
        print(result.subject.title())
        print()
        print('Target:')
        print(f'{result.required_grade_count} grades')
        print()
        print('Recommended:')
        for item in result.recommended_grade_items:
            print(f'✓ {item}')
        if result.deferred_items:
            print()
            print('Deferred:')
            for item in result.deferred_items:
                print(item)
        print()


def optimizer_performs_no_canvas_writes() -> bool:
    source = Path(__file__).read_text().lower()
    marker = 'def optimizer_performs_no_canvas_writes'
    idx = source.find(marker)
    scan_source = source[:idx] if idx >= 0 else source
    forbidden = (
        'create_assignment',
        'create_page',
        'requests.post',
        'canvas.instructure',
        'attempt_write',
        'modify_grade',
        'gradebook',
    )
    return not any(token in scan_source for token in forbidden)


def command_preview_report(_args: argparse.Namespace) -> int:
    print_grading_optimization_preview_report()
    return 0


def command_q1w2_plan_report(_args: argparse.Namespace) -> int:
    print_q1w2_grading_plan_report()
    return 0


def command_self_test() -> int:
    _OVERRIDE_STORE.clear()

    plan = build_q1w2_grading_plan()
    assert plan.week_code == 'Q1W2'
    assert plan.instructional_days == 5
    assert not plan.short_week

    math_result = next(r for r in plan.subject_results if r.subject == 'math')
    assert len(math_result.recommended_grade_items) == 3
    assert any('Lesson 2 Homework' in item for item in math_result.recommended_grade_items)
    assert any('Tuesday Classwork' in item for item in math_result.recommended_grade_items)
    assert any('Lesson 4 Homework' in item for item in math_result.recommended_grade_items)
    assert any('Thursday Classwork' in item for item in math_result.deferred_items)

    reading_result = next(r for r in plan.subject_results if r.subject == 'reading')
    assert len(reading_result.recommended_grade_items) == 3
    assert any('Lesson 3' in item for item in reading_result.recommended_grade_items)
    assert any('Wednesday Workbook' in item for item in reading_result.recommended_grade_items)
    assert any('Lesson 5' in item for item in reading_result.recommended_grade_items)

    spelling_result = next(r for r in plan.subject_results if r.subject == 'spelling')
    assert spelling_result.recommended_grade_items == ['Spelling Test 5']

    assert len(plan.teacher_decisions) == 2
    assert all(d['automatic_selection'] is False for d in plan.teacher_decisions)

    short_meta = {'code': 'Q1W3', 'startsOn': '2026-08-03', 'endsOn': '2026-08-05'}
    short_rows = [
        {'subject': 'math', 'weekday': 'Monday', 'entry_date': '2026-08-03', 'lesson': '2', 'tests': '', 'title': 'Lesson 2', 'notes': ''},
        {'subject': 'math', 'weekday': 'Tuesday', 'entry_date': '2026-08-04', 'lesson': '3', 'tests': '', 'title': 'Lesson 3', 'notes': ''},
        {'subject': 'math', 'weekday': 'Wednesday', 'entry_date': '2026-08-05', 'lesson': '4', 'tests': '', 'title': 'Lesson 4', 'notes': ''},
        {'subject': 'reading', 'weekday': 'Monday', 'entry_date': '2026-08-03', 'lesson': '2', 'tests': '', 'title': 'Lesson 2', 'notes': ''},
    ]
    short_plan = pacing.parse_rows_to_plan(short_meta, short_rows)
    short_result = optimize_week(short_plan)
    assert short_result.short_week is True
    math_short = next(r for r in short_result.subject_results if r.subject == 'math')
    assert math_short.status == 'TEACHER REVIEW REQUIRED'
    assert any('Short week' in w for w in math_short.warnings)

    override = create_grading_override(
        subject='math',
        week_code='Q1W2',
        assignment_id='artifact-math-classwork',
        recommended_choice='Tuesday Classwork',
        teacher_choice='Thursday Classwork',
        reason='More representative of mastery',
    )
    assert override.override_id
    stored = get_grading_override(override.override_id)
    assert stored is not None
    assert stored.teacher_choice == 'Thursday Classwork'
    reverted = revert_grading_override(override.override_id)
    assert reverted is not None and reverted.reverted_at
    assert get_grading_override(override.override_id) is None

    summary = grading_optimization_dashboard_summary(plan)
    assert 'Math' in summary['ready']
    assert 'Reading' in summary['ready']

    assert optimizer_performs_no_canvas_writes()
    print('PASS grading optimizer self-test')
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Canvas LLM grading balance optimizer')
    sub = parser.add_subparsers(dest='cmd', required=True)
    sub.add_parser('preview-report').set_defaults(func=command_preview_report)
    sub.add_parser('q1w2-plan-report').set_defaults(func=command_q1w2_plan_report)
    sub.add_parser('self-test').set_defaults(func=lambda _args: command_self_test())
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == '__main__':
    raise SystemExit(main())
