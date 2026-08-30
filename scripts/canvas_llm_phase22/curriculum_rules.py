#!/usr/bin/env python3
"""Curriculum Rule Library for C1J/C1J.1 — teacher-owned rules, profiles, and behavior lockdown."""
from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.canvas_llm_phase22 import phase22_workstation as p22  # noqa: E402

RULE_TYPES = ('homework', 'practice', 'classwork', 'assessment', 'grading_policy')
GENERATION_MODES = ('AUTO', 'MANUAL')
REFERENCE_TYPES = ('unit_chapter', 'chapter_lesson', 'lesson')
VALIDATION_STATES = ('PASS', 'MANUAL_MODE', 'NEEDS_TEACHER_RULE', 'INVALID')
AUTO_SUBJECTS = ('math', 'reading', 'spelling')
MANUAL_SUBJECTS = ('history', 'science', 'shurley')
SUBJECTS_WITH_RULES = AUTO_SUBJECTS
SUBJECTS_NEEDING_TEACHER_RULES = ('language-arts',)
SUBJECT_DISPLAY = {
    'math': 'Math',
    'reading': 'Reading',
    'spelling': 'Spelling',
    'history': 'History',
    'science': 'Science',
    'shurley': 'Shurley English',
    'language-arts': 'Language Arts',
}
STATUS_SUBJECT_ORDER = ('math', 'reading', 'spelling', 'history', 'science', 'shurley')
STATUS_SUBJECT_LABEL = {
    'math': 'Math',
    'reading': 'Reading',
    'spelling': 'Spelling',
    'history': 'History',
    'science': 'Science',
    'shurley': 'Shurley',
}
MANUAL_TEACHER_RULE_REASON = 'Manual Teacher Rule'
SHURLEY_CHAPTER_LESSON_RE = re.compile(r'^(\d+)\.(\d+)$')

DEFAULT_LIBRARY_PATH = REPO_ROOT / 'config/curriculum/canvas/curriculum-rule-library-2026-2027-grade-4.json'
DEFAULT_OVERRIDES_PATH = REPO_ROOT / 'config/curriculum/canvas/curriculum-rule-overrides-2026-2027.json'


def compact(value: Any) -> str:
    return p22.compact(value)


def jd(value: Any) -> str:
    return p22.jd(value)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


@dataclass
class CurriculumReference:
    reference_type: str
    unit: str | None = None
    chapter: str | None = None
    lesson: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def is_complete(self) -> bool:
        if self.reference_type == 'unit_chapter':
            return bool(compact(self.unit or '')) and bool(compact(self.chapter or ''))
        if self.reference_type == 'chapter_lesson':
            return bool(compact(self.chapter or '')) and bool(compact(self.lesson or ''))
        if self.reference_type == 'lesson':
            return bool(compact(self.lesson or ''))
        return False


@dataclass
class SubjectBehavior:
    subject: str
    generation_mode: str
    classroom_activity_enabled: bool
    homework_generation_enabled: bool
    canvas_assignment_generation_enabled: bool | str
    reference_type: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> SubjectBehavior:
        canvas_flag = payload.get('canvas_assignment_generation_enabled')
        if isinstance(canvas_flag, str):
            canvas_value: bool | str = compact(canvas_flag)
        else:
            canvas_value = bool(canvas_flag)
        return cls(
            subject=compact(payload.get('subject') or '').lower(),
            generation_mode=compact(payload.get('generation_mode') or 'MANUAL').upper(),
            classroom_activity_enabled=bool(payload.get('classroom_activity_enabled', False)),
            homework_generation_enabled=bool(payload.get('homework_generation_enabled', False)),
            canvas_assignment_generation_enabled=canvas_value,
            reference_type=compact(payload.get('reference_type') or ''),
        )

    @property
    def is_auto(self) -> bool:
        return self.generation_mode == 'AUTO'

    @property
    def is_manual(self) -> bool:
        return self.generation_mode == 'MANUAL'

    @property
    def canvas_enabled(self) -> bool:
        return self.canvas_assignment_generation_enabled is True


