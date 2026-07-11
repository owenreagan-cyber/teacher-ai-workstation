from __future__ import annotations

from typing import Any


def calculate_readiness(subjects: list[dict[str, Any]], resource_resolution: dict[str, Any], production_packet: dict[str, Any], approval_panel: dict[str, Any]) -> dict[str, Any]:
    required_subjects = [subject for subject in subjects if subject.get("assignmentPolicy", "enabled") != "disabled"]
    subject_ready = sum(1 for subject in subjects if subject.get("readinessState") in {"Ready", "Approved"})
    verified_resources = len([item for item in resource_resolution.get("resolvedResources", []) if item.get("resource") and item.get("reviewState") == "resolved"])
    unresolved_resources = len([item for item in resource_resolution.get("resolvedResources", []) if item.get("reviewState") in {"missing", "needs_review"}])
    blocked_resources = len([item for item in resource_resolution.get("resolvedResources", []) if item.get("reviewState") == "blocked"])
    pages_ready = len(production_packet.get("pages", []))
    assignments_previewed = len(production_packet.get("assignments", []))
    approved_subjects = len([item for item in approval_panel.get("subjectApprovals", []) if item.get("status") == "approved" and item.get("active")])
    due_time_blocker = 1 if any("due-time" in str(item.get("message", "")).lower() for item in production_packet.get("validation", {}).get("findings", [])) else 0

    max_points = 100.0
    raw_points = (
        min(30.0, (subject_ready / max(len(required_subjects), 1)) * 30.0)
        + min(30.0, (verified_resources / max(verified_resources + unresolved_resources + blocked_resources, 1)) * 30.0)
        + min(15.0, (pages_ready / max(len(production_packet.get("pages", [])), 1)) * 15.0)
        + min(15.0, (assignments_previewed / max(len(production_packet.get("assignments", [])), 1)) * 15.0)
        + min(10.0, (approved_subjects / max(len(subjects), 1)) * 10.0)
    )
    if due_time_blocker:
        raw_points -= 8.0
    if blocked_resources:
        raw_points -= blocked_resources * 2.0
    if unresolved_resources:
        raw_points -= min(6.0, unresolved_resources * 1.5)
    score = max(0, min(100, round(raw_points)))
    explanation = (
        f"Readiness blends subject readiness ({subject_ready}/{len(required_subjects)}), "
        f"resource verification ({verified_resources} verified / {unresolved_resources} unresolved / {blocked_resources} blocked), "
        f"preview coverage ({pages_ready} pages, {assignments_previewed} assignments), and approvals ({approved_subjects} subject approvals). "
        + ("Due-time remains a blocker on deployment readiness. " if due_time_blocker else "")
        + "The score is deterministic from these counts, then capped to 0-100."
    )
    return {
        "score": score,
        "maxScore": int(max_points),
        "subjectReady": subject_ready,
        "requiredSubjectCount": len(required_subjects),
        "verifiedResources": verified_resources,
        "unresolvedResources": unresolved_resources,
        "blockedResources": blocked_resources,
        "pagesReady": pages_ready,
        "assignmentsPreviewed": assignments_previewed,
        "approvedSubjects": approved_subjects,
        "dueTimeBlocker": bool(due_time_blocker),
        "explanation": explanation,
    }

