#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / ".local/canvas-llm/approved-course-metadata/manifest.json"

CURRENT_TARGET_COURSES = ["26404", "26427", "26442", "26493", "26495", "26496"]
HISTORICAL_TEMPLATE_COURSES = [
    "19426", "19428", "21919", "21934", "21944",
    "21957", "21970", "22254", "24399",
]

BLOCKED_ACTIONS = [
    "Canvas API calls",
    "live Canvas fetches",
    "Canvas writes or mutations",
    "file downloads",
    "file body reads",
    "page, announcement, assignment, or file body ingestion",
    "student data access",
    "DB writes, RAG, embeddings, Ollama/local model execution, or lesson generation",
]

def load_manifest() -> dict:
    if not MANIFEST.exists():
        raise SystemExit(f"FAIL: missing approved metadata manifest: {MANIFEST}")
    return json.loads(MANIFEST.read_text(encoding="utf-8"))

def course_counts(manifest: dict) -> dict[str, dict[str, int]]:
    courses = manifest.get("courses") or []
    if not isinstance(courses, list) or not courses:
        raise SystemExit("FAIL: manifest does not expose course list metadata")
    result: dict[str, dict[str, int]] = {}
    for course in courses:
        if not isinstance(course, dict):
            continue
        course_id = course.get("course_id")
        counts = course.get("counts")
        if course_id is None or not isinstance(counts, dict):
            continue
        result[str(course_id)] = counts
    if not result:
        raise SystemExit("FAIL: manifest course entries do not expose count metadata")
    return result

def is_empty_current_shell(counts: dict[str, int]) -> bool:
    return (
        counts.get("course_metadata", 0) == 1
        and counts.get("files_metadata", 0) == 0
        and counts.get("modules_metadata", 0) == 0
        and counts.get("module_items_metadata", 0) == 0
        and counts.get("pages_metadata", 0) == 0
        and counts.get("assignments_metadata", 0) == 0
        and counts.get("announcements_metadata", 0) == 0
        and counts.get("folders_metadata", 0) == 1
    )

def main() -> int:
    manifest = load_manifest()
    counts = course_counts(manifest)

    missing_current = [cid for cid in CURRENT_TARGET_COURSES if cid not in counts]
    missing_templates = [cid for cid in HISTORICAL_TEMPLATE_COURSES if cid not in counts]
    non_empty_current = [
        cid for cid in CURRENT_TARGET_COURSES
        if cid in counts and not is_empty_current_shell(counts[cid])
    ]

    passes = 0
    warns = 0
    fails = 0

    def emit(kind: str, message: str) -> None:
        nonlocal passes, warns, fails
        print(f"{kind}: {message}")
        if kind == "PASS":
            passes += 1
        elif kind == "WARN":
            warns += 1
        elif kind == "FAIL":
            fails += 1

    print("Canvas LLM Phase 18 Write Gate Readiness Review")
    print("------------------------------------------------")

    if missing_current:
        emit("FAIL", f"missing current target course metadata: {', '.join(missing_current)}")
    else:
        emit("PASS", "all approved current Canvas target courses are represented in local metadata")

    if non_empty_current:
        emit("FAIL", f"current target courses are not empty shells: {', '.join(non_empty_current)}")
    else:
        emit("PASS", "approved current Canvas target courses remain empty shells")

    if missing_templates:
        emit("FAIL", f"missing historical template metadata: {', '.join(missing_templates)}")
    else:
        emit("PASS", "historical template course metadata coverage is available")

    emit("PASS", "Phase 18 performs preview/review only")
    emit("PASS", "Phase 18 does not call Canvas API, fetch live Canvas data, or write to Canvas")
    emit("PASS", "Phase 18 does not download files or read body contents")
    emit("PASS", "Phase 18 does not access student data")
    emit("PASS", "Phase 18 does not use DB writes, RAG, embeddings, Ollama, or lesson generation")
    emit("PASS", "Phase 18 decision is NEEDS_ONE_MORE_PREVIEW_REFINEMENT")
    emit("PASS", "recommended next phase is Canvas LLM Phase 19 Minimum Canvas Write Gate Design Packet")

    print()
    print("Readiness Decision")
    print("----------------------------------------")
    print("NEEDS_ONE_MORE_PREVIEW_REFINEMENT")
    print()
    print("Reason")
    print("----------------------------------------")
    print(
        "Enough evidence exists to design a Canvas setup write gate, but real Canvas mutation "
        "should remain blocked until a separate minimum-write design packet defines the exact "
        "smallest first operation, rollback/cleanup expectations, human approval requirement, "
        "and target-course restrictions."
    )
    print()
    print("Blocked Actions")
    print("----------------------------------------")
    for action in BLOCKED_ACTIONS:
        print(f"- {action}")
    print()
    print("Summary")
    print("----------------------------------------")
    print(f"PASS: {passes}")
    print(f"WARN: {warns}")
    print(f"FAIL: {fails}")
    return 1 if fails else 0

if __name__ == "__main__":
    raise SystemExit(main())