@dataclass
class InClassEntry:
    subject: str
    entry_type: str
    unit: str | None = None
    chapter: str | None = None
    lesson: str | None = None
    reason: str = MANUAL_TEACHER_RULE_REASON
    weekday: str | None = None
    entry_date: str | None = None
    week_code: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def display_lines(self) -> list[str]:
        display = SUBJECT_DISPLAY.get(self.subject, self.subject.title())
        lines = [display, 'Type:', 'In Class']
        if self.unit:
            lines.extend(['Unit:', self.unit])
        if self.chapter and self.lesson:
            lines.append(f'Chapter {self.chapter}, Lesson {self.lesson}')
        elif self.chapter:
            lines.extend(['Chapter:', self.chapter])
        elif self.lesson:
            lines.extend(['Lesson:', self.lesson])
        lines.extend(['Reason:', self.reason])
        return lines

    def summary_text(self) -> str:
        return '\n'.join(self.display_lines())


@dataclass
class CurriculumRule:
    rule_id: str
    school_year: str
    grade_level: str
    subject: str
    curriculum_program: str
    rule_type: str
    trigger: dict[str, Any]
    generation_pattern: str
    grading_policy: dict[str, Any]
    teacher_decision_required: bool
    active: bool
    created_at: str
    updated_at: str
    title_template: str = ''
    description_template: str = ''

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> CurriculumRule:
        return cls(
            rule_id=compact(payload.get('rule_id') or ''),
            school_year=compact(payload.get('school_year') or ''),
            grade_level=compact(payload.get('grade_level') or ''),
            subject=compact(payload.get('subject') or '').lower(),
            curriculum_program=compact(payload.get('curriculum_program') or ''),
            rule_type=compact(payload.get('rule_type') or ''),
            trigger=dict(payload.get('trigger') or {}),
            generation_pattern=compact(payload.get('generation_pattern') or ''),
            grading_policy=dict(payload.get('grading_policy') or {}),
            teacher_decision_required=bool(payload.get('teacher_decision_required', False)),
            active=bool(payload.get('active', True)),
            created_at=compact(payload.get('created_at') or p22.now_utc()),
            updated_at=compact(payload.get('updated_at') or p22.now_utc()),
            title_template=compact(payload.get('title_template') or ''),
            description_template=compact(payload.get('description_template') or ''),
        )


@dataclass
class CurriculumProfile:
    profile_id: str
    school_year: str
    teacher: str
    grade_level: str
    active_rules: list[str] = field(default_factory=list)
    label: str = ''
    curriculum_programs: list[str] = field(default_factory=list)
    created_at: str = ''

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> CurriculumProfile:
        return cls(
            profile_id=compact(payload.get('profile_id') or ''),
            school_year=compact(payload.get('school_year') or ''),
            teacher=compact(payload.get('teacher') or ''),
            grade_level=compact(payload.get('grade_level') or ''),
            active_rules=[compact(r) for r in (payload.get('active_rules') or []) if compact(r)],
            label=compact(payload.get('label') or ''),
            curriculum_programs=[compact(p) for p in (payload.get('curriculum_programs') or []) if compact(p)],
            created_at=compact(payload.get('created_at') or p22.now_utc()),
        )


@dataclass
class RuleOverride:
    override_id: str
    rule_id: str
    school_year: str
    field_changed: str
    old_value: Any
    new_value: Any
    reason: str
    created_at: str
    active: bool = True
    reversible: bool = True
    reverted_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> RuleOverride:
        return cls(
            override_id=compact(payload.get('override_id') or ''),
            rule_id=compact(payload.get('rule_id') or ''),
            school_year=compact(payload.get('school_year') or ''),
            field_changed=compact(payload.get('field_changed') or ''),
            old_value=payload.get('old_value'),
            new_value=payload.get('new_value'),
            reason=compact(payload.get('reason') or ''),
            created_at=compact(payload.get('created_at') or p22.now_utc()),
            active=bool(payload.get('active', True)),
            reversible=bool(payload.get('reversible', True)),
            reverted_at=compact(payload.get('reverted_at') or '') or None,
        )


