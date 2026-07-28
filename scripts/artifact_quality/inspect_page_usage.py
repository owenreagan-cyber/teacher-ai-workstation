from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .models import POINTS_PER_INCH, CheckStatus, PreflightReport
from .profiles import ArtifactProfile


@dataclass
class PageBounds:
    page_number: int
    width: float
    height: float
    content_left: float | None
    content_top: float | None
    content_right: float | None
    content_bottom: float | None
    text_chars: int
    orientation: str


def printable_rect(profile: ArtifactProfile) -> tuple[float, float, float, float]:
    left = profile.margins.left_inches * POINTS_PER_INCH
    top = profile.margins.top_inches * POINTS_PER_INCH
    right = profile.paper.width_points - profile.margins.right_inches * POINTS_PER_INCH
    bottom = profile.paper.height_points - profile.margins.bottom_inches * POINTS_PER_INCH
    return left, top, right, bottom


def safe_rect(profile: ArtifactProfile) -> tuple[float, float, float, float]:
    left, top, right, bottom = printable_rect(profile)
    inset = profile.safe_boundary_inches * POINTS_PER_INCH
    return left + inset, top + inset, right - inset, bottom - inset


def analyze_blank_page(page_bounds: PageBounds, profile: ArtifactProfile) -> list[tuple[CheckStatus, str, str | None]]:
    """Text-only blank page heuristic — visual metrics provide fuller coverage analysis."""
    findings: list[tuple[CheckStatus, str, str | None]] = []
    if page_bounds.text_chars <= profile.page_utilization.blank_page_text_threshold:
        if page_bounds.content_left is None:
            findings.append(
                (
                    CheckStatus.WARN,
                    f"Page {page_bounds.page_number} appears nearly empty (text-only check)",
                    "Visual review recommended; drawing/ink metrics may show structure.",
                )
            )
    return findings


def apply_usage_findings(report: PreflightReport, findings: Iterable[tuple[CheckStatus, str, str | None]]) -> None:
    for status, message, details in findings:
        report.add(status, message, details=details)
