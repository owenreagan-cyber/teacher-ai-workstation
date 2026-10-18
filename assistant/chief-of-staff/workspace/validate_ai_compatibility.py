#!/usr/bin/env python3
"""Validate the synthetic-only Phase I AI compatibility architecture."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass

from ai_compatibility import (
    ROOT,
    ai_policy_errors,
    ai_view_errors,
    explain,
    load_ai_policy,
    project_ai_compatibility_view,
    synthetic_internal_model,
)
from validate import load_json


@dataclass(frozen=True)
class Check:
    level: str
    code: str
    message: str


def run_validation() -> list[Check]:
    policy = load_ai_policy()
    policy_errors = ai_policy_errors(policy)
    checks = [
        Check(
            "PASS" if not policy_errors else "FAIL",
            "ai.policy",
            "AI trust policy is read-only, non-authoritative, non-executable, and disconnected"
            if not policy_errors
            else policy_errors[0],
        )
    ]
    base_sanitization = load_json(ROOT / "registry/sanitization.json")
    inherited_forbidden = set(base_sanitization["local_only_fields"]) | set(
        base_sanitization["forbidden_export_fields"]
    )
    checks.append(
        Check(
            "PASS" if inherited_forbidden <= set(policy["forbidden_fields"]) else "FAIL",
            "ai.sanitization_inheritance",
            "Phase I preserves every Phase C local-only and forbidden export field",
        )
    )
    internal = synthetic_internal_model()
    view = project_ai_compatibility_view(internal, policy)
    projection_errors = ai_view_errors(view, policy)
    checks.append(
        Check(
            "PASS" if not projection_errors else "FAIL",
            "ai.projection",
            "synthetic internal metadata produces a closed sanitized projection"
            if not projection_errors
            else projection_errors[0],
        )
    )
    explanation = explain(view, "application-concept:grade-4-writing-launcher")
    identity_preserved = (
        explanation["authority"] == "unknown"
        and explanation["confidence"] == "high"
        and explanation["review_state"] == "unreviewed"
        and explanation["action_authority"] == "none"
    )
    checks.append(
        Check(
            "PASS" if identity_preserved else "FAIL",
            "ai.identity_uncertainty",
            "identity, authority, confidence, review state, and uncertainty remain explicit",
        )
    )
    checks.append(
        Check(
            "PASS"
            if not view["action_capabilities"]
            and not view["trust"]["authoritative"]
            and not view["trust"]["executable"]
            else "FAIL",
            "ai.no_actions",
            "projection exposes no authority mutation or action capability",
        )
    )
    checks.append(
        Check(
            "PASS"
            if policy["ai_connection_enabled"] is False
            and policy["raw_observation_export_enabled"] is False
            else "FAIL",
            "ai.no_connection_export",
            "no AI connection exists and raw observation export is disabled",
        )
    )
    return checks


def main() -> int:
    try:
        checks = run_validation()
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        print(f"FAIL: ai.validation: {exc}")
        return 1
    counts = {level: 0 for level in ("PASS", "WARN", "FAIL")}
    for check in checks:
        counts[check.level] += 1
        print(f"{check.level}: {check.code}: {check.message}")
    print(f"Summary: PASS={counts['PASS']} WARN={counts['WARN']} FAIL={counts['FAIL']}")
    return 1 if counts["FAIL"] else 0


if __name__ == "__main__":
    sys.exit(main())
