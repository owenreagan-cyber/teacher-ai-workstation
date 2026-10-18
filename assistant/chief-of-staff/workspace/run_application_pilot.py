#!/usr/bin/env python3
"""Execute the single approved Phase F application metadata pilot."""

from __future__ import annotations

import json
import sys

from application_pilot import execute_application_pilot
from pilot import PilotBoundaryError


def main() -> int:
    try:
        result = execute_application_pilot()
    except (OSError, ValueError, PilotBoundaryError) as exc:
        print(f"FAIL: application.pilot: {exc}")
        return 1
    print(
        json.dumps(
            {
                "run_id": result.run_id,
                "observation_id": result.observation_id,
                "status": result.status,
                "metadata_queries": result.metadata_queries,
                "metadata_fields_available": result.metadata_fields_available,
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
