"""Dry-run deployment packet assembly (Phase 18D).

``assemble_dry_run_packet(preview, snapshot, context)`` turns a validated
Teacher Preview into a deterministic Dry-Run Deployment Packet: a set of
proposed (never executed) deployment intents, a semantic safety diff against a
read-only live Canvas snapshot, and a fail-closed readiness evaluation.

No writes. No Canvas mutation. No token use. No network. No guessing.
"""

from __future__ import annotations

import hashlib
import html
from typing import Any

from scripts.canvas_llm_phase18c.contracts import TeacherPreview
from scripts.canvas_llm_phase27.canonicalize import canonical_hash

from .contracts import (
    CanvasSnapshot,
    DeploymentIntent,
    DryRunContext,
    DryRunPacket,
    FieldDiff,
    ObjectType,
    OperationType,
    RiskTier,
    SafetyDiffItem,
    SnapshotObject,
)
from .diff import build_safety_diff_item, compare_state, has_meaningful_change
from .readiness import evaluate_packet_readiness
from .snapshot import snapshot_hash, validate_snapshot

# Required live Canvas configuration fields per object type. Missing any of these
# blocks the affected intent with BLOCKED_MISSING_CONFIG; IDs are never guessed.
REQUIRED_CONFIG_FIELDS: dict[str, list[str]] = {
    "agenda_page": ["course_id", "module_id"],
    "assignment": ["course_id", "assignment_group_id"],
}

# Semantic content fields used for create/update/no-change resolution (excludes
# publication, which is only asserted when the publish policy is resolved).
CONTENT_FIELDS: dict[str, list[str]] = {
    "agenda_page": ["title", "body", "course_id"],
    "assignment": ["title", "due_at", "course_id", "assignment_group_id"],
}

_SOURCE_PRIORITY = {"teacher_instruction": 3, "live_pacing": 2, "canonical_rule": 1}


def compact(value: Any) -> str:
    return " ".join(str(value or "").replace("\xa0", " ").split())


def _stable_id(*parts: str) -> str:
    return hashlib.sha256("|".join(compact(p) for p in parts).encode("utf-8")).hexdigest()[:16]


def _strongest_source(days: list[Any]) -> str:
    best = "canonical_rule"
    best_rank = 1
    for day in days:
        source = getattr(day, "source", "") or "canonical_rule"
        rank = _SOURCE_PRIORITY.get(source, 0)
        if rank > best_rank:
            best = source
            best_rank = rank
    return best


def _content_days(days: list[Any]) -> list[Any]:
    return [d for d in days if getattr(d, "status", "") == "content"]


def _render_course_body(course_name: str, days: list[Any]) -> str:
    parts: list[str] = [f"<h2>{html.escape(course_name)}</h2>"]
    for day in days:
        if getattr(day, "status", "") != "content":
            continue
        parts.append(f"<h3>{html.escape(day.weekday)}</h3>")
        if compact(day.in_class):
            parts.append(f"<p>In class: {html.escape(compact(day.in_class))}</p>")
        if compact(day.homework):
            parts.append(f"<p>Homework: {html.escape(compact(day.homework))}</p>")
    return "".join(parts)


def _resolve_config(context: DryRunContext, subject: str, object_type: str) -> tuple[dict[str, Any], list[str]]:
    cfg = context.canvas_config.get(subject) or {}
    missing = [f for f in REQUIRED_CONFIG_FIELDS.get(object_type, []) if not str(cfg.get(f) or "").strip()]
    return cfg, missing


def _resolve_existing(
    index: dict[tuple[str, str, str], list[SnapshotObject]], subject: str, object_type: str, locator: str
) -> tuple[str, list[SnapshotObject]]:
    """Return ('absent'|'single'|'ambiguous', objects) for a logical target."""
    matches = index.get((subject, object_type, locator), [])
    if not matches:
        return "absent", []
    if len(matches) == 1:
        return "single", matches
    return "ambiguous", matches


