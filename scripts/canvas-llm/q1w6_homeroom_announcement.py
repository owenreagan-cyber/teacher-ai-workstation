#!/usr/bin/env python3
"""Q1W6 Homeroom family announcement — guarded creation (single write).

Creates one weekly Homeroom family announcement for Week 6 (Aug 24-28, 2026):

1. fresh-GET the Homeroom course front page and confirm it is the Week 6
   newsletter (rolling HTML base, never a PDF/Google Doc);
2. fresh-GET current Homeroom announcements and check for a current-week
   duplicate (same intended title or body);
3. back up the relevant live state before any write;
4. if no duplicate and BLOCKERS: 0, create the announcement via the guarded
   writer (short family intro + the full current newsletter HTML);
5. fresh-GET the created announcement and verify title, intro, newsletter body,
   and absence of subject pacing summaries.

The announcement body reuses the exact live newsletter HTML — it is never
rewritten. The token is never printed.
"""
from __future__ import annotations

import json
import os
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
from scripts.canvas_llm_phase22 import canvas_connection_manager as transport  # noqa: E402
from scripts.canvas_llm_phase22 import canvas_writer as writer  # noqa: E402

HOMEROOM_COURSE_ID = 26429
ANNOUNCEMENT_TITLE = "4th Grade Happenings - Week 6"
BACKUP_DIR = REPO_ROOT / ".local" / "canvas-llm" / "backups"

INTRO_HTML = (
    '<p style="margin: 0 0 12px;"><strong>Hound Families,</strong></p>'
    '<p style="margin: 0 0 12px;">Please see this week\u2019s classroom newsletter '
    'below for important dates, reminders, birthdays, and classroom updates.</p>'
    '<p style="margin: 0 0 12px;">Have a great week!</p>'
    '<p style="margin: 0 0 12px;">Mr. Reagan</p>'
)

REQUIRED_PRESENT = (
    "Hound Families",
    "Please see this week",
    "Have a great week!",
    "Mr. Reagan",
    "Week six brings some big changes",
    "Room 203",
    "new building",
    "September Birthdays",
    "Ava on September 4",
    "Timothy on September 16",
    "Charlotte on September 17",
    "Happy Birthday to Tito on August 30!",
    "Morning Carpool Times",
    "Afternoon Carpool Times",
    "No families should use the blue route",
    "Spirit Shirt Day",
    "Labor Day",
    "Picture Day",
    "Report Cards",
    "Track Out",
)

REQUIRED_ABSENT = (
    "Thaddeus",
    "Saxon",
    "Reading Mastery",
    "Shurley",
    "Classroom Practice",
    "Mastery Test",
    "Fact Assessment",
    "Spelling Test",
    "Math Test",
    "Chapter Test",
)


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


