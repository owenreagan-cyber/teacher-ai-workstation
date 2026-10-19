"""Friday 4 PM schedule + lifecycle regression tests (plain-python runnable)."""
import sys
from pathlib import Path

if str(Path(__file__).resolve().parents[2]) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from datetime import datetime, timezone

from scripts.canvas_llm_rollover import schedule


def test_friday_4pm_q2w3():
    assert schedule.friday_rollover_scheduled_at("2026-10-26") == "2026-10-23T20:00:00Z"


def test_friday_4pm_not_hardcoded():
    assert schedule.friday_rollover_scheduled_at("2026-11-02") == "2026-10-30T20:00:00Z"
    # After DST ends (Nov 1, 2026), 4 PM ET is EST (UTC-5): 21:00Z.
    assert schedule.friday_rollover_scheduled_at("2026-11-09") == "2026-11-06T21:00:00Z"


def test_timezone_aware_dst():
    # America/New_York in DST (EDT, UTC-4) on 2026-10-23.
    assert schedule.friday_rollover_scheduled_at("2026-10-26").endswith("20:00:00Z")
    # A January rollover is in EST (UTC-5): 2027-01-08 (Fri) -> 21:00Z.
    assert schedule.friday_rollover_scheduled_at("2027-01-11") == "2027-01-08T21:00:00Z"


def test_lifecycle_held_until_4pm():
    now = datetime(2026, 10, 19, 12, 0, tzinfo=timezone.utc)
    sched = schedule.friday_rollover_scheduled_at("2026-10-26")
    assert schedule.classify_state(scheduled_at=sched, now=now, ready=True,
                                   needs_owen=False, blockers=[], ledger_state=None,
                                   preparing=False) == schedule.HELD_UNTIL_4PM


def test_lifecycle_ready_when_due():
    now = datetime(2026, 10, 23, 20, 0, tzinfo=timezone.utc)
    sched = schedule.friday_rollover_scheduled_at("2026-10-26")
    assert schedule.classify_state(scheduled_at=sched, now=now, ready=True,
                                   needs_owen=False, blockers=[], ledger_state=None,
                                   preparing=False) == schedule.READY


def test_lifecycle_blocked_outranks_needs_owen():
    sched = schedule.friday_rollover_scheduled_at("2026-10-26")
    assert schedule.classify_state(scheduled_at=sched, now=datetime.now(timezone.utc),
                                   ready=False, needs_owen=True, blockers=["x"],
                                   ledger_state=None, preparing=True) == schedule.BLOCKED


def test_lifecycle_verified_terminal():
    sched = schedule.friday_rollover_scheduled_at("2026-10-26")
    assert schedule.classify_state(scheduled_at=sched, now=datetime.now(timezone.utc),
                                   ready=True, needs_owen=False, blockers=[],
                                   ledger_state=schedule.PUBLISHED_VERIFIED,
                                   preparing=False) == schedule.PUBLISHED_VERIFIED


def _run():
    import sys
    fns = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    failed = 0
    for name, fn in fns:
        try:
            fn()
            print(f"PASS {name}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"FAIL {name}: {e}")
    print(f"RESULT: {len(fns) - failed} passed, {failed} failed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    _run()
