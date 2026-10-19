"""Weekly-update announcement regression tests (CASE A–E, plain-python runnable)."""
import sys
from pathlib import Path

if str(Path(__file__).resolve().parents[2]) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from datetime import datetime, timezone

from scripts.canvas_llm_deploy.preflight import classify_weekly_announcement
from scripts.canvas_llm_intake.scheduling import (
    HELD_SCHEDULED,
    classify_announcement,
)

TITLE = "Math Canvas Weekly Update"


def test_case_a_prior_week_same_title():
    proposed = {"title": TITLE, "week_code": "Q2W3", "delayed_post_at": "2026-10-23T20:00:00Z", "agenda_hash": "h3"}
    live = [{"title": TITLE, "week_code": "Q2W2", "delayed_post_at": "2026-10-16T20:00:00Z", "agenda_hash": "h2"}]
    assert classify_weekly_announcement(proposed, live) == "PRIOR_WEEK_SAME_TITLE"


def test_case_b_exact_match_skip():
    proposed = {"title": TITLE, "week_code": "Q2W3", "delayed_post_at": "2026-10-23T20:00:00Z", "agenda_hash": "h3"}
    live = [{"title": TITLE, "week_code": "Q2W3", "delayed_post_at": "2026-10-23T20:00:00Z", "agenda_hash": "h3"}]
    assert classify_weekly_announcement(proposed, live) == "EXACT_MATCH"


def test_case_c_body_changed_same_week():
    proposed = {"title": TITLE, "week_code": "Q2W3", "delayed_post_at": "2026-10-23T20:00:00Z", "agenda_hash": "h3"}
    live = [{"title": TITLE, "week_code": "Q2W3", "delayed_post_at": "2026-10-23T20:00:00Z", "agenda_hash": "h2"}]
    assert classify_weekly_announcement(proposed, live) == "BODY_CHANGED_SAME_WEEK"


def test_case_d_agenda_hash_invariant():
    # The manifest enforces weekly_update_agenda_hash == page_agenda_hash.
    from scripts.canvas_llm_rollover import manifest as rm
    m = rm.build_rollover_manifest(2, 2, 2, 3)
    for a in m["weekly_announcements"]:
        assert a["agenda_hash"] == a["page_agenda_hash"]
        assert a["hash_consistent"] is True


def test_case_e_future_schedule_absent_from_active_feed():
    now = datetime(2026, 10, 19, 12, 0, tzinfo=timezone.utc)
    state = classify_announcement(
        delayed_post_at="2026-10-23T20:00:00Z", posted_at="2026-10-19T01:00:00Z",
        published=True, in_active_feed=False, now=now)
    assert state == HELD_SCHEDULED


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
