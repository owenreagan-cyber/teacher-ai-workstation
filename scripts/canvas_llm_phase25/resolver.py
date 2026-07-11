from __future__ import annotations

import json
from typing import Any

from .correction_memory import find_correction
from .models import ResolutionEvidence, ResolvedResource, ResourceIdentity, ResourceRequirement, ReviewQueueItem, compact
from .registry import is_verified, load_corrections, load_registry, registry_index, resource_lookup


EXACT_RESOURCE_TYPES = {
    "student-book",
    "reading-test",
    "study-guide",
    "written-test",
    "fact-test",
    "teacher-answer-key",
    "secure-assessment",
    "word-list",
    "practice-material",
    "classroom-practice",
    "page-resource",
    "investigation-resource",
}


def requirement_label(requirement: ResourceRequirement) -> str:
    return requirement.title_hint or f"{compact(requirement.subject).title()} {requirement.resource_type}"


def build_candidate_payload(resource: ResourceIdentity) -> dict[str, Any]:
    return {
        "resourceId": resource.resource_id,
        "canonicalName": resource.canonical_name,
        "verificationStatus": resource.verification_status,
        "availabilityStatus": resource.availability_status,
        "visibility": resource.visibility,
        "deploymentPolicy": resource.deployment_policy,
        "canvasStatus": resource.canvas_status,
        "lessonRef": resource.lesson_ref,
        "resourceType": resource.resource_type,
        "contentHash": resource.content_hash,
    }


def resource_matches_requirement(resource: ResourceIdentity, requirement: ResourceRequirement) -> bool:
    if compact(resource.subject).lower() != compact(requirement.subject).lower():
        return False
    if compact(resource.resource_type).lower() != compact(requirement.resource_type).lower():
        return False
    if requirement.lesson_ref and compact(resource.lesson_ref).lower() == compact(requirement.lesson_ref).lower():
        return True
    applies = resource.applicability or {}
    if requirement.lesson_number is not None and int(applies.get("lessonNumber") or -1) == int(requirement.lesson_number):
        return True
    if requirement.assessment_number is not None and int(applies.get("assessmentNumber") or -1) == int(requirement.assessment_number):
        return True
    parity = compact(applies.get("parity")).lower()
    if parity and compact(requirement.variant).lower() == parity:
        return True
    if requirement.assessment_family and compact(applies.get("assessmentFamily")).lower() == compact(requirement.assessment_family).lower():
        return True
    if applies.get("lessonRange"):
        start = int(applies["lessonRange"].get("start") or 0)
        end = int(applies["lessonRange"].get("end") or 0)
        if requirement.lesson_number is not None and start <= int(requirement.lesson_number) <= end:
            return True
    if applies.get("subjectWide") and compact(resource.subject).lower() == compact(requirement.subject).lower():
        return True
    if applies.get("curriculumSequence") and compact(resource.subject).lower() == compact(requirement.subject).lower():
        return True
    if applies.get("weekCode") and compact(applies.get("weekCode")).upper() == "Q1W5":
        return True
    return False


def resource_matches_exact(resource: ResourceIdentity, requirement: ResourceRequirement) -> bool:
    if compact(resource.subject).lower() != compact(requirement.subject).lower():
        return False
    if compact(resource.resource_type).lower() != compact(requirement.resource_type).lower():
        return False
    if compact(requirement.resource_type).lower() not in EXACT_RESOURCE_TYPES:
        return False
    if requirement.lesson_ref and compact(resource.lesson_ref).lower() == compact(requirement.lesson_ref).lower():
        return True
    if requirement.lesson_number is not None and int(resource.lesson_number or -1) == int(requirement.lesson_number):
        return True
    if requirement.assessment_number is not None and int(resource.assessment_number or -1) == int(requirement.assessment_number):
        return True
    return False


def confidence_for_method(method: str) -> float:
    return {
        "exact-verified-match": 0.99,
        "owner-approved-correction": 0.97,
        "approved-reusable-resource": 0.93,
        "approved-lesson-range-match": 0.9,
        "approved-parity-or-family-match": 0.88,
        "verified-source-alias": 0.85,
        "historical-approved-pattern": 0.8,
        "unverified-candidate": 0.45,
        "unresolved": 0.0,
    }.get(method, 0.5)


