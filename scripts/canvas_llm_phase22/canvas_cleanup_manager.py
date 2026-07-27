#!/usr/bin/env python3
"""Canvas cleanup manager — recommendations and teacher-approved cleanup only."""
from __future__ import annotations

import argparse
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.canvas_llm_phase22 import canvas_duplicate_detector as detector  # noqa: E402
from scripts.canvas_llm_phase22 import phase22_workstation as p22  # noqa: E402

CLEANUP_STATES = ('PLANNED', 'APPROVED', 'EXECUTED', 'BLOCKED', 'ROLLED_BACK')


def compact(value: Any) -> str:
    return p22.compact(value)


@dataclass
class CleanupCandidate:
    object_type: str
    object_id: str
    title: str
    safe_action: str
    requires_teacher_approval: bool
    detail: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CleanupPlan:
    plan_id: str
    safe_candidates: list[CleanupCandidate] = field(default_factory=list)
    protected_objects: list[CleanupCandidate] = field(default_factory=list)
    needs_approval: list[CleanupCandidate] = field(default_factory=list)
    blocked_objects: list[CleanupCandidate] = field(default_factory=list)
    rollback_steps: list[str] = field(default_factory=list)
    state: str = 'PLANNED'

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CleanupApproval:
    plan_id: str
    approved_by: str
    reason: str
    timestamp: str
    approved_object_ids: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CleanupExecutionResult:
    plan_id: str
    executed: bool
    deleted_object_ids: list[str]
    skipped_object_ids: list[str]
    rollback_plan_id: str | None = None
    message: str = ''

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def scan_duplicates(objects: list[detector.CanvasObjectRecord] | None = None) -> detector.DuplicateScanSummary:
    return detector.scan_duplicates(objects)


def _candidate_from_report(report: detector.DuplicateReport, object_id: str, title: str) -> CleanupCandidate:
    return CleanupCandidate(
        object_type=report.object_type,
        object_id=object_id,
        title=title,
        safe_action=report.safe_action,
        requires_teacher_approval=report.requires_teacher_approval,
        detail=report.detail,
    )


def build_cleanup_plan(
    objects: list[detector.CanvasObjectRecord] | None = None,
    *,
    plan_id: str | None = None,
) -> CleanupPlan:
    inventory = list(objects or detector.build_fixture_objects())
    inventory_map = {item.object_id: item for item in inventory}
    summary = scan_duplicates(inventory)
    plan_key = plan_id or p22.stable_id('cleanup-plan', len(summary.reports))
    safe: list[CleanupCandidate] = []
    protected: list[CleanupCandidate] = []
    needs: list[CleanupCandidate] = []
    blocked: list[CleanupCandidate] = []

    for report in summary.reports:
        keep_id = report.object_ids[0]
        for object_id, title in zip(report.object_ids, report.titles):
            record = inventory_map.get(object_id)
            candidate = _candidate_from_report(report, object_id, title)
            if record and record.front_page:
                protected.append(candidate)
                continue
            if object_id == keep_id:
                continue
            if report.safe_action == 'SAFE_DELETE_CANDIDATE':
                safe.append(candidate)
            elif report.safe_action == 'PROTECTED':
                needs.append(candidate)
            elif report.safe_action == 'NEEDS_APPROVAL':
                needs.append(candidate)
            elif report.safe_action == 'BLOCKED':
                blocked.append(_candidate_from_report(report, keep_id, report.titles[0]))

    rollback_steps = [
        'Record deleted object metadata in local cleanup audit log.',
        'Restore from Canvas recycle bin or redeploy from local artifact snapshot if needed.',
        'Verify front page, grading records, and announcement state after any approved cleanup.',
    ]
    return CleanupPlan(
        plan_id=plan_key,
        safe_candidates=safe,
        protected_objects=protected,
        needs_approval=needs,
        blocked_objects=blocked,
        rollback_steps=rollback_steps,
        state='PLANNED',
    )


def approve_cleanup(
    plan: CleanupPlan,
    *,
    approved_by: str,
    reason: str,
    object_ids: list[str] | None = None,
) -> CleanupApproval:
    allowed_ids = {item.object_id for item in plan.safe_candidates}
    requested = object_ids or [item.object_id for item in plan.safe_candidates]
    approved_ids = [item for item in requested if item in allowed_ids]
    if not approved_ids:
        raise ValueError('no safe cleanup candidates approved')
    approval = CleanupApproval(
        plan_id=plan.plan_id,
        approved_by=compact(approved_by),
        reason=compact(reason),
        timestamp=p22.now_utc(),
        approved_object_ids=approved_ids,
    )
    plan.state = 'APPROVED'
    return approval


