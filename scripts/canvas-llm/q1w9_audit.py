#!/usr/bin/env python3
"""Q1W9 live read-only audit + duplicate check (GET only, zero writes).

Usage:
    python3 scripts/canvas-llm/q1w9_audit.py

Fresh-reads the live pacing source (4A - Reagan tab), builds the local Q1W9
drafts, then GET-probes live Canvas for front pages, planned page slugs,
assignment groups, planned assignment/announcement titles, the existing subject
Weekly Update announcements, and the rolling Homeroom newsletter.

Writes only local artifacts under ``.local/canvas-llm/q1w9-audit/``.
"""
from __future__ import annotations

import csv
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
PACING_CSV = OUT_DIR / "pacing-4A-reagan-fresh.csv"

SPREADSHEET_ID = "1I-CNb_ZPnOozY2wSMNAWF3bzuRZWDdZt9yoSBKtLWD4"
SHEET_NAME = "4A - Reagan"
WEEK_DATES = ["9/14/26", "9/15/26", "9/16/26", "9/17/26", "9/18/26"]

SUBJECTS: list[tuple[str, str, int]] = [
    ("math", "Math", 26404),
    ("reading_spelling", "Reading/Spelling", 26442),
    ("language_arts", "Language Arts", 28171),
    ("history", "History", 28165),
]
HOMEROOM_NAME = "Homeroom"
HOMEROOM_COURSE_ID = 26429
SCIENCE = ("Science", 28166)

PAGE_URL = "q1w9-september-14-18-2026"
WEEK_MARKER = "September 14\u201318, 2026"
HOMEROOM_SLUG = "q1w2-july-27-31-2026"


def _pacing_url() -> str:
    return (
        "https://docs.google.com/spreadsheets/d/"
        f"{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet={urllib.parse.quote(SHEET_NAME)}"
    )


def fetch_pacing() -> list[list[str]]:
    req = urllib.request.Request(_pacing_url(), headers={"Accept": "text/csv"})
    with urllib.request.urlopen(req, timeout=60) as response:
        text = response.read().decode("utf-8")
    PACING_CSV.write_text(text, encoding="utf-8")
    return list(csv.reader(text.splitlines()))


