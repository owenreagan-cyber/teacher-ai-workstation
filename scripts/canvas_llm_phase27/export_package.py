from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

REQUIRED_EXPORT_FILES = [
    "canvas-snapshot.json",
    "safety-diff.json",
    "safety-diff-summary.txt",
    "deployment-manifest-v1.json",
    "module-placement-plan.json",
    "dependency-graph.json",
    "health-check-report.json",
    "deployment-ledger-export.json",
    "rollback-plan.json",
    "transport-readiness.json",
    "validation-report.json",
]

# Absolute and repo-root-anchored -- see ledger.py's DEFAULT_LEDGER_PATH for
# why a relative default here would be cwd-dependent and unsafe (Phase 26's
# `serve` command chdirs before Phase 27 code runs).
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_EXPORT_ROOT = (
    REPO_ROOT / ".local/canvas-llm/phase-27-canvas-readiness-and-safety-diff/exports"
)

_FORBIDDEN_CONTENT_PATTERNS = [
    re.compile(r"/Users/[A-Za-z0-9_.\-]+"),
    re.compile(r"[Aa]uthorization\s*:\s*Bearer"),
    re.compile(r"\bstudentId\b"),
]


class ExportPackageError(RuntimeError):
    pass


def generate_teacher_summary(diffs: list[dict[str, Any]]) -> str:
    lines = []
    for d in diffs:
        lines.append(f"{d['localTitle'] or d['objectId']}")
        lines.append(d["comparisonStatus"])
        if d.get("fieldDiffs"):
            for fd in d["fieldDiffs"]:
                lines.append(f"  {fd['field']}: {fd['changeKind']}")
        else:
            lines.append("  No field changes")
        if d.get("modulePlacement", {}).get("status") not in (None, "already-correct"):
            lines.append(f"  Module: {d['modulePlacement']['status']}")
        if d.get("blockers"):
            lines.append(f"  Blocked: {'; '.join(d['blockers'])}")
        lines.append(f"  Approval: {d.get('approvalState', 'Needs Review')}")
        lines.append("")
    return "\n".join(lines)


def _scan_for_forbidden_content(text: str, where: str) -> None:
    for pattern in _FORBIDDEN_CONTENT_PATTERNS:
        if pattern.search(text):
            raise ExportPackageError(f"forbidden content pattern {pattern.pattern!r} found in {where}")


def export_package(
    week_code: str,
    diffs: list[dict[str, Any]],
    manifest: dict[str, Any],
    snapshot: dict[str, Any],
    health_results: list[dict[str, Any]],
    rollback_plan: list[dict[str, Any]],
    ledger_events: list[dict[str, Any]],
    root: Path | None = None,
) -> Path:
    export_dir = Path(root or DEFAULT_EXPORT_ROOT) / week_code
    export_dir.mkdir(parents=True, exist_ok=True)

    files: dict[str, str] = {
        "canvas-snapshot.json": json.dumps(snapshot, indent=2, sort_keys=True),
        "safety-diff.json": json.dumps(diffs, indent=2, sort_keys=True),
        "safety-diff-summary.txt": generate_teacher_summary(diffs),
        "deployment-manifest-v1.json": json.dumps(manifest, indent=2, sort_keys=True),
        "module-placement-plan.json": json.dumps(
            [d.get("modulePlacement") for d in diffs], indent=2, sort_keys=True
        ),
        "dependency-graph.json": json.dumps(
            manifest.get("dependencies", {}), indent=2, sort_keys=True
        ),
        "health-check-report.json": json.dumps(health_results, indent=2, sort_keys=True),
        "deployment-ledger-export.json": json.dumps(ledger_events, indent=2, sort_keys=True),
        "rollback-plan.json": json.dumps(rollback_plan, indent=2, sort_keys=True),
        "transport-readiness.json": json.dumps(
            {"defaultTransport": "DisabledCanvasTransport", "liveReadOnlyEnabled": False},
            indent=2,
        ),
        "validation-report.json": json.dumps(
            {"failCount": manifest.get("validationSummary", {}).get("failCount", 0)}, indent=2
        ),
    }

    for name, content in files.items():
        _scan_for_forbidden_content(content, name)

    for name, content in files.items():
        (export_dir / name).write_text(content, encoding="utf-8")

    return export_dir


def validate_export_package(export_dir: Path) -> list[str]:
    """Returns a list of problems; empty list means the package is valid."""
    problems = []
    for name in REQUIRED_EXPORT_FILES:
        path = export_dir / name
        if not path.exists():
            problems.append(f"missing required export file: {name}")
            continue
        _content = path.read_text(encoding="utf-8")
        for pattern in _FORBIDDEN_CONTENT_PATTERNS:
            if pattern.search(_content):
                problems.append(f"forbidden content pattern in {name}: {pattern.pattern}")
    return problems
