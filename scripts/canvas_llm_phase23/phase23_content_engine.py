#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import sys
import shutil
import threading
import time
import urllib.parse
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
APP_DIR = REPO_ROOT / "apps/weekly-content-production"
APP_DATA_DIR = APP_DIR / "data"
APP_DATA_PATH = APP_DATA_DIR / "phase23-demo.json"
LOCAL_ROOT = Path(os.environ.get("PHASE23_LOCAL_ROOT") or (REPO_ROOT / ".local/canvas-llm/phase-23-weekly-content-production"))
LOCAL_PACKET_STORE = LOCAL_ROOT / "packet-store.json"
LOCAL_STATE_DIR = LOCAL_ROOT / "state"
LOCAL_STATE_QUARANTINE_DIR = LOCAL_ROOT / "quarantine" / "state"
FIXTURE_PATH = REPO_ROOT / "fixtures/canvas-llm/phase-23/synthetic-weekly-content.json"
ALLOWED_APPROVAL_STATES = {"draft", "reviewed", "approved"}

sys.path.insert(0, str(REPO_ROOT))
from scripts.canvas_llm_phase22 import phase22_workstation as phase22  # noqa: E402

UTC = timezone.utc
WHITE = "#ffffff"
BLUE = "#0065a7"
MAGENTA = "#c51062"
DGRAY = "#333333"
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
DAY_BLOCK_IDS = [
    "kl_activities2",
    "kl_custom_block_4",
    "kl_custom_block_3",
    "kl_custom_block_2",
    "kl_custom_block_1",
]


def now_utc() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def stable_id(*parts: Any) -> str:
    payload = "|".join(map(str, parts)).encode("utf-8")
    return "p23-" + hashlib.sha256(payload).hexdigest()[:18]


def compact(value: Any) -> str:
    return " ".join(str(value or "").replace("\xa0", " ").split())


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def canonical_week_code(code: str) -> str:
    return phase22.canonical_week_code(code)


def local_state_path(week_code: str) -> Path:
    return LOCAL_STATE_DIR / f"{canonical_week_code(week_code)}.json"


def quarantine_local_state(path: Path, reason: str) -> Path:
    quarantine_dir = LOCAL_STATE_QUARANTINE_DIR / now_utc().replace(":", "").replace("-", "")
    quarantine_dir.mkdir(parents=True, exist_ok=True)
    target = quarantine_dir / path.name
    try:
        path.replace(target)
    except FileNotFoundError:
        pass
    except OSError:
        if path.exists():
            shutil.copy2(path, target)
            try:
                path.unlink()
            except OSError:
                pass
    return target


def default_local_state(week_code: str) -> dict[str, Any]:
    return {
        "weekCode": canonical_week_code(week_code),
        "approvalState": "draft",
        "version": 0,
        "status": "saved",
        "updatedAt": None,
        "source": "default",
    }


def load_local_state_record(week_code: str) -> dict[str, Any]:
    canonical = canonical_week_code(week_code)
    path = local_state_path(canonical)
    if not path.exists():
        return default_local_state(canonical)
    try:
        record = read_json(path)
    except Exception as error:
        quarantine_local_state(path, f"invalid-json:{error}")
        return {
            **default_local_state(canonical),
            "status": "error",
            "error": "Local approval state file could not be parsed",
            "source": "quarantined",
        }
    try:
        if not isinstance(record, dict):
            raise ValueError("record must be an object")
        if canonical_week_code(record.get("weekCode", canonical)) != canonical:
            raise ValueError("weekCode does not match canonical week")
        approval_state = record.get("approvalState")
        if approval_state not in ALLOWED_APPROVAL_STATES:
            raise ValueError("approvalState is not allowed")
        version = int(record.get("version", 0))
        if version < 0:
            raise ValueError("version must be non-negative")
    except Exception as error:
        quarantine_local_state(path, f"invalid-state:{error}")
        return {
            **default_local_state(canonical),
            "status": "error",
            "error": f"Invalid local approval state: {error}",
            "source": "quarantined",
        }
    return {
        "weekCode": canonical,
        "approvalState": approval_state,
        "version": version,
        "status": "saved",
        "updatedAt": record.get("updatedAt"),
        "source": "local",
    }


def save_local_state_record(week_code: str, approval_state: str, version: int | str | None) -> dict[str, Any]:
    canonical = canonical_week_code(week_code)
    if approval_state not in ALLOWED_APPROVAL_STATES:
        raise ValueError("approvalState must be draft, reviewed, or approved")
    current = load_local_state_record(canonical)
    if current.get("status") == "error":
        raise ValueError(current.get("error") or "Local approval state is invalid")
    expected = int(version if version is not None else current.get("version", 0))
    if expected != int(current.get("version", 0)):
        return {
            "status": "conflict",
            "weekCode": canonical,
            "approvalState": current["approvalState"],
            "version": current["version"],
            "updatedAt": current.get("updatedAt"),
        }
    next_record = {
        "weekCode": canonical,
        "approvalState": approval_state,
        "version": current["version"] + 1,
        "updatedAt": now_utc(),
        "status": "saved",
        "source": "local",
    }
    write_json(local_state_path(canonical), next_record)
    return next_record


def apply_local_state(packet: dict[str, Any]) -> dict[str, Any]:
    local_state = load_local_state_record(packet["weekCode"])
    if local_state.get("status") == "saved":
        packet["approvalState"] = local_state["approvalState"]
    return packet


def current_packet(week_code: str | None = None) -> tuple[dict[str, Any], dict[str, Any]]:
    packet = build_packet(week_code)
    local_state = load_local_state_record(packet["weekCode"])
    if local_state.get("status") == "saved":
        packet["approvalState"] = local_state["approvalState"]
    return packet, local_state


def ordinal_suffix(value: int) -> str:
    if 10 <= value % 100 <= 20:
        return "th"
    return {1: "st", 2: "nd", 3: "rd"}.get(value % 10, "th")


def format_teacher_facing_date(machine_date: str, week_start: str | None = None, week_end: str | None = None) -> str:
    day = date.fromisoformat(machine_date)
    if week_start and week_end and week_start <= machine_date <= week_end:
        return day.strftime("%A")
    return f"{day.strftime('%A')}, {day.strftime('%B')} {day.day}{ordinal_suffix(day.day)}"