def verify_pacing(rows: list[list[str]]) -> dict[str, Any]:
    header = None
    for row in rows:
        if WEEK_DATES[0] in row:
            header = row
            break
    if header is None:
        return {"ok": False, "reason": "week dates 9/14/26-9/18/26 not found"}
    col = header.index(WEEK_DATES[0])
    dates = header[col : col + 5]
    days = None
    hi = rows.index(header)
    if hi + 1 < len(rows):
        days = rows[hi + 1][col : col + 5]
    subjects: dict[str, list[str]] = {}
    for row in rows[hi + 2 : hi + 10]:
        if not row or not row[0]:
            continue
        subjects[row[0].strip()] = [c.strip() for c in row[col : col + 5]]
    expected = {
        "Saxon Math": ["L28", "L29", "L30", "WA5/ FA5*", "Cleaning"],
        "Reading Mastery": ["33", "34", "35", "36", "Rotations"],
        "Spelling": ["Review", "Practice Test", "30 Test", "review", "Rotations"],
        "Shurley English": ["HG11", "HG12", "HG13", "HG14", "Friday Folders"],
        "History": [
            "E.I.C. CH5",
            "E.I.C. CH5",
            "Review",
            "Test",
            "Parent Picnic/Cleaning Room",
        ],
        "Science": ["", "", "", "", "X"],
    }
    matched: dict[str, bool] = {}
    for name, exp in expected.items():
        got = subjects.get(name)
        matched[name] = got == exp
    return {
        "ok": all(matched.values()),
        "dates": dates,
        "weekdays": days,
        "subjects": subjects,
        "matches_canonical": matched,
        "source_url": _pacing_url(),
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
        return {"__error__": f"HTTP {exc.code}: {exc.reason}"}
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


def main() -> int:
    build = _load_build()
    build.write_local_artifacts()

    print("Q1W9 LIVE AUDIT (read-only)")
    print("=" * 72)

    print("\n[1] FRESH LIVE PACING READ (4A - Reagan)")
    rows = fetch_pacing()
    pacing = verify_pacing(rows)
    print(f"  source: {pacing.get('source_url')}")
    print(f"  dates : {pacing.get('dates')}")
    print(f"  days  : {pacing.get('weekdays')}")
    for name, ok in (pacing.get("matches_canonical") or {}).items():
        print(f"  {'PASS' if ok else 'FAIL'}  {name}: {pacing['subjects'].get(name)}")
    if not pacing["ok"]:
        print("\nBLOCKER: fresh pacing does not match canonical pacing.")
        return 1
    print("  PASS: live pacing matches canonical pacing exactly.")

    credentials.load_credentials()
    base_url = os.environ["CANVAS_BASE_URL"].strip().rstrip("/")
    token = os.environ["CANVAS_TOKEN"]

    me = _get(base_url, token, "/api/v1/users/self")
    print(f"\n  user: id={me.get('id')} name={me.get('name')!r}")

    manifest = json.loads((OUT_DIR / "q1w9-manifest.json").read_text(encoding="utf-8"))
    bodies = {
        a["course"]: a.get("body") or ""
        for a in manifest["actions"]
        if a.get("object_type") == "page"
    }

    findings: dict[str, Any] = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "pacing": pacing,
        "blockers": [],
        "warnings": [],
        "duplicate_assignments": [],
        "duplicate_announcements": [],
        "front_page_actions": [],
        "page_actions": [],
        "groups_missing": [],
        "weekly_update_status": {},
    }

    print("\n[2] POWER UP A RESOURCE VERIFY (Math 26404)")
    pu = _get(base_url, token, f"/api/v1/files/{build.POWER_UP_A_FILE_ID}")
    pu_ok = (
        isinstance(pu, dict)
        and pu.get("display_name") == "Power Up A.pdf"
        and pu.get("hidden") is False
    )
    print(f"  {'PASS' if pu_ok else 'FAIL'} id={build.POWER_UP_A_FILE_ID} "
          f"display_name={pu.get('display_name')!r} hidden={pu.get('hidden')}")
    findings["power_up_a_verified"] = pu_ok
    if not pu_ok:
        findings["blockers"].append("Power Up A.pdf could not be verified in Math 26404")

    print("\n[3] SUBJECT AUDIT")
    for subject_key, name, cid in SUBJECTS:
        print(f"\n  --- {name} ({cid}) ---")
        course = _get(base_url, token, f"/api/v1/courses/{cid}")
        print(f"  course: {course.get('name')!r}")

        fp = _get(base_url, token, f"/api/v1/courses/{cid}/front_page")
        fp_url = fp.get("url") if isinstance(fp, dict) else None
        print(f"  front_page: {fp_url!r}")

        page = _get(base_url, token, f"/api/v1/courses/{cid}/pages/{PAGE_URL}")
        exists = isinstance(page, dict) and not page.get("__error__")
        if exists:
            print(f"  Q1W9 page EXISTS published={page.get('published')} "
                  f"url={page.get('url')!r}")
            (OUT_DIR / f"live-{subject_key}-q1w9-backup.html").write_text(
                page.get("body") or "", encoding="utf-8"
            )
            findings["page_actions"].append(f"{name}: UPDATE existing {PAGE_URL}")
        else:
            print(f"  Q1W9 page absent -> CREATE {PAGE_URL!r}")
            findings["page_actions"].append(f"{name}: CREATE {PAGE_URL}")
        findings["front_page_actions"].append(
            f"{name}: SET_AND_VERIFY front page -> {PAGE_URL}"
        )

        groups = _paginate(base_url, token, f"/api/v1/courses/{cid}/assignment_groups")
        gmap = {g.get("name") for g in groups}
        print(f"  assignment groups: {sorted(gmap)}")
        for title, _grp in [
            (a["resulting_title"], a["assignment_group"])
            for a in manifest["actions"]
            if a.get("object_type") == "assignment" and a["course_id"] == cid
        ]:
            pass
        for grp in sorted(
            {
                a["assignment_group"]
                for a in manifest["actions"]
                if a.get("object_type") == "assignment" and a["course_id"] == cid
            }
        ):
            if grp not in gmap:
                findings["groups_missing"].append(f"{name}: assignment group {grp!r} MISSING")
                print(f"  FAIL: missing assignment group {grp!r}")
            else:
                print(f"  PASS: group {grp!r} present")

        live_assignments = _paginate(base_url, token, f"/api/v1/courses/{cid}/assignments")
        amap = {(a.get("name") or "").strip(): a.get("id") for a in live_assignments}
        for action in manifest["actions"]:
            if action.get("object_type") != "assignment" or action["course_id"] != cid:
                continue
            t = action["resulting_title"]
            if t in amap:
                findings["duplicate_assignments"].append(f"{name}: {t!r} id={amap[t]}")
                print(f"  DUPLICATE assignment: {t!r} id={amap[t]}")
            else:
                print(f"  PLANNED CREATE: {t!r} -> {action['assignment_group']!r}")

        anns = _paginate(
            base_url,
            token,
            f"/api/v1/courses/{cid}/discussion_topics",
            {"only_announcements": "true"},
        )
        amap2 = {(a.get("title") or "").strip(): a.get("id") for a in anns}
        for action in manifest["actions"]:
            if action.get("object_type") != "announcement" or action["course_id"] != cid:
                continue
            t = action["resulting_title"]
            if action["action"] == "UPDATE":
                if t in amap2:
                    print(f"  existing reminder to UPDATE in place: {t!r} id={amap2[t]}")
                else:
                    findings["blockers"].append(f"{name}: reminder {t!r} not found to update")
                    print(f"  FAIL: reminder {t!r} not found")
                continue
            if t in amap2:
                findings["duplicate_announcements"].append(f"{name}: {t!r} id={amap2[t]}")
                print(f"  DUPLICATE announcement: {t!r} id={amap2[t]}")
            else:
                print(f"  PLANNED CREATE announcement: {t!r}")

        # Weekly update drift check
        wu_title = swu.SUBJECTS[subject_key]["title"]
        wu_hits = [a for a in anns if (a.get("title") or "").strip() == wu_title]
        if wu_hits:
            live = wu_hits[0]
            live_detail = _get(base_url, token, f"/api/v1/courses/{cid}/discussion_topics/{live['id']}")
            expected_core = swu.agenda_core(bodies[name])
            status, _mid = swu.classify_duplicate(
                [{"id": live["id"], "title": live.get("title"),
                  "message": (live_detail or {}).get("message") or ""}],
                title=wu_title,
                week_marker=WEEK_MARKER,
                expected_core=expected_core,
            )
            findings["weekly_update_status"][subject_key] = status
            print(f"  weekly update duplicate state: {status}")
        else:
            findings["weekly_update_status"][subject_key] = "MISSING"

    print(f"\n[4] {SCIENCE[0]} ({SCIENCE[1]}) — LEAVE untouched (inactive quarter)")

    print("\n[5] HOMEROOM (26429) rolling newsletter")
    course = _get(base_url, token, f"/api/v1/courses/{HOMEROOM_COURSE_ID}")
    print(f"  course: {course.get('name')!r}")
    fp = _get(base_url, token, f"/api/v1/courses/{HOMEROOM_COURSE_ID}/front_page")
    fp_url = fp.get("url") if isinstance(fp, dict) else None
    fp_body = fp.get("body") or "" if isinstance(fp, dict) else ""
    print(f"  front_page: {fp_url!r} (body {len(fp_body)} chars)")
    (OUT_DIR / "q1w9-homeroom-live-front.html").write_text(fp_body, encoding="utf-8")
    if fp_url != HOMEROOM_SLUG:
        findings["warnings"].append(
            f"Homeroom front page is {fp_url!r}, expected rolling slug {HOMEROOM_SLUG!r}"
        )
        print(f"  WARN: expected rolling slug {HOMEROOM_SLUG!r}")

    backup_dir = REPO_ROOT / ".local" / "canvas-llm" / "backups" / "q1w9"
    backup_dir.mkdir(parents=True, exist_ok=True)
    (backup_dir / f"homeroom-{HOMEROOM_SLUG}-before.html").write_text(fp_body, encoding="utf-8")
    print(f"  backed up live newsletter -> {backup_dir.name}/homeroom-{HOMEROOM_SLUG}-before.html")

    hr_anns = _paginate(
        base_url,
        token,
        f"/api/v1/courses/{HOMEROOM_COURSE_ID}/discussion_topics",
        {"only_announcements": "true"},
    )
    hr_titles = {(a.get("title") or "").strip() for a in hr_anns}
    for action in manifest["actions"]:
        if action.get("object_type") != "announcement" or action["course_id"] != 26429:
            continue
        t = action["resulting_title"]
        if action["action"] == "UPDATE" and t == action.get("existing"):
            print(f"  EXISTING announcement to UPDATE in place: {t!r} "
                  f"id={action.get('existing_id')} -> {action['resulting_title']!r}")
        elif t in hr_titles:
            findings["duplicate_announcements"].append(f"Homeroom: {t!r}")
            print(f"  DUPLICATE announcement: {t!r}")
        else:
            print(f"  PLANNED CREATE announcement: {t!r} "
                  f"@ {action.get('delayed_post_at') or 'immediate'}")

    print("\n[6] CROSS-COURSE DUPLICATE SWEEP")
    for action in manifest["actions"]:
        if action.get("object_type") != "announcement":
            continue
        t = action["resulting_title"]
        hits = []
        for _sk, name, cid in SUBJECTS + [("homeroom", HOMEROOM_NAME, HOMEROOM_COURSE_ID)]:
            anns = _paginate(
                base_url, token, f"/api/v1/courses/{cid}/discussion_topics",
                {"only_announcements": "true"},
            )
            for a in anns:
                if (a.get("title") or "").strip() == t:
                    hits.append(f"{name}#{a.get('id')}")
        if hits and not any(h.startswith(action["course"]) for h in hits):
            findings["warnings"].append(f"cross-course title collision {t!r}: {hits}")

    # Local artifact sanity
    checks = json.loads((OUT_DIR / "q1w9-package-checks.json").read_text(encoding="utf-8"))
    print("\n[7] LOCAL DRAFT CHECKS")
    for k, v in checks["newsletter_checks"].items():
        print(f"  {'PASS' if v else 'FAIL'}  newsletter.{k}")
    if not all(checks["newsletter_checks"].values()):
        findings["blockers"].append("newsletter draft checks failed")

    report_path = OUT_DIR / "q1w9-preflight-report.json"
    report_path.write_text(
        json.dumps(findings, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print("\n" + "=" * 72)
    print(f"WRITES PERFORMED: 0")
    print(f"BLOCKERS: {len(findings['blockers'])}")
    for b in findings["blockers"]:
        print(f"  - {b}")
    print(f"WARNINGS: {len(findings['warnings'])}")
    for w in findings["warnings"]:
        print(f"  - {w}")
    print(f"duplicate assignments : {len(findings['duplicate_assignments'])}")
    print(f"duplicate announcements: {len(findings['duplicate_announcements'])}")
    print(f"report: {report_path}")
    return 1 if findings["blockers"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
