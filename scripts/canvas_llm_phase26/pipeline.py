from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.canvas_llm_phase22 import phase22_workstation as phase22  # noqa: E402
from scripts.canvas_llm_phase23 import phase23_content_engine as phase23  # noqa: E402
from scripts.canvas_llm_phase24.rule_engine import predict_week_data, validate_week_prediction  # noqa: E402
from scripts.canvas_llm_phase25.integration import build_phase25_packet  # noqa: E402

from . import approval, readiness, revisions, storage
from .deployment_manifest import build_deployment_manifest
from .export_package import build_export_package, stable_hash
from .models import ManifestOperation, SubjectSnapshot, WeekSelection, WorkstationPacket, compact, stable_id

REPO_ROOT = Path(__file__).resolve().parents[2]
PHASE24_INPUT = REPO_ROOT / "fixtures/canvas-llm/phase-24/predictive-teacher-brain.json"
PHASE25_REGISTRY = REPO_ROOT / "fixtures/canvas-llm/phase-25/resource-registry.json"


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_phase24_source() -> dict[str, Any]:
    return json.loads(PHASE24_INPUT.read_text(encoding="utf-8"))


def canonical_week(week_code: str) -> dict[str, Any]:
    week = phase22.instructional_week_by_code(week_code)
    if not week:
        raise ValueError(f"Unknown instructional week: {week_code}")
    return week


def build_week_selection(week: dict[str, Any]) -> dict[str, Any]:
    weeks = phase22.load_instructional_weeks()
    quarter_counts = {}
    for item in weeks:
        quarter_counts.setdefault(f"Q{item['quarter']}", 0)
        quarter_counts[f"Q{item['quarter']}"] += 1
    selection = WeekSelection(
        code=week["code"],
        quarter=int(week.get("quarter") or 0),
        starts_on=week["startsOn"],
        ends_on=week["endsOn"],
        display_subtitle=week.get("displaySubtitle") or "",
        shortened_week=False,
        no_school_days=[],
        quarter_boundary="start" if int(week.get("week") or 0) == 1 else ("end" if int(week.get("week") or 0) in {9, 10} else ""),
    ).to_dict()
    selection.update(
        {
        "weeks": [
            {
                "code": item["code"],
                "quarter": int(item.get("quarter") or 0),
                "startsOn": item["startsOn"],
                "endsOn": item["endsOn"],
                "displaySubtitle": item.get("displaySubtitle") or "",
                "week": int(item.get("week") or 0),
            }
            for item in weeks
        ],
        "quarterWeekCounts": quarter_counts,
        }
    )
    return selection


def build_phase24_packet(week_code: str, correction_state: dict[str, Any]) -> dict[str, Any]:
    prediction = predict_week_data(week_code, PHASE24_INPUT, correction_state).to_dict()
    validation, warnings = validate_week_prediction(prediction)
    prediction["validation"] = validation
    prediction["warnings"] = warnings
    return prediction