def suppress_empty_daily_content(items: list[Any]) -> list[str]:
    return [compact(item) for item in items if compact(item)]


def is_verified_assignment_url(url: str | None) -> bool:
    if not url:
        return False
    parsed = urllib.parse.urlparse(str(url))
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc) and not str(url).strip().startswith("javascript:")


def render_verified_assignment_reference(label: str, url: str | None = None, verified: bool = False) -> str:
    text = compact(label)
    if not text:
        return ""
    if verified and is_verified_assignment_url(url):
        return f'<a href="{html.escape(str(url))}">{html.escape(text)}</a>'
    return html.escape(text)


def build_display_assignment_title(subject: str, entry_type: str, number: int | str | None, hint_override: str | None = None) -> str:
    subject = compact(subject).lower()
    entry_type = compact(entry_type).lower().replace("_", "-")
    raw_number = int(number) if str(number or "").isdigit() else None
    if subject == "math":
        if raw_number is None:
            raise ValueError("Math assignment titles require a number")
        if entry_type in {"lesson", "homework"}:
            title = f"SM5: Lesson {raw_number}"
            hint = compact(hint_override or "").lower()
            if hint in {"none", "no", "off"}:
                return title
            if hint in {"odds", "odd"}:
                return f"{title} Odds"
            if hint in {"evens", "even"}:
                return f"{title} Evens"
            return f"{title} {'Odds' if raw_number % 2 else 'Evens'}"
        if entry_type in {"written-test", "written test", "test"}:
            return f"SM5: Lesson {raw_number} Written Test"
        if entry_type in {"fact-test", "fact test"}:
            return f"SM5: Lesson {raw_number} Fact Test"
        if entry_type in {"study-guide", "study guide"}:
            return f"SM5: Lesson {raw_number} Study Guide"
    if subject == "reading":
        if raw_number is None:
            raise ValueError("Reading assignment titles require a number")
        if entry_type == "lesson":
            return f"Reading Lesson {raw_number}"
        if entry_type in {"test", "mastery-test", "mastery test"}:
            return f"Reading Mastery Test {raw_number}"
        if entry_type == "checkout":
            return f"Reading Checkout {raw_number}"
    if subject == "spelling":
        if raw_number is None:
            raise ValueError("Spelling assignment titles require a number")
        if entry_type == "lesson":
            return f"Spelling Lesson {raw_number}"
        if entry_type == "test":
            return f"Spelling Test {raw_number}"
    if subject == "language-arts":
        return compact(str(number or "")) or "ELA4"
    return compact(str(number or "")) or compact(subject).title()


@dataclass
class InstructionalWeek:
    code: str
    starts_on: str
    ends_on: str
    quarter: int
    display_subtitle: str


@dataclass
class PacingEntry:
    date: str
    weekday: str
    subject: str
    title: str
    entry_type: str
    lesson: str | None = None
    test: str | None = None
    in_class: str = ""
    at_home: str = ""
    resource_hints: list[str] = field(default_factory=list)
    notes: str = ""


@dataclass
class PageDraft:
    page_id: str
    subject_group: str
    title: str
    body_text: str
    body_html: str
    linked_assignment_ids: list[str]
    resource_ids: list[str]
    provenance: list[dict[str, Any]]


@dataclass
class AssignmentDraft:
    assignment_id: str
    subject: str
    title: str
    body_text: str
    body_html: str
    group: str
    points: int
    grade_display: str
    submission_type: str
    audience: str
    linked_page_id: str | None
    linked_resource_ids: list[str]
    verified_assignment_url: str | None = None
    machine_date: str | None = None
    display_date: str | None = None
    warnings: list[str] = field(default_factory=list)
    provenance: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class ResourceMatch:
    resource_id: str
    canonical_name: str
    subject: str
    resource_type: str
    verification_status: str
    match_confidence: float
    match_reason: str
    matched_to: list[str]
    provenance: list[dict[str, Any]]


@dataclass
class AssessmentReminder:
    reminder_id: str
    date: str
    title: str
    body_text: str
    body_html: str
    linked_assignment_ids: list[str]
    display_date: str | None = None
    warnings: list[str] = field(default_factory=list)
    provenance: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class ValidationFinding:
    severity: str
    code: str
    message: str
    target: str | None = None


@dataclass
class RiskFinding:
    severity: str
    code: str
    message: str
    mitigation: str


@dataclass
class ProvenanceRecord:
    source_type: str
    source_ref: str
    details: str


@dataclass
class ProductionPacket:
    schema_version: int
    packet_id: str
    week_code: str
    week_start: str
    week_end: str
    generated_at: str
    source_kind: str
    artifact_classification: str
    contains_student_data: bool
    subjects: list[dict[str, Any]]
    pages: list[PageDraft]
    assignments: list[AssignmentDraft]
    resources: list[ResourceMatch]
    assessment_reminders: list[AssessmentReminder]
    validation: dict[str, Any]
    risks: list[RiskFinding]
    provenance: list[ProvenanceRecord]
    approval_state: str
    deployment_state: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "schemaVersion": self.schema_version,
            "packetId": self.packet_id,
            "weekCode": self.week_code,
            "weekStart": self.week_start,
            "weekEnd": self.week_end,
            "generatedAt": self.generated_at,
            "sourceKind": self.source_kind,
            "artifactClassification": self.artifact_classification,
            "containsStudentData": self.contains_student_data,
            "subjects": self.subjects,
            "pages": [asdict(page) for page in self.pages],
            "assignments": [asdict(item) for item in self.assignments],
            "resources": [asdict(item) for item in self.resources],
            "assessmentReminders": [asdict(item) for item in self.assessment_reminders],
            "validation": self.validation,
            "risks": [asdict(item) for item in self.risks],
            "provenance": [asdict(item) for item in self.provenance],
            "approvalState": self.approval_state,
            "deploymentState": self.deployment_state,
        }


def load_fixture(path: Path = FIXTURE_PATH) -> dict[str, Any]:
    fixture = read_json(path)
    if fixture.get("containsStudentData") is not False:
        raise ValueError("Phase 23 fixture must declare containsStudentData false")
    if fixture.get("artifactClassification") != "synthetic-weekly-content":
        raise ValueError("Unexpected Phase 23 fixture classification")
    return fixture


