"""Publication-time gate + instructional-calendar regression tests (plain python)."""
import sys
from datetime import date, datetime, timezone
from pathlib import Path

if str(Path(__file__).resolve().parents[2]) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.canvas_llm_intake import week_resolution as wr
from scripts.canvas_llm_rollover import release_plan, rollover, schedule


def test_canonical_q2w4_is_friday_oct_30_4pm_edt():
    assert schedule.friday_rollover_scheduled_at("2026-11-02") == "2026-10-30T20:00:00Z"


def test_missed_window_requires_owner_time():
    now = datetime(2026, 10, 30, 21, 0, tzinfo=timezone.utc)
    resolved = schedule.resolve_publication_time("2026-11-02", now=now)
    assert resolved["requires_owner_time"] is True
    assert resolved["scheduled_at"] is None
    assert resolved["canonical_scheduled_at"] == "2026-10-30T20:00:00Z"


def test_future_window_uses_canonical_friday_4pm():
    now = datetime(2026, 10, 30, 12, 0, tzinfo=timezone.utc)
    resolved = schedule.resolve_publication_time("2026-11-02", now=now)
    assert resolved["requires_owner_time"] is False
    assert resolved["scheduled_at"] == "2026-10-30T20:00:00Z"


def test_slightly_late_scheduler_run_uses_grace_window():
    now = datetime(2026, 10, 30, 20, 15, tzinfo=timezone.utc)  # 4:15 PM ET
    resolved = schedule.resolve_publication_time("2026-11-02", now=now)
    assert resolved["requires_owner_time"] is False
    assert resolved["source"] == "CANONICAL_FRIDAY_4PM_GRACE"
    assert resolved["scheduled_at"] == "2026-10-30T20:00:00Z"


def test_beyond_grace_requires_owner_time():
    now = datetime(2026, 10, 30, 20, 31, tzinfo=timezone.utc)  # 4:31 PM ET
    resolved = schedule.resolve_publication_time("2026-11-02", now=now)
    assert resolved["requires_owner_time"] is True


def test_owner_selected_time_is_timezone_aware_and_future():
    now = datetime(2026, 10, 30, 21, 0, tzinfo=timezone.utc)
    resolved = schedule.resolve_publication_time(
        "2026-11-02", now=now, owner_selected_at="2026-11-01T09:00:00-05:00",
    )
    assert resolved["source"] == "OWNER_SELECTED"
    assert resolved["scheduled_at"] == "2026-11-01T14:00:00Z"
    for bad in ("2026-10-30T12:00:00-04:00", "2026-11-01T09:00:00"):
        try:
            schedule.resolve_publication_time("2026-11-02", now=now, owner_selected_at=bad)
            raise AssertionError("expected ValueError")
        except ValueError:
            pass


def test_thanksgiving_break_moves_rollover_to_last_instructional_friday():
    meta = schedule.instructional_rollover_meta("2026-11-30")
    assert meta["canonical_friday"] == "2026-11-27"
    assert meta["rollover_day"] == "2026-11-20"
    assert meta["moved"] is True
    assert meta["scheduled_at"] == "2026-11-20T21:00:00Z"


def test_quarter_transition_skips_winter_track_out():
    meta = schedule.instructional_rollover_meta("2027-01-11")
    assert meta["canonical_friday"] == "2027-01-08"
    assert meta["rollover_day"] == "2026-12-18"
    assert meta["scheduled_at"] == "2026-12-18T21:00:00Z"


def test_next_instructional_week_after_breaks():
    assert wr.next_week(today=date(2026, 11, 20)) == (2, 7)
    assert wr.next_week(today=date(2026, 12, 18)) == (3, 1)


def test_release_plan_names_five_targets_and_never_executes():
    plan = release_plan.build_release_plan(
        2, 3, 2, 4, now=datetime(2026, 10, 30, 21, 0, tzinfo=timezone.utc),
    )
    assert len(plan["front_page_targets"]) == 5
    assert plan["canvas_writes"] == 0 and plan["email_sends"] == 0
    assert plan["ready_to_execute"] is False
    assert "publication time" in " ".join(plan["blockers"]).lower()


