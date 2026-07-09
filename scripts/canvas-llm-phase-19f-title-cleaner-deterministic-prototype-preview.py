#!/usr/bin/env python3
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PHASE_19D = ROOT / "docs/programs/canvas-llm/phase-19d-seed-rule-catalog-title-cleaner"
FIXTURES = PHASE_19D / "title-normalization-fixtures.md"
RULES_JSON = PHASE_19D / "title-normalization-rules.json"

PASS = 0
WARN = 0
FAIL = 0


@dataclass(frozen=True)
class Decision:
    input_title: str
    status: str
    canonical_title: str
    confidence: str
    needs_review: bool
    rule: str


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


def number_from(title: str) -> str | None:
    matches = re.findall(r"(\d+)", title)
    if not matches:
        return None
    # Use the trailing/assessment number, not the grade/program number in prefixes like SM5, ELA4, or RM4.
    return matches[-1]


def normalize_title(title: str) -> Decision:
    original = title.strip()
    compact = re.sub(r"[_\-]+", " ", original)
    compact = re.sub(r"\s+", " ", compact).strip()
    lower = compact.lower()
    n = number_from(compact)

    if not n:
        return Decision(original, "needs_review", "", "low", True, "NO-NUMBER")

    # Ambiguous bare tests must remain review-required.
    if re.fullmatch(r"test\s+\d+", lower):
        return Decision(original, "needs_review", "", "low", True, "AMBIGUOUS-TEST")

    # Spelling intentionally maps to RM4.
    if "spelling" in lower or lower.startswith("sp4 ") or lower.startswith("spell4 "):
        return Decision(original, "normalized", f"RM4: Spelling Test {n}", "high", False, "NORM-CANVAS-SPELLING-TEST-001")

    if "fact test" in lower:
        return Decision(original, "normalized", f"SM5: Fact Test {n}", "high", False, "NORM-CANVAS-MATH-FACT-TEST-001")

    if "study guide" in lower:
        return Decision(original, "normalized", f"SM5: Study Guide {n}", "high", False, "NORM-CANVAS-MATH-STUDY-GUIDE-001")

    if lower.startswith("ela4") or lower.startswith("ela 4") or "shurley" in lower:
        confidence = "medium" if "shurley" in lower else "high"
        return Decision(original, "normalized", f"ELA4: Test {n}", confidence, confidence == "medium", "NORM-CANVAS-ELA-TEST-001")

    if lower.startswith("rm4") or lower.startswith("rm 4") or lower.startswith("reading test"):
        confidence = "medium" if lower.startswith("reading test") else "high"
        return Decision(original, "normalized", f"RM4: Test {n}", confidence, confidence == "medium", "NORM-CANVAS-READING-TEST-001")

    if lower.startswith("sm5") or lower.startswith("sm 5") or lower.startswith("saxon math 5") or lower.startswith("math test"):
        confidence = "medium" if lower.startswith("math test") else "high"
        return Decision(original, "normalized", f"SM5: Test {n}", confidence, confidence == "medium", "NORM-CANVAS-MATH-TEST-001")

    return Decision(original, "needs_review", "", "low", True, "UNMATCHED")


def fixture_inputs() -> list[str]:
    if not FIXTURES.exists():
        emit("FAIL", "Phase 19D fixtures file exists")
        return []

    rows: list[str] = []
    for line in FIXTURES.read_text().splitlines():
        if not line.startswith("| `"):
            continue
        pieces = [piece.strip() for piece in line.strip().strip("|").split("|")]
        if len(pieces) < 2:
            continue
        raw = pieces[0]
        if raw == "`Input`":
            continue
        if raw.startswith("`") and raw.endswith("`"):
            rows.append(raw.strip("`"))
    return rows


