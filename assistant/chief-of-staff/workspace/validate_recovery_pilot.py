#!/usr/bin/env python3
"""Validate Phase H contracts and in-memory synthetic recovery scenarios."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass

from recovery_pilot import (
    AUDIT_EVENT_TYPES,
    CANDIDATE_TYPES,
    CONFIG_PATH,
    EXPECTED_EVIDENCE_INPUTS,
    EXPECTED_SCENARIOS,
    POLICY_PATH,
    SIGNAL_TYPES,
    build_synthetic_scenarios,
    load_recovery_evidence_inputs,
    recovery_config_errors,
    recovery_source_evidence_errors,
    synthetic_scenario_errors,
)
from evidence_model import expected_artifact_errors, synthetic_math_expected_artifacts
from validate import load_json


@dataclass(frozen=True)
class Check:
    level: str
    code: str
    message: str


def run_validation() -> list[Check]:
    config = load_json(CONFIG_PATH)
    policy = load_json(POLICY_PATH)
    errors = recovery_config_errors(config, policy)
    actual_inputs = {
        (item["phase"], item["run_id"], item["artifact_ref"])
        for item in config.get("evidence_inputs", [])
    }
    checks = [
        Check(
            "PASS" if not errors else "FAIL",
            "recovery.configuration",
            "Phase H is synthetic-only, bounded, non-operational, and deterministic"
            if not errors
            else errors[0],
        ),
        Check(
            "PASS"
            if set(policy.get("candidate_types", [])) == CANDIDATE_TYPES
            and set(policy.get("signal_types", [])) == SIGNAL_TYPES
            and set(policy.get("audit_event_types", [])) == AUDIT_EVENT_TYPES
            else "FAIL",
            "recovery.model",
            "policy declares exactly seven candidates, six signals, and four audit events",
        ),
        Check(
            "PASS" if actual_inputs == EXPECTED_EVIDENCE_INPUTS else "FAIL",
            "recovery.explicit_inputs",
            "only the exact existing Phase D/E/F/G artifacts are evidence inputs",
        ),
        Check(
            "PASS" if set(config.get("synthetic_scenarios", [])) == EXPECTED_SCENARIOS else "FAIL",
            "recovery.synthetic_scope",
            "four hypothetical scenarios are declared without live missing-resource detection",
        ),
        Check(
            "PASS"
            if not config.get("host_local_output_enabled")
            and not config.get("live_signal_detection_enabled")
            and not config.get("live_candidate_generation_enabled")
            and not policy.get("recovery_execution_enabled")
            else "FAIL",
            "recovery.no_execution",
            "live detection, live candidates, output writing, and recovery execution are disabled",
        ),
    ]
    if errors:
        return checks
    inputs = load_recovery_evidence_inputs(config)
    evidence_errors = recovery_source_evidence_errors(inputs)
    checks.append(
        Check(
            "PASS" if not evidence_errors else "FAIL",
            "recovery.source_evidence",
            "the exact D/E/F/G artifacts remain valid and non-authoritative"
            if not evidence_errors
            else evidence_errors[0],
        )
    )
    scenarios = build_synthetic_scenarios(inputs)
    scenario_errors = synthetic_scenario_errors(scenarios)
    checks.append(
        Check(
            "PASS" if not scenario_errors else "FAIL",
            "recovery.scenarios",
            "all four in-memory recovery scenarios satisfy candidate, evidence, conflict, and recommendation contracts"
            if not scenario_errors
            else scenario_errors[0],
        )
    )
    all_candidates = [candidate for scenario in scenarios for candidate in scenario["candidates"]]
    checks.append(
        Check(
            "PASS"
            if all(
                item["action_state"] == "not_an_action"
                and item["authority_effect"] == "none"
                and item["authority_context"]["canonical_promotion"] is False
                for item in all_candidates
            )
            else "FAIL",
            "recovery.authority",
            "candidates preserve authority context without promotion or action",
        )
    )
    checks.append(
        Check(
            "PASS"
            if all(
                recommendation["next_step"] == "review_candidate"
                and recommendation["action_state"] == "not_an_action"
                for scenario in scenarios
                for recommendation in scenario["recommendations"]
            )
            else "FAIL",
            "recovery.recommendations",
            "recommendations request review only and never restore",
        )
    )
    expected_artifacts = synthetic_math_expected_artifacts()
    expected_artifact_contract_errors = [
        error
        for relationship in expected_artifacts
        for error in expected_artifact_errors(relationship)
    ]
    checks.append(
        Check(
            "PASS" if not expected_artifact_contract_errors else "FAIL",
            "recovery.expected_artifacts",
            "synthetic expected artifacts declare type, source, confidence, and review state without claiming existence"
            if not expected_artifact_contract_errors
            else expected_artifact_contract_errors[0],
        )
    )
    return checks


def main() -> int:
    try:
        checks = run_validation()
    except (OSError, json.JSONDecodeError, KeyError, StopIteration, TypeError, ValueError) as exc:
        print(f"FAIL: recovery.validation: {exc}")
        return 1
    counts = {level: 0 for level in ("PASS", "WARN", "FAIL")}
    for check in checks:
        counts[check.level] += 1
        print(f"{check.level}: {check.code}: {check.message}")
    print(f"Summary: PASS={counts['PASS']} WARN={counts['WARN']} FAIL={counts['FAIL']}")
    return 1 if counts["FAIL"] else 0


if __name__ == "__main__":
    sys.exit(main())