def test_execute_blocks_expired_window_before_any_write():
    import tempfile
    from scripts.canvas_llm_deploy import ledger as deploy_ledger
    from scripts.canvas_llm_intake import manifest as intake_manifest
    from scripts.canvas_llm_deploy.client import FakeDeployClient

    orig = deploy_ledger.DEPLOY_ROOT
    orig_staging = intake_manifest.staging_dir
    with tempfile.TemporaryDirectory() as tmp:
        deploy_ledger.DEPLOY_ROOT = Path(tmp) / "deployments"
        intake_manifest.staging_dir = lambda q, w: Path(tmp) / "intake" / f"q{q}w{w}"
        try:
            client = FakeDeployClient(courses={26404: {"id": 26404, "name": "Math"}})
            manifest = {
                "from_week": "Q2W3", "to_week": "Q2W4",
                "scheduled_at": "2026-10-30T20:00:00Z",
                "timezone": "America/New_York",
                "academic_courses": [], "homeroom": None,
                "weekly_announcements": [], "assignments": [],
                "assessment_reminders": [],
            }
            try:
                rollover.execute(
                    2, 3, 2, 4, client=client, owner_confirmation="ROLLOVER Q2W4",
                    now=datetime(2026, 10, 30, 21, 0, tzinfo=timezone.utc),
                    manifest=manifest,
                )
                raise AssertionError("expected RolloverBlocked")
            except rollover.RolloverBlocked:
                pass
            assert client._write_counts["POST"] == 0
            assert client._write_counts["PUT"] == 0
        finally:
            deploy_ledger.DEPLOY_ROOT = orig
            intake_manifest.staging_dir = orig_staging


def test_manual_publish_without_now_cannot_bypass_expired_gate():
    import tempfile
    from unittest import mock
    from scripts.canvas_llm_deploy.client import FakeDeployClient
    from scripts.canvas_llm_deploy import ledger as deploy_ledger
    from scripts.canvas_llm_intake import manifest as intake_manifest

    orig_deploy = deploy_ledger.DEPLOY_ROOT
    orig_staging = intake_manifest.staging_dir
    with tempfile.TemporaryDirectory() as tmp:
        deploy_ledger.DEPLOY_ROOT = Path(tmp) / "deployments"
        intake_manifest.staging_dir = lambda q, w: Path(tmp) / "intake" / f"q{q}w{w}"
        try:
            manifest = {
                "from_week": "Q2W3", "to_week": "Q2W4",
                "scheduled_at": "2026-10-30T20:00:00Z",
                "timezone": "America/New_York",
                "academic_courses": [], "homeroom": None,
                "weekly_announcements": [], "assignments": [],
                "assessment_reminders": [],
            }
            client = FakeDeployClient(courses={26404: {"id": 26404, "name": "Math"}})
            with mock.patch.object(
                rollover, "run_preflight",
                return_value={"ready": True, "blockers": [], "manifest": manifest},
            ):
                try:
                    rollover.publish_weekly_package(
                        2, 3, 2, 4, client=client, owner_confirmation="ROLLOVER Q2W4",
                    )
                    raise AssertionError("expected RolloverBlocked")
                except rollover.RolloverBlocked as exc:
                    assert "publication time" in str(exc).lower(), exc
            assert client._write_counts["POST"] == 0
            assert client._write_counts["PUT"] == 0
        finally:
            deploy_ledger.DEPLOY_ROOT = orig_deploy
            intake_manifest.staging_dir = orig_staging


