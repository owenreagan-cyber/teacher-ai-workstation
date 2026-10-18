"""Shared non-authoritative evidence and expected-artifact contracts."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from validate import SchemaValidationError, load_json, validate_schema


ROOT = Path(__file__).resolve().parent
SHARED_EVIDENCE_SCHEMA_PATH = ROOT / "schemas/shared-evidence-package.schema.json"
EXPECTED_ARTIFACT_SCHEMA_PATH = ROOT / "schemas/expected-artifact-relationship.schema.json"
EVIDENCE_TYPES = {
    "relationship",
    "project",
    "application",
    "recovery",
    "classification",
    "authority",
    "availability",
}


def make_shared_evidence_package(
    evidence_package_id: str,
    evidence_type: str,
    subject_ref: str,
    claim: str,
    *,
    observations: list[str] | None = None,
    relationships: list[str] | None = None,
    authority_role: str = "unknown",
    authority_scope: str = "unknown",
    authority_basis: str = "unknown",
    confidence: str = "unknown",
    alternatives: list[str] | None = None,
    review_state: str = "unreviewed",
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "evidence_package_id": evidence_package_id,
        "evidence_type": evidence_type,
        "subject_ref": subject_ref,
        "claim": claim,
        "observations": observations or [],
        "relationships": relationships or [],
        "authority_context": {
            "role": authority_role,
            "scope": authority_scope,
            "basis": authority_basis,
        },
        "confidence": confidence,
        "alternatives": alternatives or [],
        "review_state": review_state,
        "authority_effect": "none",
        "permission_effect": "none",
    }


def shared_evidence_errors(value: dict[str, Any]) -> list[str]:
    try:
        validate_schema(value, load_json(SHARED_EVIDENCE_SCHEMA_PATH))
    except (SchemaValidationError, TypeError) as exc:
        return [str(exc)]
    errors: list[str] = []
    if value["evidence_type"] not in EVIDENCE_TYPES:
        errors.append("unsupported shared evidence type")
    has_evidence = bool(value["observations"] or value["relationships"])
    has_declared_basis = value["authority_context"]["basis"] not in {"unknown", "none"}
    if not has_evidence and not has_declared_basis:
        errors.append("shared evidence package must cite evidence or an explicit basis")
    if value["authority_effect"] != "none" or value["permission_effect"] != "none":
        errors.append("evidence cannot create authority or permission")
    return errors


def make_expected_artifact_relationship(
    relationship_id: str,
    source_ref: str,
    expected_artifact_ref: str,
    expected_artifact_type: str,
    source: str,
    confidence: str,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "relationship_id": relationship_id,
        "relationship_type": "expected_artifact_of",
        "source_ref": source_ref,
        "expected_artifact_ref": expected_artifact_ref,
        "expected_artifact_type": expected_artifact_type,
        "source": source,
        "confidence": confidence,
        "review_state": "unreviewed",
        "existence_claim": "none",
        "authority_effect": "none",
        "action_effect": "none",
    }


def expected_artifact_errors(value: dict[str, Any]) -> list[str]:
    try:
        validate_schema(value, load_json(EXPECTED_ARTIFACT_SCHEMA_PATH))
    except (SchemaValidationError, TypeError) as exc:
        return [str(exc)]
    if value["existence_claim"] != "none":
        return ["expected artifact relationship cannot claim current existence"]
    return []


def synthetic_math_expected_artifacts() -> list[dict[str, Any]]:
    source_ref = "logical-resource:math:lesson-27"
    source = "synthetic:math-lesson-27-expectation"
    specifications = [
        ("presentation-pdf", "presentation_pdf"),
        ("html-presentation", "html_presentation"),
        ("teacher-notes", "teacher_notes"),
    ]
    return [
        make_expected_artifact_relationship(
            f"expected-artifact:math-lesson-27:{slug}",
            source_ref,
            f"logical-resource:math:lesson-27:{slug}",
            artifact_type,
            source,
            "medium",
        )
        for slug, artifact_type in specifications
    ]
