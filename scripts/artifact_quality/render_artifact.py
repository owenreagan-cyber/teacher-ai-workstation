from __future__ import annotations

from pathlib import Path

import fitz

from .models import CheckStatus, PreflightReport


def render_pdf_pages(doc: fitz.Document, output_dir: Path, *, dpi: int = 144) -> list[str]:
    renders_dir = output_dir / "renders"
    renders_dir.mkdir(parents=True, exist_ok=True)
    paths: list[str] = []
    matrix = fitz.Matrix(dpi / 72.0, dpi / 72.0)
    for index, page in enumerate(doc, start=1):
        pix = page.get_pixmap(matrix=matrix, alpha=False)
        target = renders_dir / f"page-{index:03d}.png"
        pix.save(str(target))
        paths.append(str(target))
    return paths


def render_pdf_file(path: Path, output_dir: Path, *, dpi: int = 144) -> list[str]:
    doc = fitz.open(path)
    try:
        return render_pdf_pages(doc, output_dir, dpi=dpi)
    finally:
        doc.close()


def attach_renders(report: PreflightReport, paths: list[str]) -> None:
    report.render_paths = paths
    if paths:
        report.add(CheckStatus.PASS, "Page previews rendered")
