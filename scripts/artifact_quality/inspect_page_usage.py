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


def analyze_page_usage(page_bounds: PageBounds, profile: ArtifactProfile) -> list[tuple[CheckStatus, str, str | None]]:
    findings: list[tuple[CheckStatus, str, str | None]] = []
    left, top, right, bottom = printable_rect(profile)
    safe_left, safe_top, safe_right, safe_bottom = safe_rect(profile)
    printable_width = max(right - left, 1.0)
    printable_height = max(bottom - top, 1.0)
    printable_area = printable_width * printable_height

    if page_bounds.text_chars <= profile.page_utilization.blank_page_text_threshold:
        if page_bounds.content_left is None:
            findings.append((CheckStatus.WARN, f"Page {page_bounds.page_number} appears nearly empty", "Visual review recommended."))
            return findings

    if page_bounds.content_left is None:
        return findings

    content_width = max(page_bounds.content_right - page_bounds.content_left, 0.0)
    content_height = max(page_bounds.content_bottom - page_bounds.content_top, 0.0)
    content_area = content_width * content_height
    utilization = (content_area / printable_area) * 100.0

    if utilization < profile.page_utilization.warning_below_percent:
        findings.append(
            (
                CheckStatus.WARN,
                f"Page {page_bounds.page_number} uses {utilization:.0f}% of the printable area",
                f"Approximate content box: {content_width / POINTS_PER_INCH:.2f}\" x {content_height / POINTS_PER_INCH:.2f}\".",
            )
        )

    bottom_gap_inches = (safe_bottom - page_bounds.content_bottom) / POINTS_PER_INCH
    if bottom_gap_inches > profile.page_utilization.bottom_gap_warning_inches:
        findings.append(
            (
                CheckStatus.WARN,
                f"Page {page_bounds.page_number} has a large bottom gap ({bottom_gap_inches:.2f}\")",
                "Content may end unusually high; confirm intentional workspace or pagination.",
            )
        )

    distances = {
        "left": page_bounds.content_left - safe_left,
        "top": page_bounds.content_top - safe_top,
        "right": safe_right - page_bounds.content_right,
        "bottom": safe_bottom - page_bounds.content_bottom,
    }
    warn_threshold = profile.page_utilization.boundary_warning_inches * POINTS_PER_INCH
    for edge, distance in distances.items():
        if distance < 0:
            findings.append(
                (
                    CheckStatus.FAIL,
                    f"Page {page_bounds.page_number} content extends outside the safe {edge} boundary",
                    f"Violation by {abs(distance) / POINTS_PER_INCH:.2f}\".",
                )
            )
        elif distance < warn_threshold:
            findings.append(
                (
                    CheckStatus.WARN,
                    f"Page {page_bounds.page_number} content is close to the safe {edge} boundary",
                    f"Only {distance / POINTS_PER_INCH:.2f}\" inside safe area.",
                )
            )

    return findings


def apply_usage_findings(report: PreflightReport, findings: Iterable[tuple[CheckStatus, str, str | None]]) -> None:
    for status, message, details in findings:
        report.add(status, message, details=details)
