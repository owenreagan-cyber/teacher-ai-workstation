from __future__ import annotations

from pathlib import Path

import fitz
from docx import Document
from docx.shared import Inches, Pt
from pptx import Presentation
from pptx.util import Inches as PInches, Pt as PPt


LETTER = (612, 792)
A4 = (595, 842)
# Safe inset for standard worksheet profile: margin + 0.35" boundary
SAFE_X = 72
SAFE_Y = 100
SAFE_BOTTOM_Y = 680


def _new_letter_doc() -> fitz.Document:
    doc = fitz.open()
    doc.new_page(width=LETTER[0], height=LETTER[1])
    return doc


def build_passing_worksheet(path: Path) -> None:
    doc = _new_letter_doc()
    page = doc[0]
    page.insert_text((SAFE_X, SAFE_Y), "Grade 4 Math Worksheet", fontsize=20)
    for index in range(1, 17):
        col = 0 if index % 2 else 1
        row = (index - 1) // 2
        x = SAFE_X + col * 250
        y = SAFE_Y + 40 + row * 32
        if y > SAFE_BOTTOM_Y - 40:
            break
        page.insert_text((x, y), f"{index}. Sample problem = ______", fontsize=13)
    directions = (
        "Directions: Complete each problem. Show your work in the space provided. "
        "Check your answers carefully before turning in your paper. "
        "Use pencil so you can revise your work if needed."
    )
    page.insert_textbox(
        fitz.Rect(SAFE_X, SAFE_BOTTOM_Y - 70, 540, SAFE_BOTTOM_Y - 10),
        directions,
        fontsize=12,
    )
    page.insert_text((500, SAFE_BOTTOM_Y), "1", fontsize=10)
    doc.save(path)
    doc.close()


def build_passing_guided_notes(path: Path) -> None:
    doc = fitz.open()
    for page_no in (1, 2):
        page = doc.new_page(width=LETTER[0], height=LETTER[1])
        page.insert_text((SAFE_X + 8, SAFE_Y), f"Guided Notes — Page {page_no}", fontsize=18)
        page.insert_text((SAFE_X + 8, SAFE_Y + 40), "Main idea: sample summary line for testing.", fontsize=13)
        page.insert_text((SAFE_X + 8, SAFE_Y + 80), "Notes:", fontsize=13)
        for y in range(SAFE_Y + 120, SAFE_BOTTOM_Y - 40, 28):
            page.insert_text((SAFE_X + 8, y), "______________________________________________", fontsize=12)
        page.insert_text((500, SAFE_BOTTOM_Y), str(page_no), fontsize=10)
    doc.save(path)
    doc.close()


def build_passing_teacher_key(path: Path) -> None:
    doc = fitz.open()
    for page_no in (1, 2):
        page = doc.new_page(width=LETTER[0], height=LETTER[1])
        page.insert_text((SAFE_X + 8, SAFE_Y), f"Teacher Key — Page {page_no}", fontsize=18)
        page.insert_text((SAFE_X + 8, SAFE_Y + 40), "Main idea: sample summary line for testing.", fontsize=13)
        page.insert_text((SAFE_X + 8, SAFE_Y + 80), "Answer: sample answer text.", fontsize=13)
        page.insert_text((500, SAFE_BOTTOM_Y), str(page_no), fontsize=10)
    doc.save(path)
    doc.close()


def build_warn_low_utilization(path: Path) -> None:
    doc = _new_letter_doc()
    page = doc[0]
    page.insert_text((80, 80), "Short title only", fontsize=14)
    doc.save(path)
    doc.close()


def build_warn_bottom_gap(path: Path) -> None:
    doc = _new_letter_doc()
    page = doc[0]
    page.insert_text((80, 80), "Section 1", fontsize=16)
    page.insert_text((80, 120), "A small amount of content near the top.", fontsize=13)
    doc.save(path)
    doc.close()


def build_warn_near_boundary(path: Path) -> None:
    doc = _new_letter_doc()
    page = doc[0]
    page.insert_text((42, 42), "Edge content", fontsize=12)
    doc.save(path)
    doc.close()


def build_fail_a4(path: Path) -> None:
    doc = fitz.open()
    page = doc.new_page(width=A4[0], height=A4[1])
    page.insert_text((60, 60), "A4 page sample", fontsize=14)
    doc.save(path)
    doc.close()


def build_fail_unsafe_edge(path: Path) -> None:
    doc = _new_letter_doc()
    page = doc[0]
    page.insert_text((8, 400), "CLIPPED LEFT", fontsize=14)
    doc.save(path)
    doc.close()


def build_fail_blank_final_page(path: Path) -> None:
    doc = fitz.open()
    page = doc.new_page(width=LETTER[0], height=LETTER[1])
    page.insert_text((SAFE_X, SAFE_Y), "Page 1 content", fontsize=14)
    doc.new_page(width=LETTER[0], height=LETTER[1])
    doc.save(path)
    doc.close()


def build_fail_mixed_sizes(path: Path) -> None:
    doc = fitz.open()
    page = doc.new_page(width=LETTER[0], height=LETTER[1])
    page.insert_text((80, 80), "Letter page", fontsize=14)
    page = doc.new_page(width=A4[0], height=A4[1])
    page.insert_text((80, 80), "A4 page", fontsize=14)
    doc.save(path)
    doc.close()


