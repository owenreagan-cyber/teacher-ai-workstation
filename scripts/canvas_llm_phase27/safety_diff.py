from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .comparison import compare_content
from .dependency_graph import build_dependency_graph
from .matching import match_object
from .models import SafetyDiffItem
from .module_placement import classify_module_placement

ROOT = Path(__file__).resolve().parents[2]

DUE_TIME_UNRESOLVED_WARNING = "Canvas assignment due-time convention remains owner-unresolved"

_RECOMMENDED_ACTION = {
    "CREATE": "Review new object before approval",
    "UPDATE": "Review changes before approval",
    "UNCHANGED": "No action needed",
    "BLOCKED": "Resolve blocker before approval",
    "CONFLICT": "Resolve ambiguous match before approval",
    "OMIT": "No action -- omitted by canonical policy",
    "DELETE_CANDIDATE": "Review for archival; no automatic deletion",
}


def load_subject_assignment_policy() -> dict[str, str]:
    """Real, owner-approved policy source (not a fixture flag): which
    subjects' assignments are enabled for Canvas deployment. History and
    Science are 'disabled' here today, which is why they are OMITted below
    -- this is the same config file Phase 22's canonical validator checks."""
    path = ROOT / "config/curriculum/canvas-course-mappings.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    return {
        item["subjectId"]: item.get("assignmentPolicy", "enabled")
        for item in data["currentProduction"]["courses"]
    }


def load_archived_course_ids() -> set[str]:
    """Real, owner-approved archived-course list (not a fixture flag): every
    courseId under an archivedReference entry with writesBlocked=true. A
    target matching one of these is BLOCKED, derived from the same canonical
    config Phase 22 validates, never from a per-object fixture field."""
    path = ROOT / "config/curriculum/canvas-course-mappings.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    archived: set[str] = set()
    for entry in data.get("archivedReference", []):
        if entry.get("writesBlocked"):
            for course in entry.get("courses", []):
                archived.add(str(course["courseId"]))
    return archived


def _drift_category(status: str, comparison: dict[str, Any]) -> str:
    if status == "CONFLICT":
        return "duplicate object"
    if status == "DELETE_CANDIDATE":
        return "object missing"
    if status in {"UNCHANGED", "CREATE", "OMIT"}:
        return "no drift"
    if status == "BLOCKED":
        return "unknown source change"
    if status == "UPDATE":
        kinds = {d["changeKind"] for d in comparison["fieldDiffs"]}
        if kinds == {"placement-only change"}:
            return "placement drift"
        if kinds == {"publication-only change"}:
            return "publication drift"
        if kinds and kinds <= {"date-only change"}:
            return "date drift"
        return "expected local change"
    return "unknown source change"