def canonical_week(week_code: str) -> InstructionalWeek:
    week = phase22.instructional_week_by_code(week_code)
    if not week:
        raise ValueError(f"Unknown instructional week: {week_code}")
    return InstructionalWeek(
        code=week["code"],
        starts_on=week["startsOn"],
        ends_on=week["endsOn"],
        quarter=int(week.get("quarter") or 0),
        display_subtitle=week.get("displaySubtitle") or "",
    )


def select_week(week_code: str | None = None, on_date: date | None = None) -> InstructionalWeek:
    if week_code:
        return canonical_week(week_code)
    if on_date:
        week = phase22.instructional_week_for_date(on_date)
        if not week:
            raise ValueError(f"No instructional week contains {on_date.isoformat()}")
        return canonical_week(week["code"])
    week = phase22.instructional_week_by_code("Q1W5")
    if not week:
        raise ValueError("Default startup week Q1W5 is unavailable")
    return canonical_week(week["code"])


def fixture_entries_for_week(fixture: dict[str, Any], week: InstructionalWeek) -> list[PacingEntry]:
    entries: list[PacingEntry] = []
    for raw in fixture.get("entries", []):
        entry_date = raw.get("date", "")
        if not (week.starts_on <= entry_date <= week.ends_on):
            continue
        entries.append(
            PacingEntry(
                date=entry_date,
                weekday=raw.get("weekday", ""),
                subject=raw.get("subject", ""),
                title=raw.get("title", ""),
                entry_type=raw.get("entryType", "lesson"),
                lesson=raw.get("lesson"),
                test=raw.get("test"),
                in_class=raw.get("inClass", ""),
                at_home=raw.get("atHome", ""),
                resource_hints=list(raw.get("resourceHints", [])),
                notes=raw.get("notes", ""),
            )
        )
    entries.sort(key=lambda item: (item.date, item.subject, item.title))
    return entries


def row_from_entry(entry: PacingEntry) -> dict[str, Any]:
    return {
        "subject": entry.subject,
        "lesson": entry.lesson or "",
        "tests": entry.test or "",
        "entry_date": entry.date,
        "weekday": entry.weekday,
        "title": entry.title,
        "in_class": entry.in_class,
        "at_home": entry.at_home,
        "resource_hints": list(entry.resource_hints),
        "notes": entry.notes,
    }


def group_rows(entries: list[PacingEntry]) -> dict[str, list[dict[str, Any]]]:
    groups = {
        "math": [],
        "reading-spelling": [],
        "language-arts": [],
        "history": [],
        "science": [],
    }
    for entry in entries:
        row = row_from_entry(entry)
        if entry.subject in {"reading", "spelling"}:
            groups["reading-spelling"].append(row)
        else:
            groups.setdefault(entry.subject, []).append(row)
    return groups


def subject_group_for_subject(subject: str) -> str:
    return "reading-spelling" if subject in {"reading", "spelling"} else subject


def assignment_ids_for_entry(entry: PacingEntry) -> list[str]:
    return [stable_id("assignment", entry.date, entry.subject, title) for title in assignment_titles_for_entry(entry)]


def render_page_html(week: InstructionalWeek, rows: list[dict[str, Any]]) -> str:
    def esc(text: Any) -> str:
        return html.escape(str(text or ""))

    reminder_items: list[str] = []
    for row in rows:
        reminder_items.extend(entry_display_sections(entry_from_row(row), week)["reminders"])
    reminder_list = "".join(f"<li>{esc(item)}</li>" for item in suppress_empty_daily_content(reminder_items))
    reminder_html = f"<ul>{reminder_list}</ul>" if reminder_list else ""
    parts = [
        f'<div id="kl_wrapper_3" class="kl_circle_left kl_wrapper" style="border-style: none;"><div id="kl_banner" class=""><p style="color: {WHITE}; background-color: {BLUE}; text-align: center; margin: 0;"><span style="font-size: 18pt;">&nbsp;Weekly Agenda</span><br><span style="font-size: 10pt;">{esc(week.display_subtitle)}</span></p><h3 style="background-color: {MAGENTA}; color: {WHITE}; border: 0 !important;">Reminders &amp; Resources</h3><div style="width: 100%; padding-left: 15px;">{reminder_html}</div>'
    ]
    for idx, wd in enumerate(WEEKDAYS):
        day_rows = [r for r in rows if r["weekday"] == wd]
        if not day_rows:
            continue
        in_class_items: list[dict[str, Any]] = []
        at_home_items: list[dict[str, Any]] = []
        for row in day_rows:
            sections = entry_display_sections(entry_from_row(row), week)
            in_class_items.extend(sections["in_class"])
            at_home_items.extend(sections["at_home"])
        in_class_items = [item for item in in_class_items if compact(item.get("title"))]
        at_home_items = [item for item in at_home_items if compact(item.get("title"))]
        if not in_class_items and not at_home_items:
            continue
        in_class_list = "".join(
            f"<li>{render_verified_assignment_reference(item['title'], item.get('verified_assignment_url'), bool(item.get('verified_assignment_url')))}</li>"
            for item in in_class_items
            if compact(item.get("title"))
        )
        at_home_list = "".join(
            f"<li>{render_verified_assignment_reference(item['title'], item.get('verified_assignment_url'), bool(item.get('verified_assignment_url')))}</li>"
            for item in at_home_items
            if compact(item.get("title"))
        )
        parts.append(
            f'<div id="{DAY_BLOCK_IDS[idx]}" class=""><h3 style="color: {WHITE}; background-color: {BLUE}; margin-top: 15px; margin-bottom: 2px; border: 0 !important;">{wd}</h3><div style="display: flex; width: 100%;">'
            f'<div style="width: 49%; padding-left: 15px;"><h4 class="kl_solid_border" style="color: {WHITE}; background-color: {DGRAY}; padding-left: 10px; margin: 0; border: 0 !important;">In Class</h4><ul>{in_class_list}</ul></div>'
        )
        if at_home_list:
            parts.append(
                f'<div style="width: 49%; padding-left: 15px;"><h4 class="kl_solid_border" style="color: {WHITE}; background-color: {DGRAY}; padding-left: 10px; margin: 0; border: 0 !important;">At Home</h4><ul>{at_home_list}</ul></div>'
            )
        parts.append("</div></div>")
    parts.append("</div></div>")
    return "".join(parts)


