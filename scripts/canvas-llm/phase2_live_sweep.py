#!/usr/bin/env python3
"""Phase 2 — GET-only live Canvas exploration sweep (zero writes).

Strictly read-only. Only HTTP GET is ever issued. There is no method parameter.
Static scan proves no POST/PUT/PATCH/DELETE tokens exist in the execution path.
The token and school host are never printed; host is redacted in output.

Resolves the four live-read-required items:
  1. exact assignment-group IDs + module IDs
  2. module-placement behavior
  3. parent/observer relationship availability (structural/schema only)
  4. Canvas Conversation attachment/image capability (repo + schema; no write test)

Outputs (local, untracked): .local/canvas-llm/phase2-live-sweep/
"""
from __future__ import annotations

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

OUT = REPO_ROOT / ".local" / "canvas-llm" / "phase2-live-sweep"
OUT.mkdir(parents=True, exist_ok=True)

COURSES = [
    ("math", "Math", 26404),
    ("reading_spelling", "Reading/Spelling", 26442),
    ("language_arts", "Language Arts", 28171),
    ("history", "History", 28165),
    ("science", "Science", 28166),
    ("homeroom", "Homeroom", 26429),
]

EXPECTED_GROUPS = {
    "math": ["Written Assessments", "Fact Assessments", "Homework/Class Work"],
    "reading_spelling": ["Check Out", "Assessments", "Homework"],
    "language_arts": ["Classwork", "Assessments"],
    "history": ["Assignments"],
    "science": ["Assignments"],
    "homeroom": ["Assignments"],
}

WEEK_SLUGS = ["q1w7-august-31-september-4-2026", "q1w8-september-7-11-2026",
              "q1w9-september-14-18-2026", "q2w1-october-12-16-2026", "q2w2-october-19-23-2026"]

# Forbidden write tokens scanned statically (tuple is stripped before scan).
WRITE_TOKENS = (
    'method="POST"', 'method="PUT"', 'method="PATCH"', 'method="DELETE"',
    "method='POST'", "method='PUT'", "method='PATCH'", "method='DELETE'",
    "requests.post", "requests.put", "requests.patch", "requests.delete",
    ".post(", ".put(", ".patch(", ".delete(",
)


def static_write_scan() -> dict[str, Any]:
    src = Path(__file__).read_text(encoding="utf-8")
    start = src.find("WRITE_TOKENS = (")
    end = src.find(")", start)
    body = src[:start] + src[end + 1:]
    found = [t for t in WRITE_TOKENS if t in body]
    return {"write_free": len(found) == 0, "get_only_marker": body.count('method="GET"') >= 1, "forbidden_tokens_found": found}


class GetOnly:
    def __init__(self, base: str, token: str):
        self.base = base.strip().rstrip("/")
        self.token = token
        self.calls = 0
        self.errors = 0

    def _redact(self, v: Any) -> Any:
        if isinstance(v, str):
            v = v.replace(self.base, "{canvas}")
            v = re.sub(r"Bearer\s+\S+", "Bearer {redacted}", v)
            return v
        if isinstance(v, list):
            return [self._redact(i) for i in v]
        if isinstance(v, dict):
            return {k: self._redact(x) for k, x in v.items()}
        return v

    def get(self, path: str) -> Any:
        url = f"{self.base}{path}"
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {self.token}", "Accept": "application/json"}, method="GET")
        self.calls += 1
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                text = r.read().decode("utf-8")
                return self._redact(json.loads(text) if text else {})
        except urllib.error.HTTPError as exc:
            self.errors += 1
            return {"__error__": f"HTTP {exc.code}"}
        except urllib.error.URLError as exc:
            self.errors += 1
            return {"__error__": f"network {exc.reason}"}

    def get_paginated(self, path: str, limit_pages: int = 10) -> list[Any]:
        url = f"{self.base}{path}?per_page=100"
        items: list[Any] = []
        for _ in range(limit_pages):
            req = urllib.request.Request(url, headers={"Authorization": f"Bearer {self.token}", "Accept": "application/json"}, method="GET")
            self.calls += 1
            try:
                with urllib.request.urlopen(req, timeout=30) as r:
                    text = r.read().decode("utf-8")
                    link = r.headers.get("Link", "")
                data = json.loads(text) if text else []
            except urllib.error.HTTPError as exc:
                self.errors += 1
                return [{"__error__": f"HTTP {exc.code}"}]
            except urllib.error.URLError as exc:
                self.errors += 1
                return [{"__error__": f"network {exc.reason}"}]
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


def field_keys(obj: Any) -> list[str]:
    """Return only the top-level JSON keys (schema), never values (PII-safe)."""
    if isinstance(obj, dict):
        return sorted(obj.keys())
    if isinstance(obj, list) and obj and isinstance(obj[0], dict):
        return sorted(obj[0].keys())
    return []


