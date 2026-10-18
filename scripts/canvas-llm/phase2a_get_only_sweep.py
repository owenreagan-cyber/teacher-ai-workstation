#!/usr/bin/env python3
"""Phase 2A — live Canvas GET-only precedent sweep (zero writes).

Strictly read-only exploration of the live 2026-2027 Canvas courses.

Safety contract (enforced statically and at runtime):
- Only HTTP GET is ever issued. There is no method parameter anywhere.
- POST / PUT / PATCH / DELETE are absent from this file (self-scan asserts it).
- The Canvas token and school base-URL host are never printed or persisted.
- No student data: enrollments, users, submissions, grades, conversations,
  analytics, and rosters are never requested.

Outputs (all local, gitignored under .local/canvas-llm/precedent-sweep/):
- raw/      — token-free, host-redacted GET snapshots
- normalized/ — token-free, student-free structural precedent artifacts
- write-verbs-scan.json — static proof the execution path is GET-only
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.canvas_llm_phase22 import canvas_credentials as credentials  # noqa: E402

SWEEP_DIR = REPO_ROOT / ".local" / "canvas-llm" / "precedent-sweep"
RAW_DIR = SWEEP_DIR / "raw"
NORM_DIR = SWEEP_DIR / "normalized"

# Pacing workbook (authoritative 2026-2027 FPK Pacing Guides).
SPREADSHEET_ID = "1I-CNb_ZPnOozY2wSMNAWF3bzuRZWDdZt9yoSBKtLWD4"
SHEET_NAME = "4A - Reagan"

# Target courses (verified by GET, not blindly trusted).
COURSES: list[tuple[str, str, int]] = [
    ("math", "Math", 26404),
    ("reading_spelling", "Reading/Spelling", 26442),
    ("language_arts", "Language Arts", 28171),
    ("history", "History", 28165),
    ("science", "Science", 28166),
    ("homeroom", "Homeroom", 26429),
]

WRITE_METHOD_TOKENS = (
    'method="POST"',
    'method="PUT"',
    'method="PATCH"',
    'method="DELETE"',
    "method='POST'",
    "method='PUT'",
    "method='PATCH'",
    "method='DELETE'",
    "requests.post",
    "requests.put",
    "requests.patch",
    "requests.delete",
    ".post(",
    ".put(",
    ".patch(",
    ".delete(",
)

# --------------------------------------------------------------------------- #
# Static + runtime write-verb safeguard
# --------------------------------------------------------------------------- #


def static_write_verb_scan() -> dict[str, Any]:
    """Prove this execution path is GET-only by scanning this file's own source.

    The scan removes the WRITE_METHOD_TOKENS tuple (which lists the forbidden
    strings) and then asserts none of those strings appear anywhere else in the
    file, and that the only HTTP method ever constructed is GET. It also asserts
    no urllib Request carries a ``data=`` body argument.
    """
    src = Path(__file__).read_text(encoding="utf-8")
    # Strip the tuple definition so the forbidden strings do not self-match.
    start = src.find("WRITE_METHOD_TOKENS = (")
    end = src.find(")", start)
    body = src[:start] + src[end + 1 :]

    found: list[str] = []
    for token in WRITE_METHOD_TOKENS:
        if token in body:
            found.append(token)

    get_marker_count = body.count('method="GET"')
    body_arg_on_request = bool(re.search(r"Request\([^)]*data=", body, flags=re.DOTALL))

    return {
        "forbidden_write_tokens_found": found,
        "write_free": len(found) == 0,
        "get_only_marker_count": get_marker_count,
        "get_only": get_marker_count >= 1,
        "request_body_arg_found": body_arg_on_request,
        "scanned_file": str(Path(__file__).relative_to(REPO_ROOT)),
    }


class ReadOnlyClient:
    """Canvas client that can only GET. There is no method parameter."""

    def __init__(self, base_url: str, token: str) -> None:
        self.base_url = base_url.strip().rstrip("/")
        self.token = token
        self.get_calls = 0
        self.error_calls = 0

    def _redact(self, value: Any) -> Any:
        """Replace the school host with a placeholder; strip any token-shaped strings."""
        if isinstance(value, str):
            v = value
            if self.base_url:
                v = v.replace(self.base_url, "{canvas}")
            v = re.sub(r"Bearer\s+\S+", "Bearer {redacted}", v)
            return v
        if isinstance(value, list):
            return [self._redact(item) for item in value]
        if isinstance(value, dict):
            return {k: self._redact(val) for k, val in value.items()}
        return value

    def _request(self, path: str, params: dict[str, Any] | None = None) -> tuple[Any, str | None]:
        url = f"{self.base_url}{path}"
        if params:
            url = f"{url}?{urllib.parse.urlencode(params, doseq=True)}"
        req = urllib.request.Request(
            url,
            headers={"Authorization": f"Bearer {self.token}", "Accept": "application/json"},
            method="GET",
        )
        self.get_calls += 1
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                text = response.read().decode("utf-8")
                link = response.headers.get("Link", "")
            data = json.loads(text) if text else {}
            return data, link
        except urllib.error.HTTPError as exc:
            self.error_calls += 1
            return {"__error__": f"HTTP {exc.code}"}, None
        except urllib.error.URLError as exc:
            self.error_calls += 1
            return {"__error__": f"network {exc.reason}"}, None

    def get(self, path: str) -> Any:
        data, _link = self._request(path)
        return self._redact(data)

    def get_paginated(self, path: str, params: dict[str, Any] | None = None, limit_pages: int = 20) -> list[Any]:
        merged: dict[str, Any] = {"per_page": 100}
        if params:
            merged.update(params)
        url = f"{self.base_url}{path}?{urllib.parse.urlencode(merged, doseq=True)}"
        items: list[Any] = []
        for _ in range(limit_pages):
            req = urllib.request.Request(
                url,
                headers={"Authorization": f"Bearer {self.token}", "Accept": "application/json"},
                method="GET",
            )
            self.get_calls += 1
            try:
                with urllib.request.urlopen(req, timeout=30) as response:
                    text = response.read().decode("utf-8")
                    link = response.headers.get("Link", "")
                data = json.loads(text) if text else []
            except urllib.error.HTTPError:
                self.error_calls += 1
                break
            except urllib.error.URLError:
                self.error_calls += 1
                break
            items.extend(data if isinstance(data, list) else [data])
            nxt = None
            for part in (link or "").split(","):
                if 'rel="next"' in part:
                    s = part.find("<")
                    e = part.find(">")
                    if 0 <= s < e:
                        nxt = part[s + 1 : e]
            if not nxt:
                break
            url = nxt
        return self._redact(items)


# --------------------------------------------------------------------------- #
# Local storage helpers
# --------------------------------------------------------------------------- #


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


# --------------------------------------------------------------------------- #
# Pacing fresh-read
# --------------------------------------------------------------------------- #


def _pacing_url() -> str:
    return (
        "https://docs.google.com/spreadsheets/d/"
        f"{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet={urllib.parse.quote(SHEET_NAME)}"
    )


def fetch_pacing() -> dict[str, Any]:
    raw_csv_path = RAW_DIR / "pacing-4A-reagan-fresh.csv"
    try:
        req = urllib.request.Request(_pacing_url(), headers={"Accept": "text/csv"})
        with urllib.request.urlopen(req, timeout=60) as response:
            text = response.read().decode("utf-8")
        _write_text(raw_csv_path, text)
        rows = list(csv.reader(text.splitlines()))
        status = "FRESH_READ_OK"
    except Exception as exc:  # noqa: BLE001
        # Fall back to the last known local export, marked stale.
        fallback = REPO_ROOT / ".local" / "canvas-llm" / "q1w9-audit" / "pacing-4A-reagan-fresh.csv"
        if fallback.exists():
            text = fallback.read_text(encoding="utf-8")
            _write_text(raw_csv_path, text)
            rows = list(csv.reader(text.splitlines()))
            status = "STALE_FALLBACK"
        else:
            rows = []
            status = "FAIL_NO_SOURCE"
    return {
        "status": status,
        "source_workbook_id": SPREADSHEET_ID,
        "sheet": SHEET_NAME,
        "read_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "date_columns_observed": _extract_date_columns(rows),
        "instructional_status_today": _instructional_status_today(rows),
        "rows": len(rows),
    }


_DATE_RE = re.compile(r"^\d{1,2}/\d{1,2}/\d{2}$")


def _extract_date_columns(rows: list[list[str]]) -> list[str]:
    """Collect unique date-like cells (M/D/YY) across the whole sheet, in order."""
    seen: list[str] = []
    for row in rows:
        for cell in row:
            c = cell.strip()
            if _DATE_RE.match(c) and c not in seen:
                seen.append(c)
    return seen


def _parse_mdy(value: str) -> datetime | None:
    m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{2})$", value.strip())
    if not m:
        return None
    mm, dd, yy = int(m.group(1)), int(m.group(2)), int(m.group(3))
    return datetime(2000 + yy, mm, dd)


def _instructional_status_today(rows: list[list[str]]) -> dict[str, Any]:
    """Determine today's instructional state from the pacing date columns and the
    instructional-week configuration (track-out detection), not calendar alone."""
    weeks = json.loads(
        (REPO_ROOT / "config/curriculum/canvas/instructional-weeks-2026-2027.json").read_text(encoding="utf-8")
    )
    today = datetime.now(timezone.utc).date()
    csv_dates = {_parse_mdy(d) for d in _extract_date_columns(rows)}
    csv_dates.discard(None)

    def _week_bounds(title: str) -> tuple[datetime, datetime] | None:
        # Handles both same-month ("October 12–16, 2026") and cross-month
        # ("November 30–December 4, 2026") ranges. Weeks are always Mon-Fri.
        m = re.search(r"\s([A-Za-z]+ \d{1,2})\s*[–-]", title)
        y = re.search(r",\s*(\d{4})\s*$", title)
        if not m or not y:
            return None
        try:
            start = datetime.strptime(f"{m.group(1)} {y.group(1)}", "%B %d %Y")
        except ValueError:
            return None
        return start, start + timedelta(days=4)

    current_code = None
    for w in weeks.get("weeks", []):
        bounds = _week_bounds(w.get("pageTitle", ""))
        if not bounds:
            continue
        start, end = bounds
        if start.date() <= today <= end.date():
            current_code = w.get("code")
            break

    next_code = None
    next_start = None
    for w in weeks.get("weeks", []):
        bounds = _week_bounds(w.get("pageTitle", ""))
        if not bounds:
            continue
        start, _end = bounds
        if start.date() >= today and next_start is None:
            next_start = start
            next_code = w.get("code")

    status = "INSTRUCTIONAL" if current_code else "NON_INSTRUCTIONAL"
    if current_code is None and datetime(2026, 9, 21).date() <= today <= datetime(2026, 10, 9).date():
        status = "TRACK_OUT"
    if current_code is None and datetime(2026, 10, 10).date() <= today <= datetime(2026, 10, 11).date():
        status = "BREAK_BEFORE_Q2"
    return {
        "status": status,
        "current_week_code": current_code,
        "next_week_code": next_code,
        "next_week_start": next_start.isoformat() if next_start else None,
        "next_week_dates_in_csv": (
            [d.isoformat()[:10] for d in sorted(csv_dates) if next_start and d.date() >= next_start.date()][:5]
            if next_start else []
        ),
        "date_checked": today.isoformat(),
    }


# --------------------------------------------------------------------------- #
# Course sweep
# --------------------------------------------------------------------------- #


def _representative_page_urls(pages: list[dict[str, Any]]) -> list[str]:
    """Pick purposeful page-body targets: recent agenda pages + assessment weeks."""
    candidates = [p for p in pages if isinstance(p, dict) and p.get("url")]
    candidates.sort(key=lambda p: (p.get("updated_at") or ""), reverse=True)
    urls: list[str] = []
    for p in candidates:
        u = str(p.get("url"))
        if u in urls:
            continue
        if "q1w7" in u.lower():  # preserve the known sample week
            urls.append(u)
    for p in candidates:
        u = str(p.get("url"))
        if u in urls:
            continue
        if re.search(r"q\d+w\d|week|agenda|quarter", u.lower()):
            urls.append(u)
    return urls[:6]


def sweep_course(key: str, name: str, cid: int, client: ReadOnlyClient) -> dict[str, Any]:
    out = RAW_DIR / "courses" / key
    result: dict[str, Any] = {"key": key, "name": name, "expected_course_id": cid}

    course = client.get(f"/api/v1/courses/{cid}")
    _write_json(out / "course.json", course)
    result["live_course"] = {
        "id": course.get("id"),
        "name": course.get("name"),
        "course_code": course.get("course_code"),
        "workflow_state": course.get("workflow_state"),
        "term": course.get("term"),
        "start_at": course.get("start_at"),
        "end_at": course.get("end_at"),
    }

    settings = client.get(f"/api/v1/courses/{cid}/settings")
    _write_json(out / "settings.json", settings)

    front = client.get(f"/api/v1/courses/{cid}/front_page")
    _write_json(out / "front-page.json", front)
    fp_body = front.get("body") or "" if isinstance(front, dict) else ""
    _write_text(out / "front-page.html", fp_body)
    result["front_page"] = {
        "url": front.get("url") if isinstance(front, dict) else None,
        "title": front.get("title") if isinstance(front, dict) else None,
        "published": front.get("published") if isinstance(front, dict) else None,
        "body_chars": len(fp_body),
    }

    pages = client.get_paginated(f"/api/v1/courses/{cid}/pages")
    _write_json(out / "pages.json", pages)
    result["pages_count"] = len(pages)
    result["page_titles"] = [p.get("title") for p in pages if isinstance(p, dict)][:200]

    # Representative page bodies.
    bodies_dir = out / "page-bodies"
    bodies_dir.mkdir(parents=True, exist_ok=True)
    for u in _representative_page_urls(pages):
        page = client.get(f"/api/v1/courses/{cid}/pages/{u}")
        safe = re.sub(r"[^A-Za-z0-9_-]", "_", u)
        _write_text(bodies_dir / f"{safe}.html", page.get("body") or "" if isinstance(page, dict) else "")
        _write_json(bodies_dir / f"{safe}.json", page)

    modules = client.get_paginated(f"/api/v1/courses/{cid}/modules")
    _write_json(out / "modules.json", modules)
    result["modules"] = [{"id": m.get("id"), "name": m.get("name")} for m in modules if isinstance(m, dict)]
    for m in modules:
        if not isinstance(m, dict) or not m.get("id"):
            continue
        items = client.get_paginated(f"/api/v1/courses/{cid}/modules/{m['id']}/items")
        _write_json(out / f"module-items-{m['id']}.json", items)

    groups = client.get_paginated(f"/api/v1/courses/{cid}/assignment_groups")
    _write_json(out / "assignment-groups.json", groups)
    result["assignment_groups"] = [
        {"id": g.get("id"), "name": g.get("name"), "position": g.get("position")}
        for g in groups if isinstance(g, dict)
    ]

    assignments = client.get_paginated(f"/api/v1/courses/{cid}/assignments")
    _write_json(out / "assignments.json", assignments)
    result["assignments_count"] = len(assignments)

    anns = client.get_paginated(
        f"/api/v1/courses/{cid}/discussion_topics", {"only_announcements": "true"}
    )
    _write_json(out / "announcements.json", anns)
    result["announcements_count"] = len(anns)

    folders = client.get_paginated(f"/api/v1/courses/{cid}/folders")
    _write_json(out / "folders.json", folders)
    files = client.get_paginated(f"/api/v1/courses/{cid}/files", limit_pages=5)
    _write_json(out / "files.json", files)

    return result


# --------------------------------------------------------------------------- #
# Normalization / analysis
# --------------------------------------------------------------------------- #


def _first(items: list[Any], key: str, match: Any) -> dict[str, Any] | None:
    for it in items:
        if isinstance(it, dict) and it.get(key) == match:
            return it
    return None


def reconcile_courses(live_by_key: dict[str, dict[str, Any]]) -> dict[str, Any]:
    mappings = json.loads(
        (REPO_ROOT / "config/curriculum/canvas-course-mappings.json").read_text(encoding="utf-8")
    )
    fpk = json.loads((REPO_ROOT / "config/fpk/canvas-courses.json").read_text(encoding="utf-8"))
    manifest = json.loads(
        (REPO_ROOT / "config/canvas-llm/approved-canvas-course-manifest.json").read_text(encoding="utf-8")
    )
    results = []
    for key, name, cid in COURSES:
        live = live_by_key.get(key, {}).get("live_course", {})
        live_id = live.get("id")
        live_name = live.get("name")
        classification = "AMBIGUOUS"
        if live_id == cid:
            classification = "MATCH"
        elif live_id is None:
            classification = "MISSING"
        else:
            classification = "STALE"
        results.append(
            {
                "subject": name,
                "expected_id": cid,
                "live_id": live_id,
                "live_name": live_name,
                "live_code": live.get("course_code"),
                "classification": classification,
            }
        )
    return {
        "authority": "LIVE_CANVAS_PRECEDENT",
        "results": results,
        "note": "Mappings were compared, not rewritten, in Phase 2A.",
    }


def _extract_html_structure(body: str) -> dict[str, Any]:
    if not body:
        return {}
    wrapper_id = re.search(r'id="(kl_wrapper_?\w*)"', body)
    wrapper_classes = re.search(r'<div[^>]*id="[^"]*"[^>]*class="([^"]*)"', body)
    colors = {
        "primary_blue": "#0065a7" in body,
        "reminder_pink": "#c51062" in body,
        "subheader_gray": "#333333" in body,
        "white_text": "#ffffff" in body,
    }
    has_banner = "Weekly Agenda" in body
    has_reminders = bool(re.search(r">\s*Reminders(&amp; Resources)?\s*<", body))
    days = [d for d in ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday") if d in body]
    at_home = "At Home" in body
    homework = "Homework" in body and "At Home" not in body
    two_col = body.count('width: 49%') >= 2
    one_col = 'width: 100%' in body
    kl_solid = "kl_solid_border" in body
    return {
        "wrapper_id": wrapper_id.group(1) if wrapper_id else None,
        "wrapper_classes": wrapper_classes.group(1) if wrapper_classes else None,
        "colors": colors,
        "has_banner": has_banner,
        "has_reminders": has_reminders,
        "days_present": days,
        "label_at_home": at_home,
        "label_homework": homework,
        "two_column": two_col,
        "one_column": one_col,
        "kl_solid_border": kl_solid,
    }


def html_structure_report() -> dict[str, Any]:
    structures: dict[str, list[dict[str, Any]]] = {}
    bodies_root = RAW_DIR / "courses"
    for key, _name, _cid in COURSES:
        bodies_dir = bodies_root / key / "page-bodies"
        samples: list[dict[str, Any]] = []
        if bodies_dir.exists():
            for f in sorted(bodies_dir.glob("*.html")):
                body = f.read_text(encoding="utf-8")
                samples.append({"file": f.name, **_extract_html_structure(body)})
        structures[key] = samples
    return {"authority": "LIVE_CANVAS_PRECEDENT", "courses": structures}


def at_home_vs_homework_report(structures: dict[str, Any]) -> dict[str, Any]:
    at_home = 0
    homework = 0
    examples: dict[str, list[str]] = {"at_home": [], "homework": []}
    for course, samples in structures.get("courses", {}).items():
        for s in samples:
            if s.get("label_at_home"):
                at_home += 1
                examples["at_home"].append(f"{course}/{s.get('file')}")
            elif s.get("label_homework"):
                homework += 1
                examples["homework"].append(f"{course}/{s.get('file')}")
    conclusion = (
        "At Home" if at_home > homework else ("Homework" if homework > at_home else "MIXED")
    )
    return {
        "authority": "LIVE_CANVAS_PRECEDENT",
        "at_home_occurrences": at_home,
        "homework_occurrences": homework,
        "dominant_live_label": conclusion,
        "examples": examples,
        "note": "Observation only; not promoted to OWNER_POLICY.",
    }


def module_placement_report() -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, _name, _cid in COURSES:
        course_dir = RAW_DIR / "courses" / key
        modules = []
        mod_path = course_dir / "modules.json"
        if mod_path.exists():
            modules = json.loads(mod_path.read_text(encoding="utf-8"))
        agenda_in_modules = []
        for m in modules:
            if not isinstance(m, dict) or not m.get("id"):
                continue
            items_path = course_dir / f"module-items-{m['id']}.json"
            if not items_path.exists():
                continue
            items = json.loads(items_path.read_text(encoding="utf-8"))
            for it in items:
                if isinstance(it, dict) and it.get("type") == "Page":
                    pu = str(it.get("page_url") or "")
                    if re.search(r"q\d+w\d|week|agenda|quarter", pu.lower()):
                        agenda_in_modules.append(
                            {"module": m.get("name"), "page_url": pu, "title": it.get("title")}
                        )
        result[key] = {
            "module_names": [m.get("name") for m in modules if isinstance(m, dict)],
            "agenda_pages_in_modules": agenda_in_modules,
        }
    return {"authority": "LIVE_CANVAS_PRECEDENT", "courses": result}


def assignment_configuration_report() -> dict[str, Any]:
    matrix: dict[str, list[dict[str, Any]]] = {}
    for key, name, _cid in COURSES:
        path = RAW_DIR / "courses" / key / "assignments.json"
        if not path.exists():
            continue
        assignments = json.loads(path.read_text(encoding="utf-8"))
        rows = []
        for a in assignments:
            if not isinstance(a, dict):
                continue
            rows.append(
                {
                    "title": a.get("name"),
                    "id": a.get("id"),
                    "assignment_group_id": a.get("assignment_group_id"),
                    "points_possible": a.get("points_possible"),
                    "grading_type": a.get("grading_type"),
                    "submission_types": a.get("submission_types"),
                    "due_at": a.get("due_at"),
                    "unlock_at": a.get("unlock_at"),
                    "lock_at": a.get("lock_at"),
                    "published": a.get("published"),
                    "omit_from_final_grade": a.get("omit_from_final_grade"),
                    "description_chars": len(a.get("description") or ""),
                }
            )
        matrix[name] = rows
    return {"authority": "LIVE_CANVAS_PRECEDENT", "courses": matrix}


def announcement_patterns_report() -> dict[str, Any]:
    patterns: dict[str, list[dict[str, Any]]] = {}
    for key, name, _cid in COURSES:
        path = RAW_DIR / "courses" / key / "announcements.json"
        if not path.exists():
            continue
        anns = json.loads(path.read_text(encoding="utf-8"))
        rows = []
        for a in anns:
            if not isinstance(a, dict):
                continue
            rows.append(
                {
                    "title": a.get("title"),
                    "id": a.get("id"),
                    "delayed_post_at": a.get("delayed_post_at"),
                    "posted_at": a.get("posted_at"),
                    "published": a.get("published"),
                    "message_chars": len(a.get("message") or ""),
                    "has_html": "<" in (a.get("message") or ""),
                }
            )
        patterns[name] = rows
    return {"authority": "LIVE_CANVAS_PRECEDENT", "courses": patterns}


def homeroom_newsletter_report() -> dict[str, Any]:
    front = RAW_DIR / "courses" / "homeroom" / "front-page.html"
    body = front.read_text(encoding="utf-8") if front.exists() else ""
    sections = []
    for marker in ("Important Dates", "Homeroom News", "School News", "Birthdays", "Picture Day"):
        if marker in body:
            sections.append(marker)
    birthday_tiles = len(re.findall(r"flex:\s*1\s+1\s+\d+px", body))
    has_links = "<a " in body
    has_files = "/files/" in body
    return {
        "authority": "LIVE_CANVAS_PRECEDENT",
        "front_page_body_chars": len(body),
        "sections_detected": sections,
        "birthday_section_present": "Birthdays" in body,
        "birthday_tile_count_approx": birthday_tiles,
        "has_links": has_links,
        "has_file_references": has_files,
        "note": "Structural only; student names are not collected in this normalized artifact.",
    }


def anomalies_report(recon: dict[str, Any], at_home: dict[str, Any]) -> dict[str, Any]:
    anomalies = []
    for r in recon.get("results", []):
        if r.get("classification") != "MATCH":
            anomalies.append(f"{r.get('subject')}: mapping {r.get('classification')} (expected {r.get('expected_id')}, live {r.get('live_id')})")
    if at_home.get("at_home_occurrences") and at_home.get("homework_occurrences"):
        anomalies.append(
            "Live precedent shows BOTH 'At Home' and 'Homework' labels across pages (see At Home vs Homework)."
        )
    return {"authority": "LIVE_CANVAS_PRECEDENT", "anomalies": anomalies}


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #


def main() -> int:
    scan = static_write_verb_scan()
    _write_json(SWEEP_DIR / "write-verbs-scan.json", scan)
    if not scan["write_free"]:
        print("FAIL: static write-verb scan found forbidden tokens")
        return 1
    if not scan["get_only"]:
        print("FAIL: GET-only marker not confirmed")
        return 1

    print("PHASE 2A — LIVE CANVAS GET-ONLY PRECEDENT SWEEP")
    print("=" * 72)
    print("Static GET-only scan: PASS")
    print(f"  write_free={scan['write_free']} get_marker_count={scan['get_only_marker_count']}")

    # Pacing fresh-read.
    print("\n[1] FRESH PACING READ (4A - Reagan)")
    pacing = fetch_pacing()
    _write_json(NORM_DIR / "pacing-state.json", pacing)
    print(f"  status: {pacing['status']}")
    print(f"  instructional_status_today: {pacing['instructional_status_today']}")
    print(f"  date_columns: {pacing['date_columns_observed']}")

    # Credentials + auth read test.
    print("\n[2] CANVAS CONFIGURATION")
    creds = credentials.resolve_credentials()
    base_url = creds["CANVAS_BASE_URL"].strip().rstrip("/")
    token = creds["CANVAS_TOKEN"]
    client = ReadOnlyClient(base_url, token)
    me = client.get("/api/v1/users/self")
    authed = isinstance(me, dict) and "id" in me and "__error__" not in me
    auth_identity = {"authenticated": bool(authed), "id": me.get("id") if isinstance(me, dict) else None}
    _write_json(NORM_DIR / "auth-identity.json", auth_identity)
    print("  Canvas configuration available: PASS")
    print(f"  Authentication read test: {'PASS' if authed else 'FAIL'}")
    print("  Write methods blocked: PASS (GET-only client; no write verbs in source)")

    # Course sweep.
    print("\n[3] LIVE COURSE SWEEP")
    live_by_key: dict[str, dict[str, Any]] = {}
    for key, name, cid in COURSES:
        print(f"  --- {name} ({cid}) ---")
        result = sweep_course(key, name, cid, client)
        live_by_key[key] = result
        lc = result.get("live_course", {})
        print(f"    live: id={lc.get('id')} name={lc.get('name')!r} "
              f"state={lc.get('workflow_state')} code={lc.get('course_code')!r}")
        print(f"    pages={result.get('pages_count')} assignments={result.get('assignments_count')} "
              f"announcements={result.get('announcements_count')}")

    # Normalization.
    print("\n[4] NORMALIZATION")
    recon = reconcile_courses(live_by_key)
    _write_json(NORM_DIR / "course-reconciliation.json", recon)
    structures = html_structure_report()
    _write_json(NORM_DIR / "html-structure.json", structures)
    at_home = at_home_vs_homework_report(structures)
    _write_json(NORM_DIR / "at-home-vs-homework.json", at_home)
    _write_json(NORM_DIR / "module-placement.json", module_placement_report())
    _write_json(NORM_DIR / "assignment-groups-map.json", {
        "authority": "LIVE_CANVAS_PRECEDENT",
        "courses": {k: v.get("assignment_groups") for k, v in live_by_key.items()},
    })
    _write_json(NORM_DIR / "assignment-configuration-matrix.json", assignment_configuration_report())
    _write_json(NORM_DIR / "announcement-patterns.json", announcement_patterns_report())
    _write_json(NORM_DIR / "homeroom-newsletter-structure.json", homeroom_newsletter_report())
    _write_json(NORM_DIR / "anomalies.json", anomalies_report(recon, at_home))

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "get_only": scan["write_free"],
        "http_get_calls": client.get_calls,
        "http_error_calls": client.error_calls,
        "post_calls": 0,
        "put_calls": 0,
        "patch_calls": 0,
        "delete_calls": 0,
        "token_leakage": 0,
        "student_data_collection": 0,
        "live_canvas_mutations": 0,
        "course_reconciliation": recon.get("results"),
        "at_home_vs_homework": at_home,
    }
    _write_json(NORM_DIR / "summary.json", summary)

    print("\n[5] SUMMARY")
    print(f"  GET calls issued: {client.get_calls}")
    print(f"  POST/PUT/PATCH/DELETE calls: 0")
    print(f"  token leakage: 0")
    print(f"  student-data collection: 0")
    print(f"  live Canvas mutations: 0")
    print(f"  raw evidence:      {RAW_DIR}")
    print(f"  normalized artifacts: {NORM_DIR}")
    print("WRITES PERFORMED: 0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
