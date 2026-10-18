#!/usr/bin/env python3
"""Validate Phase G policy and one explicitly named local relationship run."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass

from pilot import APPROVED_OUTPUT_ROOT
from relationship_pilot import (
    ASSERTION_TYPES,
    CONFIG_PATH,
    EXPECTED_EVIDENCE_INPUTS,
    NODE_TYPES,
    POLICY_PATH,
    RELATIONSHIP_TYPES,
    graph_errors,
    load_evidence_inputs,
    relationship_config_errors,
    source_evidence_errors,
)
from validate import load_json
from validate_observation import audit_event_errors


RUN_ID_PATTERN = re.compile(r"^run:relationship-intelligence-pilot-[a-z0-9-]+$")


@dataclass(frozen=True)
class Check:
    level: str
    code: str
    message: str


def validate_live_run(run_id: str) -> list[Check]:
    if RUN_ID_PATTERN.fullmatch(run_id) is None:
        return [Check("FAIL", "relationship.run_id", "run ID is outside Phase G")]
    graph = load_json(APPROVED_OUTPUT_ROOT / "relationships" / f"{run_id}.json")
    audit = load_json(APPROVED_OUTPUT_ROOT / "audit" / f"{run_id}-relationships.json")
    config = load_json(CONFIG_PATH)
    expected_artifacts = [item["artifact_ref"] for item in config["evidence_inputs"]]

    contract_errors = graph_errors(graph)
    if graph.get("run_id") != run_id:
        contract_errors.append("relationship graph run provenance mismatch")
    checks = [
        Check(
            "PASS" if not contract_errors else "FAIL",
            "relationship.graph",
            "relationship graph, nodes, candidates, and evidence packages satisfy their contracts"
            if not contract_errors
            else contract_errors[0],
        )
    ]
    checks.append(
        Check(
            "PASS" if graph.get("input_artifacts") == expected_artifacts else "FAIL",
            "relationship.inputs",
            "graph records exactly the three approved D/E/F evidence artifacts",
        )
    )
    relationships = graph.get("relationships", [])
    effects_safe = all(
        item.get("authority_claim") == "none"
        and item.get("ownership_effect") == "none"
        and item.get("permission_effect") == "none"
        and item.get("action_effect") == "none"
        and item.get("review_state") == "unreviewed"
        for item in relationships
    ) and all(
        graph.get(key) == "none"
        for key in ("authority_effect", "ownership_effect", "permission_effect", "action_effect")
    )
    checks.append(
        Check(
            "PASS" if effects_safe else "FAIL",
            "relationship.security",
            "relationships remain unreviewed evidence with no authority, ownership, permission, or action effect",
        )
    )
    conflict_safe = all(
        item.get("resolution_state") == "unresolved"
        and item.get("automatic_resolution") is False
        for item in graph.get("conflicts", [])
    )
    drift_safe = all(
        item.get("result") == "relationship_changed"
        and item.get("automatic_deletion") is False
        for item in graph.get("drift_events", [])
    )
    checks.append(
        Check(
            "PASS" if conflict_safe and drift_safe else "FAIL",
            "relationship.conflict_drift",
            "conflicts remain unresolved and drift never deletes prior relationships",
        )
    )

    audit_errors = [
        error for event in audit.get("events", []) for error in audit_event_errors(event)
    ]
    expected_types = {"relationship_created", "relationship_validated"}
    actual_types = {event.get("event_type") for event in audit.get("events", [])}
    expected_targets = {item["relationship_id"] for item in relationships}
    created_targets = {
        event.get("target_ref")
        for event in audit.get("events", [])
        if event.get("event_type") == "relationship_created"
    }
    validated_targets = {
        event.get("target_ref")
        for event in audit.get("events", [])
        if event.get("event_type") == "relationship_validated"
    }
    if (
        audit.get("run_id") != run_id
        or actual_types != expected_types
        or created_targets != expected_targets
        or validated_targets != expected_targets
        or len(audit.get("events", [])) != 2 * len(relationships)
    ):
        audit_errors.append("Phase G relationship audit event set is incomplete")
    checks.append(
        Check(
            "PASS" if not audit_errors else "FAIL",
            "relationship.audit",
            "every relationship has one creation and one validation audit event"
            if not audit_errors
            else audit_errors[0],
        )
    )
    checks.append(
        Check(
            "PASS"
            if len(graph.get("nodes", [])) <= config["limits"]["max_nodes"]
            and len(relationships) <= config["limits"]["max_relationships"]
            else "FAIL",
            "relationship.limits",
            "graph remains within the 12-node and 10-relationship pilot limits",
        )
    )
    return checks


def run_validation(run_id: str | None = None) -> list[Check]:
    config = load_json(CONFIG_PATH)
    policy = load_json(POLICY_PATH)
    errors = relationship_config_errors(config, policy)
    actual_inputs = {
        (item["phase"], item["run_id"], item["artifact_ref"])
        for item in config.get("evidence_inputs", [])
    }
    checks = [
        Check(
            "PASS" if not errors else "FAIL",
            "relationship.configuration",
            "Phase G configuration is explicit, deterministic, and non-operational"
            if not errors
            else errors[0],
        ),
        Check(
            "PASS"
            if set(policy.get("supported_node_types", [])) == NODE_TYPES
            and set(policy.get("supported_relationship_types", [])) == RELATIONSHIP_TYPES
            and set(policy.get("supported_assertion_types", [])) == ASSERTION_TYPES
            else "FAIL",
            "relationship.model",
            "policy declares exactly 12 node, 10 relationship, and 4 assertion types",
        ),
        Check(
            "PASS" if actual_inputs == EXPECTED_EVIDENCE_INPUTS else "FAIL",
            "relationship.explicit_inputs",
            "only the approved existing Phase D/E/F artifacts are inputs",
        ),
        Check(
            "PASS"
            if not policy.get("automatic_discovery_enabled")
            and not policy.get("automatic_authority_enabled")
            and not policy.get("automatic_resolution_enabled")
            and not policy.get("action_relationships_enabled")
            and all(value == "none" for value in policy.get("effects", {}).values())
            else "FAIL",
            "relationship.no_authority_action",
            "discovery, authority, resolution, and actions are disabled",
        ),
    ]
    if not errors:
        inputs = load_evidence_inputs(config)
        source_errors = source_evidence_errors(inputs)
        checks.append(
            Check(
                "PASS" if not source_errors else "FAIL",
                "relationship.source_evidence",
                "the exact D/E/F artifacts remain valid evidence"
                if not source_errors
                else source_errors[0],
            )
        )
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
        print(f"FAIL: relationship.validation: {exc}")
        return 1
    counts = {level: 0 for level in ("PASS", "WARN", "FAIL")}
    for check in checks:
        counts[check.level] += 1
        print(f"{check.level}: {check.code}: {check.message}")
    print(f"Summary: PASS={counts['PASS']} WARN={counts['WARN']} FAIL={counts['FAIL']}")
    return 1 if counts["FAIL"] else 0


if __name__ == "__main__":
    sys.exit(main())
