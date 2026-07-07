#!/usr/bin/env python3
"""Canvas LLM Phase 11 sandbox metadata import preview gate.

Creates a preview-only mapping report from ignored local Phase 9B metadata.

Approved scope:
- course 24399 only
- local ignored staging metadata only
- preview report only
- no knowledge DB import
- no runtime SQLite/database writes
- no Canvas API calls
- no production writes
- no student data
- no real curriculum body ingestion
- no generation/RAG/embeddings
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

ENTITY_MAP = {
    "course_metadata": "canvas_course_metadata_preview",
    "modules": "canvas_module_metadata_preview",
    "module_items": "canvas_module_item_metadata_preview",
    "pages_metadata": "canvas_page_metadata_preview",
    "assignments_metadata": "canvas_assignment_metadata_preview",
    "announcements_metadata": "canvas_announcement_metadata_preview",
    "files_metadata": "canvas_file_metadata_preview",
}

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


def validate_root(root: Path) -> list[str]:
    errors: list[str] = []
    normalized = root.as_posix().rstrip("/")
    approved = APPROVED_STAGING_ROOT.as_posix()
    if normalized != approved:
        errors.append(f"staging root must be {approved}; got {normalized}")
    if not root.exists():
        errors.append(f"staging root missing: {root}")
    if not (root / "manifest.json").exists():
        errors.append(f"manifest missing: {root / 'manifest.json'}")
    return errors


def record_count(value: Any) -> int:
    if isinstance(value, list):
        return len(value)
    if isinstance(value, dict):
        return 1
    return 0


def scan_forbidden_text(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    hits: list[str] = []
    for pattern in FORBIDDEN_TEXT_PATTERNS:
        if pattern.search(text):
            hits.append(f"{path}: pattern {pattern.pattern}")
    return hits


def preview_fields(payload: Any, max_fields: int = 12) -> list[str]:
    records: list[Any]
    if isinstance(payload, list):
        records = payload
    else:
        records = [payload]

    fields: set[str] = set()
    for record in records[:20]:
        if isinstance(record, dict):
            fields.update(str(key) for key in record.keys())

    return sorted(fields)[:max_fields]


def build_preview(root: Path) -> tuple[dict[str, Any], list[str], list[str]]:
    manifest_path = root / "manifest.json"
    manifest = load_json(manifest_path)

    errors: list[str] = []
    warnings: list[str] = []

    if manifest.get("course_id") != APPROVED_COURSE_ID:
        errors.append(f"manifest course_id must be {APPROVED_COURSE_ID}; got {manifest.get('course_id')!r}")

    expected_flags = {
        "read_only": True,
        "metadata_only": True,
        "canvas_write": False,
        "student_data": False,
        "real_curriculum_body_ingestion": False,
        "token_value_printed": False,
    }
    for key, expected in expected_flags.items():
        if manifest.get(key) != expected:
            errors.append(f"manifest {key} must be {expected!r}; got {manifest.get(key)!r}")

    manifest_files = manifest.get("files", [])
    if not isinstance(manifest_files, list):
        errors.append("manifest files must be a list")
        manifest_files = []

    endpoint_classes = {entry.get("endpoint_class") for entry in manifest_files if isinstance(entry, dict)}
    missing = sorted(EXPECTED_ENDPOINTS - endpoint_classes)
    extra = sorted(endpoint_classes - EXPECTED_ENDPOINTS)
    if missing:
        errors.append(f"manifest missing expected endpoint classes: {', '.join(missing)}")
    if extra:
        errors.append(f"manifest contains unexpected endpoint classes: {', '.join(extra)}")

    preview = {
        "phase": "canvas_llm_phase_11_sandbox_metadata_import_preview_gate",
        "course_id": APPROVED_COURSE_ID,
        "staging_root": str(root),
        "preview_only": True,
        "import_performed": False,
        "knowledge_db_write": False,
        "runtime_database_write": False,
        "canvas_api_call": False,
        "production_write": False,
        "student_data": False,
        "real_curriculum_body_ingestion": False,
        "generation_rag_embeddings": False,
        "entity_previews": [],
        "warnings": warnings,
    }

    forbidden_text_hits: list[str] = []

    for entry in manifest_files:
        if not isinstance(entry, dict):
            errors.append("manifest file entry must be an object")
            continue

        endpoint_class = entry.get("endpoint_class")
        path_text = entry.get("path")
        sanitized = entry.get("sanitized")

        if endpoint_class not in EXPECTED_ENDPOINTS:
            errors.append(f"unexpected endpoint class: {endpoint_class}")
            continue
        if sanitized is not True:
            errors.append(f"{endpoint_class} manifest entry must be sanitized=true")
            continue
        if not isinstance(path_text, str):
            errors.append(f"{endpoint_class} manifest entry path must be a string")
            continue

        path = Path(path_text)
        if not path.exists():
            errors.append(f"{endpoint_class} metadata file missing: {path}")
            continue
        if not path.as_posix().startswith(root.as_posix().rstrip("/") + "/"):
            errors.append(f"{endpoint_class} path is outside approved staging root: {path}")
            continue

        payload = load_json(path)
        count = record_count(payload)
        expected_count = entry.get("record_count")
        if count != expected_count:
            errors.append(f"{endpoint_class} record count mismatch: manifest {expected_count}, file {count}")

        if endpoint_class == "announcements_metadata" and count == 0:
            warnings.append("announcements_metadata has 0 records in sandbox staging")

        forbidden_text_hits.extend(scan_forbidden_text(path))

        preview["entity_previews"].append(
            {
                "endpoint_class": endpoint_class,
                "preview_entity": ENTITY_MAP[endpoint_class],
                "source_record_count": count,
                "candidate_preview_record_count": count,
                "sample_fields": preview_fields(payload),
                "source_path": str(path),
                "would_import": False,
                "would_write_knowledge_db": False,
                "would_write_runtime_database": False,
                "would_write_production": False,
            }
        )

    if forbidden_text_hits:
        errors.extend([f"forbidden text pattern found: {hit}" for hit in forbidden_text_hits])

    return preview, errors, warnings


def cmd_plan(args: argparse.Namespace) -> int:
    root = Path(args.staging_root)
    plan = {
        "phase": "canvas_llm_phase_11_sandbox_metadata_import_preview_gate",
        "course_id": APPROVED_COURSE_ID,
        "staging_root": str(root),
        "preview_only": True,
        "import_performed": False,
        "knowledge_db_write": False,
        "runtime_database_write": False,
        "canvas_api_call": False,
        "production_write": False,
        "expected_endpoint_classes": sorted(EXPECTED_ENDPOINTS),
        "preview_entity_types": ENTITY_MAP,
    }
    pass_msg("import preview plan generated without Canvas API call, import, or database write")
    print(json.dumps(plan, indent=2, sort_keys=True))
    return 0


def cmd_preview(args: argparse.Namespace) -> int:
    root = Path(args.staging_root)
    root_errors = validate_root(root)
    if root_errors:
        for error in root_errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1

    preview, errors, warnings = build_preview(root)
    if errors:
        for error in errors[:30]:
            print(f"FAIL: {error}", file=sys.stderr)
        if len(errors) > 30:
            print(f"FAIL: plus {len(errors) - 30} more errors", file=sys.stderr)
        return 1

    pass_msg("preview source accepted course 24399 only")
    pass_msg("preview confirms read-only metadata-only staged source")
    pass_msg("preview entity mappings generated")
    pass_msg("preview only; no import performed")
    pass_msg("no knowledge DB write, runtime database write, Canvas API call, or production write performed")
    pass_msg("token/bearer/access-token text patterns not found")

    for warning in warnings:
        warn_msg(warning)

    print(json.dumps(preview, indent=2, sort_keys=True))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Phase 11 sandbox metadata import preview gate.")
    parser.add_argument("--staging-root", default=str(APPROVED_STAGING_ROOT))

    subcommands = parser.add_subparsers(dest="command", required=True)

    plan = subcommands.add_parser("plan")
    plan.set_defaults(func=cmd_plan)

    preview = subcommands.add_parser("preview")
    preview.set_defaults(func=cmd_preview)

    return parser


def main() -> int:
    args = build_parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
