"""Part D — bounded local-AI adapter (Ollama).

The local model (qwen3.6:35b) acts as the reasoning worker inside the Chief,
not as a coding assistant. It receives normalized pacing + owner policy +
teacher-approved precedent + artifact schema, and returns structured JSON
proposals with per-field provenance.

It does NOT receive: Canvas token, Gmail/OAuth secrets, student grades, rosters,
parent data, or raw API dumps. It never writes to Canvas.

Deterministic extraction remains authoritative; if the model is unavailable we
WARN and preserve deterministic extraction (never block raw pacing review).
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from typing import Any

from . import constants as C

# Required model instruction (see mission Part D).
_SYSTEM_INSTRUCTION = (
    "You are the local reasoning worker inside a teacher's Chief of Staff for "
    "Canvas weekly planning. Translate only supported information. Preserve "
    "unresolved information as unresolved. Never invent homework, page numbers, "
    "problem ranges, tests, dates, points, or curriculum meaning. Distinguish "
    "source evidence from precedent. A precedent is not automatically a rule. "
    "Output STRICT JSON only — no prose, no markdown fences."
)


def ollama_models() -> list[str]:
    try:
        out = subprocess.run(
            [C.OLLAMA_BINARY, "list"], capture_output=True, text=True, timeout=20
        )
        names: list[str] = []
        for line in out.stdout.splitlines()[1:]:
            name = line.split()[0] if line.split() else ""
            if name:
                names.append(name)
        return names
    except Exception:  # noqa: BLE001
        return []


def model_available(model: str = C.OLLAMA_MODEL) -> bool:
    return model in ollama_models()


def run_model(prompt: str, model: str = C.OLLAMA_MODEL, timeout: int = 300) -> dict[str, Any]:
    """Run the local model and return structured JSON. Raises on failure."""
    if not model_available(model):
        raise RuntimeError(f"model {model!r} not present in `ollama list`")
    proc = subprocess.run(
        [C.OLLAMA_BINARY, "run", model, "--format", "json", "--nowordwrap"],
        input=_SYSTEM_INSTRUCTION + "\n\n" + prompt,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"ollama exited {proc.returncode}: {proc.stderr.strip()[:200]}")
    raw = proc.stdout.strip()
    if not raw:
        raise RuntimeError("ollama returned empty output")
    return _parse_json(raw)


def _parse_json(raw: str) -> dict[str, Any]:
    # Prefer a direct object; fall back to the first balanced {...} block.
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass
    start = raw.find("{")
    if start == -1:
        raise RuntimeError("no JSON object found in model output")
    depth = 0
    for i in range(start, len(raw)):
        ch = raw[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                data = json.loads(raw[start : i + 1])
                if isinstance(data, dict):
                    return data
                raise RuntimeError("first balanced JSON block is not an object")
    raise RuntimeError("unbalanced JSON in model output")


def build_proposal_prompt(week: dict[str, Any], bundle: dict[str, Any], subject: str) -> str:
    """Compose the model prompt from normalized pacing + policy + precedent."""
    days = week.get("days", {})
    subject_days = {
        wd: day["subjects"].get(subject, {}).get("raw", "")
        for wd, day in days.items()
    }
    # Trim policy to a compact, safe view (no secrets present by construction).
    policy_slim = [
        {"domain": r["domain"], "data": r["data"]} for r in bundle.get("policy", [])
    ]
    teacher_slim = [
        {k: r.get(k) for k in ("subject", "artifact_type", "teacher_final", "rule", "authority")}
        for r in bundle.get("teacher_approved", [])
    ]
    precedent_slim = [
        {"domain": r["domain"], "data": r["data"]} for r in bundle.get("live_precedent", [])
    ]
    payload = {
        "task": "propose one week of Canvas agenda content for a single subject",
        "week": week.get("week"),
        "subject": subject,
        "rawPacingByWeekday": subject_days,
        "ownerPolicy": policy_slim,
        "teacherApproved": teacher_slim,
        "livePrecedent": precedent_slim,
        "outputSchema": {
            "proposals": {
                "<Weekday>": {
                    "inClass": PROVENANCE_FIELD,
                    "atHome": PROVENANCE_FIELD,
                }
            },
            "unresolved": ["string"],
        },
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


PROVENANCE_FIELD = {
    "value": "string | null",
    "status": "PROPOSED",
    "authority": "MODEL_INFERENCE",
    "derivedFrom": ["string"],
    "confidence": "high|medium|low",
    "requiresTeacherApproval": True,
}


def propose_subject(week: dict[str, Any], bundle: dict[str, Any], subject: str) -> dict[str, Any]:
    """Run the local model for one subject. Returns a structured result (never raises)."""
    if not model_available():
        return {
            "subject": subject,
            "status": "WARN",
            "reason": "local model unavailable",
            "authority": "MODEL_INFERENCE",
            "proposals": {},
            "unresolved": list(week.get("days", {}).keys()),
        }
    prompt = build_proposal_prompt(week, bundle, subject)
    try:
        data = run_model(prompt)
        return {
            "subject": subject,
            "status": "OK",
            "model": C.OLLAMA_MODEL,
            "authority": "MODEL_INFERENCE",
            "proposals": data.get("proposals", {}),
            "unresolved": data.get("unresolved", []),
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "subject": subject,
            "status": "WARN",
            "reason": type(exc).__name__ + ": " + str(exc)[:200],
            "model": C.OLLAMA_MODEL,
            "authority": "MODEL_INFERENCE",
            "proposals": {},
            "unresolved": list(week.get("days", {}).keys()),
        }


def command_self_test() -> int:
    # Structured JSON parsing (no model required).
    assert _parse_json('{"a": 1}') == {"a": 1}
    assert _parse_json('prefix {"b": [1,2]} suffix') == {"b": [1, 2]}
    try:
        _parse_json("no json here")
        raise AssertionError("expected RuntimeError")
    except RuntimeError:
        pass
    # Provenance field shape.
    assert PROVENANCE_FIELD["authority"] == "MODEL_INFERENCE"
    assert PROVENANCE_FIELD["requiresTeacherApproval"] is True
    print("PASS local LLM adapter self-test")
    return 0


if __name__ == "__main__":
    sys.exit(command_self_test())
