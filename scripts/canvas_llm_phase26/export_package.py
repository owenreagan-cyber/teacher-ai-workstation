from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def stable_hash(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def build_week_summary(packet: dict[str, Any]) -> str:
    readiness = packet.get("readiness", {})
    return "\n".join(
        [
            f"Week: {packet['weekCode']}",
            f"Packet: {packet['packetId']}",
            f"Readiness: {readiness.get('score', 0)} / {readiness.get('maxScore', 100)}",
            f"Subjects ready: {readiness.get('subjectReady', 0)} / {readiness.get('requiredSubjectCount', 0)}",
            f"Resources: {readiness.get('verifiedResources', 0)} verified, {readiness.get('unresolvedResources', 0)} unresolved, {readiness.get('blockedResources', 0)} blocked",
            f"Pages previewed: {readiness.get('pagesReady', 0)}",
            f"Assignments previewed: {readiness.get('assignmentsPreviewed', 0)}",
            f"Full-week approval: {packet.get('approvalPanel', {}).get('fullWeekApprovalState', 'Not approved')}",
            "",
            packet.get("readiness", {}).get("explanation", ""),
        ]
    )


def build_export_package(packet: dict[str, Any], export_root: Path) -> dict[str, Any]:
    week_dir = export_root / packet["weekCode"]
    week_dir.mkdir(parents=True, exist_ok=True)
    write_json(week_dir / "week-packet.json", packet)
    write_text(week_dir / "week-summary.txt", build_week_summary(packet))
    write_json(week_dir / "validation-report.json", packet.get("validation", {}))
    write_json(week_dir / "provenance.json", {"provenance": packet.get("provenance", [])})
    write_json(week_dir / "resource-review.json", packet.get("resourceResolution", {}))
    write_json(week_dir / "revision-history.json", {"revisions": packet.get("revisionHistory", [])})
    write_json(week_dir / "deployment-manifest-preview.json", packet.get("deploymentManifestPreview", {}))
    for folder in ("agenda-pages", "assignments", "reminders", "resources"):
        (week_dir / folder).mkdir(parents=True, exist_ok=True)
    for index, page in enumerate(packet.get("productionPacket", {}).get("pages", []), start=1):
        write_text(week_dir / "agenda-pages" / f"page-{index:02d}.txt", f"{page.get('title')}\n\n{page.get('body_text') or page.get('bodyText')}")
    for index, assignment in enumerate(packet.get("productionPacket", {}).get("assignments", []), start=1):
        write_text(week_dir / "assignments" / f"assignment-{index:02d}.txt", f"{assignment.get('title')}\n\n{assignment.get('body_text') or assignment.get('bodyText')}")
    for index, reminder in enumerate(packet.get("productionPacket", {}).get("assessmentReminders", []), start=1):
        write_text(week_dir / "reminders" / f"reminder-{index:02d}.txt", f"{reminder.get('title')}\n\n{reminder.get('body_text') or reminder.get('bodyText')}")
    for index, resource in enumerate(packet.get("resourceResolution", {}).get("resolvedResources", []), start=1):
        write_text(week_dir / "resources" / f"resource-{index:02d}.txt", json.dumps(resource, indent=2, sort_keys=True, ensure_ascii=False))
    manifest = {
        "weekCode": packet["weekCode"],
        "savedPath": str(week_dir),
        "fileCount": sum(1 for item in week_dir.rglob("*") if item.is_file()),
        "packageHash": stable_hash(packet),
    }
    return manifest

