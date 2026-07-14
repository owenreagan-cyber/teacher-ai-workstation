from __future__ import annotations

from pathlib import Path
from typing import Any

from .dependency_graph import build_dependency_graph
from .freshness import blocks_readiness, classify_freshness
from .rollback_plan import build_rollback_plan
from .safety_diff import DUE_TIME_UNRESOLVED_WARNING

REPO_ROOT = Path(__file__).resolve().parents[2]


def _repo_relative(path: str) -> str:
    """Provenance must never leak a local absolute filesystem path into an
    exported manifest (Part 32). Store paths relative to the repo root."""
    try:
        return str(Path(path).resolve().relative_to(REPO_ROOT))
    except ValueError:
        return Path(path).name

OPERATION_KIND_BY_OBJECT_TYPE = {
    "page": "upsert-page",
    "assignment": "upsert-assignment",
    "module": "place-page-in-module",
    "module_item": "place-assignment-in-module",
    "announcement": "prepare-announcement",
    "file": "reference-existing-file",
    "course_target": "health-check-only",
}

_STATUS_TO_OPERATION_STATUS = {
    "CREATE": "ready",
    "UPDATE": "ready",
    "UNCHANGED": "unchanged",
    "BLOCKED": "blocked",
    "CONFLICT": "conflict",
    "OMIT": "omitted",
    "DELETE_CANDIDATE": "needs-review",
}


def build_manifest(
    packet: dict[str, Any],
    diffs: list[dict[str, Any]],
    snapshot: dict[str, Any],
    phase26_packet_path: str,
    snapshot_path: str,
) -> dict[str, Any]:
    freshness = classify_freshness(snapshot["generatedAt"])

    object_ids = [d["objectId"] for d in diffs]
    edges = [(d["objectId"], dep) for d in diffs for dep in d.get("dependencies", [])]
    # Seed with everything already BLOCKED/OMIT/CONFLICT for intrinsic reasons
    # (due-time, archived-course, policy, ambiguous match) -- otherwise this
    # rebuild only sees graph-structural blocks (cycles/missing edges) and
    # `dependencies.blocked` misses objects that are BLOCKED purely because
    # they depend on one of these (e.g. an object depending on a due-time
    # -blocked assignment). safety_diff.py computes the same seed set for
    # the same reason; this mirrors it so the manifest's own dependency
    # report is consistent with the statuses it is reporting on.
    intrinsically_blocked = {
        d["objectId"] for d in diffs if d["comparisonStatus"] in {"BLOCKED", "OMIT", "CONFLICT"}
    }
    graph = build_dependency_graph(object_ids, edges, initially_blocked=intrinsically_blocked)

    operations = []
    for d in diffs:
        kind = OPERATION_KIND_BY_OBJECT_TYPE.get(d["objectType"], "health-check-only")
        op_status = _STATUS_TO_OPERATION_STATUS[d["comparisonStatus"]]
        if blocks_readiness(freshness) and op_status == "ready":
            op_status = "blocked"
        operations.append(
            {
                "operationId": d["objectId"],
                "kind": kind,
                "status": op_status,
                "executable": False,
                "dependsOn": d.get("dependencies", []),
            }
        )

    blockers = sorted({b for d in diffs for b in d.get("blockers", [])})
    conflicts = [d["objectId"] for d in diffs if d["comparisonStatus"] == "CONFLICT"]
    fail_count = len(graph.cycles) + len(graph.missing) + len(conflicts)
    pass_count = len([d for d in diffs if d["comparisonStatus"] != "CONFLICT"])

    # Two different questions, not one: "did the software build this packet
    # correctly" (a dependency cycle or a missing dependency edge is a real
    # defect) versus "is this specific week's content ready to deploy" (a
    # CONFLICT/BLOCKED/OMIT item is expected, valid demo content that needs a
    # teacher decision, not a software bug). Reuses the graph already built
    # above; adds no new subsystem or category.
    structural_fail_count = len(graph.cycles) + len(graph.missing)
    system_validation_status = "PASS" if structural_fail_count == 0 else "FAIL"

    return {
        "manifestVersion": 1,
        "packetVersion": 1,
        "packetRevision": int(
            packet.get("localState", {}).get("weekState", {}).get("revision", 0) or 0
        ),
        "weekCode": packet["weekCode"],
        "generatedAt": packet.get("generatedAt", ""),
        "mode": "preview-only",
        "executable": False,
        "sourceHashes": {"phase26Packet": packet.get("packetId", "")},
        "targetSnapshotId": snapshot["snapshotId"],
        "targetSnapshotGeneratedAt": snapshot["generatedAt"],
        "targetSnapshotAge": freshness,
        "targetSnapshotFreshness": freshness,
        "overallReadiness": (
            "blocked" if (blocks_readiness(freshness) or fail_count) else "preview-only"
        ),
        "systemValidationStatus": system_validation_status,
        "approvals": [],
        "operations": operations,
        "dependencies": graph.to_dict(),
        "blockers": blockers,
        "warnings": [DUE_TIME_UNRESOLVED_WARNING],
        "rollbackPlan": build_rollback_plan(diffs),
        "validationSummary": {
            "passCount": pass_count,
            "warnCount": 1,
            "failCount": fail_count,
        },
        "provenance": [
            {"sourceType": "phase26", "sourceRef": _repo_relative(str(phase26_packet_path))},
            {"sourceType": "snapshot", "sourceRef": _repo_relative(str(snapshot_path))},
        ],
    }
