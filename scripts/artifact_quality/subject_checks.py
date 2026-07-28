from __future__ import annotations

from pathlib import Path

import fitz

from .models import CheckStatus, PreflightReport
from .profiles import ArtifactProfile


SUBJECT_DOCS = {
    "math": "standards/instructional-artifacts/subjects/math.md",
    "shurley": "standards/instructional-artifacts/subjects/shurley-grammar.md",
    "reading": "standards/instructional-artifacts/subjects/reading.md",
    "history": "standards/instructional-artifacts/subjects/history.md",
    "science": "standards/instructional-artifacts/subjects/science.md",
}


def apply_subject_checks(
    subject: str | None,
    profile: ArtifactProfile,
    report: PreflightReport,
    *,
    doc: fitz.Document | None = None,
    source_path: Path | None = None,
) -> None:
    if not subject:
        return

    normalized = subject.lower().replace("_", "-")
    doc_rel = SUBJECT_DOCS.get(normalized)
    if doc_rel:
        doc_path = Path(__file__).resolve().parents[2] / doc_rel
        if doc_path.is_file():
            report.add(CheckStatus.PASS, f"Subject profile documented: {normalized}")
        else:
            report.add(CheckStatus.WARN, f"Subject documentation missing for {normalized}")
    else:
        report.add(CheckStatus.WARN, f"Unknown subject '{subject}' — generic profile only")

    text = ""
    if doc is not None:
        text = "".join(page.get_text("text") for page in doc)
    elif source_path and source_path.suffix.lower() in {".html", ".htm"}:
        text = source_path.read_text(encoding="utf-8", errors="replace")

    if normalized == "shurley" and profile.requirements.require_single_line_sentences and text:
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("Directions"):
                continue
            if len(stripped) > 70 and " " in stripped and stripped.count(".") <= 1:
                report.add(
                    CheckStatus.FAIL,
                    "Shurley sentence appears wrapped across layout lines",
                    details=f"Line: {stripped[:80]}",
                )
                break
        else:
            report.add(CheckStatus.PASS, "Shurley single-line sentence layout check passed")

    manual_checks = {
        "math": "Manual instructional review: computation space, vertical alignment, symbol rendering.",
        "reading": "Manual instructional review: passage/question separation, line numbers, response spacing.",
        "history": "Manual instructional review: timeline order, map labels, grayscale usability.",
        "science": "Manual instructional review: diagram labels, process arrows, table grouping.",
    }
    if normalized in manual_checks:
        report.add(CheckStatus.WARN, manual_checks[normalized])

    extensions = (profile.subject_extensions or {}).get(normalized)
    if extensions:
        report.add(CheckStatus.PASS, f"Profile subject extensions loaded for {normalized}")
