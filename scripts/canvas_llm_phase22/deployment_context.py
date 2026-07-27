#!/usr/bin/env python3
"""Deployment context validation for controlled Canvas writes."""
from __future__ import annotations

import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.canvas_llm_phase22 import canvas_course_resolver as resolver  # noqa: E402
from scripts.canvas_llm_phase22 import phase22_workstation as p22  # noqa: E402


def compact(value: Any) -> str:
    return p22.compact(value)


@dataclass
class DeploymentContext:
    subject: str
    assignment_type: str
    course_id: int
    canonical_prefix: str
    assignment_group: str
    title: str = ''

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DeploymentContextResult:
    allowed: bool
    reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def validate_deployment_context(
    context: DeploymentContext,
    *,
    target_type: str,
) -> DeploymentContextResult:
    route = resolver.resolve_route(context.subject, context.assignment_type)
    if route.status == 'MANUAL' or not route.allowed:
        return DeploymentContextResult(False, f'manual subject blocked: {context.subject}')
    if route.course_id != context.course_id:
        return DeploymentContextResult(False, 'course_id mismatch')
    if context.canonical_prefix and not compact(context.title).upper().startswith(context.canonical_prefix.upper()):
        return DeploymentContextResult(False, 'prefix mismatch')
    if target_type == 'assignment' and not context.assignment_group:
        return DeploymentContextResult(False, 'missing assignment group')
    return DeploymentContextResult(True, 'context valid')