def _provenance(preview: TeacherPreview, subject: str, source: str, detail: str) -> list[dict[str, Any]]:
    envelope: list[dict[str, Any]] = [
        {"sourceType": "canonical-weekly-plan", "sourceRef": preview.week_code, "details": "Phase 18A canonical WeeklyPlan"},
        {"sourceType": "teacher-preview", "sourceRef": preview.week_code, "details": "Phase 18C Teacher Preview"},
        {"sourceType": "subject", "sourceRef": subject, "details": detail},
        {"sourceType": "source", "sourceRef": source, "details": f"decided by {source}"},
    ]
    return envelope


def _build_page_intent(
    preview: TeacherPreview,
    course: Any,
    subject: str,
    context: DryRunContext,
    index: dict[tuple[str, str, str], list[SnapshotObject]],
    blocker_kinds: set[str],
    blocked_reasons: list[str],
    *,
    read_blocked: bool = False,
) -> DeploymentIntent | None:
    course_name = course.course
    locator = f"{subject}-agenda-{preview.week_code.lower()}"
    intent_id = _stable_id(preview.week_code, "agenda_page", subject, locator)
    source = _strongest_source(course.days)
    week_title = getattr(preview, "week_title", "") or preview.week_code
    title = f"{course_name} — {week_title}"

    if read_blocked:
        blocker_kinds.add("read_failure")
        blocked_reasons.append(f"{course_name} agenda page: live read failed")
        return DeploymentIntent(
            id=intent_id, operation=OperationType.BLOCKED.value, object_type=ObjectType.AGENDA_PAGE.value,
            course=subject, canonical_source=source, target_locator=locator,
            desired_state={"title": title}, current_state={},
            provenance=_provenance(preview, subject, source, f"agenda page for {course_name}"),
            preconditions={"week_code": preview.week_code}, blockers=["read_failure"],
            risk=RiskTier.HIGH.value, reason=f"live read failed for {course_name} agenda page",
        )

    cfg, missing = _resolve_config(context, subject, "agenda_page")
    if missing:
        blocker_kinds.add("missing_config")
        blocked_reasons.append(f"missing config for {course_name} agenda page: {', '.join(missing)}")
        return DeploymentIntent(
            id=intent_id, operation=OperationType.BLOCKED.value, object_type=ObjectType.AGENDA_PAGE.value,
            course=subject, canonical_source=source, target_locator=locator,
            desired_state={"title": title}, current_state={},
            provenance=_provenance(preview, subject, source, f"agenda page for {course_name}"),
            preconditions={"week_code": preview.week_code}, blockers=list(missing),
            risk=RiskTier.HIGH.value, reason=f"missing Canvas configuration for {course_name} agenda page",
        )

    # Unresolved canonical content blocks the page (cannot render a complete page).
    if any(getattr(d, "status", "") == "unresolved" for d in course.days):
        blocker_kinds.add("unresolved")
        blocked_reasons.append(f"{course_name} agenda page blocked: unresolved canonical content")
        return DeploymentIntent(
            id=intent_id, operation=OperationType.BLOCKED.value, object_type=ObjectType.AGENDA_PAGE.value,
            course=subject, canonical_source=source, target_locator=locator,
            desired_state={"title": title}, current_state={},
            provenance=_provenance(preview, subject, source, f"agenda page for {course_name}"),
            preconditions={"week_code": preview.week_code}, blockers=["unresolved_content"],
            risk=RiskTier.HIGH.value, reason=f"unresolved canonical content in {course_name}",
        )

    body = _render_course_body(course_name, course.days)
    publication = context.resolved_publish_state if context.publish_policy == "resolved" else "unresolved"
    desired = {
        "title": title,
        "body": body,
        "course_id": str(cfg.get("course_id") or ""),
        "publication": publication,
    }

    kind, objs = _resolve_existing(index, subject, "agenda_page", locator)
    blockers: list[str] = []
    had_remote_drift = False
    current: dict[str, Any] = {}

    if kind == "ambiguous":
        blockers.append("ambiguous_target")
        op = OperationType.BLOCKED.value
    elif kind == "single":
        obj = objs[0]
        current = dict(obj.current_state)
        if obj.course != subject:
            blockers.append("wrong_course")
            op = OperationType.BLOCKED.value
        elif _belongs_to_other_course(obj, cfg):
            blockers.append("wrong_course")
            op = OperationType.BLOCKED.value
        elif not obj.managed:
            blockers.append("ownership_uncertain")
            op = OperationType.BLOCKED.value
        elif obj.baseline_hash and obj.content_hash != obj.baseline_hash:
            blockers.append("remote_drift")
            had_remote_drift = True
            op = OperationType.BLOCKED.value
        else:
            content_diffs = compare_state(current, desired, CONTENT_FIELDS["agenda_page"])
            if has_meaningful_change(content_diffs):
                op = OperationType.UPDATE.value
            else:
                op = OperationType.NO_CHANGE.value
    else:
        # Absent -> create, unless a teacher-owned title collision exists.
        op = OperationType.CREATE.value
        for (c, otype, _loc), objs2 in index.items():
            if c == subject and otype == "agenda_page":
                for o in objs2:
                    if not o.managed and compact(o.title) == compact(title):
                        blockers.append("title_collision")
                        op = OperationType.BLOCKED.value
                        break

    # Publication policy must be resolved for any actual write.
    if op in (OperationType.CREATE.value, OperationType.UPDATE.value) and context.publish_policy != "resolved":
        blockers.append("policy:publish_state_unresolved")
        op = OperationType.BLOCKED.value

    if op == OperationType.BLOCKED.value:
        blocker_kinds.add(_blocker_kind(blockers))
        for b in blockers:
            blocked_reasons.append(f"{course_name} agenda page: {b}")

    field_diffs: list[FieldDiff] = compare_state(current, desired, ["title", "body", "course_id", "publication"])
    return DeploymentIntent(
        id=intent_id, operation=op, object_type=ObjectType.AGENDA_PAGE.value,
        course=subject, canonical_source=source, target_locator=locator,
        desired_state=desired, current_state=current,
        provenance=_provenance(preview, subject, source, f"agenda page for {course_name}"),
        preconditions={
            "expected_object_id": objs[0].object_id if kind == "single" else "",
            "expected_current_hash": objs[0].content_hash if kind == "single" else "",
            "week_code": preview.week_code,
        },
        blockers=blockers, risk=(RiskTier.HIGH.value if blockers else RiskTier.MEDIUM.value),
        reason=_reason(op, source, f"{course_name} agenda page", blockers, had_remote_drift),
    )


