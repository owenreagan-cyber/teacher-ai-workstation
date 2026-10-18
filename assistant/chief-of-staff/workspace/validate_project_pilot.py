#!/usr/bin/env python3
"""Validate Phase E policy and one explicitly named host-local project run."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from typing import Any

from pilot import APPROVED_OUTPUT_ROOT
from project_pilot import (
    CONFIG_PATH,
    GIT_OPERATION_ARGS,
    project_config_errors,
    project_observation_errors,
)
from validate import load_json
from validate_observation import audit_event_errors, inventory_run_errors


ROOT = CONFIG_PATH.parents[2]
RUN_ID_PATTERN = re.compile(
    r"^run:history-project-intelligence-pilot-[a-z0-9-]+$"
)
FORBIDDEN_OBSERVATION_KEYS = {
    "content",
    "readme_content",
    "source_content",
    "commit_message",
    "commit_history",
    "issue_data",
    "secret",
    "credentials",
    "package_manifest",
    "dependency_graph",
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
        return [Check("FAIL", "project.run_id", "run ID is outside Phase E")]
    run = load_json(APPROVED_OUTPUT_ROOT / "inventory-runs" / f"{run_id}.json")
    observation = load_json(
        APPROVED_OUTPUT_ROOT / "observations" / f"{run_id}-project.json"
    )
    audit = load_json(APPROVED_OUTPUT_ROOT / "audit" / f"{run_id}-project.json")
    config = load_json(CONFIG_PATH)

    run_errors = inventory_run_errors(run)
    checks = [
        Check(
            "PASS" if not run_errors else "FAIL",
            "project.inventory_run",
            "project inventory run matches the Phase C contract"
            if not run_errors
            else run_errors[0],
        )
    ]
    observation_errors = project_observation_errors(observation)
    if observation.get("run_id") != run_id:
        observation_errors.append("project observation run provenance mismatch")
    checks.append(
        Check(
            "PASS" if not observation_errors else "FAIL",
            "project.observation",
            "project observation has separate identities and read-only metadata"
            if not observation_errors
            else observation_errors[0],
        )
    )

    forbidden = _keys(observation) & FORBIDDEN_OBSERVATION_KEYS
    checks.append(
        Check(
            "PASS" if not forbidden else "FAIL",
            "project.privacy",
            "project observation contains no content, secrets, history, or manifests"
            if not forbidden
            else f"forbidden observation fields: {sorted(forbidden)}",
        )
    )

    git_safe = (
        observation["git"]["metadata_method"] == "read_only_git_allowlist"
        and not observation["git"]["history_inspected"]
        and not observation["git"]["other_branches_inspected"]
        and set(config["git_operations"]) == set(GIT_OPERATION_ARGS)
    )
    checks.append(
        Check(
            "PASS" if git_safe else "FAIL",
            "project.git_safety",
            "Git metadata is limited to five non-mutating operations",
        )
    )

    evidence_safe = all(
        item["state_candidate"] != "abandoned"
        and item["review_state"] == "unreviewed"
        for item in observation["state_evidence"]
    )
    checks.append(
        Check(
            "PASS" if evidence_safe else "FAIL",
            "project.state_evidence",
            "state remains explainable evidence without abandonment inference",
        )
    )

    relationships_safe = all(
        item["authority_claim"] == "none"
        and item["automatic_linking"] is False
        for item in observation["relationships"]
    )
    checks.append(
        Check(
            "PASS" if relationships_safe else "FAIL",
            "project.relationships",
            "relationship candidates are unreviewed and non-authoritative",
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
        audit_errors.append("successful Phase E audit event set is incomplete")
    checks.append(
        Check(
            "PASS" if not audit_errors else "FAIL",
            "project.audit",
            "audit records project start, completion, and validation"
            if not audit_errors
            else audit_errors[0],
        )
    )
    checks.append(
        Check(
            "PASS" if run["status"] == "completed" and not run["errors"] else "FAIL",
            "project.status",
            "Phase E run completed without warnings or errors",
        )
    )
    return checks


def run_validation(run_id: str | None = None) -> list[Check]:
    config = load_json(CONFIG_PATH)
    errors = project_config_errors(config)
    storage = load_json(ROOT / "registry/storage-sources.json")
    projects = load_json(ROOT / "registry/projects.json")
    source_ids = {item["id"] for item in storage["sources"]}
    project_ids = {f"project:{item['id']}" for item in projects["projects"]}
    checks = [
        Check(
            "PASS" if not errors else "FAIL",
            "project.configuration",
            "single project pilot is explicit and read-only" if not errors else errors[0],
        ),
        Check(
            "PASS" if config["parent_source_id"] in source_ids else "FAIL",
            "project.source_registration",
            "project observation is scoped beneath projects-local",
        ),
        Check(
            "PASS" if config["project_id"] in project_ids else "FAIL",
            "project.identity_registration",
            "project:history resolves to the static Project Registry",
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
        print(f"FAIL: project.validation: {exc}")
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
