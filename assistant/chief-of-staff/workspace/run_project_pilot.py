#!/usr/bin/env python3
"""Execute the single approved Phase E project metadata pilot."""

from __future__ import annotations

import json
import sys

from pilot import PilotBoundaryError
from project_pilot import execute_project_pilot


def main() -> int:
    try:
        result = execute_project_pilot()
    except (OSError, ValueError, PilotBoundaryError) as exc:
        print(f"FAIL: project.pilot: {exc}")
        return 1
    print(
        json.dumps(
            {
                "run_id": result.run_id,
                "observation_id": result.observation_id,
                "status": result.status,
                "git_commands": result.git_commands,
                "metadata_records": result.metadata_records,
                "runtime_seconds": result.runtime_seconds,
                "snapshot_size_bytes": result.snapshot_size_bytes,
                "total_output_size_bytes": result.total_output_size_bytes,
                "output_files": result.output_files,
                "audit_event_types": result.audit_event_types,
            },
            indent=2,
        )
    )
    return 0 if result.status == "completed" else 1


if __name__ == "__main__":
    sys.exit(main())
