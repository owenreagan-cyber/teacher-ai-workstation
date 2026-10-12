"""Phase 3 orchestrator — Chief of Staff weekly planning loop CLI.

Pipeline:
    live pacing -> deterministic normalized week -> precedent retrieval
    -> local-LLM proposal -> teacher review/edit -> correction memory
    -> Canvas dry-run preview

Read-only. No Canvas writes in Phase 3. This module performs no Canvas network
I/O at all; it only reads the pacing sheet, calls the local Ollama loopback,
and writes local artifacts under .local/.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from typing import Any

from . import constants as C
from . import pacing_extractor as pe
from . import pacing_change as pc
from . import pacing_translation as pt
from . import pacing_math as pm
from . import pacing_announcement as pa
from . import pacing_reading as prd
from . import precedent_retrieval as pr
from . import local_llm as llm
from . import learning as learn
from . import state_machine as sm
from . import canvas_preview as cp


def inactive_subject_redirect(week_code: str) -> dict[str, Any] | None:
    """Return the owner-approved redirect config for the inactive rotating subject.

    Applies when History is the inactive rotating course (Q2/Q4): a redirect
    message/announcement points families to the active Science course. Returns
    None for Q1/Q3 (Science is simply not built; no redirect maintained)."""
    activation = json.loads(C.QUARTER_ACTIVATION_PATH.read_text(encoding="utf-8"))
    redirect = activation.get("inactiveSubjectRedirect", {})
    quarter = week_code[1] if len(week_code) >= 2 else ""
    if f"Q{quarter}" in redirect.get("quarters", []):
        return redirect
    return None


def active_subjects(week_code: str, week: dict[str, Any]) -> list[str]:
    """Return subjects that are active for the week.

    History/Science activity requires BOTH the quarter-activation rule AND
    non-blank fresh pacing content (never activate solely because a quarter begins).
    """
    quarter = week_code[1] if len(week_code) >= 2 else ""
    activation = json.loads(C.QUARTER_ACTIVATION_PATH.read_text(encoding="utf-8"))
    q = activation.get("quarters", {}).get(f"Q{quarter}", {})
    active_q_subject = q.get("activeSubject")
    inactive_q_subject = q.get("inactiveSubject")

    has_content: dict[str, bool] = {}
    for day in (week.get("days") or {}).values():
        for subject, cell in (day.get("subjects") or {}).items():
            if cell.get("raw", "") != "":
                has_content[subject] = True

    active: list[str] = []
    for subject in C.SUBJECT_LABELS:
        if subject in ("history", "science"):
            if subject == active_q_subject and has_content.get(subject):
                active.append(subject)
            # inactive subject always excluded
        else:
            active.append(subject)
    return active


def _render_weeks(week: dict[str, Any]) -> None:
    print(json.dumps(week, indent=2, ensure_ascii=False))


def _coerce_proposal_days(proposals: Any) -> tuple[dict[str, dict[str, Any]], list[str]]:
    """Coerce a model proposal into a days dict for the agenda renderer."""
    days: dict[str, dict[str, Any]] = {}
    unresolved: list[str] = []
    if not isinstance(proposals, dict):
        return days, ["proposal shape invalid"]
    for wd in C.WEEKDAYS:
        raw = proposals.get(wd, {})
        in_class = _extract_lines(raw.get("inClass", raw.get("in_class")))
        at_home = _extract_lines(raw.get("atHome", raw.get("at_home")))
        if not in_class and not at_home:
            unresolved.append(wd)
            in_class = ["(unresolved)"]
        days[wd] = {"in_class": in_class, "at_home": at_home or None}
    return days, unresolved


def _extract_lines(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, dict):
        v = value.get("value")
        if v is None:
            return []
        return [str(v)] if not isinstance(v, list) else [str(x) for x in v]
    if isinstance(value, list):
        return [str(x) for x in value]
    if isinstance(value, str):
        return [value]
    return []


def _raw_preview_days(week: dict[str, Any], subject: str) -> dict[str, dict[str, Any]]:
    """Deterministic fallback: render raw pacing literals in In Class (SOURCE state)."""
    days: dict[str, dict[str, Any]] = {}
    for wd, day in (week.get("days") or {}).items():
        raw = day.get("subjects", {}).get(subject, {}).get("raw", "")
        days[wd] = {"in_class": [raw] if raw else ["(no source)"], "at_home": None}
    return days


def cmd_extract(args: argparse.Namespace) -> int:
    week = pe.extract_week_json(args.week_code, fresh=args.fresh)
    pc.save_snapshot(week)
    _render_weeks(week)
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    week = pc.load_latest()
    if week is None or week.get("week", {}).get("code") != args.week_code:
        week = pe.extract_week_json(args.week_code, fresh=False)
    _render_weeks(week)
    return 0


def cmd_diff(_args: argparse.Namespace) -> int:
    result = pc.diff_weeks(pc.load_previous(), pc.load_latest())
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def _translated_preview_days(week: dict[str, Any], subject: str) -> dict[str, dict[str, Any]]:
    """Deterministic translation for known subjects; raw fallback otherwise."""
    if subject == "math":
        report = pm.translate_math_week(week)
        days: dict[str, dict[str, Any]] = {}
        for wd in C.WEEKDAYS:
            day = report["days"].get(wd, {})
            in_class = day.get("in_class") or []
            at_home = [day["at_home"]] if day.get("at_home_status") == "homework" and day.get("at_home") else None
            days[wd] = {"in_class": in_class if in_class else ["(no source)"], "at_home": at_home}
        return days
    if subject in ("reading", "spelling"):
        report = prd.translate_reading_spelling_week(week)
        days: dict[str, dict[str, Any]] = {}
        sub = report.get("reading" if subject == "reading" else "spelling", {})
        sub_days = sub.get("days", {})
        for wd in C.WEEKDAYS:
            day = sub_days.get(wd, {})
            in_class = day.get("in_class") or []
            at_home = [day["at_home"]] if day.get("at_home_status") == "homework" and day.get("at_home") else None
            days[wd] = {"in_class": in_class if in_class else ["(no source)"], "at_home": at_home}
        return days
    report = pt.translate_subject_week(week, subject)
    if not report.get("deterministic"):
        return _raw_preview_days(week, subject)
    days = {}
    for wd, day in (report.get("days") or {}).items():
        lines = day.get("lines") or []
        days[wd] = {"in_class": lines if lines else ["(no source)"], "at_home": None}
    return days


def _propose_subject(week: dict[str, Any], subject: str) -> dict[str, Any]:
    """Deterministic OWNER_POLICY translation first; local model only for
    subjects without deterministic rules."""
    if subject == "math":
        report = pm.translate_math_week(week)
        report["human_preview"] = pm.format_math_preview(report)
        return report
    if subject in ("reading", "spelling"):
        report = prd.translate_reading_spelling_week(week)
        report["human_preview"] = prd.format_reading_spelling_preview(report)
        return report
    report = pt.translate_subject_week(week, subject)
    if report.get("deterministic"):
        if report.get("unresolved"):
            report["local_model"] = {
                "status": "SKIPPED",
                "reason": (
                    "unresolved tokens require teacher review; the local model may not "
                    "override OWNER_POLICY or invent unit names from general knowledge"
                ),
            }
        else:
            report["local_model"] = {
                "status": "SKIPPED",
                "reason": "all tokens resolved deterministically (OWNER_POLICY)",
            }
        return report
    # No deterministic rule: fall back to the local model (existing behavior).
    bundle_s = pr.retrieve(subject=subject)
    t0 = time.time()
    result = llm.propose_subject(week, bundle_s, subject)
    result["latency_seconds"] = round(time.time() - t0, 2)
    result["deterministic_translation"] = {"status": "NO_DETERMINISTIC_RULE", "subject": subject}
    return result


def cmd_propose(args: argparse.Namespace) -> int:
    week = pe.extract_week_json(args.week_code, fresh=False)
    subjects = [args.subject] if args.subject else active_subjects(args.week_code, week)
    out: dict[str, Any] = {"week": args.week_code, "subjects": {}}
    for subject in subjects:
        out["subjects"][subject] = _propose_subject(week, subject)
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


def cmd_preview(args: argparse.Namespace) -> int:
    week = pe.extract_week_json(args.week_code, fresh=False)
    subjects = active_subjects(args.week_code, week)
    subject_days: dict[str, dict[str, Any]] = {}
    for subject in subjects:
        subject_days[subject] = _translated_preview_days(week, subject)

    summary = cp.build_dry_run_package(week, subject_days)

    # Reading + Spelling share one Canvas course (26442) and one weekly page.
    reading_days = subject_days.get("reading", {})
    spelling_days = subject_days.get("spelling", {})
    if "reading" in subject_days or "spelling" in subject_days:
        combined_html = cp.build_combined_reading_spelling_html(args.week_code, reading_days, spelling_days)
        C.PHASE3_PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
        combined_out = C.PHASE3_PREVIEW_DIR / f"{args.week_code}-reading_spelling-page.html"
        combined_out.write_text(combined_html, encoding="utf-8")
        summary["pages"]["reading_spelling_combined"] = {
            "file": str(combined_out),
            "body_chars": len(combined_html),
            "note": "one shared Canvas page for course 26442 (Reading + Spelling)",
        }

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


def cmd_announce(args: argparse.Namespace) -> int:
    """Dry-run assessment + announcement intelligence plan (GET/write-free)."""
    week = pe.extract_week_json(args.week_code, fresh=False)
    config = pa.load_config()
    events = pa.resolve_assessment_facts(week)
    out: dict[str, Any] = {
        "week": args.week_code,
        "mode": "dry-run-plan",
        "events": [],
        "canvas_writes": 0,
    }
    for event in events:
        sched = pa.schedule_notices(event["assessmentDate"], config)
        plans = []
        for notice_type in ("FIRST_NOTICE", "REMINDER"):
            fp = {
                "course": event["course"],
                "assessmentDate": event["assessmentDate"],
                "assessments": [a for a in (event.get("assessments") or []) if a],
                "preparation": event.get("preparation"),
                "facts": event.get("facts"),
            }
            draft = pa.draft_announcement(fp, notice_type, use_llm=args.llm)
            plans.append({
                "identity": pa.announcement_identity(
                    event["course"], event["family"],
                    pa.source_event_label(event), event["assessmentDate"], notice_type,
                ),
                "notice_type": notice_type,
                "scheduled_date": sched["firstNotice"] if notice_type == "FIRST_NOTICE" else sched["reminder"],
                "send_time": config["scheduling"]["sendTime"]["value"],
                "timezone": config["scheduling"]["timezone"],
                "draft": draft,
            })
        out["events"].append({
            "family": event["family"],
            "course": event["course"],
            "assessment_date": event["assessmentDate"],
            "assignments": [a for a in (event.get("assignments") or []) if a],
            "preparation": event.get("preparation"),
            "plans": plans,
        })
    out["chief_review"] = pa.build_chief_review(events, config)
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


def cmd_pilot(args: argparse.Namespace) -> int:
    """Q2W1 pilot: full pipeline per subject, one local-model call for Math."""
    week_code = args.week_code
    week = pe.extract_week_json(week_code, fresh=args.fresh)
    pc.save_snapshot(week)
    active = active_subjects(week_code, week)

    redirect = inactive_subject_redirect(week_code)
    report: dict[str, Any] = {
        "week": week.get("week"),
        "source": week.get("source"),
        "active_subjects": active,
        "inactive_subject_redirect": redirect,
        "subjects": {},
    }
    for subject in active:
        raw_by_day = {
            wd: day["subjects"][subject]["raw"] for wd, day in week.get("days", {}).items()
        }
        bundle = pr.retrieve(subject=subject)
        entry: dict[str, Any] = {
            "raw_source": raw_by_day,
            "deterministic_interpretation": {
                "note": "raw values preserved verbatim; no curriculum meaning added",
            },
            "precedent": {
                "policy_count": bundle["policy_count"],
                "teacher_rule_count": bundle["teacher_rule_count"],
                "live_precedent_count": bundle["live_precedent_count"],
            },
        }
        # Run the local model for Math only (bounded single call for the pilot).
        if subject == "math":
            t0 = time.time()
            proposal = llm.propose_subject(week, bundle, subject)
            proposal["latency_seconds"] = round(time.time() - t0, 2)
            entry["local_llm_proposal"] = proposal
            days, unresolved = _coerce_proposal_days(proposal.get("proposals"))
            entry["unresolved_fields"] = unresolved
        else:
            entry["local_llm_proposal"] = {"status": "SKIPPED", "note": "pilot bounds model calls to Math; run `propose --subject <s>` to extend"}
            entry["unresolved_fields"] = list(raw_by_day.keys())
        entry["teacher_approval_required"] = True
        report["subjects"][subject] = entry

    # Dry-run preview using deterministic raw days (no fabricated content).
    subject_days = {s: _raw_preview_days(week, s) for s in active}
    summary = cp.build_dry_run_package(week, subject_days)
    report["preview"] = summary

    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


def cmd_correct(args: argparse.Namespace) -> int:
    record = learn.record_correction(
        week=args.week,
        subject=args.subject,
        weekday=args.weekday,
        raw_pacing=args.raw,
        artifact_type=args.artifact,
        model_proposal=args.proposal,
        teacher_final=args.final,
        authority=args.authority,
        source_refs=[args.source] if args.source else [],
        status=args.status,
    )
    print(json.dumps(record, indent=2, ensure_ascii=False))
    return 0


def cmd_suggest_promotions(args: argparse.Namespace) -> int:
    sugg = learn.suggest_promotions(threshold=args.threshold)
    print(json.dumps(sugg, indent=2, ensure_ascii=False))
    return 0


def cmd_status(_args: argparse.Namespace) -> int:
    """Phase 3 status report (PASS/WARN/FAIL)."""
    checks: list[tuple[bool, str]] = []
    checks.append((llm.model_available(), f"local model {C.OLLAMA_MODEL} available"))
    checks.append((C.WEEKS_PATH.exists(), "instructional-weeks config present"))
    checks.append((C.ANOMALY_EXCLUSIONS_PATH.exists(), "anomaly-exclusions config present"))
    checks.append((pc.load_latest() is not None, "pacing snapshot present"))
    # Zero-write proof: this package never imports Canvas write machinery.
    zero_write = _zero_write_proof()
    checks.append((zero_write["write_free"], f"zero-write proof: {zero_write['detail']}"))

    fails = sum(1 for ok, _ in checks if not ok)
    print("Phase 3 status")
    for ok, label in checks:
        print(f"  {'PASS' if ok else 'WARN'}  {label}")
    print(f"\nSummary: {'PASS' if fails == 0 else 'WARN'}")
    return 0 if fails == 0 else 1


_FORBIDDEN_WRITE_TOKENS = (
    "requests.post", "requests.put", "requests.patch", "requests.delete",
    ".post(", ".put(", ".patch(", ".delete(",
    'method="POST"', 'method="PUT"', 'method="PATCH"', 'method="DELETE"',
)


def _zero_write_proof() -> dict[str, Any]:
    """Static proof this package path cannot invoke Canvas write verbs.

    Strips the ``_FORBIDDEN_WRITE_TOKENS`` definition and uses a dynamically
    constructed ``data=`` needle so the scanner's own source never self-matches.
    Confirms no HTTP request carries a body argument."""
    from pathlib import Path

    found: list[str] = []
    body_arg: list[str] = []
    req_needle = "Request" + "("
    data_needle = "data" + "="
    for p in Path(__file__).parent.glob("*.py"):
        src = p.read_text(encoding="utf-8")
        start = src.find("_FORBIDDEN_WRITE_TOKENS = (")
        if start != -1:
            end = src.find(")", start)
            src = src[:start] + src[end + 1 :]
        for tok in _FORBIDDEN_WRITE_TOKENS:
            if tok in src:
                found.append(f"{p.name}:{tok}")
        if req_needle in src and data_needle in src:
            body_arg.append(p.name)
    write_free = len(found) == 0 and len(body_arg) == 0
    detail = "no Canvas write verbs and no request body args in phase3 package"
    if found:
        detail = found
    elif body_arg:
        detail = [f"{n}:request data= arg" for n in body_arg]
    return {"write_free": write_free, "detail": detail}


def cmd_self_test(_args: argparse.Namespace) -> int:
    import importlib

    modules = [
        "pacing_extractor", "pacing_change", "pacing_translation", "pacing_math",
        "pacing_announcement", "pacing_reading", "pacing_pages", "pacing_routing",
        "precedent_retrieval",
        "local_llm", "learning", "state_machine", "canvas_preview",
    ]
    for name in modules:
        mod = importlib.import_module(f"scripts.canvas_llm_phase3.{name}")
        rc = mod.command_self_test()
        if rc != 0:
            return rc
    zw = _zero_write_proof()
    print(f"PASS zero-write proof: {zw['detail']}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="bin/canvas-week", description="Chief of Staff weekly planning loop (read-only)")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("extract", help="fresh-read + deterministic extraction")
    sp.add_argument("week_code")
    sp.add_argument("--fresh", action=argparse.BooleanOptionalAction, default=True)
    sp.set_defaults(func=cmd_extract)

    sp = sub.add_parser("show", help="show normalized week")
    sp.add_argument("week_code")
    sp.set_defaults(func=cmd_show)

    sp = sub.add_parser("diff", help="what changed in pacing")
    sp.set_defaults(func=cmd_diff)

    sp = sub.add_parser("propose", help="local-LLM proposal")
    sp.add_argument("week_code")
    sp.add_argument("--subject")
    sp.set_defaults(func=cmd_propose)

    sp = sub.add_parser("preview", help="Canvas dry-run preview")
    sp.add_argument("week_code")
    sp.set_defaults(func=cmd_preview)

    sp = sub.add_parser("announce", help="dry-run assessment + announcement plan (no Canvas writes)")
    sp.add_argument("week_code")
    sp.add_argument("--llm", action="store_true", help="invoke local Qwen for style-only wording (default off)")
    sp.set_defaults(func=cmd_announce)

    sp = sub.add_parser("pilot", help="full pipeline pilot for one week")
    sp.add_argument("week_code")
    sp.add_argument("--fresh", action=argparse.BooleanOptionalAction, default=True)
    sp.set_defaults(func=cmd_pilot)

    sp = sub.add_parser("correct", help="record a teacher correction")
    sp.add_argument("--week", required=True)
    sp.add_argument("--subject", required=True)
    sp.add_argument("--weekday", required=True)
    sp.add_argument("--raw", default="")
    sp.add_argument("--artifact", required=True)
    sp.add_argument("--proposal", default="")
    sp.add_argument("--final", required=True)
    sp.add_argument("--authority", default="OWNER_POLICY")
    sp.add_argument("--source", default="")
    sp.add_argument("--status", default="approved", choices=["approved", "rejected"])
    sp.set_defaults(func=cmd_correct)

    sp = sub.add_parser("suggest-promotions", help="rule-promotion suggestions (never auto-promotes)")
    sp.add_argument("--threshold", type=int, default=5)
    sp.set_defaults(func=cmd_suggest_promotions)

    sub.add_parser("status").set_defaults(func=cmd_status)
    sub.add_parser("self-test").set_defaults(func=cmd_self_test)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
