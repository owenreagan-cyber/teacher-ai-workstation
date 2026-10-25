#!/usr/bin/env python3
"""Seed a deterministic Q2W3 fixture for isolated headless UI tests.

Creates (under the given state root):
- a minimal canonical intake packet so /api/home and /api/planner-week work;
- a Weekly Planner Agent plan + a baseline snapshot;
- an assessment-date change (Math Written Assessment 8: Thursday -> Friday) so
  the Assessment Date Watch surfaces old/new dates with Canvas state.

No network, no Canvas writes, no real notifications.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))


def _write(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def seed(state_root: str) -> dict:
    os.environ["TAW_STATE_ROOT"] = state_root
    from scripts.canvas_planner.state_root import state_root as _root
    from scripts.canvas_llm_intake import constants as IC
    from scripts.weekly_planner_agent import service
    from scripts.weekly_planner_agent.models import (
        Assessment, Authority, DayPlan, PlanStatus, WeeklyPlan,
    )

    root = Path(state_root)

    # --- minimal canonical intake packet (Q2W3) ---
    intake_dir = root / "canvas-llm" / "intake" / "2026-2027" / "q2" / "w3"
    _write(intake_dir / "intake-manifest.json", {
        "quarter": 2, "week": 3, "week_code": "Q2W3",
        "date_range": {"start": "2026-10-26", "end": "2026-10-30"},
        "status": "SOURCE_SYNCED", "ready_to_publish": False,
        "source_hash": "fixture-source-hash",
        "source_retrieved_at": "2026-10-24T12:00:00Z",
        "subjects": {
            "math": {"state": "PLANNED"},
            "reading_spelling": {"state": "PLANNED"},
            "language_arts": {"state": "PLANNED"},
            "science": {"state": "PLANNED"},
        },
        "page_lookup": {},
        "approval_summary": {},
    })
    _write(root / "canvas-planner" / "pacing-source.json", {
        "name": "2026-2027 FPK Pacing Guides", "tab": "4A - Reagan",
        "spreadsheet_id": "fixture-spreadsheet",
    })

    # --- agent plan ---
    plan = WeeklyPlan(week_id="Q2W3", quarter=2, week=3,
                      date_range={"start": "2026-10-26", "end": "2026-10-30"})
    plan.source_provenance = {"name": "FPK Pacing Guides", "tab": "4A - Reagan",
                              "spreadsheet_id": "fixture-spreadsheet"}
    plan.upsert_day(DayPlan(
        subject="math", day="Thursday", date="2026-11-05", lesson="WA8",
        classwork=["WA8"], homework=[],
        assessment=Assessment(name="Written Assessment 8", subject="math",
                              day="Thursday", date="2026-11-05"),
        authority=Authority.VERIFIED_PACING, status=PlanStatus.CONFIRMED_SOURCE,
    ))
    for day in ("Monday", "Tuesday", "Wednesday", "Friday"):
        plan.upsert_day(DayPlan(subject="math", day=day, lesson=f"Lesson {day}",
                                authority=Authority.VERIFIED_PACING))
    # One predicted/inferred day to exercise confidence distinction in the UI.
    plan.upsert_day(DayPlan(subject="science", day="Wednesday", lesson="Chapter 7",
                            authority=Authority.SUBJECT_RULES, confidence="predicted"))
    service.save_plan(2, 3, plan)

    def pacing(date):
        return {
            "identity": plan.source_provenance,
            "cells": {"math|Thursday": {
                "lesson": "Written Assessment 8", "chapter": None,
                "classwork": ["Written Assessment 8"], "homework": [],
                "assessment": {"name": "Written Assessment 8", "date": date, "day": "Thursday"},
            }},
        }

    def canvas(due):
        return {
            "status": "OK", "observed_at": "2026-10-24T12:00:00Z",
            "courses": {"math": {
                "front_page": {"title": "Q2W3 Math", "page_id": "q2w3"},
                "assignments": [{"id": "a1", "name": "SM5: Written Assessment 8",
                                 "due_at": due}],
                "announcements": [], "pages": [], "assignment_groups": [],
            }},
        }

    # Baseline, then the change (pacing -> Friday; Canvas still due Thursday).
    service.sync(2, 3, pacing=pacing("2026-11-05"), canvas=canvas("2026-11-05T23:59:00Z"))
    report = service.sync(2, 3, pacing=pacing("2026-11-06"), canvas=canvas("2026-11-05T23:59:00Z"))
    return {
        "week": "Q2W3",
        "events": len(report["events"]),
        "assessment_watch": len(report.get("assessment_watch") or []),
        "state_root": str(root),
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: seed_fixture.py <state_root>", file=sys.stderr)
        sys.exit(2)
    result = seed(sys.argv[1])
    print(json.dumps(result))
