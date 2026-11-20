#!/usr/bin/env python3
"""Assignment draft generator for C1I — drafts only, no Canvas assignment publishing."""
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

from scripts.canvas_llm_phase22 import approval_queue as queue  # noqa: E402
from scripts.canvas_llm_phase22 import artifact_registry as registry  # noqa: E402
from scripts.canvas_llm_phase22 import homework_rules as rules  # noqa: E402
from scripts.canvas_llm_phase22 import pacing_parser as pacing  # noqa: E402
from scripts.canvas_llm_phase22 import phase22_workstation as p22  # noqa: E402
from scripts.canvas_llm_phase22 import teacher_decisions as decisions  # noqa: E402

TEACHER_DECISION_CHOICES = (
    'count_toward_final_grade',
    'do_not_count_toward_final_grade',
)


def compact(value: Any) -> str:
    return p22.compact(value)


def jd(value: Any) -> str:
    return registry.jd(value)


@dataclass
class AssignmentDraft:
    draft_id: str
    subject: str
    title: str
    description: str
    category: str
    points: float
    grading_type: str
    counts_toward_final_grade: bool
    teacher_decision_required: bool
    source_rule: str
    week_code: str
    artifact_id: str | None = None
    content_hash: str | None = None
    needs_teacher_rule: bool = False
    queue_status: str = 'READY'
    teacher_decision_choices: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def content_hash_for_draft(draft: AssignmentDraft) -> str:
    canonical = jd({
        'title': draft.title,
        'description': draft.description,
        'category': draft.category,
        'points': draft.points,
        'grading_type': draft.grading_type,
        'source_rule': draft.source_rule,
        'week_code': draft.week_code,
    })
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]


def application_to_draft(application: rules.RuleApplication) -> AssignmentDraft:
    draft_id = p22.stable_id('assignment-draft', application.week_code, application.rule_id, application.title)
    artifact_id = p22.stable_id('artifact', draft_id, application.title)
    draft = AssignmentDraft(
        draft_id=draft_id,
        subject=application.subject,
        title=application.title,
        description=application.description,
        category=application.category,
        points=application.points,
        grading_type=application.grading_type,
        counts_toward_final_grade=application.counts_toward_final_grade,
        teacher_decision_required=application.teacher_decision_required,
        source_rule=application.rule_id,
        week_code=compact(application.week_code or ''),
        artifact_id=artifact_id,
        needs_teacher_rule=application.needs_teacher_rule,
        teacher_decision_choices=list(TEACHER_DECISION_CHOICES) if application.teacher_decision_required else [],
    )
    draft.content_hash = content_hash_for_draft(draft)
    draft.queue_status = derive_queue_status_for_draft(draft)
    return draft


def derive_queue_status_for_draft(draft: AssignmentDraft) -> str:
    if draft.needs_teacher_rule:
        return 'BLOCKED'
    if draft.teacher_decision_required:
        return 'NEEDS_REVIEW'
    return 'READY'


def draft_to_registry_row(draft: AssignmentDraft, *, weekly_plan_id: str | None = None) -> dict[str, Any]:
    """Convert an assignment draft to a drafts-table-compatible row for registry normalization."""
    payload = {
        'artifactKind': 'assignment',
        'sourceRule': draft.source_rule,
        'category': draft.category,
        'points': draft.points,
        'gradingType': draft.grading_type,
        'countsTowardFinalGrade': draft.counts_toward_final_grade,
        'teacherDecisionRequired': draft.teacher_decision_required,
        'teacherDecisionChoices': draft.teacher_decision_choices,
        'needsTeacherRule': draft.needs_teacher_rule,
        'contentHash': draft.content_hash,
        'previewOnly': True,
        'teacherApprovalRequired': True,
        'canvasWritesAllowed': False,
        'approved': False,
        'approvalState': 'Draft',
        'approvalRevision': 0,
        'needsReview': draft.queue_status == 'NEEDS_REVIEW',
        'blockers': ['missing_curriculum_rule'] if draft.needs_teacher_rule else [],
        'warnings': ['teacher_grading_choice_required'] if draft.teacher_decision_required else [],
        'deploymentStatus': 'preview_only',
    }
    return {
        'id': draft.artifact_id,
        'weekly_plan_id': weekly_plan_id,
        'kind': 'assignment',
        'subject': draft.subject,
        'title': draft.title,
        'body_text': draft.description,
        'body_html': f'<p>{html.escape(draft.description)}</p>',
        'status': 'draft',
        'payload': jd(payload),
        'created_at': p22.now_utc(),
        'updated_at': p22.now_utc(),
    }