def build_fail_placeholder(path: Path) -> None:
    doc = _new_letter_doc()
    page = doc[0]
    page.insert_text((80, 80), "TODO finish this worksheet", fontsize=14)
    doc.save(path)
    doc.close()


def build_fail_shurley_wrap(path: Path) -> None:
    doc = _new_letter_doc()
    page = doc[0]
    sentence = (
        "The quick brown fox jumps over the lazy dog while the students classify every single word "
        "in this intentionally long sample sentence for testing."
    )
    page.insert_text((80, 120), sentence, fontsize=13)
    doc.save(path)
    doc.close()


def build_passing_html(path: Path) -> None:
    path.write_text(
        """<!DOCTYPE html>
<html>
<head>
<style>
@page { size: letter; margin: 0.5in; }
@media print {
  * { box-sizing: border-box; }
  .content { break-inside: avoid; page-break-inside: avoid; }
}
</style>
</head>
<body><div class="content"><h1>Reading Check</h1><p>Sample passage text.</p></div></body>
</html>
""",
        encoding="utf-8",
    )


def build_fail_html_no_print(path: Path) -> None:
    path.write_text("<html><body><p>No print styles</p></body></html>", encoding="utf-8")


def build_fail_html_overflow(path: Path) -> None:
    path.write_text(
        """<!DOCTYPE html>
<html><head><style>
.content { overflow: hidden; height: 200px; }
</style></head><body><div class="content worksheet">Academic content</div></body></html>
""",
        encoding="utf-8",
    )


def build_passing_docx(path: Path) -> None:
    document = Document()
    section = document.sections[0]
    section.page_width = Inches(8.5)
    section.page_height = Inches(11)
    section.top_margin = Inches(0.5)
    section.bottom_margin = Inches(0.5)
    section.left_margin = Inches(0.65)
    section.right_margin = Inches(0.5)
    document.add_heading("Guided Notes DOCX", level=1)
    document.add_paragraph("Sample paragraph for structural validation.")
    document.save(path)


def build_fail_docx_a4(path: Path) -> None:
    document = Document()
    section = document.sections[0]
    section.page_width = Inches(8.27)
    section.page_height = Inches(11.69)
    document.add_paragraph("A4 section")
    document.save(path)


def build_passing_pptx(path: Path) -> None:
    presentation = Presentation()
    presentation.slide_width = PInches(13.333)
    presentation.slide_height = PInches(7.5)
    slide = presentation.slides.add_slide(presentation.slide_layouts[5])
    textbox = slide.shapes.add_textbox(PInches(0.5), PInches(0.5), PInches(12), PInches(1))
    textbox.text_frame.text = "Projector Slide Title"
    body = slide.shapes.add_textbox(PInches(0.5), PInches(1.5), PInches(12), PInches(5))
    body.text_frame.text = "One core idea for classroom display."
    presentation.save(path)


def build_fail_pptx_out_of_bounds(path: Path) -> None:
    presentation = Presentation()
    presentation.slide_width = PInches(13.333)
    presentation.slide_height = PInches(7.5)
    slide = presentation.slides.add_slide(presentation.slide_layouts[5])
    shape = slide.shapes.add_textbox(PInches(12.5), PInches(6.8), PInches(2), PInches(1))
    shape.text_frame.text = "Outside bounds"
    presentation.save(path)


def ensure_all_fixtures(base: Path) -> None:
    builders = {
        base / "passing" / "worksheet-letter.pdf": build_passing_worksheet,
        base / "passing" / "guided-notes-two-page.pdf": build_passing_guided_notes,
        base / "passing" / "teacher-key-two-page.pdf": build_passing_teacher_key,
        base / "passing" / "printable.html": build_passing_html,
        base / "passing" / "guided-notes.docx": build_passing_docx,
        base / "passing" / "projector.pptx": build_passing_pptx,
        base / "warning" / "low-utilization.pdf": build_warn_low_utilization,
        base / "warning" / "bottom-gap.pdf": build_warn_bottom_gap,
        base / "warning" / "near-boundary.pdf": build_warn_near_boundary,
        base / "failing" / "a4-page.pdf": build_fail_a4,
        base / "failing" / "unsafe-edge.pdf": build_fail_unsafe_edge,
        base / "failing" / "blank-final-page.pdf": build_fail_blank_final_page,
        base / "failing" / "mixed-sizes.pdf": build_fail_mixed_sizes,
        base / "failing" / "placeholder.pdf": build_fail_placeholder,
        base / "failing" / "html-no-print.html": build_fail_html_no_print,
        base / "failing" / "html-overflow.html": build_fail_html_overflow,
        base / "failing" / "docx-a4.docx": build_fail_docx_a4,
        base / "failing" / "pptx-out-of-bounds.pptx": build_fail_pptx_out_of_bounds,
        base / "failing" / "shurley-wrap.pdf": build_fail_shurley_wrap,
    }
    for target, builder in builders.items():
        target.parent.mkdir(parents=True, exist_ok=True)
        builder(target)