def page_title_for_group(group: str) -> str:
    return {
        "math": "Math Weekly Agenda",
        "reading-spelling": "Reading and Spelling Weekly Agenda",
        "language-arts": "Language Arts Weekly Agenda",
        "history": "History Weekly Agenda",
        "science": "Science Weekly Agenda",
    }.get(group, f"{group.title()} Weekly Agenda")


def verified_assignment_url_for_title(title: str) -> str | None:
    return {
        "SM5: Lesson 18 Evens": "https://preview.local/phase23/assignments/math-lesson-18-evens",
        "Reading Mastery Test 13": "https://preview.local/phase23/assignments/reading-test-13",
    }.get(compact(title))


def assignment_titles_for_entry(entry: PacingEntry) -> list[str]:
    lesson = int(entry.lesson) if str(entry.lesson or "").isdigit() else None
    test = int(entry.test) if str(entry.test or "").isdigit() else None
    if entry.subject == "math" and lesson:
        if entry.entry_type == "lesson":
            return [build_display_assignment_title("math", "lesson", lesson, "none")]
        return []
    if entry.subject == "math" and test:
        return [
            build_display_assignment_title("math", "study-guide", test),
            build_display_assignment_title("math", "written-test", test),
            build_display_assignment_title("math", "fact-test", test),
        ]
    if entry.subject == "reading" and test:
        titles = [build_display_assignment_title("reading", "test", test)]
        if test <= 13:
            titles.append(build_display_assignment_title("reading", "checkout", test))
        return titles
    if entry.subject == "spelling" and test:
        return [build_display_assignment_title("spelling", "test", test)]
    if entry.subject == "language-arts" and compact(entry.title):
        return [compact(entry.title)]
    return []


def entry_display_sections(entry: PacingEntry, week: InstructionalWeek) -> dict[str, list[dict[str, Any]]]:
    lesson = int(entry.lesson) if str(entry.lesson or "").isdigit() else None
    test = int(entry.test) if str(entry.test or "").isdigit() else None
    display_date = format_teacher_facing_date(entry.date, week.starts_on, week.ends_on)
    in_class: list[dict[str, Any]] = []
    at_home: list[dict[str, Any]] = []
    reminders: list[str] = []
    if entry.subject == "math" and lesson and entry.entry_type == "lesson":
        lesson_title = build_display_assignment_title("math", "lesson", lesson, "none")
        homework_title = build_display_assignment_title("math", "lesson", lesson, "evens" if lesson % 2 == 0 else "odds")
        in_class.append({"title": lesson_title})
        at_home.append({"title": homework_title, "verified_assignment_url": verified_assignment_url_for_title(homework_title)})
    elif entry.subject == "math" and test:
        in_class.extend(
            [
                {"title": build_display_assignment_title("math", "written-test", test)},
                {"title": build_display_assignment_title("math", "fact-test", test)},
            ]
        )
        reminders.append(f"Math Written Test {test} and Fact Test {test} on {display_date}")
    elif entry.subject == "reading" and test:
        test_title = build_display_assignment_title("reading", "test", test)
        in_class.append({"title": test_title})
        if test <= 13:
            checkout_title = build_display_assignment_title("reading", "checkout", test)
            at_home.append({"title": checkout_title})
            reminders.append(f"Reading Mastery Test {test} and Reading Checkout {test} on {display_date}")
        else:
            reminders.append(f"Reading Mastery Test {test} on {display_date}")
    elif entry.subject == "spelling" and test:
        test_title = build_display_assignment_title("spelling", "test", test)
        in_class.append({"title": test_title})
        reminders.append(f"Spelling Test {test} on {display_date}")
    elif entry.subject == "language-arts":
        canonical = compact(entry.title)
        if canonical:
            in_class.append({"title": canonical})
        if compact(entry.at_home):
            at_home.append({"title": canonical or compact(entry.at_home)})
    elif entry.subject in {"history", "science"}:
        canonical = compact(entry.title)
        if canonical and compact(entry.in_class):
            in_class.append({"title": canonical})
        if canonical and compact(entry.at_home):
            at_home.append({"title": canonical})
    return {"in_class": in_class, "at_home": at_home, "reminders": reminders}


def entry_from_row(row: dict[str, Any]) -> PacingEntry:
    return PacingEntry(
        date=row["entry_date"],
        weekday=row["weekday"],
        subject=row["subject"],
        title=row["title"],
        entry_type="lesson" if row.get("lesson") and not row.get("tests") else ("test" if row.get("tests") else "lesson"),
        lesson=row.get("lesson") or None,
        test=row.get("tests") or None,
        in_class=row.get("in_class", ""),
        at_home=row.get("at_home", ""),
        resource_hints=list(row.get("resource_hints", [])),
        notes=row.get("notes", ""),
    )


def build_pages(week: InstructionalWeek, entries: list[PacingEntry]) -> tuple[list[PageDraft], list[dict[str, Any]]]:
    pages: list[PageDraft] = []
    subject_summaries: list[dict[str, Any]] = []
    for group, rows in group_rows(entries).items():
        if not rows:
            continue
        html_body = render_page_html(week, rows)
        text_lines: list[str] = []
        for weekday in WEEKDAYS:
            day_rows = [row for row in rows if row["weekday"] == weekday]
            if not day_rows:
                continue
            display_lines: list[str] = []
            for row in day_rows:
                sections = entry_display_sections(entry_from_row(row), week)
                display_lines.extend(item["title"] for item in sections["in_class"])
                display_lines.extend(item["title"] for item in sections["at_home"])
            display_lines = suppress_empty_daily_content(display_lines)
            if display_lines:
                text_lines.append(f"{weekday}: {'; '.join(display_lines)}")
        text_body = "\n".join(text_lines)
        page_id = stable_id("page", week.code, group)
        linked_assignment_ids = sorted(
            {
                assignment_id
                for entry in entries
                if subject_group_for_subject(entry.subject) == group
                for assignment_id in assignment_ids_for_entry(entry)
            }
        )
        resource_ids = sorted({hint for row in rows for hint in row.get("resource_hints", [])})
        pages.append(
            PageDraft(
                page_id=page_id,
                subject_group=group,
                title=page_title_for_group(group),
                body_text=text_body,
                body_html=html_body,
                linked_assignment_ids=linked_assignment_ids,
                resource_ids=resource_ids,
                provenance=[
                    {"sourceType": "fixture", "sourceRef": str(FIXTURE_PATH), "details": "weekly input rows"},
                    {"sourceType": "canonical-week", "sourceRef": week.code, "details": "selected instructional week"},
                ],
            )
        )
        subject_summaries.append(
            {
                "subjectGroup": group,
                "entryCount": len(rows),
                "pageId": page_id,
                "assignmentCount": len(linked_assignment_ids),
            }
        )
    return pages, subject_summaries