def build_safety_diff(
    local_objects: list[dict[str, Any]],
    remote_objects: list[dict[str, Any]],
    alias_registry: dict[str, str] | None = None,
    archived_courses: set[str] | None = None,
    known_modules: dict[str, list[dict[str, Any]]] | None = None,
) -> list[dict[str, Any]]:
    """Compute the Safety Diff from real matching, dependency, and policy
    state. No field in `local_objects` or `remote_objects` is permitted to
    directly set comparisonStatus -- unlike the prior implementation, there
    is no `expectedStatus` or `conflict` field read here at all."""
    alias_registry = alias_registry or {}
    archived_courses = (
        archived_courses if archived_courses is not None else load_archived_course_ids()
    )
    known_modules = known_modules or {}
    policy = load_subject_assignment_policy()

    # Pass 1: matching + intrinsic (non-dependency) status for every local
    # object. "Intrinsic" means derivable without knowing any other object's
    # status: archived target, disabled-subject policy, unresolved due time,
    # or an ambiguous match.
    object_ids = [obj["localObjectId"] for obj in local_objects]
    pass_one: dict[str, dict[str, Any]] = {}
    matched_remote_ids: set[str] = set()
    intrinsically_blocked: set[str] = set()

    for local in local_objects:
        object_id = local["localObjectId"]
        course_ref = local["courseRef"]
        same_course_remote = [r for r in remote_objects if r.get("courseRef") == course_ref]
        match = match_object(local, same_course_remote, alias_registry)

        remote: dict[str, Any] = {}
        if match.status == "matched":
            remote = next(
                r for r in same_course_remote if r["canvasId"] == match.matchedCanvasId
            )
            matched_remote_ids.add(match.matchedCanvasId)

        comparison = compare_content(local, remote)
        blockers: list[str] = []
        subject = local.get("subject", "")
        intrinsic_status: str | None = None

        if course_ref in archived_courses:
            intrinsic_status = "BLOCKED"
            blockers.append(f"target course {course_ref} is archived")
        elif local["objectType"] == "assignment" and policy.get(subject) == "disabled":
            intrinsic_status = "OMIT"
            blockers.append(f"{subject} assignment generation is disabled by canonical policy")
        elif local["objectType"] == "assignment" and not local.get("dueTimeResolved", False):
            intrinsic_status = "BLOCKED"
            blockers.append(DUE_TIME_UNRESOLVED_WARNING)
        elif match.status == "conflict":
            intrinsic_status = "CONFLICT"

        if intrinsic_status in {"BLOCKED", "OMIT", "CONFLICT"}:
            intrinsically_blocked.add(object_id)

        pass_one[object_id] = {
            "local": local,
            "match": match,
            "remote": remote,
            "comparison": comparison,
            "intrinsic_status": intrinsic_status,
            "blockers": blockers,
        }

    # Pass 2: build the dependency graph seeded with every intrinsically
    # blocked/omitted/conflicted object, so anything depending (transitively)
    # on one of them is also blocked -- this is real propagation, computed
    # after intrinsic status is known, not a fixture field.
    edges = [
        (obj["localObjectId"], dep)
        for obj in local_objects
        for dep in obj.get("dependencies", [])
    ]
    graph = build_dependency_graph(object_ids, edges, initially_blocked=intrinsically_blocked)

    # Pass 3: final status per object.
    items: list[dict[str, Any]] = []
    for object_id, ctx in pass_one.items():
        local = ctx["local"]
        match = ctx["match"]
        remote = ctx["remote"]
        comparison = ctx["comparison"]
        blockers = list(ctx["blockers"])
        status = ctx["intrinsic_status"]

        if status is None and object_id in graph.blocked:
            status = "BLOCKED"
            blockers.append(
                "blocked by dependency on an object that is BLOCKED, OMIT, CONFLICT, "
                "missing, or part of a dependency cycle"
            )
        if status is None:
            if match.status == "unresolved" and not remote:
                status = "CREATE"
            elif comparison["fieldDiffs"]:
                status = "UPDATE"
            else:
                status = "UNCHANGED"

        item = SafetyDiffItem(
            objectId=object_id,
            objectType=local["objectType"],
            localTitle=local.get("title", local.get("canonicalTitle", "")),
            targetCourse=local["courseRef"],
            matchedCanvasId=match.matchedCanvasId,
            matchReason=match.matchReason,
            matchConfidence=match.confidence,
            comparisonStatus=status,
            fieldDiffs=comparison["fieldDiffs"],
            contentHashBefore=comparison["contentHashBefore"],
            contentHashAfter=comparison["contentHashAfter"],
            metadataHashBefore=comparison["metadataHashBefore"],
            metadataHashAfter=comparison["metadataHashAfter"],
            placementHashBefore=comparison["placementHashBefore"],
            placementHashAfter=comparison["placementHashAfter"],
            sourceRevision=local.get("sourceRevision", 0),
            approvalState="Needs Review",
            blockers=blockers,
            dependencies=local.get("dependencies", []),
            driftCategory=_drift_category(status, comparison),
            recommendedAction=_RECOMMENDED_ACTION[status],
        )
        item_dict = item.to_dict()
        item_dict["localBody"] = local.get("body", "")
        placement = classify_module_placement(
            local, remote, known_modules.get(local["courseRef"], []), status
        )
        item_dict["modulePlacement"] = placement.to_dict()
        items.append(item_dict)

    for remote in remote_objects:
        if remote["canvasId"] in matched_remote_ids:
            continue
        comparison = compare_content({}, remote)
        item = SafetyDiffItem(
            objectId=f"remote-{remote['canvasId']}",
            objectType=remote.get("objectType", "page"),
            localTitle=remote.get("title", ""),
            targetCourse=remote.get("courseRef", ""),
            matchedCanvasId=remote["canvasId"],
            matchReason="no-local-counterpart",
            matchConfidence=0.0,
            comparisonStatus="DELETE_CANDIDATE",
            fieldDiffs=comparison["fieldDiffs"],
            contentHashBefore=comparison["contentHashBefore"],
            contentHashAfter=comparison["contentHashAfter"],
            metadataHashBefore=comparison["metadataHashBefore"],
            metadataHashAfter=comparison["metadataHashAfter"],
            placementHashBefore=comparison["placementHashBefore"],
            placementHashAfter=comparison["placementHashAfter"],
            sourceRevision=0,
            approvalState="Needs Review",
            blockers=[],
            dependencies=[],
            driftCategory="object missing",
            recommendedAction=_RECOMMENDED_ACTION["DELETE_CANDIDATE"],
        )
        item_dict = item.to_dict()
        item_dict["localBody"] = remote.get("body", "")
        item_dict["modulePlacement"] = classify_module_placement(
            {}, remote, [], "DELETE_CANDIDATE"
        ).to_dict()
        items.append(item_dict)

    return items