def draft_to_registry_record(draft: AssignmentDraft, *, weekly_plan_id: str | None = None) -> registry.ArtifactRegistryRecord:
    row = draft_to_registry_row(draft, weekly_plan_id=weekly_plan_id)
    record = registry.normalize_draft_row(row)
    assert record is not None
    return record


def build_queue_items_for_drafts(drafts: list[AssignmentDraft]) -> list[queue.ApprovalQueueItem]:
    items: list[queue.ApprovalQueueItem] = []
    for draft in drafts:
        record = draft_to_registry_record(draft)
        item = queue.build_queue_item(record, approval_snapshots={})
        items.append(item)
    return items


def generate_drafts_from_plan(plan: pacing.WeeklyInstructionalPlan) -> list[AssignmentDraft]:
    applications = rules.apply_rules(plan)
    drafts = [application_to_draft(app) for app in applications if not app.needs_teacher_rule or app.subject in rules.SUBJECTS_NEEDING_TEACHER_RULES]
    return [draft for draft in drafts if gradebook_allowed(draft)]


def gradebook_allowed(draft: AssignmentDraft) -> bool:
    """Canonical 2026-11-17 Math/Reading policy gate.

    Tests/assessments plus pacing-derived Math homework/classwork and Reading
    workbook/comprehension work may become gradebook drafts. Generic
    homework/classwork and unrelated kinds stay out. An explicit structured
    owner approval may admit a specific draft.
    """
    from scripts.canvas_llm_phase3 import assignment_policy as policy
    course_by_subject = {'math': 26404, 'reading': 26442, 'spelling': 26442,
                         'language-arts': 28171, 'history': 28165, 'science': 28166}
    kind = policy.classify_assignment(title=draft.title, source_rule=draft.source_rule,
                                      group=draft.category)
    course = course_by_subject.get((draft.subject or '').strip().lower())
    group = policy.default_group(kind) or draft.category
    approval = getattr(draft, 'owner_approval', None)
    proposed = {'course': course, 'kind': kind, 'title': draft.title}
    return policy.auto_prepare_allowed(kind, course=course, group=group,
                                       approval=approval, proposed=proposed)


def generate_drafts_from_db(db: p22.WorkstationDB, weekly_plan_id: str) -> list[AssignmentDraft]:
    plan = pacing.parse_week_from_db(db, weekly_plan_id)
    return generate_drafts_from_plan(plan)


@dataclass
class DraftPreviewSummary:
    week_code: str
    generated: int
    needs_review: int
    blocked: int
    ready: int
    drafts: list[AssignmentDraft] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload['drafts'] = [draft.to_dict() for draft in self.drafts]
        return payload


def summarize_drafts(drafts: list[AssignmentDraft], week_code: str) -> DraftPreviewSummary:
    return DraftPreviewSummary(
        week_code=week_code,
        generated=len(drafts),
        needs_review=sum(1 for d in drafts if d.queue_status == 'NEEDS_REVIEW'),
        blocked=sum(1 for d in drafts if d.queue_status == 'BLOCKED'),
        ready=sum(1 for d in drafts if d.queue_status == 'READY'),
        drafts=drafts,
    )