def _build_assignment_intents(
    preview: TeacherPreview,
    course: Any,
    subject: str,
    context: DryRunContext,
    index: dict[tuple[str, str, str], list[SnapshotObject]],
    blocker_kinds: set[str],
    blocked_reasons: list[str],
    *,
    read_blocked: bool = False,
) -> list[DeploymentIntent]:
    intents: list[DeploymentIntent] = []
    course_name = course.course
    cfg, missing_cfg = _resolve_config(context, subject, "assignment")

    for day in course.days:
        if getattr(day, "status", "") != "content":
            continue
        if not compact(day.homework) or compact(day.homework).lower() == "no homework":
            continue
        locator = f"{subject}-homework-{preview.week_code.lower()}-{day.weekday.lower()}"
        intent_id = _stable_id(preview.week_code, "assignment", subject, locator)
        source = getattr(day, "source", "") or "canonical_rule"

        blockers: list[str] = []
        if read_blocked:
            blockers.append("read_failure")
        if missing_cfg:
            blockers.append("missing_config")
        elif context.due_time_policy != "resolved":
            blockers.append("policy:due_time_unresolved")
        elif not compact(context.resolved_due_time):
            blockers.append("missing_config:resolved_due_time")
        if context.publish_policy != "resolved":
            blockers.append("policy:publish_state_unresolved")

        desired = {
            "title": f"{course_name} Homework — {day.weekday}",
            "course_id": str(cfg.get("course_id") or ""),
            "assignment_group_id": str(cfg.get("assignment_group_id") or ""),
            "due_at": compact(context.resolved_due_time) if (context.due_time_policy == "resolved" and compact(context.resolved_due_time)) else None,
            "publication": context.resolved_publish_state if context.publish_policy == "resolved" else "unresolved",
        }

        kind, objs = _resolve_existing(index, subject, "assignment", locator)
        current: dict[str, Any] = {}
        had_remote_drift = False
        op = OperationType.CREATE.value

        if blockers:
            op = OperationType.BLOCKED.value
        elif kind == "ambiguous":
            blockers.append("ambiguous_target")
            op = OperationType.BLOCKED.value
        elif kind == "single":
            obj = objs[0]
            current = dict(obj.current_state)
            if obj.course != subject:
                blockers.append("wrong_course")
                op = OperationType.BLOCKED.value
            elif _belongs_to_other_course(obj, cfg):
                blockers.append("wrong_course")
                op = OperationType.BLOCKED.value
            elif not obj.managed:
                blockers.append("ownership_uncertain")
                op = OperationType.BLOCKED.value
            elif obj.baseline_hash and obj.content_hash != obj.baseline_hash:
                blockers.append("remote_drift")
                had_remote_drift = True
                op = OperationType.BLOCKED.value
            else:
                content_diffs = compare_state(current, desired, CONTENT_FIELDS["assignment"])
                op = OperationType.UPDATE.value if has_meaningful_change(content_diffs) else OperationType.NO_CHANGE.value

        if op == OperationType.BLOCKED.value:
            blocker_kinds.add(_blocker_kind(blockers))
            for b in blockers:
                blocked_reasons.append(f"{course_name} assignment ({day.weekday}): {b}")

        intents.append(
            DeploymentIntent(
                id=intent_id, operation=op, object_type=ObjectType.ASSIGNMENT.value,
                course=subject, canonical_source=source, target_locator=locator,
                desired_state=desired, current_state=current,
                provenance=_provenance(preview, subject, source, f"homework assignment for {course_name} {day.weekday}"),
                preconditions={
                    "expected_object_id": objs[0].object_id if kind == "single" else "",
                    "expected_current_hash": objs[0].content_hash if kind == "single" else "",
                    "week_code": preview.week_code,
                },
                blockers=blockers, risk=(RiskTier.HIGH.value if blockers else RiskTier.MEDIUM.value),
                reason=_reason(op, source, f"{course_name} assignment ({day.weekday})", blockers, had_remote_drift),
            )
        )
    return intents