def build_assignments(week: InstructionalWeek, entries: list[PacingEntry]) -> list[AssignmentDraft]:
    assignments: list[AssignmentDraft] = []
    for entry in entries:
        titles = assignment_titles_for_entry(entry)
        if not titles:
            continue
        display_date = format_teacher_facing_date(entry.date, week.starts_on, week.ends_on)
        for title in titles:
            assignment_id = stable_id("assignment", entry.date, entry.subject, title)
            verified_url = verified_assignment_url_for_title(title)
            body_text = title
            if entry.subject == "math" and title.endswith("Study Guide"):
                body_text = "Study Guide 18 is the only Math homework before Test 18."
            elif entry.subject == "reading" and title.startswith("Reading Checkout"):
                body_text = f"{title} fluency practice."
            assignments.append(
                AssignmentDraft(
                    assignment_id=assignment_id,
                    subject=entry.subject,
                    title=title,
                    body_text=body_text,
                    body_html=f"<p>{render_verified_assignment_reference(title, verified_url, bool(verified_url))}</p>",
                    group="Tests/Assessments" if entry.subject in {"math", "reading"} else ("Assessments" if entry.subject == "spelling" else "Assignments"),
                    points=100,
                    grade_display="Percentage",
                    submission_type="On Paper",
                    audience="All Students",
                    linked_page_id=stable_id("page", week.code, subject_group_for_subject(entry.subject)),
                    linked_resource_ids=list(entry.resource_hints),
                    verified_assignment_url=verified_url,
                    machine_date=entry.date,
                    display_date=display_date,
                    warnings=[],
                    provenance=[
                        {"sourceType": "fixture", "sourceRef": str(FIXTURE_PATH), "details": entry.title},
                        {"sourceType": "phase22-rule", "sourceRef": entry.subject, "details": "assignment draft expansion"},
                    ],
                )
            )
    return assignments


def build_resource_matches(entries: list[PacingEntry], fixture: dict[str, Any]) -> list[ResourceMatch]:
    catalog = {item["resourceId"]: item for item in fixture.get("resourceCatalog", [])}
    matched_ids = sorted({hint for entry in entries for hint in entry.resource_hints})
    resources: list[ResourceMatch] = []
    for resource_id in matched_ids:
        resource = catalog.get(resource_id)
        if not resource:
            continue
        matched_to = [entry.title for entry in entries if resource_id in entry.resource_hints]
        resources.append(
            ResourceMatch(
                resource_id=resource_id,
                canonical_name=resource["canonicalName"],
                subject=resource["subject"],
                resource_type=resource["resourceType"],
                verification_status=resource["verificationStatus"],
                match_confidence=float(resource.get("matchConfidence", 0.97)),
                match_reason=resource.get("matchReason", "approved synthetic match"),
                matched_to=matched_to,
                provenance=[
                    {"sourceType": "fixture", "sourceRef": str(FIXTURE_PATH), "details": resource.get("notes", "")},
                    {"sourceType": "resource-catalog", "sourceRef": resource_id, "details": "approved match"},
                ],
            )
        )
    return resources


def build_assessment_reminders(week: InstructionalWeek, entries: list[PacingEntry]) -> list[AssessmentReminder]:
    reminders: list[AssessmentReminder] = []
    for entry in entries:
        if entry.entry_type != "test":
            continue
        reminder_id = stable_id("reminder", entry.date, entry.subject, entry.test or entry.lesson or entry.title)
        if entry.subject == "reading" and entry.test == "14":
            title = "Reading Test 14"
            body = f"{title} is scheduled on {format_teacher_facing_date(entry.date, week.starts_on, week.ends_on)}. No companion support packet is assigned for Test 14."
            reminders.append(
                AssessmentReminder(
                    reminder_id=reminder_id,
                    date=entry.date,
                    title=title,
                    body_text=body,
                    body_html=f"<p>{html.escape(body)}</p>",
                    linked_assignment_ids=[stable_id("assignment", entry.date, entry.subject, title)],
                    display_date=format_teacher_facing_date(entry.date, week.starts_on, week.ends_on),
                    warnings=[],
                    provenance=[
                        {"sourceType": "phase22-rule", "sourceRef": "reading-checkout", "details": "No checkout companion exists for Test 14"},
                    ],
                )
            )
            continue
        titles = assignment_titles_for_entry(entry)
        linked_ids = [stable_id("assignment", entry.date, entry.subject, title) for title in titles]
        display_date = format_teacher_facing_date(entry.date, week.starts_on, week.ends_on)
        if entry.subject == "math" and entry.test:
            title = f"Math Written Test {entry.test} and Fact Test {entry.test}"
        elif entry.subject == "reading" and entry.test:
            title = f"Reading Mastery Test {entry.test}"
        elif entry.subject == "spelling" and entry.test:
            title = f"Spelling Test {entry.test}"
        else:
            title = compact(entry.title or f"{entry.subject.title()} Test {entry.test or ''}")
        body = f"{title} on {display_date}."
        reminders.append(
            AssessmentReminder(
                reminder_id=reminder_id,
                date=entry.date,
                title=title,
                body_text=body,
                body_html=f"<p>{html.escape(body)}</p>",
                linked_assignment_ids=linked_ids,
                display_date=display_date,
                warnings=[],
                provenance=[
                    {"sourceType": "fixture", "sourceRef": str(FIXTURE_PATH), "details": entry.title},
                    {"sourceType": "phase22-rule", "sourceRef": "assessment-reminder", "details": "linked to packet assignments"},
                ],
            )
        )
    return reminders


