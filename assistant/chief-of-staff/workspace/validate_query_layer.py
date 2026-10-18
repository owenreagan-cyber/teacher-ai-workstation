#!/usr/bin/env python3
"""Validate the deterministic, read-only Phase J query and explanation layer."""

from __future__ import annotations

import copy
import json
import sys
import time
from dataclasses import dataclass

from ai_compatibility import ai_view_errors, project_ai_compatibility_view
from query_layer import (
    DeterministicQueryLayer,
    QuerySecurityError,
    explanation_errors,
    load_query_model,
    load_query_policy,
    make_query,
    query_errors,
    query_policy_errors,
    response_errors,
    uncertainty_errors,
)


@dataclass(frozen=True)
class Check:
    level: str
    code: str
    message: str


def _check(level: bool, code: str, success: str, failure: str) -> Check:
    return Check("PASS" if level else "FAIL", code, success if level else failure)


def run_validation() -> list[Check]:
    policy = load_query_policy()
    policy_failures = query_policy_errors(policy)
    model = load_query_model(policy)
    layer = DeterministicQueryLayer(model)
    checks = [
        _check(
            not policy_failures,
            "query.policy",
            "policy pins the exact registries and D/E/F/G evidence artifacts",
            policy_failures[0] if policy_failures else "policy validation failed",
        )
    ]

    query = make_query(
        "entity_lookup", "project:history", query_id="query:validation:history",
        created_at="2026-09-13T12:00:00Z",
    )
    response = layer.execute(query)
    checks.append(_check(
        not query_errors(query) and not response_errors(response) and len(response["results"]) == 1,
        "query.lookup", "valid entity lookup returns a schema-valid deterministic response",
        "valid entity lookup failed",
    ))

    unknown = layer.explain("entity:not-present")
    checks.append(_check(
        unknown["subject_type"] == "unknown" and bool(unknown["uncertainties"]),
        "query.unknown", "unknown identity remains visible uncertainty rather than failure",
        "unknown identity was hidden or promoted",
    ))

    application = layer.explain("application:grade-4-writing-launcher")
    checks.append(_check(
        not explanation_errors(application)
        and bool(application["sources"])
        and bool(application["evidence_packages"])
        and application["confidence"] == "high"
        and application["review_state"] == "unreviewed",
        "explanation.contract", "explanation includes sources, evidence, confidence, review, and uncertainty",
        "application explanation is incomplete or invalid",
    ))

    related_first = layer.related_to("application:grade-4-writing-launcher")
    related_second = layer.related_to("application:grade-4-writing-launcher")
    checks.append(_check(
        related_first == related_second
        and [item["relationship_id"] for item in related_first]
        == sorted(item["relationship_id"] for item in related_first)
        and all(item["provenance"] and item["authority_effect"] == "none" for item in related_first),
        "relationship.explorer", "relationship traversal is ordered and preserves provenance without authority",
        "relationship ordering, provenance, or authority boundary failed",
    ))

    conflict_model = copy.deepcopy(model)
    conflict_relationship_id = conflict_model["relationships"][0]["relationship_id"]
    conflict_model["conflicts"] = [{
        "conflict_id": "relationship-conflict:validation",
        "subject_ref": "project:history",
        "candidate_refs": [conflict_relationship_id, "relationship:validation:alternate"],
    }]
    conflict_layer = DeterministicQueryLayer(conflict_model)
    conflict_relationships = conflict_layer.related_to("project:history")
    conflict_explanation = conflict_layer.explain("project:history")
    checks.append(_check(
        any("relationship-conflict:validation" in item["conflicts"] for item in conflict_relationships)
        and any("relationship-conflict:validation" in item for item in conflict_explanation["uncertainties"]),
        "relationship.conflicts", "unresolved conflicts appear in traversal and explanation output",
        "relationship conflicts were hidden",
    ))

    evidence = layer.why("project:history")
    checks.append(_check(
        bool(evidence)
        and all(item["provenance"] for item in evidence)
        and all(item["action_authority"] == "none" for item in evidence),
        "evidence.explorer", "evidence lookup preserves provenance, confidence, review, and no-action state",
        "evidence explorer is incomplete or exposes action authority",
    ))

    uncertainty = layer.uncertain()
    checks.append(_check(
        bool(uncertainty)
        and all(not uncertainty_errors(item) for item in uncertainty)
        and all(item["interpretation"] == "review_opportunity_not_failure" for item in uncertainty),
        "uncertainty.explorer", "unresolved items are schema-valid review opportunities, not failures",
        "uncertainty explorer failed",
    ))

    recovery = layer.execute(make_query("recovery_candidate_lookup", "resource:writing"))
    checks.append(_check(
        recovery["results"] == []
        and "disabled" in recovery["uncertainties"][0]
        and recovery["action_authority"] == "none",
        "recovery.live_boundary", "live recovery returns no candidates and exposes no action",
        "live recovery boundary failed",
    ))

    synthetic = copy.deepcopy(model)
    synthetic["recovery_candidates"] = [{
        "candidate_id": "recovery-candidate:validation",
        "subject_ref": "registry-system:writing",
        "candidate_ref": "representation:validation:backup",
        "evidence": ["explicit_backup_relationship"],
        "confidence": "high",
        "risk": "medium",
        "next_step": "Teacher review required.",
        "review_state": "unreviewed",
    }]
    recovery_candidate = DeterministicQueryLayer(synthetic).recovery_candidates("resource:writing")[0]
    checks.append(_check(
        recovery_candidate["risk"] == "medium"
        and recovery_candidate["next_step"] == "Teacher review required."
        and recovery_candidate["action_authority"] == "none",
        "recovery.explanation", "synthetic candidate displays evidence, confidence, risk, and next step only",
        "recovery explanation or no-action boundary failed",
    ))

    restricted = copy.deepcopy(model)
    restricted["entities"]["project:history"]["classification"] = "restricted"
    restricted_layer = DeterministicQueryLayer(restricted)
    blocked = False
    try:
        restricted_layer.explain("project:history")
    except QuerySecurityError:
        blocked = True
    checks.append(_check(
        blocked,
        "security.restricted", "restricted data fails closed without workspace.restricted.read",
        "restricted data was exposed without its explicit grant",
    ))

    checks.append(_check(
        not policy["ai_enabled"]
        and not policy["live_recovery_candidates_enabled"]
        and policy["action_capabilities"] == []
        and application["action_authority"] == "none",
        "security.no_ai_actions", "AI, live recovery, action capabilities, and action authority remain disabled",
        "an AI or action capability is enabled",
    ))

    internal = layer.ai_compatibility_input("application:grade-4-writing-launcher")
    view = project_ai_compatibility_view(internal)
    checks.append(_check(
        not ai_view_errors(view)
        and not view["trust"]["authoritative"]
        and not view["trust"]["executable"]
        and view["action_capabilities"] == [],
        "ai.compatibility_boundary", "Phase I sanitizes Phase J explanation structures without an AI connection",
        "Phase J cannot safely pass through the Phase I compatibility boundary",
    ))

    source = (__import__("pathlib").Path(__file__).resolve().parent / "query_layer.py").read_text(encoding="utf-8")
    forbidden = (
        "os.walk", ".rglob(", ".glob(", ".iterdir(", "subprocess", "requests", "urllib",
        "socket", "shutil", "os.remove", "os.rename", "os.replace",
    )
    checks.append(_check(
        all(token not in source for token in forbidden),
        "security.no_discovery_execution", "implementation has no discovery, network, or filesystem mutation primitive",
        "implementation contains a forbidden discovery, network, or mutation primitive",
    ))

    start = time.perf_counter()
    for _ in range(100):
        layer.explain("application:grade-4-writing-launcher")
        layer.related_to("project:history")
        layer.why("project:history")
        layer.uncertain()
    runtime = time.perf_counter() - start
    checks.append(_check(
        runtime < 5.0,
        "performance.simple_structures", f"400 in-memory operations completed in {runtime:.4f}s without cache or service",
        f"simple deterministic operations took {runtime:.4f}s",
    ))
    return checks


def main() -> int:
    try:
        checks = run_validation()
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        print(f"FAIL: query.validation: {exc}")
        return 1
    counts = {level: 0 for level in ("PASS", "WARN", "FAIL")}
    for check in checks:
        counts[check.level] += 1
        print(f"{check.level}: {check.code}: {check.message}")
    print(f"Summary: PASS={counts['PASS']} WARN={counts['WARN']} FAIL={counts['FAIL']}")
    return 1 if counts["FAIL"] else 0


if __name__ == "__main__":
    sys.exit(main())