def execute_cleanup(
    plan: CleanupPlan,
    approval: CleanupApproval | None = None,
    *,
    explicit_approval: bool = False,
) -> CleanupExecutionResult:
    """Simulate approved cleanup only — never deletes Canvas objects automatically."""
    if not explicit_approval or approval is None:
        return CleanupExecutionResult(
            plan_id=plan.plan_id,
            executed=False,
            deleted_object_ids=[],
            skipped_object_ids=[item.object_id for item in plan.safe_candidates],
            message='Cleanup blocked: explicit teacher approval required.',
        )
    if approval.plan_id != plan.plan_id:
        raise ValueError('approval plan_id mismatch')

    deleted: list[str] = []
    skipped: list[str] = []
    approved_set = set(approval.approved_object_ids)
    for candidate in plan.safe_candidates:
        if candidate.object_id in approved_set and candidate.safe_action == 'SAFE_DELETE_CANDIDATE':
            deleted.append(candidate.object_id)
        else:
            skipped.append(candidate.object_id)

    blocked_ids = [item.object_id for item in plan.blocked_objects + plan.protected_objects]
    skipped.extend(blocked_ids)

    plan.state = 'EXECUTED' if deleted else 'BLOCKED'
    rollback_id = p22.stable_id('cleanup-rollback', plan.plan_id) if deleted else None
    return CleanupExecutionResult(
        plan_id=plan.plan_id,
        executed=bool(deleted),
        deleted_object_ids=deleted,
        skipped_object_ids=sorted(set(skipped)),
        rollback_plan_id=rollback_id,
        message='Approved cleanup simulated locally; no Canvas delete transport invoked.',
    )


def print_cleanup_preview() -> None:
    plan = build_cleanup_plan()
    print('Cleanup Preview')
    print()
    print('Safe Candidates:')
    print(len(plan.safe_candidates))
    print()
    print('Protected Objects:')
    print(len(plan.protected_objects))
    print()
    print('Needs Approval:')
    print(len(plan.needs_approval) + len(plan.blocked_objects))


def cleanup_manager_has_no_automatic_deletion() -> bool:
    source = Path(__file__).read_text().lower()
    marker = 'def cleanup_manager_has_no_automatic_deletion'
    idx = source.find(marker)
    scan_source = source[:idx] if idx >= 0 else source
    forbidden = (
        'requests.delete',
        'requests.post',
        'requests.put',
        'canvas.instructure',
        'auto_delete',
        'background_cleanup',
        'gradebook',
    )
    return not any(token in scan_source for token in forbidden)


def command_cleanup_preview(_args: argparse.Namespace) -> int:
    print_cleanup_preview()
    return 0


def command_self_test() -> int:
    summary = scan_duplicates()
    assert summary.reports

    plan = build_cleanup_plan()
    assert plan.safe_candidates
    assert plan.protected_objects
    assert plan.blocked_objects or plan.needs_approval
    assert plan.rollback_steps

    blocked = execute_cleanup(plan)
    assert blocked.executed is False
    assert not blocked.deleted_object_ids

    approval = approve_cleanup(
        plan,
        approved_by='teacher',
        reason='Remove duplicate draft copies after review',
        object_ids=[plan.safe_candidates[0].object_id],
    )
    assert approval.timestamp
    assert approval.approved_object_ids

    executed = execute_cleanup(plan, approval, explicit_approval=True)
    assert executed.executed is True
    assert executed.deleted_object_ids
    assert executed.rollback_plan_id
    assert 'no Canvas delete transport' in executed.message

    assert cleanup_manager_has_no_automatic_deletion()
    print('PASS canvas cleanup manager self-test')
    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Canvas cleanup manager')
    sub = parser.add_subparsers(dest='cmd', required=True)
    sub.add_parser('cleanup-preview').set_defaults(func=command_cleanup_preview)
    sub.add_parser('self-test').set_defaults(func=lambda _args: command_self_test())
    args = parser.parse_args()
    raise SystemExit(args.func(args))
