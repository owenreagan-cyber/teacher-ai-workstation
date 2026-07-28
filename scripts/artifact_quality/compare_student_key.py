from __future__ import annotations

import re
from pathlib import Path

import fitz

from .models import CheckStatus, PreflightReport
from .profiles import ArtifactProfile
from .validate_pdf import validate_pdf
from .visual_geometry import visual_compare_pages


def _page_signatures(doc: fitz.Document) -> list[dict[str, object]]:
    signatures: list[dict[str, object]] = []
    for page in doc:
        text = page.get_text("text")
        numbers = re.findall(r"\b\d+\.", text)
        sections = re.findall(r"(?m)^[A-Z][A-Za-z0-9 \-]{2,40}:?\s*$", text)
        signatures.append(
            {
                "width": round(page.rect.width, 1),
                "height": round(page.rect.height, 1),
                "char_count": len(re.sub(r"\s+", "", text)),
                "question_numbers": numbers[:20],
                "sections": sections[:10],
            }
        )
    return signatures


def compare_student_teacher_keys(
    student_path: Path,
    teacher_path: Path,
    profile: ArtifactProfile,
    report: PreflightReport,
    *,
    visual_compare: bool = False,
    output_dir: Path | None = None,
    analysis_dpi: int | None = None,
) -> None:
    student_doc = None
    teacher_doc = None
    try:
        student_doc = fitz.open(student_path)
        teacher_doc = fitz.open(teacher_path)
    except Exception as exc:  # noqa: BLE001
        report.add(CheckStatus.FAIL, "Student or teacher PDF could not be opened for comparison", details=str(exc))
        return

    student_pages = student_doc.page_count
    teacher_pages = teacher_doc.page_count
    if profile.requirements.teacher_key_must_match_page_count and student_pages != teacher_pages:
        report.add(
            CheckStatus.FAIL,
            "Student and teacher page counts do not match",
            details=f"student={student_pages}, teacher={teacher_pages}",
        )
    elif student_pages == teacher_pages:
        report.add(CheckStatus.PASS, "Student and teacher pagination match")
    else:
        report.add(
            CheckStatus.WARN,
            "Student and teacher page counts differ",
            details=f"student={student_pages}, teacher={teacher_pages}",
        )

    student_sizes = [(round(p.rect.width, 1), round(p.rect.height, 1)) for p in student_doc]
    teacher_sizes = [(round(p.rect.width, 1), round(p.rect.height, 1)) for p in teacher_doc]
    if student_sizes == teacher_sizes:
        report.add(CheckStatus.PASS, "Student and teacher page dimensions match")
    else:
        report.add(CheckStatus.WARN, "Student and teacher page dimensions differ", details="Visual review recommended.")

    student_sigs = _page_signatures(student_doc)
    teacher_sigs = _page_signatures(teacher_doc)
    limit = min(len(student_sigs), len(teacher_sigs))
    drift_pages: list[int] = []
    for index in range(limit):
        s_sig = student_sigs[index]
        t_sig = teacher_sigs[index]
        if abs(int(s_sig["char_count"]) - int(t_sig["char_count"])) > max(int(s_sig["char_count"]), 1) * 0.5:
            drift_pages.append(index + 1)
        if s_sig["question_numbers"] and t_sig["question_numbers"] and s_sig["question_numbers"] != t_sig["question_numbers"]:
            drift_pages.append(index + 1)
    if drift_pages:
        report.add(
            CheckStatus.WARN,
            "Student/key structural differences require visual review",
            details=f"Pages flagged: {sorted(set(drift_pages))}",
        )
    else:
        report.add(CheckStatus.PASS, "Student and teacher structural layout appear aligned")

    student_doc.close()
    teacher_doc.close()

    if visual_compare and output_dir is not None:
        for status, message, details in visual_compare_pages(
            student_path, teacher_path, output_dir, profile, dpi=analysis_dpi,
        ):
            report.add(status, message, details=details)


def validate_with_optional_key(
    student_path: Path,
    teacher_path: Path | None,
    profile: ArtifactProfile,
    report: PreflightReport,
    *,
    analysis_dpi: int | None = None,
    visual_compare: bool = False,
    output_dir: Path | None = None,
) -> tuple[fitz.Document | None, list, list, list]:
    doc, page_metrics, ink_masks, clips = validate_pdf(student_path, profile, report, analysis_dpi=analysis_dpi)
    if teacher_path is not None:
        compare_student_teacher_keys(
            student_path,
            teacher_path,
            profile,
            report,
            visual_compare=visual_compare,
            output_dir=output_dir,
            analysis_dpi=analysis_dpi,
        )
    return doc, page_metrics, ink_masks, clips
