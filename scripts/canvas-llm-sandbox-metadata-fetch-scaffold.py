#!/usr/bin/env python3
"""Canvas LLM Phase 9A sandbox metadata fetch scaffold.

Phase 9A is scaffold/gate-only.
Default behavior is dry-run and performs no network/API/OAuth/live Canvas access.

Approved scope:
- Course ID: 24399 only
- Source class: sandbox_demo_canvas_course
- Read-only only
- Metadata-only only
- Local staging only

Blocked:
- Any other course ID
- Student data endpoints
- Users/enrollments/submissions/grades
- Canvas writes/publishing
- Real curriculum body ingestion
- Runtime DB writes
- RAG/embeddings/generation
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any

APPROVED_COURSE_ID = "24399"
APPROVED_SOURCE_CLASS = "sandbox_demo_canvas_course"
APPROVED_STAGING_ROOT = Path(".local/canvas-llm/sandbox-metadata/course-24399")

ALLOWED_ENDPOINT_CLASSES = {
    "course_metadata": "/api/v1/courses/24399",
    "modules": "/api/v1/courses/24399/modules",
    "module_items": "/api/v1/courses/24399/modules/{module_id}/items",
    "pages_metadata": "/api/v1/courses/24399/pages",
    "assignments_metadata": "/api/v1/courses/24399/assignments",
    "announcements_metadata": "/api/v1/announcements?context_codes[]=course_24399",
    "files_metadata": "/api/v1/courses/24399/files",
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

TOKEN_ENV_NAME = "CANVAS_API_TOKEN"


def fail(message: str) -> int:
    print(f"FAIL: {message}", file=sys.stderr)
    return 1


def pass_msg(message: str) -> None:
    print(f"PASS: {message}")


def build_plan(course_id: str) -> dict[str, Any]:
    return {
        "phase": "canvas_llm_phase_9a_sandbox_metadata_fetch_scaffold",
        "mode": "dry_run",
        "runtime_activation": "no",
        "course_id": course_id,
        "source_class": APPROVED_SOURCE_CLASS,
        "read_only": True,
        "metadata_only": True,
        "local_staging_root": str(APPROVED_STAGING_ROOT),
        "token_env_name": TOKEN_ENV_NAME,
        "token_value_printed": False,
        "allowed_endpoint_classes": ALLOWED_ENDPOINT_CLASSES,
        "blocked_endpoint_classes": sorted(BLOCKED_ENDPOINT_CLASSES),
        "rollback_command": f"rm -rf {APPROVED_STAGING_ROOT}",
        "network_access": False,
        "canvas_api_call": False,
        "oauth": False,
        "live_read": False,
        "canvas_write": False,
        "student_data": False,
        "real_curriculum_body_ingestion": False,
        "runtime_database_write": False,
        "generation_rag_embeddings": False,
    }


def validate_common(course_id: str, staging_root: Path) -> list[str]:
    errors: list[str] = []

    if course_id != APPROVED_COURSE_ID:
        errors.append(f"course ID must be {APPROVED_COURSE_ID}; got {course_id}")

    normalized = staging_root.as_posix().rstrip("/")
    approved = APPROVED_STAGING_ROOT.as_posix()
    if normalized != approved:
        errors.append(f"staging path must be {approved}; got {normalized}")

    return errors


def cmd_dry_run(args: argparse.Namespace) -> int:
    staging_root = Path(args.staging_root)
    errors = validate_common(args.course_id, staging_root)
    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1

    plan = build_plan(args.course_id)
    pass_msg("dry-run only; no network/API/OAuth/live Canvas access performed")
    pass_msg("course ID guard accepted 24399")
    pass_msg("endpoint allowlist is metadata-only")
    pass_msg("student-data endpoint classes remain blocked")
    pass_msg("token value was not read or printed")
    pass_msg("staging path guard accepted approved local staging path")
    print(json.dumps(plan, indent=2, sort_keys=True))
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    staging_root = Path(args.staging_root)
    errors = validate_common(args.course_id, staging_root)

    if TOKEN_ENV_NAME in os.environ:
        pass_msg(f"{TOKEN_ENV_NAME} environment variable is present but token value is not printed")
    else:
        pass_msg(f"{TOKEN_ENV_NAME} environment variable is not required for dry-run validation")

    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1

    pass_msg("validation accepted approved course ID 24399")
    pass_msg("validation accepted approved local staging path")
    pass_msg("no live fetch is implemented in Phase 9A")
    pass_msg("no Canvas API call was performed")
    return 0


def cmd_rollback(args: argparse.Namespace) -> int:
    staging_root = Path(args.staging_root)
    errors = validate_common(args.course_id, staging_root)
    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1

    if args.execute:
        shutil.rmtree(staging_root, ignore_errors=True)
        pass_msg(f"removed approved local staging path: {staging_root}")
    else:
        pass_msg("rollback dry-run only")
        print(f"Rollback command: rm -rf {staging_root}")

    return 0


def cmd_live_fetch(_: argparse.Namespace) -> int:
    return fail(
        "live Canvas fetch is intentionally not implemented in Phase 9A; "
        "create a separately approved execution phase before any network/API access"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Phase 9A gated scaffold for future read-only Canvas sandbox metadata fetch."
    )
    parser.add_argument("--course-id", default=APPROVED_COURSE_ID)
    parser.add_argument("--staging-root", default=str(APPROVED_STAGING_ROOT))

    subcommands = parser.add_subparsers(dest="command", required=True)

    dry_run = subcommands.add_parser("dry-run")
    dry_run.set_defaults(func=cmd_dry_run)

    validate = subcommands.add_parser("validate")
    validate.set_defaults(func=cmd_validate)

    rollback = subcommands.add_parser("rollback")
    rollback.add_argument("--execute", action="store_true")
    rollback.set_defaults(func=cmd_rollback)

    live_fetch = subcommands.add_parser("live-fetch")
    live_fetch.set_defaults(func=cmd_live_fetch)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
