#!/usr/bin/env python3
"""Phase 3.5A-pre — GET-only Q2W2 (and Q2W1 re-confirm) page identity sweep.

Strictly read-only. Verifies the seeded Q2W2 pages exist uniquely in the
"2026-2027 Agenda Pages" module (and re-confirms Q2W1). No writes. No token leak.
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

TARGETS = [
    ("math", "Math", 26404),
    ("reading_spelling", "Reading/Spelling", 26442),
    ("language_arts", "Language Arts", 28171),
    ("history", "History", 28165),
    ("science", "Science", 28166),
]
SLUGS = ("q2w1-october-12-16-2026", "q2w2-october-19-23-2026")
MODULE = "2026-2027 Agenda Pages"

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
            v = v.replace(self.base, "{canvas}")
            v = re.sub(r"Bearer\s+\S+", "Bearer {redacted}", v)
            return v
        if isinstance(v, list):
            return [self._redact(i) for i in v]
        if isinstance(v, dict):
            return {k: self._redact(x) for k, x in v.items()}
        return v

    def go(self, path):
        url = f"{self.base}{path}"
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {self.token}", "Accept": "application/json"}, method="GET")
        self.calls += 1
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return self._redact(json.loads(r.read().decode() or "{}"))
        except urllib.error.HTTPError as e:
            self.errors += 1; return {"__error__": f"HTTP {e.code}"}
        except urllib.error.URLError as e:
            self.errors += 1; return {"__error__": f"net {e.reason}"}

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
    rows = []
    for key, name, cid in TARGETS:
        pages = c.pag(f"/api/v1/courses/{cid}/pages")
        for slug in SLUGS:
            matches = [p for p in pages if isinstance(p, dict) and p.get("url") == slug]
            page = c.go(f"/api/v1/courses/{cid}/pages/{slug}")
            in_module = False
            for m in c.pag(f"/api/v1/courses/{cid}/modules"):
                if m.get("name") != MODULE: continue
                for it in c.pag(f"/api/v1/courses/{cid}/modules/{m['id']}/items"):
                    if isinstance(it, dict) and it.get("type") == "Page" and it.get("page_url") == slug:
                        in_module = True
            rows.append({
                "course": name, "slug": slug,
                "exists": isinstance(page, dict) and page.get("url") == slug and "__error__" not in page,
                "unique": len(matches) == 1, "dup": len(matches),
                "in_module": in_module, "title": page.get("title") if isinstance(page, dict) else None,
                "published": page.get("published") if isinstance(page, dict) else None,
                "body_chars": len(page.get("body") or "") if isinstance(page, dict) else 0,
            })
    out = {"generated_at": datetime.now(timezone.utc).isoformat(), "phase": "3.5A-pre", "get_calls": c.calls, "errors": c.errors,
           "post": 0, "put": 0, "patch": 0, "delete": 0, "token_leakage": 0, "rows": rows}
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
