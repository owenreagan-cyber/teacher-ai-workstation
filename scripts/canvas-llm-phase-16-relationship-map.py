#!/usr/bin/env python3
"""Generate Canvas LLM Phase 16 preview-only relationship map.

Reads ignored Phase 14B local metadata only and creates a tracked safe preview
report mapping historical template courses to current 2026-2027 target courses.

No Canvas API call, no Canvas write, no file download, no body ingestion, no
student data access, no database write, no RAG/embeddings/local model execution,
and no raw .local metadata commit.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
LOCAL_ROOT = REPO_ROOT / ".local/canvas-llm/approved-course-metadata"
LOCAL_MANIFEST = LOCAL_ROOT / "manifest.json"
APPROVED_MANIFEST = REPO_ROOT / "config/canvas-llm/approved-canvas-course-manifest.json"
REPORT_PATH = REPO_ROOT / "docs/programs/canvas-llm/canvas-phase-16-preview-relationship-map.md"

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

TEMPLATE_TO_TARGET = [
    {
        "subject": "Math",
        "template_course_id": 19428,
        "target_course_id": 26404,
        "template_reason": "Highest Math structure score and strongest file/module-item depth.",
    },
    {
        "subject": "Reading/Spelling",
        "template_course_id": 19419,
        "target_course_id": 26442,
        "template_reason": "Strongest shared RM4/SPELL historical structure.",
    },
    {
        "subject": "Language Arts",
        "template_course_id": 19426,
        "target_course_id": 26495,
        "template_reason": "Strongest ELA historical module-item relationship depth.",
    },
    {
        "subject": "History",
        "template_course_id": 21934,
        "target_course_id": 26493,
        "template_reason": "Strongest History structure, folders, modules, and module-item depth.",
    },
    {
        "subject": "Science",
        "template_course_id": 21970,
        "target_course_id": 26496,
        "template_reason": "Only approved historical Science model and sufficient page/module structure.",
    },
    {
        "subject": "Homeroom/Newsletter",
        "template_course_id": 19424,
        "target_course_id": 26427,
        "template_reason": "Best Homeroom/newsletter structure score; keep separate from academic scoring.",
    },
]


@dataclass(frozen=True)
class CourseInfo:
    course_id: int
    school_year: str
    course_role: str
    subject: str
    prefixes: tuple[str, ...]
    counts: dict[str, int]

    @property
    def relationship_total(self) -> int:
        return (
            self.counts.get("folders_metadata", 0)
            + self.counts.get("files_metadata", 0)
            + self.counts.get("modules_metadata", 0)
            + self.counts.get("module_items_metadata", 0)
            + self.counts.get("pages_metadata", 0)
            + self.counts.get("assignments_metadata", 0)
        )


def load_json(path: Path) -> Any:
    if not path.exists():
        raise SystemExit(f"missing required file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def approved_lookup() -> dict[int, dict[str, Any]]:
    data = load_json(APPROVED_MANIFEST)
    return {int(course["course_id"]): course for course in data.get("courses", [])}


def local_counts() -> dict[int, dict[str, int]]:
    data = load_json(LOCAL_MANIFEST)
    if int(data.get("course_count", 0)) != 19:
        raise SystemExit("Phase 14B local manifest must contain 19 fetched courses")

    counts: dict[int, dict[str, int]] = {}
    for course in data.get("courses", []):
        course_id = int(course["course_id"])
        raw_counts = course.get("counts", {})
        counts[course_id] = {key: int(raw_counts.get(key, 0)) for key in METADATA_KEYS}
    return counts


def build_course_info() -> dict[int, CourseInfo]:
    approved = approved_lookup()
    counts = local_counts()
    info: dict[int, CourseInfo] = {}

    for course_id, approved_course in approved.items():
        info[course_id] = CourseInfo(
            course_id=course_id,
            school_year=str(approved_course["school_year"]),
            course_role=str(approved_course["course_role"]),
            subject=str(approved_course["subject"]),
            prefixes=tuple(approved_course.get("canonical_prefixes", [])),
            counts=counts.get(course_id, {key: 0 for key in METADATA_KEYS}),
        )

    return info


def load_per_course_manifest(course_id: int) -> dict[str, Any]:
    path = LOCAL_ROOT / f"course-{course_id}" / "manifest.json"
    return load_json(path)


def preview_setup_order(template: CourseInfo) -> list[str]:
    order = []
    if template.counts.get("folders_metadata", 0):
        order.append("1. Preview folder structure from historical template.")
    if template.counts.get("files_metadata", 0):
        order.append("2. Preview file inventory and likely folder destinations.")
    if template.counts.get("modules_metadata", 0):
        order.append("3. Preview module shell order.")
    if template.counts.get("module_items_metadata", 0):
        order.append("4. Preview module item relationships to pages/files/assignments.")
    if template.counts.get("pages_metadata", 0):
        order.append("5. Preview page inventory and likely module placement.")
    if template.counts.get("assignments_metadata", 0):
        order.append("6. Preview assignment relationship metadata without body ingestion.")
    return order or ["1. No relationship preview available from this template."]


def table_row(values: list[str | int]) -> str:
    return "| " + " | ".join(str(value) for value in values) + " |"


def generate_report() -> None:
    courses = build_course_info()

    lines: list[str] = [
        "# Canvas LLM Phase 16: Preview-Only Canvas Module/File/Page Relationship Map",
        "",
        "## Status",
        "",
        "Phase 16 creates a preview-only relationship map from historical template courses to current 2026-2027 Canvas target courses.",
        "",
        "This phase reads ignored Phase 14B local metadata only. It performs no Canvas API calls, no live fetches, no Canvas writes, no renames, no moves, no uploads, no publish changes, no file downloads, no file content reads, no page body ingestion, no announcement body ingestion, no assignment body ingestion, no student data access, no database writes, no RAG, no embeddings, no local model execution, and no lesson generation.",
        "",
        "Raw fetched metadata remains ignored under `.local/canvas-llm/approved-course-metadata/...` and is not committed.",
        "",
        "## Preview Relationship Map",
        "",
        table_row(["Subject", "Template Course", "Target Course", "Template Year", "Target Year", "Files", "Folders", "Modules", "Module Items", "Pages", "Assignments", "Relationship Total"]),
        table_row(["---", "---", "---", "---", "---", "---", "---", "---", "---", "---", "---", "---"]),
    ]

    for mapping in TEMPLATE_TO_TARGET:
        template = courses[mapping["template_course_id"]]
        target = courses[mapping["target_course_id"]]
        lines.append(
            table_row(
                [
                    mapping["subject"],
                    template.course_id,
                    target.course_id,
                    template.school_year,
                    target.school_year,
                    template.counts.get("files_metadata", 0),
                    template.counts.get("folders_metadata", 0),
                    template.counts.get("modules_metadata", 0),
                    template.counts.get("module_items_metadata", 0),
                    template.counts.get("pages_metadata", 0),
                    template.counts.get("assignments_metadata", 0),
                    template.relationship_total,
                ]
            )
        )

    lines.extend(
        [
            "",
            "## Current Target Course Setup Order Preview",
            "",
        ]
    )

    for mapping in TEMPLATE_TO_TARGET:
        template = courses[mapping["template_course_id"]]
        target = courses[mapping["target_course_id"]]
        lines.extend(
            [
                f"### {mapping['subject']}",
                "",
                f"- Historical template: `{template.course_id}` (`{template.school_year}`)",
                f"- Current target: `{target.course_id}` (`{target.school_year}`)",
                f"- Reason: {mapping['template_reason']}",
                f"- Preview-only relationship total: `{template.relationship_total}`",
                f"- Current target relationship total: `{target.relationship_total}`",
                "",
                "Suggested preview order:",
                "",
            ]
        )

        for item in preview_setup_order(template):
            lines.append(f"- {item}")

        lines.extend(
            [
                "",
                "Blocked in Phase 16:",
                "",
                "- Do not write to Canvas.",
                "- Do not rename, move, upload, delete, publish, or copy anything in Canvas.",
                "- Do not download files or read file contents.",
                "- Do not ingest page, announcement, assignment, or file bodies.",
                "",
            ]
        )

    lines.extend(
        [
            "## Per-Course Relationship Metadata Availability",
            "",
            table_row(["Course ID", "Role", "Year", "Subject", "Prefixes", "Files", "Folders", "Modules", "Module Items", "Pages", "Assignments", "Announcements"]),
            table_row(["---", "---", "---", "---", "---", "---", "---", "---", "---", "---", "---", "---"]),
        ]
    )

    for course in sorted(courses.values(), key=lambda item: (item.school_year, item.course_role, item.subject, item.course_id)):
        lines.append(
            table_row(
                [
                    course.course_id,
                    course.course_role,
                    course.school_year,
                    course.subject,
                    ", ".join(course.prefixes),
                    course.counts.get("files_metadata", 0),
                    course.counts.get("folders_metadata", 0),
                    course.counts.get("modules_metadata", 0),
                    course.counts.get("module_items_metadata", 0),
                    course.counts.get("pages_metadata", 0),
                    course.counts.get("assignments_metadata", 0),
                    course.counts.get("announcements_metadata", 0),
                ]
            )
        )

    lines.extend(
        [
            "",
            "## Homeroom / Newsletter Boundary",
            "",
            "Homeroom/newsletter mapping is previewed separately from academic course mapping.",
            "",
            "- Current Homeroom target: `26427`",
            "- Recommended Homeroom/newsletter template: `19424`",
            "- Supporting Homeroom/newsletter reference: `22254`",
            "- Phase 16 does not evaluate Homeroom as academic curriculum.",
            "- Phase 16 does not ingest newsletter page bodies or announcement bodies.",
            "",
            "## Known Pattern",
            "",
            "Announcements metadata is zero across the fetched course set. Treat this as a known metadata pattern until a later phase explicitly investigates whether newsletter/reminder content lives primarily in pages, modules, or another Canvas surface.",
            "",
            "## Safety Boundaries Preserved",
            "",
            "- Phase 16 reads local ignored metadata only.",
            "- Phase 16 does not fetch from Canvas.",
            "- Phase 16 does not write to Canvas.",
            "- Phase 16 does not rename, move, upload, delete, publish, or copy Canvas objects.",
            "- Phase 16 does not download files.",
            "- Phase 16 does not read file contents.",
            "- Phase 16 does not ingest page, announcement, assignment, or file bodies.",
            "- Phase 16 does not access student data, rosters, grades, submissions, analytics, messages, discussion replies, users, or enrollments.",
            "- Phase 16 does not write to a knowledge DB, runtime DB, production system, or canonical catalog.",
            "- Phase 16 does not run RAG, embeddings, local model/Ollama, or lesson generation.",
            "- Phase 16 does not track the school Canvas URL or tokens.",
            "",
            "## Recommended Next Phase",
            "",
            "```text",
            "Canvas LLM Phase 17: Preview-Only Canvas Setup Action Packet",
            "```",
            "",
            "Phase 17 should convert this relationship map into a preview-only setup action packet: proposed folders, module shells, page placements, file relationship groups, and subject-by-subject setup order. It should still block writes, downloads, body ingestion, and raw metadata commits.",
            "",
        ]
    )

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    for mapping in TEMPLATE_TO_TARGET:
        load_per_course_manifest(mapping["template_course_id"])
        load_per_course_manifest(mapping["target_course_id"])

    generate_report()

    print("PASS: Phase 16 preview relationship map generated")
    print(f"PASS: report path: {REPORT_PATH}")
    print("PASS: source was ignored Phase 14B local metadata")
    print("PASS: no Canvas API call performed")
    print("PASS: no Canvas write performed")
    print("PASS: no rename/move/upload/delete/publish performed")
    print("PASS: no file download or body ingestion performed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
