from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

import fitz

from .inspect_page_usage import PageBounds, analyze_blank_page, apply_usage_findings
from .models import (
    A4_HEIGHT_PT,
    A4_WIDTH_PT,
    LETTER_HEIGHT_PT,
    LETTER_WIDTH_PT,
    PLACEHOLDER_PATTERNS,
    CheckStatus,
    PreflightReport,
)
from .profiles import ArtifactProfile
from .visual_geometry import (
    PageVisualMetrics,
    analyze_page_visual,
    compute_quality_score,
    evaluate_page_thresholds,
)


def _page_orientation(width: float, height: float) -> str:
    return "landscape" if width > height else "portrait"


def _matches_letter(width: float, height: float, tolerance: float) -> bool:
    pairs = ((width, height), (height, width))
    return any(abs(w - LETTER_WIDTH_PT) <= tolerance and abs(h - LETTER_HEIGHT_PT) <= tolerance for w, h in pairs)


def _matches_a4(width: float, height: float, tolerance: float) -> bool:
    pairs = ((width, height), (height, width))
    return any(abs(w - A4_WIDTH_PT) <= tolerance and abs(h - A4_HEIGHT_PT) <= tolerance for w, h in pairs)


def _collect_page_bounds(page: fitz.Page, page_number: int) -> PageBounds:
    blocks = page.get_text("blocks")
    text = page.get_text("text")
    text_chars = len(re.sub(r"\s+", "", text))
    left = top = right = bottom = None
    for block in blocks:
        if len(block) < 5:
            continue
        x0, y0, x1, y1 = block[:4]
        left = x0 if left is None else min(left, x0)
        top = y0 if top is None else min(top, y0)
        right = x1 if right is None else max(right, x1)
        bottom = y1 if bottom is None else max(bottom, y1)
    rect = page.rect
    return PageBounds(
        page_number=page_number,
        width=rect.width,
        height=rect.height,
        content_left=left,
        content_top=top,
        content_right=right,
        content_bottom=bottom,
        text_chars=text_chars,
        orientation=_page_orientation(rect.width, rect.height),
    )


def _detect_placeholders(text: str) -> list[str]:
    hits: list[str] = []
    upper = text.upper()
    for pattern in PLACEHOLDER_PATTERNS:
        if pattern.upper() in upper:
            hits.append(pattern)
    return hits


def _font_inventory(doc: fitz.Document) -> dict[str, bool]:
    fonts: dict[str, bool] = {}
    for page in doc:
        for entry in page.get_fonts():
            font_name = entry[0]
            fonts[font_name] = True
    return fonts


def analyze_pdf_visual_geometry(
    doc: fitz.Document,
    profile: ArtifactProfile,
    report: PreflightReport,
    *,
    analysis_dpi: int | None = None,
) -> tuple[list[PageVisualMetrics], list[list[list[bool]] | None], list[fitz.Rect | None]]:
    page_metrics: list[PageVisualMetrics] = []
    ink_masks: list[list[list[bool]] | None] = []
    clips: list[fitz.Rect | None] = []
    all_findings: list[tuple[CheckStatus, str, str | None]] = []
    blank_pages: list[int] = []

    for index, page in enumerate(doc, start=1):
        bounds = _collect_page_bounds(page, index)
        all_findings.extend(analyze_blank_page(bounds, profile))

        metrics, visual_findings, mask, clip = analyze_page_visual(
            page, index, profile, dpi=analysis_dpi,
        )
        page_metrics.append(metrics)
        ink_masks.append(mask)
        clips.append(clip)
        all_findings.extend(visual_findings)
        all_findings.extend(evaluate_page_thresholds(metrics, profile))

        if (
            bounds.text_chars <= profile.page_utilization.blank_page_text_threshold
            and metrics.visible_ink_percent < profile.visual_geometry.sparse_page_ink_percent
            and metrics.drawing_coverage_percent < 1.0
        ):
            blank_pages.append(index)

    clipped_failures = [msg for status, msg, _ in all_findings if status == CheckStatus.FAIL]
    if clipped_failures:
        report.add(CheckStatus.FAIL, "Essential content extends outside safe margins")
        for message in clipped_failures:
            report.add(CheckStatus.FAIL, message)
    else:
        report.add(CheckStatus.PASS, "Essential content remains inside safe margins")

    apply_usage_findings(report, (f for f in all_findings if f[0] != CheckStatus.FAIL))

    if blank_pages:
        if blank_pages == [doc.page_count] and doc.page_count > 1:
            report.add(CheckStatus.FAIL, f"Accidental blank final page detected (page {doc.page_count})")
        elif blank_pages:
            report.add(CheckStatus.WARN, f"Nearly blank pages detected: {blank_pages}")
    else:
        report.add(CheckStatus.PASS, "No accidental blank pages detected")

    report.page_metrics = [m.to_dict() for m in page_metrics]
    return page_metrics, ink_masks, clips