def resolve_requirement(
    requirement: ResourceRequirement,
    registry: list[ResourceIdentity],
    corrections: list[dict[str, Any]],
) -> ResolvedResource:
    lookup = resource_lookup(registry)
    index = registry_index(registry)
    req_visibility = compact(requirement.required_visibility).lower()
    exact_candidates = [item for item in registry if resource_matches_exact(item, requirement)]
    deduped: list[ResourceIdentity] = []
    seen_ids: set[str] = set()
    for candidate in exact_candidates:
        if candidate.resource_id in seen_ids:
            continue
        seen_ids.add(candidate.resource_id)
        deduped.append(candidate)
    exact_candidates = deduped
    correction = find_correction(
        corrections,
        requirement.subject,
        compact(requirement.week_code),
        compact(requirement.day),
        requirement.resource_type,
    )
    if correction:
        corrected = lookup.get(compact(correction.get("approvedResourceId")).lower())
        if corrected and is_verified(corrected):
            return ResolvedResource(
                requirement=requirement,
                resolution_method="owner-approved-correction",
                confidence=confidence_for_method("owner-approved-correction"),
                review_state="resolved",
                explanation=[f"Owner-approved correction promotes {correction.get('predictedResourceId')} to {corrected.resource_id}."],
                source_evidence=[ResolutionEvidence("teacher-correction", correction.get("sourceRule") or "teacher.correction", correction.get("reason") or "Teacher correction applied")],
                resource=corrected,
                linked=req_visibility == "student-facing" and corrected.visibility == "student-facing" and corrected.deployment_policy == "approved-for-canvas-link",
            )
    verified_candidates = [item for item in exact_candidates if is_verified(item) and item.availability_status == "available"]
    if verified_candidates:
        chosen = sorted(verified_candidates, key=lambda item: (-int(item.revision), compact(item.resource_id)))[0]
        ignored = [build_candidate_payload(item) for item in exact_candidates if item.resource_id != chosen.resource_id]
        explanation = [f"Matched {requirement.lesson_ref or requirement.resource_type} exactly."]
        if any(item.availability_status == "duplicate" for item in exact_candidates if item.resource_id != chosen.resource_id):
            explanation.append("Skipped duplicate copy in favor of the available verified resource.")
        if any(item.availability_status == "moved" for item in exact_candidates if item.resource_id != chosen.resource_id):
            explanation.append("Ignored a moved copy because the available verified copy wins.")
        conflicts = [build_candidate_payload(item) for item in verified_candidates if item.resource_id != chosen.resource_id]
        blocked = req_visibility == "student-facing" and chosen.visibility in {"teacher-only", "answer-key", "assessment-secure"}
        return ResolvedResource(
            requirement=requirement,
            resolution_method="exact-verified-match",
            confidence=confidence_for_method("exact-verified-match"),
            review_state="blocked" if blocked else "resolved",
            explanation=explanation + (["Teacher-only or secure resource cannot resolve student-facing output."] if blocked else []),
            source_evidence=[ResolutionEvidence("registry", chosen.resource_id, "exact verified lesson or assessment match")],
            ignored_candidates=ignored,
            conflicts=conflicts,
            blocked_reason="teacher-only or secure resource cannot resolve student-facing requirement" if blocked else None,
            resource=None if blocked else chosen,
            linked=not blocked and req_visibility == "student-facing" and chosen.visibility == "student-facing" and chosen.deployment_policy == "approved-for-canvas-link",
        )
    reusable_candidates = [item for item in registry if is_verified(item) and resource_matches_requirement(item, requirement)]
    if reusable_candidates:
        chosen = sorted(reusable_candidates, key=lambda item: (-int(item.revision), compact(item.resource_id)))[0]
        conflicts = [build_candidate_payload(item) for item in reusable_candidates[1:] if item.content_hash == chosen.content_hash or item.availability_status == chosen.availability_status]
        method = "approved-reusable-resource"
        explanation = ["Matched approved reusable resource."]
        if chosen.applicability.get("lessonRange"):
            method = "approved-lesson-range-match"
            explanation = [f"Matched approved lesson-range resource {chosen.applicability['lessonRange'].get('start')}–{chosen.applicability['lessonRange'].get('end')}."]
        elif compact(chosen.applicability.get("parity")).lower() in {"even", "odd"} or chosen.applicability.get("assessmentFamily"):
            method = "approved-parity-or-family-match"
            explanation = ["Applied approved parity or assessment-family reusable resource."]
        elif chosen.applicability.get("subjectWide") or chosen.applicability.get("curriculumSequence"):
            method = "approved-reusable-resource"
        elif chosen.aliases:
            method = "verified-source-alias"
            explanation = ["Matched verified source alias."]
        return ResolvedResource(
            requirement=requirement,
            resolution_method=method,
            confidence=confidence_for_method(method),
            review_state="resolved",
            explanation=explanation,
            source_evidence=[ResolutionEvidence("registry", chosen.resource_id, method)],
            ignored_candidates=[build_candidate_payload(item) for item in reusable_candidates[1:]],
            conflicts=conflicts,
            resource=chosen,
            linked=req_visibility == "student-facing" and chosen.visibility == "student-facing" and chosen.deployment_policy == "approved-for-canvas-link",
        )
    unverified = [item for item in registry if compact(item.resource_type).lower() == compact(requirement.resource_type).lower() and resource_matches_requirement(item, requirement) and item.verification_status == "unverified"]
    if unverified:
        chosen = unverified[0]
        return ResolvedResource(
            requirement=requirement,
            resolution_method="unverified-candidate",
            confidence=confidence_for_method("unverified-candidate"),
            review_state="needs_review",
            explanation=["Selected unverified candidate for review only."],
            source_evidence=[ResolutionEvidence("registry", chosen.resource_id, "unverified candidate")],
            ignored_candidates=[build_candidate_payload(item) for item in unverified[1:]],
            resource=chosen,
            linked=False,
        )
    return ResolvedResource(
        requirement=requirement,
        resolution_method="unresolved",
        confidence=0.0,
        review_state="missing",
        explanation=["No verified or reusable local resource matches this requirement."],
        source_evidence=[],
        ignored_candidates=[],
        conflicts=[],
        resource=None,
        linked=False,
    )


