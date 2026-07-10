#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from canvas_api_client import CanvasApiClient
from canvas_safety import (
    REFERENCE_COURSE_IDS,
    SANDBOX_COURSE_ID,
    deletion_is_temporary,
    require_local_output_path,
    require_write_allowed,
)
from canvas_sanitizer import sanitize_value

ROOT = Path(__file__).resolve().parents[2]
RUN_ROOT = ROOT / ".local/canvas-llm/sandbox-learning-runs/phase-21"
RAW_ROOT = RUN_ROOT / "raw"
LEDGER_PATH = RUN_ROOT / "artifact-ledger.json"
QW_RE = re.compile(r"\bQ([1-4])\s*W(\d{1,2})\b|q([1-4])w(\d{1,2})", re.IGNORECASE)


def now_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def write_json(path: Path, payload: Any, canvas_base_url: str | None = None) -> None:
    require_local_output_path(path, RUN_ROOT)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(sanitize_value(payload, canvas_base_url), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_raw_json(path: Path, payload: Any) -> None:
    require_local_output_path(path, RUN_ROOT)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def safe_course_ids() -> list[str]:
    return [SANDBOX_COURSE_ID, *sorted(REFERENCE_COURSE_IDS)]


def reference_course_ids() -> list[str]:
    return sorted(REFERENCE_COURSE_IDS)


def course_label(course_id: str) -> str:
    labels = {
        "24399": "Owen-designated demo sandbox",
        "21944": "15-ELA4PagesQ4W1 reference",
        "21957": "15-MAT5PagesQ4W1 reference",
        "21919": "15-REA4PagesQ4W1 reference",
    }
    return labels.get(str(course_id), "approved course")


def summarize_html(body: str | None) -> dict[str, Any]:
    body = body or ""
    classes = sorted(set(re.findall(r'class=["\']([^"\']+)["\']', body)))[:20]
    ids = sorted(set(re.findall(r'id=["\']([^"\']+)["\']', body)))[:20]
    headings = re.findall(r"<h[1-4][^>]*>(.*?)</h[1-4]>", body, flags=re.IGNORECASE | re.DOTALL)
    return {
        "length": len(body),
        "has_tables": "<table" in body.lower(),
        "has_images": "<img" in body.lower(),
        "has_iframes": "<iframe" in body.lower(),
        "class_hints": classes,
        "id_hints": ids,
        "heading_count": len(headings),
    }


def qxwy_candidates(pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates = []
    for page in pages:
        title = str(page.get("title") or "")
        url = str(page.get("url") or "")
        if QW_RE.search(title) or QW_RE.search(url):
            candidates.append({
                "title": title,
                "slug": url,
                "published": page.get("published"),
                "front_page": page.get("front_page"),
            })
    return candidates


def run_inventory(client: CanvasApiClient, course_ids: list[str] | None = None, mode: str = "inventory") -> dict[str, Any]:
    selected_course_ids = course_ids or safe_course_ids()
    inventory: dict[str, Any] = {
        "generated_at": now_stamp(),
        "mode": mode,
        "stable_rules": [
            "Canvas writes are locked to course 24399.",
            "Reference courses 21944, 21957, and 21919 are read-only.",
            "Q/W weeks reset each quarter and track.",
            "Production weekly pages are preloaded and updated, not created.",
        ],
        "hypotheses": [],
        "courses": {},
    }
    raw_dir = RAW_ROOT / now_stamp()
    for course_id in selected_course_ids:
        course: dict[str, Any] = {"course_id": course_id, "label": course_label(course_id)}
        course["tabs"] = client.get_paginated("tabs", f"/api/v1/courses/{course_id}/tabs", course_id=course_id)
        course["pages"] = client.get_paginated(
            "pages",
            f"/api/v1/courses/{course_id}/pages",
            params={"include[]": ["body"]},
            course_id=course_id,
        )
        course["assignments"] = client.get_paginated("assignments", f"/api/v1/courses/{course_id}/assignments", course_id=course_id)
        course["announcements"] = client.get_paginated(
            "announcements",
            "/api/v1/announcements",
            params={"context_codes[]": [f"course_{course_id}"]},
            course_id=course_id,
        )
        course["files"] = client.get_paginated("files", f"/api/v1/courses/{course_id}/files", course_id=course_id)
        modules = client.get_paginated("modules", f"/api/v1/courses/{course_id}/modules", course_id=course_id)
        for module in modules:
            module_id = module.get("id")
            if module_id:
                module["items"] = client.get_paginated(
                    "module_items",
                    f"/api/v1/courses/{course_id}/modules/{module_id}/items",
                    course_id=course_id,
                )
        course["modules"] = modules
        write_raw_json(raw_dir / f"course-{course_id}.json", course)

        pages = course.get("pages") if isinstance(course.get("pages"), list) else []
        candidates = qxwy_candidates(pages)
        weekly_details = []
        for candidate in candidates[:3]:
            slug = candidate.get("slug")
            if slug:
                detail = client.request(
                    "GET",
                    "page",
                    f"/api/v1/courses/{course_id}/pages/{slug}",
                    params={"include[]": ["body"]},
                    course_id=course_id,
                )
                weekly_details.append({
                    "title": detail.get("title"),
                    "slug": detail.get("url"),
                    "published": detail.get("published"),
                    "front_page": detail.get("front_page"),
                    "html_features": summarize_html(detail.get("body")),
                })
        inventory["courses"][course_id] = {
            "label": course_label(course_id),
            "tabs_count": len(course["tabs"]),
            "pages_count": len(pages),
            "assignments_count": len(course["assignments"]),
            "announcements_count": len(course["announcements"]),
            "files_count": len(course["files"]),
            "modules_count": len(modules),
            "qxwy_page_candidates": candidates,
            "weekly_page_html_hints": weekly_details,
        }
        if weekly_details:
            inventory["hypotheses"].append({
                "course_id": course_id,
                "hypothesis": "Weekly page editable regions may be inferred from repeated shell wrappers.",
                "support": "safe HTML feature summaries from candidate QxWy pages",
            })
    write_json(RUN_ROOT / "findings.json", inventory, client.base_url)
    build_learning_loop(inventory, client.base_url)
    return inventory


def build_learning_loop(findings: dict[str, Any], canvas_base_url: str | None) -> None:
    questions = []
    for course_id, course in findings.get("courses", {}).items():
        candidates = course.get("qxwy_page_candidates") or []
        questions.extend([
            question(course_id, "Which QxWy pages exist?", "answered" if candidates else "unanswered", candidates),
            question(course_id, "Which page is front page?", "needs_probe", "Use safe page fields from inventory or page detail."),
            question(course_id, "Which page shells share common HTML wrappers?", "answered" if course.get("weekly_page_html_hints") else "needs_probe", course.get("weekly_page_html_hints")),
            question(course_id, "Which module items point to QxWy pages?", "needs_probe", "Cross-check module item page_url against QxWy candidates."),
            question(course_id, "Are pages published?", "answered" if candidates else "unanswered", [{"title": item.get("title"), "published": item.get("published")} for item in candidates]),
            question(course_id, "Are there subject-specific shells for ELA, Math, Reading?", "needs_probe", "Compare reference-course shell hints without inventing unsupported findings."),
            question(course_id, "Are there repeated placeholder phrases?", "needs_probe", "Search only sanitized page body summaries or approved local inventory."),
            question(course_id, "What should be tested next in sandbox?", "needs_probe", "Recommend only safe probes in course 24399."),
        ])
    next_actions = [
        {"level": "PASS", "action": "Run --mode inventory to refresh safe course structure."},
        {"level": "PASS", "action": "Run --mode reference-inventory to refresh read-only reference course structure only."},
        {"level": "PASS", "action": "Run --mode questions to regenerate the backlog from findings."},
        {"level": "WARN", "action": "Run --mode existing-page-dry-run before any sandbox page update experiment."},
        {"level": "BLOCKED", "action": "Do not run --mode experiment unless CANVAS_BASE_URL, CANVAS_TOKEN, and --allow-writes are intentionally supplied."},
    ]
    write_json(RUN_ROOT / "questions.json", {"generated_at": now_stamp(), "questions": questions}, canvas_base_url)
    write_json(RUN_ROOT / "next-actions.json", {"generated_at": now_stamp(), "next_actions": next_actions}, canvas_base_url)


def question(course_id: str, text: str, status: str, evidence: Any) -> dict[str, Any]:
    return {"course_id": course_id, "question": text, "status": status, "evidence": evidence}


def run_questions() -> dict[str, Any]:
    findings_path = RUN_ROOT / "findings.json"
    if not findings_path.exists():
        raise SystemExit("WARN: no findings.json exists yet; run --mode inventory first")
    findings = json.loads(findings_path.read_text(encoding="utf-8"))
    build_learning_loop(findings, os.environ.get("CANVAS_BASE_URL"))
    return {"status": "PASS", "message": "question backlog regenerated"}


def load_ledger() -> list[dict[str, Any]]:
    if not LEDGER_PATH.exists():
        return []
    return json.loads(LEDGER_PATH.read_text(encoding="utf-8"))


def save_ledger(ledger: list[dict[str, Any]], base_url: str | None) -> None:
    write_json(LEDGER_PATH, ledger, base_url)


def ledger_add(ledger: list[dict[str, Any]], artifact_type: str, title: str, artifact_id: Any, cleanup_status: str) -> None:
    ledger.append({
        "created_at": now_stamp(),
        "course_id": SANDBOX_COURSE_ID,
        "artifact_type": artifact_type,
        "title": title,
        "id": artifact_id,
        "cleanup_status": cleanup_status,
    })


def run_experiment(client: CanvasApiClient, allow_writes: bool) -> dict[str, Any]:
    ledger = load_ledger()
    title_prefix = "TAW Phase 21 Temporary "
    artifacts = [
        ("page", f"{title_prefix}Page {now_stamp()}"),
        ("assignment", f"{title_prefix}Assignment {now_stamp()}"),
        ("announcement", f"{title_prefix}Announcement {now_stamp()}"),
        ("module", f"{title_prefix}Module {now_stamp()}"),
    ]
    for artifact_type, title in artifacts:
        require_write_allowed(SANDBOX_COURSE_ID, artifact_type, allow_writes)
        try:
            if artifact_type == "page":
                created = client.request("POST", "pages", f"/api/v1/courses/{SANDBOX_COURSE_ID}/pages", data={"wiki_page[title]": title, "wiki_page[body]": "<p>Temporary Phase 21 sandbox test.</p>", "wiki_page[published]": "false"}, course_id=SANDBOX_COURSE_ID)
                ledger_add(ledger, artifact_type, title, created.get("url") or created.get("page_id"), "created")
                client.request("PUT", "page", f"/api/v1/courses/{SANDBOX_COURSE_ID}/pages/{created.get('url')}", data={"wiki_page[published]": "true"}, course_id=SANDBOX_COURSE_ID)
                client.request("PUT", "page", f"/api/v1/courses/{SANDBOX_COURSE_ID}/pages/{created.get('url')}", data={"wiki_page[published]": "false"}, course_id=SANDBOX_COURSE_ID)
                client.request("DELETE", "page", f"/api/v1/courses/{SANDBOX_COURSE_ID}/pages/{created.get('url')}", course_id=SANDBOX_COURSE_ID)
                ledger[-1]["cleanup_status"] = "deleted"
            elif artifact_type == "assignment":
                created = client.request("POST", "assignments", f"/api/v1/courses/{SANDBOX_COURSE_ID}/assignments", data={"assignment[name]": title, "assignment[published]": "false"}, course_id=SANDBOX_COURSE_ID)
                ledger_add(ledger, artifact_type, title, created.get("id"), "created")
                client.request("PUT", "assignments", f"/api/v1/courses/{SANDBOX_COURSE_ID}/assignments/{created.get('id')}", data={"assignment[published]": "true"}, course_id=SANDBOX_COURSE_ID)
                client.request("PUT", "assignments", f"/api/v1/courses/{SANDBOX_COURSE_ID}/assignments/{created.get('id')}", data={"assignment[published]": "false"}, course_id=SANDBOX_COURSE_ID)
                client.request("DELETE", "assignments", f"/api/v1/courses/{SANDBOX_COURSE_ID}/assignments/{created.get('id')}", course_id=SANDBOX_COURSE_ID)
                ledger[-1]["cleanup_status"] = "deleted"
            elif artifact_type == "announcement":
                created = client.request(
                    "POST",
                    "announcements",
                    f"/api/v1/courses/{SANDBOX_COURSE_ID}/discussion_topics",
                    data={
                        "discussion_topic[title]": title,
                        "discussion_topic[message]": "Temporary Phase 21 sandbox test.",
                        "discussion_topic[is_announcement]": "true",
                        "discussion_topic[published]": "false",
                    },
                    course_id=SANDBOX_COURSE_ID,
                )
                ledger_add(ledger, artifact_type, title, created.get("id"), "created")
                client.request("DELETE", "announcements", f"/api/v1/courses/{SANDBOX_COURSE_ID}/discussion_topics/{created.get('id')}", course_id=SANDBOX_COURSE_ID)
                ledger[-1]["cleanup_status"] = "deleted"
            elif artifact_type == "module":
                created = client.request("POST", "modules", f"/api/v1/courses/{SANDBOX_COURSE_ID}/modules", data={"module[name]": title, "module[published]": "false"}, course_id=SANDBOX_COURSE_ID)
                ledger_add(ledger, artifact_type, title, created.get("id"), "created")
                client.request("DELETE", "modules", f"/api/v1/courses/{SANDBOX_COURSE_ID}/modules/{created.get('id')}", course_id=SANDBOX_COURSE_ID)
                ledger[-1]["cleanup_status"] = "deleted"
        except Exception as exc:
            ledger_add(ledger, artifact_type, title, None, f"WARN/BLOCKED cleanup or experiment failure: {exc}")
    save_ledger(ledger, client.base_url)
    return {"status": "PASS_WITH_WARN_IF_LEDGER_HAS_FAILURES", "ledger": LEDGER_PATH.as_posix()}


def run_existing_page_dry_run() -> dict[str, Any]:
    findings_path = RUN_ROOT / "findings.json"
    if not findings_path.exists():
        raise SystemExit("WARN: no findings.json exists yet; run --mode inventory first")
    findings = json.loads(findings_path.read_text(encoding="utf-8"))
    sandbox = findings.get("courses", {}).get(SANDBOX_COURSE_ID, {})
    candidates = sandbox.get("qxwy_page_candidates") or []
    if not candidates:
        raise SystemExit("WARN: no sandbox QxWy candidate page found for dry run")
    candidate = candidates[0]
    plan = {
        "mode": "existing-page-dry-run",
        "course_id": SANDBOX_COURSE_ID,
        "candidate": candidate,
        "dry_run_only": True,
        "statement": "dry run only",
        "update_plan": [
            "Fetch existing page body only through allowlisted page endpoint.",
            "Detect repeated shell wrappers and preserve header/footer/table scaffolding.",
            "Replace only likely editable lesson-content region.",
            "Do not create a real weekly page; production pages are preloaded and updated.",
        ],
    }
    write_json(RUN_ROOT / "existing-page-dry-run-plan.json", plan, os.environ.get("CANVAS_BASE_URL"))
    return plan


def run_cleanup(client: CanvasApiClient, allow_writes: bool) -> dict[str, Any]:
    ledger = load_ledger()
    results = []
    for item in ledger:
        if item.get("cleanup_status") == "deleted":
            continue
        if not deletion_is_temporary(item):
            results.append({"level": "BLOCKED", "item": item, "message": "deletion target is not recognized as temporary test artifact"})
            continue
        artifact_type = str(item.get("artifact_type"))
        artifact_id = item.get("id")
        require_write_allowed(SANDBOX_COURSE_ID, artifact_type, allow_writes)
        try:
            if artifact_type == "page":
                client.request("DELETE", "page", f"/api/v1/courses/{SANDBOX_COURSE_ID}/pages/{artifact_id}", course_id=SANDBOX_COURSE_ID)
            elif artifact_type == "assignment":
                client.request("DELETE", "assignments", f"/api/v1/courses/{SANDBOX_COURSE_ID}/assignments/{artifact_id}", course_id=SANDBOX_COURSE_ID)
            elif artifact_type == "announcement":
                client.request("DELETE", "announcements", f"/api/v1/courses/{SANDBOX_COURSE_ID}/discussion_topics/{artifact_id}", course_id=SANDBOX_COURSE_ID)
            elif artifact_type == "module":
                client.request("DELETE", "modules", f"/api/v1/courses/{SANDBOX_COURSE_ID}/modules/{artifact_id}", course_id=SANDBOX_COURSE_ID)
            else:
                results.append({"level": "BLOCKED", "item": item, "message": f"unsupported cleanup artifact type: {artifact_type}"})
                continue
            item["cleanup_status"] = "deleted"
            item["cleaned_at"] = now_stamp()
            results.append({"level": "PASS", "item": item, "message": "temporary artifact deleted"})
        except Exception as exc:
            item["cleanup_status"] = f"WARN cleanup failed: {exc}"
            results.append({"level": "WARN", "item": item, "message": "cleanup failed; artifact may need manual review"})
    save_ledger(ledger, client.base_url)
    write_json(RUN_ROOT / "cleanup-report.json", {"generated_at": now_stamp(), "results": results}, client.base_url)
    return {"status": "PASS" if not results else "WARN", "results": results}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Canvas LLM Phase 21 autonomous sandbox learning agent")
    parser.add_argument(
        "--mode",
        choices=[
            "inventory",
            "reference-inventory",
            "questions",
            "experiment",
            "existing-page-dry-run",
            "cleanup",
            "phase21c-select-existing-page",
            "phase21c-learning-expansion",
            "phase21c-existing-page-write-preview",
        ],
        default="inventory",
    )
    parser.add_argument("--allow-writes", action="store_true", help="Required for experiment and cleanup Canvas writes")
    return parser.parse_args()


# ---- Phase 21C: existing-page selector hardening + gated sandbox write helpers ----

PHASE_21C_SAFE_WRITE_MARKER = "<!-- teacher-ai-workstation phase-21c sandbox-write-marker -->"
PHASE_21C_APPROVAL_PHRASE = "PHASE_21C_SANDBOX_EXISTING_PAGE_WRITE_APPROVED"


def _phase21c_load_findings() -> dict[str, Any]:
    findings_path = RUN_ROOT / "findings.json"
    if not findings_path.exists():
        raise SystemExit("WARN: no findings.json exists yet; run --mode inventory first")
    return json.loads(findings_path.read_text(encoding="utf-8"))


def _phase21c_qw_score(page: dict[str, Any]) -> tuple[int, str, str]:
    title = str(page.get("title", "")).upper()
    slug = str(page.get("slug", "")).lower()
    published = bool(page.get("published", False))
    front_page = bool(page.get("front_page", False))

    penalty = 0

    # Prefer harmless unpublished normal weekly pages.
    if published:
        penalty += 10
    if front_page:
        penalty += 100
    if "END" in title:
        penalty += 100
    if title == "Q4W10" or slug == "q4w10":
        penalty += 50
    if "COPY" in title:
        penalty += 25

    return (penalty, title, slug)


def phase21c_select_sandbox_existing_page() -> dict[str, Any]:
    findings = _phase21c_load_findings()
    sandbox = findings.get("courses", {}).get(SANDBOX_COURSE_ID, {})
    candidates = sandbox.get("qxwy_page_candidates") or []

    safe: list[dict[str, Any]] = []
    for page in candidates:
        title = str(page.get("title", "")).upper()
        slug = str(page.get("slug", "")).lower()

        if not title.startswith("Q"):
            continue
        if "W" not in title:
            continue
        if "END" in title:
            continue
        if not slug:
            continue

        safe.append(page)

    safe = sorted(safe, key=_phase21c_qw_score)

    result = {
        "mode": "phase21c-select-existing-page",
        "course_id": SANDBOX_COURSE_ID,
        "candidate_count": len(candidates),
        "safe_candidate_count": len(safe),
        "selected": safe[0] if safe else None,
        "selection_rule": [
            "course_id must be 24399",
            "page must already exist",
            "title must look like QxWy",
            "prefer unpublished pages",
            "avoid front page",
            "avoid QxEND special pages",
            "avoid Q4W10 unless explicitly requested",
            "avoid Copy pages when a normal page exists",
        ],
        "writes_approved": False,
    }

    write_json(RUN_ROOT / "phase21c-selected-existing-page.json", result, os.environ.get("CANVAS_BASE_URL"))
    return result


def phase21c_assignment_learning_inventory() -> dict[str, Any]:
    findings = _phase21c_load_findings()
    courses = findings.get("courses", {})

    result = {
        "mode": "phase21c-assignment-announcement-attachment-learning",
        "generated_from": "safe inventory summaries",
        "rules_to_learn_next": [
            "Math lesson number to assignment naming",
            "Math Power Up to practice attachment/resource mapping",
            "Fact Test to practice/review assignment mapping",
            "Reading lesson to comprehension letter mapping",
            "Reading page number to assignment/page body mapping",
            "Announcement update pattern for test date changes",
            "Attachment/file link pattern for weekly page resources",
        ],
        "course_summaries": {},
        "writes_approved": False,
    }

    for course_id, course in courses.items():
        result["course_summaries"][course_id] = {
            "label": course.get("label"),
            "assignments_count": course.get("assignments_count"),
            "files_count": course.get("files_count"),
            "announcements_count": course.get("announcements_count"),
            "pages_count": course.get("pages_count"),
            "modules_count": course.get("modules_count"),
        }

    write_json(RUN_ROOT / "phase21c-learning-expansion-plan.json", result, os.environ.get("CANVAS_BASE_URL"))
    return result


def phase21c_existing_page_write_preview() -> dict[str, Any]:
    selected_result = phase21c_select_sandbox_existing_page()
    selected_page = selected_result.get("selected")

    result = {
        "mode": "phase21c-existing-page-write-preview",
        "course_id": SANDBOX_COURSE_ID,
        "selected": selected_page,
        "operation": "update existing sandbox page body",
        "writes_approved": False,
        "required_write_gates": [
            "--allow-writes",
            "--mode phase21c-existing-page-write",
            f"target course must be {SANDBOX_COURSE_ID}",
            "target page slug must match selected existing page",
            f"approval phrase must be {PHASE_21C_APPROVAL_PHRASE}",
        ],
        "preview_body_marker": PHASE_21C_SAFE_WRITE_MARKER,
        "rollback": [
            "restore previous body from local pre-write snapshot",
            "remove phase-21c sandbox-write-marker",
            "do not touch production or reference courses",
        ],
    }

    write_json(RUN_ROOT / "phase21c-existing-page-write-preview.json", result, os.environ.get("CANVAS_BASE_URL"))
    return result


def main() -> int:
    args = parse_args()

    if args.mode in {"experiment", "cleanup"} and not args.allow_writes:
        raise SystemExit("BLOCKED: --mode experiment/cleanup requires --allow-writes")

    if args.mode == "questions":
        result = run_questions()
    elif args.mode == "existing-page-dry-run":
        result = run_existing_page_dry_run()
    elif args.mode == "phase21c-select-existing-page":
        result = phase21c_select_sandbox_existing_page()
    elif args.mode == "phase21c-learning-expansion":
        result = phase21c_assignment_learning_inventory()
    elif args.mode == "phase21c-existing-page-write-preview":
        result = phase21c_existing_page_write_preview()
    else:
        client = CanvasApiClient.from_env()

        if args.mode == "inventory":
            result = run_inventory(client, safe_course_ids(), "inventory")
        elif args.mode == "reference-inventory":
            result = run_inventory(client, reference_course_ids(), "reference-inventory")
        elif args.mode == "experiment":
            result = run_experiment(client, args.allow_writes)
        elif args.mode == "cleanup":
            result = run_cleanup(client, args.allow_writes)
        else:
            raise SystemExit(f"FAIL: unsupported mode {args.mode}")

    print(json.dumps(sanitize_value(result, os.environ.get("CANVAS_BASE_URL")), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
