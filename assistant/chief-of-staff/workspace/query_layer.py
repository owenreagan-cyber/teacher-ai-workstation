"""Deterministic Phase J query and explanation layer over fixed approved inputs."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from pilot import PilotBoundaryError, utc_now
from recovery_pilot import (
    EXPECTED_EVIDENCE_INPUTS,
    load_recovery_evidence_inputs,
    recovery_source_evidence_errors,
)
from validate import SchemaValidationError, load_json, validate_schema


ROOT = Path(__file__).resolve().parent
POLICY_PATH = ROOT / "registry/query-policy.json"
POLICY_SCHEMA_PATH = ROOT / "schemas/query-policy.schema.json"
QUERY_SCHEMA_PATH = ROOT / "schemas/query.schema.json"
EXPLANATION_SCHEMA_PATH = ROOT / "schemas/explanation.schema.json"
RESPONSE_SCHEMA_PATH = ROOT / "schemas/query-response.schema.json"
UNCERTAINTY_SCHEMA_PATH = ROOT / "schemas/uncertainty-item.schema.json"

QUERY_TYPES = {
    "entity_lookup",
    "relationship_lookup",
    "evidence_lookup",
    "recovery_candidate_lookup",
    "project_lookup",
    "application_lookup",
    "resource_lookup",
}
SCOPES = {
    "active",
    "classroom_ready",
    "teacher_only",
    "student_safe",
    "restricted",
    "superseded",
    "all",
    "unreviewed",
    "conflicts",
}
REGISTRY_INPUTS = {"registry/projects.json", "registry/applications.json"}
REGISTRY_SCHEMAS = {
    "registry/projects.json": "schemas/project.schema.json",
    "registry/applications.json": "schemas/application.schema.json",
}
NODE_TYPE_MAP = {
    "Workspace": "workspace",
    "StorageSource": "storage_source",
    "WorkspaceItem": "workspace_item",
    "LogicalResource": "logical_resource",
    "Representation": "representation",
    "Project": "project",
    "ApplicationConcept": "application",
    "ApplicationInstance": "application",
    "Workflow": "workflow",
    "RegistryEntry": "registry_entry",
    "Observation": "workspace_item",
    "Recommendation": "recommendation",
}
RESOURCE_ENTITY_TYPES = {"logical_resource", "representation", "registry_entry"}
REVIEW_STATES = {
    "unreviewed": "unreviewed",
    "reviewed": "reviewed",
    "approved": "approved",
    "rejected": "rejected",
    "deferred": "deferred",
}
CONFIDENCE_ORDER = {"high": 0, "medium": 1, "low": 2, "unknown": 3}


class QueryValidationError(ValueError):
    """Raised when a query or its fixed source configuration is invalid."""


class QuerySecurityError(PermissionError):
    """Raised when a restricted query lacks its explicit permission grant."""


def query_policy_errors(policy: dict[str, Any]) -> list[str]:
    try:
        validate_schema(policy, load_json(POLICY_SCHEMA_PATH))
    except (SchemaValidationError, TypeError) as exc:
        return [str(exc)]
    errors: list[str] = []
    if set(policy["query_types"]) != QUERY_TYPES:
        errors.append("Phase J query type set is incomplete")
    if set(policy["scopes"]) != SCOPES:
        errors.append("Phase J scope set is incomplete")
    if set(policy["registry_inputs"]) != REGISTRY_INPUTS:
        errors.append("Phase J must name exactly the two approved static registries")
    inputs = {
        (item["phase"], item["run_id"], item["artifact_ref"])
        for item in policy["evidence_inputs"]
    }
    if inputs != EXPECTED_EVIDENCE_INPUTS:
        errors.append("Phase J must name exactly the approved D/E/F/G artifacts")
    if not all(
        policy[key]
        for key in ("deterministic_ordering", "unknown_preserved", "uncertainty_visible")
    ):
        errors.append("Phase J ordering, unknown preservation, and uncertainty visibility are required")
    if policy["live_recovery_candidates_enabled"] or policy["ai_enabled"]:
        errors.append("Phase J live recovery and AI must remain disabled")
    if policy["action_capabilities"]:
        errors.append("Phase J cannot expose action capabilities")
    return errors


def load_query_policy() -> dict[str, Any]:
    policy = load_json(POLICY_PATH)
    errors = query_policy_errors(policy)
    if errors:
        raise QueryValidationError(errors[0])
    return policy


def make_query(
    query_type: str,
    target_ref: str = "",
    *,
    scope: str = "all",
    filters: dict[str, str] | None = None,
    permission_grants: list[str] | None = None,
    query_id: str | None = None,
    created_at: str | None = None,
) -> dict[str, Any]:
    normalized_target = "".join(
        character if character.isalnum() or character in "._:-" else "-"
        for character in target_ref.lower()
    ).strip("-") or "all"
    return {
        "schema_version": 1,
        "query_id": query_id or f"query:{query_type}:{normalized_target}",
        "query_type": query_type,
        "target_ref": target_ref,
        "filters": filters or {},
        "scope": scope,
        "permission_grants": sorted(set(permission_grants or [])),
        "created_at": created_at or utc_now(),
    }


def query_errors(query: dict[str, Any]) -> list[str]:
    try:
        validate_schema(query, load_json(QUERY_SCHEMA_PATH))
    except (SchemaValidationError, TypeError) as exc:
        return [str(exc)]
    return []


def explanation_errors(explanation: dict[str, Any]) -> list[str]:
    try:
        validate_schema(explanation, load_json(EXPLANATION_SCHEMA_PATH))
    except (SchemaValidationError, TypeError) as exc:
        return [str(exc)]
    if explanation["action_authority"] != "none":
        return ["explanations cannot grant action authority"]
    return []


def response_errors(response: dict[str, Any]) -> list[str]:
    try:
        validate_schema(response, load_json(RESPONSE_SCHEMA_PATH))
    except (SchemaValidationError, TypeError) as exc:
        return [str(exc)]
    if response["authority_effect"] != "none" or response["action_authority"] != "none":
        return ["query responses cannot create authority or expose actions"]
    return []


def uncertainty_errors(item: dict[str, Any]) -> list[str]:
    try:
        validate_schema(item, load_json(UNCERTAINTY_SCHEMA_PATH))
    except (SchemaValidationError, TypeError) as exc:
        return [str(exc)]
    return []


def _authority_context(
    role: str = "unknown", scope: str = "unknown", basis: str = "unknown"
) -> dict[str, str]:
    return {"role": role, "scope": scope, "basis": basis}


def _entity(
    entity_id: str,
    label: str,
    entity_type: str,
    *,
    summary: str,
    sources: list[str],
    evidence_package_ids: list[str] | None = None,
    status: str = "unknown",
    classification: str = "unknown",
    confidence: str = "unknown",
    review_state: str = "unreviewed",
    authority_context: dict[str, str] | None = None,
    scope_tags: list[str] | None = None,
    uncertainties: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "entity_id": entity_id,
        "label": label,
        "type": entity_type,
        "summary": summary,
        "sources": sorted(set(sources)),
        "evidence_package_ids": sorted(set(evidence_package_ids or [])),
        "status": status,
        "classification": classification,
        "confidence": confidence,
        "review_state": REVIEW_STATES.get(review_state, review_state),
        "authority_context": authority_context or _authority_context(),
        "scope_tags": sorted(set(scope_tags or [])),
        "uncertainties": sorted(set(uncertainties or [])),
    }


def _direct_evidence(
    package_id: str,
    subject_ref: str,
    claim: str,
    sources: list[str],
    *,
    provenance: list[str],
    confidence: str,
    review_state: str,
    evidence_type: str,
) -> dict[str, Any]:
    return {
        "package_id": package_id,
        "subject_ref": subject_ref,
        "claim": claim,
        "sources": sorted(set(sources)),
        "provenance": sorted(set(provenance)),
        "confidence": confidence,
        "review_state": REVIEW_STATES.get(review_state, review_state),
        "evidence_type": evidence_type,
        "authority_effect": "none",
        "action_authority": "none",
    }


def _merge_entity(existing: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(existing)
    for key in ("sources", "evidence_package_ids", "scope_tags", "uncertainties"):
        merged[key] = sorted(set(existing.get(key, [])) | set(incoming.get(key, [])))
    for key in ("label", "summary", "status", "classification", "review_state"):
        if incoming.get(key) not in {None, "", "unknown", "unreviewed"}:
            merged[key] = incoming[key]
    merged["confidence"] = min(
        (existing["confidence"], incoming["confidence"]),
        key=lambda value: CONFIDENCE_ORDER[value],
    )
    if incoming.get("authority_context", {}).get("role") != "unknown":
        merged["authority_context"] = incoming["authority_context"]
    return merged


def build_query_model(
    policy: dict[str, Any],
    registries: dict[str, dict[str, Any]],
    inputs: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    graph = inputs["G"]
    entities: dict[str, dict[str, Any]] = {}
    evidence_packages: dict[str, dict[str, Any]] = {}

    graph_source = "phase:G:relationship-graph"
    for node in graph["nodes"]:
        node_type = NODE_TYPE_MAP[node["node_type"]]
        uncertainty = []
        if node["authority_claim"] == "none":
            uncertainty.append("Authority is unknown; relationship evidence does not create authority.")
        if node["review_state"] == "unreviewed":
            uncertainty.append("The supporting relationship evidence is unreviewed.")
        entities[node["node_id"]] = _entity(
            node["node_id"],
            node["label"],
            node_type,
            summary=f"{node['label']} represented in the approved Phase G relationship graph.",
            sources=[graph_source],
            status="unknown",
            confidence="high" if node["evidence_refs"] else "unknown",
            review_state=node["review_state"],
            uncertainties=uncertainty,
        )

    for project in registries["registry/projects.json"]["projects"]:
        entity_id = f"project:{project['id']}"
        assertion = project["authority_assertions"][0] if project["authority_assertions"] else {}
        review_state = REVIEW_STATES.get(project["review_state"], project["review_state"])
        package_id = f"evidence:project-registry:{project['id']}"
        uncertainty = []
        if review_state == "unreviewed":
            uncertainty.append("The static project declaration is unreviewed.")
        if project["status"] == "unknown":
            uncertainty.append("Current project status remains unknown.")
        incoming = _entity(
            entity_id,
            project["display_name"],
            "project",
            summary=f"{project['display_name']} project declared by the approved static project registry.",
            sources=["registry:projects"],
            evidence_package_ids=[package_id],
            status=project["status"],
            classification="unknown",
            confidence="high" if project["status_basis"]["owner_confirmed"] else "medium",
            review_state=review_state,
            authority_context=_authority_context(
                assertion.get("authority_role", "unknown"),
                assertion.get("authority_scope", "unknown"),
                assertion.get("basis", "unknown"),
            ),
            uncertainties=uncertainty,
        )
        entities[entity_id] = _merge_entity(entities[entity_id], incoming) if entity_id in entities else incoming
        evidence_packages[package_id] = _direct_evidence(
            package_id,
            entity_id,
            f"The approved static registry declares {project['display_name']} as a project.",
            ["registry:projects"],
            provenance=[project["status_basis"]["rule_id"]],
            confidence=incoming["confidence"],
            review_state=review_state,
            evidence_type="project",
        )

    for application in registries["registry/applications.json"]["concepts"]:
        entity_id = f"application-concept:{application['concept_id']}"
        package_id = f"evidence:application-registry:{application['concept_id']}"
        incoming = _entity(
            entity_id,
            application["display_name"],
            "application",
            summary=f"{application['display_name']} application concept declared by the approved static application registry.",
            sources=["registry:applications"],
            evidence_package_ids=[package_id],
            status="unknown",
            classification=application["data_classification"],
            confidence="medium",
            review_state="unreviewed",
            scope_tags=["teacher_only"],
            uncertainties=[
                "Application authority is not asserted by the static application registry.",
                "The application declaration has not been runtime-verified by Phase J.",
            ],
        )
        entities[entity_id] = _merge_entity(entities[entity_id], incoming) if entity_id in entities else incoming
        evidence_packages[package_id] = _direct_evidence(
            package_id,
            entity_id,
            f"The approved static registry declares {application['display_name']} as an application concept.",
            ["registry:applications"],
            provenance=["phase_b_static_policy"],
            confidence="medium",
            review_state="unreviewed",
            evidence_type="application",
        )

    phase_subjects = {
        "D": "project:history",
        "E": "project:history",
        "F": "application-concept:grade-4-writing-launcher",
    }
    for phase, subject_ref in phase_subjects.items():
        package_id = f"evidence:phase-{phase.lower()}:{subject_ref}"
        source_ref = f"phase:{phase}:approved-observation"
        claim = {
            "D": "A bounded History root metadata observation exists.",
            "E": "A bounded History project intelligence observation exists.",
            "F": "A bounded Grade 4 Writing application metadata observation exists.",
        }[phase]
        evidence_packages[package_id] = _direct_evidence(
            package_id,
            subject_ref,
            claim,
            [source_ref],
            provenance=[f"run:{inputs[phase]['run_id'].removeprefix('run:')}"] ,
            confidence="high",
            review_state="unreviewed",
            evidence_type="project" if phase in {"D", "E"} else "application",
        )
        if subject_ref in entities:
            entities[subject_ref]["sources"] = sorted(set(entities[subject_ref]["sources"] + [source_ref]))
            entities[subject_ref]["evidence_package_ids"] = sorted(
                set(entities[subject_ref]["evidence_package_ids"] + [package_id])
            )
            entities[subject_ref]["confidence"] = "high"

    relationships = sorted(deepcopy(graph["relationships"]), key=lambda item: item["relationship_id"])
    for package in graph["evidence_packages"]:
        relationship = next(
            item for item in relationships if item["relationship_id"] == package["subject_ref"]
        )
        evidence_packages[package["package_id"]] = _direct_evidence(
            package["package_id"],
            package["subject_ref"],
            package["finding"],
            [f"phase:{relationship['provenance']['source_phase']}:approved-evidence"],
            provenance=package["provenance_refs"],
            confidence=package["confidence"],
            review_state=package["review_state"],
            evidence_type="relationship",
        )

    for relationship in relationships:
        package_id = relationship["evidence"]["package_id"]
        for entity_id in (relationship["source_ref"], relationship["target_ref"]):
            if entity_id in entities:
                entities[entity_id]["evidence_package_ids"] = sorted(
                    set(entities[entity_id]["evidence_package_ids"] + [package_id])
                )

    return {
        "policy": deepcopy(policy),
        "entities": entities,
        "relationships": relationships,
        "evidence_packages": evidence_packages,
        "conflicts": sorted(deepcopy(graph["conflicts"]), key=lambda item: item.get("conflict_id", "")),
        "missing_representations": [],
        "recovery_candidates": [],
        "source_refs": [
            "registry:projects",
            "registry:applications",
            "phase:D:approved-observation",
            "phase:E:approved-observation",
            "phase:F:approved-observation",
            graph_source,
        ],
    }


def load_query_model(policy: dict[str, Any] | None = None) -> dict[str, Any]:
    active_policy = policy or load_query_policy()
    errors = query_policy_errors(active_policy)
    if errors:
        raise QueryValidationError(errors[0])
    registries = {
        relative: load_json(ROOT / relative) for relative in active_policy["registry_inputs"]
    }
    for relative, registry in registries.items():
        try:
            validate_schema(registry, load_json(ROOT / REGISTRY_SCHEMAS[relative]))
        except (SchemaValidationError, TypeError) as exc:
            raise QueryValidationError(str(exc)) from exc
    recovery_config = {"evidence_inputs": active_policy["evidence_inputs"]}
    try:
        inputs = load_recovery_evidence_inputs(recovery_config)
    except (PilotBoundaryError, OSError, ValueError) as exc:
        raise QueryValidationError(str(exc)) from exc
    source_errors = recovery_source_evidence_errors(inputs)
    if source_errors:
        raise QueryValidationError(source_errors[0])
    return build_query_model(active_policy, registries, inputs)


class DeterministicQueryLayer:
    """Read-only deterministic query surface with no discovery or action methods."""

    def __init__(self, model: dict[str, Any] | None = None) -> None:
        self.model = deepcopy(model) if model is not None else load_query_model()
        self.policy = self.model["policy"]
        self.entities = self.model["entities"]
        self.relationships = sorted(
            self.model["relationships"], key=lambda item: item["relationship_id"]
        )
        self.evidence_packages = self.model["evidence_packages"]

    def _canonical_ref(self, entity_ref: str) -> str:
        aliases = {
            f"application:{key.removeprefix('application-concept:')}": key
            for key in self.entities
            if key.startswith("application-concept:")
        }
        aliases.update(
            {
                f"resource:{key.removeprefix('registry-system:')}": key
                for key in self.entities
                if key.startswith("registry-system:")
            }
        )
        return aliases.get(entity_ref, entity_ref)

    def _has_restricted_grant(self, grants: list[str]) -> bool:
        return self.policy["restricted_permission"] in set(grants)

    def _assert_access(self, entity: dict[str, Any], grants: list[str]) -> None:
        if entity["classification"] == "restricted" and not self._has_restricted_grant(grants):
            raise QuerySecurityError(
                f"restricted entity requires {self.policy['restricted_permission']}"
            )

    def _conflict_refs(self) -> set[str]:
        refs: set[str] = set()
        for conflict in self.model.get("conflicts", []):
            for key in ("subject_ref", "source_ref", "target_ref"):
                value = conflict.get(key)
                if isinstance(value, str):
                    refs.add(value)
            refs.update(item for item in conflict.get("candidate_refs", []) if isinstance(item, str))
        return refs

    def _related_conflict_ids(self, entity_ref: str, relationship_id: str = "") -> list[str]:
        conflict_ids: list[str] = []
        for conflict in self.model.get("conflicts", []):
            candidates = set(conflict.get("candidate_refs", []))
            direct_refs = {
                conflict.get("subject_ref"), conflict.get("source_ref"), conflict.get("target_ref")
            }
            if relationship_id in candidates or entity_ref in direct_refs:
                conflict_ids.append(
                    conflict.get("conflict_id", conflict.get("subject_ref", "conflict:unknown"))
                )
        return sorted(set(conflict_ids))

    def _in_scope(self, entity: dict[str, Any], scope: str) -> bool:
        if scope == "all":
            return True
        if scope == "active":
            return entity["status"] == "active"
        if scope == "classroom_ready":
            return "classroom_ready" in entity["scope_tags"]
        if scope == "teacher_only":
            return entity["classification"] == "teacher_internal" or "teacher_only" in entity["scope_tags"]
        if scope == "student_safe":
            return entity["classification"] in {"public", "student_safe"}
        if scope == "restricted":
            return entity["classification"] == "restricted"
        if scope == "superseded":
            return entity["status"] == "superseded"
        if scope == "unreviewed":
            return entity["review_state"] == "unreviewed"
        if scope == "conflicts":
            return entity["entity_id"] in self._conflict_refs()
        raise QueryValidationError(f"unsupported scope: {scope}")

    def _resolve_entities(
        self,
        target_ref: str,
        *,
        entity_types: set[str] | None,
        scope: str,
        filters: dict[str, str],
        grants: list[str],
    ) -> list[dict[str, Any]]:
        canonical = self._canonical_ref(target_ref)
        candidates = (
            [self.entities[canonical]] if canonical and canonical in self.entities else list(self.entities.values()) if not canonical else []
        )
        results: list[dict[str, Any]] = []
        for entity in candidates:
            if entity_types is not None and entity["type"] not in entity_types:
                continue
            if not self._in_scope(entity, scope):
                continue
            if "classification" in filters and entity["classification"] != filters["classification"]:
                continue
            if "confidence" in filters and entity["confidence"] != filters["confidence"]:
                continue
            if "review_state" in filters and entity["review_state"] != filters["review_state"]:
                continue
            self._assert_access(entity, grants)
            results.append(entity)
        return sorted(results, key=lambda item: item["entity_id"])

    def explain(
        self, entity_ref: str, *, scope: str = "all", permission_grants: list[str] | None = None
    ) -> dict[str, Any]:
        grants = permission_grants or []
        if scope == "restricted" and not self._has_restricted_grant(grants):
            raise QuerySecurityError(
                f"restricted scope requires {self.policy['restricted_permission']}"
            )
        canonical = self._canonical_ref(entity_ref)
        entity = self.entities.get(canonical)
        if entity is None or not self._in_scope(entity, scope):
            explanation = {
                "schema_version": 1,
                "subject_ref": entity_ref,
                "subject_type": "unknown",
                "summary": "The entity is not present in the fixed approved Phase J inputs for this scope.",
                "sources": [],
                "evidence_packages": [],
                "relationships": [],
                "confidence": "unknown",
                "review_state": "unreviewed",
                "uncertainties": ["Entity identity or scope membership remains unknown."],
                "authority_context": _authority_context(),
                "action_authority": "none",
            }
        else:
            self._assert_access(entity, grants)
            relationships = [
                item for item in self.relationships
                if canonical in {item["source_ref"], item["target_ref"]}
            ]
            uncertainties = list(entity["uncertainties"])
            if not relationships:
                uncertainties.append("No relationship evidence is present in the approved Phase G graph.")
            if not entity["evidence_package_ids"]:
                uncertainties.append("No evidence package is linked to this entity.")
            conflict_ids = self._related_conflict_ids(canonical)
            if conflict_ids:
                uncertainties.append(
                    f"Unresolved relationship conflict(s): {', '.join(conflict_ids)}."
                )
            if not uncertainties:
                uncertainties.append("Evidence remains bounded to the fixed approved Phase J inputs.")
            explanation = {
                "schema_version": 1,
                "subject_ref": canonical,
                "subject_type": entity["type"],
                "summary": entity["summary"],
                "sources": sorted(entity["sources"]),
                "evidence_packages": sorted(entity["evidence_package_ids"]),
                "relationships": sorted(item["relationship_id"] for item in relationships),
                "confidence": entity["confidence"],
                "review_state": entity["review_state"],
                "uncertainties": sorted(set(uncertainties)),
                "authority_context": deepcopy(entity["authority_context"]),
                "action_authority": "none",
            }
        errors = explanation_errors(explanation)
        if errors:
            raise QueryValidationError(errors[0])
        return explanation

    def related_to(
        self,
        entity_ref: str,
        *,
        scope: str = "all",
        filters: dict[str, str] | None = None,
        permission_grants: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        filters = filters or {}
        grants = permission_grants or []
        if scope == "restricted" and not self._has_restricted_grant(grants):
            raise QuerySecurityError(
                f"restricted scope requires {self.policy['restricted_permission']}"
            )
        canonical = self._canonical_ref(entity_ref)
        entity = self.entities.get(canonical)
        if entity is None or not self._in_scope(entity, scope):
            return []
        self._assert_access(entity, grants)
        results = []
        for relationship in self.relationships:
            if canonical not in {relationship["source_ref"], relationship["target_ref"]}:
                continue
            if "relationship_type" in filters and relationship["relationship_type"] != filters["relationship_type"]:
                continue
            if "confidence" in filters and relationship["confidence"] != filters["confidence"]:
                continue
            if "review_state" in filters and relationship["review_state"] != filters["review_state"]:
                continue
            related_ref = relationship["target_ref"] if relationship["source_ref"] == canonical else relationship["source_ref"]
            related_entity = self.entities.get(related_ref)
            if related_entity is not None:
                self._assert_access(related_entity, grants)
                if not self._in_scope(related_entity, scope):
                    continue
                if (
                    "classification" in filters
                    and related_entity["classification"] != filters["classification"]
                ):
                    continue
            elif "classification" in filters:
                continue
            results.append(
                {
                    "relationship_id": relationship["relationship_id"],
                    "relationship_type": relationship["relationship_type"],
                    "direction": "outgoing" if relationship["source_ref"] == canonical else "incoming",
                    "related_ref": related_ref,
                    "evidence_package_id": relationship["evidence"]["package_id"],
                    "provenance": deepcopy(relationship["provenance"]),
                    "confidence": relationship["confidence"],
                    "review_state": relationship["review_state"],
                    "conflicts": self._related_conflict_ids(canonical, relationship["relationship_id"]),
                    "authority_effect": "none",
                    "action_authority": "none",
                }
            )
        return sorted(results, key=lambda item: item["relationship_id"])

    def why(
        self,
        entity_ref: str,
        *,
        scope: str = "all",
        filters: dict[str, str] | None = None,
        permission_grants: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        filters = filters or {}
        explanation = self.explain(entity_ref, scope=scope, permission_grants=permission_grants)
        entity = self.entities.get(explanation["subject_ref"])
        if (
            "classification" in filters
            and (entity is None or entity["classification"] != filters["classification"])
        ):
            return []
        packages = []
        for package_id in explanation["evidence_packages"]:
            package = self.evidence_packages.get(package_id)
            if package is None:
                continue
            if "confidence" in filters and package["confidence"] != filters["confidence"]:
                continue
            if "review_state" in filters and package["review_state"] != filters["review_state"]:
                continue
            packages.append(deepcopy(package))
        return sorted(packages, key=lambda item: item["package_id"])

    def uncertain(
        self, *, scope: str = "all", permission_grants: list[str] | None = None
    ) -> list[dict[str, Any]]:
        grants = permission_grants or []
        if scope == "restricted" and not self._has_restricted_grant(grants):
            raise QuerySecurityError(
                f"restricted scope requires {self.policy['restricted_permission']}"
            )
        items: list[dict[str, Any]] = []
        for entity in sorted(self.entities.values(), key=lambda item: item["entity_id"]):
            if not self._in_scope(entity, scope):
                continue
            self._assert_access(entity, grants)
            if entity["authority_context"]["role"] == "unknown":
                items.append(self._uncertainty_item(
                    entity["entity_id"], "unknown_authority",
                    "No approved input establishes authority for this entity.",
                    entity["confidence"], entity["review_state"],
                ))
            if not entity["evidence_package_ids"]:
                items.append(self._uncertainty_item(
                    entity["entity_id"], "missing_evidence",
                    "No evidence package is linked to this entity.",
                    "unknown", entity["review_state"],
                ))
        for conflict in self.model.get("conflicts", []):
            item_ref = conflict.get("conflict_id", conflict.get("subject_ref", "conflict:unknown"))
            items.append(self._uncertainty_item(
                item_ref, "conflict", "Competing relationship claims remain unresolved.",
                "unknown", "unreviewed",
            ))
        for signal in self.model.get("missing_representations", []):
            items.append(self._uncertainty_item(
                signal.get("signal_id", signal.get("subject_ref", "representation:unknown")),
                "missing_representation", signal.get("detail", "An expected representation is missing."),
                signal.get("confidence", "unknown"), signal.get("review_state", "unreviewed"),
            ))
        for candidate in self.model.get("recovery_candidates", []):
            if candidate.get("review_state", "unreviewed") == "unreviewed":
                items.append(self._uncertainty_item(
                    candidate.get("candidate_id", "recovery-candidate:unknown"),
                    "unreviewed_candidate", "A recovery candidate awaits teacher review.",
                    candidate.get("confidence", "unknown"), "unreviewed",
                ))
        return sorted(items, key=lambda item: (item["uncertainty_type"], item["item_ref"], item["detail"]))

    def _uncertainty_item(
        self, item_ref: str, uncertainty_type: str, detail: str, confidence: str, review_state: str
    ) -> dict[str, Any]:
        item = {
            "item_ref": item_ref,
            "uncertainty_type": uncertainty_type,
            "detail": detail,
            "confidence": confidence,
            "review_state": REVIEW_STATES.get(review_state, review_state),
            "interpretation": "review_opportunity_not_failure",
            "action_authority": "none",
        }
        errors = uncertainty_errors(item)
        if errors:
            raise QueryValidationError(errors[0])
        return item

    def recovery_candidates(
        self, entity_ref: str, *, permission_grants: list[str] | None = None
    ) -> list[dict[str, Any]]:
        canonical = self._canonical_ref(entity_ref)
        entity = self.entities.get(canonical)
        if entity is not None:
            self._assert_access(entity, permission_grants or [])
        results = []
        for candidate in self.model.get("recovery_candidates", []):
            if canonical and canonical not in {
                candidate.get("subject_ref"), candidate.get("resource_ref"), candidate.get("candidate_ref")
            }:
                continue
            results.append(
                {
                    "candidate": candidate.get("candidate_ref", candidate.get("candidate_id", "unknown")),
                    "evidence": sorted(candidate.get("evidence", [])),
                    "confidence": candidate.get("confidence", "unknown"),
                    "risk": candidate.get("risk", "unknown"),
                    "next_step": candidate.get("next_step", "Teacher review required."),
                    "review_state": candidate.get("review_state", "unreviewed"),
                    "action_authority": "none",
                }
            )
        return sorted(results, key=lambda item: item["candidate"])

    def execute(self, query: dict[str, Any]) -> dict[str, Any]:
        errors = query_errors(query)
        if errors:
            raise QueryValidationError(errors[0])
        if query["scope"] == "restricted" and not self._has_restricted_grant(query["permission_grants"]):
            raise QuerySecurityError(
                f"restricted scope requires {self.policy['restricted_permission']}"
            )
        query_type = query["query_type"]
        target = query["target_ref"]
        kwargs = {
            "scope": query["scope"],
            "filters": query["filters"],
            "grants": query["permission_grants"],
        }
        uncertainty: list[str] = []
        if query_type in {"entity_lookup", "project_lookup", "application_lookup", "resource_lookup"}:
            entity_types = {
                "project_lookup": {"project"},
                "application_lookup": {"application"},
                "resource_lookup": RESOURCE_ENTITY_TYPES,
            }.get(query_type)
            results = self._resolve_entities(
                target, entity_types=entity_types, scope=kwargs["scope"],
                filters=kwargs["filters"], grants=kwargs["grants"],
            )
            safe_results = [
                {
                    "entity_id": item["entity_id"],
                    "label": item["label"],
                    "type": item["type"],
                    "status": item["status"],
                    "classification": item["classification"],
                    "confidence": item["confidence"],
                    "review_state": item["review_state"],
                    "action_authority": "none",
                }
                for item in results
            ]
            uncertainty.extend(
                detail for item in results for detail in item["uncertainties"]
            )
            if target and not safe_results:
                uncertainty.append("Entity identity, requested type, or scope membership remains unknown.")
        elif query_type == "relationship_lookup":
            safe_results = self.related_to(
                target, scope=kwargs["scope"], filters=kwargs["filters"],
                permission_grants=kwargs["grants"],
            )
            if not safe_results:
                uncertainty.append("No matching relationship is present in the approved graph.")
            if any(item["conflicts"] for item in safe_results):
                uncertainty.append("One or more returned relationships has an unresolved conflict.")
            if any(item["review_state"] == "unreviewed" for item in safe_results):
                uncertainty.append("One or more relationship results are unreviewed.")
        elif query_type == "evidence_lookup":
            safe_results = self.why(
                target, scope=kwargs["scope"], filters=kwargs["filters"],
                permission_grants=kwargs["grants"],
            )
            if not safe_results:
                uncertainty.append("No matching evidence package is linked to this entity.")
            elif any(item["review_state"] == "unreviewed" for item in safe_results):
                uncertainty.append("One or more evidence packages are unreviewed.")
        else:
            safe_results = self.recovery_candidates(target, permission_grants=kwargs["grants"])
            if not safe_results:
                uncertainty.append("No live recovery candidates exist; live candidate generation is disabled.")
            elif any(item["review_state"] == "unreviewed" for item in safe_results):
                uncertainty.append("One or more recovery candidates require teacher review.")
        response = {
            "schema_version": 1,
            "query_id": query["query_id"],
            "query_type": query_type,
            "target_ref": target,
            "scope": query["scope"],
            "results": safe_results,
            "uncertainties": sorted(set(uncertainty)),
            "authority_effect": "none",
            "action_authority": "none",
        }
        response_validation = response_errors(response)
        if response_validation:
            raise QueryValidationError(response_validation[0])
        return response

    def status(self) -> dict[str, Any]:
        return {
            "phase": "J",
            "mode": "deterministic_read_only",
            "sources": len(self.model["source_refs"]),
            "entities": len(self.entities),
            "relationships": len(self.relationships),
            "evidence_packages": len(self.evidence_packages),
            "conflicts": len(self.model.get("conflicts", [])),
            "recovery_candidates": len(self.model.get("recovery_candidates", [])),
            "ai_enabled": False,
            "action_capabilities": [],
            "live_recovery_candidates_enabled": False,
        }

    def ai_compatibility_input(self, entity_ref: str) -> dict[str, Any]:
        """Build the deterministic internal shape consumed by Phase I; performs no AI call."""
        explanation = self.explain(entity_ref)
        if explanation["subject_type"] == "unknown":
            raise QueryValidationError("unknown entities cannot enter an AI compatibility projection")
        entity = self.entities[explanation["subject_ref"]]
        related = self.related_to(explanation["subject_ref"])
        evidence = self.why(explanation["subject_ref"])
        if not evidence:
            raise QueryValidationError("AI compatibility input requires explanation evidence")
        package_id = f"evidence-package:phase-j:{explanation['subject_ref']}"
        observations = sorted({source for item in evidence for source in item["sources"]})
        relationship_ids = [item["relationship_id"] for item in related]
        return {
            "view_id": f"ai-view:phase-j:{explanation['subject_ref']}",
            "source_refs": ["phase:J:deterministic-explanation"],
            "entities": [{
                "entity_id": entity["entity_id"],
                "label": entity["label"],
                "type": entity["type"],
                "authority": entity["authority_context"]["role"],
                "confidence": entity["confidence"],
                "review_state": entity["review_state"],
                "classification": entity["classification"],
                "metadata": {"status": entity["status"]},
            }],
            "relationships": [{
                "relationship_type": item["relationship_type"],
                "source_ref": explanation["subject_ref"] if item["direction"] == "outgoing" else item["related_ref"],
                "target_ref": item["related_ref"] if item["direction"] == "outgoing" else explanation["subject_ref"],
                "confidence": item["confidence"],
                "review_state": item["review_state"],
            } for item in related],
            "evidence_packages": [{
                "schema_version": 1,
                "evidence_package_id": package_id,
                "evidence_type": "relationship" if relationship_ids else entity["type"] if entity["type"] in {"project", "application"} else "classification",
                "subject_ref": entity["entity_id"],
                "claim": explanation["summary"],
                "observations": observations,
                "relationships": relationship_ids,
                "authority_context": deepcopy(entity["authority_context"]),
                "confidence": entity["confidence"],
                "alternatives": [],
                "review_state": entity["review_state"],
                "authority_effect": "none",
                "permission_effect": "none",
            }],
            "evidence_source_systems": {package_id: explanation["sources"]},
            "evidence_uncertainty": {package_id: explanation["uncertainties"]},
            "recommendations": [],
        }
