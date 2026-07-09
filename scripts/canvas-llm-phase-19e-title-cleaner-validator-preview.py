#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PHASE_19D = ROOT / "docs/programs/canvas-llm/phase-19d-seed-rule-catalog-title-cleaner"

EVIDENCE = PHASE_19D / "evidence.json"
RULES = PHASE_19D / "rules.json"
LINKS = PHASE_19D / "links.json"
NORMALIZATION = PHASE_19D / "title-normalization-rules.json"
FIXTURES = PHASE_19D / "title-normalization-fixtures.md"

PASS = 0
WARN = 0
FAIL = 0


def emit(level: str, message: str) -> None:
    global PASS, WARN, FAIL
    if level == "PASS":
        PASS += 1
    elif level == "WARN":
        WARN += 1
    elif level == "FAIL":
        FAIL += 1
    else:
        FAIL += 1
        print(f"FAIL: invalid level {level}: {message}")
        return
    print(f"{level}: {message}")


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text())
    except Exception as exc:
        emit("FAIL", f"{path} failed JSON parse: {exc}")
        return None


def check_file(path: Path, label: str) -> None:
    if path.exists() and path.is_file():
        emit("PASS", f"{label} exists")
    else:
        emit("FAIL", f"{label} missing")


def contains_text(path: Path, needle: str, label: str) -> None:
    if not path.exists():
        emit("FAIL", f"{label}: missing file")
        return
    if needle in path.read_text():
        emit("PASS", label)
    else:
        emit("FAIL", label)


