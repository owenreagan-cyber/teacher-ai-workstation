"""Part C — deterministic precedent retrieval.

Assembles the context bundle a local model needs, ordered by authority:

    OWNER_POLICY
    then approved/promoted teacher rules
    then recent matching LIVE_CANVAS_PRECEDENT
    then MODEL_INFERENCE

No embeddings. Deterministic, JSON-file-backed retrieval that never returns a
known anomaly as positive precedent.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

from . import constants as C


def _load_json(path: Path, default: Any) -> Any:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return default
    return default


def load_anomaly_exclusions() -> list[dict[str, Any]]:
    data = _load_json(C.ANOMALY_EXCLUSIONS_PATH, {})
    return data.get("exclusions", [])


def load_policy() -> list[dict[str, Any]]:
    """Load OWNER_POLICY records from the canonical config layer."""
    records: list[dict[str, Any]] = []

    def add(path: Path, domain: str) -> None:
        data = _load_json(path, None)
        if isinstance(data, dict) and data:
            records.append({
                "domain": domain,
                "authority": "OWNER_POLICY",
                "source": str(path.relative_to(C.REPO_ROOT)),
                "data": data,
            })

    add(C.AGENDA_RULES_PATH, "agenda-page-rules")
    add(C.WEEKLY_STANDARD_PATH, "weekly-agenda-standard")
    add(C.QUARTER_ACTIVATION_PATH, "quarter-subject-activation")
    add(C.COURSE_MAPPINGS_PATH, "canvas-course-mappings")
    for p in sorted(C.FPK_DIR.glob("*.json")):
        if p.name == "anomaly-exclusions.json":
            continue
        add(p, f"fpk/{p.stem}")
    return records


def load_teacher_rules() -> list[dict[str, Any]]:
    """Load promoted rules and approved corrections (teacher-approved only)."""
    records: list[dict[str, Any]] = []
    promoted = _load_json(C.LEARNING_FILES["promoted_rules"], [])
    if isinstance(promoted, list):
        for r in promoted:
            if isinstance(r, dict):
                r2 = dict(r)
                r2.setdefault("authority", "OWNER_POLICY")
                records.append(r2)
    # Approved corrections act as teacher-approved retrieval precedent.
    corr_path = C.LEARNING_FILES["corrections"]
    if corr_path.exists():
        for line in corr_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("status") == "approved":
                records.append(rec)
    return records


def load_live_precedent(subject: str | None = None) -> list[dict[str, Any]]:
    """Load LIVE_CANVAS_PRECEDENT records from the Phase 2A normalized sweep."""
    records: list[dict[str, Any]] = []
    if not C.PRECEDENT_NORM_DIR.exists():
        return records
    for path in sorted(C.PRECEDENT_NORM_DIR.glob("*.json")):
        data = _load_json(path, None)
        if not isinstance(data, dict):
            continue
        if subject and subject not in str(data):
            # Only include artifacts that reference the subject when filtered.
            if subject not in path.name and subject not in json.dumps(data, ensure_ascii=False):
                continue
        records.append({
            "domain": path.stem,
            "authority": "LIVE_CANVAS_PRECEDENT",
            "source": str(path.relative_to(C.REPO_ROOT)),
            "data": data,
        })
    return records


def is_anomalous(text: str, exclusions: list[dict[str, Any]]) -> bool:
    """Return True if ``text`` matches any exclusion pattern."""
    for ex in exclusions:
        pattern = ex.get("pattern", "")
        kind = ex.get("match", "title_substring")
        if not pattern:
            continue
        try:
            if kind in ("title_substring", "assignment_title", "page_slug", "assignment_setting", "layout_pattern"):
                if re.search(pattern, text):
                    return True
            elif kind in ("title_prefix", "assignment_setting"):
                if re.search(pattern, text):
                    return True
            elif kind == "title_suffix":
                if re.search(pattern, text):
                    return True
        except re.error:
            continue
    return False


def retrieve(subject: str | None = None, artifact_type: str | None = None) -> dict[str, Any]:
    """Return an authority-ordered context bundle for a subject/artifact."""
    exclusions = load_anomaly_exclusions()
    policy = load_policy()
    teacher = [r for r in load_teacher_rules() if not _excluded(r, exclusions)]
    live = [r for r in load_live_precedent(subject) if not _excluded(r, exclusions)]
    return {
        "subject": subject,
        "artifact_type": artifact_type,
        "authority_order": ["OWNER_POLICY", "TEACHER_APPROVED", "LIVE_CANVAS_PRECEDENT", "MODEL_INFERENCE"],
        "policy_count": len(policy),
        "teacher_rule_count": len(teacher),
        "live_precedent_count": len(live),
        "policy": policy,
        "teacher_approved": teacher,
        "live_precedent": live,
        "anomaly_exclusions": [ex.get("id") for ex in exclusions],
    }


def _excluded(record: dict[str, Any], exclusions: list[dict[str, Any]]) -> bool:
    text = json.dumps(record, ensure_ascii=False, default=str)
    return is_anomalous(text, exclusions)


def command_self_test() -> int:
    bundle = retrieve(subject="math")
    assert bundle["authority_order"][0] == "OWNER_POLICY"
    assert bundle["policy_count"] >= 1
    assert set(bundle["anomaly_exclusions"]) >= {"ELA4A-ELA4B-PREFIX", "DUPLICATED-HIST-PREFIX"}

    # Anomaly exclusion: duplicated HIST prefix must be flagged.
    exclusions = load_anomaly_exclusions()
    assert is_anomalous("HIST 4B: HIST 4B: Maps Vocabulary", exclusions) is True
    assert is_anomalous("SM5: Lesson 22 Homework", exclusions) is False
    assert is_anomalous("SM5: Lesson 22", exclusions) is True  # naming drift exclusion
    assert is_anomalous("RM4: Lesson 22 Workbook", exclusions) is False

    print("PASS precedent retrieval self-test")
    return 0


if __name__ == "__main__":
    sys.exit(command_self_test())
