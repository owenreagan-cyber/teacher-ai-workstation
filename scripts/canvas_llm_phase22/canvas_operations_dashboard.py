#!/usr/bin/env python3
"""Teacher-facing Canvas operations dashboard for C1E."""
from __future__ import annotations

import argparse
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.canvas_llm_phase22 import approval_queue as queue  # noqa: E402
from scripts.canvas_llm_phase22 import artifact_registry as registry  # noqa: E402
from scripts.canvas_llm_phase22 import canvas_drift as drift  # noqa: E402
from scripts.canvas_llm_phase22 import deployment_audit as audit  # noqa: E402
from scripts.canvas_llm_phase22 import deployment_readiness as readiness  # noqa: E402
from scripts.canvas_llm_phase22 import grading_optimizer as optimizer  # noqa: E402
from scripts.canvas_llm_phase22 import phase22_workstation as p22  # noqa: E402
from scripts.canvas_llm_phase22 import teacher_decisions as decisions  # noqa: E402

DASHBOARD_STATES = ('READY TO PUBLISH', 'NEEDS REVIEW', 'BLOCKED', 'DRIFT DETECTED')
BLOCKED_KINDS = ('assignment',)


def compact(value: Any) -> str:
    return p22.compact(value)


def _display_label(record: registry.ArtifactRegistryRecord) -> str:
    kind = record.artifact_kind
    title = compact(record.title or record.artifact_id)
    if kind == 'page':
        if record.subject:
            return f'{record.subject.replace("-", " ").title()} Agenda'
        return title or 'Weekly Agenda'
    if kind == 'announcement':
        return title or 'Assessment Announcement'
    if kind == 'newsletter':
        return title or 'Newsletter'
    if kind == 'newsletter_update':
        return title or 'Newsletter Update Announcement'
    if kind == 'assignment':
        return title or 'Assignment Preview'
    if kind == 'daily_brief':
        return title or 'Daily Teacher Brief'
    return title or record.artifact_id


@dataclass
class DashboardItem:
    artifact_id: str
    label: str
    artifact_kind: str
    state: str
    reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CanvasOperationsDashboard:
    ready_items: list[DashboardItem] = field(default_factory=list)
    needs_review_items: list[DashboardItem] = field(default_factory=list)
    blocked_items: list[DashboardItem] = field(default_factory=list)
    drift_items: list[DashboardItem] = field(default_factory=list)
    recent_activity: list[str] = field(default_factory=list)
    health_summary: dict[str, int] = field(default_factory=dict)
    grading_optimization_ready: list[str] = field(default_factory=list)
    grading_optimization_needs_review: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            'ready_items': [item.to_dict() for item in self.ready_items],
            'needs_review_items': [item.to_dict() for item in self.needs_review_items],
            'blocked_items': [item.to_dict() for item in self.blocked_items],
            'drift_items': [item.to_dict() for item in self.drift_items],
            'recent_activity': list(self.recent_activity),
            'health_summary': dict(self.health_summary),
            'grading_optimization_ready': list(self.grading_optimization_ready),
            'grading_optimization_needs_review': list(self.grading_optimization_needs_review),
        }


def build_dashboard(
    db: p22.WorkstationDB,
    weekly_plan_id: str | None = None,
    *,
    drift_reports: list[drift.CanvasDriftReport] | None = None,
    audit_log: audit.DeploymentAuditLog | None = None,
) -> CanvasOperationsDashboard:
    """Build teacher-facing operations dashboard from registry and readiness chain."""
    records = registry.load_registry_from_db(db, weekly_plan_id)
    decisions.sync_invalidations(db, records)
    snapshots = decisions.build_approval_snapshots(db, records)
    queue_items = queue.build_queue_from_registry(records, snapshots)
    queue_by_id = {item.artifact_id: item for item in queue_items}
    readiness_records = readiness.build_readiness_records(db, records, audit_log=audit_log)
    readiness_by_id = {item.artifact_id: item for item in readiness_records}

    dashboard = CanvasOperationsDashboard()
    drift_by_artifact = {report.artifact_id: report for report in (drift_reports or [])}

    pass_count = warn_count = block_count = 0
    for record in records:
        label = _display_label(record)
        health = registry.evaluate_artifact_health(record)
        if health == 'PASS':
            pass_count += 1
        elif health == 'WARN':
            warn_count += 1
        else:
            block_count += 1

        if record.artifact_id in drift_by_artifact:
            drift_report = drift_by_artifact[record.artifact_id]
            dashboard.drift_items.append(
                DashboardItem(
                    artifact_id=record.artifact_id,
                    label=label,
                    artifact_kind=record.artifact_kind,
                    state='DRIFT DETECTED',
                    reason=drift_report.recommendation,
                )
            )
            continue

        if record.artifact_kind in BLOCKED_KINDS:
            dashboard.blocked_items.append(
                DashboardItem(
                    artifact_id=record.artifact_id,
                    label=label,
                    artifact_kind=record.artifact_kind,
                    state='BLOCKED',
                    reason='Assignment publishing disabled',
                )
            )
            continue

        queue_item = queue_by_id[record.artifact_id]
        readiness_item = readiness_by_id[record.artifact_id]

        if queue_item.queue_status == 'NEEDS_REVIEW' or readiness_item.readiness_status == 'NEEDS_REVIEW':
            reason = 'Warning present' if record.warnings else 'Missing teacher coverage'
            dashboard.needs_review_items.append(
                DashboardItem(
                    artifact_id=record.artifact_id,
                    label=label,
                    artifact_kind=record.artifact_kind,
                    state='NEEDS REVIEW',
                    reason=reason,
                )
            )
            continue

        if (
            queue_item.queue_status in {'BLOCKED', 'STALE_APPROVAL'}
            or readiness_item.readiness_status == 'BLOCKED'
            or health == 'BLOCK'
        ):
            reason = 'Missing approval'
            if queue_item.queue_status == 'STALE_APPROVAL':
                reason = 'Stale approval'
            elif record.blockers:
                reason = record.blockers[0]
            dashboard.blocked_items.append(
                DashboardItem(
                    artifact_id=record.artifact_id,
                    label=label,
                    artifact_kind=record.artifact_kind,
                    state='BLOCKED',
                    reason=reason,
                )
            )
            continue

        if readiness_item.readiness_status == 'READY' and queue_item.queue_status == 'READY':
            dashboard.ready_items.append(
                DashboardItem(
                    artifact_id=record.artifact_id,
                    label=label,
                    artifact_kind=record.artifact_kind,
                    state='READY TO PUBLISH',
                )
            )

    log = audit_log or audit.GLOBAL_AUDIT_LOG
    dashboard.recent_activity = [
        f"{event.event_type}:{event.artifact_id}:{event.result}"
        for event in log.events[-5:]
    ]
    grading_summary = optimizer.grading_optimization_dashboard_summary()
    dashboard.grading_optimization_ready = grading_summary['ready']
    dashboard.grading_optimization_needs_review = grading_summary['needs_review']
    dashboard.health_summary = {
        'PASS': pass_count,
        'WARN': warn_count,
        'BLOCK': block_count,
        'ready': len(dashboard.ready_items),
        'needs_review': len(dashboard.needs_review_items),
        'blocked': len(dashboard.blocked_items),
        'drift': len(dashboard.drift_items),
    }
    return dashboard