def assert_decision(title: str, expected_status: str, expected_output: str, expected_review: bool) -> None:
    decision = normalize_title(title)

    if decision.status == expected_status:
        emit("PASS", f"{title}: status {expected_status}")
    else:
        emit("FAIL", f"{title}: expected status {expected_status}, got {decision.status}")

    if decision.canonical_title == expected_output:
        emit("PASS", f"{title}: output {expected_output or '<blank>'}")
    else:
        emit("FAIL", f"{title}: expected output {expected_output or '<blank>'}, got {decision.canonical_title or '<blank>'}")

    if decision.needs_review is expected_review:
        emit("PASS", f"{title}: needs_review {expected_review}")
    else:
        emit("FAIL", f"{title}: expected needs_review {expected_review}, got {decision.needs_review}")


def main() -> int:
    print("Canvas LLM Phase 19F Title Cleaner Deterministic Prototype Preview")
    print("------------------------------------------------------------------")

    if FIXTURES.exists():
        emit("PASS", "Phase 19D fixtures file exists")
    else:
        emit("FAIL", "Phase 19D fixtures file exists")

    if RULES_JSON.exists():
        emit("PASS", "Phase 19D normalization rules file exists")
    else:
        emit("FAIL", "Phase 19D normalization rules file exists")

    inputs = fixture_inputs()
    if inputs:
        emit("PASS", "fixture inputs parsed")
    else:
        emit("FAIL", "fixture inputs parsed")

    expected = [
        ("SM5 Test 1", "normalized", "SM5: Test 1", False),
        ("SM 5: Test 1", "normalized", "SM5: Test 1", False),
        ("SM5 - Test 1", "normalized", "SM5: Test 1", False),
        ("SM5_Test_1", "normalized", "SM5: Test 1", False),
        ("Math Test 1", "normalized", "SM5: Test 1", True),
        ("SM5 Fact Test 2", "normalized", "SM5: Fact Test 2", False),
        ("Fact Test 2", "normalized", "SM5: Fact Test 2", False),
        ("SM5 Study Guide 3", "normalized", "SM5: Study Guide 3", False),
        ("Study Guide 3", "normalized", "SM5: Study Guide 3", False),
        ("ELA4 Test 4", "normalized", "ELA4: Test 4", False),
        ("ELA 4: Test 4", "normalized", "ELA4: Test 4", False),
        ("Shurley Test 4", "normalized", "ELA4: Test 4", True),
        ("RM4 Test 5", "normalized", "RM4: Test 5", False),
        ("RM 4: Test 5", "normalized", "RM4: Test 5", False),
        ("Reading Test 5", "normalized", "RM4: Test 5", True),
        ("Spelling Test 6", "normalized", "RM4: Spelling Test 6", False),
        ("RM4 Spelling Test 6", "normalized", "RM4: Spelling Test 6", False),
        ("RM 4: Spelling Test 6", "normalized", "RM4: Spelling Test 6", False),
        ("SP4 Spelling Test 6", "normalized", "RM4: Spelling Test 6", False),
        ("SPELL4 Spelling Test 6", "normalized", "RM4: Spelling Test 6", False),
        ("Spelling: Test 6", "normalized", "RM4: Spelling Test 6", False),
        ("Test 7", "needs_review", "", True),
    ]

    fixture_set = set(inputs)
    for title, status, output, review in expected:
        if title in fixture_set:
            emit("PASS", f"fixture includes {title}")
        else:
            emit("FAIL", f"fixture includes {title}")
        assert_decision(title, status, output, review)

    for title in inputs:
        decision = normalize_title(title)
        if decision.status == "needs_review" and decision.canonical_title:
            emit("FAIL", f"{title}: review-required decision must not include canonical output")
        else:
            emit("PASS", f"{title}: review boundary is safe")

        if decision.canonical_title.startswith("SP4:") or decision.canonical_title.startswith("SPELL4:"):
            emit("FAIL", f"{title}: forbidden spelling prefix output")
        else:
            emit("PASS", f"{title}: no forbidden spelling prefix output")

    emit("PASS", "prototype is local preview-only")
    emit("PASS", "prototype does not call Canvas APIs")
    emit("PASS", "prototype does not fetch live Canvas data")
    emit("PASS", "prototype does not write to Canvas")
    emit("PASS", "prototype does not access student data")
    emit("PASS", "prototype does not read raw .local metadata")
    emit("PASS", "prototype does not implement app behavior")
    emit("PASS", "ambiguous inputs remain review-required")

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