def test_release_plan_owner_time_is_wired_into_execution_manifest():
    import json
    import tempfile
    from unittest import mock
    from scripts.canvas_llm_deploy.client import FakeDeployClient
    from scripts.canvas_llm_deploy import ledger as deploy_ledger
    from scripts.canvas_llm_intake import manifest as intake_manifest

    orig_deploy = deploy_ledger.DEPLOY_ROOT
    orig_staging = intake_manifest.staging_dir
    with tempfile.TemporaryDirectory() as tmp:
        deploy_ledger.DEPLOY_ROOT = Path(tmp) / "deployments"
        intake_manifest.staging_dir = lambda q, w: Path(tmp) / "intake" / f"q{q}w{w}"
        try:
            staging = intake_manifest.staging_dir(2, 4) / "planner"
            staging.mkdir(parents=True, exist_ok=True)
            (staging / "rollover-release-plan.json").write_text(json.dumps({
                "status": "READY_FOR_OWNER_REVIEW",
                "canonical_scheduled_at": "2026-10-30T20:00:00Z",
                "publication_time_required": True,
                "owner_publication_time": "2026-11-01T09:00:00-05:00",
            }), encoding="utf-8")
            manifest = {
                "from_week": "Q2W3", "to_week": "Q2W4",
                "scheduled_at": "2026-10-30T20:00:00Z",
                "timezone": "America/New_York",
                "academic_courses": [], "homeroom": None,
                "weekly_announcements": [], "assignments": [],
                "assessment_reminders": [],
            }
            client = FakeDeployClient(courses={26404: {"id": 26404, "name": "Math"}})
            with mock.patch.object(
                rollover, "run_preflight",
                return_value={"ready": True, "blockers": [], "manifest": manifest},
            ):
                report = rollover.publish_weekly_package(
                    2, 3, 2, 4, client=client, owner_confirmation="ROLLOVER Q2W4",
                    now=datetime(2026, 10, 30, 21, 0, tzinfo=timezone.utc),
                )
            assert report["scheduled_at"] == "2026-11-01T14:00:00Z", report
        finally:
            deploy_ledger.DEPLOY_ROOT = orig_deploy
            intake_manifest.staging_dir = orig_staging


def test_invalid_release_time_fails_closed():
    import json
    import tempfile
    from unittest import mock
    from scripts.canvas_llm_deploy.client import FakeDeployClient
    from scripts.canvas_llm_deploy import ledger as deploy_ledger
    from scripts.canvas_llm_intake import manifest as intake_manifest

    orig_deploy = deploy_ledger.DEPLOY_ROOT
    orig_staging = intake_manifest.staging_dir
    with tempfile.TemporaryDirectory() as tmp:
        deploy_ledger.DEPLOY_ROOT = Path(tmp) / "deployments"
        intake_manifest.staging_dir = lambda q, w: Path(tmp) / "intake" / f"q{q}w{w}"
        try:
            staging = intake_manifest.staging_dir(2, 4) / "planner"
            staging.mkdir(parents=True, exist_ok=True)
            (staging / "rollover-release-plan.json").write_text(json.dumps({
                "status": "READY_FOR_OWNER_REVIEW",
                "canonical_scheduled_at": "2026-10-30T20:00:00Z",
                "publication_time_required": True,
                "owner_publication_time": "2026-11-01T09:00:00",  # no timezone
            }), encoding="utf-8")
            manifest = {
                "from_week": "Q2W3", "to_week": "Q2W4",
                "scheduled_at": "2026-10-30T20:00:00Z",
                "timezone": "America/New_York",
                "academic_courses": [], "homeroom": None,
                "weekly_announcements": [], "assignments": [],
                "assessment_reminders": [],
            }
            client = FakeDeployClient(courses={26404: {"id": 26404, "name": "Math"}})
            with mock.patch.object(
                rollover, "run_preflight",
                return_value={"ready": True, "blockers": [], "manifest": manifest},
            ):
                try:
                    rollover.publish_weekly_package(
                        2, 3, 2, 4, client=client, owner_confirmation="ROLLOVER Q2W4",
                    )
                    raise AssertionError("expected RolloverBlocked")
                except rollover.RolloverBlocked:
                    pass
            assert client._write_counts["POST"] == 0
            assert client._write_counts["PUT"] == 0
        finally:
            deploy_ledger.DEPLOY_ROOT = orig_deploy
            intake_manifest.staging_dir = orig_staging


