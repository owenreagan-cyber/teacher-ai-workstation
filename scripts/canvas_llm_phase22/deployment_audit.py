#!/usr/bin/env python3
"""Local deployment audit trail for Canvas LLM operational readiness."""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.canvas_llm_phase22 import canvas_connector as connector  # noqa: E402
from scripts.canvas_llm_phase22 import phase22_workstation as p22  # noqa: E402

AUDIT_EVENT_TYPES = (
    'validation',
    'approval',
    'readiness_check',
    'deployment_attempt',
    'rollback',
)
REDACT_PATTERNS = connector.REDACT_PATTERNS


def compact(value: Any) -> str:
    return p22.compact(value)


def redact_value(value: str) -> str:
    redacted = value
    for pattern in REDACT_PATTERNS:
        redacted = pattern.sub('[REDACTED]', redacted)
    return redacted


@dataclass
class DeploymentAuditEvent:
    event_id: str
    artifact_id: str
    event_type: str
    actor: str
    timestamp: str
    result: str

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload['result'] = redact_value(payload['result'])
        return payload


@dataclass
class DeploymentAuditLog:
    events: list[DeploymentAuditEvent] = field(default_factory=list)

    def record(
        self,
        artifact_id: str,
        event_type: str,
        actor: str,
        result: str,
        *,
        timestamp: str | None = None,
    ) -> DeploymentAuditEvent:
        if event_type not in AUDIT_EVENT_TYPES:
            raise ValueError(f'unsupported event_type: {event_type}')
        if event_type == 'deployment_attempt':
            raise ValueError('deployment_attempt events are blocked in readiness build')
        now = timestamp or p22.now_utc()
        event = DeploymentAuditEvent(
            event_id=p22.stable_id('audit', artifact_id, event_type, actor, now),
            artifact_id=artifact_id,
            event_type=event_type,
            actor=actor,
            timestamp=now,
            result=redact_value(result),
        )
        self.events.append(event)
        return event

    def count(self) -> int:
        return len(self.events)

    def summary(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for event in self.events:
            counts[event.event_type] = counts.get(event.event_type, 0) + 1
        return counts


GLOBAL_AUDIT_LOG = DeploymentAuditLog()


def print_audit_status_report(audit_log: DeploymentAuditLog | None = None) -> None:
    log = audit_log or GLOBAL_AUDIT_LOG
    print('Audit')
    print()
    print('Events:')
    print(log.count())


def audit_has_no_deployment_events(audit_log: DeploymentAuditLog) -> bool:
    return all(event.event_type != 'deployment_attempt' for event in audit_log.events)


def audit_output_is_redacted(audit_log: DeploymentAuditLog) -> bool:
    forbidden = re.compile(r'Bearer\s+\S+|secret-token|access_token', re.I)
    for event in audit_log.events:
        if forbidden.search(event.result):
            return False
    return True


def command_status_report(_args: argparse.Namespace) -> int:
    print_audit_status_report()
    return 0


def command_self_test() -> int:
    log = DeploymentAuditLog()
    log.record('artifact-001', 'validation', 'system', 'PASS')
    log.record('artifact-001', 'approval', 'Teacher', 'approved')
    log.record('artifact-001', 'readiness_check', 'system', 'BLOCKED:connector_disabled')
    log.record('artifact-001', 'rollback', 'system', 'rollback plan generated')

    assert log.count() == 4
    assert audit_has_no_deployment_events(log)
    assert audit_output_is_redacted(log)

    try:
        log.record('artifact-001', 'deployment_attempt', 'system', 'blocked')
        raise AssertionError('deployment_attempt should be blocked')
    except ValueError:
        pass

    redacted = redact_value('Authorization: Bearer abc123 token=secret')
    assert 'abc123' not in redacted
    assert 'secret' not in redacted

    print('PASS deployment audit self-test')
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Canvas LLM deployment audit log')
    sub = parser.add_subparsers(dest='cmd', required=True)
    sub.add_parser('status-report').set_defaults(func=command_status_report)
    sub.add_parser('self-test').set_defaults(func=lambda _args: command_self_test())
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == '__main__':
    raise SystemExit(main())