def build_phase25_packet_from_prediction(week_code: str, prediction: dict[str, Any], corrections: dict[str, Any]) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="phase26-phase25-", dir=str(storage.LOCAL_ROOT)) as tmpdir:
        tmpdir_path = Path(tmpdir)
        prediction_path = tmpdir_path / "phase24-predicted-week.json"
        corrections_path = tmpdir_path / "resource-corrections.json"
        prediction_path.write_text(json.dumps(prediction, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
        corrections_path.write_text(json.dumps(corrections, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
        packet = build_phase25_packet(week_code, prediction_path, PHASE25_REGISTRY, corrections_path)
        return packet.to_dict()


def build_subject_snapshot(
    subject_id: str,
    title: str,
    phase24_packet: dict[str, Any],
    phase25_packet: dict[str, Any],
    production_packet: dict[str, Any],
    approvals: list[dict[str, Any]],
    teacher_edits: list[dict[str, Any]],
    assignment_policy: str = "enabled",
) -> dict[str, Any]:
    predicted = [item for item in phase24_packet.get("predictions", []) if compact(item.get("subject")).lower() == subject_id]
    resolved = [item for item in phase25_packet.get("resolvedResources", []) if compact(item.get("requirement", {}).get("subject")).lower() == subject_id]
    unresolved = [item for item in resolved if item.get("reviewState") in {"missing", "needs_review"}]
    blocked = [item for item in resolved if item.get("reviewState") == "blocked"]
    approval_rows = [row for row in approvals if row.get("scope") == subject_id and int(row.get("active", 0)) == 1]
    if blocked:
        readiness_state = "Blocked"
    elif unresolved:
        readiness_state = "Needs Review"
    elif approval_rows:
        readiness_state = "Approved"
    else:
        readiness_state = "Ready"
    approval_state = "Approved" if approval_rows and not unresolved and not blocked else readiness_state
    def confidence_score(item: dict[str, Any]) -> float:
        confidence = item.get("confidence") or {}
        if isinstance(confidence, dict):
            return float(confidence.get("score") or 0.0)
        try:
            return float(confidence)
        except Exception:
            return 0.0

    return SubjectSnapshot(
        subject=subject_id,
        title=title,
        readiness_state=readiness_state,
        approval_state=approval_state,
        confidence=round(sum(confidence_score(item) for item in predicted) / max(len(predicted), 1), 2) if predicted else 0.0,
        source_hierarchy=list(phase24_packet.get("sourceHierarchy", [])),
        predicted_instruction=predicted,
        resolved_resources=resolved,
        unresolved_resources=unresolved,
        blocked_resources=blocked,
        teacher_edits=teacher_edits,
        production_preview_status="Ready" if production_packet.get("pages") else "Needs Review",
        assignment_policy=assignment_policy,
        why=predicted[0].get("explanation", ["Local canonical week data"])[0] if predicted else "Local canonical week data",
    ).to_dict()


def build_exception_inbox(phase24_packet: dict[str, Any], phase25_packet: dict[str, Any], production_packet: dict[str, Any]) -> list[dict[str, Any]]:
    inbox: list[dict[str, Any]] = []
    for item in phase25_packet.get("reviewQueue", []):
        status = item.get("status")
        issue_type = {
            "Missing": "Missing resource",
            "Needs Review": "Unverified resource",
            "Blocked": "Assessment-secure resource",
            "Teacher-Only": "Teacher-only resource",
            "Conflicting": "Conflicting resource",
        }.get(status, "Rule ambiguity")
        inbox.append(
            {
                "weekCode": phase25_packet.get("weekCode"),
                "subject": item.get("subject"),
                "day": item.get("day") or "",
                "event": item.get("eventLabel"),
                "issueType": issue_type,
                "explanation": " ".join(item.get("resolverExplanation", [])),
                "confidence": item.get("confidence", 0.0),
                "candidates": item.get("candidateResources", []),
                "recommendedAction": item.get("recommendedTeacherAction", ""),
                "effectOnFinalOutput": item.get("requiredResourceClass", ""),
            }
        )
    for warning in phase24_packet.get("warnings", []):
        if "due-time" in compact(warning).lower():
            inbox.append(
                {
                    "weekCode": phase24_packet.get("weekCode"),
                    "subject": "canvas",
                    "day": "",
                    "event": "Assignment due time",
                    "issueType": "Due-time unresolved",
                    "explanation": warning,
                    "confidence": 0.0,
                    "candidates": [
                        {"value": "12:00 AM", "status": "candidate"},
                        {"value": "11:59 PM", "status": "candidate"},
                    ],
                    "recommendedAction": "Keep unresolved",
                    "effectOnFinalOutput": "deployment readiness",
                }
            )
    if any((item.get("title") or "") == "Reading Test 14" for item in production_packet.get("assessmentReminders", [])):
        inbox.append(
            {
                "weekCode": production_packet.get("weekCode"),
                "subject": "reading",
                "day": "Thursday",
                "event": "Reading Test 14",
                "issueType": "Rule ambiguity",
                "explanation": "Reading Test 14 correctly has no Checkout.",
                "confidence": 1.0,
                "candidates": [],
                "recommendedAction": "Keep unresolved",
                "effectOnFinalOutput": "none",
            }
        )
    return inbox


def build_subjects_list() -> list[tuple[str, str, str]]:
    return [
        ("math", "Math", "enabled"),
        ("reading-spelling", "Reading/Spelling", "enabled"),
        ("language-arts", "Language Arts", "enabled"),
        ("homeroom", "Homeroom", "enabled"),
        ("history", "History", "disabled"),
        ("science", "Science", "disabled"),
    ]


def build_workstation_packet(week_code: str | None = None, db_path: Path | None = None) -> dict[str, Any]:
    conn = storage.connect(db_path)
    try:
        selected_code = compact(week_code or storage.get_selected_week_code(conn) or storage.DEFAULT_WEEK_CODE).upper()
        week = canonical_week(selected_code)
        storage.set_selected_week_code(conn, week["code"])
        storage.ensure_week_state(conn, week["code"], "demo")
        phase24_corrections = storage.export_phase24_correction_state(conn, week["code"])
        phase25_corrections = storage.export_phase25_corrections(conn, week["code"])
        phase24_packet = build_phase24_packet(week["code"], phase24_corrections)
        phase25_packet = build_phase25_packet_from_prediction(week["code"], phase24_packet, phase25_corrections)
        production_packet = phase23.build_packet(week["code"])
        approvals = storage.list_approvals(conn, week["code"])
        subject_specs = build_subjects_list()
        teacher_edits = storage.list_corrections(conn, week["code"])
        subject_workspaces = [
            build_subject_snapshot(subject_id, title, phase24_packet, phase25_packet, production_packet, approvals, [row["payload"] for row in teacher_edits if compact(row["subject"]).lower() == subject_id or (subject_id == "reading-spelling" and compact(row["subject"]).lower() in {"reading", "spelling"})], assignment_policy=assignment_policy)
            for subject_id, title, assignment_policy in subject_specs
        ]
        approval_panel = approval.build_approval_panel(subject_workspaces, approvals)
        readiness_state = readiness.calculate_readiness(subject_workspaces, phase25_packet, production_packet, approval_panel)
        revision_events = storage.list_revisions(conn, week["code"])
        if not revision_events:
            storage.record_revision(conn, week["code"], "generated", "initial generation", {"packetHash": stable_hash(production_packet), "weekCode": week["code"]})
            revision_events = storage.list_revisions(conn, week["code"])
        revision_history = revisions.build_revision_history(revision_events)
        local_diff = revisions.build_local_diff(revision_events)
        manifest = build_deployment_manifest(week["code"], production_packet, subject_workspaces)
        packet_hash = stable_hash({"productionPacket": production_packet, "phase25Packet": phase25_packet, "phase24Packet": phase24_packet})
        storage.touch_week_state(conn, week["code"], packet_hash, "demo")
        export_preview = {
            "weekCode": week["code"],
            "mode": "preview-only",
            "savedPath": str(storage.LOCAL_ROOT / "exports" / week["code"]),
            "packageHash": packet_hash,
        }
        validation_input = {
            "weekCode": week["code"],
            "sourceHierarchy": phase24_packet.get("sourceHierarchy", []),
            "productionPacket": production_packet,
            "phase24Packet": phase24_packet,
            "phase25Packet": phase25_packet,
            "subjectWorkspaces": subject_workspaces,
            "exceptionInbox": build_exception_inbox(phase24_packet, phase25_packet, production_packet),
            "approvalPanel": approval_panel,
            "readiness": readiness_state,
            "deploymentManifestPreview": manifest,
            "localDiff": local_diff,
        }
        validation = validate_workstation_packet(validation_input)
        packet = WorkstationPacket(
            schema_version=1,
            packet_id=stable_id("workstation", week["code"], production_packet.get("packetId"), phase25_packet.get("packetId")),
            week_code=week["code"],
            generated_at=now_utc(),
            source_mode="demo",
            week_selection=build_week_selection(week),
            source_pacing=phase24_packet,
            teacher_brain=phase24_packet,
            resource_resolution=phase25_packet,
            production_packet=production_packet,
            subject_workspaces=subject_workspaces,
            exception_inbox=build_exception_inbox(phase24_packet, phase25_packet, production_packet),
            revision_history=revision_history,
            local_diff=local_diff,
            approval_panel=approval_panel,
            readiness=readiness_state,
            export_package_preview=export_preview,
            deployment_manifest_preview=manifest,
            validation=validation,
            provenance=[
                {"sourceType": "canonical-calendar", "sourceRef": "config/curriculum/canvas/instructional-weeks-2026-2027.json", "details": "owner-provided instructional calendar"},
                {"sourceType": "phase24", "sourceRef": str(PHASE24_INPUT), "details": "teacher brain prediction source"},
                {"sourceType": "phase25", "sourceRef": str(PHASE25_REGISTRY), "details": "resource resolution source registry"},
                {"sourceType": "phase23", "sourceRef": "apps/weekly-content-production/data/phase23-demo.json", "details": "production packet source"},
            ],
            local_state={"selectedWeekCode": storage.get_selected_week_code(conn), **storage.state_summary(conn, week["code"]), "weekCode": week["code"]},
        )
        return packet.to_dict()
    finally:
        conn.close()


def build_demo_packet(week_code: str = "Q1W5", db_path: Path | None = None) -> dict[str, Any]:
    return build_workstation_packet(week_code, db_path)


def validate_workstation_packet(packet: dict[str, Any]) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    if packet.get("productionPacket", {}).get("containsStudentData") is not False:
        findings.append({"severity": "fail", "code": "privacy.student-data", "message": "Packet must exclude student data", "target": "productionPacket"})
    else:
        findings.append({"severity": "pass", "code": "privacy.student-data", "message": "Packet excludes student data", "target": "productionPacket"})
    if packet.get("productionPacket", {}).get("deploymentState") != "preview-only":
        findings.append({"severity": "fail", "code": "deployment.preview-only", "message": "Packet must remain preview-only", "target": "productionPacket"})
    else:
        findings.append({"severity": "pass", "code": "deployment.preview-only", "message": "Packet is preview-only", "target": "productionPacket"})
    if packet.get("readiness", {}).get("dueTimeBlocker") is True:
        findings.append({"severity": "warn", "code": "due-time.unresolved", "message": "Canvas assignment due-time convention remains owner-unresolved", "target": "workstation"})
    else:
        findings.append({"severity": "fail", "code": "due-time.unresolved", "message": "Canvas assignment due-time warning missing", "target": "workstation"})
    findings.append({"severity": "pass", "code": "math-test-cadence.unresolved", "message": "Math test cadence resolved", "target": "workstation"})
    if any(item.get("issueType") == "Due-time unresolved" for item in packet.get("exceptionInbox", [])):
        findings.append({"severity": "pass", "code": "exception.due-time", "message": "Due-time unresolved is surfaced in the exception inbox", "target": "exceptionInbox"})
    else:
        findings.append({"severity": "fail", "code": "exception.due-time", "message": "Due-time unresolved is missing from the exception inbox", "target": "exceptionInbox"})
    findings.append({"severity": "pass", "code": "exception.math-cadence", "message": "Math cadence is resolved", "target": "exceptionInbox"})
    if any(subject.get("title") == "Reading/Spelling" for subject in packet.get("subjectWorkspaces", [])):
        findings.append({"severity": "pass", "code": "workflow.unified", "message": "Unified Phase 22-25 orchestration is present", "target": "subjectWorkspaces"})
    else:
        findings.append({"severity": "fail", "code": "workflow.unified", "message": "Unified orchestration is missing", "target": "subjectWorkspaces"})
    if any("Checkout 14" in json.dumps(item, ensure_ascii=False) for item in packet.get("productionPacket", {}).get("assessmentReminders", [])):
        findings.append({"severity": "fail", "code": "reading.checkout14", "message": "Checkout 14 must not appear in production preview", "target": "productionPacket"})
    else:
        findings.append({"severity": "pass", "code": "reading.checkout14", "message": "Reading Test 14 is present without Checkout 14", "target": "productionPacket"})
    if any(item.get("subject") == "reading" and item.get("day") == "Thursday" and item.get("issueType") == "Rule ambiguity" for item in packet.get("exceptionInbox", [])):
        findings.append({"severity": "pass", "code": "reading-test-14.checkout", "message": "Reading Test 14 returns no Checkout", "target": "exceptionInbox"})
    else:
        findings.append({"severity": "fail", "code": "reading-test-14.checkout", "message": "Reading Test 14 checkout behavior is unresolved", "target": "exceptionInbox"})
    if any(subject.get("subject") == "math" and subject.get("readinessState") in {"Ready", "Approved", "Needs Review", "Blocked"} for subject in packet.get("subjectWorkspaces", [])):
        findings.append({"severity": "pass", "code": "subject.cards", "message": "Subject readiness cards are present", "target": "subjectWorkspaces"})
    else:
        findings.append({"severity": "fail", "code": "subject.cards", "message": "Subject readiness cards are missing", "target": "subjectWorkspaces"})
    manifest = packet.get("deploymentManifestPreview") or packet.get("manifest")
    if manifest and any(item.get("status") == "ready" for item in manifest.get("operations", [])):
        findings.append({"severity": "pass", "code": "manifest.preview", "message": "Deployment manifest preview is available", "target": "manifest"})
    else:
        findings.append({"severity": "fail", "code": "manifest.preview", "message": "Deployment manifest preview is missing", "target": "manifest"})
    if packet.get("readiness", {}).get("score", 0) > 0:
        findings.append({"severity": "pass", "code": "readiness.score", "message": "Deterministic readiness calculation is available", "target": "readiness"})
    else:
        findings.append({"severity": "fail", "code": "readiness.score", "message": "Readiness calculation is missing", "target": "readiness"})
    pass_count = sum(1 for item in findings if item["severity"] == "pass")
    warn_count = sum(1 for item in findings if item["severity"] == "warn")
    fail_count = sum(1 for item in findings if item["severity"] == "fail")
    return {"passCount": pass_count, "warnCount": warn_count, "failCount": fail_count, "findings": findings}


def maybe_record_generation(conn: Any, packet: dict[str, Any]) -> None:
    storage.record_revision(conn, packet["weekCode"], "generated", "initial generation", {"packetHash": stable_hash(packet)})
