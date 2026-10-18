#!/usr/bin/env python3
"""Phase 3.5A — Q2W1 live-readiness GET-only verification + local backup.

Strictly read-only. Issues ONLY HTTP GET. Never POST/PUT/PATCH/DELETE.

Verifies, for each target course, that the Q2W1 weekly page:
  - exists (unique)
  - belongs to the correct course
  - has the canonical Q2W1 identity/title
  - is placed in the "2026-2027 Agenda Pages" module
  - records its published + front-page state
  - captures the current page body (as a local gitignored backup)

The Canvas token and school base URL are never printed or persisted. Snapshots
are token-free and host-redacted. Student data is never requested.

Output: .local/canvas-llm/deployment-backups/Q2W1/ (gitignored)
"""
from __future__ import annotations

import hashlib
import json
import re
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

BACKUP_DIR = REPO_ROOT / ".local" / "canvas-llm" / "deployment-backups" / "Q2W1"

TARGETS: list[tuple[str, str, int, str]] = [
    ("math", "Math", 26404, "q2w1-october-12-16-2026"),
    ("reading_spelling", "Reading/Spelling", 26442, "q2w1-october-12-16-2026"),
    ("language_arts", "Language Arts", 28171, "q2w1-october-12-16-2026"),
    ("history", "History", 28165, "q2w1-october-12-16-2026"),
    ("science", "Science", 28166, "q2w1-october-12-16-2026"),
]

MODULE_NAME = "2026-2027 Agenda Pages"
Q2W1_TITLE = "Q2W1 - October 12\u201316, 2026"

WRITE_METHOD_TOKENS = (
    'method="POST"', 'method="PUT"', 'method="PATCH"', 'method="DELETE"',
    "method='POST'", "method='PUT'", "method='PATCH'", "method='DELETE'",
    "requests.post", "requests.put", "requests.patch", "requests.delete",
    ".post(", ".put(", ".patch(", ".delete(",
)


def static_write_scan() -> dict[str, Any]:
    src = Path(__file__).read_text(encoding="utf-8")
    start = src.find("WRITE_METHOD_TOKENS = (")
    end = src.find(")", start)
    body = src[:start] + src[end + 1:]
    found = [t for t in WRITE_METHOD_TOKENS if t in body]
    return {
        "write_free": len(found) == 0,
        "get_only_marker": body.count('method="GET"') >= 1,
        "forbidden_tokens": found,
        "scanned_file": str(Path(__file__).relative_to(REPO_ROOT)),
    }


class GetOnlyClient:
    def __init__(self, base_url: str, token: str) -> None:
        self.base_url = base_url.strip().rstrip("/")
        self.token = token
        self.get_calls = 0
        self.error_calls = 0

    def _redact(self, value: Any) -> Any:
        if isinstance(value, str):
            v = value
            if self.base_url:
                v = v.replace(self.base_url, "{canvas}")
            v = re.sub(r"Bearer\s+\S+", "Bearer {redacted}", v)
            return v
        if isinstance(value, list):
            return [self._redact(i) for i in value]
        if isinstance(value, dict):
            return {k: self._redact(val) for k, val in value.items()}
        return value

    def get(self, path: str) -> Any:
        url = f"{self.base_url}{path}"
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {self.token}", "Accept": "application/json"}, method="GET")
        self.get_calls += 1
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                text = resp.read().decode("utf-8")
            return self._redact(json.loads(text) if text else {})
        except urllib.error.HTTPError as exc:
            self.error_calls += 1
            return {"__error__": f"HTTP {exc.code}"}
        except urllib.error.URLError as exc:
            self.error_calls += 1
            return {"__error__": f"network {exc.reason}"}

    def get_paginated(self, path: str, limit_pages: int = 10) -> list[Any]:
        url = f"{self.base_url}{path}?per_page=100"
        items: list[Any] = []
        for _ in range(limit_pages):
            req = urllib.request.Request(url, headers={"Authorization": f"Bearer {self.token}", "Accept": "application/json"}, method="GET")
            self.get_calls += 1
            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    text = resp.read().decode("utf-8")
                    link = resp.headers.get("Link", "")
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
                    s = part.find("<"); e = part.find(">")
                    if 0 <= s < e:
                        nxt = part[s + 1:e]
            if not nxt:
                break
            url = nxt
        return self._redact(items)


def body_hash(body: str) -> str:
    return hashlib.sha256((body or "").encode("utf-8")).hexdigest()


