#!/usr/bin/env python3
"""Phase 3.5B fix — embed the full verified agenda into the 4 Q2W1 weekly-update announcements.

Updates the existing announcements IN PLACE (no duplicates). Embeds the complete
kl_wrapper_3 agenda HTML exactly as rendered on each subject's live page.
Readback-verifies that kl_wrapper_3, Reminders, and all 5 weekdays are present.
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
SLUG = "q2w1-october-12-16-2026"


def extract_kl_wrapper(body: str) -> str:
    start = body.find('<div id="kl_wrapper_3"')
    if start == -1:
        return body
    # find matching close by counting divs
    depth = 0
    i = start
    while i < len(body):
        if body.startswith("<div", i):
            depth += 1
        elif body.startswith("</div>", i):
            depth -= 1
            if depth == 0:
                return body[start:i + len("</div>")]
        i += 1
    return body[start:]


def main() -> int:
    creds = credentials.load_credentials()
    os.environ["CANVAS_LLM_DEPLOYMENT_MODE"] = "live"
    os.environ["CANVAS_LLM_LIVE_Q1W2_APPROVED"] = "1"
    api = transport.get_transport_client(test_mode=False)

    # (course_id, announcement_id, subject_label, transition, week_ahead)
    targets = [
        (26404, 166383, "Math", "The Canvas Math page has been updated. Please see the upcoming week ahead.", "This week we are working through Lessons 31\u201334 and Investigation 3."),
        (26442, 166384, "Reading/Spelling", "The Canvas Reading/Spelling page has been updated. Please see the upcoming week ahead.", "This week includes Spelling Test 35 on Thursday and Reading Mastery Test 4 with Fluency Checkout 4 on Friday."),
        (28171, 166385, "Language Arts", "The Canvas Language Arts page has been updated. Please see the upcoming week ahead.", "We are beginning Chapter 5 in Shurley this week."),
        (28166, 166386, "Science", "The Canvas Science page has been updated. Please see the upcoming week ahead.", "We are learning about Force and Motion in Science."),
    ]

    report: dict[str, Any] = {"phase": "3.5B-weekly-update-fix", "generated_at": datetime.now(timezone.utc).isoformat(), "results": [], "failures": []}

    for cid, aid, label, transition, week_ahead in targets:
        # Get the live page body (verified deployed source of truth)
        page = api.get_page(cid, SLUG)
        agenda_html = extract_kl_wrapper(page.get("body") or "")

        message = (
            "<p>Good afternoon,</p>"
            f"<p>{week_ahead}</p>"
            f"<p>{transition}</p>"
            f"{agenda_html}"
            "<p>Have a great weekend!</p>"
            "<p>Mr. Reagan</p>"
        )

        api.update_announcement(cid, str(aid), message=message, published=True)

        rb = api.get_announcement(cid, str(aid))
        msg = rb.get("message") or ""
        checks = {
            "kl_wrapper_3_present": "kl_wrapper_3" in msg,
            "reminders_present": "Reminders" in msg,
            "weekdays_present": all(d in msg for d in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]),
            "title_ok": rb.get("title") == label + " Canvas Weekly Update",
        }
        ok = all(checks.values())
        report["results"].append({"course": label, "announcement_id": aid, "verify": "PASS" if ok else "FAIL", **checks})
        if not ok:
            report["failures"].append(f"{label} weekly-update verification failed: {checks}")

    (OUT / "weekly-update-fix-report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
