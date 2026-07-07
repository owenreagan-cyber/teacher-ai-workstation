#!/usr/bin/env python3
"""Canvas LLM Phase 14B read-only approved course metadata fetcher.

Approved live scope:
- Course IDs from config/canvas-llm/approved-canvas-course-manifest.json only
- Read-only Canvas API GET requests only
- Metadata-only sanitized output only
- Ignored local staging output only

Blocked:
- Canvas writes, file downloads, page/announcement/assignment bodies
- Users, enrollments, rosters, submissions, grades, analytics, attendance
- Student data, messages, discussion entries/replies, quiz responses
- Knowledge DB/runtime DB/production/canonical catalog writes
- RAG, embeddings, local model execution, lesson generation
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

MANIFEST_PATH = Path("config/canvas-llm/approved-canvas-course-manifest.json")
APPROVED_STAGING_ROOT = Path(".local/canvas-llm/approved-course-metadata")
TOKEN_ENV_NAME = "CANVAS_API_TOKEN"
BASE_URL_ENV_NAME = "CANVAS_BASE_URL"
APPROVAL_FLAG = "--i-understand-this-uses-read-only-canvas-api"

ALLOWED_METADATA_CATEGORIES = {
    "course_metadata",
    "folders_metadata",
    "files_metadata",
    "modules_metadata",
    "module_items_metadata",
    "pages_metadata",
    "announcements_metadata",
    "assignments_metadata_for_relationship_mapping",
}

BLOCKED_ENDPOINT_CLASSES = {
    "users",
    "enrollments",
    "rosters",
    "submissions",
    "grades",
    "analytics",
    "attendance",
    "conversations",
    "messages",
    "discussion_entries",
    "discussion_replies",
    "quiz_responses",
    "file_downloads",
    "file_contents",
    "page_bodies",
    "announcement_bodies",
    "assignment_bodies",
    "create",
    "update",
    "delete",
    "publish",
    "upload",
    "move",
    "rename",
}

SAFE_KEYS_BY_CATEGORY = {
    "course_metadata": {
        "id", "name", "course_code", "workflow_state", "account_id", "root_account_id",
        "start_at", "end_at", "created_at", "time_zone", "default_view", "uuid",
        "is_public", "license", "public_syllabus", "storage_quota_mb",
    },
    "folders_metadata": {
        "id", "name", "full_name", "context_id", "context_type", "parent_folder_id",
        "position", "folders_count", "files_count", "locked", "hidden", "locked_for_user",
        "created_at", "updated_at",
    },
    "files_metadata": {
        "id", "uuid", "folder_id", "display_name", "filename", "content-type",
        "size", "created_at", "updated_at", "unlock_at", "locked", "hidden",
        "locked_for_user", "visibility_level", "modified_at", "mime_class",
        "media_entry_id",
    },
    "modules_metadata": {
        "id", "name", "position", "unlock_at", "require_sequential_progress",
        "publish_final_grade", "published", "items_count", "state", "workflow_state",
    },
    "module_items_metadata": {
        "id", "module_id", "position", "title", "type", "content_id", "indent",
        "page_url", "published", "completion_requirement", "quiz_lti",
    },
    "pages_metadata": {
        "page_id", "url", "title", "created_at", "updated_at", "editing_roles",
        "published", "hide_from_students", "front_page", "todo_date",
    },
    "announcements_metadata": {
        "id", "title", "posted_at", "delayed_post_at", "last_reply_at",
        "require_initial_post", "user_name", "discussion_type", "workflow_state",
        "published", "locked", "pinned", "subscribed", "read_state",
    },
    "assignments_metadata": {
        "id", "name", "created_at", "updated_at", "due_at", "unlock_at", "lock_at",
        "points_possible", "grading_type", "submission_types", "workflow_state",
        "published", "muted", "anonymous_grading", "allowed_extensions",
        "position", "post_manually", "omit_from_final_grade", "module_ids",
    },
}

BODY_KEYS = {
    "body",
    "description",
    "message",
    "html_url",
    "url",
    "preview_url",
    "download_url",
    "syllabus_body",
    "submission",
    "submissions",
    "rubric",
    "discussion_subentry_count",
}


def fail(message: str) -> int:
    print(f"FAIL: {message}", file=sys.stderr)
    return 1


def pass_msg(message: str) -> None:
    print(f"PASS: {message}")


def warn_msg(message: str) -> None:
    print(f"WARN: {message}")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_manifest() -> dict[str, Any]:
    manifest = read_json(MANIFEST_PATH)
    approved = set(manifest["future_fetch_scope"]["allowed_metadata_categories"])
    if approved != ALLOWED_METADATA_CATEGORIES:
        raise ValueError("Phase 14A manifest approved metadata categories do not match Phase 14B allowlist")
    return manifest


def approved_courses(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(course["course_id"]): course for course in manifest["courses"]}


def normalize_base_url(value: str) -> str:
    clean = value.strip().rstrip("/")
    parsed = urllib.parse.urlparse(clean)
    if parsed.scheme != "https":
        raise ValueError(f"{BASE_URL_ENV_NAME} must start with https://")
    if not parsed.netloc:
        raise ValueError(f"{BASE_URL_ENV_NAME} must include a host")
    return clean


def parse_course_ids(raw: str | None, approved: dict[str, dict[str, Any]]) -> list[str]:
    if not raw or raw == "all":
        return sorted(approved, key=int)
    requested = [part.strip() for part in raw.split(",") if part.strip()]
    unapproved = sorted(set(requested) - set(approved), key=str)
    if unapproved:
        raise ValueError(f"unapproved course IDs requested: {', '.join(unapproved)}")
    return requested


def validate_staging_root(path: Path) -> None:
    normalized = path.as_posix().rstrip("/")
    approved = APPROVED_STAGING_ROOT.as_posix()
    if normalized != approved:
        raise ValueError(f"staging path must be {approved}; got {normalized}")


def endpoint_plan(course_id: str) -> dict[str, str]:
    return {
        "course_metadata": f"/api/v1/courses/{course_id}",
        "folders_metadata": f"/api/v1/courses/{course_id}/folders?per_page=100",
        "files_metadata": f"/api/v1/courses/{course_id}/files?per_page=100",
        "modules_metadata": f"/api/v1/courses/{course_id}/modules?per_page=100",
        "pages_metadata": f"/api/v1/courses/{course_id}/pages?per_page=100",
        "announcements_metadata": f"/api/v1/announcements?context_codes[]=course_{course_id}&per_page=100",
        "assignments_metadata": f"/api/v1/courses/{course_id}/assignments?per_page=100",
    }


def validate_path(category: str, path: str) -> None:
    lowered = path.lower()
    if category not in SAFE_KEYS_BY_CATEGORY:
        raise ValueError(f"unallowlisted metadata category: {category}")
    for blocked in BLOCKED_ENDPOINT_CLASSES:
        token = blocked.replace("_", "/")
        if f"/{token}" in lowered or f"{token}?" in lowered:
            raise ValueError(f"blocked endpoint class in path for {category}: {blocked}")
    blocked_query_markers = ("include[]=body", "include[]=description", "include[]=submission")
    if any(marker in lowered for marker in blocked_query_markers):
        raise ValueError(f"blocked body/content include in path for {category}")


def safe_record(category: str, record: Any) -> Any:
    if isinstance(record, list):
        return [safe_record(category, item) for item in record]
    if not isinstance(record, dict):
        return record
    allowed = SAFE_KEYS_BY_CATEGORY[category]
    cleaned = {key: record[key] for key in sorted(allowed) if key in record}
    for key in BODY_KEYS:
        cleaned.pop(key, None)
    return cleaned


def record_count(records: Any) -> int:
    if isinstance(records, list):
        return len(records)
    if records is None:
        return 0
    return 1


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
                "User-Agent": "teacher-ai-workstation-canvas-phase-14b-read-only-metadata",
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


def course_output_root(staging_root: Path, course_id: str) -> Path:
    return staging_root / f"course-{course_id}"


def course_manifest(course: dict[str, Any], counts: dict[str, int], warnings: list[str]) -> dict[str, Any]:
    return {
        "phase": "canvas_llm_phase_14b_approved_course_metadata_fetch",
        "course_id": course["course_id"],
        "course_role": course["course_role"],
        "school_year": course["school_year"],
        "subject": course["subject"],
        "canonical_prefixes": course["canonical_prefixes"],
        "fetched_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "read_only": True,
        "metadata_only": True,
        "assignments_metadata_for_relationship_mapping_only": True,
        "pages_metadata_only": True,
        "announcements_metadata_only": True,
        "body_ingestion": False,
        "file_downloads": False,
        "canvas_write": False,
        "student_data": False,
        "counts": counts,
        "warnings": warnings,
        "files": {
            "course_metadata": "course_metadata.json",
            "folders_metadata": "folders_metadata.json",
            "files_metadata": "files_metadata.json",
            "modules_metadata": "modules_metadata.json",
            "module_items_metadata": "module_items_metadata.json",
            "pages_metadata": "pages_metadata.json",
            "announcements_metadata": "announcements_metadata.json",
            "assignments_metadata": "assignments_metadata.json",
        },
    }


def cmd_plan(args: argparse.Namespace) -> int:
    try:
        manifest = load_manifest()
        courses = approved_courses(manifest)
        course_ids = parse_course_ids(args.course_ids, courses)
        validate_staging_root(Path(args.staging_root))
    except ValueError as exc:
        return fail(str(exc))

    plan = {
        "phase": "canvas_llm_phase_14b_approved_course_metadata_fetch",
        "mode": "plan",
        "approved_manifest": str(MANIFEST_PATH),
        "course_ids": [int(course_id) for course_id in course_ids],
        "local_staging_root": str(APPROVED_STAGING_ROOT),
        "token_env_name": TOKEN_ENV_NAME,
        "base_url_env_name": BASE_URL_ENV_NAME,
        "token_value_printed": False,
        "approval_flag_required": APPROVAL_FLAG,
        "allowed_metadata_categories": sorted(ALLOWED_METADATA_CATEGORIES),
        "blocked_endpoint_classes": sorted(BLOCKED_ENDPOINT_CLASSES),
        "endpoint_plan_by_course": {course_id: endpoint_plan(course_id) for course_id in course_ids},
        "canvas_write": False,
        "file_downloads": False,
        "body_ingestion": False,
        "student_data": False,
        "database_writes": False,
    }
    pass_msg("plan generated without Canvas API call")
    pass_msg(f"approved course count: {len(course_ids)}")
    pass_msg("endpoint plan is metadata-only")
    pass_msg("token value was not read or printed")
    print(json.dumps(plan, indent=2, sort_keys=True))
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    try:
        manifest = load_manifest()
        courses = approved_courses(manifest)
        course_ids = parse_course_ids(args.course_ids, courses)
        validate_staging_root(Path(args.staging_root))
        for course_id in course_ids:
            for category, path in endpoint_plan(course_id).items():
                validate_path(category, path)
    except ValueError as exc:
        return fail(str(exc))

    pass_msg(f"validation accepted {len(course_ids)} approved course IDs")
    pass_msg("validation accepted approved local staging path")
    pass_msg("live fetch requires explicit approval flag")
    pass_msg(f"{BASE_URL_ENV_NAME} and {TOKEN_ENV_NAME} are local environment variables only")
    pass_msg("token value is never printed")
    pass_msg("Canvas endpoint plan is read-only metadata-only")
    return 0


def cmd_live_fetch(args: argparse.Namespace) -> int:
    try:
        manifest = load_manifest()
        courses = approved_courses(manifest)
        course_ids = parse_course_ids(args.course_ids, courses)
        staging_root = Path(args.staging_root)
        validate_staging_root(staging_root)
        for course_id in course_ids:
            for category, path in endpoint_plan(course_id).items():
                validate_path(category, path)
    except ValueError as exc:
        return fail(str(exc))

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

    staging_root.mkdir(parents=True, exist_ok=True)
    summaries: list[dict[str, Any]] = []

    pass_msg(f"starting approved read-only Canvas metadata fetch for {len(course_ids)} courses")
    pass_msg("token value is not printed")

    try:
        for course_id in course_ids:
            course = courses[course_id]
            output_root = course_output_root(staging_root, course_id)
            output_root.mkdir(parents=True, exist_ok=True)
            counts: dict[str, int] = {}
            warnings: list[str] = []

            for category, path in endpoint_plan(course_id).items():
                raw_records = read_paginated_json(base_url, token, path)
                safe_category = "assignments_metadata" if category == "assignments_metadata" else category
                safe_records = safe_record(safe_category, raw_records)
                filename = "assignments_metadata.json" if category == "assignments_metadata" else f"{category}.json"
                write_json(output_root / filename, safe_records)
                counts[filename.removesuffix(".json")] = record_count(safe_records)
                if counts[filename.removesuffix(".json")] == 0:
                    warning = f"{filename} has zero records"
                    warnings.append(warning)
                    warn_msg(f"course {course_id}: {warning}")
                pass_msg(f"course {course_id}: wrote metadata {filename}")

            module_item_records: list[Any] = []
            modules = read_json(output_root / "modules_metadata.json")
            for module in modules if isinstance(modules, list) else []:
                module_id = module.get("id") if isinstance(module, dict) else None
                if module_id is None:
                    continue
                path = f"/api/v1/courses/{course_id}/modules/{module_id}/items?per_page=100"
                validate_path("module_items_metadata", path)
                raw_items = read_paginated_json(base_url, token, path)
                for item in raw_items:
                    if isinstance(item, dict):
                        item["module_id"] = module_id
                module_item_records.extend(raw_items)

            safe_module_items = safe_record("module_items_metadata", module_item_records)
            write_json(output_root / "module_items_metadata.json", safe_module_items)
            counts["module_items_metadata"] = record_count(safe_module_items)
            if counts["module_items_metadata"] == 0:
                warning = "module_items_metadata.json has zero records"
                warnings.append(warning)
                warn_msg(f"course {course_id}: {warning}")

            write_json(output_root / "manifest.json", course_manifest(course, counts, warnings))
            summaries.append(
                {
                    "course_id": int(course_id),
                    "course_role": course["course_role"],
                    "school_year": course["school_year"],
                    "subject": course["subject"],
                    "counts": counts,
                    "warnings": warnings,
                }
            )
            pass_msg(f"course {course_id}: wrote local staging manifest")
    except Exception as exc:
        return fail(f"Canvas metadata fetch stopped: {exc}")

    top_manifest = {
        "phase": "canvas_llm_phase_14b_approved_course_metadata_fetch",
        "fetched_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "approved_manifest": str(MANIFEST_PATH),
        "course_count": len(summaries),
        "course_ids": [item["course_id"] for item in summaries],
        "read_only": True,
        "metadata_only": True,
        "token_value_printed": False,
        "tracked_school_canvas_url": False,
        "canvas_write": False,
        "file_downloads": False,
        "body_ingestion": False,
        "student_data": False,
        "database_writes": False,
        "courses": summaries,
    }
    write_json(staging_root / "manifest.json", top_manifest)
    pass_msg(f"wrote local staging manifest: {staging_root / 'manifest.json'}")
    pass_msg("completed approved read-only metadata fetch")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Phase 14B approved read-only Canvas course metadata fetcher."
    )
    parser.add_argument("--course-ids", default="all", help="Comma-separated approved course IDs, or all.")
    parser.add_argument("--staging-root", default=str(APPROVED_STAGING_ROOT))

    subcommands = parser.add_subparsers(dest="command", required=True)

    plan = subcommands.add_parser("plan")
    plan.set_defaults(func=cmd_plan)

    validate = subcommands.add_parser("validate")
    validate.set_defaults(func=cmd_validate)

    live_fetch = subcommands.add_parser("live-fetch")
    live_fetch.add_argument(APPROVAL_FLAG, action="store_true")
    live_fetch.set_defaults(func=cmd_live_fetch)

    return parser


def main() -> int:
    args = build_parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
