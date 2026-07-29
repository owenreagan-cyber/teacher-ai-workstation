"""Curriculum Production Engine — architecture-first lesson package orchestration (no generation)."""

from .approval_workflow import ApprovalRecord, ApprovalWorkflow, WorkflowState
from .artifact_plan import ArtifactPlan, PlannedArtifact, populate_artifact_plan_references
from .content_map import ContentItem, ContentMap, ContentPriority
from .curriculum_intake import CurriculumIntake
from .fixture_loader import build_from_fixture, load_package_fixture
from .lesson_model import LessonModel, ProductionStatus
from .lesson_package import LessonPackageInput, LessonPackagePlan
from .lesson_sequence import InstructionalSequence, load_sequence_catalog
from .production_registry import ProductionRegistry
from .relationship_graph import RelationshipGraph, RelationshipType
from .validation import ValidationReport, validate_lesson_package
from .workflow import build_lesson_package
from .intake_validation import validate_lesson_package_plan

__all__ = [
    "ApprovalRecord",
    "ApprovalWorkflow",
    "ArtifactPlan",
    "ContentItem",
    "ContentMap",
    "ContentPriority",
    "CurriculumIntake",
    "InstructionalSequence",
    "LessonModel",
    "LessonPackageInput",
    "LessonPackagePlan",
    "PlannedArtifact",
    "ProductionRegistry",
    "ProductionStatus",
    "RelationshipGraph",
    "RelationshipType",
    "ValidationReport",
    "WorkflowState",
    "build_from_fixture",
    "build_lesson_package",
    "load_package_fixture",
    "load_sequence_catalog",
    "validate_lesson_package",
    "validate_lesson_package_plan",
]
