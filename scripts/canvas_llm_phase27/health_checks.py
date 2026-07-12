from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .dependency_graph import build_dependency_graph
from .freshness import blocks_readiness, classify_freshness
from .ledger import DeploymentLedger
from .transport import DisabledCanvasTransport, MutationNotAllowedError

ROOT = Path(__file__).resolve().parents[2]

HEALTH_STATUSES = {"PASS", "WARN", "FAIL", "BLOCKED", "NOT_APPLICABLE"}


@dataclass
class HealthCheckResult:
    check: str
    status: str
    detail: str

    def __post_init__(self) -> None:
        if self.status not in HEALTH_STATUSES:
            raise ValueError(f"invalid health check status: {self.status!r}")

    def to_dict(self) -> dict[str, Any]:
        return {"check": self.check, "status": self.status, "detail": self.detail}


def _known_course_refs() -> set[str]:
    path = ROOT / "config/curriculum/canvas-course-mappings.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    known = {str(c["courseId"]) for c in data["currentProduction"]["courses"]}
    for entry in data.get("archivedReference", []):
        known.update(str(c["courseId"]) for c in entry.get("courses", []))
    return known


def classify_resolved_resource(item: dict[str, Any]) -> str:
    """Classifies one Phase 25/26 resolvedResources entry using the fields
    Phase 25 already computes (resolutionMethod, resource.verificationStatus,
    resource.visibility, resource.deploymentPolicy, blockedReason) -- no new
    resource-verification logic, just reading what Phase 25/26 already
    resolved. Matches the visibility/deployment-policy vocabulary documented
    in docs/programs/canvas-llm/phase-25-curriculum-source-intelligence/
    resource-safety-classification.md."""
    resource = item.get("resource") or {}
    if item.get("resolutionMethod") == "unresolved" or not resource:
        return "missing"
    if item.get("blockedReason") or resource.get("deploymentPolicy") == "blocked":
        return "blocked"
    visibility = resource.get("visibility")
    if visibility == "teacher-only":
        return "teacher-only"
    if visibility == "assessment-secure":
        return "assessment-secure"
    if resource.get("verificationStatus") in {"verified", "owner-approved"}:
        return "verified"
    return "unverified"


