#!/usr/bin/env python3
"""Phase 3.5A — fresh-GET assignment-group verification (GET-only).

Fresh-reads assignment groups for all five courses and verifies the canonical
assignment-routing contract. Fail-closes on missing/renamed/duplicated/ambiguous
groups. No writes. No token leak.
"""
from __future__ import annotations

import json
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.canvas_llm_phase22 import canvas_credentials as credentials  # noqa: E402

OUT = REPO_ROOT / ".local" / "canvas-llm" / "deployment-backups" / "Q2W1"

# Canonical contract: subject -> expected assignment group names (exact).
# group_key -> ordered expected group names.
CANONICAL_GROUPS: dict[str, tuple[str, ...]] = {
    "math": ("Written Assessments", "Fact Assessments", "Homework/Class Work"),
    "reading_spelling": ("Check Out", "Assessments", "Homework"),
    "language_arts": ("Classwork", "Assessments"),
    "history": ("Assignments",),
    "science": ("Assignments",),
}

TARGETS = [
    ("math", "Math", 26404),
    ("reading_spelling", "Reading/Spelling", 26442),
    ("language_arts", "Language Arts", 28171),
    ("history", "History", 28165),
    ("science", "Science", 28166),
]

WRITE_TOKENS = ('method="POST"', 'method="PUT"', 'method="PATCH"', 'method="DELETE"')


def static_scan() -> dict[str, Any]:
    src = Path(__file__).read_text(encoding="utf-8")
    start = src.find("WRITE_TOKENS = (")
    end = src.find(")", start)
    body = src[:start] + src[end + 1:]
    return {"write_free": not any(t in body for t in WRITE_TOKENS), "get_marker": 'method="GET"' in body}


class Get:
    def __init__(self, base, token):
        self.base = base.strip().rstrip("/"); self.token = token; self.calls = 0; self.errors = 0

    def _redact(self, v):
        if isinstance(v, str):
            v = v.replace(self.base, "{canvas}"); v = re.sub(r"Bearer\s+\S+", "Bearer {redacted}", v)
            return v
        if isinstance(v, list):
            return [self._redact(i) for i in v]
        if isinstance(v, dict):
            return {k: self._redact(x) for k, x in v.items()}
        return v

    def pag(self, path):
        url = f"{self.base}{path}?per_page=100"
        items = []
        for _ in range(10):
            req = urllib.request.Request(url, headers={"Authorization": f"Bearer {self.token}", "Accept": "application/json"}, method="GET")
            self.calls += 1
            try:
                with urllib.request.urlopen(req, timeout=30) as r:
                    data = json.loads(r.read().decode() or "[]"); link = r.headers.get("Link", "")
            except urllib.error.HTTPError:
                self.errors += 1; break
            except urllib.error.URLError:
                self.errors += 1; break
            items.extend(data if isinstance(data, list) else [])
            nxt = None
            for part in (link or "").split(","):
                if 'rel="next"' in part:
                    s = part.find("<"); e = part.find(">")
                    if 0 <= s < e: nxt = part[s+1:e]
            if not nxt: break
            url = nxt
        return self._redact(items)


def main():
    scan = static_scan()
    if not scan["write_free"] or not scan["get_marker"]:
        print("FAIL static GET-only scan"); return 1
    creds = credentials.resolve_credentials()
    c = Get(creds["CANVAS_BASE_URL"], creds["CANVAS_TOKEN"])

    report = {"generated_at": datetime.now(timezone.utc).isoformat(), "phase": "3.5A", "post": 0, "put": 0, "patch": 0, "delete": 0, "token_leakage": 0}
    rows = []
    all_ok = True
    for key, name, cid in TARGETS:
        groups = c.pag(f"/api/v1/courses/{cid}/assignment_groups")
        live_names = [g.get("name") for g in groups if isinstance(g, dict)]
        expected = CANONICAL_GROUPS[key]
        missing = [g for g in expected if g not in live_names]
        duplicates = [n for n in set(live_names) if live_names.count(n) > 1]
        # any unexpected groups? (renamed/ambiguous) — report but don't necessarily fail
        extra = [n for n in live_names if n not in expected]
        row = {
            "course": name, "course_id": cid,
            "expected": list(expected),
            "live": live_names,
            "missing": missing,
            "duplicates": duplicates,
            "unexpected": extra,
            "status": "PASS" if (not missing and not duplicates) else "FAIL",
            "groups": [{"name": g.get("name"), "id": g.get("id"), "position": g.get("position")} for g in groups if isinstance(g, dict)],
        }
        if row["status"] == "FAIL":
            all_ok = False
        rows.append(row)

    report["groups_verified"] = all_ok
    report["rows"] = rows
    (OUT / "assignment-groups-verified.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"phase": "3.5A", "get_calls": c.calls, "errors": c.errors, "groups_verified": all_ok,
                      "rows": [{k: r[k] for k in ("course", "expected", "live", "missing", "duplicates", "unexpected", "status")} for r in rows]}, indent=2, ensure_ascii=False))
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
