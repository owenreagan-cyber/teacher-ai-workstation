from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore

from .models import LETTER_HEIGHT_PT, LETTER_WIDTH_PT


@dataclass
class PaperSpec:
    width_points: float = LETTER_WIDTH_PT
    height_points: float = LETTER_HEIGHT_PT
    orientation: str = "portrait"
    size_tolerance_points: float = 2.0


@dataclass
class MarginSpec:
    top_inches: float = 0.50
    bottom_inches: float = 0.50
    left_inches: float = 0.55
    right_inches: float = 0.55


@dataclass
class UtilizationSpec:
    warning_below_percent: float = 70.0
    bottom_gap_warning_inches: float = 2.25
    boundary_warning_inches: float = 0.10
    blank_page_text_threshold: int = 5


@dataclass
class RequirementSpec:
    page_numbers_after_first: bool = False
    render_pages: bool = False
    teacher_key_must_match_page_count: bool = False
    require_single_line_sentences: bool = False
    min_body_font_pt: float = 12.5
    max_body_font_pt: float = 14.0


@dataclass
class PrintingSpec:
    scale: str = "actual-size"
    percent: int = 100


@dataclass
class SlideSpec:
    width_inches: float = 13.333
    height_inches: float = 7.5
    min_title_font_pt: float = 28.0
    min_body_font_pt: float = 18.0


@dataclass
class ArtifactProfile:
    name: str
    artifact_type: str
    paper: PaperSpec
    margins: MarginSpec
    page_utilization: UtilizationSpec
    requirements: RequirementSpec
    printing: PrintingSpec
    safe_boundary_inches: float = 0.35
    slides: Optional[SlideSpec] = None
    subject_extensions: dict[str, Any] | None = None


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def profiles_dir() -> Path:
    return _repo_root() / "configs" / "artifact-profiles"


def load_profile(name: str) -> ArtifactProfile:
    path = profiles_dir() / f"{name}.yaml"
    if not path.is_file():
        raise FileNotFoundError(f"Profile not found: {path}")
    raw = _load_structured_file(path)
    return parse_profile(raw, expected_name=name)


def list_profiles() -> list[str]:
    return sorted(p.stem for p in profiles_dir().glob("*.yaml"))


def _load_structured_file(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if yaml is not None:
        data = yaml.safe_load(text)
    else:
        data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError(f"Profile must be a mapping: {path}")
    return data


def parse_profile(raw: dict[str, Any], *, expected_name: str | None = None) -> ArtifactProfile:
    name = str(raw.get("name") or expected_name or "")
    if not name:
        raise ValueError("Profile missing name")
    if expected_name and name != expected_name:
        raise ValueError(f"Profile name mismatch: expected {expected_name}, got {name}")

    paper_raw = raw.get("paper") or {}
    margins_raw = raw.get("margins") or {}
    util_raw = raw.get("page_utilization") or {}
    req_raw = raw.get("requirements") or {}
    print_raw = raw.get("printing") or {}
    slides_raw = raw.get("slides")

    paper = PaperSpec(
        width_points=float(paper_raw.get("width_points", LETTER_WIDTH_PT)),
        height_points=float(paper_raw.get("height_points", LETTER_HEIGHT_PT)),
        orientation=str(paper_raw.get("orientation", "portrait")).lower(),
        size_tolerance_points=float(paper_raw.get("size_tolerance_points", 2.0)),
    )
    margins = MarginSpec(
        top_inches=float(margins_raw.get("top_inches", 0.50)),
        bottom_inches=float(margins_raw.get("bottom_inches", 0.50)),
        left_inches=float(margins_raw.get("left_inches", 0.55)),
        right_inches=float(margins_raw.get("right_inches", 0.55)),
    )
    utilization = UtilizationSpec(
        warning_below_percent=float(util_raw.get("warning_below_percent", 70.0)),
        bottom_gap_warning_inches=float(util_raw.get("bottom_gap_warning_inches", 2.25)),
        boundary_warning_inches=float(util_raw.get("boundary_warning_inches", 0.10)),
        blank_page_text_threshold=int(util_raw.get("blank_page_text_threshold", 5)),
    )
    requirements = RequirementSpec(
        page_numbers_after_first=bool(req_raw.get("page_numbers_after_first", False)),
        render_pages=bool(req_raw.get("render_pages", False)),
        teacher_key_must_match_page_count=bool(req_raw.get("teacher_key_must_match_page_count", False)),
        require_single_line_sentences=bool(req_raw.get("require_single_line_sentences", False)),
        min_body_font_pt=float(req_raw.get("min_body_font_pt", 12.5)),
        max_body_font_pt=float(req_raw.get("max_body_font_pt", 14.0)),
    )
    printing = PrintingSpec(
        scale=str(print_raw.get("scale", "actual-size")),
        percent=int(print_raw.get("percent", 100)),
    )
    slides = None
    if slides_raw:
        slides = SlideSpec(
            width_inches=float(slides_raw.get("width_inches", 13.333)),
            height_inches=float(slides_raw.get("height_inches", 7.5)),
            min_title_font_pt=float(slides_raw.get("min_title_font_pt", 28.0)),
            min_body_font_pt=float(slides_raw.get("min_body_font_pt", 18.0)),
        )

    artifact_type = str(raw.get("artifact_type") or "pdf").lower()
    safe_boundary = float(raw.get("safe_boundary_inches", 0.35))
    subject_extensions = raw.get("subject_extensions")
    if subject_extensions is not None and not isinstance(subject_extensions, dict):
        raise ValueError("subject_extensions must be a mapping")

    return ArtifactProfile(
        name=name,
        artifact_type=artifact_type,
        paper=paper,
        margins=margins,
        safe_boundary_inches=safe_boundary,
        page_utilization=utilization,
        requirements=requirements,
        printing=printing,
        slides=slides,
        subject_extensions=subject_extensions,
    )
