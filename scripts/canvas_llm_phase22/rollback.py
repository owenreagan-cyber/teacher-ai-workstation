#!/usr/bin/env python3
"""Rollback and recovery planning for future Canvas LLM deployment operations."""
from __future__ import annotations

import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.canvas_llm_phase22 import phase22_workstation as p22  # noqa: E402

ROLLBACK_OPERATIONS = (
    'create_announcement',
    'update_announcement',
    'create_assignment',
    'update_page',
)


def compact(value: Any) -> str:
    return p22.compact(value)


@dataclass
class RollbackPlan:
    rollback_id: str
    deployment_id: str
    operation: str
    created_state: str
    restore_action: str
    verification_steps: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def is_complete(self) -> bool:
        return bool(
            compact(self.rollback_id)
            and compact(self.deployment_id)
            and compact(self.operation)
            and compact(self.created_state)
            and compact(self.restore_action)
            and self.verification_steps
        )


def operation_for_artifact_kind(artifact_kind: str) -> str:
    mapping = {
        'announcement': 'create_announcement',
        'newsletter_update': 'create_announcement',
        'assignment': 'create_assignment',
        'newsletter': 'update_page',
        'daily_brief': 'create_announcement',
    }
    return mapping.get(artifact_kind, 'create_announcement')


def generate_rollback_plan(
    deployment_id: str,
    artifact_id: str,
    artifact_kind: str,
    *,
    operation: str | None = None,
) -> RollbackPlan:
    op = compact(operation or operation_for_artifact_kind(artifact_kind))
    rollback_id = p22.stable_id('rollback', deployment_id, artifact_id, op)
    restore_action = {
        'create_announcement': 'Delete created announcement or restore prior announcement draft state.',
        'update_announcement': 'Restore prior announcement body from local artifact snapshot.',
        'create_assignment': 'Delete created assignment or restore prior assignment draft state.',
        'update_page': 'Restore prior page HTML from local artifact snapshot.',
    }.get(op, 'Restore prior local artifact snapshot and mark deployment reverted.')
    verification_steps = [
        'Confirm Canvas target object absent or matches pre-deploy snapshot.',
        'Confirm local artifact registry shows preview-only deployment status.',
        'Confirm teacher decision record remains auditable and unchanged.',
    ]
    return RollbackPlan(
        rollback_id=rollback_id,
        deployment_id=deployment_id,
        operation=op,
        created_state=f'local-preview:{artifact_id}',
        restore_action=restore_action,
        verification_steps=verification_steps,
    )
