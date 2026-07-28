"""Load Grade 4 multi-profile configuration from grade_4_profiles.yaml."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .profiles import (
    ArtifactProfile,
    EducationalLayoutSpec,
    MarginSpec,
    PaperSpec,
    PrintingSpec,
    RequirementSpec,
    SlideSpec,
    UtilizationSpec,
    VisualGeometrySpec,
    _load_structured_file,
    profiles_dir,
)

GRADE_4_FILE = "grade_4_profiles.yaml"
GRADE_4_KEYS = (
    "grade_4_worksheet",
    "grade_4_guided_notes",
    "grade_4_quiz",
    "grade_4_teacher_key",
    "grade_4_presentation",
)


def _grade_4_path() -> Path:
    return profiles_dir() / GRADE_4_FILE


def load_grade_4_catalog() -> dict[str, Any]:
    path = _grade_4_path()
    if not path.is_file():
        raise FileNotFoundError(f"Grade 4 profile catalog not found: {path}")
    raw = _load_structured_file(path)
    if not isinstance(raw, dict):
        raise ValueError(f"Grade 4 profile catalog must be a mapping: {path}")
    return raw


def list_grade_4_profiles() -> list[str]:
    catalog = load_grade_4_catalog()
    return sorted(k for k in catalog if k.startswith("grade_4_"))


def resolve_profile_name(name: str) -> tuple[str, str | None]:
    """Return (resolved_name, grade_4_key_or_none). Supports grade_4_profiles:grade_4_worksheet."""
    if ":" in name:
        file_part, key_part = name.split(":", 1)
        if file_part.replace(".yaml", "") == "grade_4_profiles":
            return key_part, key_part
    if name in GRADE_4_KEYS or name.startswith("grade_4_"):
        return name, name
    return name, None


def is_grade_4_profile(name: str) -> bool:
    _, key = resolve_profile_name(name)
    return key is not None and key in load_grade_4_catalog()


def load_grade_4_profile(key: str) -> ArtifactProfile:
    catalog = load_grade_4_catalog()
    if key not in catalog:
        raise KeyError(f"Unknown Grade 4 profile key: {key}")
    defaults = catalog.get("default_settings") or {}
    spec = catalog[key]
    if not isinstance(spec, dict):
        raise ValueError(f"Grade 4 profile {key} must be a mapping")

    margins_raw = spec.get("safe_margins") or {}
    ws_raw = spec.get("writing_space_expected_range") or {}
    bottom_raw = spec.get("bottom_whitespace") or {}
    balance_raw = spec.get("page_balance") or {}
    contact = defaults.get("contact_sheet") or {}
    annotated = defaults.get("annotated_render") or {}
    comparison = defaults.get("comparison") or {}
    edu_raw = spec.get("educational_layout") or {}
    req_raw = spec.get("requirements") or {}
    slides_raw = spec.get("slides") or {}

    bg_threshold = float(defaults.get("background_lum_threshold", 245))
    lum_delta = float(defaults.get("visible_ink_color_distance", 15))
    footer_in = float(bottom_raw.get("ignore_footer_height_inches", 0.5))

    margins = MarginSpec(
        top_inches=float(margins_raw.get("margin_top_inches", 0.50)),
        bottom_inches=float(margins_raw.get("margin_bottom_inches", 0.50)),
        left_inches=float(margins_raw.get("margin_left_inches", 0.50)),
        right_inches=float(margins_raw.get("margin_right_inches", 0.50)),
    )
    ws_min = float(ws_raw.get("min_pct", 25.0))
    ws_max = float(ws_raw.get("max_pct", 60.0))
    visual = VisualGeometrySpec(
        analysis_dpi=int(defaults.get("analysis_dpi", 72)),
        output_dpi=int(defaults.get("render_dpi", 150)),
        background_luminance_delta=lum_delta,
        footer_band_ratio=min(footer_in / 11.0, 0.08) if footer_in else 0.04,
        sparse_page_ink_percent=float(balance_raw.get("sparse_page_ink_min_pct", 5.0)),
        dense_page_ink_percent=float(balance_raw.get("dense_page_ink_max_pct", 65.0)),
        bottom_gap_warning_inches=float(bottom_raw.get("max_allowed_inches", 1.5)),
        writing_space_range=(ws_min, ws_max),
        page_balance_top_heavy_ratio=float(balance_raw.get("top_heavy_ratio_threshold", 3.5)),
        page_balance_sparse_band=float(balance_raw.get("bottom_heavy_ratio_threshold", 0.2)),
        comparison_dimension_tolerance=float(comparison.get("layout_shift_tolerance_px", 12.0)) / 200.0,
        generate_annotated_renders=bool(annotated.get("enabled", True)),
        generate_contact_sheet=bool(contact.get("enabled", True)),
    )
    requirements = RequirementSpec(
        page_numbers_after_first=bool(req_raw.get("page_numbers_after_first", key == "grade_4_teacher_key")),
        teacher_key_must_match_page_count=bool(req_raw.get("teacher_key_must_match_page_count", key == "grade_4_teacher_key")),
        min_body_font_pt=float(edu_raw.get("min_body_font_pt", 14.0 if key != "grade_4_teacher_key" else 12.0)),
        max_body_font_pt=16.0,
    )
    educational = EducationalLayoutSpec(
        min_body_font_pt=float(edu_raw.get("min_body_font_pt", requirements.min_body_font_pt)),
        min_direction_font_pt=float(edu_raw.get("min_direction_font_pt", 14.0)),
        min_slide_title_font_pt=float(edu_raw.get("min_slide_title_font_pt", 28.0)),
        min_slide_body_font_pt=float(edu_raw.get("min_slide_body_font_pt", 22.0)),
        max_bullets_per_slide=int(edu_raw.get("max_bullets_per_slide", 5)),
        max_slide_words=int(edu_raw.get("max_slide_words", 40)),
    )
    slides = None
    if slides_raw or key == "grade_4_presentation":
        sr = slides_raw or {}
        slides = SlideSpec(
            width_inches=float(sr.get("width_inches", 13.333)),
            height_inches=float(sr.get("height_inches", 7.5)),
            min_title_font_pt=float(sr.get("min_title_font_pt", 28.0)),
            min_body_font_pt=float(sr.get("min_body_font_pt", 22.0)),
        )

    artifact_type = str(spec.get("artifact_type") or ("pptx" if key == "grade_4_presentation" else "pdf"))
    display_name = str(spec.get("profile_name") or key)

    return ArtifactProfile(
        name=display_name,
        artifact_type=artifact_type,
        paper=PaperSpec(),
        margins=margins,
        page_utilization=UtilizationSpec(
            bottom_gap_warning_inches=visual.bottom_gap_warning_inches,
        ),
        requirements=requirements,
        printing=PrintingSpec(),
        visual_geometry=visual,
        educational_layout=educational,
        slides=slides,
        subject_extensions={"history": {"grade_4_profile_key": key}},
    )