def print_draft_preview_report(summary: DraftPreviewSummary) -> None:
    print('Assignment Draft Preview')
    print()
    print(summary.week_code)
    print()
    print('Generated:')
    print(summary.generated)
    print()
    print('Needs Review:')
    print(summary.needs_review)
    print()
    print('Blocked:')
    print(summary.blocked)
    print()
    print('No Canvas writes performed.')


def teacher_decision_points_for_drafts(drafts: list[AssignmentDraft]) -> list[dict[str, Any]]:
    points: list[dict[str, Any]] = []
    for draft in drafts:
        if not draft.teacher_decision_required:
            continue
        points.append({
            'artifact_id': draft.artifact_id,
            'title': draft.title,
            'subject': draft.subject,
            'choices': list(draft.teacher_decision_choices),
            'prompt': 'Count toward final grade or do not count toward final grade',
            'automatic_selection': False,
        })
    return points


def generator_performs_no_canvas_writes() -> bool:
    source = Path(__file__).read_text().lower()
    marker = 'def generator_performs_no_canvas_writes'
    idx = source.find(marker)
    scan_source = source[:idx] if idx >= 0 else source
    forbidden = ('create_assignment', 'requests.post', 'canvas.instructure', 'attempt_write')
    return not any(token in scan_source for token in forbidden)


def command_preview_report(_args: argparse.Namespace) -> int:
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
    ]
    plan = pacing.parse_rows_to_plan(week_meta, rows)
    drafts = generate_drafts_from_plan(plan)
    summary = summarize_drafts(drafts, plan.week_code)
    print_draft_preview_report(summary)
    return 0


def command_self_test() -> int:
    import tempfile

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
    drafts = generate_drafts_from_plan(plan)
    # 2026-11-17 policy: pacing-derived Math/Reading work is admitted.
    assert len(drafts) == 9, [d.title for d in drafts]
    assert all(gradebook_allowed(d) for d in drafts)
    assert any('Lesson 2 Homework' in d.title for d in drafts)
    assert any('Lesson 3 Classwork' in d.title for d in drafts)
    assert any('Workbook and Comprehension' in d.title for d in drafts)
    assert any(' Workbook' in d.title and 'Comprehension' not in d.title for d in drafts)
    assert any('Spelling Test 5' in d.title for d in drafts)
    assert not any('quiz' in d.title.lower() or 'project' in d.title.lower()
                   or 'investigation' in d.title.lower() for d in drafts)

    for draft in drafts:
        assert draft.artifact_id
        assert draft.content_hash
        assert draft.source_rule
        record = draft_to_registry_record(draft)
        assert record.artifact_kind == 'assignment'
        assert record.content_hash == draft.content_hash
        assert record.canvas_writes_allowed is False

    queue_items = build_queue_items_for_drafts(drafts)
    assert len(queue_items) == len(drafts)

    decision_points = teacher_decision_points_for_drafts(drafts)
    assert all(point['automatic_selection'] is False for point in decision_points)

    temp_db = Path(tempfile.mkstemp(suffix='.sqlite3')[1])
    db = p22.WorkstationDB(temp_db)
    db.migrate()
    db.seed_from_fixture()
    wid = registry.seed_demo_week(db)
    db_drafts = generate_drafts_from_db(db, wid)
    assert db_drafts
    assert all(gradebook_allowed(d) for d in db_drafts)
    assert not any('quiz' in d.title.lower() or 'project' in d.title.lower()
                   for d in db_drafts)

    assert generator_performs_no_canvas_writes()
    temp_db.unlink(missing_ok=True)
    print('PASS assignment draft generator self-test')
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Canvas LLM assignment draft generator')
    sub = parser.add_subparsers(dest='cmd', required=True)
    sub.add_parser('preview-report').set_defaults(func=command_preview_report)
    sub.add_parser('self-test').set_defaults(func=lambda _args: command_self_test())
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == '__main__':
    raise SystemExit(main())
