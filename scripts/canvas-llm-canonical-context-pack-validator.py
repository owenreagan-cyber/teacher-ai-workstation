#!/usr/bin/env python3
"""Validate the Canvas LLM canonical context pack.

This validator is deterministic, local-only, and read-only. It performs no
Canvas calls, database writes, external network access, or fixture generation.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
PACK_DIR = REPO_ROOT / "docs/programs/canvas-llm/canonical-context-pack"
MANIFEST_PATH = PACK_DIR / "context-pack-manifest.json"

EXPECTED_MARKDOWN_FILES = {
    "README.md",
    "agenda-page-contract.md",
    "announcement-contract.md",
    "approval-and-publish-contract.md",
    "assignment-contract.md",
    "calendar-disruption-contract.md",
    "canonical-source-matrix.md",
    "canvas-course-routing.md",
    "legacy-app-comparison-oracle.md",
    "math-rules-and-maps.md",
    "naming-conventions.md",
    "newsletter-homeroom-contract.md",
    "product-and-architecture-rules.md",
    "reading-rules-and-maps.md",
    "resource-resolution-contract.md",
    "school-calendar-2026-27.md",
    "spelling-rules-and-maps.md",
    "together-logic.md",
    "unresolved-owner-decisions.md",
    "weekly-input-contract.md",
}

PASS_COUNT = 0
WARN_COUNT = 0
FAIL_COUNT = 0


def pass_check(message: str) -> None:
    global PASS_COUNT
    PASS_COUNT += 1
    print(f"PASS: {message}")


def warn_check(message: str) -> None:
    global WARN_COUNT
    WARN_COUNT += 1
    print(f"WARN: {message}")


def fail_check(message: str) -> None:
    global FAIL_COUNT
    FAIL_COUNT += 1
    print(f"FAIL: {message}")


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        fail_check(f"cannot read {path.relative_to(REPO_ROOT)}: {exc}")
        return ""


def require_file(path: Path) -> None:
    rel = path.relative_to(REPO_ROOT)
    if path.is_file():
        pass_check(f"required file exists: {rel}")
    else:
        fail_check(f"required file missing: {rel}")


def require_nonempty(path: Path) -> None:
    rel = path.relative_to(REPO_ROOT)
    if path.is_file() and path.stat().st_size > 0:
        pass_check(f"required file is non-empty: {rel}")
    else:
        fail_check(f"required file is empty or missing: {rel}")


def require_contains(path: Path, needle: str, description: str) -> None:
    text = read_text(path)
    if needle in text:
        pass_check(description)
    else:
        fail_check(f"{description} — missing text: {needle!r}")


def require_absent(path: Path, needle: str, description: str) -> None:
    text = read_text(path)
    if needle not in text:
        pass_check(description)
    else:
        fail_check(f"{description} — prohibited text found: {needle!r}")


def require_any_contains(
    paths: Iterable[Path], needle: str, description: str
) -> None:
    for path in paths:
        if needle in read_text(path):
            pass_check(description)
            return
    fail_check(f"{description} — missing text: {needle!r}")


def validate_inventory() -> None:
    if PACK_DIR.is_dir():
        pass_check(
            f"required directory exists: {PACK_DIR.relative_to(REPO_ROOT)}"
        )
    else:
        fail_check(
            f"required directory missing: {PACK_DIR.relative_to(REPO_ROOT)}"
        )

    require_file(MANIFEST_PATH)

    actual_markdown = {
        path.name for path in PACK_DIR.glob("*.md") if path.is_file()
    }

    missing = sorted(EXPECTED_MARKDOWN_FILES - actual_markdown)
    extra = sorted(actual_markdown - EXPECTED_MARKDOWN_FILES)

    if not missing:
        pass_check("all expected Context Pack Markdown files exist")
    else:
        fail_check(f"missing Context Pack Markdown files: {missing}")

    if not extra:
        pass_check("no unexpected Context Pack Markdown files exist")
    else:
        warn_check(f"unexpected Context Pack Markdown files exist: {extra}")

    for name in sorted(EXPECTED_MARKDOWN_FILES):
        require_nonempty(PACK_DIR / name)

    require_nonempty(MANIFEST_PATH)


def validate_manifest() -> dict:
    try:
        payload = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail_check(f"context-pack manifest is invalid JSON: {exc}")
        return {}

    pass_check("context-pack manifest is valid JSON")

    expected_pairs = {
        "schemaVersion": 1,
        "schoolYear": "2026-2027",
        "productMode": "single-user-local-first",
    }

    for key, expected in expected_pairs.items():
        actual = payload.get(key)
        if actual == expected:
            pass_check(f"manifest {key} is {expected!r}")
        else:
            fail_check(
                f"manifest {key} expected {expected!r}, found {actual!r}"
            )

    status = payload.get("status")
    if status == "validated":
        pass_check("manifest status is 'validated'")
    else:
        fail_check(
            f"manifest status expected 'validated', found {status!r}"
        )

    validation = payload.get("validation")
    if isinstance(validation, dict):
        pass_check("manifest contains validation metadata")
    else:
        fail_check("manifest validation metadata is missing")

    expected_command = (
        "bin/chief-of-staff "
        "--canvas-llm-canonical-context-pack-status"
    )
    actual_command = (
        validation.get("statusCommand")
        if isinstance(validation, dict)
        else None
    )
    if actual_command == expected_command:
        pass_check("manifest records the canonical status command")
    else:
        fail_check(
            "manifest canonical status command is missing or incorrect"
        )

    sources = payload.get("canonicalSources")
    if isinstance(sources, list) and len(sources) >= 9:
        pass_check("manifest records at least nine canonical sources")
    else:
        fail_check("manifest canonicalSources must contain at least nine entries")

    return payload


def validate_product_boundary() -> None:
    architecture = PACK_DIR / "product-and-architecture-rules.md"
    weekly = PACK_DIR / "weekly-input-contract.md"
    legacy = PACK_DIR / "legacy-app-comparison-oracle.md"
    approval = PACK_DIR / "approval-and-publish-contract.md"

    require_contains(
        architecture,
        "a single-user, local-first Teacher AI Workstation",
        "product is explicitly single-user and local-first",
    )
    require_contains(
        architecture,
        "Canonical teacher work lives in SQLite.",
        "SQLite is the teacher-work authority",
    )
    require_contains(
        architecture,
        "127.0.0.1",
        "localhost-only service boundary is recorded",
    )
    require_contains(
        architecture,
        "Synthetic fixtures are prohibited as the implicit production source.",
        "synthetic fixtures are prohibited as implicit production input",
    )
    require_contains(
        weekly,
        "The editable weekly model is the production source of truth",
        "editable weekly model is the production source of truth",
    )
    require_contains(
        architecture,
        "Do not replace Phase 27 with an unreviewed direct deployment bridge.",
        "Phase 27 safety boundary is preserved",
    )
    require_contains(
        legacy,
        "`.local/reference-apps/...` must remain ignored.",
        "legacy reference applications remain ignored evidence",
    )
    require_contains(
        legacy,
        "They are evidence repositories.",
        "legacy apps are evidence rather than runtime dependencies",
    )
    require_contains(
        approval,
        "Export is not publish.",
        "export and Canvas publish remain distinct",
    )


def validate_announcement_rules() -> None:
    announcement = PACK_DIR / "announcement-contract.md"
    together = PACK_DIR / "together-logic.md"

    require_contains(
        announcement,
        "Standalone Spelling announcements are allowed.",
        "standalone Spelling announcements are allowed",
    )
    require_contains(
        announcement,
        "Standalone Reading announcements are allowed.",
        "standalone Reading announcements are allowed",
    )
    require_contains(
        announcement,
        "same canonical week_code",
        "Reading and Spelling combination uses canonical week identity",
    )
    require_contains(
        together,
        "Spelling assessment without a Reading assessment that week → standalone Spelling announcement;",
        "Spelling-only week produces standalone Spelling announcement",
    )
    require_contains(
        together,
        "Reading and Spelling assessments in the same instructional week → combined family announcement;",
        "same-week Reading and Spelling assessments combine",
    )

    prohibited_pattern = re.compile(
        r"standalone spelling announcements are blocked",
        re.IGNORECASE,
    )

    violations: list[str] = []
    for path in sorted(PACK_DIR.glob("*.md")):
        if prohibited_pattern.search(read_text(path)):
            violations.append(path.name)

    if violations:
        fail_check(
            "incorrect standalone-Spelling prohibition found in: "
            + ", ".join(violations)
        )
    else:
        pass_check(
            "incorrect standalone-Spelling prohibition is absent from the Context Pack"
        )


def validate_curriculum_safety() -> None:
    reading = PACK_DIR / "reading-rules-and-maps.md"
    spelling = PACK_DIR / "spelling-rules-and-maps.md"
    announcement = PACK_DIR / "announcement-contract.md"
    resources = PACK_DIR / "resource-resolution-contract.md"

    require_any_contains(
        [reading, announcement],
        "Reading Test 14",
        "Reading Test 14 exception is documented",
    )
    require_contains(
        announcement,
        "Reading Test 14 has no Checkout.",
        "Reading Test 14 explicitly has no Checkout",
    )
    require_contains(
        resources,
        "Reading Test 14 must not request or resolve a Checkout 14 resource.",
        "resource resolution prohibits Checkout 14",
    )
    require_contains(
        spelling,
        "Tests 1–24",
        "Spelling canonical range is Tests 1–24",
    )
    require_contains(
        announcement,
        "Spelling Test 25 must not be announced until:",
        "Spelling Test 25 announcement remains gated",
    )
    require_contains(
        resources,
        "No Test 25 resource may be treated as canonical",
        "Spelling Test 25 resources remain unresolved",
    )


def validate_resource_safety() -> None:
    resources = PACK_DIR / "resource-resolution-contract.md"

    require_contains(
        resources,
        "teacher-only",
        "teacher-only visibility is documented",
    )
    require_contains(
        resources,
        "answer-key",
        "answer-key sensitivity is documented",
    )
    require_contains(
        resources,
        "assessment-secure",
        "assessment-secure sensitivity is documented",
    )
    require_contains(
        resources,
        "never be replaced with a fake link",
        "fake resource links are prohibited",
    )
    require_contains(
        resources,
        "Local filesystem paths are internal only.",
        "local paths remain internal",
    )
    require_contains(
        resources,
        "verified or owner-approved",
        "production resources require verification or owner approval",
    )


def validate_approval_safety() -> None:
    approval = PACK_DIR / "approval-and-publish-contract.md"

    for status in (
        "CREATE",
        "UPDATE",
        "UNCHANGED",
        "BLOCKED",
        "CONFLICT",
        "OMIT",
        "DELETE_CANDIDATE",
    ):
        require_contains(
            approval,
            status,
            f"approval contract includes comparison status {status}",
        )

    require_contains(
        approval,
        "objectId\nmanifestRevision\nsnapshotId",
        "approval binds to object, manifest revision, and snapshot",
    )
    require_contains(
        approval,
        "Ledger event history must be append-only.",
        "deployment ledger event history is append-only",
    )
    require_contains(
        approval,
        "A successful HTTP response alone is insufficient.",
        "successful request alone is not deployment proof",
    )
    require_contains(
        approval,
        "read-back verification passed",
        "deployed state requires read-back verification",
    )
    require_contains(
        approval,
        "Canvas assignment due-time convention remains unresolved.",
        "unresolved due-time blocker is preserved",
    )
    require_contains(
        approval,
        "Automatic deletion is prohibited.",
        "automatic Canvas deletion is prohibited",
    )


def validate_no_secret_material() -> None:
    secret_patterns = [
        re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
        re.compile(r"Bearer\s+[A-Za-z0-9._-]{20,}", re.IGNORECASE),
        re.compile(r"CANVAS_API_TOKEN\s*=\s*['\"][^'\"]+['\"]"),
    ]

    findings: list[str] = []

    for path in [*PACK_DIR.glob("*.md"), MANIFEST_PATH]:
        text = read_text(path)
        for pattern in secret_patterns:
            if pattern.search(text):
                findings.append(f"{path.name}: {pattern.pattern}")

    if findings:
        fail_check(f"possible secret material found: {findings}")
    else:
        pass_check("no obvious token or authorization secret material found")


def main() -> int:
    print("Canvas LLM Canonical Context Pack Validator")
    print(f"Context pack: {PACK_DIR.relative_to(REPO_ROOT)}")
    print()

    validate_inventory()
    validate_manifest()
    validate_product_boundary()
    validate_announcement_rules()
    validate_curriculum_safety()
    validate_resource_safety()
    validate_approval_safety()
    validate_no_secret_material()

    print()
    print(f"PASS: {PASS_COUNT}")
    print(f"WARN: {WARN_COUNT}")
    print(f"FAIL: {FAIL_COUNT}")

    return 1 if FAIL_COUNT else 0


if __name__ == "__main__":
    sys.exit(main())
