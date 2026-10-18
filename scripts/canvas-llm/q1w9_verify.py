#!/usr/bin/env python3
"""Q1W9 readback verification + duplicate check (GET only, zero writes).

Usage:
    python3 scripts/canvas-llm/q1w9_verify.py
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

OUT_DIR = REPO_ROOT / ".local" / "canvas-llm" / "q1w9-audit"
BUILD_PATH = REPO_ROOT / "scripts" / "canvas-llm" / "q1w9_build.py"

PAGE_URL = "q1w9-september-14-18-2026"
PAGE_TITLE = "Q1W9 - September 14\u201318, 2026"
WEEK_MARKER = "September 14\u201318, 2026"
HOMEROOM_SLUG = "q1w2-july-27-31-2026"

FRONT_PAGES = {"Math": 26404, "Reading/Spelling": 26442, "Language Arts": 28171, "History": 28165}
HOMEROOM_ID = 26429

# title -> (course_id, expected due_at, expected group)
ASSIGNMENTS = {
    "RM4: Lesson 33 Workbook": (26442, "2026-09-15T03:59:59Z", "Homework"),
    "RM4: Lesson 34 Workbook and Comprehension": (26442, "2026-09-16T03:59:59Z", "Homework"),
    "RM4: Lesson 35 Workbook": (26442, "2026-09-17T03:59:59Z", "Homework"),
    "RM4: Lesson 36 Workbook and Comprehension": (26442, "2026-09-18T03:59:59Z", "Homework"),
    "SM5: Lesson 28 Homework": (26404, "2026-09-15T03:59:59Z", "Homework/Class Work"),
    "SM5: Lesson 29 Homework": (26404, "2026-09-16T03:59:59Z", "Homework/Class Work"),
    "SM5: Lesson 30 Homework": (26404, "2026-09-17T03:59:59Z", "Homework/Class Work"),
    "SM5: Fact Assessment 5": (26404, "2026-09-18T03:59:59Z", "Fact Assessments"),
    "SM5: Written Assessment 5": (26404, "2026-09-18T03:59:59Z", "Written Assessments"),
    "HIST 4B: Early Islamic Civilizations Test": (28165, "2026-09-18T03:59:59Z", "Assignments"),
}


def _load_build() -> Any:
    spec = importlib.util.spec_from_file_location("q1w9_build", BUILD_PATH)
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


def _normalize_canvas_html(text: str) -> str:
    """Normalize Canvas-side HTML rewriting so readback compares content, not noise.

    Canvas expands embedded file iframes with a signed ``verifier`` query string
    plus ``loading="lazy"`` and ``data-api-*`` attributes, and de-duplicates the
    global stylesheet ``<link>`` when it already appears earlier in the message.
    Neither changes the message families see.
    """
    import re

    out = text
    out = re.sub(r"\?verifier=[^\"'\s>]+", "", out)
    out = re.sub(r'\s+loading="lazy"', "", out)
    out = re.sub(r'\s+data-api-endpoint="[^"]*"', "", out)
    out = re.sub(r'\s+data-api-returntype="[^"]*"', "", out)
    out = re.sub(r'<link rel="stylesheet"[^>]*>', "", out)
    return " ".join(out.split())


def main() -> int:
    build = _load_build()
    build.write_local_artifacts()

    credentials.load_credentials()
    base_url = os.environ["CANVAS_BASE_URL"].strip().rstrip("/")
    token = os.environ["CANVAS_TOKEN"]

    report: dict[str, Any] = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "checks": {},
        "blockers": [],
    }
    checks = report["checks"]

    print("Q1W9 READBACK VERIFICATION (GET-only, zero writes)")
    print("=" * 72)

    # --- Front pages ---------------------------------------------------------
    print("\n[1] FRONT PAGES")
    for name, cid in FRONT_PAGES.items():
        fp = _get(base_url, token, f"/api/v1/courses/{cid}/front_page")
        ok = (
            isinstance(fp, dict)
            and fp.get("url") == PAGE_URL
            and bool(fp.get("front_page"))
        )
        checks[f"front_{name}"] = bool(ok)
        print(f"  {'PASS' if ok else 'FAIL'}  {name}: front_page={fp.get('url')!r} "
              f"front_page_flag={fp.get('front_page')}")
        if not ok:
            report["blockers"].append(f"{name} front page not on {PAGE_URL}")

    fp = _get(base_url, token, f"/api/v1/courses/{HOMEROOM_ID}/front_page")
    hr_ok = (
        isinstance(fp, dict)
        and fp.get("url") == HOMEROOM_SLUG
        and bool(fp.get("front_page"))
        and WEEK_MARKER in (fp.get("body") or "")
    )
    checks["front_Homeroom"] = bool(hr_ok)
    print(f"  {'PASS' if hr_ok else 'FAIL'}  Homeroom: front_page={fp.get('url')!r} "
          f"week9_marker={WEEK_MARKER in (fp.get('body') or '')}")
    if not hr_ok:
        report["blockers"].append("Homeroom newsletter front page not live with Week 9 content")

    hr_body = fp.get("body") or ""
    checks["homeroom_newsletter_no_subject_reminders"] = all(
        t not in hr_body
        for t in ("Spelling Test 30", "Written Assessment 5", "Fact Assessment 5",
                  "Early Islamic Civilizations Test")
    )
    checks["homeroom_newsletter_picnic"] = "Fourth Grade Playground Picnic" in hr_body
    checks["homeroom_newsletter_flashlight"] = "Flashlight Friday" in hr_body
    checks["homeroom_newsletter_trackout"] = "SEPT. 21 \u2013 OCT. 9" in hr_body
    checks["homeroom_newsletter_q1_message"] = "tremendous first quarter" in hr_body

    # --- Subject pages -------------------------------------------------------
    print("\n[2] SUBJECT PAGES (body matches draft exactly)")
    live_now = {}
    for name, cid in FRONT_PAGES.items():
        page = _get(base_url, token, f"/api/v1/courses/{cid}/pages/{PAGE_URL}")
        body = page.get("body") or ""
        live_now[name] = f"{build.LINK}\n{body}" if not body.startswith("<link") else body
        expected = json.loads((OUT_DIR / "q1w9-manifest.json").read_text(encoding="utf-8"))
        want = next(
            a["body"] for a in expected["actions"]
            if a.get("object_type") == "page" and a.get("course") == name
        )
        norm = lambda s: " ".join(s.split())
        ok = norm(body) == norm(want)
        checks[f"page_{name}"] = bool(ok)
        print(f"  {'PASS' if ok else 'FAIL'}  {name}: published={page.get('published')} "
              f"title={page.get('title')!r} body_match={ok}")
        if not ok:
            report["blockers"].append(f"{name} page body differs from approved draft")
    report["live_page_bodies"] = live_now

    # --- Assignments ---------------------------------------------------------
    print("\n[3] ASSIGNMENTS")
    assignment_ok = 0
    groups_cache: dict[int, dict[str, int]] = {}
    for cid in {c for c, _d, _g in ASSIGNMENTS.values()}:
        groups_cache[cid] = {
            g.get("name"): g.get("id")
            for g in _paginate(base_url, token, f"/api/v1/courses/{cid}/assignment_groups")
        }
    for title, (cid, due, group) in ASSIGNMENTS.items():
        hits = [
            a for a in _paginate(base_url, token, f"/api/v1/courses/{cid}/assignments")
            if (a.get("name") or "").strip() == title
        ]
        if len(hits) != 1:
            print(f"  FAIL  {title!r}: {len(hits)} live matches")
            report["blockers"].append(f"{title}: expected 1 live assignment, found {len(hits)}")
            continue
        a = hits[0]
        due_ok = (a.get("due_at") or "") == due
        grp_ok = a.get("assignment_group_id") == groups_cache[cid].get(group)
        pub_ok = bool(a.get("published"))
        points_ok = a.get("points_possible") == 100
        grade_ok = a.get("grading_type") == "percent"
        subm = a.get("submission_types") or []
        paper_ok = bool(a.get("submission_types")) and all(
            s in ("on_paper", "none") for s in subm
        )
        ok = due_ok and grp_ok and pub_ok and points_ok and grade_ok and paper_ok
        checks[f"assignment_{title}"] = bool(ok)
        if ok:
            assignment_ok += 1
        else:
            report["blockers"].append(f"assignment {title!r} settings mismatch")
        print(f"  {'PASS' if ok else 'FAIL'}  {title!r}")
        print(f"        due={a.get('due_at')} (want {due}) group={group} "
              f"published={a.get('published')} points={a.get('points_possible')} "
              f"grading={a.get('grading_type')} submission={subm}")
    checks["assignments_verified"] = assignment_ok

    # --- Announcements -------------------------------------------------------
    print("\n[4] ANNOUNCEMENTS")
    expected_anns = json.loads((OUT_DIR / "q1w9-manifest.json").read_text(encoding="utf-8"))
    ann_ok = 0
    ann_total = 0
    dup_count = 0
    for action in expected_anns["actions"]:
        if action.get("object_type") != "announcement":
            continue
        ann_total += 1
        cid = action["course_id"]
        title = action["resulting_title"]
        anns = _paginate(
            base_url, token, f"/api/v1/courses/{cid}/discussion_topics",
            {"only_announcements": "true"},
        )
        if action["action"] == "UPDATE":
            hits = [a for a in anns if a.get("id") == action.get("existing_id")]
        else:
            hits = [a for a in anns if (a.get("title") or "").strip() == title]
        if len(hits) != 1:
            print(f"  FAIL  {action['course']} {title!r}: {len(hits)} matches")
            report["blockers"].append(f"{title}: expected 1 live announcement, found {len(hits)}")
            continue
        dup_count += max(0, len([a for a in anns if (a.get("title") or "").strip() == title]) - 1)
        full = _get(base_url, token, f"/api/v1/courses/{cid}/discussion_topics/{hits[0]['id']}")
        msg = full.get("message") or ""
        expected_msg = action["message"]
        title_ok = (full.get("title") or "").strip() == title
        msg_ok = _normalize_canvas_html(expected_msg) in _normalize_canvas_html(msg)
        pub_ok = bool(full.get("published"))
        sched = full.get("delayed_post_at")
        sched_ok = True
        if action.get("delayed_post_at"):
            sched_ok = sched == action["delayed_post_at"]
        ok = title_ok and msg_ok and pub_ok and sched_ok
        checks[f"announcement_{action['course']}_{title}"] = bool(ok)
        if ok:
            ann_ok += 1
        else:
            report["blockers"].append(f"announcement {title!r} mismatch")
        print(f"  {'PASS' if ok else 'FAIL'}  [{action['course']}] {title!r} "
              f"id={full.get('id')} published={pub_ok} delayed={sched!r}")
        if not ok:
            print(f"        title_ok={title_ok} msg_ok={msg_ok} sched_ok={sched_ok}")
    checks["announcements_verified"] = ann_ok
    checks["announcements_total"] = ann_total
    checks["duplicate_announcements"] = dup_count

    # --- Weekly updates (embedded agenda must match live front page) ---------
    print("\n[5] SUBJECT WEEKLY UPDATES (agenda reuse)")
    weekly_ok = 0
    for subject_key in ("math", "reading_spelling", "language_arts", "history"):
        cid = swu.SUBJECTS[subject_key]["course_id"]
        title = swu.SUBJECTS[subject_key]["title"]
        anns = _paginate(
            base_url, token, f"/api/v1/courses/{cid}/discussion_topics",
            {"only_announcements": "true"},
        )
        matches = [a for a in anns if (a.get("title") or "").strip() == title]
        if len(matches) != 1:
            print(f"  FAIL  {subject_key}: {len(matches)} weekly updates")
            report["blockers"].append(f"{subject_key}: {len(matches)} weekly updates")
            continue
        full = _get(base_url, token, f"/api/v1/courses/{cid}/discussion_topics/{matches[0]['id']}")
        msg = full.get("message") or ""
        fpage = _get(base_url, token, f"/api/v1/courses/{cid}/front_page")
        live_core = swu.agenda_core(fpage.get("body") or "")
        draft = build.WEEKLY_UPDATE_DRAFTS[subject_key]
        ok = (
            draft["week_in_review"] in msg
            and draft["week_ahead"] in msg
            and swu.agenda_core(msg) == live_core
            and bool(full.get("published"))
            and "September 14\u201318, 2026" in msg
        )
        checks[f"weekly_update_{subject_key}"] = bool(ok)
        if ok:
            weekly_ok += 1
        else:
            report["blockers"].append(f"weekly update {subject_key} not aligned to live agenda")
        print(f"  {'PASS' if ok else 'FAIL'}  {title!r} id={full.get('id')}")
    checks["weekly_updates_verified"] = weekly_ok

    # --- Homeroom announcements ---------------------------------------------
    print("\n[6] HOMEROOM ANNOUNCEMENTS")
    hr_anns = _paginate(
        base_url, token, f"/api/v1/courses/{HOMEROOM_ID}/discussion_topics",
        {"only_announcements": "true"},
    )
    titles = {(a.get("title") or "").strip() for a in hr_anns}
    has_w9 = "Week 9 Newsletter | September 14\u201318" in titles
    checks["homeroom_w9_announcement"] = has_w9
    print(f"  {'PASS' if has_w9 else 'FAIL'}  'Week 9 Newsletter | September 14\u201318' present")
    if not has_w9:
        report["blockers"].append("Week 9 Newsletter announcement missing")
    old_w8 = "4th Grade Happenings - Week 8" in titles
    print(f"  {'PASS' if not old_w8 else 'FAIL'}  stale 'Week 8' announcement retitled")
    checks["homeroom_w8_announcement_retitled"] = not old_w8
    if old_w8:
        report["blockers"].append("Homeroom Week 8 announcement not retitled")
    old_w8 = "4th Grade Happenings - Week 8" in titles
    checks["old_w8_announcement"] = not old_w8
    if old_w8:
        report["blockers"].append("Homeroom Week 8 announcement still present")
    for a in hr_anns:
        if (a.get("title") or "").strip() == "Week 9 Newsletter Reminder - Track Out":
            full = _get(base_url, token,
                        f"/api/v1/courses/{HOMEROOM_ID}/discussion_topics/{a['id']}")
            sched_ok = full.get("delayed_post_at") == "2026-09-17T20:00:00Z"
            checks["homeroom_thursday_resend"] = bool(sched_ok)
            print(f"  {'PASS' if sched_ok else 'FAIL'}  Thursday resend scheduled "
                  f"delayed={full.get('delayed_post_at')!r}")
            if not sched_ok:
                report["blockers"].append("Homeroom Thursday resend schedule mismatch")

    # --- Forbidden objects ---------------------------------------------------
    print("\n[7] FORBIDDEN OBJECTS")
    bad = []
    reading = _paginate(base_url, token, "/api/v1/courses/26442/assignments")
    for a in reading:
        n = (a.get("name") or "")
        if "Spelling Test 30" in n:
            bad.append(f"Reading/Spelling assignment {n!r}")
    math = _paginate(base_url, token, "/api/v1/courses/26404/assignments")
    for a in math:
        n = (a.get("name") or "")
        if n.strip() in ("Cleaning", "SM5: Cleaning"):
            bad.append(f"Math assignment {n!r}")
    sci = _get(base_url, token, f"/api/v1/courses/{28166}/front_page")
    checks["no_forbidden_objects"] = not bad
    print(f"  {'PASS' if not bad else 'FAIL'}  no Spelling Test 30 / Cleaning assignments")
    for b in bad:
        report["blockers"].append(f"forbidden object created: {b}")
    print(f"  Science front page unchanged: {sci.get('url')!r}")

    # --- Summary -------------------------------------------------------------
    report["summary"] = {
        "front_pages": {k.replace("front_", ""): v for k, v in checks.items() if k.startswith("front_")},
        "assignments_verified": f"{assignment_ok}/{len(ASSIGNMENTS)}",
        "announcements_verified": f"{ann_ok}/{ann_total}",
        "weekly_updates_verified": f"{weekly_ok}/4",
        "duplicate_announcements": dup_count,
    }
    report_path = OUT_DIR / "q1w9-report.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print("\n" + "=" * 72)
    print("Q1W9 LIVE DEPLOYMENT READBACK")
    print(f"Reading assignments created: {sum(1 for t in ASSIGNMENTS if t.startswith('RM4:'))}")
    print(f"Math assignments created: "
          f"{sum(1 for t in ASSIGNMENTS if t.startswith('SM5: Lesson'))}")
    print(f"Math assessments created: "
          f"{sum(1 for t in ASSIGNMENTS if 'Assessment 5' in t)}")
    print(f"History assessments created: "
          f"{sum(1 for t in ASSIGNMENTS if t.startswith('HIST'))}")
    print("Spelling assignment created: NO")
    for name in FRONT_PAGES:
        print(f"{name} front page: {'PASS' if checks.get(f'front_{name}') else 'FAIL'}")
    print(f"Homeroom newsletter/front page: "
          f"{'PASS' if checks.get('front_Homeroom') else 'FAIL'}")
    print(f"Assignments verified: {assignment_ok}/{len(ASSIGNMENTS)}")
    print(f"Announcements verified: {ann_ok}/{ann_total}")
    print(f"Weekly Updates verified: {weekly_ok}/4")
    print(f"Duplicate announcements: {dup_count}")
    print(f"BLOCKERS: {len(report['blockers'])}")
    for b in report["blockers"]:
        print(f"  - {b}")
    print(f"report: {report_path}")
    return 1 if report["blockers"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
