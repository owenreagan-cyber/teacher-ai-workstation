"""Canonical Canvas Grade Check / Teacher Alert workflow (read-only).

This package scans Canvas grades read-only and produces teacher-facing flags
plus copy-ready parent templates. It NEVER modifies grades, assignments,
submissions, or student records, and NEVER sends parent communication
automatically.

Modules:
- config:      load grade-check config, resolve quarter, select active subjects
- reader:      read-only Canvas grade data source (live + injectable fixtures)
- engine:      assessment classification, flag computation, reconciliation
- state:       local persistent flag state (gitignored)
- templates:   copy/paste parent message templates
- report:      teacher report / email composition
- emailer:     gated email delivery (never enabled without explicit approval)
- cli:         bin/grade-check entry point (--preview / --send / --self-test)
"""

__all__ = ["config", "reader", "engine", "state", "templates", "report", "emailer", "cli"]
