#!/usr/bin/env python3
"""Canvas repair center for C1H — recommendations only, no repairs executed."""
from __future__ import annotations

import argparse
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.canvas_llm_phase22 import canvas_drift as drift  # noqa: E402
from scripts.canvas_llm_phase22 import phase22_workstation as p22  # noqa: E402

GLOBAL_DRIFT_ITEMS: list[drift.CanvasDriftReport] = []


def compact(value: Any) -> str:
    return p22.compact(value)


@dataclass
class RepairCenterSummary:
    issues: int
    needs_approval: int
    recommendations: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_repair_center(reports: list[drift.CanvasDriftReport]) -> RepairCenterSummary:
    recommendations = [report.recommendation for report in reports]
    return RepairCenterSummary(
        issues=len(reports),
        needs_approval=sum(1 for report in reports if report.requires_teacher_approval),
        recommendations=recommendations,
    )


def print_repair_center_report(reports: list[drift.CanvasDriftReport] | None = None) -> None:
    items = reports if reports is not None else GLOBAL_DRIFT_ITEMS
    summary = build_repair_center(items)
    print('Canvas Repair Center')
    print()
    print('Issues:')
    print(summary.issues)
    print()
    print('Needs Approval:')
    print(summary.needs_approval)
    print()
    print('Recommendations:')
    print()
    if summary.recommendations:
        for recommendation in summary.recommendations:
            print(recommendation)
            print()
    else:
        print('None')
        print()
    print('No repairs executed.')


def repair_center_executes_no_repairs() -> bool:
    source = Path(__file__).read_text().lower()
    marker = 'def repair_center_executes_no_repairs'
    idx = source.find(marker)
    scan_source = source[:idx] if idx >= 0 else source
    forbidden = ('auto_repair', 'create_page', 'create_announcement', 'attempt_write')
    return not any(token in scan_source for token in forbidden)


def command_repair_center_report(_args: argparse.Namespace) -> int:
    print_repair_center_report()
    return 0


def command_self_test() -> int:
    reports = [
        drift.CanvasDriftReport(
            artifact_id='artifact-001',
            expected_hash='abc123',
            actual_hash='def456',
            difference_type='STALE_VERSION',
            recommendation='Update Newsletter Page',
            requires_teacher_approval=True,
        ),
        drift.CanvasDriftReport(
            artifact_id='artifact-002',
            expected_hash='111',
            actual_hash=None,
            difference_type='OBJECT_MISSING',
            recommendation='Restore Agenda Version',
            requires_teacher_approval=True,
        ),
    ]
    summary = build_repair_center(reports)
    assert summary.issues == 2
    assert summary.needs_approval == 2
    assert repair_center_executes_no_repairs()
    print('PASS canvas repair center self-test')
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Canvas LLM repair center')
    sub = parser.add_subparsers(dest='cmd', required=True)
    sub.add_parser('repair-center-report').set_defaults(func=command_repair_center_report)
    sub.add_parser('self-test').set_defaults(func=lambda _args: command_self_test())
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == '__main__':
    raise SystemExit(main())