def run_health_checks(
    diffs: list[dict[str, Any]],
    manifest: dict[str, Any],
    snapshot: dict[str, Any],
    ledger_path: Path | None = None,
    phase26_packet: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Deterministic, no-AI-judgment health checks over a built Phase 27
    packet. Every result here is derived from real production state (the
    diffs, the manifest, the snapshot, and -- when available -- the ledger),
    never from a fixture-declared status."""
    results: list[HealthCheckResult] = []

    def add(check: str, status: str, detail: str) -> None:
        results.append(HealthCheckResult(check, status, detail))

    # snapshot schema + freshness
    add(
        "snapshot-schema",
        "PASS" if snapshot.get("snapshotId") and snapshot.get("generatedAt") else "FAIL",
        "snapshot has required snapshotId/generatedAt fields",
    )
    freshness = classify_freshness(snapshot.get("generatedAt", ""))
    add(
        "snapshot-freshness",
        "FAIL" if blocks_readiness(freshness) else "PASS",
        f"snapshot freshness classified as {freshness!r}",
    )

    # target-course existence / archived protection
    known_courses = _known_course_refs()
    target_courses = {d["targetCourse"] for d in diffs if d.get("targetCourse")}
    unknown_courses = target_courses - known_courses
    archived_targets = [
        d["objectId"] for d in diffs if "archived" in " ".join(d.get("blockers", [])).lower()
    ]
    add(
        "target-course-existence",
        "WARN" if unknown_courses else "PASS",
        f"unknown course refs: {sorted(unknown_courses)}" if unknown_courses else "all target courses recognized",
    )
    add(
        "archived-course-protection",
        "PASS" if all(d["comparisonStatus"] == "BLOCKED" for d in diffs if d["objectId"] in archived_targets) else "FAIL",
        f"{len(archived_targets)} archived-course operation(s), all BLOCKED" if archived_targets else "no archived-course targets present",
    )

    # duplicate objects (same objectId appearing twice would indicate a bug upstream)
    ids = [d["objectId"] for d in diffs]
    duplicates = {i for i in ids if ids.count(i) > 1}
    add(
        "duplicate-objects",
        "FAIL" if duplicates else "PASS",
        f"duplicate objectIds: {sorted(duplicates)}" if duplicates else "no duplicate objectIds",
    )

    # module placement
    missing_module = [d["objectId"] for d in diffs if d.get("modulePlacement", {}).get("status") == "missing-module"]
    ambiguous_module = [d["objectId"] for d in diffs if d.get("modulePlacement", {}).get("status") == "ambiguous-module"]
    needs_reorder = [d["objectId"] for d in diffs if d.get("modulePlacement", {}).get("status") == "needs-reorder"]
    add(
        "missing-module",
        "WARN" if missing_module else "PASS",
        f"objects with missing target module: {missing_module}" if missing_module else "no missing modules",
    )
    add(
        "ambiguous-module",
        "WARN" if ambiguous_module else "PASS",
        f"objects with ambiguous target module: {ambiguous_module}" if ambiguous_module else "no ambiguous modules",
    )
    add(
        "module-order",
        "WARN" if needs_reorder else "PASS",
        f"objects needing reorder: {needs_reorder}" if needs_reorder else "no reorder needed",
    )

    # publication / title / body drift signals (informational, from field diffs)
    material_changes = [d["objectId"] for d in diffs if any(fd["changeKind"] == "material content change" for fd in d.get("fieldDiffs", []))]
    add(
        "content-drift",
        "PASS",
        f"{len(material_changes)} object(s) with material content changes pending review",
    )

    # resource verification is not implemented yet in this checkpoint
    resolved_resources = ((phase26_packet or {}).get("resourceResolution", {}) or {}).get(
        "resolvedResources", []
    )
    if resolved_resources:
        counts: dict[str, int] = {}
        for item in resolved_resources:
            state = classify_resolved_resource(item)
            counts[state] = counts.get(state, 0) + 1
        status = "WARN" if counts.get("missing") or counts.get("blocked") else "PASS"
        add(
            "resource-link-verification",
            status,
            "resolved-resource states (from Phase 25/26 resolution): "
            + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())),
        )
    else:
        add(
            "resource-link-verification",
            "NOT_APPLICABLE",
            "no phase26Packet.resourceResolution.resolvedResources supplied to this health-check run",
        )

    # due-time / approvals
    due_time_blocked = [d["objectId"] for d in diffs if any("due-time" in b.lower() for b in d.get("blockers", []))]
    add(
        "unresolved-due-time",
        "WARN" if due_time_blocked else "PASS",
        f"assignments blocked on due-time convention: {due_time_blocked}" if due_time_blocked
        else "no due-time-blocked assignments",
    )

    # dependency graph
    object_ids = [d["objectId"] for d in diffs]
    edges = [(d["objectId"], dep) for d in diffs for dep in d.get("dependencies", [])]
    graph = build_dependency_graph(object_ids, edges)
    add(
        "dependency-cycle",
        "FAIL" if graph.cycles else "PASS",
        f"cycles detected: {graph.cycles}" if graph.cycles else "no dependency cycles",
    )
    add(
        "unresolved-dependency",
        "FAIL" if graph.missing else "PASS",
        f"missing dependency edges: {graph.missing}" if graph.missing else "no unresolved dependencies",
    )
    orphaned = [
        dep
        for d in diffs
        for dep in d.get("dependencies", [])
        if dep not in object_ids
    ]
    add(
        "orphaned-operation",
        "FAIL" if orphaned else "PASS",
        f"dependencies referencing unknown operations: {orphaned}" if orphaned else "no orphaned dependencies",
    )

    # curriculum policy prohibitions (Part 22 named checks)
    history_assignments = [d for d in diffs if d["objectType"] == "assignment" and "history" in d["localTitle"].lower()]
    science_assignments = [d for d in diffs if d["objectType"] == "assignment" and "science" in d["localTitle"].lower()]
    add(
        "history-assignment-prohibition",
        "PASS" if all(d["comparisonStatus"] == "OMIT" for d in history_assignments) else "FAIL",
        "all History assignments are OMIT" if history_assignments else "no History assignments present",
    )
    add(
        "science-assignment-prohibition",
        "PASS" if all(d["comparisonStatus"] == "OMIT" for d in science_assignments) else "FAIL",
        "all Science assignments are OMIT" if science_assignments else "no Science assignments present",
    )
    checkout_14_present = any("checkout 14" in (d.get("localTitle", "") + " ".join(str(fd) for fd in d.get("fieldDiffs", []))).lower() for d in diffs)
    add(
        "checkout-14-absence",
        "FAIL" if checkout_14_present else "PASS",
        "Checkout 14 does not appear (Reading Mastery 4 has no Checkout 14)",
    )

    # mutation-disabled state: real call, not a print statement
    try:
        DisabledCanvasTransport().create_page()
        add("mutation-disabled-state", "FAIL", "DisabledCanvasTransport did not reject a mutation")
    except MutationNotAllowedError:
        add("mutation-disabled-state", "PASS", "DisabledCanvasTransport rejects mutation calls")

    # manifest-level checks
    add(
        "manifest-executable-false",
        "PASS" if manifest.get("executable") is False else "FAIL",
        "manifest.executable is False",
    )

    # ledger integrity, if a ledger path was provided
    if ledger_path is not None and Path(ledger_path).exists():
        ledger = DeploymentLedger(ledger_path)
        try:
            ok = ledger.integrity_check()
            add(
                "ledger-integrity",
                "PASS" if ok else "FAIL",
                f"PRAGMA integrity_check={'ok' if ok else 'failed'}",
            )
        finally:
            ledger.close()
    else:
        add("ledger-integrity", "NOT_APPLICABLE", "no ledger path provided to this health check run")

    return [r.to_dict() for r in results]
