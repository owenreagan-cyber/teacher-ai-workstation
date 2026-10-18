#!/usr/bin/env python3
"""Q1W8 subject package preflight — build local drafts + GET-only live checks.

Usage:
    python3 scripts/canvas-llm/q1w8_preflight.py
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.canvas_llm_phase22 import canvas_credentials as credentials  # noqa: E402
from scripts.canvas_llm_phase22 import subject_weekly_update as swu  # noqa: E402

OUT_DIR = REPO_ROOT / ".local" / "canvas-llm" / "q1w8-audit"
BUILD_PATH = REPO_ROOT / "scripts" / "canvas-llm" / "build_q1w8_subject_package.py"

SUBJECTS: list[tuple[str, int]] = [
    ("Math", 26404),
    ("Reading/Spelling", 26442),
    ("Language Arts", 28171),
    ("History", 28165),
]
SCIENCE = ("Science", 28166)
PAGE_URL = "q1w8-september-7-11-2026"
WEEK_MARKER = "September 7\u201311, 2026"

PLANNED_ASSIGNMENTS: dict[int, list[tuple[str, str]]] = {
    26404: [
        ("SM5: Lesson 26 Homework", "Homework/Class Work"),
        ("SM5: Written Assessment 4", "Written Assessments"),
        ("SM5: Fact Assessment 4", "Fact Assessments"),
    ],
    26442: [
        ("RM4: Lesson 30 Workbook", "Homework"),
        ("RM4: Lesson 31 Workbook and Comprehension", "Homework"),
    ],
}

PLANNED_ANNOUNCEMENTS: dict[int, list[str]] = {
    26404: ["Math Assessment Reminder - Thursday"],
    26442: ["Reading Test & Fluency Checkout Reminder - Wednesday"],
}

WEEKLY_UPDATE_DRAFTS: dict[str, dict[str, Any]] = {
    "math": {
        "week_in_review": (
            "We had another great week in Math! Students completed Lessons 21\u201325 "
            "and worked hard throughout the week."
        ),
        "week_ahead": (
            "Next week, students will complete <strong>Written Assessment 4 and Fact "
            "Assessment 4 on Thursday, September 10</strong>. Fact Assessment 4 includes "
            "<strong>40 multiplication facts</strong>. We will review together in class on "
            "Wednesday before completing Lessons 26 and 27."
        ),
    },
    "reading_spelling": {
        "week_in_review": (
            "In Reading, students completed Lessons 25\u201329. In Spelling, students "
            "completed Lessons 21\u201325."
        ),
        "week_ahead": (
            "Next week, students will complete a <strong>Reading Test and Fluency Checkout "
            "on Wednesday, September 9</strong>. The Reading Test will cover vocabulary "
            "and story concepts from Lessons 21\u201330. "
            "Looking ahead, the final Spelling Test of Track 1 will be on "
            "<strong>Wednesday, September 16</strong>."
        ),
    },
    "language_arts": {
        "week_in_review": (
            "We had a productive week in Language Arts! Students completed the "
            "<strong>Chapter 3 Shurley English Test</strong> and began our Personal "
            "Narrative writing unit."
        ),
        "week_ahead": (
            "Next week, we will continue our Personal Narrative writing unit with "
            "Lessons 7\u201310."
        ),
    },
    "history": {
        "week_in_review": (
            "We had a great week in History! Students completed our World Mountains unit, "
            "including the World Mountains Test, and began their Map Project."
        ),
        "week_ahead": (
            "Next week, we will continue with "
            "<strong>Medieval Islamic Kingdoms Chapters 2\u20134</strong>."
        ),
    },
}


def _load_build() -> Any:
    spec = importlib.util.spec_from_file_location("build_q1w8_subject_package", BUILD_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _get(base_url: str, token: str, path: str) -> Any:
    req = urllib.request.Request(
        f"{base_url}{path}",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            text = response.read().decode("utf-8")
            return json.loads(text) if text else None
    except urllib.error.HTTPError as exc:
        detail = ""
        try:
            detail = (exc.read() or b"").decode("utf-8", "replace")[:300]
        except Exception:  # noqa: BLE001
            detail = ""
        return {"__error__": f"HTTP {exc.code}: {detail or exc.reason}"}
    except urllib.error.URLError as exc:
        return {"__error__": f"network: {exc.reason}"}


def _paginate(base_url: str, token: str, path: str, params: dict[str, Any] | None = None) -> list[Any]:
    merged = {"per_page": 100}
    if params:
        merged.update(params)
    url = f"{base_url}{path}?{urllib.parse.urlencode(merged, doseq=True)}"
    items: list[Any] = []
    for _ in range(50):
        req = urllib.request.Request(
            url,
            headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            text = response.read().decode("utf-8")
            link = response.headers.get("Link", "")
        data = json.loads(text) if text else []
        items.extend(data if isinstance(data, list) else [data])
        nxt = None
        for part in link.split(","):
            if 'rel="next"' in part:
                s = part.find("<")
                e = part.find(">")
                if 0 <= s < e:
                    nxt = part[s + 1 : e]
        if not nxt:
            break
        url = nxt
    return items


def _page_bodies(manifest: dict[str, Any]) -> dict[str, str]:
    bodies: dict[str, str] = {}
    for action in manifest.get("actions", []):
        if action.get("object_type") == "page":
            bodies[action["course"]] = action.get("body") or ""
    return bodies


def _print_agenda_table(title: str, rows: list[tuple[str, str]]) -> None:
    print(f"\n{title}")
    for day, content in rows:
        print(f"  {day}: {content}")


def main() -> int:
    build = _load_build()
    build.write_local_artifacts()

    credentials.load_credentials()
    base_url = os.environ["CANVAS_BASE_URL"].strip().rstrip("/")
    token = os.environ["CANVAS_TOKEN"]

    manifest = json.loads((OUT_DIR / "q1w8-manifest.json").read_text(encoding="utf-8"))
    bodies = _page_bodies(manifest)
    blockers: list[str] = []
    warnings: list[str] = []

    print("Q1W8 SUBJECT PACKAGE — TEACHER REVIEW (build + GET-only preflight)")
    print(f"generated_at_utc: {datetime.now(timezone.utc).isoformat()}")
    me = _get(base_url, token, "/api/v1/users/self")
    print(f"USER: id={me.get('id')} name={me.get('name')!r}")

    # Power Up C verification
    pu = _get(base_url, token, f"/api/v1/files/{build.POWER_UP_C_FILE_ID}")
    pu_ok = (
        isinstance(pu, dict)
        and pu.get("display_name") == "Power Up C.pdf"
        and pu.get("hidden") is False
        and pu.get("id") == build.POWER_UP_C_FILE_ID
    )
    print("\nPOWER UP C FILE/RESOURCE STATUS")
    if pu_ok:
        print(
            f"  VERIFIED: Power Up C.pdf id={build.POWER_UP_C_FILE_ID} hidden=false "
            f"preview={build.POWER_UP_C_PREVIEW}"
        )
    else:
        blockers.append("Power Up C file could not be verified for Math assessment reminder embed")
        print(f"  FAIL: {pu}")

    # Teacher review tables
    _print_agenda_table(
        "Math",
        [
            ("Mon", "Labor Day — No School"),
            ("Tue", "Lesson 26 / Problems 1-10 | At Home: Lesson 26 Problems 12-30 EVENS"),
            ("Wed", "Review Sheet"),
            ("Thu", "Written Assessment 4 / Fact Assessment 4"),
            ("Fri", "Lesson 27 / Problems 1-10"),
        ],
    )
    _print_agenda_table(
        "Reading/Spelling",
        [
            ("Mon", "Labor Day — No School"),
            ("Tue", "Spelling L26 / Reading L30 / Workbook"),
            ("Wed", "Spelling L27 / Reading Test / Fluency Checkout"),
            ("Thu", "Spelling L28 / Reading L31 / Workbook and Comprehension"),
            ("Fri", "Spelling L29 / Reading L32"),
        ],
    )
    _print_agenda_table(
        "Language Arts",
        [
            ("Mon", "Labor Day — No School"),
            ("Tue", "Personal Narrative Lesson 7"),
            ("Wed", "Personal Narrative Lesson 8"),
            ("Thu", "Personal Narrative Lesson 9"),
            ("Fri", "Personal Narrative Lesson 10"),
        ],
    )
    _print_agenda_table(
        "History",
        [
            ("Mon", "Labor Day — No School"),
            ("Tue", "Medieval Islamic Kingdoms Chapter 2"),
            ("Wed", "Medieval Islamic Kingdoms Chapter 3"),
            ("Thu", "Medieval Islamic Kingdoms Chapter 4"),
            ("Fri", "Medieval Islamic Kingdoms Chapter 4"),
        ],
    )
    print("\nScience")
    print("  blank (inactive quarter — leave untouched)")

    warnings.append(
        "Language Arts Personal Narrative Lessons 7–10 use Owen's approved lesson numbers; "
        "verified subtitle mappings exist only for Lessons 1–4 (Q1W7)"
    )

    print("\n--- LIVE PREFLIGHT ---")
    drift_notes: list[str] = []
    dup_assign: list[str] = []
    dup_ann: list[str] = []
    front_page_actions: list[str] = []

    for name, cid in SUBJECTS:
        print(f"\n{name} ({cid})")
        course = _get(base_url, token, f"/api/v1/courses/{cid}")
        print(f"  course name={course.get('name')!r}")

        fp = _get(base_url, token, f"/api/v1/courses/{cid}/front_page")
        fp_url = fp.get("url") if isinstance(fp, dict) else None
        print(f"  current front_page={fp_url!r} (Q1W8 target={PAGE_URL!r})")
        if fp_url != PAGE_URL:
            front_page_actions.append(f"{name}: UPDATE {PAGE_URL} + SET_AND_VERIFY front page")
            drift_notes.append(f"{name} front page still on {fp_url!r}")

        q8 = _get(base_url, token, f"/api/v1/courses/{cid}/pages/{PAGE_URL}")
        live_blank = (q8.get("body") or "").count("&nbsp;&nbsp;")
        print(f"  Q1W8 page exists published={q8.get('published')} blank_placeholders={live_blank}")

        groups = _paginate(base_url, token, f"/api/v1/courses/{cid}/assignment_groups")
        gmap = {g.get("name"): g.get("id") for g in groups}
        for title, grp in PLANNED_ASSIGNMENTS.get(cid, []):
            if grp not in gmap:
                blockers.append(f"{name}: missing assignment group {grp!r}")
            hits = [
                a
                for a in _paginate(base_url, token, f"/api/v1/courses/{cid}/assignments")
                if (a.get("name") or "").strip() == title
            ]
            if hits:
                dup_assign.append(f"{name}: {title!r} (id {hits[0].get('id')})")
            else:
                print(f"  PLANNED CREATE assignment: {title!r} -> {grp!r}")

        for title in PLANNED_ANNOUNCEMENTS.get(cid, []):
            hits = [
                a
                for a in _paginate(
                    base_url,
                    token,
                    f"/api/v1/courses/{cid}/discussion_topics",
                    {"only_announcements": "true"},
                )
                if (a.get("title") or "").strip() == title
            ]
            if hits:
                dup_ann.append(f"{name}: {title!r} (id {hits[0].get('id')})")
            else:
                print(f"  PLANNED CREATE announcement: {title!r}")

        wu_title = swu.SUBJECTS[
            {
                "Math": "math",
                "Reading/Spelling": "reading_spelling",
                "Language Arts": "language_arts",
                "History": "history",
            }[name]
        ]["title"]
        wu_hits = [
            a
            for a in _paginate(
                base_url,
                token,
                f"/api/v1/courses/{cid}/discussion_topics",
                {"only_announcements": "true"},
            )
            if (a.get("title") or "").strip() == wu_title
        ]
        if wu_hits:
            dup_ann.append(f"{name}: {wu_title!r} (id {wu_hits[0].get('id')}) — UPDATE in place at launch")
        else:
            print(f"  PLANNED Weekly Update: {wu_title!r}")

    print(f"\n{SCIENCE[0]} ({SCIENCE[1]}) — LEAVE untouched (inactive quarter)")

    # Weekly update drafts
    print("\nWEEKLY UPDATE ANNOUNCEMENT PLAN")
    for subject_key, draft in WEEKLY_UPDATE_DRAFTS.items():
        course = swu.SUBJECTS[subject_key]["label"]
        title = swu.SUBJECTS[subject_key]["title"]
        manifest_body = bodies[
            {
                "math": "Math",
                "reading_spelling": "Reading/Spelling",
                "language_arts": "Language Arts",
                "history": "History",
            }[subject_key]
        ]
        msg = swu.build_message(
            subject_key,
            draft["week_in_review"],
            draft["week_ahead"],
            manifest_body,
        )
        slug = subject_key.replace("_", "-")
        path = OUT_DIR / f"q1w8-subject-weekly-update-{slug}.html"
        path.write_text(msg, encoding="utf-8")
        print(f"  {course}: {title!r} -> {path.name}")

    print("\nPLANNED PAGE UPDATES")
    for name in ("Math", "Reading/Spelling", "Language Arts", "History"):
        print(f"  - {name}: UPDATE in place {PAGE_URL!r}")

    print("\nPLANNED FRONT-PAGE ACTIONS")
    if front_page_actions:
        for item in front_page_actions:
            print(f"  - {item}")
    else:
        print("  - none (already on Q1W8 — verify only)")

    print("\nPLANNED ASSIGNMENTS")
    for cid in (26404, 26442):
        for title, grp in PLANNED_ASSIGNMENTS.get(cid, []):
            print(f"  - CREATE {title!r} ({grp})")

    print("\nMATH ASSESSMENT REMINDER DRAFT")
    print(f"  - {OUT_DIR / 'q1w8-math-assessment-reminder.html'}")
    print("  - embeds verified Power Up C.pdf (6120836)")

    print("\nREADING TEST & FLUENCY CHECKOUT REMINDER DRAFT")
    print(f"  - {OUT_DIR / 'q1w8-reading-test-reminder.html'}")

    print("\nREADING/SPELLING SEPT. 16 SPELLING REMINDER STATUS")
    print("  - included on Reading/Spelling page Reminders + Weekly Update prose only")
    print("  - no Sept. 16 Spelling Test assignment planned for Q1W8")

    print("\nDUPLICATE STATUS")
    print(f"  assignments: {len(dup_assign)} existing matches")
    for item in dup_assign:
        print(f"    - {item}")
    print(f"  announcements: {len(dup_ann)} existing matches")
    for item in dup_ann:
        print(f"    - {item}")

    print("\nDRIFT STATUS")
    if drift_notes:
        for note in drift_notes:
            print(f"  - {note}")
    else:
        print("  - no unexpected live drift beyond expected Q1W7 front pages")

    if warnings:
        print("\nWARNINGS (teacher review)")
        for w in warnings:
            print(f"  - {w}")

    print("\nWRITES PERFORMED: 0")
    print(f"BLOCKERS: {len(blockers)}")
    for b in blockers:
        print(f"  - {b}")

    print("\nLocal artifacts:")
    print(f"  - {OUT_DIR / 'q1w8-manifest.json'}")
    print(f"  - {OUT_DIR / 'q1w8-preflight-report.json'}")
    print("\nSTOPPED FOR OWEN APPROVAL — do not launch yet.")

    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "blockers": blockers,
        "warnings": warnings,
        "duplicate_assignments": dup_assign,
        "duplicate_announcements": dup_ann,
        "drift_notes": drift_notes,
        "power_up_c_verified": pu_ok,
        "writes_performed": 0,
    }
    report_path = OUT_DIR / "q1w8-preflight-report.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return 1 if blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
