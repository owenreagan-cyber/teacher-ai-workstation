#!/usr/bin/env python3
"""Run the single fixed Phase D history metadata pilot."""

from __future__ import annotations

import json
import sys

from pilot import PilotBoundaryError, execute_history_pilot


def main() -> int:
    try:
        result = execute_history_pilot()
    except (OSError, ValueError, PilotBoundaryError) as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}))
        return 1
    print(
        json.dumps(
            {
                "run_id": result.run_id,
                "status": result.status,
                "item_count": result.item_count,
                "runtime_seconds": round(result.runtime_seconds, 6),
                "observation_size_bytes": result.observation_size_bytes,
                "total_output_size_bytes": result.total_output_size_bytes,
                "hidden_entries_skipped": result.hidden_entries_skipped,
                "symlinks_skipped": result.symlinks_skipped,
                "output_files": result.output_files,
                "audit_event_types": result.audit_event_types,
            },
            indent=2,
        )
    )
    return 0 if result.status == "completed" else 1


if __name__ == "__main__":
    sys.exit(main())