def resolve_requirements(
    requirements: list[ResourceRequirement],
    registry: list[ResourceIdentity],
    corrections: list[dict[str, Any]],
) -> list[ResolvedResource]:
    return [resolve_requirement(requirement, registry, corrections) for requirement in requirements]


def build_review_queue(resolved: list[ResolvedResource]) -> list[ReviewQueueItem]:
    queue: list[ReviewQueueItem] = []
    for item in resolved:
        status = "Resolved"
        if item.review_state == "missing":
            status = "Missing"
        elif item.review_state == "needs_review":
            status = "Needs Review"
        elif item.review_state == "blocked":
            status = "Blocked"
        elif item.conflicts:
            status = "Conflicting"
        elif item.resource and item.resource.visibility in {"teacher-only", "answer-key", "assessment-secure"}:
            status = "Teacher-Only"
        queue.append(
            ReviewQueueItem(
                event_id=item.requirement.event_id,
                subject=item.requirement.subject,
                event_label=requirement_label(item.requirement),
                required_resource_class=item.requirement.resource_type,
                status=status,
                candidate_resources=[build_candidate_payload(item.resource)] if item.resource else [],
                resolver_explanation=list(item.explanation),
                confidence=item.confidence,
                recommended_teacher_action={
                    "Resolved": "No action needed.",
                    "Needs Review": "Review the candidate and promote it only if approved.",
                    "Missing": "Add an approved registry entry or a teacher correction.",
                    "Blocked": "Keep the resource out of student-facing HTML.",
                    "Conflicting": "Choose the preferred candidate and quarantine the other copies.",
                    "Teacher-Only": "Retain for teacher use only.",
                }.get(status, "No action needed."),
            )
        )
    return queue
