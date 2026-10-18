#!/usr/bin/env python3
"""Validate the deterministic, non-executable Phase K human interface."""

from __future__ import annotations

import io
import json
import sys
import time
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import dataclass

from chief import main as chief_main
from human_interface import (
    EXPLANATION_SECTIONS,
    REVIEW_STATES,
    build_interface_status,
    build_review_queue,
    interface_policy_errors,
    interface_status_errors,
    load_interface_policy,
    make_review_item,
    render_evidence,
    render_explanation,
    render_recovery,
    render_relationships,
    render_review_queue,
    render_status,
    review_item_errors,
)
from query_layer import DeterministicQueryLayer


@dataclass(frozen=True)
class Check:
    level: str
    code: str
    message: str


def _check(condition: bool, code: str, success: str, failure: str) -> Check:
    return Check("PASS" if condition else "FAIL", code, success if condition else failure)


def run_validation() -> list[Check]:
    policy = load_interface_policy()
    layer = DeterministicQueryLayer()
    status = build_interface_status(layer)
    queue = build_review_queue(layer)
    checks = [
        _check(
            not interface_policy_errors(policy),
            "interface.policy",
            "CLI-only policy declares six commands, five review states, and no AI or actions",
            "interface policy is invalid",
        ),
        _check(
            not interface_status_errors(status)
            and [item["name"] for item in status["systems"]]
            == ["Resource Registry", "Workspace Model", "Relationships", "Recovery"],
            "interface.status",
            "status reports registry, workspace, relationship, recovery, validation, and authority health",
            "status contract or system health output is invalid",
        ),
        _check(
            bool(status["available_systems"])
            and status["known_entities"] == len(layer.entities)
            and status["unresolved_items"] == len(queue),
            "interface.inventory",
            "status exposes available systems, known-entity count, and unresolved-item count",
            "status inventory counts are inconsistent",
        ),
    ]

    explanation = layer.explain("application:grade-4-writing-launcher")
    evidence = layer.why("application:grade-4-writing-launcher")
    relationships = layer.related_to("application:grade-4-writing-launcher")
    rendered_explanation = render_explanation(explanation, evidence, relationships)
    headings = {section.replace("_", " ").upper() for section in EXPLANATION_SECTIONS}
    checks.append(_check(
        all(heading in rendered_explanation for heading in headings)
        and explanation["action_authority"] == "none",
        "interface.explain",
        "explanation distinguishes identity, known facts, sources, evidence, relationships, confidence, authority, review, unknowns, and actions",
        "human explanation sections or no-action state are incomplete",
    ))

    unknown = layer.explain("entity:not-present")
    rendered_unknown = render_explanation(unknown, [], [])
    checks.append(_check(
        unknown["subject_type"] == "unknown"
        and "Type: unknown" in rendered_unknown
        and "None available." in rendered_unknown,
        "interface.unknown",
        "unknown identity remains a readable uncertainty rather than a failure",
        "unknown identity was hidden or promoted",
    ))

    rendered_relationships = render_relationships(
        "application:grade-4-writing-launcher", relationships,
        ["Relationship assertions remain unreviewed."],
    )
    checks.append(_check(
        all(token in rendered_relationships for token in ("RELATIONSHIPS", "EVIDENCE", "CONFIDENCE", "AUTHORITY", "ACTIONS")),
        "interface.relationships",
        "relationship view shows related entities, type, direction, evidence, confidence, and no authority",
        "relationship presentation is incomplete",
    ))

    rendered_evidence = render_evidence(
        "application:grade-4-writing-launcher", evidence,
        ["Evidence packages remain unreviewed."],
    )
    checks.append(_check(
        all(token in rendered_evidence for token in ("SOURCES / OBSERVATIONS", "PROVENANCE", "CONFIDENCE", "UNKNOWNS", "ACTIONS")),
        "interface.evidence",
        "evidence view shows packages, observations, provenance, confidence, uncertainty, and no actions",
        "evidence presentation is incomplete",
    ))

    rendered_queue = render_review_queue(queue)
    checks.append(_check(
        bool(queue)
        and [item["item_id"] for item in queue] == sorted(item["item_id"] for item in queue)
        and all(not review_item_errors(item) for item in queue)
        and all(item["recommendation_state"] == "not_an_action" for item in queue)
        and "ACTIONS\nNone available." in rendered_queue,
        "interface.review_queue",
        "review queue is ordered, evidence-linked, non-authoritative, and non-executable",
        "review queue contract, ordering, or action boundary failed",
    ))

    state_items = [
        make_review_item(
            f"review-item:validation:{state}", f"entity:{state}", "unknown_authority",
            f"Synthetic {state} state.", confidence="high", review_state=state,
        )
        for state in sorted(REVIEW_STATES)
    ]
    checks.append(_check(
        {item["review_state"] for item in state_items} == REVIEW_STATES
        and {item["confidence"] for item in state_items} == {"high"},
        "interface.review_states",
        "unreviewed, reviewed, approved, rejected, and deferred remain distinct from confidence",
        "review state collapsed into confidence or lost a supported state",
    ))

    recovery = render_recovery(
        "resource:synthetic",
        [{
            "candidate": "representation:synthetic:backup",
            "evidence": ["explicit_backup_relationship"],
            "confidence": "high",
            "risk": "medium",
            "next_step": "Teacher review required.",
            "review_state": "unreviewed",
            "action_authority": "none",
        }],
        [],
    )
    checks.append(_check(
        "confidence high; risk medium" in recovery
        and "Teacher review required." in recovery
        and "None available; restore, copy, and move are not implemented." in recovery,
        "interface.recovery",
        "recovery view displays candidate evidence, confidence, risk, and next step without execution",
        "recovery presentation or no-action boundary failed",
    ))

    checks.append(_check(
        not policy["web_interface_enabled"]
        and not policy["persistent_service_enabled"]
        and not policy["natural_language_enabled"]
        and not policy["ai_enabled"]
        and not policy["source_write_enabled"]
        and policy["action_capabilities"] == []
        and status["actions"] == [],
        "interface.security",
        "web service, natural language, AI, source writes, and action capabilities remain disabled",
        "a prohibited Phase K capability is enabled",
    ))

    commands = [
        ["status"], ["explain", "project:history"], ["related", "project:history"],
        ["evidence", "project:history"], ["uncertain"], ["recovery", "project:history"],
    ]
    command_results = []
    for command in commands:
        output = io.StringIO()
        with redirect_stdout(output), redirect_stderr(io.StringIO()):
            code = chief_main(command, layer=layer)
        command_results.append((code, output.getvalue()))
    checks.append(_check(
        all(code == 0 and "ACTIONS" in output for code, output in command_results),
        "interface.cli",
        "all six deterministic CLI commands produce human output with an explicit action boundary",
        "one or more CLI commands failed or hid the action boundary",
    ))

    first_status = render_status(status)
    checks.append(_check(
        first_status == render_status(status)
        and rendered_explanation == render_explanation(explanation, evidence, relationships),
        "interface.determinism",
        "identical status and explanation inputs produce byte-identical output",
        "human formatting is nondeterministic",
    ))

    started = time.perf_counter()
    for _ in range(1000):
        render_status(status)
        render_explanation(explanation, evidence, relationships)
        render_review_queue(queue)
    runtime = time.perf_counter() - started
    checks.append(_check(
        runtime < 5.0,
        "interface.performance",
        f"3,000 in-memory formatting operations completed in {runtime:.4f}s without a service or cache",
        f"simple deterministic formatting took {runtime:.4f}s",
    ))
    return checks


def main() -> int:
    try:
        checks = run_validation()
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        print(f"FAIL: interface.validation: {exc}")
        return 1
    counts = {level: 0 for level in ("PASS", "WARN", "FAIL")}
    for check in checks:
        counts[check.level] += 1
        print(f"{check.level}: {check.code}: {check.message}")
    print(f"Summary: PASS={counts['PASS']} WARN={counts['WARN']} FAIL={counts['FAIL']}")
    return 1 if counts["FAIL"] else 0


if __name__ == "__main__":
    sys.exit(main())
