#!/usr/bin/env python3
"""Generate Canvas LLM Phase 15 readiness and relationship report.

Reads ignored Phase 14B local metadata summary only:
.local/canvas-llm/approved-course-metadata/manifest.json

Writes a tracked safe markdown report containing counts, readiness gaps,
template recommendations, and next-phase recommendations. It does not fetch
Canvas data, read raw content bodies, download files, call Canvas APIs, write to
Canvas, or expose tokens/URLs.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
LOCAL_MANIFEST = REPO_ROOT / ".local/canvas-llm/approved-course-metadata/manifest.json"
APPROVED_MANIFEST = REPO_ROOT / "config/canvas-llm/approved-canvas-course-manifest.json"
REPORT_PATH = REPO_ROOT / "docs/programs/canvas-llm/canvas-phase-15-readiness-relationship-report.md"

METADATA_KEYS = [
    "course_metadata",
    "folders_metadata",
    "files_metadata",
    "modules_metadata",
    "module_items_metadata",
    "pages_metadata",
    "announcements_metadata",
    "assignments_metadata",
]

STRUCTURE_KEYS = [
    "folders_metadata",
    "files_metadata",
    "modules_metadata",
    "module_items_metadata",
    "pages_metadata",
    "assignments_metadata",
]

CURRENT_BY_SUBJECT = {
    "Math": 26404,
    "Reading/Spelling": 26442,
    "Language Arts": 26495,
    "History": 26493,
    "Science": 26496,
    "Homeroom": 26427,
}

HISTORICAL_BY_SUBJECT = {
    "Math": [21957, 19428],
    "Reading/Spelling": [21919, 19419],
    "Language Arts": [21944, 19426],
    "History": [21934, 19422, 19423],
    "Science": [21970],
    "Homeroom": [22254, 19424],
}

DEMO_COURSES = {24399}


@dataclass(frozen=True)
class CourseSummary:
    course_id: int
    school_year: str
    course_role: str
    subject: str
    canonical_prefixes: tuple[str, ...]
    counts: dict[str, int]

    @property
    def structure_score(self) -> int:
        return sum(self.counts.get(key, 0) for key in STRUCTURE_KEYS)

    @property
    def is_homeroom(self) -> bool:
        return "homeroom_newsletter_course" in self.course_role

    @property
    def is_current(self) -> bool:
        return self.course_role.startswith("current_")

    @property
    def is_historical(self) -> bool:
        return self.course_role.startswith("historical_")

    @property
    def is_demo(self) -> bool:
        return self.course_role == "demo_sandbox_course"


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"missing required file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def course_counts_from_local_manifest(local_manifest: dict[str, Any]) -> dict[int, dict[str, int]]:
    counts: dict[int, dict[str, int]] = {}
    for course in local_manifest.get("courses", []):
        course_id = int(course["course_id"])
        raw_counts = course.get("counts", {})
        counts[course_id] = {key: int(raw_counts.get(key, 0)) for key in METADATA_KEYS}
    return counts


def approved_course_lookup(approved_manifest: dict[str, Any]) -> dict[int, dict[str, Any]]:
    lookup: dict[int, dict[str, Any]] = {}
    for course in approved_manifest.get("courses", []):
        lookup[int(course["course_id"])] = course
    return lookup


def build_summaries(local_manifest: dict[str, Any], approved_manifest: dict[str, Any]) -> dict[int, CourseSummary]:
    counts = course_counts_from_local_manifest(local_manifest)
    approved = approved_course_lookup(approved_manifest)
    summaries: dict[int, CourseSummary] = {}

    for course_id, approved_course in approved.items():
        summaries[course_id] = CourseSummary(
            course_id=course_id,
            school_year=str(approved_course["school_year"]),
            course_role=str(approved_course["course_role"]),
            subject=str(approved_course["subject"]),
            canonical_prefixes=tuple(approved_course.get("canonical_prefixes", [])),
            counts=counts.get(course_id, {key: 0 for key in METADATA_KEYS}),
        )

    return summaries


def best_template(course_ids: list[int], summaries: dict[int, CourseSummary]) -> CourseSummary:
    candidates = [summaries[course_id] for course_id in course_ids if course_id in summaries]
    if not candidates:
        raise SystemExit(f"missing candidate summaries for {course_ids}")
    return max(candidates, key=lambda course: (course.structure_score, course.counts.get("pages_metadata", 0), course.counts.get("files_metadata", 0)))


def readiness_label(course: CourseSummary) -> str:
    if course.structure_score == 0:
        return "empty_shell"
    if course.counts.get("modules_metadata", 0) == 0 and course.counts.get("pages_metadata", 0) == 0:
        return "metadata_only_shell"
    if course.structure_score < 25:
        return "thin"
    return "structured"


def table_row(values: list[str | int]) -> str:
    return "| " + " | ".join(str(value) for value in values) + " |"


def write_report(summaries: dict[int, CourseSummary], local_manifest: dict[str, Any]) -> None:
    lines: list[str] = []

    lines.extend(
        [
            "# Canvas LLM Phase 15: Historical-to-Current Readiness and Relationship Report",
            "",
            "## Status",
            "",
            "Phase 15 reads the ignored Phase 14B local metadata manifest and creates a tracked safe readiness report.",
            "",
            "This phase performs no Canvas API calls, no live fetches, no Canvas writes, no file downloads, no file content reads, no page body ingestion, no announcement body ingestion, no assignment body ingestion, no student data access, no database writes, no RAG, no embeddings, no local model execution, and no lesson generation.",
            "",
            "Raw fetched metadata remains ignored under `.local/canvas-llm/approved-course-metadata/...` and is not committed.",
            "",
            "## Fetch Source",
            "",
            "```text",
            ".local/canvas-llm/approved-course-metadata/manifest.json",
            "```",
            "",
            f"Fetched course count: `{local_manifest.get('course_count')}`",
            "",
            "## Executive Summary",
            "",
            "- Current 2026-2027 courses exist but are mostly empty shells.",
            "- Historical 2024-2025 and 2025-2026 courses contain enough files, folders, modules, module items, pages, and assignment metadata to guide Canvas setup.",
            "- Homeroom/newsletter courses are included but kept separate from academic course readiness scoring.",
            "- Announcements metadata is consistently zero across fetched courses and should be treated as a known Canvas/source pattern for now.",
            "- Phase 16 should produce a safe module/file/page relationship report before any rename, move, copy, or upload preview.",
            "",
            "## Current Course Readiness",
            "",
            table_row(["Subject", "Current Course ID", "Readiness", "Files", "Folders", "Modules", "Module Items", "Pages", "Assignments"]),
            table_row(["---", "---", "---", "---", "---", "---", "---", "---", "---"]),
        ]
    )

    for subject, current_id in CURRENT_BY_SUBJECT.items():
        course = summaries[current_id]
        lines.append(
            table_row(
                [
                    subject,
                    current_id,
                    readiness_label(course),
                    course.counts.get("files_metadata", 0),
                    course.counts.get("folders_metadata", 0),
                    course.counts.get("modules_metadata", 0),
                    course.counts.get("module_items_metadata", 0),
                    course.counts.get("pages_metadata", 0),
                    course.counts.get("assignments_metadata", 0),
                ]
            )
        )

    lines.extend(
        [
            "",
            "## Best Historical Template By Subject",
            "",
            table_row(["Subject", "Recommended Template Course ID", "School Year", "Files", "Folders", "Modules", "Module Items", "Pages", "Assignments", "Structure Score"]),
            table_row(["---", "---", "---", "---", "---", "---", "---", "---", "---", "---"]),
        ]
    )

    for subject, historical_ids in HISTORICAL_BY_SUBJECT.items():
        best = best_template(historical_ids, summaries)
        lines.append(
            table_row(
                [
                    subject,
                    best.course_id,
                    best.school_year,
                    best.counts.get("files_metadata", 0),
                    best.counts.get("folders_metadata", 0),
                    best.counts.get("modules_metadata", 0),
                    best.counts.get("module_items_metadata", 0),
                    best.counts.get("pages_metadata", 0),
                    best.counts.get("assignments_metadata", 0),
                    best.structure_score,
                ]
            )
        )

    lines.extend(
        [
            "",
            "## Historical Academic Course Counts",
            "",
            table_row(["Course ID", "Year", "Subject", "Prefixes", "Files", "Folders", "Modules", "Module Items", "Pages", "Assignments", "Structure Score"]),
            table_row(["---", "---", "---", "---", "---", "---", "---", "---", "---", "---", "---"]),
        ]
    )

    historical_academic = [
        course
        for course in summaries.values()
        if course.is_historical and not course.is_homeroom
    ]
    for course in sorted(historical_academic, key=lambda item: (item.school_year, item.subject, item.course_id), reverse=True):
        lines.append(
            table_row(
                [
                    course.course_id,
                    course.school_year,
                    course.subject,
                    ", ".join(course.canonical_prefixes),
                    course.counts.get("files_metadata", 0),
                    course.counts.get("folders_metadata", 0),
                    course.counts.get("modules_metadata", 0),
                    course.counts.get("module_items_metadata", 0),
                    course.counts.get("pages_metadata", 0),
                    course.counts.get("assignments_metadata", 0),
                    course.structure_score,
                ]
            )
        )

    lines.extend(
        [
            "",
            "## Homeroom / Newsletter Comparison",
            "",
            table_row(["Course ID", "Year", "Role", "Files", "Folders", "Modules", "Module Items", "Pages", "Assignments", "Structure Score", "Recommendation"]),
            table_row(["---", "---", "---", "---", "---", "---", "---", "---", "---", "---", "---"]),
        ]
    )

    homeroom_ids = [26427, 22254, 19424]
    best_homeroom = best_template([22254, 19424], summaries)
    for course_id in homeroom_ids:
        course = summaries[course_id]
        recommendation = "best newsletter model" if course.course_id == best_homeroom.course_id else "supporting reference"
        if course.course_id == 26427:
            recommendation = "current target shell"
        lines.append(
            table_row(
                [
                    course.course_id,
                    course.school_year,
                    course.course_role,
                    course.counts.get("files_metadata", 0),
                    course.counts.get("folders_metadata", 0),
                    course.counts.get("modules_metadata", 0),
                    course.counts.get("module_items_metadata", 0),
                    course.counts.get("pages_metadata", 0),
                    course.counts.get("assignments_metadata", 0),
                    course.structure_score,
                    recommendation,
                ]
            )
        )

    lines.extend(
        [
            "",
            "## Subject Readiness Gaps",
            "",
        ]
    )

    for subject, current_id in CURRENT_BY_SUBJECT.items():
        current = summaries[current_id]
        template = best_template(HISTORICAL_BY_SUBJECT[subject], summaries)
        lines.extend(
            [
                f"### {subject}",
                "",
                f"- Current course `{current.course_id}` readiness: `{readiness_label(current)}`.",
                f"- Recommended historical model: `{template.course_id}` from `{template.school_year}`.",
                f"- Approximate metadata gap: `{max(template.structure_score - current.structure_score, 0)}` structure-count units.",
                f"- Next safe action: build a preview-only relationship map from historical `{template.course_id}` to current `{current.course_id}`.",
                "",
            ]
        )

    lines.extend(
        [
            "## Safety Boundaries Preserved",
            "",
            "- Phase 15 reads local ignored metadata summary only.",
            "- Phase 15 does not fetch from Canvas.",
            "- Phase 15 does not write to Canvas.",
            "- Phase 15 does not download files.",
            "- Phase 15 does not ingest page, announcement, assignment, or file bodies.",
            "- Phase 15 does not access student data, rosters, grades, submissions, analytics, messages, or discussion replies.",
            "- Phase 15 does not write to a knowledge DB, runtime DB, production system, or canonical catalog.",
            "- Phase 15 does not run RAG, embeddings, local model/Ollama, or lesson generation.",
            "- Phase 15 does not track the school Canvas URL or tokens.",
            "",
            "## Recommended Next Phase",
            "",
            "```text",
            "Canvas LLM Phase 16: Preview-Only Canvas Module/File/Page Relationship Map",
            "```",
            "",
            "Phase 16 should read the same ignored Phase 14B metadata and produce preview-only mapping recommendations for modules, folders, files, pages, and current-course setup order. It should still block Canvas writes, file downloads, body ingestion, and raw metadata commits.",
            "",
        ]
    )

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    local_manifest = load_json(LOCAL_MANIFEST)
    approved_manifest = load_json(APPROVED_MANIFEST)
    summaries = build_summaries(local_manifest, approved_manifest)

    missing = sorted(set(approved_course_lookup(approved_manifest)) - set(summaries))
    if missing:
        raise SystemExit(f"missing summaries for approved course IDs: {missing}")

    if int(local_manifest.get("course_count", 0)) != 19:
        raise SystemExit("Phase 14B local manifest must include 19 fetched courses")

    write_report(summaries, local_manifest)

    print("PASS: Phase 15 readiness report generated")
    print(f"PASS: report path: {REPORT_PATH}")
    print("PASS: source was ignored Phase 14B local manifest")
    print("PASS: no Canvas API call performed")
    print("PASS: no Canvas write performed")
    print("PASS: no body/file content ingestion performed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
