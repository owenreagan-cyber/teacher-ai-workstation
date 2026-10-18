#!/usr/bin/env python3
"""Validate Phase B static workspace policy without observing the machine."""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
REGISTRY_SCHEMAS = {
    "workspace.json": "workspace.schema.json",
    "storage-sources.json": "storage-source.schema.json",
    "applications.json": "application.schema.json",
    "projects.json": "project.schema.json",
    "classifications.json": "classification.schema.json",
    "permissions.json": "permission.schema.json",
}
SUPPORTED_SCHEMA_KEYS = {
    "$schema",
    "title",
    "type",
    "required",
    "properties",
    "additionalProperties",
    "items",
    "minItems",
    "maxItems",
    "uniqueItems",
    "enum",
    "const",
    "pattern",
}


class SchemaValidationError(ValueError):
    pass


@dataclass(frozen=True)
class Check:
    level: str
    code: str
    message: str


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _matches_type(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "null":
        return value is None
    raise SchemaValidationError(f"unsupported schema type: {expected}")


def validate_schema(value: Any, schema: dict[str, Any], location: str = "$") -> None:
    unsupported = set(schema) - SUPPORTED_SCHEMA_KEYS
    if unsupported:
        raise SchemaValidationError(
            f"{location}: unsupported schema keyword(s): {sorted(unsupported)}"
        )

    expected = schema.get("type")
    if expected is not None:
        options = expected if isinstance(expected, list) else [expected]
        if not any(_matches_type(value, option) for option in options):
            raise SchemaValidationError(
                f"{location}: expected type {options}, got {type(value).__name__}"
            )

    if "const" in schema and value != schema["const"]:
        raise SchemaValidationError(f"{location}: expected constant {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        raise SchemaValidationError(f"{location}: value {value!r} is not allowed")
    if "pattern" in schema and isinstance(value, str):
        if re.search(schema["pattern"], value) is None:
            raise SchemaValidationError(f"{location}: value does not match pattern")

    if isinstance(value, dict):
        required = schema.get("required", [])
        missing = [key for key in required if key not in value]
        if missing:
            raise SchemaValidationError(f"{location}: missing required keys {missing}")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            extras = set(value) - set(properties)
            if extras:
                raise SchemaValidationError(
                    f"{location}: unexpected properties {sorted(extras)}"
                )
        for key, child in value.items():
            if key in properties:
                validate_schema(child, properties[key], f"{location}.{key}")

    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            raise SchemaValidationError(f"{location}: too few items")
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            raise SchemaValidationError(f"{location}: too many items")
        if schema.get("uniqueItems"):
            encoded = [json.dumps(item, sort_keys=True) for item in value]
            if len(encoded) != len(set(encoded)):
                raise SchemaValidationError(f"{location}: items must be unique")
        if "items" in schema:
            for index, child in enumerate(value):
                validate_schema(child, schema["items"], f"{location}[{index}]")


def authority_errors(sources: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    canonical: dict[tuple[str, str], list[str]] = defaultdict(list)
    source_scopes = {"source_code", "curriculum_binary", "registry_metadata"}
    for source in sources:
        source_id = source.get("id", "unknown-source")
        kind = source.get("kind")
        for assertion in source.get("authority_assertions", []):
            role = assertion.get("authority_role")
            scope = assertion.get("authority_scope")
            subject = assertion.get("subject_ref")
            basis = assertion.get("basis")
            if kind == "backup" and role == "canonical":
                errors.append(f"{source_id}: backup source cannot claim canonical")
            if role == "deployment" and scope in source_scopes:
                errors.append(
                    f"{source_id}: deployment cannot claim source authority for {scope}"
                )
            if basis == "timestamp":
                errors.append(f"{source_id}: timestamp cannot establish authority")
            if role == "canonical" and subject and scope:
                canonical[(subject, scope)].append(source_id)
    for (subject, scope), owners in sorted(canonical.items()):
        if len(set(owners)) > 1:
            errors.append(
                f"conflicting canonical claims for {subject}/{scope}: {sorted(set(owners))}"
            )
    return errors


def classification_assignment_errors(value: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required = {"value", "classification_basis", "confidence", "review_state"}
    missing = required - set(value)
    if missing:
        errors.append(f"classification missing fields: {sorted(missing)}")
        return errors
    basis = value.get("classification_basis")
    if not isinstance(basis, dict):
        return ["classification_basis must be an object"]
    basis_required = {"kind", "rule_id", "rule_version", "evidence"}
    basis_missing = basis_required - set(basis)
    if basis_missing:
        errors.append(f"classification_basis missing fields: {sorted(basis_missing)}")
    if not isinstance(basis.get("evidence"), list) or not basis.get("evidence"):
        errors.append("classification_basis evidence must be a non-empty array")
    return errors


def project_errors(projects: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    for project in projects:
        if project.get("status") != "abandoned":
            continue
        basis = project.get("status_basis", {})
        if basis.get("kind") != "owner_assertion" or not basis.get(
            "owner_confirmed"
        ):
            errors.append(
                f"{project.get('id', 'unknown-project')}: abandoned requires owner confirmation"
            )
    return errors


def permission_errors(document: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if document.get("default_effect") != "deny":
        errors.append("permission default must be deny")
    if document.get("phase_b_execution_enabled") is not False:
        errors.append("Phase B execution must remain disabled")
    capabilities = {item.get("id"): item for item in document.get("capabilities", [])}
    if None in capabilities:
        errors.append("capability ID is required")
    if len(capabilities) != len(document.get("capabilities", [])):
        errors.append("capability IDs must be unique")
    levels = document.get("levels", [])
    if {item.get("level") for item in levels} != {0, 1, 2, 3, 4}:
        errors.append("permission levels must be exactly 0 through 4")
    for level in levels:
        number = level.get("level")
        if level.get("unrestricted_filesystem_access") is not False:
            errors.append(f"level {number}: unrestricted filesystem access is forbidden")
        if level.get("execution_allowed") is not False:
            errors.append(f"level {number}: Phase B execution is forbidden")
        for capability_id in level.get("allowed_capabilities", []):
            capability = capabilities.get(capability_id)
            if capability is None:
                errors.append(f"level {number}: unknown capability {capability_id}")
                continue
            if capability.get("minimum_level") != number:
                errors.append(
                    f"level {number}: capability level mismatch for {capability_id}"
                )
            if number == 0 and capability.get("mutating"):
                errors.append(f"level 0: mutating capability forbidden: {capability_id}")
    for capability in capabilities.values():
        if capability.get("mutating") and capability.get("phase_b_effect") != "blocked":
            errors.append(
                f"mutating capability must be blocked: {capability.get('id')}"
            )
    delete = capabilities.get("file.delete")
    if delete and delete.get("approval") != "two_step_teacher":
        errors.append("file.delete must require two-step teacher approval")
    level_four = next((item for item in levels if item.get("level") == 4), {})
    if not all(
        level_four.get(key) is True
        for key in ("scoped_grants_required", "approval_required", "stop_points_required")
    ):
        errors.append("level 4 requires scoped grants, approval, and stop points")
    return errors


def semantic_checks(documents: dict[str, dict[str, Any]]) -> list[Check]:
    checks: list[Check] = []
    workspace = documents["workspace.json"]
    roots = workspace["recursive_scan_policy"]["never_recursive_scan_roots"]
    checks.append(
        Check(
            "PASS" if "/Users/owen" in roots else "FAIL",
            "workspace.home_root",
            "/Users/owen is prohibited as a recursive scan root",
        )
    )
    area_map = {area["id"]: area for area in workspace["areas"]}
    expected_areas = {
        "projects",
        "documents",
        "desktop",
        "downloads",
        "applications",
        "library",
        "cloud-storage",
        "archives",
        "external-storage",
    }
    checks.append(
        Check(
            "PASS" if set(area_map) == expected_areas else "FAIL",
            "workspace.areas",
            "all nine workspace policy areas are declared",
        )
    )
    library_safe = (
        area_map.get("library", {}).get("indexing_policy") == "denied"
        and area_map.get("library", {}).get("mutation_policy") == "forbidden"
    )
    checks.append(
        Check(
            "PASS" if library_safe else "FAIL",
            "workspace.library",
            "Library indexing and mutation are forbidden",
        )
    )

    storage = documents["storage-sources.json"]
    storage_errors = authority_errors(storage["sources"])
    checks.append(
        Check(
            "PASS" if not storage_errors else "FAIL",
            "storage.authority",
            "authority claims are scoped and nonconflicting"
            if not storage_errors
            else storage_errors[0],
        )
    )
    disconnected = all(
        source["connection_state"] == "unknown" for source in storage["sources"]
    )
    checks.append(
        Check(
            "PASS" if not storage["runtime_connections_enabled"] and disconnected else "FAIL",
            "storage.connections",
            "all storage sources are unobserved policy declarations",
        )
    )
    access_safe = all(
        source["access_policy"]["content_read"] == "forbidden"
        and source["access_policy"]["hashing"] == "separate_approval"
        and source["access_policy"]["write"] == "forbidden"
        and not source["scan_policy"]["implicit_recursion"]
        and not source["scan_policy"]["follow_symlinks"]
        and not source["scan_policy"]["cloud_placeholder_download"]
        for source in storage["sources"]
    )
    checks.append(
        Check(
            "PASS" if access_safe else "FAIL",
            "storage.access",
            "content, hashing, writes, implicit recursion, symlinks, and downloads are gated",
        )
    )

    applications = documents["applications.json"]
    app_static = (
        not applications["runtime_discovery_enabled"]
        and not applications["launch_enabled"]
        and applications["installed_instances"] == []
    )
    checks.append(
        Check(
            "PASS" if app_static else "FAIL",
            "application.static_only",
            "application concepts contain no discovered instances or launch behavior",
        )
    )

    projects = documents["projects.json"]
    project_state_errors = project_errors(projects["projects"])
    checks.append(
        Check(
            "PASS" if not project_state_errors else "FAIL",
            "project.status",
            "project status does not infer abandonment"
            if not project_state_errors
            else project_state_errors[0],
        )
    )
    checks.append(
        Check(
            "PASS"
            if not projects["git_inspection_enabled"]
            and not projects["filesystem_discovery_enabled"]
            else "FAIL",
            "project.discovery",
            "Git inspection and filesystem discovery are disabled",
        )
    )

    classifications = documents["classifications.json"]
    dimensions = classifications["dimensions"]
    separate = set(dimensions) == {
        "workspace_role",
        "data_sensitivity",
        "authority_role",
        "lifecycle",
    }
    checks.append(
        Check(
            "PASS" if separate else "FAIL",
            "classification.dimensions",
            "workspace role, sensitivity, authority, and lifecycle remain separate",
        )
    )
    checks.append(
        Check(
            "PASS"
            if classifications["policies"]["unknown_preferred_over_unsupported_claim"]
            and not classifications["policies"]["newer_implies_canonical"]
            else "FAIL",
            "classification.conservative",
            "unknown is preferred and recency cannot establish authority",
        )
    )

    permissions = documents["permissions.json"]
    policy_errors = permission_errors(permissions)
    checks.append(
        Check(
            "PASS" if not policy_errors else "FAIL",
            "permission.levels",
            "permission levels are default-deny and non-executable"
            if not policy_errors
            else policy_errors[0],
        )
    )

    project_ids = {item["id"] for item in projects["projects"]}
    concept_ids = {item["concept_id"] for item in applications["concepts"]}
    cross_errors = []
    for concept in applications["concepts"]:
        cross_errors.extend(
            f"unknown project reference: {value}"
            for value in concept["related_project_ids"]
            if value not in project_ids
        )
    for project in projects["projects"]:
        cross_errors.extend(
            f"unknown application concept: {value}"
            for value in project["related_application_concepts"]
            if value not in concept_ids
        )
    checks.append(
        Check(
            "PASS" if not cross_errors else "FAIL",
            "registry.cross_reference",
            "project and application references resolve"
            if not cross_errors
            else cross_errors[0],
        )
    )
    return checks


def run_validation() -> list[Check]:
    checks: list[Check] = []
    documents: dict[str, dict[str, Any]] = {}
    for registry_name, schema_name in REGISTRY_SCHEMAS.items():
        document = load_json(ROOT / "registry" / registry_name)
        schema = load_json(ROOT / "schemas" / schema_name)
        try:
            validate_schema(document, schema)
        except (SchemaValidationError, TypeError) as exc:
            checks.append(Check("FAIL", f"schema.{registry_name}", str(exc)))
        else:
            checks.append(
                Check(
                    "PASS",
                    f"schema.{registry_name}",
                    f"{registry_name} matches {schema_name}",
                )
            )
        documents[registry_name] = document
    if any(check.level == "FAIL" for check in checks):
        return checks
    return checks + semantic_checks(documents)


def main() -> int:
    try:
        checks = run_validation()
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        print(f"FAIL: policy.validation: {exc}")
        return 1
    counts = {level: 0 for level in ("PASS", "WARN", "FAIL")}
    for check in checks:
        counts[check.level] += 1
        print(f"{check.level}: {check.code}: {check.message}")
    print(
        f"Summary: PASS={counts['PASS']} WARN={counts['WARN']} FAIL={counts['FAIL']}"
    )
    return 1 if counts["FAIL"] else 0


if __name__ == "__main__":
    sys.exit(main())