def _belongs_to_other_course(obj: SnapshotObject, cfg: dict[str, Any]) -> bool:
    recorded = str(obj.current_state.get("course_id") or "").strip()
    expected = str(cfg.get("course_id") or "").strip()
    return bool(recorded and expected and recorded != expected)


def _blocker_kind(blockers: list[str]) -> str:
    if "read_failure" in blockers:
        return "read_failure"
    if any(b.startswith("policy:") for b in blockers):
        return "policy"
    if "ownership_uncertain" in blockers or "wrong_course" in blockers:
        return "ownership"
    if "remote_drift" in blockers:
        return "remote_drift"
    if "title_collision" in blockers or "ambiguous_target" in blockers:
        return "collision"
    if "unresolved_content" in blockers:
        return "unresolved"
    return "missing_config"


def _reason(op: str, source: str, target: str, blockers: list[str], had_remote_drift: bool) -> str:
    if op == OperationType.NO_CHANGE.value:
        return f"NO_CHANGE: {target} already matches canonical desired state"
    if op == OperationType.SKIP.value:
        return f"SKIP: {target} (protected)"
    if op == OperationType.BLOCKED.value:
        return f"BLOCKED: {target} — {', '.join(blockers) or 'blocker'}"
    if had_remote_drift:
        return f"REVIEW: {target} drifted remotely from system baseline (source: {source})"
    if op == OperationType.UPDATE.value:
        return f"UPDATE: {target} differs from canonical desired state (source: {source})"
    return f"CREATE: {target} does not yet exist in Canvas (source: {source})"


