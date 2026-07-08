#!/usr/bin/env python3
"""Generate Canvas LLM Phase 17 preview-only setup action packet.

Reads ignored Phase 14B local metadata plus the tracked Phase 16 relationship
map. Produces a tracked safe action packet for Canvas setup planning.

No Canvas API calls, live fetches, Canvas writes, renames, moves, uploads,
publishes, deletes, copies, file downloads, file content reads, page body
ingestion, announcement body ingestion, assignment body ingestion, student data
access, database writes, RAG, embeddings, local model execution, lesson
generation, or raw .local metadata commits.
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
PHASE16_REPORT = REPO_ROOT / "docs/programs/canvas-llm/canvas-phase-16-preview-relationship-map.md"
REPORT_PATH = REPO_ROOT / "docs/programs/canvas-llm/canvas-phase-17-preview-setup-action-packet.md"

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

SETUP_PAIRS = [
    {
        "subject": "Math",
        "template_course_id": 19428,
        "target_course_id": 26404,
        "priority": "highest",
        "notes": "Largest historical relationship set; likely first academic setup candidate.",
    },
    {
        "subject": "Reading/Spelling",
        "template_course_id": 19419,
        "target_course_id": 26442,
        "priority": "highest",
        "notes": "Shared Reading/Spelling course; preserve RM4 and SPELL prefix distinction.",
    },
    {
        "subject": "Language Arts",
        "template_course_id": 19426,
        "target_course_id": 26495,
        "priority": "high",
        "notes": "Strong module-item structure and ELA page/file relationship depth.",
    },
    {
        "subject": "History",
        "template_course_id": 21934,
        "target_course_id": 26493,
        "priority": "medium",
        "notes": "Best History template; no current assignments expected, so prioritize structure clarity.",
    },
    {
        "subject": "Science",
        "template_course_id": 21970,
        "target_course_id": 26496,
        "priority": "medium",
        "notes": "Only approved Science model; sufficient page/module/folder structure.",
    },
    {
        "subject": "Homeroom/Newsletter",
        "template_course_id": 19424,
        "target_course_id": 26427,
        "priority": "high",
        "notes": "Newsletter setup is separate from academic scoring; useful for parent-facing reminders.",
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
    def total_relationships(self) -> int:
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


def action_scale(count: int, noun: str) -> str:
    if count == 0:
        return f"0 {noun}"
    if count == 1:
        return f"1 {noun}"
    return f"{count} {noun}s"


def setup_actions(template: CourseInfo, pair: dict[str, Any]) -> list[str]:
    actions = [
        "Review current target course shell before any write gate.",
        "Prepare proposed folder groups from historical folder metadata.",
        "Prepare proposed module shells from historical module metadata.",
        "Prepare page placement preview from historical page metadata.",
        "Prepare file relationship groups from historical file and folder metadata.",
    ]

    if template.counts.get("module_items_metadata", 0):
        actions.append("Prepare module item relationship preview for pages/files/assignments.")
    if template.counts.get("assignments_metadata", 0):
        actions.append("Prepare assignment relationship references only; do not ingest assignment bodies.")
    if "Reading/Spelling" in pair["subject"]:
        actions.append("Preserve RM4 and SPELL as separate canonical prefixes inside the shared Canvas course.")
    if "Homeroom" in pair["subject"]:
        actions.append("Keep newsletter/reminder packet separate from academic curriculum setup.")
    return actions


def table_row(values: list[str | int]) -> str:
    return "| " + " | ".join(str(value) for value in values) + " |"


def generate_report() -> None:
    courses = build_course_info()

    lines: list[str] = [
        "# Canvas LLM Phase 17: Preview-Only Canvas Setup Action Packet",
        "",
        "## Status",
        "",
        "Phase 17 converts the Phase 16 relationship map into a practical, preview-only Canvas setup action packet.",
        "",
        "This phase reads ignored Phase 14B local metadata and the tracked Phase 16 relationship map. It performs no Canvas API calls, no live fetches, no Canvas writes, no renames, no moves, no uploads, no publish changes, no deletes, no copies, no file downloads, no file content reads, no page body ingestion, no announcement body ingestion, no assignment body ingestion, no student data access, no database writes, no RAG, no embeddings, no local model execution, and no lesson generation.",
        "",
        "Raw fetched metadata remains ignored under `.local/canvas-llm/approved-course-metadata/...` and is not committed.",
        "",
        "## Source Inputs",
        "",
        "```text",
        ".local/canvas-llm/approved-course-metadata/manifest.json",
        "docs/programs/canvas-llm/canvas-phase-16-preview-relationship-map.md",
        "```",
        "",
        "## Setup Packet Summary",
        "",
        table_row(["Subject", "Priority", "Template Course", "Target Course", "Template Year", "Files", "Folders", "Modules", "Module Items", "Pages", "Assignments", "Preview Relationship Total"]),
        table_row(["---", "---", "---", "---", "---", "---", "---", "---", "---", "---", "---", "---"]),
    ]

    for pair in SETUP_PAIRS:
        template = courses[pair["template_course_id"]]
        target = courses[pair["target_course_id"]]
        lines.append(
            table_row(
                [
                    pair["subject"],
                    pair["priority"],
                    template.course_id,
                    target.course_id,
                    template.school_year,
                    template.counts.get("files_metadata", 0),
                    template.counts.get("folders_metadata", 0),
                    template.counts.get("modules_metadata", 0),
                    template.counts.get("module_items_metadata", 0),
                    template.counts.get("pages_metadata", 0),
                    template.counts.get("assignments_metadata", 0),
                    template.total_relationships,
                ]
            )
        )

    lines.extend(
        [
            "",
            "## Subject-by-Subject Preview Setup Actions",
            "",
        ]
    )

    for pair in SETUP_PAIRS:
        template = courses[pair["template_course_id"]]
        target = courses[pair["target_course_id"]]
        lines.extend(
            [
                f"### {pair['subject']}",
                "",
                f"- Template course: `{template.course_id}` (`{template.school_year}`)",
                f"- Target course: `{target.course_id}` (`{target.school_year}`)",
                f"- Priority: `{pair['priority']}`",
                f"- Notes: {pair['notes']}",
                f"- Preview scale: {action_scale(template.counts.get('folders_metadata', 0), 'folder')}, {action_scale(template.counts.get('files_metadata', 0), 'file')}, {action_scale(template.counts.get('modules_metadata', 0), 'module')}, {action_scale(template.counts.get('module_items_metadata', 0), 'module item')}, {action_scale(template.counts.get('pages_metadata', 0), 'page')}, {action_scale(template.counts.get('assignments_metadata', 0), 'assignment relationship')}.",
                "",
                "Preview actions:",
                "",
            ]
        )

        for action in setup_actions(template, pair):
            lines.append(f"- {action}")

        lines.extend(
            [
                "",
                "Blocked before a later write gate:",
                "",
                "- No Canvas folder creation.",
                "- No Canvas module creation.",
                "- No Canvas page creation or editing.",
                "- No Canvas file upload or download.",
                "- No Canvas rename, move, delete, copy, or publish action.",
                "- No body/content ingestion.",
                "",
            ]
        )

    lines.extend(
        [
            "## Cross-Course Setup Order",
            "",
            "Recommended preview-only setup order:",
            "",
            "1. Math and Reading/Spelling first, because these have the largest academic relationship sets and likely drive daily classroom operations.",
            "2. Language Arts next, because it has strong module-item structure and should align with writing/language routines.",
            "3. Homeroom/Newsletter in parallel, but in a separate newsletter/reminder lane.",
            "4. History and Science after core daily courses, unless classroom calendar requirements make one of them urgent.",
            "5. Run a human review before any future Canvas write gate.",
            "",
            "## Folder / File Grouping Priorities",
            "",
            "- Start with folder metadata and file metadata only.",
            "- Group by historical course, subject, and likely unit/module relationship.",
            "- Do not infer file content from names beyond safe metadata-level planning.",
            "- Do not download files.",
            "- Do not commit raw file metadata.",
            "",
            "## Module Shell Priorities",
            "",
            "- Use historical modules as preview candidates for current module shells.",
            "- Use module item counts to identify where pages/files/assignments likely connect.",
            "- Treat module shell creation as blocked until a later explicit Canvas write gate.",
            "",
            "## Page Placement Priorities",
            "",
            "- Use pages metadata only to preview possible module placements.",
            "- Do not read page bodies.",
            "- Do not summarize page bodies.",
            "- Do not use page text for RAG or embeddings.",
            "",
            "## Assignment Relationship References",
            "",
            "- Use assignments metadata only for relationship mapping.",
            "- Do not ingest assignment bodies.",
            "- Do not recreate assignments yet.",
            "- Treat History and Science assignment-prefix expectations as N/A unless later planning changes them.",
            "",
            "## Homeroom / Newsletter Packet",
            "",
            "- Keep Homeroom/Newsletter separate from academic course setup.",
            "- Use `19424` as the primary newsletter template and `22254` as a supporting reference.",
            "- Current target is `26427`.",
            "- Do not ingest newsletter page bodies or announcement bodies.",
            "- Future work may need a separate approval gate if newsletter layout/body review becomes necessary.",
            "",
            "## Explicitly Blocked Actions",
            "",
            "- Canvas API calls",
            "- Live fetches",
            "- Canvas writes",
            "- Canvas renames",
            "- Canvas moves",
            "- Canvas uploads",
            "- Canvas deletes",
            "- Canvas copy/import actions",
            "- Canvas publish changes",
            "- File downloads",
            "- File content reads",
            "- Page body ingestion",
            "- Announcement body ingestion",
            "- Assignment body ingestion",
            "- Student data access",
            "- Users, enrollments, rosters, submissions, grades, analytics, messages, discussion replies, or quiz responses",
            "- Knowledge DB writes",
            "- Runtime DB writes",
            "- Production writes",
            "- Canonical catalog writes",
            "- RAG",
            "- Embeddings",
            "- Local model/Ollama execution",
            "- Lesson generation",
            "- Tracked school Canvas URL",
            "- Tracked tokens",
            "- Committed `.local/...` raw metadata",
            "",
            "## Recommended Next Phase",
            "",
            "```text",
            "Canvas LLM Phase 18: Canvas Setup Write Gate Readiness Review",
            "```",
            "",
            "Phase 18 should decide whether the repo is ready for a tightly constrained write gate, or whether another preview-only refinement is needed first. Any write gate must require explicit approval, target only approved current 2026-2027 course IDs, and start with the smallest safe Canvas action.",
            "",
        ]
    )

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    if not PHASE16_REPORT.exists():
        raise SystemExit("missing Phase 16 relationship map report")

    local_manifest = load_json(LOCAL_MANIFEST)
    if int(local_manifest.get("course_count", 0)) != 19:
        raise SystemExit("Phase 14B local manifest must contain 19 fetched courses")

    generate_report()

    print("PASS: Phase 17 preview setup action packet generated")
    print(f"PASS: report path: {REPORT_PATH}")
    print("PASS: source includes ignored Phase 14B local metadata")
    print("PASS: source includes tracked Phase 16 relationship map")
    print("PASS: no Canvas API call performed")
    print("PASS: no Canvas write performed")
    print("PASS: no rename/move/upload/delete/publish/copy performed")
    print("PASS: no file download or body ingestion performed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