@dataclass
class RuleValidation:
    subject: str
    state: str
    message: str
    rule_count: int = 0
    generation_mode: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CurriculumRuleLibrary:
    profile: CurriculumProfile
    rules: list[CurriculumRule]
    subject_behaviors: list[SubjectBehavior] = field(default_factory=list)
    subjects_needing_teacher_rules: list[str] = field(default_factory=list)
    overrides: list[RuleOverride] = field(default_factory=list)
    audit_history: list[dict[str, Any]] = field(default_factory=list)

    def rule_by_id(self, rule_id: str) -> CurriculumRule | None:
        return next((rule for rule in self.rules if rule.rule_id == rule_id), None)

    def behavior_for_subject(self, subject: str) -> SubjectBehavior | None:
        subject_key = compact(subject).lower()
        return next((b for b in self.subject_behaviors if b.subject == subject_key), None)

    def active_rules(self) -> list[CurriculumRule]:
        active_ids = set(self.profile.active_rules)
        return [rule for rule in self.rules if rule.rule_id in active_ids and rule.active]

    def active_overrides(self) -> list[RuleOverride]:
        return [override for override in self.overrides if override.active and not override.reverted_at]


def load_library(
    library_path: Path | None = None,
    overrides_path: Path | None = None,
) -> CurriculumRuleLibrary:
    library_path = library_path or DEFAULT_LIBRARY_PATH
    overrides_path = overrides_path or DEFAULT_OVERRIDES_PATH
    payload = load_json(library_path)
    profile = CurriculumProfile.from_dict(payload.get('profile') or {})
    rules = [CurriculumRule.from_dict(row) for row in (payload.get('rules') or [])]
    behaviors = [SubjectBehavior.from_dict(row) for row in (payload.get('subject_behaviors') or [])]
    subjects = [compact(s).lower() for s in (payload.get('subjects_needing_teacher_rules') or SUBJECTS_NEEDING_TEACHER_RULES)]

    overrides: list[RuleOverride] = []
    audit_history: list[dict[str, Any]] = []
    if overrides_path.exists():
        override_payload = load_json(overrides_path)
        overrides = [RuleOverride.from_dict(row) for row in (override_payload.get('overrides') or [])]
        audit_history = list(override_payload.get('audit_history') or [])

    return CurriculumRuleLibrary(
        profile=profile,
        rules=rules,
        subject_behaviors=behaviors,
        subjects_needing_teacher_rules=subjects,
        overrides=overrides,
        audit_history=audit_history,
    )


def apply_overrides_to_rule(rule: CurriculumRule, overrides: list[RuleOverride]) -> CurriculumRule:
    effective = copy.deepcopy(rule)
    for override in overrides:
        if override.rule_id != rule.rule_id or not override.active or override.reverted_at:
            continue
        if override.field_changed.startswith('grading_policy.'):
            field_name = override.field_changed.split('.', 1)[1]
            effective.grading_policy[field_name] = override.new_value
        elif override.field_changed == 'teacher_decision_required':
            effective.teacher_decision_required = bool(override.new_value)
        elif override.field_changed == 'active':
            effective.active = bool(override.new_value)
    effective.updated_at = p22.now_utc()
    return effective


def effective_rules(library: CurriculumRuleLibrary | None = None) -> list[CurriculumRule]:
    library = library or load_library()
    active_overrides = library.active_overrides()
    return [apply_overrides_to_rule(rule, active_overrides) for rule in library.active_rules()]


def create_override(
    library: CurriculumRuleLibrary,
    *,
    rule_id: str,
    field_changed: str,
    new_value: Any,
    reason: str,
    school_year: str | None = None,
) -> RuleOverride:
    rule = library.rule_by_id(rule_id)
    if rule is None:
        raise ValueError(f'Unknown rule_id: {rule_id}')

    old_value: Any
    if field_changed.startswith('grading_policy.'):
        old_value = rule.grading_policy.get(field_changed.split('.', 1)[1])
    elif field_changed == 'teacher_decision_required':
        old_value = rule.teacher_decision_required
    elif field_changed == 'active':
        old_value = rule.active
    else:
        raise ValueError(f'Unsupported override field: {field_changed}')

    override = RuleOverride(
        override_id=p22.stable_id('rule-override', rule_id, field_changed, p22.now_utc()),
        rule_id=rule_id,
        school_year=school_year or library.profile.school_year,
        field_changed=field_changed,
        old_value=old_value,
        new_value=new_value,
        reason=reason,
        created_at=p22.now_utc(),
    )
    library.overrides.append(override)
    library.audit_history.append({
        'event': 'override_created',
        'override_id': override.override_id,
        'rule_id': override.rule_id,
        'field_changed': override.field_changed,
        'timestamp': override.created_at,
    })
    return override