def _normalize_snapshot(preview: TeacherPreview, snapshot: Any) -> CanvasSnapshot:
    """Accept either a CanvasSnapshot or a plain dict snapshot."""
    if isinstance(snapshot, CanvasSnapshot):
        return snapshot
    return CanvasSnapshot(
        week_code=preview.week_code,
        snapshot_id=str(snapshot.get("snapshot_id") or "snapshot"),
        captured_at=str(snapshot.get("captured_at") or ""),
        objects=[SnapshotObject(**o) for o in snapshot.get("objects", [])],
        fetch_errors=list(snapshot.get("fetch_errors") or []),
        read_failure=bool(snapshot.get("read_failure")),
        read_failure_reason=str(snapshot.get("read_failure_reason") or ""),
    )


def _detect_intent_collisions(intents: list[DeploymentIntent]) -> list[str]:
    """Two intents targeting the same logical Canvas object incompatibly."""
    by_key: dict[tuple[str, str, str], list[DeploymentIntent]] = {}
    for intent in intents:
        by_key.setdefault((intent.course, intent.object_type, intent.target_locator), []).append(intent)
    collisions: list[str] = []
    for key, group in by_key.items():
        if len(group) > 1:
            collisions.append(f"collision on {key}: {[i.id for i in group]}")
    return collisions


def assemble_dry_run_packet(
    preview: TeacherPreview,
    snapshot: Any,
    context: DryRunContext | None = None,
) -> DryRunPacket:
    """Assemble a deterministic, read-only Dry-Run Deployment Packet.

    Raises ValueError (fails closed) if the snapshot is malformed.
    """
    context = context or DryRunContext()
    snap_obj = _normalize_snapshot(preview, snapshot)

    errors = validate_snapshot(snap_obj)
    if errors:
        raise ValueError("malformed Canvas snapshot: " + "; ".join(errors))

    blocker_kinds: set[str] = set()
    blocked_reasons: list[str] = []
    warnings: list[str] = list(getattr(preview, "warnings", []) or [])
    intents: list[DeploymentIntent] = []

    if snap_obj.read_failure:
        blocker_kinds.add("read_failure")
        blocked_reasons.append(snap_obj.read_failure_reason or "Canvas read failure")

    index = snap_obj.index()

    for course in preview.courses:
        subject = course.subject_key
        if course.protected:
            locator = f"{subject}-agenda-{preview.week_code.lower()}"
            intents.append(
                DeploymentIntent(
                    id=_stable_id(preview.week_code, "agenda_page", subject, locator),
                    operation=OperationType.SKIP.value,
                    object_type=ObjectType.AGENDA_PAGE.value,
                    course=subject, canonical_source="protected",
                    target_locator=locator,
                    desired_state={}, current_state={},
                    provenance=_provenance(preview, subject, "protected", f"protected course {course.course}"),
                    preconditions={"week_code": preview.week_code}, blockers=[],
                    risk=RiskTier.LOW.value, reason=f"SKIP: protected course {course.course}",
                )
            )
            warnings.append(f"{course.course}: protected — no actions generated")
            continue

        read_blocked = subject in snap_obj.fetch_errors
        if read_blocked:
            blocked_reasons.append(f"{course.course}: live state fetch failed (partial read)")

        page_intent = _build_page_intent(preview, course, subject, context, index, blocker_kinds, blocked_reasons, read_blocked=read_blocked)
        if page_intent is not None:
            intents.append(page_intent)
        if "assignment" in (course.requested_artifacts or []):
            intents.extend(_build_assignment_intents(preview, course, subject, context, index, blocker_kinds, blocked_reasons, read_blocked=read_blocked))

    collisions = _detect_intent_collisions(intents)
    if collisions:
        blocker_kinds.add("collision")
        blocked_reasons.extend(collisions)

    canonical_identity = _canonical_identity(preview)
    preview_hash_value = canonical_hash(_preview_serializable(preview))
    preview_identity = f"preview-{preview_hash_value[:16]}"
    snapshot_hash_value = snapshot_hash(snap_obj)
    readiness = evaluate_packet_readiness(blocker_kinds)

    no_change = [i.id for i in intents if i.operation == OperationType.NO_CHANGE.value]
    blocked = list(dict.fromkeys(blocked_reasons))
    warnings = list(dict.fromkeys(warnings))

    packet = DryRunPacket(
        week_code=preview.week_code,
        canonical_plan_identity=canonical_identity,
        canonical_revision=canonical_identity,
        preview_identity=preview_identity,
        preview_hash=preview_hash_value,
        snapshot_identity=snap_obj.snapshot_id,
        snapshot_hash=snapshot_hash_value,
        target_environment=context.target_environment,
        intents=intents,
        blocked=blocked,
        warnings=warnings,
        no_change=no_change,
        provenance=[
            {"sourceType": "canonical-weekly-plan", "sourceRef": canonical_identity, "details": "Phase 18A canonical WeeklyPlan"},
            {"sourceType": "teacher-preview", "sourceRef": preview_identity, "details": "Phase 18C Teacher Preview"},
            {"sourceType": "canvas-snapshot", "sourceRef": snap_obj.snapshot_id, "details": "read-only live Canvas snapshot"},
        ],
        readiness=readiness,
    )
    packet.packet_hash = _packet_hash(packet)
    return packet