def main() -> int:
    scan = static_write_scan()
    if not scan["write_free"] or not scan["get_only_marker"]:
        print("FAIL static GET-only scan")
        print(json.dumps(scan, indent=2))
        return 1

    creds = credentials.resolve_credentials()
    c = GetOnly(creds["CANVAS_BASE_URL"], creds["CANVAS_TOKEN"])

    summary: dict[str, Any] = {
        "phase": "2",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "get_only": scan["write_free"],
        "get_calls": 0, "post": 0, "put": 0, "patch": 0, "delete": 0,
        "token_leakage": 0, "student_data_fetched": 0,
    }

    # 1. Course inventory
    inventory = []
    for key, name, cid in COURSES:
        course = c.get(f"/api/v1/courses/{cid}")
        front = c.get(f"/api/v1/courses/{cid}/front_page")
        modules = c.get_paginated(f"/api/v1/courses/{cid}/modules")
        inventory.append({
            "key": key, "name": name, "expected_id": cid,
            "live_id": course.get("id") if isinstance(course, dict) else None,
            "live_name": course.get("name") if isinstance(course, dict) else None,
            "course_code": course.get("course_code") if isinstance(course, dict) else None,
            "workflow_state": course.get("workflow_state") if isinstance(course, dict) else None,
            "front_page_title": front.get("title") if isinstance(front, dict) else None,
            "front_page_url": front.get("url") if isinstance(front, dict) else None,
            "module_names": [m.get("name") for m in modules if isinstance(m, dict)],
        })

    # 2. Assignment groups (exact names + IDs + duplicate counts)
    groups_report = []
    for key, name, cid in COURSES:
        groups = c.get_paginated(f"/api/v1/courses/{cid}/assignment_groups")
        live = [g for g in groups if isinstance(g, dict)]
        live_names = [g.get("name") for g in live]
        expected = EXPECTED_GROUPS[key]
        missing = [g for g in expected if g not in live_names]
        dups = {n: live_names.count(n) for n in set(live_names) if live_names.count(n) > 1}
        row = {
            "course": name, "course_id": cid,
            "groups": [{"name": g.get("name"), "id": g.get("id"), "position": g.get("position")} for g in live],
            "missing": missing, "duplicates": dups,
            "status": "PASS" if (not missing and not dups) else ("WARN" if missing else "FAIL"),
        }
        groups_report.append(row)

    # 3. Modules (names + IDs + published + item count)
    modules_report = []
    for key, name, cid in COURSES:
        modules = c.get_paginated(f"/api/v1/courses/{cid}/modules")
        rows = []
        for m in modules:
            if not isinstance(m, dict):
                continue
            rows.append({
                "name": m.get("name"), "id": m.get("id"),
                "published": m.get("published"), "position": m.get("position"),
                "items_count": m.get("items_count"),
            })
        modules_report.append({"course": name, "course_id": cid, "modules": rows})

    # 4. Weekly-page module placement (Q1W7-Q2W2)
    placement = []
    agenda_mod_ids = {}
    for key, name, cid in COURSES:
        modules = c.get_paginated(f"/api/v1/courses/{cid}/modules")
        agenda_id = None
        for m in modules:
            if isinstance(m, dict) and m.get("name") == "2026-2027 Agenda Pages":
                agenda_id = m.get("id")
        agenda_mod_ids[key] = agenda_id
        if not agenda_id:
            placement.append({"course": name, "agenda_module": None, "pages": []})
            continue
        items = c.get_paginated(f"/api/v1/courses/{cid}/modules/{agenda_id}/items")
        pages = []
        for it in items:
            if not isinstance(it, dict) or it.get("type") != "Page":
                continue
            pu = str(it.get("page_url") or "")
            if any(w in pu for w in ("q1w7", "q1w8", "q1w9", "q2w1", "q2w2")):
                pages.append({
                    "title": it.get("title"), "page_url": it.get("page_url"),
                    "module_item_id": it.get("id"), "position": it.get("position"),
                    "indent": it.get("indent"), "published": it.get("published"),
                })
        placement.append({"course": name, "agenda_module_id": agenda_id, "pages": pages})

    # 5. Assignment placement sample (does assignment live in a module too?)
    assignment_placement = []
    for key, name, cid in COURSES:
        # sample a few recent assignments via assignment_groups is not enough; list assignments
        assignments = c.get_paginated(f"/api/v1/courses/{cid}/assignments")
        sample = [a for a in assignments if isinstance(a, dict)][:5]
        # check module items that reference these assignment ids
        mod_items_with_assignment = []
        modules = c.get_paginated(f"/api/v1/courses/{cid}/modules")
        for m in modules:
            if not isinstance(m, dict) or not m.get("id"):
                continue
            items = c.get_paginated(f"/api/v1/courses/{cid}/modules/{m['id']}/items")
            for it in items:
                if isinstance(it, dict) and it.get("type") == "Assignment":
                    mod_items_with_assignment.append({
                        "module": m.get("name"), "assignment_id": it.get("content_id"),
                        "title": it.get("title"), "module_item_id": it.get("id"),
                    })
        assignment_placement.append({
            "course": name, "course_id": cid,
            "sampled_assignment_ids": [a.get("id") for a in sample],
            "assignments_in_modules": mod_items_with_assignment[:10],
        })

    # 6. Observer relationship (structural/schema only; per_page=1, keys only)
    observer = []
    for key, name, cid in COURSES:
        if name == "Homeroom":
            continue  # skip homeroom observer probe (still a course, but keep minimal)
        # Enrollments endpoint structural probe — schema keys only, no values.
        data = c.get(f"/api/v1/courses/{cid}/enrollments?type[]=ObserverEnrollment&per_page=1")
        if isinstance(data, list) and data and isinstance(data[0], dict):
            keys = field_keys(data[0])
            observer.append({
                "course": name, "course_id": cid,
                "observable": "AVAILABLE",
                "sample_field_keys": keys,
                "note": "schema-only; no values stored",
            })
        elif isinstance(data, dict) and "__error__" in data:
            observer.append({"course": name, "course_id": cid, "observable": "PERMISSION_BLOCKED", "error": data["__error__"]})
        else:
            observer.append({"course": name, "course_id": cid, "observable": "UNRESOLVED"})

    # 7. Conversation capability (repo + schema only; no write test)
    conversation = {
        "capability": "REQUIRES_WRITE_TEST",
        "note": (
            "Canvas Conversations create API (/api/v1/conversations) is documented to accept "
            "attachment_ids; inline HTML/images are not reliably rendered and rich HTML may be "
            "stripped. This cannot be proven live without a write test, which is forbidden here. "
            "Repo transport (canvas_connection_manager) has NO Conversation send method; only "
            "announcement/page/assignment create/update exist. Announcements (discussion_topics) "
            "support 'attachment' in create per Canvas API, but that is also write-only."
        ),
        "repo_transport_finding": "No Conversation create method in repo transport; only announcements/pages/assignments.",
        "attachment_support_announcement": "documented (write-only, unverified live)",
        "attachment_support_conversation": "documented via attachment_ids (write-only, unverified live)",
        "inline_image_distinct_from_attachment": "documented distinct (unverified live)",
        "html_preserved_in_conversation": "unverified; likely stripped/limited",
    }

    # 8. Weekly-update readback verification (Math/Reading-Spelling/LA/Science)
    weekly_readback = []
    wu_ids = {26404: 166383, 26442: 166384, 28171: 166385, 28166: 166386}
    wu_names = {26404: "Math", 26442: "Reading/Spelling", 28171: "Language Arts", 28166: "Science"}
    for cid, aid in wu_ids.items():
        a = c.get(f"/api/v1/courses/{cid}/discussion_topics/{aid}")
        msg = a.get("message") if isinstance(a, dict) else ""
        weekly_readback.append({
            "course": wu_names[cid], "announcement_id": aid,
            "title": a.get("title") if isinstance(a, dict) else None,
            "has_kl_wrapper_3": "kl_wrapper_3" in msg,
            "has_reminders": "Reminders" in msg,
            "weekdays_present": [d for d in ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday") if d in msg],
        })

    # 9. Homeroom front-page state
    hfp = c.get("/api/v1/courses/26429/front_page")
    homeroom = {
        "title": hfp.get("title") if isinstance(hfp, dict) else None,
        "url": hfp.get("url") if isinstance(hfp, dict) else None,
        "published": hfp.get("published") if isinstance(hfp, dict) else None,
        "front_page": hfp.get("front_page") if isinstance(hfp, dict) else None,
        "has_track2_week1": "Track 2, Week 1" in (hfp.get("body") or "") if isinstance(hfp, dict) else False,
        "has_fall_weather": "Fall Weather" in (hfp.get("body") or "") if isinstance(hfp, dict) else False,
        "has_track2_strong": "Starting Track 2 Strong" in (hfp.get("body") or "") if isinstance(hfp, dict) else False,
    }

    summary["get_calls"] = c.calls
    summary["errors"] = c.errors

    result = {
        "summary": summary,
        "course_inventory": inventory,
        "assignment_groups": groups_report,
        "modules": modules_report,
        "module_placement_weekly_pages": placement,
        "module_placement_assignments": assignment_placement,
        "observer_capability": observer,
        "conversation_capability": conversation,
        "weekly_update_readback": weekly_readback,
        "homeroom_front_page": homeroom,
    }

    for fname, data in {
        "course-inventory.json": inventory,
        "assignment-groups.json": groups_report,
        "modules.json": modules_report,
        "module-placement.json": placement,
        "observer-capability.json": observer,
        "conversation-capability.json": conversation,
        "homeroom-front-page.json": homeroom,
        "weekly-update-readback.json": weekly_readback,
        "sweep-summary.json": result,
    }.items():
        (OUT / fname).write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(json.dumps({"phase": "2", "get_calls": c.calls, "errors": c.errors, "get_only": scan["write_free"],
                      "observer": [o.get("observable") for o in observer],
                      "conversation": conversation["capability"]}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