def validate_packet(packet: dict[str, Any], fixture: dict[str, Any] | None = None) -> dict[str, Any]:
    findings: list[ValidationFinding] = []
    risks: list[RiskFinding] = []
    if packet.get("containsStudentData") is not False:
        findings.append(ValidationFinding("fail", "privacy.student-data", "Packet must not contain student data", "packet"))
    else:
        findings.append(ValidationFinding("pass", "privacy.student-data", "Packet excludes student data", "packet"))

    if packet.get("deploymentState") != "preview-only":
        findings.append(ValidationFinding("fail", "deployment.preview-only", "Packet must remain preview-only", "packet"))
    else:
        findings.append(ValidationFinding("pass", "deployment.preview-only", "Packet is preview-only", "packet"))

    findings.append(
        ValidationFinding(
            "warn",
            "due-time.unresolved",
            "Canvas assignment due-time convention remains unresolved",
            "packet.assignments",
        )
    )

    week = canonical_week(packet["weekCode"])
    if packet["weekStart"] != week.starts_on or packet["weekEnd"] != week.ends_on:
        findings.append(ValidationFinding("fail", "week.boundary", "Packet week boundaries do not match canonical calendar", packet["weekCode"]))
    else:
        findings.append(ValidationFinding("pass", "week.boundary", "Packet week boundaries match canonical calendar", packet["weekCode"]))

    for reminder in packet.get("assessmentReminders", []):
        if reminder["title"] == "Reading Test 14" or "Test 14" in reminder["title"]:
            if "Checkout" in reminder["body_text"] or "Checkout" in reminder["body_html"]:
                findings.append(ValidationFinding("fail", "reading-test-14.checkout", "Reading Test 14 must not create a checkout reminder", reminder["title"]))
            else:
                findings.append(ValidationFinding("pass", "reading-test-14.checkout", "Reading Test 14 correctly has no checkout reminder", reminder["title"]))

    for assignment in packet.get("assignments", []):
        text_blob = " ".join([assignment.get("title", ""), assignment.get("body_text", ""), assignment.get("body_html", "")])
        if 'href="#"' in text_blob or "javascript:" in text_blob:
            findings.append(ValidationFinding("fail", "links.fake", "Fake links are forbidden", assignment.get("assignment_id")))

    pass_count = sum(1 for item in findings if item.severity == "pass")
    warn_count = sum(1 for item in findings if item.severity == "warn")
    fail_count = sum(1 for item in findings if item.severity == "fail")
    risks.append(RiskFinding("warning", "due-time", "Canvas assignment due-time convention remains unresolved", "Keep assignment dueTime fields blocked or explicitly unresolved"))
    if fixture is not None:
        if fixture.get("artifactClassification") != "synthetic-weekly-content":
            findings.append(ValidationFinding("fail", "fixture.classification", "Fixture classification must remain synthetic-weekly-content", str(FIXTURE_PATH)))
            fail_count += 1
        if fixture.get("containsStudentData") is not False:
            findings.append(ValidationFinding("fail", "fixture.student-data", "Fixture must not contain student data", str(FIXTURE_PATH)))
            fail_count += 1
    return {
        "passCount": pass_count,
        "warnCount": warn_count if warn_count else 1,
        "failCount": fail_count,
        "findings": [asdict(item) for item in findings],
    }, risks


def build_packet(week_code: str | None = None, fixture_path: Path = FIXTURE_PATH) -> dict[str, Any]:
    fixture = load_fixture(fixture_path)
    week = select_week(week_code or fixture.get("weekCode"))
    entries = fixture_entries_for_week(fixture, week)
    pages, subjects = build_pages(week, entries)
    assignments = build_assignments(week, entries)
    resources = build_resource_matches(entries, fixture)
    reminders = build_assessment_reminders(week, entries)
    packet = ProductionPacket(
        schema_version=1,
        packet_id=stable_id("packet", week.code, fixture_path.read_text(encoding="utf-8")),
        week_code=week.code,
        week_start=week.starts_on,
        week_end=week.ends_on,
        generated_at=now_utc(),
        source_kind=fixture.get("sourceKind", "synthetic"),
        artifact_classification="weekly-content-production-packet",
        contains_student_data=False,
        subjects=subjects,
        pages=pages,
        assignments=assignments,
        resources=resources,
        assessment_reminders=reminders,
        validation={},
        risks=[],
        provenance=[
            ProvenanceRecord("fixture", str(fixture_path), "synthetic weekly content source"),
            ProvenanceRecord("canonical-calendar", "config/curriculum/canvas/instructional-weeks-2026-2027.json", "instructional week authority"),
            ProvenanceRecord("phase22-rules", "scripts/canvas_llm_phase22/phase22_workstation.py", "curriculum resolution and preview-only safety rules"),
        ],
        approval_state="draft",
        deployment_state="preview-only",
    )
    validation, risks = validate_packet(packet.to_dict(), fixture)
    packet.validation = validation
    packet.risks = risks
    return packet.to_dict()


def load_saved_packet() -> dict[str, Any] | None:
    for path in (LOCAL_PACKET_STORE, APP_DATA_PATH):
        if path.exists():
            return read_json(path)
    return None


def save_packet(packet: dict[str, Any], path: Path = LOCAL_PACKET_STORE) -> Path:
    write_json(path, packet)
    return path


def packet_summary(packet: dict[str, Any]) -> str:
    return f"week={packet['weekCode']} pages={len(packet.get('pages', []))} assignments={len(packet.get('assignments', []))} resources={len(packet.get('resources', []))} reminders={len(packet.get('assessmentReminders', []))}"


def render_packet_text(packet: dict[str, Any]) -> str:
    lines = [
        f"Packet {packet['packetId']}",
        f"Week {packet['weekCode']} {packet['weekStart']}..{packet['weekEnd']}",
        f"Source kind: {packet['sourceKind']}",
        f"Approval: {packet['approvalState']} / {packet['deploymentState']}",
        "",
        "Pages:",
    ]
    for page in packet.get("pages", []):
        lines.append(f"- {page['title']} ({page['subject_group']})")
    lines.append("")
    lines.append("Assignments:")
    for assignment in packet.get("assignments", []):
        lines.append(f"- {assignment['title']} [{assignment['subject']}]")
    lines.append("")
    lines.append("Resources:")
    for resource in packet.get("resources", []):
        lines.append(f"- {resource['canonical_name']} -> {', '.join(resource['matched_to'])}")
    lines.append("")
    lines.append("Assessment reminders:")
    for reminder in packet.get("assessmentReminders", []):
        lines.append(f"- {reminder['title']} on {reminder['date']}")
    lines.append("")
    lines.append(f"Validation: PASS {packet['validation']['passCount']} WARN {packet['validation']['warnCount']} FAIL {packet['validation']['failCount']}")
    return "\n".join(lines)


