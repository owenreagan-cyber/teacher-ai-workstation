#!/usr/bin/env python3
"""Guarded Q1W8 subject package launch + verification.

Usage:
    CANVAS_LLM_DEPLOYMENT_MODE=live CANVAS_LLM_LIVE_Q1W2_APPROVED=1 \
        python3 scripts/canvas-llm/q1w8_subject_launch.py
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.canvas_llm_phase22 import canvas_credentials as credentials  # noqa: E402
from scripts.canvas_llm_phase22 import canvas_launcher as launcher  # noqa: E402
from scripts.canvas_llm_phase22 import subject_weekly_update as swu  # noqa: E402

BUILD_PATH = REPO_ROOT / "scripts" / "canvas-llm" / "build_q1w8_subject_package.py"
OUT_DIR = REPO_ROOT / ".local" / "canvas-llm" / "q1w8-audit"
PAGE_URL = "q1w8-september-7-11-2026"
WEEK_MARKER = "September 7\u201311, 2026"

ASSIGNMENT_TITLES = [
    ("Math", 26404, "SM5: Lesson 26 Homework"),
    ("Math", 26404, "SM5: Written Assessment 4"),
    ("Math", 26404, "SM5: Fact Assessment 4"),
    ("Reading/Spelling", 26442, "RM4: Lesson 30 Workbook"),
    ("Reading/Spelling", 26442, "RM4: Lesson 31 Workbook and Comprehension"),
]

REMINDER_TITLES = {
    26404: "Math Assessment Reminder - Thursday",
    26442: "Reading Test & Fluency Checkout Reminder - Wednesday",
}

FRONT_PAGES = {
    "Math": 26404,
    "Reading/Spelling": 26442,
    "Language Arts": 28171,
    "History": 28165,
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
        return {"__error__": f"HTTP {exc.code}"}
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


def _verify(base_url: str, token: str, build: Any) -> dict[str, Any]:
    r: dict[str, Any] = {}
    manifest = json.loads((OUT_DIR / "q1w8-manifest.json").read_text(encoding="utf-8"))
    page_bodies = {
        a["course"]: a["body"]
        for a in manifest["actions"]
        if a.get("object_type") == "page"
    }

    for name, cid in FRONT_PAGES.items():
        fp = _get(base_url, token, f"/api/v1/courses/{cid}/front_page")
        ok = (
            isinstance(fp, dict)
            and fp.get("url") == PAGE_URL
            and bool(fp.get("front_page"))
        )
        r[f"front_{name}"] = ok

    history_body = page_bodies.get("History") or ""
    r["history_wording"] = (
        "Medieval Islamic Kingdoms Chapter 2" in history_body
        and "E.I.C." not in history_body
        and "EIC" not in history_body
    )

    assign_ok = 0
    for _name, cid, title in ASSIGNMENT_TITLES:
        hits = [
            a
            for a in _paginate(base_url, token, f"/api/v1/courses/{cid}/assignments")
            if (a.get("name") or "").strip() == title
        ]
        if hits:
            assign_ok += 1
    r["assignments_created"] = assign_ok

    pu = _get(base_url, token, f"/api/v1/files/{build.POWER_UP_C_FILE_ID}")
    r["power_up_c"] = (
        pu.get("hidden") is False
        and pu.get("display_name") == "Power Up C.pdf"
        and pu.get("id") == build.POWER_UP_C_FILE_ID
    )

    math_ann = _paginate(
        base_url,
        token,
        f"/api/v1/courses/26404/discussion_topics",
        {"only_announcements": "true"},
    )
    math_hit = [
        a for a in math_ann if (a.get("title") or "").strip() == REMINDER_TITLES[26404]
    ]
    r["math_reminder"] = False
    if math_hit:
        full = _get(base_url, token, f"/api/v1/courses/26404/discussion_topics/{math_hit[0]['id']}")
        msg = full.get("message") or ""
        r["math_reminder"] = (
            bool(full.get("published"))
            and str(build.POWER_UP_C_FILE_ID) in msg
            and "Written Assessment 4" in msg
        )

    read_ann = _paginate(
        base_url,
        token,
        f"/api/v1/courses/26442/discussion_topics",
        {"only_announcements": "true"},
    )
    read_hit = [
        a for a in read_ann if (a.get("title") or "").strip() == REMINDER_TITLES[26442]
    ]
    r["reading_reminder"] = False
    if read_hit:
        full = _get(base_url, token, f"/api/v1/courses/26442/discussion_topics/{read_hit[0]['id']}")
        msg = full.get("message") or ""
        r["reading_reminder"] = bool(full.get("published")) and "Fluency Checkout" in msg

    weekly_ok = 0
    duplicates = 0
    for subject_key in ("math", "reading_spelling", "language_arts", "history"):
        cid = swu.SUBJECTS[subject_key]["course_id"]
        title = swu.SUBJECTS[subject_key]["title"]
        anns = _paginate(
            base_url,
            token,
            f"/api/v1/courses/{cid}/discussion_topics",
            {"only_announcements": "true"},
        )
        matches = swu.find_weekly_update(anns, title=title, week_marker=WEEK_MARKER)
        duplicates += max(0, len(matches) - 1)
        if len(matches) != 1:
            continue
        full = _get(base_url, token, f"/api/v1/courses/{cid}/discussion_topics/{matches[0]['id']}")
        msg = full.get("message") or ""
        fp = _get(base_url, token, f"/api/v1/courses/{cid}/front_page")
        live_core = swu.agenda_core((fp or {}).get("body") or "")
        draft = build.WEEKLY_UPDATE_DRAFTS[subject_key]
        if (
            draft["week_in_review"] in msg
            and draft["week_ahead"] in msg
            and swu.agenda_core(msg) == live_core
            and bool(full.get("published"))
        ):
            weekly_ok += 1
    r["weekly_updates"] = weekly_ok
    r["duplicate_weekly_updates"] = duplicates

    stale = 0
    for cid in FRONT_PAGES.values():
        fp = _get(base_url, token, f"/api/v1/courses/{cid}/front_page")
        body = (fp or {}).get("body") or ""
        stale += len(re.findall(r"\bE\.I\.C\.", body))
    r["stale_eic"] = stale
    return r


def main() -> int:
    build = _load_build()
    build.write_local_artifacts()
    launcher.set_approval("Q1W8", approved=True)

    os.environ["CANVAS_LLM_DEPLOYMENT_MODE"] = "live"
    os.environ["CANVAS_LLM_LIVE_Q1W2_APPROVED"] = "1"

    print("=== Q1W8 SUBJECT PACKAGE — GUARDED LAUNCH ===")
    rc = launcher.command_launch("Q1W8")
    if rc != 0:
        print("LAUNCH STOPPED — see blockers above.")
        return rc

    credentials.load_credentials()
    base_url = os.environ["CANVAS_BASE_URL"].strip().rstrip("/")
    token = os.environ["CANVAS_TOKEN"]

    print("\n=== Q1W8 SUBJECT PACKAGE — VERIFY (GET-only) ===")
    v = _verify(base_url, token, build)

    print("\n=== FINAL REPORT ===")
    print(f"Math front page: {'PASS' if v['front_Math'] else 'FAIL'}")
    print(f"Reading/Spelling front page: {'PASS' if v['front_Reading/Spelling'] else 'FAIL'}")
    print(f"Language Arts front page: {'PASS' if v['front_Language Arts'] else 'FAIL'}")
    print(f"History front page: {'PASS' if v['front_History'] else 'FAIL'}")
    print(f"History wording uses Medieval Islamic Kingdoms: {'PASS' if v['history_wording'] else 'FAIL'}")
    print(f"assignments created: {v['assignments_created']}/5")
    print(f"Math reminder: {'LIVE' if v['math_reminder'] else 'FAIL'}")
    print(f"Reading reminder: {'LIVE' if v['reading_reminder'] else 'FAIL'}")
    print(f"Power Up C: {'PASS' if v['power_up_c'] else 'FAIL'}")
    print(f"Weekly Updates updated: {v['weekly_updates']}/4")
    print(f"duplicates created: {v['duplicate_weekly_updates']}")

    manifest = json.loads((OUT_DIR / "q1w8-manifest.json").read_text(encoding="utf-8"))
    writes = sum(
        1
        for a in manifest["actions"]
        if a.get("action") in ("CREATE", "UPDATE")
        and a.get("object_type") != "course"
    )
    print(f"WRITES PERFORMED: {writes}")

    remaining: list[str] = []
    if v["assignments_created"] != 5:
        remaining.append("assignments")
    if not v["math_reminder"]:
        remaining.append("Math assessment reminder")
    if not v["reading_reminder"]:
        remaining.append("Reading test reminder")
    if v["weekly_updates"] != 4:
        remaining.append("Weekly Updates")
    for name in FRONT_PAGES:
        if not v[f"front_{name}"]:
            remaining.append(f"{name} front page")
    if not v["history_wording"]:
        remaining.append("History wording")
    if not v["power_up_c"]:
        remaining.append("Power Up C")

    print(f"REMAINING WRITE ACTIONS: {len(remaining)}")
    for item in remaining:
        print(f"  - {item}")
    print(f"BLOCKERS: {len(remaining)}")

    all_pass = (
        all(v[f"front_{n}"] for n in FRONT_PAGES)
        and v["history_wording"]
        and v["assignments_created"] == 5
        and v["math_reminder"]
        and v["reading_reminder"]
        and v["power_up_c"]
        and v["weekly_updates"] == 4
        and v["duplicate_weekly_updates"] == 0
        and v["stale_eic"] == 0
        and not remaining
    )
    if all_pass:
        print("Q1W8 SUBJECT PACKAGE: COMPLETE")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