def validate_packet(packet: DryRunPacket) -> list[str]:
    """Structural validation of a dry-run packet. Empty list means valid."""
    errors: list[str] = []
    valid_operations = {op.value for op in OperationType}
    for intent in packet.intents:
        if intent.operation not in valid_operations:
            errors.append(f"intent {intent.id} has unknown operation {intent.operation!r}")
        if not intent.id:
            errors.append("intent missing id")
        if not intent.reason:
            errors.append(f"intent {intent.id} missing reason")
        if not intent.provenance:
            errors.append(f"intent {intent.id} missing canonical provenance")
        if not intent.canonical_source:
            errors.append(f"intent {intent.id} missing canonical_source")
    recomputed = _packet_hash(packet)
    if packet.packet_hash and packet.packet_hash != recomputed:
        errors.append("packet hash mismatch")
    return errors


def build_safety_diff(packet: DryRunPacket) -> list[SafetyDiffItem]:
    """Derive the ordered safety-diff items from a packet's intents."""
    items: list[SafetyDiffItem] = []
    for intent in packet.intents:
        content_fields = CONTENT_FIELDS.get(intent.object_type, ["title", "body", "publication"])
        field_diffs = compare_state(intent.current_state, intent.desired_state, content_fields)
        had_remote_drift = "remote_drift" in intent.blockers
        items.append(
            build_safety_diff_item(
                intent.id, intent.object_type, intent.course, intent.target_locator,
                intent.operation, intent.canonical_source, field_diffs, intent.blockers,
                had_remote_drift=had_remote_drift,
            )
        )
    return items


def _canonical_identity(preview: TeacherPreview) -> str:
    for entry in getattr(preview, "provenance", []) or []:
        if isinstance(entry, dict) and entry.get("sourceType") == "canonical-weekly-plan":
            ref = entry.get("sourceRef")
            if ref:
                return str(ref)
    return f"wp-{preview.week_code}"


def _preview_serializable(preview: TeacherPreview) -> Any:
    if hasattr(preview, "to_dict"):
        return preview.to_dict()
    return preview


def _packet_hash(packet: DryRunPacket) -> str:
    payload = {
        "week_code": packet.week_code,
        "canonical_revision": packet.canonical_revision,
        "preview_hash": packet.preview_hash,
        "snapshot_hash": packet.snapshot_hash,
        "target_environment": packet.target_environment,
        "intents": [i.to_dict() for i in packet.intents],
    }
    return canonical_hash(payload)
