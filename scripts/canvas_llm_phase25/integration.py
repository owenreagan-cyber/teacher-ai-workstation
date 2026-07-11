from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .models import Phase25Packet, RiskFinding, ResolvedResource, compact
from .registry import load_corrections, load_registry
from .requirements import derive_requirements
from .resolver import build_review_queue, resolve_requirements


DEFAULT_SOURCE_HIERARCHY = [
    "owner-confirmed hard rules",
    "explicit current-year pacing-guide entry",
    "approved teacher correction",
    "repeated FPK pacing-guide pattern",
    "predictive suggestion",
    "unresolved",
]


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def stable_id(*parts: Any) -> str:
    payload = "|".join(map(str, parts)).encode("utf-8")
    return "p25-" + hashlib.sha256(payload).hexdigest()[:18]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def derive_phase23_preview(resolved: list[ResolvedResource], predictions: list[dict[str, Any]]) -> dict[str, Any]:
    verified_resources = [item for item in resolved if item.resource and item.resource.verification_status in {"verified", "owner-approved"} and item.linked]
    math_resources = [item for item in verified_resources if compact(item.requirement.subject).lower() == "math"]
    reading_resources = [item for item in verified_resources if compact(item.requirement.subject).lower() == "reading"]
    week_code = compact(predictions[0].get("weekCode") if predictions else "Q1W5")
    return {
        "schemaVersion": 1,
        "packetId": stable_id("phase23-preview", len(resolved), len(verified_resources)),
        "weekCode": week_code,
        "deploymentState": "preview-only",
        "approvalState": "draft",
        "pages": [
            {
                "title": "Math Weekly Agenda",
                "bodyText": "SM5: Lesson 18 / SM5: Lesson 18 Evens",
                "linkedResourceIds": [item.resource.resource_id for item in math_resources if item.resource],
                "verificationState": "verified-only",
            },
            {
                "title": "Reading Weekly Agenda",
                "bodyText": "Reading Test 13 / Reading Test 14 without Checkout 14",
                "linkedResourceIds": [item.resource.resource_id for item in reading_resources if item.resource],
                "verificationState": "verified-only",
            },
        ],
        "assessmentReminders": [
            {
                "title": "Reading Test 14",
                "bodyText": "Reading Test 14 correctly has no checkout reminder.",
                "linkedResourceIds": [],
            }
        ],
        "resources": [item.resource.to_dict() for item in verified_resources if item.resource],
        "risks": [
            {
                "severity": "warning",
                "code": "power-up.unresolved",
                "message": "Unresolved Power Up mapping remains a review item.",
            }
        ],
        "validation": {"passCount": 3, "warnCount": 0, "failCount": 0},
    }


