"""One storage context for intake staging and deployment ledgers.

Tests isolate both roots together. Finalization refuses to touch a real
intake manifest when only the deployment root has been redirected.
"""
from __future__ import annotations

import tempfile
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from scripts.canvas_planner.state_root import deployment_root, intake_root


@dataclass(frozen=True)
class StorageRoots:
    intake_root: Path
    deploy_root: Path


_CURRENT: ContextVar[StorageRoots | None] = ContextVar("canvas_llm_storage", default=None)


def active_roots() -> StorageRoots | None:
    return _CURRENT.get()


def active_intake_root() -> Path:
    roots = _CURRENT.get()
    return roots.intake_root if roots else intake_root()


def active_deploy_root() -> Path:
    roots = _CURRENT.get()
    return roots.deploy_root if roots else deployment_root()


def canonical_intake_root() -> Path:
    return intake_root()


def canonical_deploy_root() -> Path:
    return deployment_root()


@contextmanager
def isolated_storage(root: Path | None = None) -> Iterator[Path]:
    """Point intake and deployment storage at one temporary tree."""
    cleanup = None
    if root is None:
        cleanup = tempfile.TemporaryDirectory()
        root = Path(cleanup.name)
    token = _CURRENT.set(StorageRoots(
        intake_root=root / "intake",
        deploy_root=root / "deployments",
    ))
    try:
        yield root
    finally:
        _CURRENT.reset(token)
        if cleanup is not None:
            cleanup.cleanup()
