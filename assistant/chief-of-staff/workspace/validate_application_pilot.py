#!/usr/bin/env python3
"""Validate Phase F policy and one explicitly named local application run."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from typing import Any

from application_pilot import (
    CONFIG_PATH,
    METADATA_FIELD_MAP,
    application_config_errors,
    application_observation_errors,
)
from pilot import APPROVED_OUTPUT_ROOT
from validate import load_json
from validate_observation import audit_event_errors, inventory_run_errors


ROOT = CONFIG_PATH.parents[2]
RUN_ID_PATTERN = re.compile(r"^run:grade-4-writing-application-pilot-[a-z0-9-]+$")
FORBIDDEN_KEYS = {
    "application_contents",
    "app_data_container",
    "preferences",
    "caches",
    "user_database",
    "credentials",
    "tokens",
    "private_documents",
    "launch_history",
    "usage_history",
    "code_signing",
    "dependency_graph",
    "embedded_resources",
    "screenshots",
}


@dataclass(frozen=True)
class Check:
    level: str
    code: str
    message: str


def _keys(value: Any) -> set[str]:
    if isinstance(value, dict):
        result = set(value)
        for child in value.values():
            result.update(_keys(child))
        return result
    if isinstance(value, list):
        result: set[str] = set()
        for child in value:
            result.update(_keys(child))
        return result
    return set()


def validate_live_run(run_id: str) -> list[Check]:
    if RUN_ID_PATTERN.fullmatch(run_id) is None:
        return [Check("FAIL", "application.run_id", "run ID is outside Phase F")]
    run = load_json(APPROVED_OUTPUT_ROOT / "inventory-runs" / f"{run_id}.json")
    observation = load_json(
        APPROVED_OUTPUT_ROOT / "observations" / f"{run_id}-application.json"
    )
    audit = load_json(
        APPROVED_OUTPUT_ROOT / "audit" / f"{run_id}-application.json"
    )

    run_errors = inventory_run_errors(run)
    checks = [
        Check(
            "PASS" if not run_errors else "FAIL",
            "application.inventory_run",
            "application run matches the Phase C contract"
            if not run_errors
            else run_errors[0],
        )
    ]
    observation_errors = application_observation_errors(observation)
    if observation.get("run_id") != run_id:
        observation_errors.append("application observation run provenance mismatch")
    checks.append(
        Check(
            "PASS" if not observation_errors else "FAIL",
            "application.observation",
            "application identities and metadata match the approved contract"
            if not observation_errors
            else observation_errors[0],
        )
    )

    forbidden = _keys(observation) & FORBIDDEN_KEYS
    checks.append(
        Check(
            "PASS" if not forbidden else "FAIL",
            "application.privacy",
            "snapshot contains no application content or private data"
            if not forbidden
            else f"forbidden application fields: {sorted(forbidden)}",
        )
    )

    metadata_safe = (
        observation["metadata"]["metadata_source"]
        == "spotlight_metadata_allowlist"
        and observation["metadata"]["bundle_contents_read"] is False
        and observation["metadata"]["signing_inspected"] is False
    )
    checks.append(
        Check(
            "PASS" if metadata_safe else "FAIL",
            "application.metadata_source",
            "metadata came only from the four-key Spotlight allowlist",
        )
    )

    relationships_safe = all(
        item["authority_claim"] == "none"
        and item["automatic_linking"] is False
        and item["review_state"] == "unreviewed"
        for item in observation["relationships"]
    )
    checks.append(
        Check(
            "PASS" if relationships_safe else "FAIL",
            "application.relationships",
            "application relationship candidates have no authority or linking",
        )
    )

    audit_errors = [
        error for event in audit["events"] for error in audit_event_errors(event)
    ]
    expected_events = {
        "observation_started",
        "observation_completed",
        "validation_passed",
    }
    if audit.get("run_id") != run_id or {
        event.get("event_type") for event in audit["events"]
    } != expected_events:
        audit_errors.append("successful Phase F audit event set is incomplete")
    checks.append(
        Check(
            "PASS" if not audit_errors else "FAIL",
            "application.audit",
            "audit records application start, completion, and validation"
            if not audit_errors
            else audit_errors[0],
        )
    )
    checks.append(
        Check(
            "PASS" if run["status"] == "completed" and not run["errors"] else "FAIL",
            "application.status",
            "Phase F run completed without warnings or errors",
        )
    )
    return checks


def run_validation(run_id: str | None = None) -> list[Check]:
    config = load_json(CONFIG_PATH)
    errors = application_config_errors(config)
    storage = load_json(ROOT / "registry/storage-sources.json")
    applications = load_json(ROOT / "registry/applications.json")
    projects = load_json(ROOT / "registry/projects.json")
    source_ids = {item["id"] for item in storage["sources"]}
    concept_ids = {
        f"application-concept:{item['concept_id']}"
        for item in applications["concepts"]
    }
    project_ids = {f"project:{item['id']}" for item in projects["projects"]}
    checks = [
        Check(
            "PASS" if not errors else "FAIL",
            "application.configuration",
            "single application pilot is explicit and metadata-only"
            if not errors
            else errors[0],
        ),
        Check(
            "PASS" if config["parent_source_id"] in source_ids else "FAIL",
            "application.source_registration",
            "application instance is scoped beneath applications-local",
        ),
        Check(
            "PASS" if config["application_concept_id"] in concept_ids else "FAIL",
            "application.concept_registration",
            "application concept resolves to the static Application Registry",
        ),
        Check(
            "PASS" if "project:grade-4-writing" in project_ids else "FAIL",
            "application.project_registration",
            "declared Writing project target resolves",
        ),
        Check(
            "PASS"
            if set(config["metadata_keys"]) == set(METADATA_FIELD_MAP)
            and not config["prohibitions"]["application_discovery"]
            else "FAIL",
            "application.no_discovery",
            "only four metadata keys are allowed and discovery is disabled",
        ),
    ]
    if run_id and all(check.level == "PASS" for check in checks):
        checks.extend(validate_live_run(run_id))
    return checks


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id")
    args = parser.parse_args()
    try:
        checks = run_validation(args.run_id)
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        print(f"FAIL: application.validation: {exc}")
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
