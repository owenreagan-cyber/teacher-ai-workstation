#!/usr/bin/env python3
"""Read-only validator for Canvas LLM fake/local knowledge DB fixtures.

This script validates repo-contained fake/local JSON only.
It does not perform Canvas API calls, OAuth, network access, runtime database writes,
RAG, embeddings, generation, or real curriculum ingestion.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

PASS_COUNT = 0
WARN_COUNT = 0
FAIL_COUNT = 0


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = ROOT / "fixtures" / "canvas-llm" / "knowledge-db"

FILES = {
    "sources": FIXTURE_DIR / "fake-sources.json",
    "evidence": FIXTURE_DIR / "fake-evidence.json",
    "patterns": FIXTURE_DIR / "fake-patterns.json",
    "facts": FIXTURE_DIR / "fake-facts.json",
    "qa": FIXTURE_DIR / "fake-qa.json",
    "courses": FIXTURE_DIR / "fake-courses.json",
    "modules": FIXTURE_DIR / "fake-modules.json",
    "pages": FIXTURE_DIR / "fake-pages.json",
    "assignments": FIXTURE_DIR / "fake-assignments.json",
    "announcements": FIXTURE_DIR / "fake-announcements.json",
    "files": FIXTURE_DIR / "fake-files.json",
}

FORBIDDEN_PATTERNS = {
    "canvas token": re.compile(r"canvas[_-]?token|access[_-]?token|bearer\s+[a-z0-9._-]+", re.I),
    "email address": re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I),
    "live Canvas URL": re.compile(r"https?://[^\"'\s]*(canvas|instructure)[^\"'\s]*", re.I),
    "student marker": re.compile(r"\bstudent\s+(name|id|email|number)\b", re.I),
}


def pass_msg(message: str) -> None:
    global PASS_COUNT
    PASS_COUNT += 1
    print(f"PASS: {message}")


def warn_msg(message: str) -> None:
    global WARN_COUNT
    WARN_COUNT += 1
    print(f"WARN: {message}")


def fail_msg(message: str) -> None:
    global FAIL_COUNT
    FAIL_COUNT += 1
    print(f"FAIL: {message}")


def section(title: str) -> None:
    print()
    print(title)
    print("----------------------------------------")


def load_json(label: str, path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        fail_msg(f"missing JSON fixture: {path.relative_to(ROOT)}")
        return []

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail_msg(f"invalid JSON fixture {path.relative_to(ROOT)}: {exc}")
        return []

    if not isinstance(data, list):
        fail_msg(f"{path.relative_to(ROOT)} must be a JSON list")
        return []

    bad_items = [idx for idx, item in enumerate(data) if not isinstance(item, dict)]
    if bad_items:
        fail_msg(f"{path.relative_to(ROOT)} has non-object entries at indexes {bad_items}")
        return []

    pass_msg(f"loaded {label}: {path.relative_to(ROOT)}")
    return data


def require_field(item: dict[str, Any], field: str, label: str) -> bool:
    value = item.get(field)
    if value in (None, "", []):
        fail_msg(f"{label} missing required field: {field}")
        return False
    pass_msg(f"{label} has required field: {field}")
    return True


def require_expected(item: dict[str, Any], field: str, expected: str, label: str) -> None:
    actual = item.get(field)
    if actual == expected:
        pass_msg(f"{label} {field} is {expected}")
    else:
        fail_msg(f"{label} {field} expected {expected}, got {actual!r}")


def index_by(items: list[dict[str, Any]], key: str, label: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for item in items:
        value = item.get(key)
        if not isinstance(value, str) or not value:
            fail_msg(f"{label} entry missing string id field: {key}")
            continue
        if value in result:
            fail_msg(f"{label} duplicate id: {value}")
            continue
        result[value] = item
    if result:
        pass_msg(f"{label} ids are unique by {key}")
    return result


def check_refs(
    item: dict[str, Any],
    field: str,
    allowed: dict[str, dict[str, Any]],
    label: str,
) -> None:
    refs = item.get(field, [])
    if not isinstance(refs, list) or not refs:
        fail_msg(f"{label} missing non-empty reference list: {field}")
        return

    for ref in refs:
        if ref in allowed:
            pass_msg(f"{label} {field} reference exists: {ref}")
        else:
            fail_msg(f"{label} {field} reference missing: {ref}")


def check_single_ref(
    item: dict[str, Any],
    field: str,
    allowed: dict[str, dict[str, Any]],
    label: str,
) -> None:
    ref = item.get(field)
    if not isinstance(ref, str) or not ref:
        fail_msg(f"{label} missing string reference: {field}")
        return

    if ref in allowed:
        pass_msg(f"{label} {field} reference exists: {ref}")
    else:
        fail_msg(f"{label} {field} reference missing: {ref}")


def scan_forbidden_text(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    for label, pattern in FORBIDDEN_PATTERNS.items():
        if pattern.search(text):
            fail_msg(f"forbidden {label} pattern found in {path.relative_to(ROOT)}")
        else:
            pass_msg(f"no forbidden {label} pattern in {path.relative_to(ROOT)}")


def main() -> int:
    section("Canvas LLM Fake/Local Knowledge DB Validator")
    print("Status: phase_6_fake_local_relationship_validator")
    print("Runtime activation: no")
    print("Canvas API/OAuth/live reads: blocked")
    print("Canvas writes/publishing: blocked")
    print("Student data: blocked")
    print("Real curriculum ingestion: blocked")
    print("Runtime SQLite/database writes: blocked")
    print("Generation/RAG/embeddings: blocked")

    section("Load Fixtures")
    data = {label: load_json(label, path) for label, path in FILES.items()}

    section("Forbidden Content Scan")
    for path in FILES.values():
        if path.exists():
            scan_forbidden_text(path)

    section("Build ID Indexes")
    sources = index_by(data["sources"], "source_reference_id", "sources")
    evidence = index_by(data["evidence"], "evidence_id", "evidence")
    patterns = index_by(data["patterns"], "pattern_id", "patterns")
    facts = index_by(data["facts"], "fact_id", "facts")
    qa = index_by(data["qa"], "question_id", "qa")
    courses = index_by(data["courses"], "course_id", "courses")
    modules = index_by(data["modules"], "module_id", "modules")
    pages = index_by(data["pages"], "page_id", "pages")
    assignments = index_by(data["assignments"], "assignment_id", "assignments")
    announcements = index_by(data["announcements"], "announcement_id", "announcements")
    files = index_by(data["files"], "file_id", "files")

    section("Required Safety Fields")
    for group_label, items in data.items():
        for item in items:
            item_label = f"{group_label}:{next(iter(item.values()), 'unknown')}"
            require_field(item, "source_class", item_label)
            require_field(item, "evidence_level", item_label)
            require_field(item, "approval_status", item_label)
            require_field(item, "verification_status", item_label)
            require_expected(item, "source_class", "fake_local_fixture", item_label)
            require_expected(item, "evidence_level", "Level 0", item_label)
            require_expected(item, "approval_status", "fixture_approved", item_label)
            require_expected(item, "verification_status", "fake_local_verified", item_label)

    section("Source Evidence Chain")
    for item in data["evidence"]:
        check_single_ref(item, "source_reference_id", sources, f"evidence:{item.get('evidence_id')}")

    for item in data["patterns"]:
        label = f"pattern:{item.get('pattern_id')}"
        check_refs(item, "source_reference_ids", sources, label)
        check_refs(item, "evidence_ids", evidence, label)

    for item in data["facts"]:
        label = f"fact:{item.get('fact_id')}"
        check_refs(item, "source_reference_ids", sources, label)
        check_refs(item, "evidence_ids", evidence, label)
        check_refs(item, "pattern_ids", patterns, label)

    for item in data["qa"]:
        label = f"qa:{item.get('question_id')}"
        check_refs(item, "fact_ids", facts, label)
        check_refs(item, "evidence_ids", evidence, label)
        check_refs(item, "source_reference_ids", sources, label)
        require_field(item, "answer_text", label)

    section("Canvas Object Relationships")
    for item in data["modules"]:
        label = f"module:{item.get('module_id')}"
        check_single_ref(item, "course_id", courses, label)
        check_refs(item, "page_ids", pages, label)
        check_refs(item, "assignment_ids", assignments, label)

    for item in data["pages"]:
        label = f"page:{item.get('page_id')}"
        check_single_ref(item, "course_id", courses, label)
        check_single_ref(item, "module_id", modules, label)
        check_refs(item, "pattern_ids", patterns, label)
        check_refs(item, "fact_ids", facts, label)
        check_refs(item, "source_reference_ids", sources, label)
        check_refs(item, "evidence_ids", evidence, label)

    for group_label, collection in (
        ("assignment", data["assignments"]),
        ("announcement", data["announcements"]),
        ("file", data["files"]),
    ):
        for item in collection:
            label = f"{group_label}:{item.get(group_label + '_id', item.get('file_id'))}"
            check_single_ref(item, "course_id", courses, label)
            check_refs(item, "source_reference_ids", sources, label)
            check_refs(item, "evidence_ids", evidence, label)

    section("Boundary Confirmation")
    pass_msg("validator performs no Canvas API calls")
    pass_msg("validator performs no OAuth or token access")
    pass_msg("validator performs no network access")
    pass_msg("validator performs no runtime database writes")
    pass_msg("validator performs no generation, RAG, or embeddings")
    pass_msg("validator reads fake/local repo fixtures only")

    section("Summary")
    print(f"PASS: {PASS_COUNT}")
    print(f"WARN: {WARN_COUNT}")
    print(f"FAIL: {FAIL_COUNT}")

    return 1 if FAIL_COUNT else 0


if __name__ == "__main__":
    sys.exit(main())
