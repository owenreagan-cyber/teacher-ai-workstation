#!/usr/bin/env python3
"""Q1W9 Homeroom announcement message repair (UPDATE in place, no duplicates).

Canvas de-duplicated the global stylesheet <link> when the announcement intro
already carried it and the embedded newsletter carried it again; the writer
payload also appended a second trailing global <script>. This rewrites the two
Homeroom Week 9 announcements to the exact approved message, in place.

Usage:
    CANVAS_LLM_DEPLOYMENT_MODE=live CANVAS_LLM_LIVE_Q1W2_APPROVED=1 \
        python3 scripts/canvas-llm/q1w9_homeroom_repair.py
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.canvas_llm_phase22 import canvas_credentials as credentials  # noqa: E402
from scripts.canvas_llm_phase22 import canvas_writer as writer  # noqa: E402

OUT_DIR = REPO_ROOT / ".local" / "canvas-llm" / "q1w9-audit"
BUILD_PATH = REPO_ROOT / "scripts" / "canvas-llm" / "q1w9_build.py"


def _load_build() -> Any:
    spec = importlib.util.spec_from_file_location("q1w9_build", BUILD_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def main() -> int:
    build = _load_build()
    build.write_local_artifacts()
    manifest = json.loads((OUT_DIR / "q1w9-manifest.json").read_text(encoding="utf-8"))

    os.environ["CANVAS_LLM_DEPLOYMENT_MODE"] = "live"
    os.environ["CANVAS_LLM_LIVE_Q1W2_APPROVED"] = "1"
    credentials.load_credentials()

    targets = [
        a for a in manifest["actions"]
        if a.get("object_type") == "announcement" and a.get("course") == "Homeroom"
    ]

    writes = 0

    def find_id(course_id: int, title: str) -> str | None:
        import urllib.parse
        import urllib.request

        base = os.environ["CANVAS_BASE_URL"].strip().rstrip("/")
        token = os.environ["CANVAS_TOKEN"]
        url = (
            f"{base}/api/v1/courses/{course_id}/discussion_topics?"
            + urllib.parse.urlencode({"only_announcements": "true", "per_page": 100})
        )
        while url:
            req = urllib.request.Request(
                url, headers={"Authorization": f"Bearer {token}"}, method="GET"
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode())
                link = resp.headers.get("Link", "")
            for item in data:
                if (item.get("title") or "").strip() == title:
                    return str(item.get("id"))
            url = None
            for part in link.split(","):
                if 'rel="next"' in part:
                    url = part[part.find("<") + 1 : part.find(">")]
        return None

    for action in targets:
        topic_id = action.get("existing_id")
        if not topic_id:
            topic_id = find_id(action["course_id"], action["resulting_title"])
        if not topic_id:
            raise SystemExit(f"Homeroom target not found live: {action['resulting_title']!r}")
        res = writer.update_announcement_live(
            course_id=action["course_id"],
            topic_id=str(topic_id),
            title=action["resulting_title"],
            new_title=action["resulting_title"],
            message=action["message"],
            published=True,
            approved=True,
        )
        if res.write_status == "WRITTEN":
            writes += 1
            print(f"WRITTEN: Homeroom announcement {action['resulting_title']!r} "
                  f"id={topic_id} body_hash={res.body_hash}")
        else:
            print(f"BLOCKED: {action['resulting_title']!r} {res.blockers}")
            return 1
    print(f"WRITES PERFORMED: {writes}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
