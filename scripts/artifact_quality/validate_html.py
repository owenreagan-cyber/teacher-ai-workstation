from __future__ import annotations

import re
from pathlib import Path

from .models import CheckStatus, PLACEHOLDER_PATTERNS, PreflightReport
from .profiles import ArtifactProfile


def validate_html(path: Path, profile: ArtifactProfile, report: PreflightReport) -> None:
    if not path.is_file():
        report.add(CheckStatus.FAIL, "HTML input file does not exist")
        return

    text = path.read_text(encoding="utf-8", errors="replace")
    report.add(CheckStatus.PASS, "HTML file opens successfully")

    lower = text.lower()
    if "@page" in lower:
        report.add(CheckStatus.PASS, "@page print rule present")
    else:
        report.add(CheckStatus.FAIL, "Missing @page print rule")

    if re.search(r"size\s*:\s*letter|8\.5in\s+11in|8\.5\s*in\s*11\s*in", lower):
        report.add(CheckStatus.PASS, "US Letter page size declared")
    else:
        report.add(CheckStatus.WARN, "US Letter page size not clearly declared")

    if "@media print" in lower:
        report.add(CheckStatus.PASS, "@media print block present")
    else:
        report.add(CheckStatus.FAIL, "Missing @media print styles")

    if "box-sizing" in lower and "border-box" in lower:
        report.add(CheckStatus.PASS, "box-sizing: border-box present")
    else:
        report.add(CheckStatus.WARN, "box-sizing: border-box not detected")

    if "break-inside: avoid" in lower or "page-break-inside: avoid" in lower:
        report.add(CheckStatus.PASS, "Page-break avoidance rules present")
    else:
        report.add(CheckStatus.WARN, "No break-inside/page-break-inside avoid rules detected")

    if re.search(r"overflow\s*:\s*hidden", lower) and re.search(r"(worksheet|passage|question|content|academic)", lower):
        report.add(CheckStatus.FAIL, "Dangerous overflow:hidden on instructional content")
    else:
        report.add(CheckStatus.PASS, "No dangerous overflow clipping detected")

    if re.search(r"position\s*:\s*fixed", lower):
        report.add(CheckStatus.WARN, "Fixed-position elements detected", details="Verify print layout at 100% scale.")
    else:
        report.add(CheckStatus.PASS, "No fixed-position elements detected")

    placeholders = [pattern for pattern in PLACEHOLDER_PATTERNS if pattern.upper() in text.upper()]
    if placeholders:
        report.add(CheckStatus.FAIL, "Unresolved placeholders detected in HTML", details=", ".join(placeholders))
    else:
        report.add(CheckStatus.PASS, "No unresolved placeholders detected in HTML")

    report.add(
        CheckStatus.WARN,
        "HTML print-to-PDF conversion not run automatically",
        details="Export or print to PDF locally, then run PDF preflight for final pagination proof.",
    )