def validate_pdf(
    path: Path,
    profile: ArtifactProfile,
    report: PreflightReport,
    *,
    analysis_dpi: int | None = None,
) -> tuple[fitz.Document | None, list[PageVisualMetrics], list[list[list[bool]] | None], list[fitz.Rect | None]]:
    if not path.exists():
        report.add(CheckStatus.FAIL, "Input file does not exist")
        return None, [], [], []
    if not path.is_file():
        report.add(CheckStatus.FAIL, "Input path is not a regular file")
        return None, [], [], []

    try:
        doc = fitz.open(path)
    except Exception as exc:  # noqa: BLE001
        report.add(CheckStatus.FAIL, "File is not a readable PDF", details=str(exc))
        return None, [], [], []

    report.add(CheckStatus.PASS, "File opens successfully")
    page_count = doc.page_count
    if page_count <= 0:
        report.add(CheckStatus.FAIL, "PDF has zero pages")
        doc.close()
        return None, [], [], []

    report.add(CheckStatus.PASS, f"{page_count} page{'s' if page_count != 1 else ''} detected")

    tolerance = profile.paper.size_tolerance_points
    page_sizes: list[tuple[float, float]] = []
    orientations: list[str] = []
    all_letter = True
    any_a4 = False
    for index, page in enumerate(doc, start=1):
        rect = page.rect
        page_sizes.append((rect.width, rect.height))
        orientation = _page_orientation(rect.width, rect.height)
        orientations.append(orientation)
        letter_ok = _matches_letter(rect.width, rect.height, tolerance)
        if not letter_ok:
            all_letter = False
        if _matches_a4(rect.width, rect.height, tolerance):
            any_a4 = True

    if all_letter:
        report.add(CheckStatus.PASS, "All pages are US Letter")
    elif any_a4 and profile.paper.width_points == LETTER_WIDTH_PT:
        report.add(CheckStatus.FAIL, "One or more pages use A4 instead of US Letter")
    else:
        report.add(CheckStatus.FAIL, "One or more pages are not US Letter")

    unique_sizes = {tuple(round(v, 1) for v in size) for size in page_sizes}
    if len(unique_sizes) > 1 and not profile.subject_extensions:
        report.add(CheckStatus.FAIL, "Mixed page sizes detected within one artifact")

    expected_orientation = profile.paper.orientation
    if all(o == expected_orientation for o in orientations):
        report.add(CheckStatus.PASS, f"All pages use {expected_orientation} orientation")
    else:
        unexpected = [i + 1 for i, o in enumerate(orientations) if o != expected_orientation]
        if expected_orientation == "portrait":
            report.add(CheckStatus.WARN, f"Unexpected landscape pages detected: {unexpected}")
        else:
            report.add(CheckStatus.FAIL, f"Pages not in required {expected_orientation} orientation: {unexpected}")

    page_metrics, ink_masks, clips = analyze_pdf_visual_geometry(doc, profile, report, analysis_dpi=analysis_dpi)

    full_text = "".join(page.get_text("text") for page in doc)
    placeholders = _detect_placeholders(full_text)
    if placeholders:
        report.add(CheckStatus.FAIL, "Unresolved placeholders detected", details=", ".join(sorted(set(placeholders))))
    else:
        report.add(CheckStatus.PASS, "No unresolved placeholders detected")

    if profile.requirements.page_numbers_after_first and page_count > 1:
        numbered = _pages_with_numbers(doc)
        if len(numbered) < page_count - 1:
            report.add(CheckStatus.WARN, "Page numbers may be missing on multi-page packet", details=f"Detected on pages: {numbered or 'none'}")
        else:
            report.add(CheckStatus.PASS, "Page numbers detected on multi-page packet")

    fonts = _font_inventory(doc)
    if fonts:
        report.add(CheckStatus.PASS, f"Font inventory captured ({len(fonts)} fonts)")
        if not _fonts_embedded(doc):
            report.add(CheckStatus.WARN, "Font embedding cannot be fully confirmed", details="Manual print proof recommended.")
    else:
        report.add(CheckStatus.WARN, "Font inventory unavailable", details="No fonts detected via page scan.")

    return doc, page_metrics, ink_masks, clips


def finalize_quality_score(report: PreflightReport, page_metrics: list[PageVisualMetrics]) -> None:
    pass_count = sum(1 for c in report.checks if c.status == CheckStatus.PASS)
    total = max(len(report.checks), 1)
    fail_count = sum(1 for c in report.checks if c.status == CheckStatus.FAIL)
    warn_count = sum(1 for c in report.checks if c.status == CheckStatus.WARN)
    score = compute_quality_score(pass_count / total, page_metrics, fail_count, warn_count)
    report.quality_score = score.to_dict()
    report.add(
        CheckStatus.PASS,
        f"Quality score — mechanical: {score.mechanical_score:.0f}, visual heuristic: {score.visual_heuristic_score:.0f}",
        details=f"Instructional status: {score.instructional_status}. Scores do not override FAIL.",
    )


def _pages_with_numbers(doc: fitz.Document) -> list[int]:
    numbered: list[int] = []
    for index, page in enumerate(doc, start=1):
        text = page.get_text("text")
        if re.search(r"\b\d+\s*/\s*\d+\b", text) or re.search(r"(?m)^\s*\d+\s*$", text):
            numbered.append(index)
    return numbered


def _fonts_embedded(doc: fitz.Document) -> bool:
    for page in doc:
        for entry in page.get_fonts():
            if len(entry) > 2 and str(entry[2]).lower() == "type1":
                return True
            ext = entry[1].lower() if len(entry) > 1 and isinstance(entry[1], str) else ""
            if ext in {"ttf", "otf", "cff", "cid"}:
                return True
    return False
