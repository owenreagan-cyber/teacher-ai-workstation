from __future__ import annotations

import json
from pathlib import Path

from .models import CheckStatus, PreflightReport


def format_terminal_report(report: PreflightReport) -> str:
    lines = [
        "Artifact Quality Preflight",
        "==========================",
        "",
        f"Input: {report.input_path}",
        f"Profile: {report.profile_name}",
    ]
    if report.subject:
        lines.append(f"Subject: {report.subject}")
    if report.student_path:
        lines.append(f"Student: {report.student_path}")
    if report.teacher_path:
        lines.append(f"Teacher: {report.teacher_path}")
    lines.append("")

    for check in report.checks:
        prefix = check.status.value.ljust(4)
        page_suffix = f" (page {check.page})" if check.page is not None else ""
        lines.append(f"{prefix}  {check.message}{page_suffix}")
        if check.details:
            for detail_line in check.details.splitlines():
                lines.append(f"      {detail_line}")

    lines.extend(["", f"FINAL STATUS: {report.final_status.value}"])
    return "\n".join(lines)


def write_reports(report: PreflightReport, output_dir: Path, *, json_output: bool = True) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "report.txt").write_text(format_terminal_report(report) + "\n", encoding="utf-8")
    if json_output:
        (output_dir / "report.json").write_text(
            json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )


def print_report(report: PreflightReport) -> None:
    print(format_terminal_report(report))