def main() -> int:
    print("Canvas LLM Phase 19E Title Cleaner Validator Preview")
    print("----------------------------------------------------")

    for path, label in [
        (EVIDENCE, "Phase 19D evidence.json"),
        (RULES, "Phase 19D rules.json"),
        (LINKS, "Phase 19D links.json"),
        (NORMALIZATION, "Phase 19D title-normalization-rules.json"),
        (FIXTURES, "Phase 19D title-normalization-fixtures.md"),
    ]:
        check_file(path, label)

    evidence = load_json(EVIDENCE)
    rules = load_json(RULES)
    links = load_json(LINKS)
    normalization = load_json(NORMALIZATION)

    if evidence is not None:
        emit("PASS", "evidence.json parses")
    if rules is not None:
        emit("PASS", "rules.json parses")
    if links is not None:
        emit("PASS", "links.json parses")
    if normalization is not None:
        emit("PASS", "title-normalization-rules.json parses")

    if not all(x is not None for x in [evidence, rules, links, normalization]):
        emit("FAIL", "required JSON could not be fully loaded")
        return summarize()

    evidence_ids = {item.get("evidence_id") for item in evidence.get("evidence", [])}
    rule_ids = {item.get("rule_id") for item in rules.get("rules", [])}
    link_ids = {item.get("link_id") for item in links.get("links", [])}

    if "preview_only" == normalization.get("status"):
        emit("PASS", "normalization status is preview_only")
    else:
        emit("FAIL", "normalization status is preview_only")

    global_behavior = normalization.get("global_behavior", {})
    if global_behavior.get("never_silently_mutate_canvas") is True:
        emit("PASS", "never_silently_mutate_canvas is true")
    else:
        emit("FAIL", "never_silently_mutate_canvas is true")

    if global_behavior.get("ambiguous_input_requires_review") is True:
        emit("PASS", "ambiguous_input_requires_review is true")
    else:
        emit("FAIL", "ambiguous_input_requires_review is true")

    required_patterns = {
        "SM5: Test {number}",
        "SM5: Fact Test {number}",
        "SM5: Study Guide {number}",
        "ELA4: Test {number}",
        "RM4: Test {number}",
        "RM4: Spelling Test {number}",
    }

    normalization_text = NORMALIZATION.read_text()
    rules_text = RULES.read_text()
    fixture_text = FIXTURES.read_text()

    for pattern in sorted(required_patterns):
        if pattern in normalization_text or pattern in rules_text:
            emit("PASS", f"canonical pattern present: {pattern}")
        else:
            emit("FAIL", f"canonical pattern missing: {pattern}")

    if '"canonical_pattern": "SP4:' not in normalization_text and '"canonical_pattern": "SPELL4:' not in normalization_text:
        emit("PASS", "Spelling canonical outputs do not use SP4 or SPELL4")
    else:
        emit("FAIL", "Spelling canonical outputs do not use SP4 or SPELL4")

    fixture_checks = [
        ("SM5 Test 1", "fixture includes SM5 Test close input"),
        ("SM 5: Test 1", "fixture includes spaced SM5 close input"),
        ("SM5 Fact Test 2", "fixture includes Math Fact Test close input"),
        ("SM5 Study Guide 3", "fixture includes Math Study Guide close input"),
        ("ELA4 Test 4", "fixture includes ELA Test close input"),
        ("RM4 Test 5", "fixture includes Reading Test close input"),
        ("Spelling Test 6", "fixture includes Spelling Test close input"),
        ("SP4 Spelling Test 6", "fixture includes SP4 Spelling correction input"),
        ("Test 7", "fixture includes ambiguous Test input"),
        ("needs_review", "fixture includes needs_review confidence"),
    ]

    for needle, label in fixture_checks:
        if needle in fixture_text:
            emit("PASS", label)
        else:
            emit("FAIL", label)

    for normalizer in normalization.get("rules", []):
        rid = normalizer.get("rule_ref")
        nid = normalizer.get("normalizer_id", "unknown normalizer")
        if rid in rule_ids:
            emit("PASS", f"{nid} references known rule {rid}")
        else:
            emit("FAIL", f"{nid} references unknown rule {rid}")

    for rule in rules.get("rules", []):
        rid = rule.get("rule_id", "unknown rule")
        for ev_id in rule.get("evidence_refs", []):
            if ev_id in evidence_ids:
                emit("PASS", f"{rid} evidence ref exists: {ev_id}")
            else:
                emit("FAIL", f"{rid} evidence ref missing: {ev_id}")

    for link in links.get("links", []):
        lid = link.get("link_id", "unknown link")
        if lid in link_ids:
            emit("PASS", f"{lid} has stable link ID")
        else:
            emit("FAIL", "link missing stable link ID")

        from_id = link.get("from_id")
        to_id = link.get("to_id")

        if from_id in evidence_ids or from_id in rule_ids:
            emit("PASS", f"{lid} source ID resolves")
        else:
            emit("FAIL", f"{lid} source ID does not resolve: {from_id}")

        if to_id in evidence_ids or to_id in rule_ids:
            emit("PASS", f"{lid} target ID resolves")
        else:
            emit("FAIL", f"{lid} target ID does not resolve: {to_id}")

    blocked_actions = " ".join(global_behavior.get("blocked_actions", []))
    if "canvas_write" in blocked_actions:
        emit("PASS", "normalizer blocks canvas_write")
    else:
        emit("FAIL", "normalizer blocks canvas_write")

    if "student_data_access" in blocked_actions:
        emit("PASS", "normalizer blocks student_data_access")
    else:
        emit("FAIL", "normalizer blocks student_data_access")

    for forbidden in [
        "Canvas API calls",
        "Canvas writes",
        "student data access",
        "raw `.local` metadata reads or commits",
        "school Canvas URL commits",
    ]:
        contains_text(
            ROOT / "docs/programs/canvas-llm/phase-19e-title-cleaner-validator-preview/preview-only-boundary.md",
            forbidden,
            f"Phase 19E boundary blocks {forbidden}",
        )

    emit("PASS", "validator is local preview-only")
    emit("PASS", "validator does not call Canvas APIs")
    emit("PASS", "validator does not fetch live Canvas data")
    emit("PASS", "validator does not write to Canvas")
    emit("PASS", "validator does not access student data")
    emit("PASS", "validator does not read raw .local metadata")
    emit("PASS", "validator does not implement app behavior")

    return summarize()


def summarize() -> int:
    print()
    print("Summary")
    print("-------")
    print(f"PASS: {PASS}")
    print(f"WARN: {WARN}")
    print(f"FAIL: {FAIL}")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