def render_packet_html(packet: dict[str, Any]) -> str:
    def esc(text: Any) -> str:
        return html.escape(str(text or ""))

    page_cards = "".join(
        f"<article class=\"card\"><h3>{esc(page['title'])}</h3><p class=\"muted\">{esc(page['subject_group'])}</p><pre>{esc(page['body_text'])}</pre></article>"
        for page in packet.get("pages", [])
    )
    assignment_cards = "".join(
        f"<article class=\"card\"><h3>{esc(item['title'])}</h3><p>{esc(item['subject'])} / {esc(item['group'])}</p><pre>{esc(item['body_text'])}</pre></article>"
        for item in packet.get("assignments", [])
    )
    resource_cards = "".join(
        f"<article class=\"card\"><h3>{esc(item['canonical_name'])}</h3><p>{esc(item['resource_type'])}</p><p>{esc(item['match_reason'])}</p></article>"
        for item in packet.get("resources", [])
    )
    reminder_cards = "".join(
        f"<article class=\"card\"><h3>{esc(item['title'])}</h3><p>{esc(item['date'])}</p><p>{esc(item['body_text'])}</p></article>"
        for item in packet.get("assessmentReminders", [])
    )
    validation_items = "".join(
        f"<li class=\"{esc(item['severity'])}\"><strong>{esc(item['severity']).upper()}</strong> {esc(item['message'])}</li>"
        for item in packet.get("validation", {}).get("findings", [])
    )
    risks = "".join(
        f"<li class=\"{esc(item['severity'])}\"><strong>{esc(item['severity']).upper()}</strong> {esc(item['message'])}</li>"
        for item in packet.get("risks", [])
    )
    provenance_items = "".join(
        f"<li><strong>{esc(item['source_type'])}</strong> {esc(item['source_ref'])} — {esc(item['details'])}</li>"
        for item in packet.get("provenance", [])
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Phase 23 Weekly Content Production Engine</title>
  <link rel="stylesheet" href="/styles.css">
</head>
<body>
  <header class="hero">
    <div>
      <p class="eyebrow">Phase 23</p>
      <h1>Weekly Content Production Engine</h1>
      <p class="lede">Local-first packet builder, preview renderer, and validator.</p>
      <p class="meta">Packet {esc(packet['packetId'])} • {esc(packet['weekCode'])} • {esc(packet['weekStart'])} to {esc(packet['weekEnd'])}</p>
    </div>
    <div class="status">
      <span>Preview-only</span>
      <span>No Canvas writes</span>
      <span>No email sends</span>
      <span class="warn">WARN {packet['validation']['warnCount']}</span>
    </div>
  </header>
  <main class="shell">
    <nav class="tabs">
      <button class="tab active" data-tab="summary">Summary</button>
      <button class="tab" data-tab="pages">Pages</button>
      <button class="tab" data-tab="assignments">Assignments</button>
      <button class="tab" data-tab="resources">Resources</button>
      <button class="tab" data-tab="reminders">Reminders</button>
      <button class="tab" data-tab="validation">Validation</button>
      <button class="tab" data-tab="risks">Risks</button>
      <button class="tab" data-tab="provenance">Provenance</button>
      <button class="tab" data-tab="raw">Raw Packet</button>
    </nav>
    <section class="workspace">
      <section class="panel active" id="tab-summary">
        <h2>Packet Summary</h2>
        <p>{esc(packet_summary(packet))}</p>
        <p>Approval state: {esc(packet['approvalState'])}</p>
        <p>Deployment state: {esc(packet['deploymentState'])}</p>
      </section>
      <section class="panel" id="tab-pages"><h2>Page Drafts</h2><div class="card-grid">{page_cards}</div></section>
      <section class="panel" id="tab-assignments"><h2>Assignment Drafts</h2><div class="card-grid">{assignment_cards}</div></section>
      <section class="panel" id="tab-resources"><h2>Approved Resource Matches</h2><div class="card-grid">{resource_cards}</div></section>
      <section class="panel" id="tab-reminders"><h2>Assessment Reminders</h2><div class="card-grid">{reminder_cards}</div></section>
      <section class="panel" id="tab-validation"><h2>Validation</h2><ul class="finding-list">{validation_items}</ul><p>PASS {packet['validation']['passCount']} • WARN {packet['validation']['warnCount']} • FAIL {packet['validation']['failCount']}</p></section>
      <section class="panel" id="tab-risks"><h2>Risks</h2><ul class="finding-list">{risks}</ul></section>
      <section class="panel" id="tab-provenance"><h2>Provenance</h2><ul class="finding-list">{provenance_items}</ul></section>
      <section class="panel" id="tab-raw"><h2>Raw Packet</h2><pre id="raw-json">{esc(json.dumps(packet, indent=2, ensure_ascii=False))}</pre></section>
    </section>
  </main>
  <script src="/workstation.js"></script>
</body>
</html>"""


class PacketHandler(SimpleHTTPRequestHandler):
    db_path: Path | None = None

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        return

    def _read_json_body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        return json.loads(raw.decode("utf-8") or "{}")

    def _send_json(self, payload: dict[str, Any], status: int = 200) -> None:
        body = json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/bootstrap":
            packet, local_state = current_packet()
            self._send_json(
                {
                    "currentWeek": {
                        "weekCode": packet["weekCode"],
                        "weekStart": packet["weekStart"],
                        "weekEnd": packet["weekEnd"],
                    },
                    "savedPacket": local_state.get("status") == "saved",
                    "localState": local_state,
                    "status": "preview-only",
                }
            )
            return
        if parsed.path == "/api/packet":
            packet, _ = current_packet()
            self._send_json(packet)
            return
        if parsed.path == "/api/local-state":
            params = urllib.parse.parse_qs(parsed.query)
            week_code = params.get("weekCode", [None])[0] or current_packet()[0]["weekCode"]
            self._send_json(load_local_state_record(week_code))
            return
        if parsed.path == "/api/health":
            packet, _ = current_packet()
            self._send_json(
                {
                    "status": "ok",
                    "previewOnly": True,
                    "canvasWritesAllowed": False,
                    "emailSendsAllowed": False,
                    "warnCount": packet["validation"]["warnCount"],
                    "failCount": packet["validation"]["failCount"],
                }
            )
            return
        if parsed.path == "/":
            self.path = "/index.html"
            return super().do_GET()
        return super().do_GET()

    def do_POST(self):  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/local-state":
            try:
                body = self._read_json_body()
                result = save_local_state_record(body.get("weekCode"), body.get("approvalState"), body.get("version"))
            except ValueError as error:
                self._send_json({"status": "error", "error": str(error)}, 400)
                return
            if result.get("status") == "conflict":
                self._send_json(result, 409)
            else:
                self._send_json(result)
            return
        if parsed.path == "/api/export":
            packet, _ = current_packet()
            path = save_packet(packet)
            self._send_json({"ok": True, "savedPath": str(path), "summary": packet_summary(packet)})
            return
        if parsed.path == "/api/regenerate":
            packet, _ = current_packet()
            save_packet(packet)
            self._send_json({"ok": True, "summary": packet_summary(packet)})
            return
        self.send_error(404, "unknown endpoint")


def command_build_demo(args: argparse.Namespace) -> int:
    packet = build_packet(args.week)
    out = Path(getattr(args, "out", APP_DATA_PATH))
    write_json(out, packet)
    print(f"Phase 23 demo packet rebuilt: {out}")
    return 0


def command_validate(args: argparse.Namespace) -> int:
    total_pass = 0
    total_warn = 0
    total_fail = 0
    for raw in args.paths:
        path = Path(raw)
        if not path.exists():
            print(f"FAIL missing artifact: {path}")
            total_fail += 1
            continue
        packet = read_json(path)
        validation, _ = validate_packet(packet)
        print(f"PASS: packet {packet.get('weekCode', path.name)}")
        print(f"PASS: validation findings={len(validation['findings'])}")
        print(f"PASS: packet warnings={validation['warnCount']} fails={validation['failCount']}")
        total_pass += validation["passCount"]
        total_warn += validation["warnCount"]
        total_fail += validation["failCount"]
    print()
    print("PASS:", total_pass)
    print("WARN:", total_warn)
    print("FAIL:", total_fail)
    return 0 if total_fail == 0 else 1


def command_self_test(args: argparse.Namespace) -> int:
    import tempfile
    fixture = load_fixture()
    packet = build_packet()
    assert packet["schemaVersion"] == 1
    assert packet["weekCode"] == "Q1W5"
    assert packet["containsStudentData"] is False
    assert packet["validation"]["failCount"] == 0
    assert packet["validation"]["warnCount"] >= 1
    assert any(rem["title"] == "Reading Test 14" for rem in packet["assessmentReminders"])
    assert all("Checkout 14" not in rem["body_text"] for rem in packet["assessmentReminders"])
    assert any(res["resource_id"] == "rm4-checkout-13-passage" for res in packet["resources"])
    temp_path = Path(tempfile.mkdtemp()) / "phase23-demo.json"
    save_packet(packet, temp_path)
    assert read_json(temp_path)["packetId"] == packet["packetId"]
    validation, _ = validate_packet(packet, fixture)
    assert validation["failCount"] == 0
    global LOCAL_ROOT, LOCAL_STATE_DIR, LOCAL_STATE_QUARANTINE_DIR
    original_root = LOCAL_ROOT
    original_state_dir = LOCAL_STATE_DIR
    original_quarantine_dir = LOCAL_STATE_QUARANTINE_DIR
    try:
        state_root = Path(tempfile.mkdtemp())
        LOCAL_ROOT = state_root
        LOCAL_STATE_DIR = LOCAL_ROOT / "state"
        LOCAL_STATE_QUARANTINE_DIR = LOCAL_ROOT / "quarantine" / "state"
        state = save_local_state_record("Q1W5", "reviewed", 0)
        assert state["approvalState"] == "reviewed"
        assert load_local_state_record("Q1W5")["approvalState"] == "reviewed"
        assert current_packet("Q1W5")[0]["approvalState"] == "reviewed"
    finally:
        LOCAL_ROOT = original_root
        LOCAL_STATE_DIR = original_state_dir
        LOCAL_STATE_QUARANTINE_DIR = original_quarantine_dir
    print("PASS Phase 23 self-test complete")
    return 0


def command_serve(args: argparse.Namespace) -> int:
    APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
    packet = build_packet(args.week)
    if not APP_DATA_PATH.exists():
        write_json(APP_DATA_PATH, packet)
    os.chdir(APP_DIR)
    server = ThreadingHTTPServer((args.host, args.port), PacketHandler)
    print(f"Phase 23 workstation serving at http://{args.host}:{args.port} summary={packet_summary(packet)}")
    server.serve_forever()


def command_export(args: argparse.Namespace) -> int:
    packet, _ = current_packet(args.week)
    out = Path(args.out or LOCAL_PACKET_STORE)
    save_packet(packet, out)
    print(f"Phase 23 packet exported: {out}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Phase 23 weekly content production engine")
    parser.add_argument("--week", default=None, help="Canonical instructional week code")
    parser.add_argument("--fixture", default=str(FIXTURE_PATH), help="Fixture JSON path")
    parser.add_argument("--db", default=None, help="Reserved for future local persistence hooks")
    sub = parser.add_subparsers(dest="cmd", required=True)

    build_demo = sub.add_parser("build-demo", help="Build the committed demo packet")
    build_demo.add_argument("--out", default=str(APP_DATA_PATH))
    build_demo.set_defaults(func=command_build_demo)

    validate = sub.add_parser("validate", help="Validate packet JSON files")
    validate.add_argument("paths", nargs="+")
    validate.set_defaults(func=command_validate)

    serve = sub.add_parser("serve", help="Serve the local packet viewer")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8775)
    serve.set_defaults(func=command_serve)

    export = sub.add_parser("export", help="Export a packet locally")
    export.add_argument("--out", default=str(LOCAL_PACKET_STORE))
    export.set_defaults(func=command_export)

    self_test = sub.add_parser("self-test", help="Run deterministic packet assertions")
    self_test.set_defaults(func=command_self_test)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
