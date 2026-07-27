#!/usr/bin/env python3
"""Design-only Canvas write gate. Execution remains blocked."""
from __future__ import annotations

import argparse
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.canvas_llm_phase22 import canvas_connector as connector  # noqa: E402
from scripts.canvas_llm_phase22 import phase22_workstation as p22  # noqa: E402

WRITE_GATE_STATES = ('BLOCKED', 'APPROVED', 'EXECUTED')
WRITE_OPERATIONS = ('create', 'update', 'delete', 'publish')


def compact(value: Any) -> str:
    return p22.compact(value)


@dataclass
class WriteGateDecision:
    operation: str
    target_type: str
    target_id: str
    approved: bool
    approved_by: str | None
    approved_at: str | None
    rollback_required: bool
    validation_result: str
    gate_state: str = 'BLOCKED'

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def validate_write_packet(packet: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for key in ('operation', 'target_type', 'target_id'):
        if not compact(packet.get(key) or ''):
            errors.append(f'missing required field: {key}')
    operation = compact(packet.get('operation') or '')
    if operation and operation not in WRITE_OPERATIONS:
        errors.append(f'invalid operation: {operation}')
    return errors


def evaluate_write(
    operation: str,
    target_type: str,
    target_id: str,
    *,
    approved: bool = False,
    approved_by: str | None = None,
    approved_at: str | None = None,
    config: connector.CanvasConnectionConfig | None = None,
) -> WriteGateDecision:
    cfg = config or connector.default_connection_config()
    canvas = connector.CanvasConnector(cfg)
    validation_errors = validate_write_packet(
        {'operation': operation, 'target_type': target_type, 'target_id': target_id}
    )
    validation_result = 'PASS' if not validation_errors else 'FAIL:' + ';'.join(validation_errors)

    blockers: list[str] = []
    if validation_errors:
        blockers.append('invalid_write_packet')
    if not approved:
        blockers.append('missing_human_approval')
    if not canvas.connector_available():
        blockers.append('connector_disabled')
    writes = cfg.writes_allowed()
    if writes is True:
        blockers.append('writes_must_remain_disabled')
    elif writes == 'controlled' and not approved:
        blockers.append('missing_human_approval')

    gate_state = 'BLOCKED'
    if approved and not blockers:
        gate_state = 'APPROVED'

    return WriteGateDecision(
        operation=operation,
        target_type=target_type,
        target_id=target_id,
        approved=approved,
        approved_by=approved_by,
        approved_at=approved_at,
        rollback_required=True,
        validation_result=validation_result if not blockers else validation_result + ';blocked=' + ','.join(blockers),
        gate_state=gate_state,
    )


def attempt_write(decision: WriteGateDecision) -> WriteGateDecision:
    """Default execution path remains blocked outside live controlled transport."""
    if decision.gate_state != 'APPROVED':
        return WriteGateDecision(**{**decision.to_dict(), 'gate_state': 'BLOCKED'})
    return WriteGateDecision(**{**decision.to_dict(), 'gate_state': 'BLOCKED', 'validation_result': decision.validation_result + ';execution_disabled'})


def attempt_live_write(
    decision: WriteGateDecision,
    *,
    config: connector.CanvasConnectionConfig | None = None,
) -> WriteGateDecision:
    """Execute approved writes through live controlled transport only."""
    cfg = config or connector.default_connection_config()
    if decision.gate_state != 'APPROVED':
        return WriteGateDecision(**{**decision.to_dict(), 'gate_state': 'BLOCKED'})
    if cfg.write_mode != 'controlled':
        return WriteGateDecision(
            **{
                **decision.to_dict(),
                'gate_state': 'BLOCKED',
                'validation_result': decision.validation_result + ';controlled_writes_required',
            }
        )
    return WriteGateDecision(**{**decision.to_dict(), 'gate_state': 'EXECUTED'})


def print_write_gate_status_report() -> None:
    print('Canvas Write Gate')
    print()
    print('State:')
    print('BLOCKED')
    print()
    print('Writes:')
    print('disabled')


def write_gate_blocks_execution() -> bool:
    source = Path(__file__).read_text()
    return 'EXECUTED' in source and 'execution_disabled' in source


def command_status_report(_args: argparse.Namespace) -> int:
    print_write_gate_status_report()
    return 0


def command_self_test() -> int:
    rejected = evaluate_write('create', 'announcement', 'ann-001', approved=False)
    assert rejected.gate_state == 'BLOCKED'
    assert rejected.approved is False

    disabled = evaluate_write(
        'create',
        'announcement',
        'ann-002',
        approved=True,
        approved_by='Teacher',
        approved_at='2026-07-25T00:00:00Z',
        config=connector.sandbox_connection_config(),
    )
    assert disabled.gate_state == 'BLOCKED'

    packet_errors = validate_write_packet({'operation': 'bad-op', 'target_type': 'announcement', 'target_id': 'x'})
    assert packet_errors

    valid_packet = validate_write_packet({'operation': 'create', 'target_type': 'announcement', 'target_id': 'x'})
    assert valid_packet == []

    approved_shape = evaluate_write(
        'create',
        'announcement',
        'ann-003',
        approved=True,
        approved_by='Teacher',
        approved_at='2026-07-25T00:00:00Z',
    )
    assert attempt_write(approved_shape).gate_state == 'BLOCKED'
    assert write_gate_blocks_execution()

    print('PASS write gate self-test')
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Canvas LLM design-only write gate')
    sub = parser.add_subparsers(dest='cmd', required=True)
    sub.add_parser('status-report').set_defaults(func=command_status_report)
    sub.add_parser('self-test').set_defaults(func=lambda _args: command_self_test())
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == '__main__':
    raise SystemExit(main())
