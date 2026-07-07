#!/usr/bin/env python3
"""Canvas LLM Phase 9B read-only sandbox metadata fetcher.

Approved live scope:
- Course ID 24399 only
- Read-only Canvas API GET requests only
- Metadata-only sanitized output only
- Local staging output only

Blocked:
- Any course except 24399
- Users, enrollments, submissions, grades, analytics, conversations, messages
- Student data
- Canvas writes/publishing
- Real curriculum body/content ingestion
- Runtime database writes
- Generation, RAG, embeddings, local model execution
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

APPROVED_COURSE_ID = "24399"
APPROVED_SOURCE_CLASS = "sandbox_demo_canvas_course"
APPROVED_STAGING_ROOT = Path(".local/canvas-llm/sandbox-metadata/course-24399")
TOKEN_ENV_NAME = "CANVAS_API_TOKEN"
BASE_URL_ENV_NAME = "CANVAS_BASE_URL"
APPROVAL_FLAG = "--i-understand-this-uses-read-only-canvas-api"

ALLOWED_ENDPOINT_CLASSES = {
    "course_metadata",
    "modules",
    "module_items",
    "pages_metadata",
    "assignments_metadata",
    "announcements_metadata",
    "files_metadata",
}

BLOCKED_ENDPOINT_CLASSES = {
    "users",
    "enrollments",
    "submissions",
    "grades",
    "analytics",
    "conversations",
    "messages",
    "discussion_replies",
    "attendance",
    "student_work",
    "student_identity_data",
    "create",
    "update",
    "delete",
    "publish",
}

# Store only metadata keys. Drop body/content/description/message/syllabus-like fields.
SAFE_KEYS_BY_ENDPOINT = {
    "course_metadata": {
        "id", "name", "course_code", "workflow_state", "account_id", "root_account_id",
        "start_at", "end_at", "created_at", "time_zone", "default_view", "uuid",
        "is_public", "license", "public_syllabus", "storage_quota_mb",
    },
    "modules": {
        "id", "name", "position", "unlock_at", "require_sequential_progress",
        "publish_final_grade", "published", "items_count", "state", "workflow_state",
    },
    "module_items": {
        "id", "module_id", "position", "title", "type", "content_id", "indent",
        "page_url", "published", "completion_requirement", "quiz_lti",
    },
    "pages_metadata": {
        "page_id", "url", "title", "created_at", "updated_at", "editing_roles",
        "published", "hide_from_students", "front_page", "todo_date",
    },
    "assignments_metadata": {
        "id", "name", "created_at", "updated_at", "due_at", "unlock_at", "lock_at",
        "points_possible", "grading_type", "submission_types", "workflow_state",
        "published", "muted", "anonymous_grading", "allowed_extensions",
        "position", "post_manually", "omit_from_final_grade",
    },
    "announcements_metadata": {
        "id", "title", "posted_at", "delayed_post_at", "last_reply_at",
        "require_initial_post", "user_name", "discussion_type", "workflow_state",
        "published", "locked", "pinned", "subscribed", "read_state",
    },
    "files_metadata": {
        "id", "uuid", "folder_id", "display_name", "filename", "content-type",
        "url", "size", "created_at", "updated_at", "unlock_at", "locked",
        "hidden", "locked_for_user", "visibility_level", "thumbnail_url",
        "modified_at", "mime_class", "media_entry_id",
    },
}


def fail(message: str) -> int:
    print(f"FAIL: {message}", file=sys.stderr)
    return 1


def pass_msg(message: str) -> None:
    print(f"PASS: {message}")


def normalize_base_url(value: str) -> str:
    clean = value.strip().rstrip("/")
    parsed = urllib.parse.urlparse(clean)
    if parsed.scheme != "https":
        raise ValueError("CANVAS_BASE_URL must start with https://")
    if not parsed.netloc:
        raise ValueError("CANVAS_BASE_URL must include a host")
    return clean


def validate_common(course_id: str, staging_root: Path) -> list[str]:
    errors: list[str] = []

    if course_id != APPROVED_COURSE_ID:
        errors.append(f"course ID must be {APPROVED_COURSE_ID}; got {course_id}")

    normalized = staging_root.as_posix().rstrip("/")
    approved = APPROVED_STAGING_ROOT.as_posix()
    if normalized != approved:
        errors.append(f"staging path must be {approved}; got {normalized}")

    return errors


def endpoint_plan(course_id: str) -> dict[str, str]:
    return {
        "course_metadata": f"/api/v1/courses/{course_id}",
        "modules": f"/api/v1/courses/{course_id}/modules?per_page=100",
        "pages_metadata": f"/api/v1/courses/{course_id}/pages?per_page=100",
        "assignments_metadata": f"/api/v1/courses/{course_id}/assignments?per_page=100",
        "announcements_metadata": f"/api/v1/announcements?context_codes[]=course_{course_id}&per_page=100",
        "files_metadata": f"/api/v1/courses/{course_id}/files?per_page=100",
    }


def safe_record(endpoint_class: str, record: Any) -> Any:
    if isinstance(record, list):
        return [safe_record(endpoint_class, item) for item in record]

    if not isinstance(record, dict):
        return record

    allowed = SAFE_KEYS_BY_ENDPOINT[endpoint_class]
    cleaned = {key: record[key] for key in sorted(allowed) if key in record}

    # Keep relationship ID for nested module-item fetches.
    if endpoint_class == "module_items" and "module_id" not in cleaned and "module_id" in record:
        cleaned["module_id"] = record["module_id"]

    return cleaned


def read_paginated_json(base_url: str, token: str, path: str) -> list[Any]:
    results: list[Any] = []
    next_url: str | None = f"{base_url}{path}"

    while next_url:
        request = urllib.request.Request(
            next_url,
            method="GET",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
                "User-Agent": "teacher-ai-workstation-canvas-phase-9b-read-only-metadata",
            },
        )

        with urllib.request.urlopen(request, timeout=30) as response:
            status = getattr(response, "status", None)
            if status is not None and not (200 <= status < 300):
                raise RuntimeError(f"Canvas API returned HTTP {status}")

            payload = json.loads(response.read().decode("utf-8"))
            if isinstance(payload, list):
                results.extend(payload)
            else:
                results.append(payload)

            next_url = parse_next_link(response.headers.get("Link"))

    return results


def parse_next_link(link_header: str | None) -> str | None:
    if not link_header:
        return None

    for part in link_header.split(","):
        section = part.strip()
        if 'rel="next"' not in section:
            continue
        if section.startswith("<") and ">" in section:
            return section[1:section.index(">")]

    return None


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def cmd_plan(args: argparse.Namespace) -> int:
    errors = validate_common(args.course_id, Path(args.staging_root))
    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1

    plan = {
        "phase": "canvas_llm_phase_9b_sandbox_api_metadata_fetch",
        "mode": "plan",
        "course_id": args.course_id,
        "source_class": APPROVED_SOURCE_CLASS,
        "read_only": True,
        "metadata_only": True,
        "local_staging_root": str(APPROVED_STAGING_ROOT),
        "token_env_name": TOKEN_ENV_NAME,
        "base_url_env_name": BASE_URL_ENV_NAME,
        "token_value_printed": False,
        "approval_flag_required": APPROVAL_FLAG,
        "allowed_endpoint_classes": sorted(ALLOWED_ENDPOINT_CLASSES),
        "blocked_endpoint_classes": sorted(BLOCKED_ENDPOINT_CLASSES),
        "endpoint_plan": endpoint_plan(args.course_id),
        "rollback_command": f"rm -rf {APPROVED_STAGING_ROOT}",
        "canvas_write": False,
        "student_data": False,
        "real_curriculum_body_ingestion": False,
        "runtime_database_write": False,
        "generation_rag_embeddings": False,
    }

    pass_msg("plan generated without Canvas API call")
    pass_msg("course ID guard accepted 24399")
    pass_msg("endpoint plan is metadata-only")
    pass_msg("token value was not read or printed")
    print(json.dumps(plan, indent=2, sort_keys=True))
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    errors = validate_common(args.course_id, Path(args.staging_root))
    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1

    pass_msg("validation accepted approved course ID 24399")
    pass_msg("validation accepted approved local staging path")
    pass_msg("live fetch requires explicit approval flag")
    pass_msg("CANVAS_BASE_URL and CANVAS_API_TOKEN are local environment variables only")
    pass_msg("token value is never printed")
    return 0


def cmd_live_fetch(args: argparse.Namespace) -> int:
    errors = validate_common(args.course_id, Path(args.staging_root))
    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1

    if not args.i_understand_this_uses_read_only_canvas_api:
        return fail(f"live fetch requires explicit approval flag: {APPROVAL_FLAG}")

    token = os.environ.get(TOKEN_ENV_NAME)
    if not token:
        return fail(f"{TOKEN_ENV_NAME} is required for live fetch but was not printed")

    base_url_value = os.environ.get(BASE_URL_ENV_NAME)
    if not base_url_value:
        return fail(f"{BASE_URL_ENV_NAME} is required for live fetch")

    try:
        base_url = normalize_base_url(base_url_value)
    except ValueError as exc:
        return fail(str(exc))

    staging_root = Path(args.staging_root)
    staging_root.mkdir(parents=True, exist_ok=True)

    endpoints = endpoint_plan(args.course_id)
    manifest: dict[str, Any] = {
        "phase": "canvas_llm_phase_9b_sandbox_api_metadata_fetch",
        "course_id": args.course_id,
        "source_class": APPROVED_SOURCE_CLASS,
        "fetched_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "base_url_host": urllib.parse.urlparse(base_url).netloc,
        "read_only": True,
        "metadata_only": True,
        "token_value_printed": False,
        "canvas_write": False,
        "student_data": False,
        "real_curriculum_body_ingestion": False,
        "files": [],
    }

    pass_msg("starting approved read-only Canvas metadata fetch for course 24399")
    pass_msg("token value is not printed")

    for endpoint_class, path in endpoints.items():
        raw_records = read_paginated_json(base_url, token, path)
        safe_records = safe_record(endpoint_class, raw_records)
        output_path = staging_root / f"{endpoint_class}.json"
        write_json(output_path, safe_records)
        manifest["files"].append(
            {
                "endpoint_class": endpoint_class,
                "path": str(output_path),
                "record_count": len(safe_records) if isinstance(safe_records, list) else 1,
                "sanitized": True,
            }
        )
        pass_msg(f"wrote sanitized metadata: {output_path}")

    modules_path = staging_root / "modules.json"
    modules = json.loads(modules_path.read_text(encoding="utf-8")) if modules_path.exists() else []
    module_item_records = []
    for module in modules:
        module_id = module.get("id")
        if module_id is None:
            continue
        path = f"/api/v1/courses/{args.course_id}/modules/{module_id}/items?per_page=100"
        raw_items = read_paginated_json(base_url, token, path)
        for item in raw_items:
            if isinstance(item, dict):
                item["module_id"] = module_id
        module_item_records.extend(raw_items)

    safe_module_items = safe_record("module_items", module_item_records)
    module_items_path = staging_root / "module_items.json"
    write_json(module_items_path, safe_module_items)
    manifest["files"].append(
        {
            "endpoint_class": "module_items",
            "path": str(module_items_path),
            "record_count": len(safe_module_items),
            "sanitized": True,
        }
    )
    pass_msg(f"wrote sanitized metadata: {module_items_path}")

    manifest_path = staging_root / "manifest.json"
    write_json(manifest_path, manifest)
    pass_msg(f"wrote local staging manifest: {manifest_path}")
    pass_msg("completed approved read-only metadata fetch")
    return 0


def cmd_rollback(args: argparse.Namespace) -> int:
    errors = validate_common(args.course_id, Path(args.staging_root))
    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print(f"Rollback command: rm -rf {Path(args.staging_root)}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Phase 9B approved read-only Canvas sandbox metadata fetcher."
    )
    parser.add_argument("--course-id", default=APPROVED_COURSE_ID)
    parser.add_argument("--staging-root", default=str(APPROVED_STAGING_ROOT))

    subcommands = parser.add_subparsers(dest="command", required=True)

    plan = subcommands.add_parser("plan")
    plan.set_defaults(func=cmd_plan)

    validate = subcommands.add_parser("validate")
    validate.set_defaults(func=cmd_validate)

    live_fetch = subcommands.add_parser("live-fetch")
    live_fetch.add_argument(
        "--i-understand-this-uses-read-only-canvas-api",
        action="store_true",
    )
    live_fetch.set_defaults(func=cmd_live_fetch)

    rollback = subcommands.add_parser("rollback")
    rollback.set_defaults(func=cmd_rollback)

    return parser


def main() -> int:
    args = build_parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
