"""Pure adapter from approved Phase 18D intents to future Phase 22 writer requests.

``build_writer_requests(...)`` transforms mutation-eligible, fully-approved
deployment intents into data-only ``WriterRequest`` objects. It generates
*zero* requests for any intent that is not exactly approved, not policy-fresh,
not config-fresh, not ownership-safe, not provenance-complete, not publish-
resolved, or not live-state-fresh.

This is data only. No writer import. No execution function. No writes.
"""

from __future__ import annotations

from typing import Any

from scripts.canvas_llm_phase18d.contracts import (
    ApprovalRecord,
    CanvasSnapshot,
    DeploymentIntent,
    DryRunPacket,
)
from scripts.canvas_llm_phase27.canonicalize import canonical_hash

from .contracts import ExecutionPreconditionReport, ReadinessState, WriterRequest
from .policy import OwnerCanvasPolicy, due_timestamp, policy_hash
from .preconditions import evaluate_preconditions, logical_target_identity

MUTATION_OPERATIONS = ("CREATE", "UPDATE")


def stable_request_id(packet: DryRunPacket, intent: DeploymentIntent) -> str:
    """Deterministic request ID: same inputs -> same ID."""
    return "wr-" + canonical_hash(
        [packet.packet_hash, intent.id, intent.operation, intent.object_type, intent.course, intent.target_locator]
    )[:20]


def _build_request(
    packet: DryRunPacket,
    intent: DeploymentIntent,
    policy: OwnerCanvasPolicy,
    report: ExecutionPreconditionReport,
) -> WriterRequest:
    desired = intent.desired_state or {}
    submission_type = policy.homework_submission_type if intent.object_type == "assignment" else ""
    due_at = ""
    if intent.object_type == "assignment":
        assigned_date = str(desired.get("assigned_date") or desired.get("due_at") or "")
        timezone = str(desired.get("timezone") or policy.timezone)
        if assigned_date:
            due_at = due_timestamp(assigned_date, timezone, policy.homework_due_time_local)
    return WriterRequest(
        request_id=stable_request_id(packet, intent),
        packet_hash=packet.packet_hash,
        intent_id=intent.id,
        policy_hash=policy_hash(policy),
        operation=intent.operation,
        target_type=intent.object_type,
        course_id=str(desired.get("course_id", "")),
        target_canvas_id=report.target_canvas_id,
        title=str(desired.get("title", "")),
        body=str(desired.get("body", "")),
        due_at=due_at,
        submission_type=submission_type,
        assignment_group_id=str(desired.get("assignment_group_id", "") or ""),
        published=policy.publish_decision if policy.publication_resolved() else "",
        expected_current_hash=report.expected_current_hash,
        expected_last_updated=report.expected_last_updated,
        provenance=list(intent.provenance or []),
    )


def detect_request_collisions(requests: list[WriterRequest]) -> list[str]:
    """Detect multiple requests targeting the same logical object incompatibly."""
    by_target: dict[str, list[WriterRequest]] = {}
    for r in requests:
        key = f"{r.target_type}|{r.course_id}|{r.target_canvas_id}|{r.title}"
        by_target.setdefault(key, []).append(r)
    collisions: list[str] = []
    for key, group in by_target.items():
        if len(group) > 1:
            collisions.append(f"duplicate writer request on {key}: {[r.request_id for r in group]}")
    return collisions


def build_writer_requests(
    packet: DryRunPacket,
    approval: ApprovalRecord | None,
    policy: OwnerCanvasPolicy,
    *,
    canvas_config: dict[str, Any],
    snapshot: CanvasSnapshot | None = None,
    target_environment: str | None = None,
) -> list[WriterRequest]:
    """Build data-only writer requests for exactly-eligible intents.

    Returns an empty list when the packet, approval, policy, config, or live
    state is not fully valid. Never raises; never executes.
    """
    requests: list[WriterRequest] = []
    for intent in packet.intents:
        if intent.operation not in MUTATION_OPERATIONS:
            continue
        report = evaluate_preconditions(
            packet,
            intent,
            approval,
            policy,
            canvas_config=canvas_config,
            snapshot=snapshot,
            target_environment=target_environment,
        )
        if report.readiness != ReadinessState.READY_FOR_EXECUTION_REVIEW.value:
            continue
        requests.append(_build_request(packet, intent, policy, report))

    collisions = detect_request_collisions(requests)
    if collisions:
        # Fail closed: drop every colliding request's target group.
        bad_keys = {
            f"{r.target_type}|{r.course_id}|{r.target_canvas_id}|{r.title}"
            for r in requests
            if any(r.request_id in c for c in collisions)
        }
        requests = [
            r for r in requests
            if f"{r.target_type}|{r.course_id}|{r.target_canvas_id}|{r.title}" not in bad_keys
        ]

    requests.sort(key=lambda r: (r.course_id, r.target_type, r.target_canvas_id, r.title, r.request_id))
    return requests


def build_writer_requests_with_reports(
    packet: DryRunPacket,
    approval: ApprovalRecord | None,
    policy: OwnerCanvasPolicy,
    *,
    canvas_config: dict[str, Any],
    snapshot: CanvasSnapshot | None = None,
    target_environment: str | None = None,
) -> tuple[list[WriterRequest], list[ExecutionPreconditionReport]]:
    """Return requests plus per-intent precondition reports (for inspection)."""
    requests = build_writer_requests(
        packet,
        approval,
        policy,
        canvas_config=canvas_config,
        snapshot=snapshot,
        target_environment=target_environment,
    )
    reports: list[ExecutionPreconditionReport] = []
    for intent in packet.intents:
        if intent.operation not in MUTATION_OPERATIONS:
            continue
        reports.append(
            evaluate_preconditions(
                packet,
                intent,
                approval,
                policy,
                canvas_config=canvas_config,
                snapshot=snapshot,
                target_environment=target_environment,
            )
        )
    return requests, reports


__all__ = [
    "build_writer_requests",
    "build_writer_requests_with_reports",
    "detect_request_collisions",
    "stable_request_id",
]