def _list_announcements(base_url: str, token: str) -> list[dict[str, Any]]:
    url = (
        f"{base_url}/api/v1/courses/{HOMEROOM_COURSE_ID}/discussion_topics"
        "?only_announcements=true&per_page=100"
    )
    items: list[dict[str, Any]] = []
    for _ in range(10):
        req = urllib.request.Request(
            url,
            headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            text = response.read().decode("utf-8")
            link = response.headers.get("Link", "")
        data = json.loads(text) if text else []
        if isinstance(data, list):
            items.extend(data)
        else:
            items.append(data)
            break
        nxt = None
        for part in link.split(","):
            if 'rel="next"' in part:
                start = part.find("<")
                end = part.find(">")
                if 0 <= start < end:
                    nxt = part[start + 1 : end]
        if not nxt:
            break
        url = nxt
    return items


def _duplicate_status(announcements: list[dict[str, Any]]) -> str | None:
    """Return the existing announcement id if a current-week duplicate exists."""
    for a in announcements:
        title = a.get("title") or ""
        msg = a.get("message") or ""
        if ANNOUNCEMENT_TITLE in title:
            return str(a.get("id"))
        if "Week six brings some big changes" in msg:
            return str(a.get("id"))
    return None


def _backup(front: dict[str, Any], announcements: list[dict[str, Any]]) -> Path:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = BACKUP_DIR / f"homeroom-announcement-preflight-{stamp}.json"
    payload = {
        "course_id": HOMEROOM_COURSE_ID,
        "front_page_url": front.get("url"),
        "front_page_title": front.get("title"),
        "front_page_updated_at": front.get("updated_at"),
        "front_page_body": front.get("body") or "",
        "existing_announcements": [
            {
                "id": a.get("id"),
                "title": a.get("title"),
                "posted_at": a.get("posted_at"),
                "message": a.get("message") or "",
            }
            for a in announcements
        ],
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    return path


def run(*, apply_write: bool = True) -> int:
    credentials.load_credentials()
    base_url = os.environ["CANVAS_BASE_URL"].strip().rstrip("/")
    token = os.environ["CANVAS_TOKEN"]

    # 1. Fresh GET front page.
    front = _get(base_url, token, f"/api/v1/courses/{HOMEROOM_COURSE_ID}/front_page")
    if isinstance(front, dict) and "__error__" in front:
        print(f"BLOCKED: front page read failed: {front['__error__']}")
        return 1
    body = front.get("body") or ""
    if "Week six brings some big changes" not in body:
        print("BLOCKED: front page is not the Week 6 newsletter; no write.")
        return 1
    print(
        f"front page: url={front.get('url')!r} title={front.get('title')!r} "
        f"updated_at={front.get('updated_at')!r} (Week 6 confirmed)"
    )

    # 2. Fresh GET announcements + duplicate check.
    announcements = _list_announcements(base_url, token)
    existing_id = _duplicate_status(announcements)
    if existing_id is not None:
        print(f"ALREADY_APPLIED: current-week announcement already exists (id={existing_id}); zero writes.")
        return 0
    print(f"duplicate check: no current-week announcement among {len(announcements)} live announcements")

    # 3. Backup live state.
    backup = _backup(front, announcements)
    print(f"backup written: {backup}")

    # 4. Build message = intro + full current newsletter HTML.
    message = INTRO_HTML + "\n" + body
    print(f"announcement message built: intro + full newsletter HTML ({len(message)} chars)")

    if not apply_write:
        preview = REPO_ROOT / ".local" / "canvas-llm" / "q1w6-announcement-preview.html"
        preview.write_text(message)
        print(f"PREVIEW ONLY: no write performed; preview saved to {preview}")
        return 0

    # 5. Create the announcement through the guarded writer.
    client = transport.Phase22LiveCanvasClient.from_env()
    result = writer.create_announcement_live(
        course_id=HOMEROOM_COURSE_ID,
        title=ANNOUNCEMENT_TITLE,
        message=message,
        published=True,
        approved=True,
        approved_by="Owen Reagan",
        client=client,
    )
    if result.write_status != "WRITTEN":
        print(f"BLOCKED: {result.write_status} ({', '.join(result.blockers) or 'blocked'})")
        return 1
    print(f"WRITTEN: announcement title={ANNOUNCEMENT_TITLE!r} id={result.target_id}")

    # 6. Fresh GET and verify.
    created = _get(
        base_url, token, f"/api/v1/courses/{HOMEROOM_COURSE_ID}/discussion_topics/{result.target_id}"
    )
    if isinstance(created, dict) and "__error__" in created:
        print(f"BLOCKED: verify read failed: {created['__error__']}")
        return 1
    msg = created.get("message") or ""
    title = created.get("title") or ""
    missing = [s for s in REQUIRED_PRESENT if s not in msg]
    found_absent = [s for s in REQUIRED_ABSENT if s in msg]
    print(json.dumps({
        "title": title,
        "title_ok": title == ANNOUNCEMENT_TITLE,
        "published": created.get("published"),
        "posted_at": created.get("posted_at"),
        "missing_content": missing,
        "unexpected_content": found_absent,
    }, indent=2, ensure_ascii=False))
    if title != ANNOUNCEMENT_TITLE or missing or found_absent:
        print("BLOCKED: verification failed.")
        return 1
    print("VERIFIED: family announcement created with intro + full Week 6 newsletter; no subject pacing summaries.")
    return 0


def main(argv: list[str] | None = None) -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Q1W6 Homeroom family announcement")
    parser.add_argument("--preview", action="store_true", help="fresh GET + build preview only; no write")
    args = parser.parse_args(argv)
    return run(apply_write=not args.preview)


if __name__ == "__main__":
    raise SystemExit(main())
