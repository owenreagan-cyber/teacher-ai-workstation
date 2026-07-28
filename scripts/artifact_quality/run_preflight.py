#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.artifact_quality.compare_student_key import validate_with_optional_key  # noqa: E402
from scripts.artifact_quality.models import CheckStatus, PreflightReport  # noqa: E402
from scripts.artifact_quality.profiles import load_profile  # noqa: E402
from scripts.artifact_quality.render_artifact import attach_renders, render_pdf_pages  # noqa: E402
from scripts.artifact_quality.reporting import print_report, write_reports  # noqa: E402
from scripts.artifact_quality.subject_checks import apply_subject_checks  # noqa: E402
from scripts.artifact_quality.validate_docx import validate_docx  # noqa: E402
from scripts.artifact_quality.validate_html import validate_html  # noqa: E402
from scripts.artifact_quality.validate_pdf import validate_pdf  # noqa: E402
from scripts.artifact_quality.validate_pptx import validate_pptx  # noqa: E402


def _default_output_dir(input_path: Path) -> Path:
    return REPO_ROOT / ".local" / "artifact-quality" / input_path.stem


def _suffix_kind(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return "pdf"
    if suffix == ".docx":
        return "docx"
    if suffix in {".html", ".htm"}:
        return "html"
    if suffix == ".pptx":
        return "pptx"
    return "unknown"


def run_preflight(
    *,
    profile_name: str,
    input_path: Path,
    subject: str | None = None,
    student_path: Path | None = None,
    teacher_path: Path | None = None,
    output_dir: Path | None = None,
    render: bool = False,
    json_output: bool = False,
    strict: bool = False,
) -> PreflightReport:
    profile = load_profile(profile_name)
    primary = student_path or input_path
    report = PreflightReport(
        input_path=str(primary),
        profile_name=profile_name,
        subject=subject,
        student_path=str(student_path) if student_path else None,
        teacher_path=str(teacher_path) if teacher_path else None,
    )

    kind = _suffix_kind(primary)
    report.artifact_type = kind
    out_dir = output_dir or _default_output_dir(primary)
    report.output_dir = str(out_dir)

    doc = None
    if kind == "pdf":
        if student_path and teacher_path:
            doc = validate_with_optional_key(student_path, teacher_path, profile, report)
        else:
            doc = validate_pdf(primary, profile, report)
        apply_subject_checks(subject, profile, report, doc=doc, source_path=primary)
    elif kind == "docx":
        validate_docx(primary, profile, report)
        apply_subject_checks(subject, profile, report, source_path=primary)
    elif kind == "html":
        validate_html(primary, profile, report)
        apply_subject_checks(subject, profile, report, source_path=primary)
    elif kind == "pptx":
        validate_pptx(primary, profile, report)
        apply_subject_checks(subject, profile, report, source_path=primary)
    else:
        report.add(CheckStatus.FAIL, f"Unsupported input type: {primary.suffix}")

    should_render = render or profile.requirements.render_pages or report.final_status != CheckStatus.PASS
    if doc is not None and should_render:
        paths = render_pdf_pages(doc, out_dir)
        attach_renders(report, paths)

    if doc is not None:
        doc.close()

    if json_output or output_dir is not None or render:
        write_reports(report, out_dir, json_output=True)

    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Instructional Artifact Quality preflight — local-first printable resource validation.",
    )
    parser.add_argument("--profile", required=True, help="Profile name from configs/artifact-profiles/")
    parser.add_argument("--subject", help="Subject key: math, shurley, reading, history, science")
    parser.add_argument("--input", dest="input_path", help="Primary artifact path")
    parser.add_argument("--student", dest="student_path", help="Student artifact for key comparison")
    parser.add_argument("--teacher", dest="teacher_path", help="Teacher key artifact for comparison")
    parser.add_argument("--output-dir", type=Path, help="Write report and renders under this directory")
    parser.add_argument("--json", action="store_true", help="Also write machine-readable report.json")
    parser.add_argument("--render", action="store_true", help="Render PDF pages to PNG previews")
    parser.add_argument("--strict", action="store_true", help="Return exit code 2 on WARN")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    primary = args.student_path or args.input_path
    if primary is None:
        parser.error("one of --input or --student is required")

    report = run_preflight(
        profile_name=args.profile,
        input_path=Path(primary),
        subject=args.subject,
        student_path=Path(args.student_path) if args.student_path else None,
        teacher_path=Path(args.teacher_path) if args.teacher_path else None,
        output_dir=args.output_dir,
        render=args.render,
        json_output=args.json,
        strict=args.strict,
    )
    print_report(report)
    return report.exit_code(strict=args.strict)


if __name__ == "__main__":
    sys.exit(main())