def revert_override(library: CurriculumRuleLibrary, override_id: str) -> RuleOverride:
    override = next((item for item in library.overrides if item.override_id == override_id), None)
    if override is None:
        raise ValueError(f'Unknown override_id: {override_id}')
    if not override.reversible:
        raise ValueError(f'Override not reversible: {override_id}')
    override.active = False
    override.reverted_at = p22.now_utc()
    library.audit_history.append({
        'event': 'override_reverted',
        'override_id': override.override_id,
        'rule_id': override.rule_id,
        'timestamp': override.reverted_at,
    })
    return override


def parse_shurley_reference(token: str) -> CurriculumReference:
    value = compact(token)
    match = SHURLEY_CHAPTER_LESSON_RE.match(value)
    if not match:
        raise ValueError('Shurley reference requires chapter.lesson format (example: 1.3)')
    return CurriculumReference(
        reference_type='chapter_lesson',
        chapter=match.group(1),
        lesson=match.group(2),
    )


def parse_unit_chapter_reference(row: dict[str, Any]) -> CurriculumReference:
    unit = compact(row.get('unit') or '')
    chapter = compact(row.get('chapter') or row.get('lesson') or '')
    if not unit:
        notes = compact(row.get('notes') or '')
        if notes.lower().startswith('unit:'):
            unit = compact(notes.split(':', 1)[1])
    if not chapter:
        title = compact(row.get('title') or '')
        if title.lower().startswith('chapter'):
            chapter = compact(title.split()[-1])
    return CurriculumReference(reference_type='unit_chapter', unit=unit or None, chapter=chapter or None)


def parse_curriculum_reference(row: dict[str, Any], reference_type: str) -> CurriculumReference:
    ref_type = compact(reference_type)
    if ref_type == 'chapter_lesson':
        return parse_shurley_reference(compact(row.get('lesson') or row.get('chapter_lesson') or ''))
    if ref_type == 'unit_chapter':
        return parse_unit_chapter_reference(row)
    return CurriculumReference(reference_type='lesson', lesson=compact(row.get('lesson') or '') or None)


def validate_curriculum_reference(reference: CurriculumReference) -> bool:
    return reference.is_complete()


def build_in_class_entry(
    subject: str,
    reference: CurriculumReference,
    *,
    weekday: str | None = None,
    entry_date: str | None = None,
    week_code: str | None = None,
) -> InClassEntry:
    return InClassEntry(
        subject=compact(subject).lower(),
        entry_type='in_class',
        unit=reference.unit,
        chapter=reference.chapter,
        lesson=reference.lesson,
        reason=MANUAL_TEACHER_RULE_REASON,
        weekday=weekday,
        entry_date=entry_date,
        week_code=week_code,
    )


def filter_nonempty_sections(sections: dict[str, list[str]]) -> dict[str, list[str]]:
    filtered: dict[str, list[str]] = {}
    for name, items in sections.items():
        nonempty = [compact(item) for item in (items or []) if compact(item)]
        if nonempty:
            filtered[name] = nonempty
    return filtered


def render_labeled_sections(sections: dict[str, list[str]]) -> str:
    lines: list[str] = []
    for name, items in filter_nonempty_sections(sections).items():
        lines.append(f'{name}:')
        for item in items:
            lines.append(item)
    return '\n'.join(lines)