def print_dashboard_report(dashboard: CanvasOperationsDashboard) -> None:
    print('Canvas Operations Dashboard')
    print()
    print('READY')
    print(f'{len(dashboard.ready_items)} items')
    for item in dashboard.ready_items:
        print(f'✓ {item.label}')
    print()
    print('NEEDS REVIEW')
    print(f'{len(dashboard.needs_review_items)} items')
    for item in dashboard.needs_review_items:
        detail = f' ({item.reason})' if item.reason else ''
        print(f'• {item.label}{detail}')
    print()
    print('BLOCKED')
    print(f'{len(dashboard.blocked_items)} items')
    for item in dashboard.blocked_items:
        detail = f' ({item.reason})' if item.reason else ''
        print(f'• {item.label}{detail}')
    print()
    print('DRIFT')
    print(f'{len(dashboard.drift_items)} items')
    for item in dashboard.drift_items:
        detail = f' ({item.reason})' if item.reason else ''
        print(f'• {item.label}{detail}')
    print()
    print('GRADING OPTIMIZATION')
    print()
    print('READY:')
    for label in dashboard.grading_optimization_ready:
        print(label)
    if not dashboard.grading_optimization_ready:
        print('None')
    print()
    print('NEEDS TEACHER REVIEW:')
    for label in dashboard.grading_optimization_needs_review:
        print(label)
    if not dashboard.grading_optimization_needs_review:
        print('None')
    print()
    print('No publishing performed.')


def dashboard_performs_no_publishing() -> bool:
    source = Path(__file__).read_text().lower()
    marker = 'def dashboard_performs_no_publishing'
    idx = source.find(marker)
    scan_source = source[:idx] if idx >= 0 else source
    forbidden = ('create_announcement', 'create_page', 'attempt_write', 'requests.post')
    return not any(token in scan_source for token in forbidden)


def command_dashboard_report(_args: argparse.Namespace) -> int:
    db = p22.WorkstationDB()
    if not db.path.exists():
        db.migrate()
        db.seed_from_fixture()
    wid = registry.seed_demo_week(db)
    records = registry.load_registry_from_db(db, wid)
    announcement = next((r for r in records if r.artifact_kind == 'announcement'), None)
    if announcement:
        decisions.record_decision(db, announcement, 'approve')
    dashboard = build_dashboard(db, wid)
    print_dashboard_report(dashboard)
    return 0


def command_self_test() -> int:
    import tempfile

    temp_db = Path(tempfile.mkstemp(suffix='.sqlite3')[1])
    db = p22.WorkstationDB(temp_db)
    db.migrate()
    db.seed_from_fixture()
    wid = registry.seed_demo_week(db)
    records = registry.load_registry_from_db(db, wid)
    announcement = next(r for r in records if r.artifact_kind == 'announcement')
    decisions.record_decision(db, announcement, 'approve', teacher_display='Teacher')

    dashboard = build_dashboard(db, wid)
    assert dashboard.health_summary['ready'] >= 1 or dashboard.ready_items
    assert any(item.artifact_kind == 'assignment' for item in dashboard.blocked_items)
    assert dashboard.grading_optimization_ready
    assert dashboard_performs_no_publishing()

    temp_db.unlink(missing_ok=True)
    print('PASS canvas operations dashboard self-test')
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Canvas LLM operations dashboard')
    sub = parser.add_subparsers(dest='cmd', required=True)
    sub.add_parser('dashboard-report').set_defaults(func=command_dashboard_report)
    sub.add_parser('self-test').set_defaults(func=lambda _args: command_self_test())
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == '__main__':
    raise SystemExit(main())
