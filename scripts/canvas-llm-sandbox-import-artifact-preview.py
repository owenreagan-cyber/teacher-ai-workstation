#!/usr/bin/env python3
"""Validate the Canvas LLM Phase 12 fake/local import artifact preview fixture.

This validator is intentionally local, read-only, and fixture-only. It must not
read Canvas credentials, call Canvas APIs, import into a knowledge DB, write to
runtime databases, write to production registries, ingest curriculum bodies,
create embeddings, or execute local models.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_PATH = (
    REPO_ROOT
    / "fixtures"
    / "canvas-llm"
    / "import-preview"
    / "fake-local-sandbox-import-artifact-course-24399.json"
)

APPROVED_COURSE_ID = 24399
EXPECTED_COUNTS = {
    "course_metadata": 1,
    "modules": 3,
    "pages_metadata": 48,
    "assignments_metadata": 115,
    "announcements_metadata": 0,
    "files_metadata": 220,
    "module_items": 185,
}
EXPECTED_WARNING = "announcements_metadata has 0 records in sandbox staging"

MUST_BE_FALSE_FLAGS = [
    "real_metadata_copied",
    "import_performed",
    "knowledge_db_write",
    "runtime_database_write",
    "canvas_api_call",
    "production_write",
    "canonical_catalog_write",
    "student_data",
    "real_curriculum_body_ingestion",
    "generation_rag_embeddings",
    "local_model_ollama_execution",
    "tracked_school_canvas_url",
    "tracked_tokens_or_secrets",
    "local_staging_committed",
]

MUST_BE_TRUE_FLAGS = [
    "based_on_reviewed_phase_11_shape",
]


def emit(status: str, message: str) -> None:
    print(f"{status}: {message}")


def pass_fail(condition: bool, pass_message: str, fail_message: str) -> bool:
    if condition:
        emit("PASS", pass_message)
        return True
    emit("FAIL", fail_message)
    return False


def git_output(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def load_artifact() -> tuple[dict[str, Any] | None, list[str]]:
    if not ARTIFACT_PATH.exists():
        return None, [f"Phase 12 artifact missing: {ARTIFACT_PATH.relative_to(REPO_ROOT)}"]

    try:
        data = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, [f"Phase 12 artifact JSON does not parse: {exc}"]

    if not isinstance(data, dict):
        return None, ["Phase 12 artifact root must be a JSON object"]

    return data, []


def check_git_ignored(path: str) -> bool:
    result = subprocess.run(
        ["git", "check-ignore", "-q", path],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0


def check_no_tracked_local_staging() -> bool:
    result = git_output(["git", "ls-files", ".local/canvas-llm"])
    return result.returncode == 0 and not result.stdout.strip()


def check_no_sensitive_markers() -> bool:
    """Check Phase 12 tracked outputs, not legacy repo safety fixtures.

    The repo already contains older validators and negative fixtures that
    intentionally name blocked patterns such as canvas.instructure.com,
    access_token, and canvas_token. Phase 12 should prove that the new tracked
    fake/local artifact and its README do not introduce those markers.
    """

    phase12_paths = [
        REPO_ROOT / "fixtures/canvas-llm/import-preview/README.md",
        ARTIFACT_PATH,
    ]
    blocked_patterns = [
        "canvas.instructure.com",
        "Authorization: Bearer",
        "CANVAS_TOKEN",
        "canvas_token",
        "access_token",
        "Bearer ",
    ]

    blocked = []
    for phase12_path in phase12_paths:
        if not phase12_path.exists():
            continue
        text = phase12_path.read_text(encoding="utf-8")
        for pattern in blocked_patterns:
            if pattern in text:
                blocked.append(f"{phase12_path.relative_to(REPO_ROOT)} contains {pattern}")

    if blocked:
        for line in blocked:
            emit("FAIL", f"Potential Phase 12 Canvas URL/token marker: {line}")
        return False

    return True


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

    data, load_failures = load_artifact()
    if data is None:
        for message in load_failures:
            failed(message)
        print(f"Phase 12 artifact preview: PASS {passes} / WARN {warnings} / FAIL {failures}")
        return 1

    passed("Phase 12 fake/local import artifact JSON parses")

    if data.get("phase") == "canvas_llm_phase_12_fake_local_sandbox_import_artifact_gate":
        passed("Artifact identifies Canvas LLM Phase 12")
    else:
        failed("Artifact phase is missing or incorrect")

    if data.get("course_id") == APPROVED_COURSE_ID:
        passed("Artifact contains approved course 24399")
    else:
        failed("Artifact course_id is not approved course 24399")

    approved_course_ids = data.get("course_scope", {}).get("approved_course_ids")
    if approved_course_ids == [APPROVED_COURSE_ID]:
        passed("Artifact course scope contains course 24399 only")
    else:
        failed("Artifact course scope must contain course 24399 only")

    if data.get("source_class") == "sandbox_demo_canvas_course":
        passed("Artifact source class is sandbox demo Canvas course")
    else:
        failed("Artifact source class is missing or unsafe")

    if data.get("artifact_class") == "fake_local_import_preview_artifact":
        passed("Artifact class is fake/local import preview artifact")
    else:
        failed("Artifact class is missing or unsafe")

    for flag in MUST_BE_TRUE_FLAGS:
        if data.get(flag) is True:
            passed(f"Artifact explicitly sets {flag}=true")
        else:
            failed(f"Artifact must explicitly set {flag}=true")

    for flag in MUST_BE_FALSE_FLAGS:
        if data.get(flag) is False:
            passed(f"Artifact explicitly sets {flag}=false")
        else:
            failed(f"Artifact must explicitly set {flag}=false")

    if data.get("entity_counts") == EXPECTED_COUNTS:
        passed("Artifact preserves reviewed Phase 9B/Phase 11 entity counts")
    else:
        failed("Artifact entity_counts mismatch")

    expected_warnings = data.get("expected_warnings")
    if isinstance(expected_warnings, list) and EXPECTED_WARNING in expected_warnings:
        warned(EXPECTED_WARNING)
        passed("Artifact preserves expected announcements_metadata warning")
    else:
        failed("Artifact does not preserve expected announcements_metadata warning")

    fake_entities = data.get("fake_entities")
    if isinstance(fake_entities, dict) and fake_entities:
        passed("Artifact includes fake entity mapping shape")
    else:
        failed("Artifact must include fake entity mapping shape")

    artifact_text = json.dumps(data, sort_keys=True)
    blocked_markers = [
        '"id":',
        '"url": "http',
        '"html_url"',
        '"body":',
        '"description":',
        '"content":',
        "canvas.instructure.com",
    ]
    for marker in blocked_markers:
        if marker in artifact_text:
            failed(f"Artifact appears to contain blocked real metadata/content marker: {marker}")
        else:
            passed(f"Artifact does not contain blocked marker: {marker}")

    local_manifest = ".local/canvas-llm/sandbox-metadata/course-24399/manifest.json"
    if check_git_ignored(local_manifest):
        passed(".local Canvas metadata manifest is ignored")
    else:
        failed(".local Canvas metadata manifest is not ignored")

    if check_no_tracked_local_staging():
        passed(".local Canvas metadata is not tracked")
    else:
        failed(".local Canvas metadata is tracked")

    if check_no_sensitive_markers():
        passed("No tracked Canvas URL/token marker found")
    else:
        failures += 1

    print(f"Phase 12 artifact preview: PASS {passes} / WARN {warnings} / FAIL {failures}")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
