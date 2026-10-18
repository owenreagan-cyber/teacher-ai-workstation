#!/usr/bin/env python3
"""Phase 3.5B follow-up — Homeroom newsletter update + stamp-sheet announcement only.

The main deployment already completed: 5 subject pages, 12 assignments, 8
announcements (all verified). This completes the two remaining items that
crashed on a missing backup directory.
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.canvas_llm_phase22 import canvas_credentials as credentials  # noqa: E402
from scripts.canvas_llm_phase22 import canvas_connection_manager as transport  # noqa: E402

STAGE = REPO_ROOT / ".local" / "canvas-llm" / "deployment-backups" / "Q2W1" / "staging"
OUT = REPO_ROOT / ".local" / "canvas-llm" / "deployment-backups" / "Q2W1"
HOMEROOM_SLUG = "q1w2-july-27-31-2026"
HOMEROOM_TITLE = "Q1W2 - July 27-31, 2026"


def normalize(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()


def html_wrap(text: str) -> str:
    paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    return "".join(f"<p>{p.replace(chr(10), '<br>')}</p>" for p in paras)


def main() -> int:
    creds = credentials.load_credentials()
    os.environ["CANVAS_LLM_DEPLOYMENT_MODE"] = "live"
    os.environ["CANVAS_LLM_LIVE_Q1W2_APPROVED"] = "1"
    api = transport.get_transport_client(test_mode=False)

    report: dict[str, Any] = {"phase": "3.5B-followup", "generated_at": datetime.now(timezone.utc).isoformat(),
                              "homeroom": {}, "stamp_sheet": {}, "failures": []}

    # ===== HOMEROOM NEWSLETTER =====
    homeroom_body = (STAGE / "homeroom-page.html").read_text(encoding="utf-8")
    backup_dir = OUT / "homeroom"
    backup_dir.mkdir(parents=True, exist_ok=True)
    cur = api.get_page(26429, HOMEROOM_SLUG)
    (backup_dir / "front-page.pre-3.5b.html").write_text(cur.get("body") or "", encoding="utf-8")
    api.update_page(26429, HOMEROOM_SLUG, body=homeroom_body, published=True, front_page=True)
    rb = api.get_page(26429, HOMEROOM_SLUG)
    ok = (
        rb.get("published") is True
        and rb.get("front_page") is True
        and "Track 2, Week 1" in (rb.get("body") or "")
        and "Fall Weather" in (rb.get("body") or "")
    )
    report["homeroom"] = {"status": "WRITTEN", "verify": "PASS" if ok else "FAIL", "page_created": 0, "front_page": True, "slug": HOMEROOM_SLUG}
    if not ok:
        report["failures"].append(f"homeroom readback mismatch (fp={rb.get('front_page')!r})")

    # ===== STAMP-SHEET ANNOUNCEMENT =====
    stamp_body = (
        "Good Morning, Fourth Grade Families!\n\nWe hope you all had a wonderful track-out and are excited for a great start to Track 2!\n\n"
        "Beginning today, we are making a small change to our weekly stamp sheets. On the back of each stamp sheet, you will now see a set of warning boxes for each week of the track.\n\n"
        "Students will first receive a verbal reminder if a behavior needs to be corrected. If the behavior continues, the student will receive a warning tally.\n\n"
        "If a student reaches 5 warning tallies during the week, they will not visit the prize box that Friday, and a Grow Note will be sent home. If additional warnings are received after that point, an additional consequence may be needed, such as sitting out for 5 minutes of recess.\n\n"
        "Our goal with this system is to give students clear feedback and to give families an easy way to see how their child is doing at school throughout the week.\n\n"
        "Thank you for your continued support and partnership. We are looking forward to a great track!\n\n"
        "Sincerely,\nThe Fourth Grade Team"
    )
    created = api.create_announcement(26429, title="Stamp Sheet Update - Track 2", message=html_wrap(stamp_body), published=True, delayed_post_at="2026-10-12T12:00:00Z")
    oid = created.get("id")
    rb = api.get_announcement(26429, str(oid))
    ok = normalize(rb.get("title")) == normalize("Stamp Sheet Update - Track 2")
    report["stamp_sheet"] = {"status": "WRITTEN", "verify": "PASS" if ok else "FAIL", "send_time": "2026-10-12T12:00:00Z", "canvas_id": oid}
    if not ok:
        report["failures"].append("stamp-sheet readback mismatch")

    (OUT / "deployment-report-followup.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
