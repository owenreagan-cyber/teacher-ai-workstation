"""Part F — learning from Owen's corrections.

Stores local teacher-correction records under the gitignored ``.local/learning/``
location (Phase 1 schema). A teacher correction is NOT an automatic universal
rule. Repeated identical corrections can produce a rule-promotion *suggestion*,
but promotion never happens without explicit Owen approval.

No fine-tuning. No embeddings.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import constants as C


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def record_correction(
    *,
    week: str,
    subject: str,
    weekday: str,
    raw_pacing: str,
    artifact_type: str,
    model_proposal: Any,
    teacher_final: Any,
    authority: str,
    source_refs: list[str],
    status: str,  # "approved" | "rejected"
) -> dict[str, Any]:
    record = {
        "timestamp": _now(),
        "week": week,
        "subject": subject,
        "weekday": weekday,
        "raw_pacing": raw_pacing,
        "artifact_type": artifact_type,
        "model_proposal": model_proposal,
        "teacher_final": teacher_final,
        "authority": authority,
        "source": source_refs,
        "status": status,
    }
    path = C.LEARNING_FILES["corrections"]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record


def load_corrections() -> list[dict[str, Any]]:
    path = C.LEARNING_FILES["corrections"]
    if not path.exists():
        return []
    out: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def load_promoted_rules() -> list[dict[str, Any]]:
    path = C.LEARNING_FILES["promoted_rules"]
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, list) else []


def _pattern_key(correction: dict[str, Any]) -> tuple[str, str, str]:
    """Group key for repeated-pattern detection (subject, artifact, normalized final)."""
    final = json.dumps(correction.get("teacher_final"), ensure_ascii=False, sort_keys=True)
    return (
        str(correction.get("subject")),
        str(correction.get("artifact_type")),
        final,
    )


def suggest_promotions(threshold: int = 5) -> list[dict[str, Any]]:
    """Return rule-promotion *suggestions* for patterns approved >= threshold times.
    Never promotes automatically."""
    approved = [c for c in load_corrections() if c.get("status") == "approved"]
    counts: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for c in approved:
        counts.setdefault(_pattern_key(c), []).append(c)
    promoted = load_promoted_rules()
    promoted_rules = {json.dumps(r.get("rule"), sort_keys=True) for r in promoted}

    suggestions: list[dict[str, Any]] = []
    for key, items in counts.items():
        if len(items) < threshold:
            continue
        latest = max(items, key=lambda c: c.get("timestamp", ""))
        if json.dumps(latest.get("teacher_final"), sort_keys=True) in promoted_rules:
            continue
        suggestions.append({
            "subject": key[0],
            "artifact_type": key[1],
            "teacher_final": latest.get("teacher_final"),
            "count": len(items),
            "message": (
                f"You have approved this pattern {len(items)} times. "
                "Promote it to a standing rule?"
            ),
            "requires_explicit_approval": True,
        })
    return suggestions


def promote_rule(*, rule: dict[str, Any], approved_by: str, approved: bool) -> dict[str, Any]:
    """Promote a rule to a standing rule. Refuses unless ``approved`` is explicitly True."""
    if not approved:
        return {"error": "promotion requires explicit approval (approved=True)", "promoted": False}
    path = C.LEARNING_FILES["promoted_rules"]
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = load_promoted_rules()
    record = dict(rule)
    record["approved_by"] = approved_by
    record["authority"] = "OWNER_POLICY"
    record["promoted_at"] = _now()
    record["requires_teacher_approval"] = False
    existing.append(record)
    path.write_text(json.dumps(existing, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"promoted": True, "record": record}


def command_self_test() -> int:
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        C.LEARNING_FILES = {k: Path(tmp) / Path(v).name for k, v in C.LEARNING_FILES.items()}
        for i in range(5):
            record_correction(
                week="Q2W1",
                subject="math",
                weekday="Monday",
                raw_pacing="L31",
                artifact_type="agenda-in-class",
                model_proposal="Lesson 30",
                teacher_final="Lesson 31",
                authority="OWNER_POLICY",
                source_refs=["pacing:math:Monday"],
                status="approved",
            )
        # 5 identical approvals => one promotion suggestion.
        sugg = suggest_promotions(threshold=5)
        assert len(sugg) == 1, sugg
        assert sugg[0]["count"] == 5
        assert sugg[0]["requires_explicit_approval"] is True

        # No automatic promotion happened.
        assert load_promoted_rules() == []

        # Explicit rejection must not promote.
        r = promote_rule(rule={"rule": "x"}, approved_by="test", approved=False)
        assert r["promoted"] is False

        # Explicit approval promotes.
        r = promote_rule(rule={"rule": "math Monday = Lesson N"}, approved_by="Owen Reagan", approved=True)
        assert r["promoted"] is True
        assert load_promoted_rules()[0]["authority"] == "OWNER_POLICY"

    print("PASS learning/correction self-test")
    return 0


if __name__ == "__main__":
    sys.exit(command_self_test())