def test_execute_missing_now_with_required_flag_blocks():
    from scripts.canvas_llm_deploy.client import FakeDeployClient
    manifest = {
        "from_week": "Q2W3", "to_week": "Q2W4",
        "scheduled_at": "2026-10-30T20:00:00Z", "timezone": "America/New_York",
        "publication_time_required": True,
        "academic_courses": [], "homeroom": None,
        "weekly_announcements": [], "assignments": [], "assessment_reminders": [],
    }
    client = FakeDeployClient(courses={26404: {"id": 26404, "name": "Math"}})
    try:
        rollover.execute(
            2, 3, 2, 4, client=client, owner_confirmation="ROLLOVER Q2W4",
            manifest=manifest,
        )
        raise AssertionError("expected RolloverBlocked")
    except rollover.RolloverBlocked as exc:
        assert "publication time" in str(exc).lower(), exc
    assert client._write_counts["POST"] == 0
    assert client._write_counts["PUT"] == 0


def test_expired_release_timestamp_fails_closed():
    import json
    import tempfile
    from unittest import mock
    from scripts.canvas_llm_deploy.client import FakeDeployClient
    from scripts.canvas_llm_deploy import ledger as deploy_ledger
    from scripts.canvas_llm_intake import manifest as intake_manifest

    orig_deploy = deploy_ledger.DEPLOY_ROOT
    orig_staging = intake_manifest.staging_dir
    with tempfile.TemporaryDirectory() as tmp:
        deploy_ledger.DEPLOY_ROOT = Path(tmp) / "deployments"
        intake_manifest.staging_dir = lambda q, w: Path(tmp) / "intake" / f"q{q}w{w}"
        try:
            staging = intake_manifest.staging_dir(2, 4) / "planner"
            staging.mkdir(parents=True, exist_ok=True)
            (staging / "rollover-release-plan.json").write_text(json.dumps({
                "status": "READY_FOR_OWNER_REVIEW",
                "canonical_scheduled_at": "2026-10-30T20:00:00Z",
                "publication_time_required": True,
                "owner_publication_time": "2026-10-30T12:00:00-04:00",  # expired
            }), encoding="utf-8")
            manifest = {
                "from_week": "Q2W3", "to_week": "Q2W4",
                "scheduled_at": "2026-10-30T20:00:00Z", "timezone": "America/New_York",
                "academic_courses": [], "homeroom": None,
                "weekly_announcements": [], "assignments": [], "assessment_reminders": [],
            }
            client = FakeDeployClient(courses={26404: {"id": 26404, "name": "Math"}})
            with mock.patch.object(
                rollover, "run_preflight",
                return_value={"ready": True, "blockers": [], "manifest": manifest},
            ):
                try:
                    rollover.publish_weekly_package(
                        2, 3, 2, 4, client=client, owner_confirmation="ROLLOVER Q2W4",
                    )
                    raise AssertionError("expected RolloverBlocked")
                except rollover.RolloverBlocked:
                    pass
            assert client._write_counts["POST"] == 0
            assert client._write_counts["PUT"] == 0
        finally:
            deploy_ledger.DEPLOY_ROOT = orig_deploy
            intake_manifest.staging_dir = orig_staging


def test_preflight_is_get_only_and_zero_write():
    from scripts.canvas_llm_deploy.client import FakeDeployClient
    client = FakeDeployClient(courses={26404: {"id": 26404, "name": "Math"}})
    manifest = {
        "from_week": "Q2W3", "to_week": "Q2W4",
        "scheduled_at": "2026-10-30T20:00:00Z", "timezone": "America/New_York",
        "academic_courses": [], "homeroom": None,
        "weekly_announcements": [], "assignments": [], "assessment_reminders": [],
    }
    result = rollover.run_preflight(
        2, 3, 2, 4, client=client, manifest_override=manifest,
    )
    assert result["canvas_writes"] == 0
    assert client._write_counts["POST"] == 0
    assert client._write_counts["PUT"] == 0
    assert client._write_counts["PATCH"] == 0
    assert client._write_counts["DELETE"] == 0


def _run():
    fns = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    failed = 0
    for name, fn in fns:
        try:
            fn()
            print(f"PASS {name}")
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"FAIL {name}: {exc}")
    print(f"RESULT: {len(fns) - failed} passed, {failed} failed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    _run()