def validate_subject(subject: str, library: CurriculumRuleLibrary | None = None) -> RuleValidation:
    library = library or load_library()
    subject_key = compact(subject).lower()
    display = SUBJECT_DISPLAY.get(subject_key, subject_key.replace('-', ' ').title())
    behavior = library.behavior_for_subject(subject_key)

    if behavior and behavior.is_manual and behavior.classroom_activity_enabled:
        return RuleValidation(
            subject=display,
            state='MANUAL_MODE',
            message='Manual teacher-controlled in-class tracking.',
            rule_count=0,
            generation_mode='MANUAL',
        )

    if subject_key in library.subjects_needing_teacher_rules:
        return RuleValidation(
            subject=display,
            state='NEEDS_TEACHER_RULE',
            message='Teacher rule required.',
            rule_count=0,
        )

    if behavior and behavior.is_auto:
        subject_rules = [rule for rule in library.active_rules() if rule.subject == subject_key]
        if not subject_rules:
            return RuleValidation(
                subject=display,
                state='INVALID',
                message='AUTO mode configured but no active curriculum rules.',
                rule_count=0,
                generation_mode='AUTO',
            )
        return RuleValidation(
            subject=display,
            state='PASS',
            message='Automatic generation available.',
            rule_count=len(subject_rules),
            generation_mode='AUTO',
        )

    subject_rules = [rule for rule in library.active_rules() if rule.subject == subject_key]
    if not subject_rules:
        return RuleValidation(
            subject=display,
            state='INVALID',
            message='No active curriculum rules configured.',
            rule_count=0,
        )

    return RuleValidation(
        subject=display,
        state='PASS',
        message='Active curriculum rules configured.',
        rule_count=len(subject_rules),
    )


def validate_all_subjects(library: CurriculumRuleLibrary | None = None) -> list[RuleValidation]:
    library = library or load_library()
    subjects = list(STATUS_SUBJECT_ORDER) + list(library.subjects_needing_teacher_rules)
    seen: set[str] = set()
    ordered: list[str] = []
    for subject in subjects:
        key = compact(subject).lower()
        if key not in seen:
            seen.add(key)
            ordered.append(key)
    return [validate_subject(subject, library) for subject in ordered]


def _format_status_line(validation: RuleValidation) -> str:
    if validation.state == 'PASS' and validation.generation_mode == 'AUTO':
        return 'AUTO PASS'
    if validation.state == 'MANUAL_MODE':
        return 'MANUAL MODE'
    if validation.state == 'NEEDS_TEACHER_RULE':
        return 'NEEDS RULE'
    return validation.state


def curriculum_rules_status_summary(library: CurriculumRuleLibrary | None = None) -> dict[str, str]:
    library = library or load_library()
    return {
        subject: _format_status_line(validate_subject(subject, library))
        for subject in STATUS_SUBJECT_ORDER
    }


def behavior_preview_for_subject(subject: str, library: CurriculumRuleLibrary | None = None) -> dict[str, str]:
    library = library or load_library()
    subject_key = compact(subject).lower()
    behavior = library.behavior_for_subject(subject_key)
    display = SUBJECT_DISPLAY.get(subject_key, subject_key.title())
    if behavior is None:
        return {
            'subject': display,
            'generation': 'Unknown',
            'homework': 'Unknown',
            'canvas_assignment': 'Unknown',
        }
    if behavior.is_manual:
        generation = 'In Class Only'
    elif behavior.homework_generation_enabled:
        generation = 'Assignment Drafts'
    else:
        generation = 'Classroom Activity'
    return {
        'subject': display,
        'generation': generation,
        'homework': 'Disabled' if not behavior.homework_generation_enabled else 'Enabled',
        'canvas_assignment': 'Disabled' if not behavior.canvas_enabled else 'Enabled',
    }


def print_curriculum_rules_status_report() -> None:
    summary = curriculum_rules_status_summary()
    print('Curriculum Rules')
    print()
    for subject in STATUS_SUBJECT_ORDER:
        print(f'{STATUS_SUBJECT_LABEL[subject]}:')
        print(summary[subject])
        print()


def print_curriculum_behavior_preview_report(subject: str = 'history') -> None:
    preview = behavior_preview_for_subject(subject)
    print('Subject:')
    print(preview['subject'])
    print()
    print('Generation:')
    print(preview['generation'])
    print()
    print('Homework:')
    print(preview['homework'])
    print()
    print('Canvas Assignment:')
    print(preview['canvas_assignment'])


def print_curriculum_profile_status_report() -> None:
    library = load_library()
    profile = library.profile
    active_count = len(library.active_rules())
    override_count = len(library.active_overrides())
    label = profile.label or f'{profile.school_year} Grade {profile.grade_level}'
    print('Active Profile:')
    print()
    print(label)
    print()
    print('Rules:')
    print(f'{active_count} active')
    print()
    print('Overrides:')
    print(override_count)