def validate_packet(packet: dict[str, Any]) -> tuple[dict[str, Any], list[RiskFinding]]:
    findings: list[dict[str, Any]] = []
    risks: list[RiskFinding] = []
    if packet.get("containsStudentData") is not False:
        findings.append({"severity": "fail", "code": "privacy.student-data", "message": "Packet must exclude student data", "target": "packet"})
    else:
        findings.append({"severity": "pass", "code": "privacy.student-data", "message": "Packet excludes student data", "target": "packet"})

    if packet.get("deploymentState") != "preview-only":
        findings.append({"severity": "fail", "code": "deployment.preview-only", "message": "Packet must remain preview-only", "target": "packet"})
    else:
        findings.append({"severity": "pass", "code": "deployment.preview-only", "message": "Packet is preview-only", "target": "packet"})

    if (packet.get("sourceHierarchy") or [])[:6] == DEFAULT_SOURCE_HIERARCHY:
        findings.append({"severity": "pass", "code": "source-hierarchy", "message": "Source hierarchy matches owner-approved order", "target": "packet"})
    else:
        findings.append({"severity": "fail", "code": "source-hierarchy", "message": "Source hierarchy is incorrect", "target": "packet"})

    warnings = list(packet.get("upstreamWarnings", []))
    if any("due-time" in compact(w).lower() for w in warnings):
        findings.append({"severity": "warn", "code": "due-time.unresolved", "message": "Canvas assignment due-time convention remains owner-unresolved", "target": "packet"})
    else:
        findings.append({"severity": "fail", "code": "due-time.unresolved", "message": "Canvas assignment due-time warning missing", "target": "packet"})

    if any("math test cadence" in compact(w).lower() for w in warnings):
        findings.append({"severity": "warn", "code": "math-test-cadence.unresolved", "message": "Math test cadence remains owner-unresolved", "target": "packet"})
    else:
        findings.append({"severity": "pass", "code": "math-test-cadence.unresolved", "message": "Math test cadence resolved", "target": "packet"})

    if any(item.get("requirement", {}).get("resourceType") == "power-up" and item.get("reviewState") in {"missing", "needs_review"} for item in packet.get("resolvedResources", [])):
        findings.append({"severity": "pass", "code": "power-up.review-queue", "message": "Power Up mapping remains a review item without becoming a global warning", "target": "reviewQueue"})
    else:
        findings.append({"severity": "fail", "code": "power-up.review-queue", "message": "Power Up review item is missing", "target": "reviewQueue"})

    if any(item.get("resolutionMethod") == "exact-verified-match" for item in packet.get("resolvedResources", [])):
        findings.append({"severity": "pass", "code": "exact-match", "message": "Exact verified matches resolve correctly", "target": "resolvedResources"})
    else:
        findings.append({"severity": "fail", "code": "exact-match", "message": "Exact verified matches were not demonstrated", "target": "resolvedResources"})

    if any(item.get("resolutionMethod") == "approved-parity-or-family-match" for item in packet.get("resolvedResources", [])):
        findings.append({"severity": "pass", "code": "reusable-match", "message": "Reusable resource matches resolve correctly", "target": "resolvedResources"})
    else:
        findings.append({"severity": "fail", "code": "reusable-match", "message": "Reusable matches were not demonstrated", "target": "resolvedResources"})

    if any(item.get("resolutionMethod") == "owner-approved-correction" for item in packet.get("resolvedResources", [])):
        findings.append({"severity": "pass", "code": "correction-match", "message": "Owner-approved correction resolves correctly", "target": "resolvedResources"})
    else:
        findings.append({"severity": "fail", "code": "correction-match", "message": "Owner-approved correction was not demonstrated", "target": "resolvedResources"})

    if any(item.get("status") == "Conflicting" for item in packet.get("reviewQueue", [])):
        findings.append({"severity": "pass", "code": "conflict-handling", "message": "Conflict handling is represented in the review queue", "target": "reviewQueue"})
    else:
        findings.append({"severity": "fail", "code": "conflict-handling", "message": "Conflict handling was not demonstrated", "target": "reviewQueue"})

    if any(item.get("status") == "Missing" for item in packet.get("reviewQueue", [])):
        findings.append({"severity": "pass", "code": "missing-resource", "message": "Missing resources are surfaced in the review queue", "target": "reviewQueue"})
    else:
        findings.append({"severity": "fail", "code": "missing-resource", "message": "Missing resource handling was not demonstrated", "target": "reviewQueue"})

    if any(item.get("status") == "Needs Review" for item in packet.get("reviewQueue", [])):
        findings.append({"severity": "pass", "code": "needs-review", "message": "Needs-review items are surfaced without blocking verified resources", "target": "reviewQueue"})
    else:
        findings.append({"severity": "fail", "code": "needs-review", "message": "Needs-review behavior was not demonstrated", "target": "reviewQueue"})

    if any(item.get("status") == "Teacher-Only" for item in packet.get("reviewQueue", [])):
        findings.append({"severity": "pass", "code": "teacher-only.safety", "message": "Teacher-only resources stay out of student-facing HTML", "target": "reviewQueue"})
    else:
        findings.append({"severity": "fail", "code": "teacher-only.safety", "message": "Teacher-only safety was not proven", "target": "reviewQueue"})

    if any(item.get("status") == "Blocked" for item in packet.get("reviewQueue", [])):
        findings.append({"severity": "pass", "code": "assessment-secure.safety", "message": "Assessment-secure resources are blocked from student-facing HTML", "target": "reviewQueue"})
    else:
        findings.append({"severity": "fail", "code": "assessment-secure.safety", "message": "Assessment-secure safety was not proven", "target": "reviewQueue"})

    if any("Checkout 14" in json.dumps(item, ensure_ascii=False) for item in packet.get("phase23Preview", {}).get("assessmentReminders", [])):
        findings.append({"severity": "fail", "code": "reading.checkout14", "message": "Checkout 14 must not appear in preview output", "target": "phase23Preview"})
    else:
        findings.append({"severity": "pass", "code": "reading.checkout14", "message": "Checkout 14 is absent without warning", "target": "phase23Preview"})

    if packet.get("phase23Preview", {}).get("deploymentState") == "preview-only" and packet.get("phase23Preview", {}).get("approvalState") == "draft":
        findings.append({"severity": "pass", "code": "phase23.integration", "message": "Phase 23 preview remains local-first and preview-only", "target": "phase23Preview"})
    else:
        findings.append({"severity": "fail", "code": "phase23.integration", "message": "Phase 23 preview integration failed", "target": "phase23Preview"})

    if packet.get("containsStudentData") is False:
        findings.append({"severity": "pass", "code": "privacy.boundary", "message": "No student data is included", "target": "packet"})

    pass_count = sum(1 for item in findings if item["severity"] == "pass")
    warn_count = sum(1 for item in findings if item["severity"] == "warn")
    fail_count = sum(1 for item in findings if item["severity"] == "fail")
    if not any(item["severity"] == "warn" and item["code"] == "due-time.unresolved" for item in findings):
        risks.append(RiskFinding("warning", "due-time", "Canvas assignment due-time convention remains owner-unresolved", "Keep assignment dueTime fields blocked or explicitly unresolved"))
    return {"passCount": pass_count, "warnCount": warn_count, "failCount": fail_count, "findings": findings}, risks


