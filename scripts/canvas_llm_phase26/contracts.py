"""Phase 26 pure contracts (import-safe).

Re-exports the pure workstation dataclasses from ``models`` so consumers can
import the workstation contract without loading pipeline/assembly logic or Canvas
execution infrastructure.
"""

from __future__ import annotations

from .models import (
    ManifestOperation,
    SubjectSnapshot,
    WeekSelection,
    WorkstationPacket,
    compact,
    stable_id,
)

__all__ = [
    "ManifestOperation",
    "SubjectSnapshot",
    "WeekSelection",
    "WorkstationPacket",
    "compact",
    "stable_id",
]
