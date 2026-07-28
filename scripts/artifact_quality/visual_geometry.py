"""Rendered-page visual geometry metrics for PDF preflight.

Metrics are conservative heuristics — not proof of instructional quality.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

import fitz
from PIL import Image, ImageDraw, ImageFont

from .inspect_page_usage import printable_rect, safe_rect
from .models import POINTS_PER_INCH, CheckStatus
from .profiles import ArtifactProfile, VisualGeometrySpec


@dataclass
class PageVisualMetrics:
    page_number: int
    width: float
    height: float
    orientation: str
    text_coverage_percent: float = 0.0
    drawing_coverage_percent: float = 0.0
    visible_ink_percent: float = 0.0
    writing_space_percent: float = 0.0
    bottom_whitespace_inches: float = 0.0
    safe_margin_state: str = "PASS"
    page_balance: str = "PASS"
    confidence_notes: list[str] = field(default_factory=list)
    render_path: str | None = None
    annotated_render_path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "page_number": self.page_number,
            "width": round(self.width, 2),
            "height": round(self.height, 2),
            "orientation": self.orientation,
            "text_coverage_percent": round(self.text_coverage_percent, 1),
            "drawing_coverage_percent": round(self.drawing_coverage_percent, 1),
            "visible_ink_percent": round(self.visible_ink_percent, 1),
            "writing_space_percent": round(self.writing_space_percent, 1),
            "bottom_whitespace_inches": round(self.bottom_whitespace_inches, 2),
            "safe_margin_state": self.safe_margin_state,
            "page_balance": self.page_balance,
            "confidence_notes": self.confidence_notes,
            "render_path": self.render_path,
            "annotated_render_path": self.annotated_render_path,
        }


@dataclass
class QualityScore:
    mechanical_score: float
    visual_heuristic_score: float
    instructional_status: str = "Manual Review Required"

    def to_dict(self) -> dict[str, Any]:
        return {
            "mechanical_score": round(self.mechanical_score, 1),
            "visual_heuristic_score": round(self.visual_heuristic_score, 1),
            "instructional_status": self.instructional_status,
        }


def _page_orientation(width: float, height: float) -> str:
    return "landscape" if width > height else "portrait"


def _union_area(rects: Iterable[tuple[float, float, float, float]]) -> float:
    """Conservative union estimate via grid sampling (avoids double-counting overlap)."""
    rects = list(rects)
    if not rects:
        return 0.0
    min_x = min(r[0] for r in rects)
    min_y = min(r[1] for r in rects)
    max_x = max(r[2] for r in rects)
    max_y = max(r[3] for r in rects)
    span_w = max(max_x - min_x, 1.0)
    span_h = max(max_y - min_y, 1.0)
    grid = 32
    cell_w = span_w / grid
    cell_h = span_h / grid
    covered = 0
    for gy in range(grid):
        cy = min_y + (gy + 0.5) * cell_h
        for gx in range(grid):
            cx = min_x + (gx + 0.5) * cell_w
            for x0, y0, x1, y1 in rects:
                if x0 <= cx <= x1 and y0 <= cy <= y1:
                    covered += 1
                    break
    return (covered / (grid * grid)) * span_w * span_h


def compute_text_coverage(page: fitz.Page, profile: ArtifactProfile) -> float:
    left, top, right, bottom = printable_rect(profile)
    printable_area = max((right - left) * (bottom - top), 1.0)
    blocks = page.get_text("blocks")
    rects: list[tuple[float, float, float, float]] = []
    for block in blocks:
        if len(block) < 5:
            continue
        x0, y0, x1, y1 = block[:4]
        if x1 <= left or x0 >= right or y1 <= top or y0 >= bottom:
            continue
        rects.append((max(x0, left), max(y0, top), min(x1, right), min(y1, bottom)))
    if not rects:
        return 0.0
    return min((_union_area(rects) / printable_area) * 100.0, 100.0)


def _drawing_element_area(item: dict[str, Any]) -> float:
    rect = item.get("rect")
    if rect is not None:
        w = max(rect.width, 0.0)
        h = max(rect.height, 0.0)
        if item.get("type") == "l":
            return max(w, h) * 0.02 * POINTS_PER_INCH
        if item.get("type") == "re":
            fill = item.get("fill")
            if fill is None:
                stroke = max(w, h) * 0.015 * POINTS_PER_INCH
                return max(w * h * 0.05, stroke)
            return w * h
        return w * h * 0.1
    items = item.get("items")
    if not items:
        return 0.0
    total = 0.0
    for sub in items:
        if isinstance(sub, dict):
            total += _drawing_element_area(sub)
        elif isinstance(sub, (list, tuple)) and len(sub) >= 2:
            if sub[0] == "l" and len(sub) >= 3:
                p1, p2 = sub[1], sub[2]
                length = math.hypot(p2.x - p1.x, p2.y - p1.y)
                total += length * 0.015 * POINTS_PER_INCH
            elif sub[0] == "re" and len(sub) >= 2:
                r = sub[1]
                w, h = max(r.width, 0.0), max(r.height, 0.0)
                total += w * h * 0.05
    return total


def compute_drawing_coverage(page: fitz.Page, profile: ArtifactProfile) -> float:
    left, top, right, bottom = printable_rect(profile)
    printable_area = max((right - left) * (bottom - top), 1.0)
    try:
        drawings = page.get_drawings()
    except Exception:  # noqa: BLE001
        return 0.0
    total_area = 0.0
    for drawing in drawings:
        rect = drawing.get("rect")
        if rect is not None:
            if rect.x1 <= left or rect.x0 >= right or rect.y1 <= top or rect.y0 >= bottom:
                continue
        total_area += _drawing_element_area(drawing)
    return min((total_area / printable_area) * 100.0, 100.0)


def _render_printable_clip(page: fitz.Page, profile: ArtifactProfile, dpi: int) -> tuple[Image.Image, fitz.Rect]:
    left, top, right, bottom = printable_rect(profile)
    clip = fitz.Rect(left, top, right, bottom)
    scale = dpi / 72.0
    matrix = fitz.Matrix(scale, scale)
    pix = page.get_pixmap(matrix=matrix, clip=clip, alpha=False)
    image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    pix = None
    return image, clip


def _estimate_background_luminance(image: Image.Image, sample_border: int = 8) -> float:
    w, h = image.size
    pixels: list[float] = []
    for x in range(w):
        for y in list(range(min(sample_border, h))) + list(range(max(0, h - sample_border), h)):
            r, g, b = image.getpixel((x, y))
            pixels.append(0.299 * r + 0.587 * g + 0.114 * b)
    for y in range(h):
        for x in list(range(min(sample_border, w))) + list(range(max(0, w - sample_border), w)):
            r, g, b = image.getpixel((x, y))
            pixels.append(0.299 * r + 0.587 * g + 0.114 * b)
    if not pixels:
        return 255.0
    pixels.sort()
    return pixels[len(pixels) // 2]


def compute_visible_ink(image: Image.Image, spec: VisualGeometrySpec) -> tuple[float, list[list[bool]]]:
    bg = _estimate_background_luminance(image)
    threshold = spec.background_luminance_delta
    w, h = image.size
    mask: list[list[bool]] = [[False] * w for _ in range(h)]
    ink_count = 0
    for y in range(h):
        row = mask[y]
        for x in range(w):
            r, g, b = image.getpixel((x, y))
            lum = 0.299 * r + 0.587 * g + 0.114 * b
            if abs(lum - bg) >= threshold:
                row[x] = True
                ink_count += 1
    total = max(w * h, 1)
    return (ink_count / total) * 100.0, mask


def _detect_horizontal_lines(page: fitz.Page, profile: ArtifactProfile, min_width_ratio: float = 0.4) -> list[tuple[float, float, float, float]]:
    left, top, right, bottom = printable_rect(profile)
    printable_width = right - left
    min_width = printable_width * min_width_ratio
    lines: list[tuple[float, float, float, float]] = []
    try:
        drawings = page.get_drawings()
    except Exception:  # noqa: BLE001
        drawings = []
    for drawing in drawings:
        for item in drawing.get("items", []):
            if not isinstance(item, (list, tuple)) or len(item) < 3:
                continue
            if item[0] != "l":
                continue
            p1, p2 = item[1], item[2]
            if abs(p1.y - p2.y) <= 2.0 and abs(p1.x - p2.x) >= min_width:
                x0, x1 = sorted((p1.x, p2.x))
                y = (p1.y + p2.y) / 2.0
                lines.append((x0, y - 1, x1, y + 1))
    return lines


def _detect_answer_boxes(page: fitz.Page, profile: ArtifactProfile) -> list[tuple[float, float, float, float]]:
    left, top, right, bottom = printable_rect(profile)
    boxes: list[tuple[float, float, float, float]] = []
    try:
        drawings = page.get_drawings()
    except Exception:  # noqa: BLE001
        drawings = []
    for drawing in drawings:
        rect = drawing.get("rect")
        if rect is None:
            continue
        w, h = rect.width, rect.height
        if w < 40 or h < 12:
            continue
        if h > 80 or w > (right - left) * 0.95:
            continue
        if rect.x0 >= left and rect.x1 <= right and rect.y0 >= top and rect.y1 <= bottom:
            if drawing.get("fill") is None:
                boxes.append((rect.x0, rect.y0, rect.x1, rect.y1))
    return boxes


def estimate_writing_space(
    page: fitz.Page,
    profile: ArtifactProfile,
    ink_mask: list[list[bool]] | None,
    clip: fitz.Rect,
    dpi: int,
) -> float:
    left, top, right, bottom = printable_rect(profile)
    printable_area = max((right - left) * (bottom - top), 1.0)
    scale = dpi / 72.0
    writing_area = 0.0

    h_lines = _detect_horizontal_lines(page, profile)
    if len(h_lines) >= 3:
        band_height = 0.0
        if len(h_lines) >= 2:
            ys = sorted((l[1] + l[3]) / 2.0 for l in h_lines)
            gaps = [ys[i + 1] - ys[i] for i in range(len(ys) - 1)]
            band_height = sum(g for g in gaps if 8 <= g <= 40) / max(len([g for g in gaps if 8 <= g <= 40]), 1)
        for x0, y0, x1, y1 in h_lines:
            line_h = max(band_height, 14.0)
            writing_area += (x1 - x0) * line_h * 0.6

    for x0, y0, x1, y1 in _detect_answer_boxes(page, profile):
        writing_area += (x1 - x0) * (y1 - y0) * 0.7

    text = page.get_text("text")
    if "______" in text or "_____" in text:
        for block in page.get_text("blocks"):
            if len(block) < 5:
                continue
            content = block[4] if len(block) > 4 else ""
            if isinstance(content, str) and ("___" in content or "..." in content):
                x0, y0, x1, y1 = block[:4]
                writing_area += max((x1 - x0) * (y1 - y0) * 0.5, 0.0)

    return min((writing_area / printable_area) * 100.0, 100.0)


def compute_bottom_whitespace(
    ink_mask: list[list[bool]],
    clip: fitz.Rect,
    dpi: int,
    spec: VisualGeometrySpec,
    writing_space_percent: float,
) -> float:
    h = len(ink_mask)
    w = len(ink_mask[0]) if h else 0
    if h == 0 or w == 0:
        return (clip.height) / POINTS_PER_INCH

    row_threshold = max(int(w * spec.ink_row_coverage_ratio), 3)
    footer_rows = max(int(h * spec.footer_band_ratio), 1)
    lowest_ink_row = -1
    for y in range(h - footer_rows - 1, -1, -1):
        if sum(1 for x in range(w) if ink_mask[y][x]) >= row_threshold:
            lowest_ink_row = y
            break

    if lowest_ink_row < 0:
        return (clip.height) / POINTS_PER_INCH

    remaining_px = h - 1 - lowest_ink_row
    gap_inches = (remaining_px / dpi)
    if writing_space_percent >= spec.writing_space_min_percent and gap_inches > spec.bottom_gap_warning_inches * 0.5:
        gap_inches *= max(0.3, 1.0 - writing_space_percent / 100.0)
    return gap_inches


def classify_page_balance(
    ink_mask: list[list[bool]],
    spec: VisualGeometrySpec,
    text_coverage: float,
    visible_ink: float,
) -> tuple[str, list[str]]:
    h = len(ink_mask)
    w = len(ink_mask[0]) if h else 0
    notes: list[str] = []
    if h == 0 or w == 0:
        return "PASS", notes

    band_h = h // 4
    bands = []
    for i in range(4):
        y0 = i * band_h
        y1 = h if i == 3 else (i + 1) * band_h
        count = sum(1 for y in range(y0, y1) for x in range(w) if ink_mask[y][x])
        bands.append(count / max((y1 - y0) * w, 1))

    top_half = sum(bands[:2]) / 2.0
    bottom_half = sum(bands[2:]) / 2.0
    total_ink = sum(bands) / 4.0

    if visible_ink < spec.sparse_page_ink_percent and text_coverage < 5.0:
        notes.append("Nearly blank page detected")
        return "sparse", notes
    if text_coverage < 8.0 and visible_ink < spec.sparse_page_ink_percent * 1.5 and top_half > bottom_half * 3:
        notes.append("Title-only or header-heavy page")
        return "title-only", notes
    if top_half > bottom_half * spec.page_balance_top_heavy_ratio and bottom_half < spec.page_balance_sparse_band:
        notes.append("Strongly top-heavy layout")
        return "top-heavy", notes
    if bottom_half > top_half * spec.page_balance_top_heavy_ratio and top_half < spec.page_balance_sparse_band:
        notes.append("Strongly bottom-heavy layout")
        return "bottom-heavy", notes
    if visible_ink > spec.dense_page_ink_percent:
        notes.append("Unusually dense page")
        return "dense", notes
    if bands[2] + bands[3] < spec.page_balance_sparse_band and top_half > 0.02:
        notes.append("Excessive empty lower half")
        return "empty-lower", notes
    return "PASS", notes


def analyze_safe_margins(
    page: fitz.Page,
    profile: ArtifactProfile,
    ink_mask: list[list[bool]] | None,
    clip: fitz.Rect,
    dpi: int,
) -> tuple[str, list[tuple[CheckStatus, str, str | None]]]:
    findings: list[tuple[CheckStatus, str, str | None]] = []
    safe_left, safe_top, safe_right, safe_bottom = safe_rect(profile)
    page_num = page.number + 1

    if page.rect.width <= 0 or page.rect.height <= 0:
        findings.append((CheckStatus.FAIL, f"Page {page_num} has invalid geometry", None))
        return "FAIL", findings

    if ink_mask is not None and len(ink_mask) > 0:
        h = len(ink_mask)
        w = len(ink_mask[0])
        scale = dpi / 72.0
        ink_points: list[tuple[float, float]] = []
        for y in range(h):
            for x in range(w):
                if ink_mask[y][x]:
                    px = clip.x0 + x / scale
                    py = clip.y0 + y / scale
                    ink_points.append((px, py))
        if ink_points:
            min_x = min(p[0] for p in ink_points)
            min_y = min(p[1] for p in ink_points)
            max_x = max(p[0] for p in ink_points)
            max_y = max(p[1] for p in ink_points)
            warn_pt = profile.page_utilization.boundary_warning_inches * POINTS_PER_INCH
            for edge, val, bound in (
                ("left", min_x, safe_left),
                ("top", min_y, safe_top),
                ("right", max_x, safe_right),
                ("bottom", max_y, safe_bottom),
            ):
                if edge in ("right", "bottom"):
                    distance = bound - val
                    violation = val - bound
                else:
                    distance = val - bound
                    violation = bound - val
                if violation > 1.0:
                    findings.append(
                        (
                            CheckStatus.FAIL,
                            f"Page {page_num} essential content extends outside the safe {edge} boundary",
                            f"Violation by {violation / POINTS_PER_INCH:.2f}\".",
                        )
                    )
                elif distance < warn_pt:
                    findings.append(
                        (
                            CheckStatus.WARN,
                            f"Page {page_num} content is close to the safe {edge} boundary",
                            f"Only {max(distance, 0) / POINTS_PER_INCH:.2f}\" inside safe area.",
                        )
                    )

    state = "FAIL" if any(f[0] == CheckStatus.FAIL for f in findings) else (
        "WARN" if any(f[0] == CheckStatus.WARN for f in findings) else "PASS"
    )
    return state, findings


def analyze_page_visual(
    page: fitz.Page,
    page_number: int,
    profile: ArtifactProfile,
    *,
    dpi: int | None = None,
    render_path: str | None = None,
) -> tuple[PageVisualMetrics, list[tuple[CheckStatus, str, str | None]], list[list[bool]] | None, fitz.Rect | None]:
    spec = profile.visual_geometry
    analysis_dpi = dpi or spec.analysis_dpi
    rect = page.rect
    metrics = PageVisualMetrics(
        page_number=page_number,
        width=rect.width,
        height=rect.height,
        orientation=_page_orientation(rect.width, rect.height),
        render_path=render_path,
    )
    findings: list[tuple[CheckStatus, str, str | None]] = []

    metrics.text_coverage_percent = compute_text_coverage(page, profile)
    metrics.drawing_coverage_percent = compute_drawing_coverage(page, profile)

    try:
        image, clip = _render_printable_clip(page, profile, analysis_dpi)
    except Exception as exc:  # noqa: BLE001
        metrics.confidence_notes.append(f"Render failed: {exc}")
        findings.append((CheckStatus.WARN, f"Page {page_number} visual render failed", str(exc)))
        return metrics, findings, None, None

    metrics.visible_ink_percent, ink_mask = compute_visible_ink(image, spec)
    metrics.writing_space_percent = estimate_writing_space(page, profile, ink_mask, clip, analysis_dpi)
    metrics.bottom_whitespace_inches = compute_bottom_whitespace(
        ink_mask, clip, analysis_dpi, spec, metrics.writing_space_percent,
    )

    balance, balance_notes = classify_page_balance(
        ink_mask, spec, metrics.text_coverage_percent, metrics.visible_ink_percent,
    )
    metrics.page_balance = balance
    metrics.confidence_notes.extend(balance_notes)

    margin_state, margin_findings = analyze_safe_margins(page, profile, ink_mask, clip, analysis_dpi)
    metrics.safe_margin_state = margin_state
    findings.extend(margin_findings)

    image.close()
    return metrics, findings, ink_mask, clip


def evaluate_page_thresholds(
    metrics: PageVisualMetrics,
    profile: ArtifactProfile,
) -> list[tuple[CheckStatus, str, str | None]]:
    spec = profile.visual_geometry
    findings: list[tuple[CheckStatus, str, str | None]] = []
    pn = metrics.page_number

    summary = (
        f"Page {pn} visual metrics:\n"
        f"  Text coverage: {metrics.text_coverage_percent:.0f}%\n"
        f"  Drawing coverage: {metrics.drawing_coverage_percent:.0f}%\n"
        f"  Visible ink: {metrics.visible_ink_percent:.0f}%\n"
        f"  Estimated writing space: {metrics.writing_space_percent:.0f}%\n"
        f"  Bottom whitespace: {metrics.bottom_whitespace_inches:.2f} in\n"
        f"  Page balance: {metrics.page_balance.upper()}"
    )
    findings.append((CheckStatus.PASS, summary, None))

    ws_min, ws_max = spec.writing_space_range
    if metrics.writing_space_percent > 0 and (metrics.writing_space_percent < ws_min or metrics.writing_space_percent > ws_max):
        findings.append(
            (
                CheckStatus.WARN,
                f"Page {pn} estimated structured writing space ({metrics.writing_space_percent:.0f}%) outside profile range ({ws_min:.0f}–{ws_max:.0f}%)",
                "Heuristic estimate only; confirm intentional layout.",
            )
        )

    if metrics.bottom_whitespace_inches > spec.bottom_gap_warning_inches:
        if metrics.writing_space_percent < spec.writing_space_min_percent:
            findings.append(
                (
                    CheckStatus.WARN,
                    f"Page {pn} has a large bottom gap ({metrics.bottom_whitespace_inches:.2f}\")",
                    "Content may end unusually high; confirm intentional workspace or pagination.",
                )
            )

    if metrics.page_balance not in {"PASS", "pass"}:
        detail = "; ".join(metrics.confidence_notes) if metrics.confidence_notes else metrics.page_balance
        findings.append(
            (
                CheckStatus.WARN,
                f"Page {pn} page balance: {metrics.page_balance}",
                detail,
            )
        )

    return findings


def compute_quality_score(
    mechanical_pass_ratio: float,
    page_metrics: list[PageVisualMetrics],
    fail_count: int,
    warn_count: int,
) -> QualityScore:
    if fail_count > 0:
        mech = max(0.0, mechanical_pass_ratio * 50.0)
        visual = 0.0
    else:
        mech = mechanical_pass_ratio * 100.0
        if page_metrics:
            ink_scores = [min(m.visible_ink_percent, 100.0) for m in page_metrics]
            margin_ok = sum(1 for m in page_metrics if m.safe_margin_state == "PASS") / len(page_metrics)
            balance_ok = sum(1 for m in page_metrics if m.page_balance == "PASS") / len(page_metrics)
            visual = (sum(ink_scores) / len(ink_scores)) * 0.4 + margin_ok * 30.0 + balance_ok * 30.0
            visual = min(visual, 100.0)
            if warn_count:
                visual = max(0.0, visual - warn_count * 5.0)
        else:
            visual = 50.0
    return QualityScore(mechanical_score=mech, visual_heuristic_score=visual)


def annotate_page_render(
    base_path: Path,
    metrics: PageVisualMetrics,
    profile: ArtifactProfile,
    ink_mask: list[list[bool]] | None,
    clip: fitz.Rect | None,
    output_path: Path,
    dpi: int,
) -> str:
    image = Image.open(base_path).convert("RGB")
    draw = ImageDraw.Draw(image, "RGBA")
    w, h = image.size
    scale = dpi / 72.0

    draw.rectangle([0, 0, w - 1, h - 1], outline=(0, 120, 255, 200), width=2)
    inset = profile.safe_boundary_inches * POINTS_PER_INCH * scale
    draw.rectangle([inset, inset, w - inset, h - inset], outline=(0, 180, 80, 200), width=2)

    if ink_mask and clip is not None and len(ink_mask) == h and (len(ink_mask[0]) if ink_mask else 0) == w:
        lowest = -1
        row_threshold = max(int(w * profile.visual_geometry.ink_row_coverage_ratio), 3)
        for y in range(h - 1, -1, -1):
            if sum(1 for x in range(w) if ink_mask[y][x]) >= row_threshold:
                lowest = y
                break
        if lowest >= 0:
            draw.line([(0, lowest), (w, lowest)], fill=(255, 140, 0, 180), width=2)

    label = (
        f"P{metrics.page_number}  text:{metrics.text_coverage_percent:.0f}%  "
        f"draw:{metrics.drawing_coverage_percent:.0f}%  ink:{metrics.visible_ink_percent:.0f}%  "
        f"ws:{metrics.writing_space_percent:.0f}%  gap:{metrics.bottom_whitespace_inches:.2f}\""
    )
    draw.rectangle([0, 0, w, 22], fill=(255, 255, 255, 220))
    draw.text((4, 4), label, fill=(0, 0, 0, 255))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)
    image.close()
    return str(output_path)


def generate_contact_sheet(
    render_paths: list[str],
    output_dir: Path,
    *,
    max_width: int = 2400,
    thumb_width: int = 400,
    label_height: int = 24,
) -> list[str]:
    if not render_paths:
        return []
    sheets: list[str] = []
    max_per_sheet = 20
    chunks = [render_paths[i : i + max_per_sheet] for i in range(0, len(render_paths), max_per_sheet)]

    for sheet_idx, chunk in enumerate(chunks):
        thumbs: list[Image.Image] = []
        for path in chunk:
            img = Image.open(path).convert("RGB")
            ratio = thumb_width / max(img.width, 1)
            thumb_h = max(int(img.height * ratio), 1)
            thumb = img.resize((thumb_width, thumb_h), Image.Resampling.LANCZOS)
            img.close()
            canvas = Image.new("RGB", (thumb_width, thumb_h + label_height), (255, 255, 255))
            canvas.paste(thumb, (0, 0))
            draw = ImageDraw.Draw(canvas)
            page_num = Path(path).stem.replace("page-", "")
            draw.text((4, thumb_h + 4), f"Page {int(page_num)}", fill=(0, 0, 0))
            thumbs.append(canvas)
            thumb.close()

        cols = min(4, len(thumbs))
        rows = math.ceil(len(thumbs) / cols)
        cell_w = thumb_width
        cell_h = max(t.height for t in thumbs)
        sheet_w = cols * cell_w
        sheet_h = rows * cell_h
        if sheet_w > max_width:
            scale = max_width / sheet_w
            cols = max(1, int(cols * scale))
            rows = math.ceil(len(thumbs) / cols)
            cell_w = max_width // cols
            sheet_w = cols * cell_w
            sheet_h = rows * cell_h

        sheet = Image.new("RGB", (sheet_w, sheet_h), (240, 240, 240))
        for idx, thumb in enumerate(thumbs):
            r, c = divmod(idx, cols)
            resized = thumb
            if thumb.width != cell_w:
                ratio = cell_w / thumb.width
                resized = thumb.resize((cell_w, int(thumb.height * ratio)), Image.Resampling.LANCZOS)
            sheet.paste(resized, (c * cell_w, r * cell_h))
            if resized is not thumb:
                resized.close()
            thumb.close()

        suffix = f"-{sheet_idx + 1:02d}" if len(chunks) > 1 else ""
        out = output_dir / f"preview-contact-sheet{suffix}.png"
        sheet.save(out)
        sheet.close()
        sheets.append(str(out))
    return sheets

def visual_compare_pages(
    student_path: Path,
    teacher_path: Path,
    output_dir: Path,
    profile: ArtifactProfile,
    *,
    dpi: int | None = None,
) -> list[tuple[CheckStatus, str, str | None]]:
    spec = profile.visual_geometry
    analysis_dpi = dpi or spec.analysis_dpi
    findings: list[tuple[CheckStatus, str, str | None]] = []
    compare_dir = output_dir / "visual-compare"
    compare_dir.mkdir(parents=True, exist_ok=True)

    s_doc = fitz.open(student_path)
    t_doc = fitz.open(teacher_path)
    try:
        limit = min(s_doc.page_count, t_doc.page_count)
        drift_pages: list[int] = []
        for idx in range(limit):
            page_num = idx + 1
            s_page = s_doc[idx]
            t_page = t_doc[idx]
            s_img, s_clip = _render_printable_clip(s_page, profile, analysis_dpi)
            t_img, t_clip = _render_printable_clip(t_page, profile, analysis_dpi)

            s_path = compare_dir / f"page-{page_num:03d}-student.png"
            t_path = compare_dir / f"page-{page_num:03d}-teacher.png"
            s_img.save(s_path)
            t_img.save(t_path)

            tw = max(s_img.width, t_img.width)
            th = max(s_img.height, t_img.height)
            if abs(s_img.width - t_img.width) > tw * spec.comparison_dimension_tolerance or abs(s_img.height - t_img.height) > th * spec.comparison_dimension_tolerance:
                drift_pages.append(page_num)
                findings.append(
                    (
                        CheckStatus.WARN,
                        f"Page {page_num} student/teacher render dimensions differ",
                        "Visual review recommended.",
                    )
                )

            s_ink, s_mask = compute_visible_ink(s_img, spec)
            t_ink, t_mask = compute_visible_ink(t_img, spec)
            ink_delta = abs(s_ink - t_ink)

            diff = Image.new("RGB", (tw, th), (255, 255, 255))
            diff_draw = ImageDraw.Draw(diff)
            overlay = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
            overlay_draw = ImageDraw.Draw(overlay)

            s_resized = s_img if s_img.size == (tw, th) else s_img.resize((tw, th), Image.Resampling.LANCZOS)
            t_resized = t_img if t_img.size == (tw, th) else t_img.resize((tw, th), Image.Resampling.LANCZOS)

            for y in range(min(th, len(s_mask), len(t_mask))):
                for x in range(min(tw, len(s_mask[y]), len(t_mask[y]))):
                    s_on = s_mask[y][x] if y < len(s_mask) and x < len(s_mask[y]) else False
                    t_on = t_mask[y][x] if y < len(t_mask) and x < len(t_mask[y]) else False
                    if s_on != t_on:
                        diff_draw.point((x, y), fill=(255, 0, 0))
                    if s_on and t_on:
                        overlay_draw.point((x, y), fill=(0, 128, 0, 80))

            diff_path = compare_dir / f"page-{page_num:03d}-diff.png"
            diff.save(diff_path)
            overlay_path = compare_dir / f"page-{page_num:03d}-overlay.png"
            base = s_resized.convert("RGBA")
            base.alpha_composite(overlay)
            base.convert("RGB").save(overlay_path)
            base.close()
            diff.close()
            overlay.close()

            if ink_delta > spec.comparison_ink_delta_warn_percent:
                drift_pages.append(page_num)
                findings.append(
                    (
                        CheckStatus.WARN,
                        f"Page {page_num} student/key visible-ink difference ({ink_delta:.0f}%) requires visual review",
                        f"student={s_ink:.0f}%, teacher={t_ink:.0f}%",
                    )
                )

            s_img.close()
            t_img.close()
            if s_resized is not s_img:
                s_resized.close()
            if t_resized is not t_img:
                t_resized.close()

        if not drift_pages:
            findings.append((CheckStatus.PASS, "Student/teacher visual comparison shows no major layout drift", None))
        else:
            findings.append(
                (
                    CheckStatus.WARN,
                    "Student/key visual differences require teacher review",
                    f"Pages flagged: {sorted(set(drift_pages))}",
                )
            )
    finally:
        s_doc.close()
        t_doc.close()
    return findings
