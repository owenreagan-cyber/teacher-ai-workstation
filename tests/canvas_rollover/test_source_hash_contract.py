"""source_hash is the intake identity. agenda_hash is the page composite."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.canvas_llm_deploy.client import FakeDeployClient
from scripts.canvas_llm_deploy.plan import agenda_composite_hash, build_plan
from scripts.canvas_llm_intake import manifest as imf
from scripts.canvas_llm_rollover import manifest as rollover_manifest
from scripts.canvas_llm_rollover import rollover
from scripts.canvas_llm_storage import isolated_storage

NOW = datetime(2026, 11, 7, 22, 0, tzinfo=timezone.utc)
SOURCE = "intake-source-hash"


def _packet():
    manifest = imf.new_manifest(
        quarter=2, week=5, week_code="Q2W5",
        date_range={"start": "2026-11-09", "end": "2026-11-13"},
    )
    manifest["source_hash"] = SOURCE
    imf.save_manifest(2, 5, manifest)
    drafts = imf.staging_dir(2, 5) / "drafts"
    drafts.mkdir(parents=True, exist_ok=True)
    (drafts / "math-page.html").write_text("<div>math agenda</div>", encoding="utf-8")
    (drafts / "announcements.json").write_text(json.dumps([
        {"course": "Math", "title": "Math Canvas Weekly Update", "message": "Math week"},
    ]), encoding="utf-8")
    (drafts / "assignments.json").write_text("[]", encoding="utf-8")
    (drafts / "assessment-reminders.json").write_text("[]", encoding="utf-8")


def test_builder_keeps_source_and_agenda_distinct():
    with isolated_storage():
        _packet()
        rolled = rollover_manifest.build_rollover_manifest(2, 4, 2, 5, now=NOW)
        plan = build_plan(2, 5, now=NOW)
        assert rolled["source_hash"] == SOURCE
        assert plan["source_hash"] == SOURCE
        assert rolled["agenda_hash"] != SOURCE
        assert rolled["agenda_hash"] == plan["agenda_hash"]
        agendas = {item["subject"]: item["agenda_hash"] for item in rolled["weekly_announcements"]}
        assert rolled["agenda_hash"] == agenda_composite_hash("Q2W5", agendas)
        rolled["source_hash"] = rolled["agenda_hash"]
        blockers = rollover._prewrite_blockers(rolled, FakeDeployClient(), now=NOW, quarter=2, week=5)
        assert "manifest source hash does not match the authoritative source" in blockers
        rolled["source_hash"] = SOURCE
        rolled["agenda_hash"] = "changed-agenda"
        blockers = rollover._prewrite_blockers(rolled, FakeDeployClient(), now=NOW, quarter=2, week=5)
        assert "manifest agenda hash does not match the weekly agendas" in blockers
        client = FakeDeployClient()
        rolled["plan_fingerprint"] = "stale-fingerprint"
        blockers = rollover._prewrite_blockers(rolled, client, now=NOW, quarter=2, week=5)
        assert "manifest plan fingerprint does not match the intake manifest" in blockers
        assert client._write_counts["POST"] == 0 and client._write_counts["PUT"] == 0


def test_missing_agenda_field_does_not_invent_a_source_hash():
    manifest = {
        "to_week": "Q2W5",
        "source_hash": SOURCE,
        "weekly_announcements": [{"subject": "math", "agenda_hash": "abc", "title": "Math"}],
        "academic_courses": [],
        "assignments": [],
        "assessment_reminders": [],
    }
    with isolated_storage():
        _packet()
        blockers = rollover._prewrite_blockers(manifest, FakeDeployClient(), now=NOW, quarter=2, week=5)
        assert "agenda hash" not in " ".join(blockers)
        manifest["source_hash"] = ""
        blockers = rollover._prewrite_blockers(manifest, FakeDeployClient(), now=NOW, quarter=2, week=5)
        assert "manifest source hash is missing" in blockers


def _run():
    failed = 0
    tests = [(name, fn) for name, fn in sorted(globals().items()) if name.startswith("test_") and callable(fn)]
    for name, fn in tests:
        try:
            fn()
            print(f"PASS {name}")
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"FAIL {name}: {type(exc).__name__}: {exc}")
    print(f"RESULT: {len(tests) - failed} passed, {failed} failed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    _run()
