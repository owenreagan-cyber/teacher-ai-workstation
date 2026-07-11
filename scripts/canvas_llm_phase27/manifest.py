from __future__ import annotations

from typing import Any


def build_manifest(packet: dict[str, Any], diffs: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "manifestVersion": 1,
        "packetVersion": 1,
        "packetRevision": int(packet.get("localState", {}).get("weekState", {}).get("revision", 0) or 0),
        "weekCode": packet["weekCode"],
        "generatedAt": packet.get("generatedAt", ""),
        "mode": "preview-only",
        "sourceHashes": {"phase26Packet": packet.get("packetId", "")},
        "targetSnapshotId": "synthetic-canvas-snapshot",
        "targetSnapshotGeneratedAt": packet.get("generatedAt", ""),
        "targetSnapshotAge": "fresh",
        "overallReadiness": "preview-only",
        "approvals": [],
        "operations": [
            {"kind": "health-check-only", "objectId": d["objectId"], "status": d["comparisonStatus"].lower(), "executable": False}
            for d in diffs
        ],
        "dependencies": [],
        "blockers": [d["localTitle"] for d in diffs if d["comparisonStatus"] == "BLOCKED"],
        "warnings": ["Canvas assignment due-time convention remains owner-unresolved"],
        "rollbackPlan": [],
        "validationSummary": {"passCount": len(diffs), "warnCount": 1, "failCount": 0},
        "provenance": [{"sourceType": "phase26", "sourceRef": "apps/unified-weekly-production/data/phase26-demo.json"}],
    }

