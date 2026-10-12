"""Phase 3 — Chief of Staff weekly planning loop (pacing + local AI review).

Shared constants and paths for the deterministic pacing engine, precedent
retrieval, local-LLM adapter, teacher review loop, correction memory, lifecycle
state machine, and Canvas dry-run preview.

Read-only phase: no Canvas writes. Local-first: no external network beyond the
authorized Google Sheets pacing export and the local Ollama loopback.
"""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# Authoritative live pacing source.
SPREADSHEET_ID = "1I-CNb_ZPnOozY2wSMNAWF3bzuRZWDdZt9yoSBKtLWD4"
SHEET_NAME = "4A - Reagan"

# Pacing-sheet subject row display name -> canonical subject key.
SUBJECT_ROWS: dict[str, str] = {
    "Saxon Math": "math",
    "Reading Mastery": "reading",
    "Spelling": "spelling",
    "Shurley English": "language_arts",
    "History": "history",
    "Science": "science",
}

SUBJECT_LABELS: dict[str, str] = {
    "math": "Math",
    "reading": "Reading",
    "spelling": "Spelling",
    "language_arts": "Language Arts",
    "history": "History",
    "science": "Science",
}

AUTHORITY_TYPES = ("OWNER_POLICY", "LIVE_CANVAS_PRECEDENT", "MODEL_INFERENCE")
LIFECYCLE_STATES = ("SOURCE", "PROPOSED", "TEACHER_APPROVED", "PUBLISHED_VERIFIED")

LOCAL_DIR = REPO_ROOT / ".local"
PACING_DIR = LOCAL_DIR / "pacing"
LEARNING_DIR = LOCAL_DIR / "learning"
PRECEDENT_NORM_DIR = LOCAL_DIR / "canvas-llm" / "precedent-sweep" / "normalized"
PHASE3_PREVIEW_DIR = LOCAL_DIR / "phase3-preview"

CONFIG_DIR = REPO_ROOT / "config"
CANVAS_CONFIG_DIR = CONFIG_DIR / "curriculum" / "canvas"
FPK_DIR = CONFIG_DIR / "fpk"

WEEKS_PATH = CANVAS_CONFIG_DIR / "instructional-weeks-2026-2027.json"
QUARTER_ACTIVATION_PATH = CANVAS_CONFIG_DIR / "quarter-subject-activation-2026-2027.json"
AGENDA_RULES_PATH = CANVAS_CONFIG_DIR / "agenda-page-rules.json"
WEEKLY_STANDARD_PATH = CANVAS_CONFIG_DIR / "weekly-agenda-standard-2026-2027.json"
PACING_TRANSLATION_RULES_PATH = CANVAS_CONFIG_DIR / "pacing-translation-rules-2026-2027.json"
MATH_WORK_PATTERNS_PATH = CANVAS_CONFIG_DIR / "math-work-patterns-2026-2027.json"
READING_SPELLING_WORK_PATTERNS_PATH = CANVAS_CONFIG_DIR / "reading-spelling-work-patterns-2026-2027.json"
ASSESSMENT_ANNOUNCEMENT_POLICY_PATH = CANVAS_CONFIG_DIR / "assessment-announcement-policy-2026-2027.json"
ASSIGNMENT_ROUTING_CONTRACT_PATH = CANVAS_CONFIG_DIR / "assignment-routing-contract-2026-2027.json"
COURSE_MAPPINGS_PATH = CONFIG_DIR / "curriculum" / "canvas-course-mappings.json"
ANOMALY_EXCLUSIONS_PATH = FPK_DIR / "anomaly-exclusions.json"

LEARNING_FILES = {
    "corrections": LEARNING_DIR / "teacher-corrections.jsonl",
    "approved_language": LEARNING_DIR / "approved-language.jsonl",
    "artifact_precedent": LEARNING_DIR / "artifact-precedent.jsonl",
    "promoted_rules": LEARNING_DIR / "promoted-rules.json",
    "rejected_suggestions": LEARNING_DIR / "rejected-suggestions.jsonl",
}

# Local Ollama model for the interpretation/review worker.
OLLAMA_MODEL = "qwen3.6:35b"
OLLAMA_FALLBACK_MODELS = ("qwen3.5:35b", "llama3.2:latest")
OLLAMA_BINARY = "ollama"

# Weekday order used by the instructional calendar.
WEEKDAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday")