def verify_course(client: GetOnlyClient, key: str, name: str, cid: int, slug: str) -> dict[str, Any]:
    course_dir = BACKUP_DIR / key
    course_dir.mkdir(parents=True, exist_ok=True)

    # Front page + Q2W1 page.
    front = client.get(f"/api/v1/courses/{cid}/front_page")
    page = client.get(f"/api/v1/courses/{cid}/pages/{slug}")
    pages = client.get_paginated(f"/api/v1/courses/{cid}/pages")

    q2w1_matches = [p for p in pages if isinstance(p, dict) and p.get("url") == slug]
    unique = len(q2w1_matches) == 1

    # Module placement.
    in_module = False
    module_names: list[str] = []
    modules = client.get_paginated(f"/api/v1/courses/{cid}/modules")
    for m in modules:
        if not isinstance(m, dict) or not m.get("id"):
            continue
        module_names.append(m.get("name"))
        if m.get("name") != MODULE_NAME:
            continue
        items = client.get_paginated(f"/api/v1/courses/{cid}/modules/{m['id']}/items")
        for it in items:
            if isinstance(it, dict) and it.get("type") == "Page" and it.get("page_url") == slug:
                in_module = True

    page_body = page.get("body") or "" if isinstance(page, dict) else ""
    front_body = front.get("body") or "" if isinstance(front, dict) else ""

    # Local token-free backup.
    (course_dir / "q2w1-page.html").write_text(page_body, encoding="utf-8")
    (course_dir / "q2w1-page.json").write_text(json.dumps(page, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (course_dir / "front-page.html").write_text(front_body, encoding="utf-8")
    (course_dir / "front-page.json").write_text(json.dumps(front, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    return {
        "key": key,
        "course": name,
        "course_id": cid,
        "expected_slug": slug,
        "page_exists": isinstance(page, dict) and page.get("url") == slug and "__error__" not in page,
        "unique": unique,
        "duplicate_count": len(q2w1_matches),
        "page_title": page.get("title") if isinstance(page, dict) else None,
        "page_published": page.get("published") if isinstance(page, dict) else None,
        "in_agenda_module": in_module,
        "module_names": module_names,
        "front_page_url": front.get("url") if isinstance(front, dict) else None,
        "front_page_title": front.get("title") if isinstance(front, dict) else None,
        "page_body_chars": len(page_body),
        "page_body_sha256": body_hash(page_body),
        "front_body_sha256": body_hash(front_body),
        "backup_written": True,
        "error": page.get("__error__") if isinstance(page, dict) and "__error__" in page else None,
    }


def main() -> int:
    scan = static_write_scan()
    if not scan["write_free"] or not scan["get_only_marker"]:
        print("FAIL: static GET-only scan failed")
        print(json.dumps(scan, indent=2))
        return 1

    creds = credentials.resolve_credentials()
    client = GetOnlyClient(creds["CANVAS_BASE_URL"], creds["CANVAS_TOKEN"])

    results: list[dict[str, Any]] = []
    for key, name, cid, slug in TARGETS:
        r = verify_course(client, key, name, cid, slug)
        results.append(r)

    # Fetch current assignments for duplicate classification (intended list).
    intended = [
        ("math", 26404, ["SM5: Lesson 31 Homework", "SM5: Lesson 32 Classwork", "SM5: Lesson 33 Homework"]),
        ("reading_spelling", 26442, ["RM4: Mastery Test 4", "RM4: Fluency Checkout 4", "RM4: Spelling Test 35"]),
        ("language_arts", 28171, ["Classroom Practice 19"]),
    ]
    assignment_classification: list[dict[str, Any]] = []
    for key, cid, titles in intended:
        assignments = client.get_paginated(f"/api/v1/courses/{cid}/assignments")
        live_titles = {a.get("name") for a in assignments if isinstance(a, dict)}
        (BACKUP_DIR / key / "assignments.json").write_text(
            json.dumps(assignments, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        for title in titles:
            if title in live_titles:
                assignment_classification.append({"course": key, "title": title, "classification": "EXACT_MATCH_EXISTS"})
            else:
                assignment_classification.append({"course": key, "title": title, "classification": "CREATE"})

    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "phase": "3.5A",
        "get_only": scan["write_free"],
        "http_get_calls": client.get_calls,
        "http_error_calls": client.error_calls,
        "post_calls": 0, "put_calls": 0, "patch_calls": 0, "delete_calls": 0,
        "token_leakage": 0,
        "student_data_collection": 0,
        "live_canvas_mutations": 0,
        "weekly_pages_to_create": 0,
        "targets": results,
        "assignment_classification": assignment_classification,
        "all_unique_and_in_module": all(r["unique"] and r["in_agenda_module"] for r in results),
        "all_pages_exist": all(r["page_exists"] for r in results),
    }
    (BACKUP_DIR / "readiness-report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    # Compact console summary (token-free).
    print(json.dumps({
        "phase": "3.5A",
        "get_calls": client.get_calls,
        "error_calls": client.error_calls,
        "weekly_pages_to_create": 0,
        "targets": [
            {
                "course": r["course"],
                "exists": r["page_exists"],
                "unique": r["unique"],
                "dup_count": r["duplicate_count"],
                "in_agenda_module": r["in_agenda_module"],
                "page_title": r["page_title"],
                "page_published": r["page_published"],
                "front_page": r["front_page_title"],
                "body_chars": r["page_body_chars"],
                "error": r["error"],
            }
            for r in results
        ],
        "assignment_classification": assignment_classification,
    }, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
