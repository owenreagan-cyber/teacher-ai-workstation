from __future__ import annotations

from pathlib import Path

import fitz

from .inspect_page_usage import printable_rect, safe_rect
from .models import CheckStatus, PreflightReport
from .profiles import ArtifactProfile
from .visual_geometry import PageVisualMetrics, annotate_page_render, generate_contact_sheet


def render_pdf_pages(
    doc: fitz.Document,
    output_dir: Path,
    *,
    dpi: int = 144,
    profile: ArtifactProfile | None = None,
) -> list[str]:
    renders_dir = output_dir / "renders"
    renders_dir.mkdir(parents=True, exist_ok=True)
    paths: list[str] = []
    matrix = fitz.Matrix(dpi / 72.0, dpi / 72.0)
    for index, page in enumerate(doc, start=1):
        if profile is not None:
            left, top, right, bottom = printable_rect(profile)
            clip = fitz.Rect(left, top, right, bottom)
            pix = page.get_pixmap(matrix=matrix, clip=clip, alpha=False)
        else:
            pix = page.get_pixmap(matrix=matrix, alpha=False)
        target = renders_dir / f"page-{index:03d}.png"
        pix.save(str(target))
        paths.append(str(target))
    return paths


def render_pdf_file(path: Path, output_dir: Path, *, dpi: int = 144, profile: ArtifactProfile | None = None) -> list[str]:
    doc = fitz.open(path)
    try:
        return render_pdf_pages(doc, output_dir, dpi=dpi, profile=profile)
    finally:
        doc.close()


def attach_renders(report: PreflightReport, paths: list[str]) -> None:
    report.render_paths = paths
    if paths:
        report.add(CheckStatus.PASS, "Page previews rendered")


def attach_annotated_renders(report: PreflightReport, paths: list[str]) -> None:
    report.annotated_render_paths = paths
    if paths:
        report.add(CheckStatus.PASS, f"Annotated page previews generated ({len(paths)} pages)")


def attach_contact_sheets(report: PreflightReport, paths: list[str]) -> None:
    report.contact_sheet_paths = paths
    if paths:
        report.add(CheckStatus.PASS, f"Contact sheet generated: {paths[0]}")


def generate_annotated_renders(
    render_paths: list[str],
    page_metrics: list[PageVisualMetrics],
    profile: ArtifactProfile,
    output_dir: Path,
    *,
    ink_masks: list[list[list[bool]] | None] | None = None,
    clips: list[fitz.Rect | None] | None = None,
    dpi: int = 144,
) -> list[str]:
    annotated_dir = output_dir / "annotated"
    annotated_dir.mkdir(parents=True, exist_ok=True)
    paths: list[str] = []
    metrics_by_page = {m.page_number: m for m in page_metrics}
    for render_path in render_paths:
        stem = Path(render_path).stem
        page_num = int(stem.replace("page-", ""))
        metrics = metrics_by_page.get(page_num)
        if metrics is None:
            continue
        mask = None
        clip = None
        if ink_masks and page_num - 1 < len(ink_masks):
            mask = ink_masks[page_num - 1]
        if clips and page_num - 1 < len(clips):
            clip = clips[page_num - 1]
        out = annotated_dir / f"{stem}-annotated.png"
        paths.append(
            annotate_page_render(
                Path(render_path), metrics, profile, mask, clip, out, dpi,
            )
        )
        metrics.annotated_render_path = str(out)
    return paths