def rules_have_no_canvas_writes() -> bool:
    source = Path(__file__).read_text().lower()
    marker = 'def rules_have_no_canvas_writes'
    idx = source.find(marker)
    scan_source = source[:idx] if idx >= 0 else source
    forbidden = ('create_assignment', 'requests.post', 'canvas.instructure', 'attempt_write')
    return not any(token in scan_source for token in forbidden)


def command_status_report(_args: argparse.Namespace) -> int:
    print_curriculum_rules_status_report()
    return 0


def command_behavior_preview(args: argparse.Namespace) -> int:
    print_curriculum_behavior_preview_report(compact(args.subject or 'history'))
    return 0


def command_profile_report(_args: argparse.Namespace) -> int:
    print_curriculum_profile_status_report()
    return 0


def command_self_test() -> int:
    library = load_library()
    assert library.profile.profile_id == '2026-2027-grade-4-default'
    assert len(library.active_rules()) == 9
    assert len(library.subject_behaviors) == 6

    math_behavior = library.behavior_for_subject('math')
    assert math_behavior is not None and math_behavior.is_auto
    history_behavior = library.behavior_for_subject('history')
    assert history_behavior is not None and history_behavior.is_manual
    assert history_behavior.homework_generation_enabled is False

    shurley_ref = parse_shurley_reference('1.3')
    assert shurley_ref.chapter == '1' and shurley_ref.lesson == '3'
    try:
        parse_shurley_reference('3')
        raise AssertionError('expected shurley parse failure')
    except ValueError:
        pass

    history_ref = CurriculumReference(reference_type='unit_chapter', unit='The American Revolution', chapter='8')
    assert validate_curriculum_reference(history_ref)
    incomplete = CurriculumReference(reference_type='unit_chapter', unit='Energy and Matter')
    assert not validate_curriculum_reference(incomplete)

    entry = build_in_class_entry('history', history_ref)
    assert 'The American Revolution' in entry.summary_text()
    assert 'Manual Teacher Rule' in entry.summary_text()

    sections = filter_nonempty_sections({'Homework': [], 'Assessment': ['Quiz 1'], 'Materials': ['']})
    assert 'Homework' not in sections
    assert 'Materials' not in sections
    rendered = render_labeled_sections({'Homework': [], 'Assessment': [], 'Notes': []})
    assert rendered == ''
    assert 'None' not in render_labeled_sections({'Homework': ['Worksheet 1']})

    math_rules = [rule for rule in library.active_rules() if rule.subject == 'math']
    assert len(math_rules) == 4
    monday = library.rule_by_id('math-monday-homework')
    assert monday is not None
    assert '12-30 even' in monday.generation_pattern.lower()

    validation = validate_subject('math', library)
    assert validation.state == 'PASS'
    history = validate_subject('history', library)
    assert history.state == 'MANUAL_MODE'
    science = validate_subject('science', library)
    assert science.state == 'MANUAL_MODE'
    shurley = validate_subject('shurley', library)
    assert shurley.state == 'MANUAL_MODE'

    override = create_override(
        library,
        rule_id='math-wednesday-homework',
        field_changed='grading_policy.points',
        new_value=75,
        reason='Test override',
    )
    assert override.old_value == 100
    reverted = revert_override(library, override.override_id)
    assert reverted.reverted_at

    summary = curriculum_rules_status_summary(library)
    assert summary['math'] == 'AUTO PASS'
    assert summary['history'] == 'MANUAL MODE'

    preview = behavior_preview_for_subject('history', library)
    assert preview['generation'] == 'In Class Only'
    assert preview['homework'] == 'Disabled'

    assert rules_have_no_canvas_writes()
    print('PASS curriculum rules self-test')
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Canvas LLM curriculum rule library')
    sub = parser.add_subparsers(dest='cmd', required=True)
    sub.add_parser('status-report').set_defaults(func=command_status_report)
    behavior = sub.add_parser('behavior-preview')
    behavior.add_argument('subject', nargs='?', default='history')
    behavior.set_defaults(func=command_behavior_preview)
    sub.add_parser('profile-report').set_defaults(func=command_profile_report)
    sub.add_parser('self-test').set_defaults(func=lambda _args: command_self_test())
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == '__main__':
    raise SystemExit(main())
