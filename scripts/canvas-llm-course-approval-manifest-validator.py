#!/usr/bin/env python3
"""Validate the Canvas LLM Phase 14A approved course manifest.

This validator is local/read-only and validates the tracked manifest only.
It performs no Canvas API calls, course enumeration, file downloads, database
writes, RAG, embeddings, local model execution, or lesson generation.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = REPO_ROOT / "config/canvas-llm/approved-canvas-course-manifest.json"

EXPECTED_COURSE_IDS = {
    26404, 26442, 26495, 26493, 26496, 26427,
    24399,
    21957, 21919, 21944, 21934, 21970, 22254,
    19428, 19419, 19426, 19422, 19423, 19424,
}

EXPECTED_SHARED_PREFIX_COURSES = {
    26442: ["RM4", "SPELL"],
    21919: ["RM4", "SPELL"],
    19419: ["RM4", "SPELL"],
}

EXPECTED_ROLES = {
    "current_operational_course",
    "current_homeroom_newsletter_course",
    "historical_academic_course",
    "historical_homeroom_newsletter_course",
    "demo_sandbox_course",
}

EXPECTED_ALLOWED_METADATA = {
    "course_metadata",
    "folders_metadata",
    "files_metadata",
    "modules_metadata",
    "module_items_metadata",
    "pages_metadata",
    "announcements_metadata",
    "assignments_metadata_for_relationship_mapping",
}

EXPECTED_BLOCKED = {
    "student_data",
    "users",
    "enrollments",
    "rosters",
    "submissions",
    "grades",
    "analytics",
    "attendance",
    "conversations",
    "discussion_entries",
    "quiz_responses",
    "file_downloads",
    "file_contents",
    "page_bodies",
    "announcement_bodies",
    "assignment_bodies",
    "canvas_writes",
    "renames",
    "moves",
    "deletes",
    "uploads",
    "publish_changes",
}


def emit(status: str, message: str) -> None:
    print(f"{status}: {message}")


def git_check_ignored(path: str) -> bool:
    result = subprocess.run(
        ["git", "check-ignore", "-q", path],
        cwd=REPO_ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0


def git_ls_files(path: str) -> str:
    result = subprocess.run(
        ["git", "ls-files", path],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return result.stdout.strip()


def main() -> int:
    passes = 0
    warnings = 0
    failures = 0

    def passed(message: str) -> None:
        nonlocal passes
        passes += 1
        emit("PASS", message)

    def warned(message: str) -> None:
        nonlocal warnings
        warnings += 1
        emit("WARN", message)

    def failed(message: str) -> None:
        nonlocal failures
        failures += 1
        emit("FAIL", message)

    if not MANIFEST_PATH.exists():
        failed("Approved Canvas course manifest exists")
        print(f"Phase 14A manifest validator: PASS {passes} / WARN {warnings} / FAIL {failures}")
        return 1

    try:
        data: dict[str, Any] = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        failed(f"Manifest JSON parses: {exc}")
        print(f"Phase 14A manifest validator: PASS {passes} / WARN {warnings} / FAIL {failures}")
        return 1

    passed("Approved Canvas course manifest JSON parses")

    if data.get("manifest") == "approved_canvas_course_manifest":
        passed("Manifest type is approved_canvas_course_manifest")
    else:
        failed("Manifest type is incorrect")

    if data.get("phase") == "canvas_llm_phase_14a_course_approval_manifest":
        passed("Manifest identifies Phase 14A")
    else:
        failed("Manifest phase is incorrect")

    safety = data.get("safety", {})
    for flag in [
        "api_fetch_performed_by_this_manifest",
        "canvas_write_approved",
        "file_download_approved",
        "body_ingestion_approved",
        "student_data_approved",
        "tracked_school_canvas_url",
        "tracked_tokens_or_secrets",
        "committed_local_fetched_metadata",
    ]:
        if safety.get(flag) is False:
            passed(f"Safety flag {flag}=false")
        else:
            failed(f"Safety flag {flag} must be false")

    courses = data.get("courses")
    if isinstance(courses, list) and courses:
        passed("Manifest has course list")
    else:
        failed("Manifest course list is missing or empty")
        courses = []

    course_ids = [course.get("course_id") for course in courses if isinstance(course, dict)]
    course_id_set = set(course_ids)

    if course_id_set == EXPECTED_COURSE_IDS:
        passed("Manifest contains exactly the approved Canvas course IDs")
    else:
        failed(f"Manifest course IDs mismatch: {sorted(course_id_set)}")

    if len(course_ids) == 19:
        passed("Manifest contains 19 approved course rows")
    else:
        failed(f"Manifest should contain 19 course rows, found {len(course_ids)}")

    for course_id, prefixes in EXPECTED_SHARED_PREFIX_COURSES.items():
        matches = [course for course in courses if course.get("course_id") == course_id]
        if len(matches) == 1 and matches[0].get("canonical_prefixes") == prefixes:
            passed(f"Shared Reading/Spelling course {course_id} has RM4 and SPELL prefixes")
        else:
            failed(f"Shared Reading/Spelling course {course_id} does not have expected prefixes")

    roles = {course.get("course_role") for course in courses if isinstance(course, dict)}
    if EXPECTED_ROLES.issubset(roles):
        passed("Manifest includes all expected course roles")
    else:
        failed(f"Manifest missing expected roles: {sorted(EXPECTED_ROLES - roles)}")

    homeroom_ids = {
        course.get("course_id")
        for course in courses
        if "homeroom_newsletter_course" in str(course.get("course_role"))
    }
    if homeroom_ids == {26427, 22254, 19424}:
        passed("Manifest includes current and historical Homeroom newsletter courses")
    else:
        failed(f"Homeroom course IDs mismatch: {sorted(homeroom_ids)}")

    demo_ids = {
        course.get("course_id")
        for course in courses
        if course.get("course_role") == "demo_sandbox_course"
    }
    if demo_ids == {24399}:
        passed("Manifest includes approved demo sandbox course 24399")
    else:
        failed(f"Demo sandbox course IDs mismatch: {sorted(demo_ids)}")

    future_scope = data.get("future_fetch_scope", {})
    allowed_metadata = set(future_scope.get("allowed_metadata_categories", []))
    if EXPECTED_ALLOWED_METADATA.issubset(allowed_metadata):
        passed("Manifest includes all expected allowed metadata categories")
    else:
        failed(f"Manifest missing allowed metadata categories: {sorted(EXPECTED_ALLOWED_METADATA - allowed_metadata)}")

    blocked = set(future_scope.get("blocked_data_classes", []))
    if EXPECTED_BLOCKED.issubset(blocked):
        passed("Manifest includes all expected blocked data classes")
    else:
        failed(f"Manifest missing blocked data classes: {sorted(EXPECTED_BLOCKED - blocked)}")

    manifest_text = MANIFEST_PATH.read_text(encoding="utf-8")
    forbidden_markers = [
        "canvas.instructure.com",
        "Authorization: Bearer",
        "CANVAS_TOKEN",
        "canvas_token",
        "access_token",
        "Bearer ",
        "https://",
    ]
    for marker in forbidden_markers:
        if marker in manifest_text:
            failed(f"Manifest contains forbidden marker: {marker}")
        else:
            passed(f"Manifest does not contain forbidden marker: {marker}")

    if git_check_ignored(".local/canvas-llm/sandbox-metadata/course-24399/manifest.json"):
        passed(".local Canvas metadata manifest is ignored")
    else:
        failed(".local Canvas metadata manifest is not ignored")

    if not git_ls_files(".local/canvas-llm"):
        passed(".local Canvas metadata is not tracked")
    else:
        failed(".local Canvas metadata is tracked")

    if failures == 0 and warnings == 0:
        passed("Phase 14A course approval manifest is ready for a later read-only fetch phase")

    print(f"Phase 14A manifest validator: PASS {passes} / WARN {warnings} / FAIL {failures}")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
