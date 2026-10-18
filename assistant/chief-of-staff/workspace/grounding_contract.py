"""Closed-vocabulary Phase L.5F response contract and safe diagnostics.

This module is deterministic and model-independent. It never connects to a
runtime, repairs model output, persists rejected content, or grants actions.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ai_context_adapter import ai_context_package_errors, local_model_request_errors
from validate import SchemaValidationError, load_json, validate_schema


ROOT = Path(__file__).resolve().parent
RESPONSE_V2_SCHEMA_PATH = ROOT / "schemas/local-model-response-v2.schema.json"
DIAGNOSTIC_SCHEMA_PATH = ROOT / "schemas/grounding-validation-result.schema.json"

V2_REQUIRED_FIELDS = (
    "schema_version",
    "response_id",
    "request_id",
    "context_id",
    "task",
    "subject_ref",
    "known_refs",
    "evidence_refs",
    "uncertainty_refs",
    "relationship_refs",
    "confidence",
    "authority",
    "review_state",
    "action_authority",
    "actions",
    "recommendations",
    "permissions",
    "access_claims",
)

GROUNDING_VIOLATION_CODES = {
    "KNOWN_CLAIM_MISSING",
    "KNOWN_CLAIM_UNSUPPORTED",
    "EVIDENCE_CLAIM_MISSING",
    "EVIDENCE_CLAIM_UNSUPPORTED",
    "EVIDENCE_COUNT_MISMATCH",
    "UNCERTAINTY_MISSING",
    "UNCERTAINTY_UNSUPPORTED",
    "UNCERTAINTY_COUNT_MISMATCH",
    "AUTHORITY_CHANGED",
    "REVIEW_STATE_CHANGED",
    "CONFIDENCE_CHANGED",
    "RELATIONSHIP_UNSUPPORTED",
    "ACTION_CONTENT_PRESENT",
    "RECOMMENDATION_CONTENT_PRESENT",
    "ACCESS_CLAIM_PRESENT",
    "PERMISSION_CLAIM_PRESENT",
    "UNKNOWN_RESPONSE_FIELD",
    "MISSING_REQUIRED_FIELD",
    "INVALID_ENUM_VALUE",
    "DUPLICATE_REFERENCE",
    "IDENTITY_MISMATCH",
    "INVALID_STRUCTURE",
}

CONTRACT_METADATA = {
    "contract_id": "local-model-response.v2",
    "known_refs": "exactly_all_supplied",
    "evidence_refs": "exactly_all_supplied",
    "uncertainty_refs": "exactly_all_supplied",
    "relationship_refs": "exactly_zero",
    "subject_ref": "exactly_one_supplied",
    "confidence": "exact_copy",
    "authority": "exact_copy",
    "review_state": "exact_copy",
    "action_authority": "exact_none",
    "actions": "exactly_zero",
    "recommendations": "exactly_zero",
    "permissions": "exactly_zero",
    "access_claims": "exactly_zero",
}

V2_OUTPUT_RULES = [
    "Return exactly one JSON object matching local-model-response.v2; no prose outside JSON.",
    "subject_ref: copy the single supplied subject_ref exactly.",
    "known_refs: select every supplied known_ref exactly once; do not paraphrase facts.",
    "evidence_refs: select every supplied evidence_ref exactly once; do not invent identifiers.",
    "uncertainty_refs: select every supplied uncertainty_ref exactly once; omit none.",
    "relationship_refs: return an empty array; relationship inference is excluded.",
    "confidence: copy the supplied confidence enum exactly.",
    "authority: copy the supplied authority enum exactly; never infer authority.",
    "review_state: copy the supplied review_state enum exactly.",
    "action_authority: return none exactly.",
    "actions: return an empty array.",
    "recommendations: return an empty array.",
    "permissions: return an empty array.",
    "access_claims: return an empty array.",
    "Do not create factual sentences, new fields, new identifiers, or semantic equivalents.",
]


def _subject_value(items: list[dict[str, Any]], subject: str, key: str) -> str:
    matches = [item[key] for item in items if item["subject_ref"] == subject]
    if len(matches) != 1:
        raise ValueError(f"context must contain exactly one {key} for subject")
    return matches[0]


def build_response_vocabulary(
    context: dict[str, Any], request: dict[str, Any]
) -> dict[str, Any]:
    """Create stable prompt-visible references without adding source facts."""

    context_errors = ai_context_package_errors(context)
    if context_errors:
        raise ValueError(context_errors[0])
    request_errors = local_model_request_errors(request, context)
    if request_errors:
        raise ValueError(request_errors[0])
    if len(context["entities"]) != 1:
        raise ValueError("v2 explain requires exactly one entity")
    subject = context["entities"][0]["entity_id"]
    known = {
        f"known:{index:03d}": item
        for index, item in enumerate(context["entities"], start=1)
    }
    evidence = {
        f"evidence:{index:03d}": item
        for index, item in enumerate(
            sorted(context["evidence_summary"], key=lambda value: value["evidence_id"]),
            start=1,
        )
    }
    uncertainties = {
        f"uncertainty:{index:03d}": value
        for index, value in enumerate(context["uncertainties"], start=1)
    }
    return {
        "contract_id": CONTRACT_METADATA["contract_id"],
        "subject_ref": subject,
        "known_refs": list(known),
        "evidence_refs": list(evidence),
        "uncertainty_refs": list(uncertainties),
        "relationship_refs": [],
        "confidence": _subject_value(context["confidence"], subject, "value"),
        "authority": _subject_value(context["authority_context"], subject, "role"),
        "review_state": _subject_value(context["review_state"], subject, "state"),
        "action_authority": "none",
        "_known": known,
        "_evidence": evidence,
        "_uncertainties": uncertainties,
    }


def prompt_vocabulary(vocabulary: dict[str, Any]) -> dict[str, Any]:
    """Return only the selection vocabulary that may enter the prompt."""

    return {
        key: vocabulary[key]
        for key in (
            "contract_id",
            "subject_ref",
            "known_refs",
            "evidence_refs",
            "uncertainty_refs",
            "relationship_refs",
            "confidence",
            "authority",
            "review_state",
            "action_authority",
        )
    }


def build_ideal_response_v2(
    context: dict[str, Any], request: dict[str, Any]
) -> dict[str, Any]:
    vocabulary = build_response_vocabulary(context, request)
    suffix = request["request_id"].removeprefix("local-model-request:")
    return {
        "schema_version": 2,
        "response_id": f"local-model-response-v2:{suffix}",
        "request_id": request["request_id"],
        "context_id": context["context_id"],
        "task": "explain",
        "subject_ref": vocabulary["subject_ref"],
        "known_refs": vocabulary["known_refs"],
        "evidence_refs": vocabulary["evidence_refs"],
        "uncertainty_refs": vocabulary["uncertainty_refs"],
        "relationship_refs": [],
        "confidence": vocabulary["confidence"],
        "authority": vocabulary["authority"],
        "review_state": vocabulary["review_state"],
        "action_authority": "none",
        "actions": [],
        "recommendations": [],
        "permissions": [],
        "access_claims": [],
    }


def _diagnostic(code: str, pointer: str, source_type: str) -> dict[str, str]:
    if code not in GROUNDING_VIOLATION_CODES:
        raise ValueError(f"unsupported diagnostic code: {code}")
    return {
        "code": code,
        "response_pointer": pointer,
        "expected_source_type": source_type,
    }


def _reference_diagnostics(
    actual: Any,
    expected: list[str],
    pointer: str,
    missing_code: str,
    unsupported_code: str,
    count_code: str | None,
    source_type: str,
) -> list[dict[str, str]]:
    if not isinstance(actual, list):
        return [_diagnostic("INVALID_STRUCTURE", pointer, source_type)]
    diagnostics: list[dict[str, str]] = []
    if len(actual) != len(set(item for item in actual if isinstance(item, str))):
        diagnostics.append(_diagnostic("DUPLICATE_REFERENCE", pointer, source_type))
    actual_set = set(item for item in actual if isinstance(item, str))
    expected_set = set(expected)
    if expected_set - actual_set:
        diagnostics.append(_diagnostic(missing_code, pointer, source_type))
    if actual_set - expected_set:
        diagnostics.append(_diagnostic(unsupported_code, pointer, source_type))
    if count_code and len(actual) != len(expected):
        diagnostics.append(_diagnostic(count_code, pointer, source_type))
    return diagnostics


def _failure_category(diagnostics: list[dict[str, str]]) -> str:
    codes = {item["code"] for item in diagnostics}
    if "AUTHORITY_CHANGED" in codes:
        return "authority_violation"
    if codes & {
        "ACTION_CONTENT_PRESENT",
        "RECOMMENDATION_CONTENT_PRESENT",
        "ACCESS_CLAIM_PRESENT",
        "PERMISSION_CLAIM_PRESENT",
        "RELATIONSHIP_UNSUPPORTED",
    }:
        return "capability_violation"
    if codes & {
        "UNKNOWN_RESPONSE_FIELD",
        "MISSING_REQUIRED_FIELD",
        "INVALID_ENUM_VALUE",
        "INVALID_STRUCTURE",
    }:
        return "schema_validation_failed"
    return "grounding_validation_failed"


def validate_grounding_response_v2(
    response: Any, request: dict[str, Any], context: dict[str, Any]
) -> dict[str, Any]:
    """Validate v2 and return structural diagnostics without rejected values."""

    vocabulary = build_response_vocabulary(context, request)
    schema = load_json(RESPONSE_V2_SCHEMA_PATH)
    diagnostics: list[dict[str, str]] = []
    if not isinstance(response, dict):
        diagnostics.append(_diagnostic("INVALID_STRUCTURE", "/", "response_contract"))
    else:
        missing = [key for key in V2_REQUIRED_FIELDS if key not in response]
        for key in missing:
            diagnostics.append(_diagnostic("MISSING_REQUIRED_FIELD", f"/{key}", "response_contract"))
        if set(response) - set(V2_REQUIRED_FIELDS):
            diagnostics.append(_diagnostic("UNKNOWN_RESPONSE_FIELD", "/", "closed_schema"))

        enum_expectations = {
            "schema_version": 2,
            "task": "explain",
            "confidence": vocabulary["confidence"],
            "authority": vocabulary["authority"],
            "review_state": vocabulary["review_state"],
            "action_authority": "none",
        }
        code_for = {
            "confidence": "CONFIDENCE_CHANGED",
            "authority": "AUTHORITY_CHANGED",
            "review_state": "REVIEW_STATE_CHANGED",
        }
        for field, expected in enum_expectations.items():
            if field in response and response[field] != expected:
                diagnostics.append(_diagnostic(
                    code_for.get(field, "INVALID_ENUM_VALUE"),
                    f"/{field}",
                    "enum",
                ))

        identity_expectations = {
            "response_id": build_ideal_response_v2(context, request)["response_id"],
            "request_id": request["request_id"],
            "context_id": context["context_id"],
            "subject_ref": vocabulary["subject_ref"],
        }
        for field, expected in identity_expectations.items():
            if field in response and response[field] != expected:
                diagnostics.append(_diagnostic("IDENTITY_MISMATCH", f"/{field}", "identity"))

        if "known_refs" in response:
            diagnostics.extend(_reference_diagnostics(
                response["known_refs"], vocabulary["known_refs"], "/known_refs",
                "KNOWN_CLAIM_MISSING", "KNOWN_CLAIM_UNSUPPORTED", None,
                "entity_summary",
            ))
        if "evidence_refs" in response:
            diagnostics.extend(_reference_diagnostics(
                response["evidence_refs"], vocabulary["evidence_refs"], "/evidence_refs",
                "EVIDENCE_CLAIM_MISSING", "EVIDENCE_CLAIM_UNSUPPORTED",
                "EVIDENCE_COUNT_MISMATCH", "evidence_summary",
            ))
        if "uncertainty_refs" in response:
            diagnostics.extend(_reference_diagnostics(
                response["uncertainty_refs"], vocabulary["uncertainty_refs"], "/uncertainty_refs",
                "UNCERTAINTY_MISSING", "UNCERTAINTY_UNSUPPORTED",
                "UNCERTAINTY_COUNT_MISMATCH", "uncertainty",
            ))

        if response.get("relationship_refs"):
            diagnostics.append(_diagnostic(
                "RELATIONSHIP_UNSUPPORTED", "/relationship_refs", "relationship_excluded"
            ))
        for field, code in (
            ("actions", "ACTION_CONTENT_PRESENT"),
            ("recommendations", "RECOMMENDATION_CONTENT_PRESENT"),
            ("permissions", "PERMISSION_CLAIM_PRESENT"),
            ("access_claims", "ACCESS_CLAIM_PRESENT"),
        ):
            if response.get(field):
                diagnostics.append(_diagnostic(code, f"/{field}", "empty_collection"))

        try:
            validate_schema(response, schema)
        except (SchemaValidationError, TypeError):
            if not diagnostics:
                diagnostics.append(_diagnostic("INVALID_STRUCTURE", "/", "response_contract"))

    unique = {
        (item["code"], item["response_pointer"], item["expected_source_type"]): item
        for item in diagnostics
    }
    ordered = [unique[key] for key in sorted(unique)]
    result = {
        "schema_version": 1,
        "accepted": not ordered,
        "failure_category": "none" if not ordered else _failure_category(ordered),
        "violations": ordered,
        "raw_response_retained": False,
        "hidden_reasoning_retained": False,
        "persisted": False,
    }
    validate_schema(result, load_json(DIAGNOSTIC_SCHEMA_PATH))
    return result


def render_validated_explanation_v2(
    response: dict[str, Any], request: dict[str, Any], context: dict[str, Any]
) -> str:
    """Render trusted prose exclusively from deterministic context lookups."""

    validation = validate_grounding_response_v2(response, request, context)
    if not validation["accepted"]:
        raise ValueError("only an accepted v2 response may be rendered")
    vocabulary = build_response_vocabulary(context, request)
    lines = [
        f"Subject: {context['entities'][0]['label']}",
        "Known:",
    ]
    lines.extend(f"- {vocabulary['_known'][ref]['summary']}" for ref in response["known_refs"])
    lines.append("Evidence:")
    lines.extend(
        f"- {vocabulary['_evidence'][ref]['claim']} "
        f"[{vocabulary['_evidence'][ref]['evidence_id']}; "
        f"confidence={vocabulary['_evidence'][ref]['confidence']}]"
        for ref in response["evidence_refs"]
    )
    lines.append("Uncertainty:")
    lines.extend(f"- {vocabulary['_uncertainties'][ref]}" for ref in response["uncertainty_refs"])
    lines.extend((
        f"Confidence: {response['confidence']}",
        f"Authority: {response['authority']}",
        f"Review state: {response['review_state']}",
        "Action authority: none",
    ))
    return "\n".join(lines)


def prompt_schema_consistency_errors() -> list[str]:
    schema = load_json(RESPONSE_V2_SCHEMA_PATH)
    errors: list[str] = []
    if tuple(schema.get("required", [])) != V2_REQUIRED_FIELDS:
        errors.append("v2 required fields disagree with contract metadata")
    joined = "\n".join(V2_OUTPUT_RULES)
    for field in CONTRACT_METADATA:
        if field == "contract_id":
            continue
        if f"{field}:" not in joined:
            errors.append(f"prompt omits {field} contract")
    for field in ("known_refs", "evidence_refs", "uncertainty_refs"):
        if schema["properties"][field].get("uniqueItems") is not True:
            errors.append(f"schema does not prohibit duplicate {field}")
    for field in ("relationship_refs", "actions", "recommendations", "permissions", "access_claims"):
        if schema["properties"][field].get("maxItems") != 0:
            errors.append(f"schema does not require empty {field}")
    return errors
