#!/usr/bin/env python3
"""Canvas LLM Phase 10 sandbox metadata review gate.

Reviews ignored local Canvas metadata staged by Phase 9B.

Approved scope:
- course 24399 only
- local ignored staging metadata only
- read/review/validate only
- no Canvas API calls
- no import into knowledge DB
- no production writes
- no real curriculum body ingestion
- no student data
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

APPROVED_COURSE_ID = "24399"
APPROVED_STAGING_ROOT = Path(".local/canvas-llm/sandbox-metadata/course-24399")
EXPECTED_ENDPOINTS = {
    "course_metadata",
    "modules",
    "pages_metadata",
    "assignments_metadata",
    "announcements_metadata",
    "files_metadata",
    "module_items",
}
# Exact unsafe keys are blocked. Metadata status keys such as
# publish_final_grade and hide_from_students are allowed because they are
# course-object visibility/status metadata, not grade/student records.
FORBIDDEN_KEYS = {
    "body",
    "description",
    "message",
    "html_url_body",
    "syllabus_body",
    "submission",
    "submissions",
    "grade",
    "grades",
    "score",
    "scores",
    "user",
    "users",
    "user_id",
    "user_name",
    "enrollment",
    "enrollments",
    "student",
    "students",
    "student_id",
    "student_name",
    "participants",
    "conversation",
    "conversations",
    "replies",
}
ALLOWED_METADATA_KEYS = {
    "publish_final_grade",
    "hide_from_students",
    "locked_for_user",
    "user_name",
}
FORBIDDEN_KEY_PATTERNS = [
    re.compile(r".*_body$", re.IGNORECASE),
    re.compile(r"^body$", re.IGNORECASE),
    re.compile(r"^description$", re.IGNORECASE),
    re.compile(r"^message$", re.IGNORECASE),
    re.compile(r"^submissions?$", re.IGNORECASE),
    re.compile(r"^grades?$", re.IGNORECASE),
    re.compile(r"^scores?$", re.IGNORECASE),
    re.compile(r"^students?$", re.IGNORECASE),
    re.compile(r"^student_(id|name|email)$", re.IGNORECASE),
    re.compile(r"^users?$", re.IGNORECASE),
    re.compile(r"^user_(id|email)$", re.IGNORECASE),
    re.compile(r"^enrollments?$", re.IGNORECASE),
    re.compile(r"^conversations?$", re.IGNORECASE),
]
FORBIDDEN_TEXT_PATTERNS = [
    re.compile(r"Bearer\s+[A-Za-z0-9_=-]{20,}"),
    re.compile(r"CANVAS_API_TOKEN\s*="),
    re.compile(r"access_token", re.IGNORECASE),
]


def fail(message: str) -> int:
    print(f"FAIL: {message}", file=sys.stderr)
    return 1


def pass_msg(message: str) -> None:
    print(f"PASS: {message}")


def warn_msg(message: str) -> None:
    print(f"WARN: {message}")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_root(path: Path) -> list[str]:
    errors: list[str] = []
    normalized = path.as_posix().rstrip("/")
    approved = APPROVED_STAGING_ROOT.as_posix()
    if normalized != approved:
        errors.append(f"staging root must be {approved}; got {normalized}")
    if not path.exists():
        errors.append(f"staging root missing: {path}")
    if not (path / "manifest.json").exists():
        errors.append(f"manifest missing: {path / 'manifest.json'}")
    return errors


def scan_forbidden_keys(value: Any, location: str, hits: list[str]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            key_text = str(key)
            if key_text in ALLOWED_METADATA_KEYS:
                scan_forbidden_keys(child, f"{location}.{key_text}", hits)
                continue
            if key_text in FORBIDDEN_KEYS:
                hits.append(f"{location}.{key_text}")
            for pattern in FORBIDDEN_KEY_PATTERNS:
                if pattern.fullmatch(key_text):
                    hits.append(f"{location}.{key_text}")
                    break
            scan_forbidden_keys(child, f"{location}.{key_text}", hits)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            scan_forbidden_keys(child, f"{location}[{index}]", hits)


def scan_forbidden_text(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    hits: list[str] = []
    for pattern in FORBIDDEN_TEXT_PATTERNS:
        if pattern.search(text):
            hits.append(f"{path}: pattern {pattern.pattern}")
    return hits


def record_count(value: Any) -> int:
    if isinstance(value, list):
        return len(value)
    if isinstance(value, dict):
        return 1
    return 0


def cmd_review(args: argparse.Namespace) -> int:
    root = Path(args.staging_root)
    errors = validate_root(root)
    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1

    manifest_path = root / "manifest.json"
    manifest = load_json(manifest_path)

    if manifest.get("course_id") != APPROVED_COURSE_ID:
        return fail(f"manifest course_id must be {APPROVED_COURSE_ID}; got {manifest.get('course_id')!r}")

    expected_flags = {
        "read_only": True,
        "metadata_only": True,
        "canvas_write": False,
        "student_data": False,
        "real_curriculum_body_ingestion": False,
        "token_value_printed": False,
    }
    for key, expected in expected_flags.items():
        actual = manifest.get(key)
        if actual != expected:
            return fail(f"manifest {key} must be {expected!r}; got {actual!r}")

    pass_msg("manifest confirms course 24399 only")
    pass_msg("manifest confirms read-only metadata-only output")
    pass_msg("manifest confirms no Canvas writes, student data, curriculum body ingestion, or token printing")

    manifest_files = manifest.get("files", [])
    if not isinstance(manifest_files, list):
        return fail("manifest files must be a list")

    endpoint_classes = {entry.get("endpoint_class") for entry in manifest_files if isinstance(entry, dict)}
    missing = sorted(EXPECTED_ENDPOINTS - endpoint_classes)
    extra = sorted(endpoint_classes - EXPECTED_ENDPOINTS)
    if missing:
        return fail(f"manifest missing expected endpoint classes: {', '.join(missing)}")
    if extra:
        return fail(f"manifest contains unexpected endpoint classes: {', '.join(extra)}")
    pass_msg("manifest endpoint classes match approved Phase 10 review set")

    review_summary: dict[str, Any] = {
        "phase": "canvas_llm_phase_10_sandbox_metadata_review_gate",
        "course_id": APPROVED_COURSE_ID,
        "staging_root": str(root),
        "review_only": True,
        "import_performed": False,
        "canvas_api_call": False,
        "production_write": False,
        "endpoint_counts": {},
        "warnings": [],
    }

    forbidden_key_hits: list[str] = []
    forbidden_text_hits: list[str] = []

    for entry in manifest_files:
        if not isinstance(entry, dict):
            return fail("manifest file entry must be an object")
        endpoint_class = entry.get("endpoint_class")
        path_text = entry.get("path")
        sanitized = entry.get("sanitized")
        if endpoint_class not in EXPECTED_ENDPOINTS:
            return fail(f"unexpected endpoint class: {endpoint_class}")
        if sanitized is not True:
            return fail(f"{endpoint_class} manifest entry must be sanitized=true")
        if not isinstance(path_text, str):
            return fail(f"{endpoint_class} manifest entry path must be a string")

        path = Path(path_text)
        if not path.exists():
            return fail(f"{endpoint_class} metadata file missing: {path}")
        if not path.as_posix().startswith(root.as_posix().rstrip("/") + "/"):
            return fail(f"{endpoint_class} path is outside approved staging root: {path}")

        payload = load_json(path)
        count = record_count(payload)
        expected_count = entry.get("record_count")
        if expected_count != count:
            return fail(f"{endpoint_class} record count mismatch: manifest {expected_count}, file {count}")

        review_summary["endpoint_counts"][endpoint_class] = count
        scan_forbidden_keys(payload, endpoint_class, forbidden_key_hits)
        forbidden_text_hits.extend(scan_forbidden_text(path))

    if forbidden_key_hits:
        for hit in forbidden_key_hits[:25]:
            print(f"FAIL: forbidden key found: {hit}", file=sys.stderr)
        if len(forbidden_key_hits) > 25:
            print(f"FAIL: plus {len(forbidden_key_hits) - 25} more forbidden key hits", file=sys.stderr)
        return 1

    if forbidden_text_hits:
        for hit in forbidden_text_hits:
            print(f"FAIL: forbidden text pattern found: {hit}", file=sys.stderr)
        return 1

    if review_summary["endpoint_counts"].get("announcements_metadata", 0) == 0:
        review_summary["warnings"].append("announcements_metadata has 0 records in sandbox staging")
        warn_msg("announcements_metadata has 0 records in sandbox staging")

    pass_msg("all metadata files exist under approved local staging root")
    pass_msg("manifest record counts match staged files")
    pass_msg("forbidden body/content/student/grade/enrollment-style keys not found")
    pass_msg("token/bearer/access-token text patterns not found")
    pass_msg("review only; no Canvas API call, import, or production write performed")

    print(json.dumps(review_summary, indent=2, sort_keys=True))
    return 0


def cmd_plan(args: argparse.Namespace) -> int:
    root = Path(args.staging_root)
    plan = {
        "phase": "canvas_llm_phase_10_sandbox_metadata_review_gate",
        "course_id": APPROVED_COURSE_ID,
        "staging_root": str(root),
        "review_only": True,
        "import_performed": False,
        "canvas_api_call": False,
        "production_write": False,
        "expected_endpoint_classes": sorted(EXPECTED_ENDPOINTS),
    }
    pass_msg("review plan generated without reading Canvas API or importing metadata")
    print(json.dumps(plan, indent=2, sort_keys=True))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Phase 10 local sandbox metadata review gate.")
    parser.add_argument("--staging-root", default=str(APPROVED_STAGING_ROOT))

    subcommands = parser.add_subparsers(dest="command", required=True)

    plan = subcommands.add_parser("plan")
    plan.set_defaults(func=cmd_plan)

    review = subcommands.add_parser("review")
    review.set_defaults(func=cmd_review)

    return parser


def main() -> int:
    args = build_parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
