#!/usr/bin/env python3
"""Validate Phase C contracts without observing the host."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from validate import SchemaValidationError, load_json, validate_schema


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
POLICY_SCHEMAS = {
    "observation-storage.json": "observation-storage.schema.json",
    "sanitization.json": "sanitization.schema.json",
    "agent-view-policy.json": "agent-view-policy.schema.json",
    "retention.json": "retention.schema.json",
}
CONTRACT_SCHEMAS = {
    "inventory_run": "inventory-run.schema.json",
    "observation": "observation-snapshot.schema.json",
    "audit_event": "audit-event.schema.json",
    "recommendation": "recommendation.schema.json",
}
REQUIRED_PROHIBITIONS = {
    "content_read",
    "hashing",
    "writes",
    "symlink_following",
    "cloud_download",
    "unapproved_recursion",
    "source_escape",
}


@dataclass(frozen=True)
class Check:
    level: str
    code: str
    message: str


def load_phase_c_fixtures() -> dict[str, Any]:
    return load_json(ROOT / "tests/fixtures/observation-cases.json")


def schema_errors(value: Any, schema_name: str) -> list[str]:
    try:
        validate_schema(value, load_json(ROOT / "schemas" / schema_name))
    except (SchemaValidationError, TypeError) as exc:
        return [str(exc)]
    return []


def inventory_run_errors(value: dict[str, Any]) -> list[str]:
    errors = schema_errors(value, CONTRACT_SCHEMAS["inventory_run"])
    if errors:
        return errors
    limits = value["limits"]
    bounds = {
        "max_depth": (0, 20),
        "max_items": (1, 100000),
        "max_duration_seconds": (1, 3600),
    }
    for key, (minimum, maximum) in bounds.items():
        if not minimum <= limits[key] <= maximum:
            errors.append(f"{key} must be between {minimum} and {maximum}")
    if set(value["prohibited_operations"]) != REQUIRED_PROHIBITIONS:
        errors.append("run must declare every prohibited operation")
    if value["status"] == "completed" and value["completed_at"] is None:
        errors.append("completed run requires completed_at")
    return errors


def observation_errors(value: dict[str, Any]) -> list[str]:
    errors = schema_errors(value, CONTRACT_SCHEMAS["observation"])
    if errors:
        return errors
    pairs = {
        "unavailable_item": "unavailable",
        "cloud_placeholder": "placeholder",
    }
    expected = pairs.get(value["item_type"])
    if expected and value["availability"] != expected:
        errors.append(f"{value['item_type']} requires availability={expected}")
    if value["item_type"] == "cloud_placeholder":
        if value["metadata"]["placeholder_state"] not in {"not_downloaded", "unknown"}:
            errors.append("cloud placeholder cannot claim downloaded content")
    return errors


def audit_event_errors(value: dict[str, Any]) -> list[str]:
    errors = schema_errors(value, CONTRACT_SCHEMAS["audit_event"])
    if errors:
        return errors
    expected_prefix = {
        "observation_started": "run:",
        "observation_completed": "run:",
        "recommendation_created": "recommendation:",
        "approval_requested": "approval:",
        "approval_granted": "approval:",
        "approval_denied": "approval:",
        "relationship_created": "relationship:",
        "relationship_validated": "relationship:",
        "relationship_conflict_detected": "relationship-conflict:",
        "relationship_reviewed": "relationship:",
        "recovery_candidate_created": "recovery-candidate:",
        "recovery_candidate_validated": "recovery-candidate:",
        "recovery_conflict_detected": "recovery-conflict:",
        "recovery_reviewed": "recovery-candidate:",
    }.get(value["event_type"])
    if expected_prefix and not value["target_ref"].startswith(expected_prefix):
        errors.append(f"{value['event_type']} requires target {expected_prefix}")
    return errors


def recommendation_errors(value: dict[str, Any]) -> list[str]:
    return schema_errors(value, CONTRACT_SCHEMAS["recommendation"])


def _policy_checks(policies: dict[str, dict[str, Any]]) -> list[Check]:
    storage = policies["observation-storage.json"]
    folders = {item["name"] for item in storage["folders"]}
    expected_folders = {
        "inventory-runs",
        "observations",
        "relationships",
        "recommendations",
        "audit",
        "cache",
    }
    checks = [
        Check(
            "PASS" if folders == expected_folders else "FAIL",
            "observation.storage_structure",
            "six host-local storage roles are declared without unrestricted instantiation",
        ),
        Check(
            "PASS"
            if storage["instantiate_in_phase_c"] is False
            and storage["authority_role"] == "evidence_only"
            else "FAIL",
            "observation.evidence_only",
            "Phase C storage is uninstantiated evidence, never authority",
        ),
    ]

    ignore_lines = {
        line.strip()
        for line in (REPO_ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    }
    checks.append(
        Check(
            "PASS" if storage["runtime_root"] in ignore_lines else "FAIL",
            "observation.gitignore",
            "future host-local observation root has an exact ignore rule",
        )
    )

    sanitization = policies["sanitization.json"]
    blocked_fields = set(sanitization["local_only_fields"]) | set(
        sanitization["forbidden_export_fields"]
    )
    required_blocked = {
        "absolute_path",
        "filename",
        "content",
        "document_text",
        "extracted_text",
        "ocr_text",
        "embedding",
        "credentials",
        "student_data",
    }
    checks.append(
        Check(
            "PASS"
            if not sanitization["phase_c_export_enabled"]
            and required_blocked <= blocked_fields
            else "FAIL",
            "sanitization.fail_closed",
            "Phase C export is disabled and sensitive fields are blocked",
        )
    )

    agent = policies["agent-view-policy.json"]
    forbidden_categories = set(agent["forbidden_categories"])
    checks.append(
        Check(
            "PASS"
            if not agent["phase_c_cloud_access_enabled"]
            and agent["action_capability"] == "none"
            and {"student_data", "filesystem_access", "absolute_paths"}
            <= forbidden_categories
            else "FAIL",
            "agent_view.disabled",
            "cloud access and action capability are disabled",
        )
    )

    retention = policies["retention.json"]
    record_types = {item["record_type"] for item in retention["policies"]}
    checks.append(
        Check(
            "PASS"
            if not retention["phase_c_enforcement_enabled"]
            and retention["authority_effect"] == "none"
            and record_types
            == {"inventory_run", "observation_snapshot", "recommendation", "audit_event", "cache"}
            and all(item["active_days"] > 0 for item in retention["policies"])
            else "FAIL",
            "retention.non_authorizing",
            "retention is bounded, unenforced, and has no authority effect",
        )
    )
    return checks


def run_validation() -> list[Check]:
    checks: list[Check] = []
    policies: dict[str, dict[str, Any]] = {}
    for registry_name, schema_name in POLICY_SCHEMAS.items():
        document = load_json(ROOT / "registry" / registry_name)
        errors = schema_errors(document, schema_name)
        checks.append(
            Check(
                "FAIL" if errors else "PASS",
                f"schema.{registry_name}",
                errors[0] if errors else f"{registry_name} matches {schema_name}",
            )
        )
        policies[registry_name] = document
    if any(check.level == "FAIL" for check in checks):
        return checks

    fixtures = load_phase_c_fixtures()
    valid_contracts = {
        "inventory_run": fixtures["inventory_run"]["valid"],
        "observation.file": fixtures["observation"]["valid_file"],
        "observation.unavailable": fixtures["observation"]["unavailable_item"],
        "observation.placeholder": fixtures["observation"]["cloud_placeholder"],
        "audit_event": fixtures["audit_event"]["valid"],
        "recommendation": fixtures["recommendation"]["valid"],
    }
    validators = {
        "inventory_run": inventory_run_errors,
        "observation.file": observation_errors,
        "observation.unavailable": observation_errors,
        "observation.placeholder": observation_errors,
        "audit_event": audit_event_errors,
        "recommendation": recommendation_errors,
    }
    for name, value in valid_contracts.items():
        errors = validators[name](value)
        checks.append(
            Check(
                "FAIL" if errors else "PASS",
                f"contract.{name}",
                errors[0] if errors else f"synthetic {name} satisfies its contract",
            )
        )
    return checks + _policy_checks(policies)


def main() -> int:
    try:
        checks = run_validation()
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        print(f"FAIL: observation.validation: {exc}")
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