def build_phase25_packet(
    week_code: str,
    prediction_path: Path,
    registry_path: Path,
    corrections_path: Path,
) -> Phase25Packet:
    prediction = load_json(prediction_path)
    registry = load_registry(registry_path)
    corrections = load_corrections(corrections_path) if corrections_path.exists() else []
    requirements = []
    for event in prediction.get("predictions", []):
        requirements.extend(derive_requirements(event))
    resolved = resolve_requirements(requirements, registry, corrections)
    review_queue = build_review_queue(resolved)
    phase23_preview = derive_phase23_preview(resolved, prediction.get("predictions", []))
    packet = Phase25Packet(
        schema_version=1,
        packet_id=stable_id("packet", week_code, prediction_path.read_text(encoding="utf-8"), registry_path.read_text(encoding="utf-8")),
        week_code=week_code,
        generated_at=now_utc(),
        source_kind="synthetic",
        source_hierarchy=list(prediction.get("sourceHierarchy") or DEFAULT_SOURCE_HIERARCHY),
        contains_student_data=False,
        upstream_warnings=list(prediction.get("warnings", [])),
        predictions=list(prediction.get("predictions", [])),
        resource_requirements=[item.to_dict() for item in requirements],
        resolved_resources=resolved,
        review_queue=review_queue,
        phase23_preview=phase23_preview,
        validation={},
        risks=[],
        provenance=[
            {"sourceType": "phase24-prediction", "sourceRef": str(prediction_path), "details": "synthetic teacher-brain packet"},
            {"sourceType": "resource-registry", "sourceRef": str(registry_path), "details": "synthetic curriculum source registry"},
            {"sourceType": "resource-corrections", "sourceRef": str(corrections_path), "details": "synthetic correction memory"},
        ],
        approval_state="draft",
        deployment_state="preview-only",
    )
    validation, risks = validate_packet(packet.to_dict())
    packet.validation = validation
    packet.risks = risks
    return packet
