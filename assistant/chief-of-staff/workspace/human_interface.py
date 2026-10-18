"""Reusable deterministic Phase K presentation and human-review helpers."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from query_layer import DeterministicQueryLayer
from validate import SchemaValidationError, load_json, validate_schema


ROOT = Path(__file__).resolve().parent
POLICY_PATH = ROOT / "registry/interface-policy.json"
POLICY_SCHEMA_PATH = ROOT / "schemas/interface-policy.schema.json"
REVIEW_ITEM_SCHEMA_PATH = ROOT / "schemas/review-queue-item.schema.json"
STATUS_SCHEMA_PATH = ROOT / "schemas/interface-status.schema.json"

COMMANDS = {"status", "explain", "related", "evidence", "uncertain", "recovery"}
EXPLANATION_SECTIONS = {
    "identity", "known", "sources", "evidence", "relationships", "confidence",
    "authority", "review_state", "unknowns", "actions",
}
REVIEW_STATES = {"unreviewed", "reviewed", "approved", "rejected", "deferred"}
REVIEW_REASONS = {
    "conflict", "unknown_authority", "missing_evidence", "missing_representation",
    "recovery_candidate", "unreviewed_relationship",
}


class InterfaceValidationError(ValueError):
    """Raised when an interface contract or generated view is invalid."""


def interface_policy_errors(policy: dict[str, Any]) -> list[str]:
    try:
        validate_schema(policy, load_json(POLICY_SCHEMA_PATH))
    except (SchemaValidationError, TypeError) as exc:
        return [str(exc)]
    errors: list[str] = []
    if set(policy["commands"]) != COMMANDS:
        errors.append("Phase K command set is incomplete")
    if set(policy["explanation_sections"]) != EXPLANATION_SECTIONS:
        errors.append("Phase K explanation section set is incomplete")
    if set(policy["review_states"]) != REVIEW_STATES:
        errors.append("Phase K review state set is incomplete")
    if set(policy["review_reasons"]) != REVIEW_REASONS:
        errors.append("Phase K review reason set is incomplete")
    if any(
        policy[key]
        for key in (
            "web_interface_enabled", "persistent_service_enabled",
            "natural_language_enabled", "ai_enabled", "source_write_enabled",
        )
    ):
        errors.append("Phase K web, service, natural-language, AI, and source-write capabilities must remain disabled")
    if policy["action_capabilities"]:
        errors.append("Phase K cannot expose action capabilities")
    return errors


def load_interface_policy() -> dict[str, Any]:
    policy = load_json(POLICY_PATH)
    errors = interface_policy_errors(policy)
    if errors:
        raise InterfaceValidationError(errors[0])
    return policy


def review_item_errors(item: dict[str, Any]) -> list[str]:
    try:
        validate_schema(item, load_json(REVIEW_ITEM_SCHEMA_PATH))
    except (SchemaValidationError, TypeError) as exc:
        return [str(exc)]
    if item["confidence"] == item["review_state"]:
        return ["confidence and review state must remain independent dimensions"]
    if item["authority_effect"] != "none" or item["action_authority"] != "none":
        return ["review items cannot create authority or actions"]
    return []


def interface_status_errors(status: dict[str, Any]) -> list[str]:
    try:
        validate_schema(status, load_json(STATUS_SCHEMA_PATH))
    except (SchemaValidationError, TypeError) as exc:
        return [str(exc)]
    if status["actions"]:
        return ["interface status cannot expose actions"]
    return []


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9._:-]+", "-", value.lower()).strip("-") or "unknown"


def make_review_item(
    item_id: str,
    subject_ref: str,
    reason_type: str,
    summary: str,
    *,
    source_refs: list[str] | None = None,
    confidence: str = "unknown",
    review_state: str = "unreviewed",
    recommended_next_step: str = "Teacher review required.",
) -> dict[str, Any]:
    item = {
        "schema_version": 1,
        "item_id": item_id,
        "subject_ref": subject_ref,
        "reason_type": reason_type,
        "summary": summary,
        "source_refs": sorted(set(source_refs or [])),
        "confidence": confidence,
        "review_state": review_state,
        "recommended_next_step": recommended_next_step,
        "recommendation_state": "not_an_action",
        "authority_effect": "none",
        "action_authority": "none",
    }
    errors = review_item_errors(item)
    if errors:
        raise InterfaceValidationError(errors[0])
    return item


def build_review_queue(
    layer: DeterministicQueryLayer,
    *,
    scope: str = "all",
    permission_grants: list[str] | None = None,
    review_state: str | None = None,
) -> list[dict[str, Any]]:
    if review_state is not None and review_state not in REVIEW_STATES:
        raise InterfaceValidationError(f"unsupported review state: {review_state}")
    grants = permission_grants or []
    reason_map = {
        "conflict": ("conflict", "Review competing evidence; do not select a winner automatically."),
        "unknown_authority": ("unknown_authority", "Review authority evidence; unknown remains unknown."),
        "missing_evidence": ("missing_evidence", "Review whether an approved evidence source should be added."),
        "missing_representation": ("missing_representation", "Review the expected representation and its evidence."),
        "unreviewed_candidate": ("recovery_candidate", "Review candidate evidence and risk; no recovery action is available."),
        "unknown_entity": ("missing_evidence", "Review identity and approved source coverage."),
    }
    items: dict[str, dict[str, Any]] = {}
    for uncertainty in layer.uncertain(scope=scope, permission_grants=grants):
        reason_type, next_step = reason_map[uncertainty["uncertainty_type"]]
        subject = uncertainty["item_ref"]
        entity = layer.entities.get(subject)
        source_refs = entity["sources"] if entity is not None else [subject]
        item_id = f"review-item:{reason_type}:{_slug(subject)}"
        items[item_id] = make_review_item(
            item_id,
            subject,
            reason_type,
            uncertainty["detail"],
            source_refs=source_refs,
            confidence=uncertainty["confidence"],
            review_state=uncertainty["review_state"],
            recommended_next_step=next_step,
        )

    visible_relationship_ids = {
        relationship["relationship_id"]
        for entity_id in sorted(layer.entities)
        for relationship in layer.related_to(
            entity_id, scope=scope, permission_grants=grants
        )
    }
    for relationship in layer.relationships:
        if relationship["relationship_id"] not in visible_relationship_ids:
            continue
        if relationship["review_state"] not in {"unreviewed", "deferred"}:
            continue
        item_id = f"review-item:unreviewed-relationship:{_slug(relationship['relationship_id'])}"
        items[item_id] = make_review_item(
            item_id,
            relationship["relationship_id"],
            "unreviewed_relationship",
            (
                f"Review {relationship['relationship_type']} from "
                f"{relationship['source_ref']} to {relationship['target_ref']}."
            ),
            source_refs=[
                relationship["evidence"]["package_id"],
                relationship["provenance"]["source_observation_ref"],
            ],
            confidence=relationship["confidence"],
            review_state=relationship["review_state"],
            recommended_next_step="Teacher may review the relationship assertion; no approval action is implemented.",
        )

    queue = sorted(items.values(), key=lambda item: item["item_id"])
    if review_state is not None:
        queue = [item for item in queue if item["review_state"] == review_state]
    return queue


def build_interface_status(layer: DeterministicQueryLayer) -> dict[str, Any]:
    queue = build_review_queue(layer)
    resource_count = sum(
        item["type"] in {"logical_resource", "representation", "registry_entry"}
        for item in layer.entities.values()
    )
    unknown_authority = sum(
        item["authority_context"]["role"] == "unknown"
        for item in layer.entities.values()
    )
    assigned_authority = len(layer.entities) - unknown_authority
    conflicts = len(layer.model.get("conflicts", []))
    systems = [
        {
            "name": "Resource Registry",
            "status": "OK" if resource_count else "WARN",
            "detail": f"{resource_count} resource or representation entities available.",
        },
        {
            "name": "Workspace Model",
            "status": "OK" if layer.entities else "FAIL",
            "detail": f"{len(layer.entities)} entities loaded from fixed approved inputs.",
        },
        {
            "name": "Relationships",
            "status": "WARN" if conflicts else "OK",
            "detail": f"{len(layer.relationships)} relationships; {conflicts} unresolved conflicts.",
        },
        {
            "name": "Recovery",
            "status": "OK",
            "detail": "Explanation-only; live candidate generation and recovery execution are disabled.",
        },
    ]
    available_systems = sorted(
        item["label"]
        for item in layer.entities.values()
        if item["type"] == "registry_entry"
        or item["entity_id"].startswith("application-concept:")
    )
    status = {
        "schema_version": 1,
        "title": "Chief of Staff Status",
        "systems": systems,
        "available_systems": available_systems,
        "known_entities": len(layer.entities),
        "unresolved_items": len(queue),
        "authority_state": {
            "assigned": assigned_authority,
            "unknown": unknown_authority,
            "conflicts": conflicts,
        },
        "validation_status": "PASS",
        "actions": [],
    }
    errors = interface_status_errors(status)
    if errors:
        raise InterfaceValidationError(errors[0])
    return status


def _heading(title: str) -> str:
    return f"\n{title.upper()}"


def _list(values: list[str], empty: str = "None") -> list[str]:
    return [f"- {value}" for value in values] if values else [empty]


def render_status(status: dict[str, Any]) -> str:
    lines = [status["title"], _heading("Systems")]
    lines.extend(
        f"{item['name']}: {item['status']} — {item['detail']}"
        for item in status["systems"]
    )
    lines.extend([_heading("Known"), f"{status['known_entities']} entities available."])
    lines.extend([_heading("Available Systems"), *_list(status["available_systems"])])
    lines.extend([_heading("Evidence"), "Fixed registries and approved Phase D/E/F/G artifacts loaded."])
    lines.extend([_heading("Confidence"), f"Contract validation: {status['validation_status']}"])
    authority = status["authority_state"]
    lines.extend([
        _heading("Authority"),
        f"Assigned: {authority['assigned']}; unknown: {authority['unknown']}; conflicts: {authority['conflicts']}.",
    ])
    lines.extend([_heading("Unknowns"), f"{status['unresolved_items']} items require or await review."])
    lines.extend([_heading("Actions"), "None available."])
    return "\n".join(lines)


def render_explanation(
    explanation: dict[str, Any],
    evidence: list[dict[str, Any]],
    relationships: list[dict[str, Any]],
) -> str:
    authority = explanation["authority_context"]
    lines = [
        "CHIEF OF STAFF EXPLANATION",
        _heading("Identity"),
        explanation["subject_ref"],
        f"Type: {explanation['subject_type']}",
        _heading("Known"),
        explanation["summary"],
        _heading("Sources"),
        *_list(explanation["sources"]),
        _heading("Evidence"),
    ]
    lines.extend(
        _list([
            f"{item['claim']} [{item['package_id']}; provenance: {', '.join(item['provenance']) or 'unknown'}]"
            for item in evidence
        ], "No evidence package is linked.")
    )
    lines.append(_heading("Relationships"))
    lines.extend(
        _list([
            f"{item['relationship_type']} {item['direction']} {item['related_ref']} [{item['confidence']}]"
            for item in relationships
        ], "No relationships are known.")
    )
    lines.extend([
        _heading("Confidence"), explanation["confidence"].title(),
        _heading("Authority"),
        f"Role: {authority['role']}; scope: {authority['scope']}; basis: {authority['basis']}.",
        _heading("Review State"), explanation["review_state"].title(),
        _heading("Unknowns"), *_list(explanation["uncertainties"]),
        _heading("Actions"), "None available.",
    ])
    return "\n".join(lines)


def render_relationships(entity_ref: str, values: list[dict[str, Any]], unknowns: list[str]) -> str:
    lines = [
        "CHIEF OF STAFF RELATIONSHIPS",
        _heading("Identity"), entity_ref,
        _heading("Known"), f"{len(values)} matching relationships.",
        _heading("Relationships"),
    ]
    lines.extend(_list([
        f"{item['relationship_type']} {item['direction']} {item['related_ref']}"
        for item in values
    ], "No matching relationships."))
    lines.extend([_heading("Evidence")])
    lines.extend(_list([
        f"{item['evidence_package_id']} — {item['provenance']['rule_id']}"
        for item in values
    ], "No relationship evidence."))
    lines.extend([_heading("Confidence")])
    lines.extend(_list([
        f"{item['relationship_id']}: {item['confidence'].title()} ({item['review_state']})"
        for item in values
    ], "Unknown"))
    lines.extend([
        _heading("Authority"), "Relationships create no authority.",
        _heading("Unknowns"), *_list(unknowns, "None reported."),
        _heading("Actions"), "None available.",
    ])
    return "\n".join(lines)


def render_evidence(entity_ref: str, values: list[dict[str, Any]], unknowns: list[str]) -> str:
    lines = [
        "CHIEF OF STAFF EVIDENCE",
        _heading("Identity"), entity_ref,
        _heading("Known"), f"{len(values)} matching evidence packages.",
        _heading("Evidence"),
    ]
    lines.extend(_list([
        f"{item['package_id']}: {item['claim']}"
        for item in values
    ], "No evidence package is linked."))
    lines.extend([_heading("Sources / Observations")])
    lines.extend(_list(sorted({source for item in values for source in item["sources"]})))
    lines.extend([_heading("Provenance")])
    lines.extend(_list(sorted({source for item in values for source in item["provenance"]})))
    lines.extend([_heading("Confidence")])
    lines.extend(_list([
        f"{item['package_id']}: {item['confidence'].title()} ({item['review_state']})"
        for item in values
    ], "Unknown"))
    lines.extend([
        _heading("Authority"), "Evidence creates no authority.",
        _heading("Unknowns"), *_list(unknowns, "None reported."),
        _heading("Actions"), "None available.",
    ])
    return "\n".join(lines)


def render_review_queue(values: list[dict[str, Any]]) -> str:
    lines = [
        "CHIEF OF STAFF REVIEW QUEUE",
        _heading("Known"), f"{len(values)} unresolved items require or await human judgment.",
        _heading("Unknowns"),
    ]
    lines.extend(_list([
        f"{item['subject_ref']}: {item['summary']} [{item['reason_type']}; {item['review_state']}]"
        for item in values
    ], "No unresolved items are visible in this scope."))
    lines.extend([_heading("Evidence")])
    lines.extend(_list(sorted({source for item in values for source in item["source_refs"]})))
    lines.extend([_heading("Confidence")])
    lines.extend(_list([
        f"{item['item_id']}: {item['confidence'].title()}"
        for item in values
    ], "Unknown"))
    lines.extend([
        _heading("Authority"), "Teacher judgment is required; the interface creates no authority.",
        _heading("Recommendations"),
        *_list([item["recommended_next_step"] for item in values], "No recommendation."),
        _heading("Actions"), "None available.",
    ])
    return "\n".join(lines)


def render_recovery(entity_ref: str, values: list[dict[str, Any]], unknowns: list[str]) -> str:
    lines = [
        "CHIEF OF STAFF RECOVERY EXPLANATION",
        _heading("Identity"), entity_ref,
        _heading("Known"), f"{len(values)} candidate representations.",
        _heading("Evidence"),
    ]
    lines.extend(_list([
        f"{item['candidate']}: {', '.join(item['evidence']) or 'no evidence'}"
        for item in values
    ], "No recovery candidate evidence."))
    lines.extend([_heading("Confidence / Risk")])
    lines.extend(_list([
        f"{item['candidate']}: confidence {item['confidence']}; risk {item['risk']}"
        for item in values
    ], "Confidence: unknown; risk: unknown."))
    lines.extend([_heading("Next Step")])
    lines.extend(_list([item["next_step"] for item in values], "No recovery step proposed."))
    lines.extend([
        _heading("Authority"), "Recovery candidates create no authority.",
        _heading("Unknowns"), *_list(unknowns, "None reported."),
        _heading("Actions"), "None available; restore, copy, and move are not implemented.",
    ])
    return "\n".join(lines)
