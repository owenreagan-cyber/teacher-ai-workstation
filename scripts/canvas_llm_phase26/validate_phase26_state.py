from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.canvas_llm_phase22.phase22_workstation import WorkstationDB  # noqa: E402
from scripts.canvas_llm_phase26.pipeline import (  # noqa: E402
    build_workstation_packet,
    validate_workstation_packet,
)


def print_validation(validation: dict) -> None:
    for finding in validation["findings"]:
        print(
            f"{finding['severity'].upper()}: "
            f"{finding['code']} {finding['message']}"
        )
    print(f"PASS: {validation['passCount']}")
    print(f"WARN: {validation['warnCount']}")
    print(f"FAIL: {validation['failCount']}")


def run_sqlite_math_regression() -> int:
    root = Path(tempfile.mkdtemp())
    phase22_db_path = root / "phase22.sqlite3"
    phase26_db_path = root / "phase26.sqlite3"

    db = WorkstationDB(phase22_db_path)
    db.migrate()

    week_id = db.create_week("2026-08-17")
    week = db.get_week(week_id)
    math = next(
        subject
        for subject in week["subjects"]
        if subject["subject"] == "math"
    )

    updates = [
        {
            "lesson": "18",
            "title": "Lesson 18",
            "in_class": "Lesson 18",
            "at_home": "Evens",
        },
        {
            "lesson": "19",
            "title": "Lesson 19",
            "in_class": "Lesson 19",
            "at_home": "Odds",
        },
        {
            "lesson": "20",
            "title": "Lesson 20",
            "in_class": "Lesson 20",
            "at_home": "Evens",
        },
        {
            "tests": "4",
            "title": "Written Test 4",
            "in_class": "Written Test 4 and Fact Test 4",
        },
        {
            "lesson": "21",
            "title": "Lesson 21",
            "in_class": "Lesson 21",
        },
    ]

    for day, fields in zip(math["days"], updates):
        result = db.patch_table(
            "daily_subject_entries",
            day["id"],
            fields,
            day["version"],
        )
        assert not result.get("conflict")

    packet = build_workstation_packet(
        "Q1W5",
        phase26_db_path,
        source_mode="sqlite",
        phase22_db_path=phase22_db_path,
    )

    production = packet["productionPacket"]
    validation = packet["validation"]

    titles = {
        item["title"]
        for item in production["assignments"]
    }

    expected_titles = {
        "SM5: Lesson 18",
        "SM5: Lesson 19",
        "SM5: Lesson 20",
        "SM5: Study Guide 4",
        "SM5: Math Test 4",
        "SM5: Fact Test 4",
        "SM5: Lesson 21",
    }

    reading_findings = [
        item
        for item in validation["findings"]
        if item["code"].startswith("reading")
    ]

    assert packet["sourceMode"] == "sqlite"
    assert production["sourceKind"] == "sqlite"
    assert production["deploymentState"] == "preview-only"
    assert production["containsStudentData"] is False
    assert production["validation"]["failCount"] == 0
    assert validation["failCount"] == 0
    assert reading_findings == []
    assert titles == expected_titles
    assert len(production["pages"]) == 1
    assert production["pages"][0]["subject_group"] == "math"
    assert packet["localState"]["weekState"]["source_mode"] == "sqlite"
    assert all(
        item.get("source_type") != "fixture"
        for item in production["provenance"]
    )

    print("PASS: Phase 26 SQLite Math regression")
    print("PASS: sourceMode=sqlite")
    print("PASS: productionPacket.sourceKind=sqlite")
    print("PASS: Math assignments originate from Phase 22 SQLite")
    print("PASS: Reading findings=[]")
    print("PASS: deploymentState=preview-only")
    print_validation(validation)

    return 0


def main() -> int:
    if not sys.argv[1:]:
        return run_sqlite_math_regression()

    failures = 0
    for raw in sys.argv[1:]:
        path = Path(raw)
        payload = json.loads(path.read_text(encoding="utf-8"))
        validation = validate_workstation_packet(payload)
        print_validation(validation)
        failures += validation["failCount"]
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

