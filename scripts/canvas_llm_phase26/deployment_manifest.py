from __future__ import annotations

from typing import Any


def build_deployment_manifest(week_code: str, production_packet: dict[str, Any], subject_workspaces: list[dict[str, Any]]) -> dict[str, Any]:
    operations: list[dict[str, Any]] = []
    for subject in subject_workspaces:
        status = "ready"
        reason = ""
        if subject.get("readinessState") == "Blocked":
            status = "blocked"
            reason = "blocked-resource"
        elif subject.get("readinessState") == "Needs Review":
            status = "needs-review"
            reason = "unresolved-resource"
        elif subject.get("approvalState") != "Approved":
            status = "needs-review"
            reason = "approval-pending"
        operations.append({"type": "page", "subject": subject["title"], "status": status, "reason": reason})
        if subject.get("assignmentPolicy", "enabled") == "disabled":
            operations.append({"type": "assignment", "subject": subject["title"], "status": "omitted", "reason": "assignment-disabled"})
        elif subject.get("readinessState") == "Blocked":
            operations.append({"type": "assignment", "subject": subject["title"], "status": "blocked", "reason": "due-time-unresolved" if subject["subject"] == "math" else "blocked-resource"})
        else:
            operations.append({"type": "assignment", "subject": subject["title"], "status": "ready", "reason": ""})
    return {
        "weekCode": week_code,
        "mode": "preview-only",
        "operations": operations,
        "packetId": production_packet.get("packetId"),
    }

