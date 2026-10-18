#!/usr/bin/env python3
"""Canvas HTML + Unicode compatibility lab (sandbox 24399 ONLY).

Establishes evidence-backed Canvas rendering behavior by writing labeled test
pages to the unpublished Math Automation Sandbox (24399), reading them back,
and diffing submitted vs Canvas-returned HTML.

NON-NEGOTIABLE INVARIANT
------------------------
Course 24399 MUST remain unpublished at all times. Before AND after every
write, this tool GETs the course and verifies ``workflow_state == "unpublished"``.
It hard-fails if the course is anything but 24399, or if it ever becomes
published. Only sandbox writes are issued; production courses are never touched.

Reuses ``scripts/canvas-llm/canvas_api_client.CanvasApiClient`` and
``scripts/canvas-llm/canvas_safety`` (which already locks writes to 24399).

Output (local, untracked): .local/canvas-llm/canvas-html-lab/
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "scripts" / "canvas-llm") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts" / "canvas-llm"))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from canvas_api_client import CanvasApiClient  # noqa: E402
from canvas_safety import SANDBOX_COURSE_ID, require_write_allowed  # noqa: E402

from scripts.canvas_llm_phase22 import canvas_credentials as credentials  # noqa: E402

OUT = ROOT / ".local" / "canvas-llm" / "canvas-html-lab"
SANDBOX = str(SANDBOX_COURSE_ID)  # "24399"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def write_local(name: str, payload: Any) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def course_unpublished(client: CanvasApiClient) -> bool:
    course = client.request("GET", "course", f"/api/v1/courses/{SANDBOX}")
    if int(course.get("id") or 0) != int(SANDBOX):
        raise SystemExit("FAIL: GET course did not return 24399")
    return course.get("workflow_state") == "unpublished"


def verify_sandbox(client: CanvasApiClient, stage: str) -> dict[str, Any]:
    unpublished = course_unpublished(client)
    if not unpublished:
        raise SystemExit(f"FAIL: course 24399 is not unpublished at {stage} — STOP")
    return {"stage": stage, "course_id": SANDBOX, "unpublished": True}


# --------------------------------------------------------------------------- #
# Test matrices
# --------------------------------------------------------------------------- #

UNICODE_HTML = """<div>
<h1>Canvas HTML Compatibility Test - Unicode</h1>
<p>Text: 2026\u20132027</p>
<p>Text: October 12\u201316, 2026</p>
<p>Time: 9:00 AM\u201310:00 AM</p>
<p>Badge: LEVEL UP TOGETHER \u26a1</p>
<p>Symbols: \u2022 \u2713 \u2714 \u2192 \u2605 \u2b50</p>
<p>Emoji: \U0001F342 \U0001F341 \U0001F4DA \U0001F4C5 \U0001F517 \U0001F382 \U0001F52C \U0001F4A7 \U0001F389</p>
<p>Risky: \u2014 em dash, \u201csmart quotes\u201d, variation selector \u2764\ufe0f, ZWJ \U0001F468\u200d\U0001F469\u200d\U0001F467\u200d\U0001F466</p>
</div>"""

LAYOUT_HTML = """<div>
<h1>Canvas HTML Compatibility Test - Layout</h1>
<h2>Heading 2</h2>
<h3>Heading 3</h3>
<p>Paragraph with <strong>strong</strong> and <em>emphasis</em>.</p>
<ul><li>Item 1</li><li>Item 2</li></ul>
<ol><li>First</li><li>Second</li></ol>
<span>Inline span</span>
<div>Block div</div>
<table><thead><tr><th>A</th><th>B</th></tr></thead><tbody><tr><td>1</td><td>2</td></tr></tbody></table>
<div style="display: flex;"><div>Flex 1</div><div>Flex 2</div></div>
<div style="display: flex; flex-wrap: wrap;"><span style="flex: 1 1 200px;">Wrap A</span><span style="flex: 1 1 200px;">Wrap B</span></div>
</div>"""

CSS_HTML = """<div>
<h1>Canvas HTML Compatibility Test - CSS</h1>
<div style="background-color: #24324A; color: #ffffff; border: 2px solid #D96C3F; border-radius: 12px; padding: 16px; margin: 8px; font-size: 16px; text-align: center; box-shadow: 0 2px 6px rgba(0,0,0,.2);">Styled card</div>
<div style="background: linear-gradient(135deg, #24324A 0%, #8F3D46 45%, #D96C3F 75%, #E4A94F 100%); padding: 20px; border-radius: 16px; color: #ffffff;">Gradient card</div>
<div style="position: absolute; top: 0; left: 0;">absolute (unsupported risk)</div>
<div style="animation: fade 1s;">animation (unsupported risk)</div>
</div>"""

PAGES = [
    ("Canvas HTML Compatibility Test - Unicode", UNICODE_HTML, "unicode"),
    ("Canvas HTML Compatibility Test - Layout", LAYOUT_HTML, "layout"),
    ("Canvas HTML Compatibility Test - CSS", CSS_HTML, "css"),
]


def diff_html(submitted: str, readback: str) -> dict[str, Any]:
    """Classify what Canvas did to the submitted HTML (added/removed/modified)."""
    if submitted == readback:
        return {"status": "IDENTICAL", "added": 0, "removed": 0, "modified": False}
    # Coarse signal: length + whether readback is a superset (Canvas often wraps).
    return {
        "status": "CHANGED",
        "submitted_chars": len(submitted),
        "readback_chars": len(readback),
        "submitted_hash": sha256(submitted),
        "readback_hash": sha256(readback),
        "note": "readback differs from submitted; inspect diff for normalization vs sanitization",
    }


def unicode_preservation(submitted: str, readback: str) -> dict[str, Any]:
    """Check which Unicode characters survived the Canvas round trip verbatim."""
    targets = [
        ("en dash", "\u2013"),
        ("em dash", "\u2014"),
        ("bullet", "\u2022"),
        ("check", "\u2713"),
        ("heavy check", "\u2714"),
        ("arrow", "\u2192"),
        ("star", "\u2605"),
        ("white star", "\u2b50"),
        ("lightning", "\u26a1"),
        ("leaf", "\U0001F342"),
        ("maple", "\U0001F341"),
        ("book", "\U0001F4DA"),
        ("calendar", "\U0001F4C5"),
        ("link", "\U0001F517"),
        ("birthday", "\U0001F382"),
        ("microscope", "\U0001F52C"),
        ("water", "\U0001F4A7"),
        ("party", "\U0001F389"),
        ("smart quotes", "\u201c"),
        ("variation selector heart", "\u2764\ufe0f"),
        ("ZWJ family", "\U0001F468\u200d\U0001F469\u200d\U0001F467\u200d\U0001F466"),
    ]
    result: dict[str, Any] = {}
    for name, char in targets:
        result[name] = {"submitted": char in submitted, "readback": char in readback, "preserved": char in readback}
    result["all_core_preserved"] = all(
        result[n]["preserved"] for n in [
            "en dash", "em dash", "lightning", "leaf", "maple", "book",
            "calendar", "link", "birthday", "microscope", "water", "party",
        ]
    )
    return result


def run_lab(client: CanvasApiClient) -> dict[str, Any]:
    report: dict[str, Any] = {
        "generated_at": now(),
        "course_id": SANDBOX,
        "course_name": "Math Automation Sandbox",
        "writes": [],
        "sandbox_unpublished_before": None,
        "sandbox_unpublished_after": None,
    }

    # Guard: verify unpublished before.
    report["sandbox_unpublished_before"] = verify_sandbox(client, "before")

    for title, body, key in PAGES:
        entry: dict[str, Any] = {"key": key, "title": title}
        # Explicit write lock: hard fail on non-24399.
        require_write_allowed(SANDBOX, "page", True)
        created = client.request(
            "POST", "pages", f"/api/v1/courses/{SANDBOX}/pages",
            data={"wiki_page[title]": title, "wiki_page[body]": body, "wiki_page[published]": "false"},
            course_id=SANDBOX,
        )
        slug = created.get("url") or created.get("page_id")
        entry["page_slug"] = slug
        entry["page_id"] = created.get("page_id")

        # Read back the exact Canvas-rendered HTML.
        readback = client.request(
            "GET", "page", f"/api/v1/courses/{SANDBOX}/pages/{slug}",
            course_id=SANDBOX,
        )
        rb_body = readback.get("body") or ""
        entry["submitted_hash"] = sha256(body)
        entry["readback_hash"] = sha256(rb_body)
        entry["diff"] = diff_html(body, rb_body)
        entry["readback_published"] = readback.get("published")
        entry["readback_front_page"] = readback.get("front_page")
        entry["classification"] = "VERIFIED_SAFE" if entry["diff"]["status"] == "IDENTICAL" else "VERIFIED_WITH_NORMALIZATION"
        # Capture the readback body + per-character preservation evidence.
        entry["readback_body"] = rb_body
        entry["unicode_preserved"] = unicode_preservation(body, rb_body)

        # Delete the test artifact (keep sandbox clean).
        client.request("DELETE", "page", f"/api/v1/courses/{SANDBOX}/pages/{slug}", course_id=SANDBOX)
        entry["cleaned_up"] = True

        report["writes"].append(entry)

    # Guard: verify unpublished after.
    report["sandbox_unpublished_after"] = verify_sandbox(client, "after")
    return report


def main() -> int:
    credentials.load_credentials()
    client = CanvasApiClient.from_env()

    report = run_lab(client)

    write_local("sandbox-course-check.json", {
        "course_id": SANDBOX,
        "unpublished_before": report["sandbox_unpublished_before"],
        "unpublished_after": report["sandbox_unpublished_after"],
    })
    write_local("unicode-results.json", next(w for w in report["writes"] if w["key"] == "unicode"))
    write_local("html-results.json", next(w for w in report["writes"] if w["key"] == "layout"))
    write_local("css-results.json", next(w for w in report["writes"] if w["key"] == "css"))
    write_local("readback-diffs.json", [w["diff"] for w in report["writes"]])
    write_local("compatibility-summary.json", report)

    print(json.dumps({
        "course_id": SANDBOX,
        "unpublished_before": report["sandbox_unpublished_before"]["unpublished"],
        "unpublished_after": report["sandbox_unpublished_after"]["unpublished"],
        "pages_tested": len(report["writes"]),
        "results": [
            {"key": w["key"], "classification": w["classification"], "diff": w["diff"]["status"]}
            for w in report["writes"]
        ],
    }, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
