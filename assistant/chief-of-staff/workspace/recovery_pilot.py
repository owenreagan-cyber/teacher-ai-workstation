"""Pure Phase H recovery-candidate reasoning over approved evidence references."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path, PurePosixPath
from typing import Any

from pilot import APPROVED_OUTPUT_ROOT, PilotBoundaryError, enforce_output_root
from evidence_model import make_shared_evidence_package, shared_evidence_errors
from relationship_pilot import graph_errors, source_evidence_errors
from validate import SchemaValidationError, load_json, validate_schema
from validate_observation import audit_event_errors


ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "registry/pilots/recovery-intelligence-candidate-architecture.json"
POLICY_PATH = ROOT / "registry/recovery-policy.json"
CONFIG_SCHEMA_PATH = ROOT / "schemas/recovery-pilot.schema.json"
POLICY_SCHEMA_PATH = ROOT / "schemas/recovery-policy.schema.json"
SIGNAL_SCHEMA_PATH = ROOT / "schemas/missing-resource-signal.schema.json"
EVIDENCE_SCHEMA_PATH = ROOT / "schemas/recovery-evidence-package.schema.json"
CANDIDATE_SCHEMA_PATH = ROOT / "schemas/recovery-candidate.schema.json"
EXPLANATION_SCHEMA_PATH = ROOT / "schemas/recovery-explanation.schema.json"
RECOMMENDATION_SCHEMA_PATH = ROOT / "schemas/recovery-recommendation.schema.json"
CONFLICT_SCHEMA_PATH = ROOT / "schemas/recovery-conflict.schema.json"

CANDIDATE_TYPES = {
    "same_resource_candidate",
    "alternate_representation_candidate",
    "backup_candidate",
    "mirror_candidate",
    "archive_candidate",
    "previous_version_candidate",
    "unknown_candidate",
}
SIGNAL_TYPES = {
    "availability_changed",
    "relationship_changed",
    "authority_conflict",
    "representation_missing",
    "source_unavailable",
    "candidate_changed",
}
CONFIDENCE_LEVELS = {"high", "medium", "low", "unknown"}
RISK_LEVELS = {"low", "medium", "high", "unknown"}
AUDIT_EVENT_TYPES = {
    "recovery_candidate_created",
    "recovery_candidate_validated",
    "recovery_conflict_detected",
    "recovery_reviewed",
}
EXPECTED_EVIDENCE_INPUTS = {
    (
        "D",
        "run:history-project-metadata-pilot-20260913t004754454694z",
        "observations/run:history-project-metadata-pilot-20260913t004754454694z.json",
    ),
    (
        "E",
        "run:history-project-intelligence-pilot-20260913t010602083477z",
        "observations/run:history-project-intelligence-pilot-20260913t010602083477z-project.json",
    ),
    (
        "F",
        "run:grade-4-writing-application-pilot-20260913t012118468832z",
        "observations/run:grade-4-writing-application-pilot-20260913t012118468832z-application.json",
    ),
    (
        "G",
        "run:relationship-intelligence-pilot-20260913t020208966961z",
        "relationships/run:relationship-intelligence-pilot-20260913t020208966961z.json",
    ),
}
EXPECTED_SCENARIOS = {
    "missing_representation_with_relationship",
    "explicit_backup_candidate",
    "conflicting_candidates",
    "insufficient_evidence",
}


def recovery_config_errors(
    config: dict[str, Any], policy: dict[str, Any]
) -> list[str]:
    try:
        validate_schema(config, load_json(CONFIG_SCHEMA_PATH))
        validate_schema(policy, load_json(POLICY_SCHEMA_PATH))
    except (SchemaValidationError, TypeError) as exc:
        return [str(exc)]
    errors: list[str] = []
    inputs = {
        (item["phase"], item["run_id"], item["artifact_ref"])
        for item in config["evidence_inputs"]
    }
    if inputs != EXPECTED_EVIDENCE_INPUTS:
        errors.append("Phase H must name exactly the approved D/E/F/G artifacts")
    if set(config["synthetic_scenarios"]) != EXPECTED_SCENARIOS:
        errors.append("Phase H must contain exactly four approved synthetic scenarios")
    if any(config["prohibitions"].values()):
        errors.append("all Phase H prohibited capabilities must remain false")
    if any(
        config[key]
        for key in (
            "live_signal_detection_enabled",
            "live_candidate_generation_enabled",
            "host_local_output_enabled",
        )
    ):
        errors.append("Phase H cannot detect live signals, generate live candidates, or write output")
    if set(policy["candidate_types"]) != CANDIDATE_TYPES:
        errors.append("Phase H recovery candidate type set is incomplete")
    if set(policy["signal_types"]) != SIGNAL_TYPES:
        errors.append("Phase H signal type set is incomplete")
    if set(policy["confidence_levels"]) != CONFIDENCE_LEVELS:
        errors.append("Phase H confidence type set is incomplete")
    if set(policy["risk_levels"]) != RISK_LEVELS:
        errors.append("Phase H recovery risk type set is incomplete")
    if set(policy["audit_event_types"]) != AUDIT_EVENT_TYPES:
        errors.append("Phase H audit event type set is incomplete")
    if any(
        policy[key]
        for key in (
            "automatic_candidate_discovery",
            "automatic_winner_selection",
            "automatic_authority_promotion",
            "recovery_execution_enabled",
        )
    ):
        errors.append("Phase H automatic discovery, decisions, authority, and execution are forbidden")
    if not policy["shared_evidence_required"] or not policy["recovery_explanation_required"]:
        errors.append("Phase H shared evidence and recovery explanations are required")
    if policy["expected_artifact_existence_implied"]:
        errors.append("expected artifact relationships cannot imply current existence")
    return errors


def load_recovery_configuration() -> tuple[dict[str, Any], dict[str, Any]]:
    config = load_json(CONFIG_PATH)
    policy = load_json(POLICY_PATH)
    errors = recovery_config_errors(config, policy)
    if errors:
        raise PilotBoundaryError(errors[0])
    return config, policy


def resolve_recovery_evidence_artifact(artifact_ref: str) -> Path:
    relative = PurePosixPath(artifact_ref)
    if relative.is_absolute() or ".." in relative.parts:
        raise PilotBoundaryError("recovery evidence path traversal is forbidden")
    if len(relative.parts) != 2 or relative.parts[0] not in {"observations", "relationships"}:
        raise PilotBoundaryError("recovery evidence must be an explicit observation or relationship artifact")
    output_root = enforce_output_root(APPROVED_OUTPUT_ROOT, APPROVED_OUTPUT_ROOT)
    candidate = output_root.joinpath(*relative.parts)
    if candidate.is_symlink():
        raise PilotBoundaryError("recovery evidence cannot be a symlink")
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(output_root)
    except (OSError, ValueError) as exc:
        raise PilotBoundaryError("approved recovery evidence artifact is unavailable") from exc
    if not resolved.is_file():
        raise PilotBoundaryError("recovery evidence must be a regular file")
    return resolved


def load_recovery_evidence_inputs(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    inputs: dict[str, dict[str, Any]] = {}
    for item in config["evidence_inputs"]:
        artifact = load_json(resolve_recovery_evidence_artifact(item["artifact_ref"]))
        if artifact.get("run_id") != item["run_id"]:
            raise PilotBoundaryError(f"Phase {item['phase']} recovery evidence provenance mismatch")
        inputs[item["phase"]] = artifact
    if set(inputs) != {"D", "E", "F", "G"}:
        raise PilotBoundaryError("recovery evidence input set is incomplete")
    return inputs


def recovery_source_evidence_errors(inputs: dict[str, dict[str, Any]]) -> list[str]:
    errors = source_evidence_errors({phase: inputs[phase] for phase in ("D", "E", "F")})
    errors.extend(graph_errors(inputs["G"]))
    return errors


def signal_errors(value: dict[str, Any]) -> list[str]:
    try:
        validate_schema(value, load_json(SIGNAL_SCHEMA_PATH))
    except (SchemaValidationError, TypeError) as exc:
        return [str(exc)]
    return []


def recovery_evidence_errors(value: dict[str, Any]) -> list[str]:
    try:
        validate_schema(value, load_json(EVIDENCE_SCHEMA_PATH))
    except (SchemaValidationError, TypeError) as exc:
        return [str(exc)]
    assessed = assess_recovery_confidence(value["evidence"])
    if value["confidence"] != assessed:
        return ["recovery evidence confidence does not match deterministic assessment"]
    if value["authority_effect"] != "none":
        return ["recovery evidence cannot create authority"]
    shared_errors = shared_evidence_errors(value["shared_evidence_package"])
    if shared_errors:
        return shared_errors
    shared = value["shared_evidence_package"]
    if (
        shared["subject_ref"] != value["subject"]
        or shared["claim"] != value["finding"]
        or shared["confidence"] != value["confidence"]
        or shared["review_state"] != value["review_state"]
    ):
        return ["shared evidence package does not preserve recovery evidence semantics"]
    return []


def recovery_recommendation_errors(value: dict[str, Any]) -> list[str]:
    try:
        validate_schema(value, load_json(RECOMMENDATION_SCHEMA_PATH))
    except (SchemaValidationError, TypeError) as exc:
        return [str(exc)]
    return []


def recovery_conflict_errors(value: dict[str, Any]) -> list[str]:
    try:
        validate_schema(value, load_json(CONFLICT_SCHEMA_PATH))
    except (SchemaValidationError, TypeError) as exc:
        return [str(exc)]
    return []


def assess_recovery_confidence(evidence: list[dict[str, Any]]) -> str:
    if not evidence:
        return "unknown"
    evidence_types = {item["type"] for item in evidence}
    if evidence_types <= {"filename_similarity", "structural_evidence"}:
        return "low"
    for item in evidence:
        detail = item["detail"].lower()
        if item["type"] in {"resource_registry_metadata", "knowledge_vault_reference"}:
            return "high"
        if item["type"] == "authority_assertion" and any(
            token in detail for token in ("role=backup", "role=mirror", "role=archive", "explicit authority")
        ):
            return "high"
        if item["type"] == "relationship" and any(
            token in detail for token in ("representation_of", "backed_up_by", "mirrored_to")
        ):
            return "high"
    if any(
        item["type"] in {"project_observation", "application_observation"}
        or (
            item["type"] == "relationship"
            and any(
                token in item["detail"].lower()
                for token in ("belongs_to_project", "deployed_to", "version_of", "used_by_application")
            )
        )
        for item in evidence
    ):
        return "medium"
    return "unknown"


def make_signal(
    signal_id: str,
    subject_ref: str,
    signal_type: str,
    previous_state: str,
    current_state: str,
    evidence: list[str],
    confidence: str,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "signal_id": signal_id,
        "subject_ref": subject_ref,
        "signal_type": signal_type,
        "previous_state": previous_state,
        "current_state": current_state,
        "evidence": evidence,
        "confidence": confidence,
        "review_state": "unreviewed",
        "interpretation": "review_opportunity_not_failure",
        "source_mode": "synthetic_only",
    }


def make_recovery_evidence_package(
    package_id: str,
    subject_ref: str,
    candidate_ref: str,
    finding: str,
    evidence: list[dict[str, Any]],
    unknowns: list[str],
    alternatives: list[str] | None = None,
) -> dict[str, Any]:
    relationship_refs = [item["source"] for item in evidence if item["type"] == "relationship"]
    observation_refs = [item["source"] for item in evidence if item["type"] != "relationship"]
    authority_role = "unknown"
    authority_scope = "unknown"
    authority_basis = "unknown"
    for item in evidence:
        detail = item["detail"].lower()
        if item["type"] == "authority_assertion":
            authority_basis = item["source"]
            for role in ("backup", "mirror", "archive", "canonical", "deployment"):
                if f"role={role}" in detail:
                    authority_role = role
                    break
            if "scope=backup_recovery" in detail:
                authority_scope = "backup_recovery"
    confidence = assess_recovery_confidence(evidence)
    shared = make_shared_evidence_package(
        package_id.replace("recovery-evidence:", "evidence-package:recovery:"),
        "recovery",
        subject_ref,
        finding,
        observations=observation_refs,
        relationships=relationship_refs,
        authority_role=authority_role,
        authority_scope=authority_scope,
        authority_basis=authority_basis,
        confidence=confidence,
        alternatives=alternatives or [],
    )
    return {
        "schema_version": 1,
        "package_id": package_id,
        "shared_evidence_package": shared,
        "finding": finding,
        "subject": subject_ref,
        "candidate": candidate_ref,
        "evidence": evidence,
        "confidence": confidence,
        "unknowns": unknowns,
        "alternatives": alternatives or [],
        "recommended_next_step": "review_candidate",
        "review_state": "unreviewed",
        "authority_effect": "none",
    }


def make_recovery_candidate(
    candidate_id: str,
    subject_ref: str,
    candidate_ref: str,
    candidate_type: str,
    package: dict[str, Any],
    *,
    authority_role: str = "unknown",
    authority_scope: str = "unknown",
    authority_basis: str = "unreviewed_evidence",
    risk_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    context = risk_context or {
        "authority_ambiguity": True,
        "candidate_age": "unknown",
        "sensitivity": "unknown",
        "provenance_complete": True,
        "conflicting_relationships": False,
        "scope_uncertainty": True,
    }
    recovery_risk, risk_basis = assess_recovery_risk(context)
    explanation = {
        "candidate": candidate_ref,
        "why_found": [package["finding"]],
        "supporting_evidence": [item["detail"] for item in package["evidence"]],
        "unknowns": package["unknowns"],
        "recommended_next_step": "review_candidate",
        "action_state": "not_an_action",
    }
    return {
        "schema_version": 1,
        "candidate_id": candidate_id,
        "subject_ref": subject_ref,
        "candidate_ref": candidate_ref,
        "candidate_type": candidate_type,
        "evidence_package": {
            "package_id": package["package_id"],
            "evidence_refs": [item["source"] for item in package["evidence"]],
        },
        "confidence": package["confidence"],
        "recovery_risk": recovery_risk,
        "risk_basis": risk_basis,
        "risk_context": context,
        "authority_context": {
            "role": authority_role,
            "scope": authority_scope,
            "basis": authority_basis,
            "canonical_promotion": False,
        },
        "explanation": explanation,
        "recommended_next_step": "review_candidate",
        "review_state": "unreviewed",
        "action_state": "not_an_action",
        "authority_effect": "none",
    }


def recovery_candidate_errors(
    value: dict[str, Any], packages: dict[str, dict[str, Any]]
) -> list[str]:
    try:
        validate_schema(value, load_json(CANDIDATE_SCHEMA_PATH))
    except (SchemaValidationError, TypeError) as exc:
        return [str(exc)]
    errors: list[str] = []
    if not value["candidate_ref"].startswith("representation:"):
        errors.append("recovery candidate must identify a representation")
    expected_risk, expected_basis = assess_recovery_risk(value["risk_context"])
    if value["recovery_risk"] != expected_risk or value["risk_basis"] != expected_basis:
        errors.append("recovery risk does not match deterministic assessment")
    try:
        validate_schema(value["explanation"], load_json(EXPLANATION_SCHEMA_PATH))
    except (SchemaValidationError, TypeError) as exc:
        errors.append(str(exc))
    if value["explanation"].get("candidate") != value["candidate_ref"]:
        errors.append("recovery explanation candidate does not match")
    package = packages.get(value["evidence_package"]["package_id"])
    if package is None:
        errors.append("recovery candidate evidence package does not resolve")
    else:
        errors.extend(recovery_evidence_errors(package))
        if package.get("subject") != value["subject_ref"] or package.get("candidate") != value["candidate_ref"]:
            errors.append("recovery evidence subject or candidate does not match")
        if package.get("confidence") != value["confidence"]:
            errors.append("recovery candidate confidence does not match evidence")
        shared_context = package.get("shared_evidence_package", {}).get("authority_context", {})
        for key in ("role", "scope"):
            claimed = value["authority_context"][key]
            evidenced = shared_context.get(key, "unknown")
            if claimed != "unknown" and claimed != evidenced:
                errors.append(f"candidate authority {key} is not supported by shared evidence")
    context = value["authority_context"]
    candidate_type = value["candidate_type"]
    if candidate_type == "backup_candidate" and (
        context["role"] != "backup" or context["scope"] != "backup_recovery"
    ):
        errors.append("backup candidate must retain backup/backup_recovery authority context")
    if candidate_type == "mirror_candidate" and context["role"] != "mirror":
        errors.append("mirror candidate must retain mirror authority context")
    if candidate_type == "archive_candidate" and context["role"] != "archive":
        errors.append("archive candidate must retain archive authority context")
    if context["role"] == "canonical" and context["basis"] == "timestamp":
        errors.append("timestamp cannot establish canonical authority")
    return errors


def assess_recovery_risk(context: dict[str, Any]) -> tuple[str, list[str]]:
    basis: list[str] = []
    sensitivity = context["sensitivity"]
    if sensitivity in {"student_private", "restricted"}:
        basis.append(f"sensitivity:{sensitivity}")
    if context["conflicting_relationships"]:
        basis.append("conflicting_relationships")
    if not context["provenance_complete"]:
        basis.append("missing_provenance")
    if basis:
        return "high", basis
    if sensitivity == "unknown" and context["candidate_age"] == "unknown":
        return "unknown", ["risk_context_insufficient"]
    if context["authority_ambiguity"]:
        basis.append("authority_ambiguity")
    if context["candidate_age"] in {"old", "unknown"}:
        basis.append(f"candidate_age:{context['candidate_age']}")
    if context["scope_uncertainty"]:
        basis.append("scope_uncertainty")
    if sensitivity == "unknown":
        basis.append("sensitivity:unknown")
    if basis:
        return "medium", basis
    return "low", ["authority_scope_provenance_and_sensitivity_resolved"]


def make_recovery_recommendation(
    recommendation_id: str,
    candidate: dict[str, Any],
    finding: str,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "recommendation_id": recommendation_id,
        "subject_ref": candidate["subject_ref"],
        "candidate_ref": candidate["candidate_ref"],
        "finding": finding,
        "confidence": candidate["confidence"],
        "next_step": "review_candidate",
        "review_state": "unreviewed",
        "action_state": "not_an_action",
        "authority_effect": "none",
    }


def detect_recovery_conflicts(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for candidate in candidates:
        grouped[candidate["subject_ref"]].append(candidate)
    conflicts: list[dict[str, Any]] = []
    for index, (subject_ref, competing) in enumerate(sorted(grouped.items()), start=1):
        if len({item["candidate_ref"] for item in competing}) < 2:
            continue
        conflicts.append(
            {
                "schema_version": 1,
                "conflict_id": f"recovery-conflict:synthetic-{index:04d}",
                "subject_ref": subject_ref,
                "competing_candidate_ids": sorted(item["candidate_id"] for item in competing),
                "evidence_package_ids": sorted(item["evidence_package"]["package_id"] for item in competing),
                "resolution_state": "unresolved",
                "review_state": "unreviewed",
                "automatic_winner": False,
                "action_state": "not_an_action",
                "authority_effect": "none",
            }
        )
    return conflicts


def recovery_audit_event(
    event_id: str,
    event_type: str,
    target_ref: str,
    *,
    actor: str = "system:recovery-intelligence-pilot",
) -> dict[str, Any]:
    if event_type not in AUDIT_EVENT_TYPES:
        raise PilotBoundaryError("unsupported recovery audit event type")
    return {
        "schema_version": 1,
        "event_id": event_id,
        "event_type": event_type,
        "timestamp": "2026-09-12T12:00:00Z",
        "actor": actor,
        "target_ref": target_ref,
        "evidence": {
            "refs": [target_ref],
            "summary": f"Synthetic Phase H {event_type.replace('_', ' ')} without recovery action.",
        },
        "result": "passed" if event_type == "recovery_candidate_validated" else "recorded",
    }


def _scenario_result(
    scenario_id: str,
    signal: dict[str, Any],
    candidates: list[dict[str, Any]],
    packages: list[dict[str, Any]],
    recommendations: list[dict[str, Any]],
) -> dict[str, Any]:
    conflicts = detect_recovery_conflicts(candidates)
    events: list[dict[str, Any]] = []
    for index, candidate in enumerate(candidates, start=1):
        events.append(recovery_audit_event(f"audit:recovery-{scenario_id}-{index:02d}-created", "recovery_candidate_created", candidate["candidate_id"]))
        events.append(recovery_audit_event(f"audit:recovery-{scenario_id}-{index:02d}-validated", "recovery_candidate_validated", candidate["candidate_id"]))
    for index, conflict in enumerate(conflicts, start=1):
        events.append(recovery_audit_event(f"audit:recovery-{scenario_id}-{index:02d}-conflict", "recovery_conflict_detected", conflict["conflict_id"]))
    return {
        "scenario_id": scenario_id,
        "signal": signal,
        "candidates": candidates,
        "evidence_packages": packages,
        "recommendations": recommendations,
        "conflicts": conflicts,
        "audit_events": events,
    }


def build_synthetic_scenarios(inputs: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    relationship = next(
        item
        for item in inputs["G"]["relationships"]
        if item["source_ref"] == "representation:grade-4-writing:installed-bundle"
        and item["relationship_type"] == "representation_of"
    )
    writing_subject = relationship["target_ref"]
    writing_candidate_ref = relationship["source_ref"]
    signal_one = make_signal(
        "recovery-signal:synthetic-missing-representation",
        writing_subject,
        "representation_missing",
        "representation_known",
        "representation_not_observed_hypothesis",
        [relationship["relationship_id"]],
        "unknown",
    )
    package_one = make_recovery_evidence_package(
        "recovery-evidence:synthetic-writing-representation",
        writing_subject,
        writing_candidate_ref,
        "Existing relationship evidence suggests a possible representation.",
        [{"type": "relationship", "source": relationship["relationship_id"], "detail": "representation_of connects candidate representation to subject application instance", "strength": "high"}],
        ["The missing state is hypothetical and has not been detected.", "Candidate availability has not been re-observed."],
    )
    candidate_one = make_recovery_candidate(
        "recovery-candidate:synthetic-writing-representation",
        writing_subject,
        writing_candidate_ref,
        "alternate_representation_candidate",
        package_one,
        risk_context={
            "authority_ambiguity": True,
            "candidate_age": "unknown",
            "sensitivity": "teacher_internal",
            "provenance_complete": True,
            "conflicting_relationships": False,
            "scope_uncertainty": True,
        },
    )
    recommendation_one = make_recovery_recommendation(
        "recovery-recommendation:synthetic-writing-representation",
        candidate_one,
        "Review the evidence-backed representation candidate.",
    )

    backup_subject = "logical-resource:synthetic-teacher-resource"
    backup_ref = "representation:synthetic:backup-copy"
    signal_two = make_signal(
        "recovery-signal:synthetic-backup",
        backup_subject,
        "source_unavailable",
        "source_available",
        "source_unavailable_hypothesis",
        ["authority-assertion:synthetic-backup"],
        "unknown",
    )
    package_two = make_recovery_evidence_package(
        "recovery-evidence:synthetic-backup",
        backup_subject,
        backup_ref,
        "A fictional explicit backup declaration supports a backup candidate.",
        [{"type": "authority_assertion", "source": "authority-assertion:synthetic-backup", "detail": "role=backup scope=backup_recovery explicit declaration", "strength": "high"}],
        ["The backup has not been scanned or compared.", "Canonical authority remains unknown."],
    )
    candidate_two = make_recovery_candidate(
        "recovery-candidate:synthetic-backup",
        backup_subject,
        backup_ref,
        "backup_candidate",
        package_two,
        authority_role="backup",
        authority_scope="backup_recovery",
        authority_basis="explicit_synthetic_backup_declaration",
        risk_context={
            "authority_ambiguity": True,
            "candidate_age": "unknown",
            "sensitivity": "teacher_internal",
            "provenance_complete": True,
            "conflicting_relationships": False,
            "scope_uncertainty": False,
        },
    )
    recommendation_two = make_recovery_recommendation(
        "recovery-recommendation:synthetic-backup",
        candidate_two,
        "Review the declared backup candidate without restoring it.",
    )

    conflict_subject = "logical-resource:synthetic-conflicting-resource"
    signal_three = make_signal(
        "recovery-signal:synthetic-authority-conflict",
        conflict_subject,
        "authority_conflict",
        "one_candidate_expected",
        "two_candidates_asserted",
        ["authority-assertion:synthetic-mirror", "authority-assertion:synthetic-archive"],
        "unknown",
    )
    conflict_specs = [
        ("mirror", "mirror_candidate", "representation:synthetic:mirror-copy", "role=mirror scope=backup_recovery explicit declaration"),
        ("archive", "archive_candidate", "representation:synthetic:archive-copy", "role=archive scope=backup_recovery explicit declaration"),
    ]
    conflict_packages: list[dict[str, Any]] = []
    conflict_candidates: list[dict[str, Any]] = []
    conflict_recommendations: list[dict[str, Any]] = []
    for role, candidate_type, candidate_ref, detail in conflict_specs:
        package = make_recovery_evidence_package(
            f"recovery-evidence:synthetic-conflict-{role}",
            conflict_subject,
            candidate_ref,
            f"A fictional explicit {role} declaration supports a candidate.",
            [{"type": "authority_assertion", "source": f"authority-assertion:synthetic-{role}", "detail": detail, "strength": "high"}],
            ["The candidates have not been compared.", "No winning recovery path has been selected."],
            [item[2] for item in conflict_specs if item[2] != candidate_ref],
        )
        candidate = make_recovery_candidate(
            f"recovery-candidate:synthetic-conflict-{role}",
            conflict_subject,
            candidate_ref,
            candidate_type,
            package,
            authority_role=role,
            authority_scope="backup_recovery",
            authority_basis=f"explicit_synthetic_{role}_declaration",
            risk_context={
                "authority_ambiguity": True,
                "candidate_age": "unknown",
                "sensitivity": "teacher_internal",
                "provenance_complete": True,
                "conflicting_relationships": True,
                "scope_uncertainty": False,
            },
        )
        conflict_packages.append(package)
        conflict_candidates.append(candidate)
        conflict_recommendations.append(
            make_recovery_recommendation(
                f"recovery-recommendation:synthetic-conflict-{role}",
                candidate,
                "Review competing evidence; do not select or restore automatically.",
            )
        )

    signal_four = make_signal(
        "recovery-signal:synthetic-insufficient-evidence",
        "logical-resource:synthetic-unknown-resource",
        "availability_changed",
        "unknown",
        "unknown",
        [],
        "unknown",
    )
    return [
        _scenario_result("missing-representation", signal_one, [candidate_one], [package_one], [recommendation_one]),
        _scenario_result("backup-candidate", signal_two, [candidate_two], [package_two], [recommendation_two]),
        _scenario_result("conflicting-candidates", signal_three, conflict_candidates, conflict_packages, conflict_recommendations),
        _scenario_result("insufficient-evidence", signal_four, [], [], []),
    ]


def synthetic_scenario_errors(scenarios: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    if len(scenarios) != 4:
        errors.append("exactly four synthetic recovery scenarios are required")
    for scenario in scenarios:
        errors.extend(signal_errors(scenario["signal"]))
        packages = {item["package_id"]: item for item in scenario["evidence_packages"]}
        for package in packages.values():
            errors.extend(recovery_evidence_errors(package))
        for candidate in scenario["candidates"]:
            errors.extend(recovery_candidate_errors(candidate, packages))
        for recommendation in scenario["recommendations"]:
            errors.extend(recovery_recommendation_errors(recommendation))
        for conflict in scenario["conflicts"]:
            errors.extend(recovery_conflict_errors(conflict))
        for event in scenario["audit_events"]:
            errors.extend(audit_event_errors(event))
    no_evidence = next(item for item in scenarios if item["scenario_id"] == "insufficient-evidence")
    if no_evidence["candidates"] or no_evidence["recommendations"]:
        errors.append("insufficient evidence must create no candidate or recommendation")
    conflict = next(item for item in scenarios if item["scenario_id"] == "conflicting-candidates")
    if len(conflict["conflicts"]) != 1 or conflict["conflicts"][0]["automatic_winner"]:
        errors.append("competing recovery candidates must remain unresolved")
    return errors
