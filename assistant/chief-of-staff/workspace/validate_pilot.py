#!/usr/bin/env python3
"""Validate the Phase D pilot definition and one explicitly named local run."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pilot import (
    APPROVED_OUTPUT_ROOT,
    CONFIG_PATH,
    CONFIG_SCHEMA_PATH,
    RELATIONSHIP_SCHEMA_PATH,
    ROOT,
    pilot_config_errors,
    validate_observation_batch,
)
from validate import SchemaValidationError, load_json, validate_schema
from validate_observation import audit_event_errors, inventory_run_errors


RUN_ID_PATTERN = re.compile(r"^run:history-project-metadata-pilot-[a-z0-9-]+$")


@dataclass(frozen=True)
class Check:
    level: str
    code: str
    message: str


def _load_wrapper(path: Path, expected_keys: set[str]) -> dict[str, Any]:
    value = load_json(path)
    if set(value) != expected_keys:
        raise ValueError(f"{path.name}: unexpected wrapper fields")
    return value


def validate_run(run_id: str) -> list[Check]:
    if RUN_ID_PATTERN.fullmatch(run_id) is None:
        return [Check("FAIL", "pilot.run_id", "run ID is not a Phase D pilot ID")]

    run_path = APPROVED_OUTPUT_ROOT / "inventory-runs" / f"{run_id}.json"
    observation_path = APPROVED_OUTPUT_ROOT / "observations" / f"{run_id}.json"
    audit_path = APPROVED_OUTPUT_ROOT / "audit" / f"{run_id}.json"
    run = load_json(run_path)
    observations = _load_wrapper(
        observation_path,
        {
            "schema_version",
            "run_id",
            "source_id",
            "observations",
            "relationship_preparation",
        },
    )
    audit = _load_wrapper(audit_path, {"schema_version", "run_id", "events"})

    run_errors = inventory_run_errors(run)
    checks = [
        Check(
            "PASS" if not run_errors else "FAIL",
            "pilot.inventory_run",
            "live inventory run matches the Phase C contract"
            if not run_errors
            else run_errors[0],
        )
    ]
    config = load_json(CONFIG_PATH)
    batch_errors = validate_observation_batch(
        observations["observations"],
        run_id=run_id,
        source_id=config["source_id"],
        max_items=config["limits"]["max_items"],
    )
    if observations["run_id"] != run_id or observations["source_id"] != config["source_id"]:
        batch_errors.append("observation wrapper provenance mismatch")
    checks.append(
        Check(
            "PASS" if not batch_errors else "FAIL",
            "pilot.observations",
            "live observations are bounded metadata-only evidence"
            if not batch_errors
            else batch_errors[0],
        )
    )

    relationship_errors: list[str] = []
    if len(observations["relationship_preparation"]) != 1:
        relationship_errors.append("exactly one relationship preparation record required")
    else:
        try:
            validate_schema(
                observations["relationship_preparation"][0],
                load_json(RELATIONSHIP_SCHEMA_PATH),
            )
        except (SchemaValidationError, TypeError) as exc:
            relationship_errors.append(str(exc))
    checks.append(
        Check(
            "PASS" if not relationship_errors else "FAIL",
            "pilot.relationship_preparation",
            "relationship evidence is unreviewed and non-authoritative"
            if not relationship_errors
            else relationship_errors[0],
        )
    )

    audit_errors = [
        error for event in audit["events"] for error in audit_event_errors(event)
    ]
    event_types = {event.get("event_type") for event in audit["events"]}
    expected_events = {
        "observation_started",
        "observation_completed",
        "validation_passed",
    }
    if audit["run_id"] != run_id or event_types != expected_events:
        audit_errors.append("successful run audit event set is incomplete")
    checks.append(
        Check(
            "PASS" if not audit_errors else "FAIL",
            "pilot.audit",
            "live audit records start, completion, and validation"
            if not audit_errors
            else audit_errors[0],
        )
    )

    status_ok = run["status"] == "completed" and run["errors"] == []
    checks.append(
        Check(
            "PASS" if status_ok else "FAIL",
            "pilot.status",
            "live pilot completed without warnings or errors",
        )
    )
    return checks


def run_validation(run_id: str | None = None) -> list[Check]:
    config = load_json(CONFIG_PATH)
    config_errors = pilot_config_errors(config)
    storage_sources = load_json(ROOT / "registry/storage-sources.json")
    registered_source_ids = {item["id"] for item in storage_sources["sources"]}
    checks = [
        Check(
            "PASS" if not config_errors else "FAIL",
            "pilot.configuration",
            "single history pilot is explicit, bounded, and non-mutating"
            if not config_errors
            else config_errors[0],
        ),
        Check(
            "PASS"
            if CONFIG_SCHEMA_PATH.is_file() and RELATIONSHIP_SCHEMA_PATH.is_file()
            else "FAIL",
            "pilot.contracts",
            "pilot and relationship-evidence contracts are present",
        ),
        Check(
            "PASS" if config["parent_source_id"] in registered_source_ids else "FAIL",
            "pilot.source_registration",
            "pilot source is scoped beneath the registered projects-local source",
        ),
    ]
    if run_id and all(check.level == "PASS" for check in checks):
        checks.extend(validate_run(run_id))
    return checks


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id")
    args = parser.parse_args()
    try:
        checks = run_validation(args.run_id)
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        print(f"FAIL: pilot.validation: {exc}")
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
