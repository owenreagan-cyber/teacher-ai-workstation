"""Announcement active-feed identity, message normalization, and idempotency."""
import sys
from datetime import datetime, timezone
from pathlib import Path

if str(Path(__file__).resolve().parents[2]) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.canvas_llm_deploy.client import FakeDeployClient
from scripts.canvas_llm_intake import scheduling as sched
from scripts.canvas_llm_rollover.rollover import (
    _announcement_in_active_feed,
    _canvas_comparable_announcement_message,
)


def test_active_feed_membership_uses_topic_id_not_recurring_title():
    client = FakeDeployClient(courses={26404: {"id": 26404, "name": "Math"}})
    title = "Math Canvas Weekly Update"
    prior = client.create_announcement(
        26404, title=title, message="<p>Q2W4 body</p>",
        published=True, delayed_post_at=None,
    )
    held = client.create_announcement(
        26404, title=title, message="<p>Q2W5 body</p>",
        published=True, delayed_post_at="2027-06-01T20:00:00Z",
    )
    now = datetime(2026, 11, 8, 12, 0, tzinfo=timezone.utc)
    in_feed_prior = _announcement_in_active_feed(client, 26404, prior["id"])
    in_feed_held = _announcement_in_active_feed(client, 26404, held["id"])
    assert in_feed_prior is True
    assert in_feed_held is False
    state_prior = sched.classify_announcement(
        delayed_post_at=prior.get("delayed_post_at"),
        posted_at="2026-10-31T04:47:45Z",
        published=True,
        in_active_feed=in_feed_prior,
        now=now,
    )
    state_held = sched.classify_announcement(
        delayed_post_at=held.get("delayed_post_at"),
        posted_at="2026-11-08T05:28:05Z",
        published=True,
        in_active_feed=in_feed_held,
        now=now,
    )
    assert state_prior == sched.POSTED
    assert state_held == sched.HELD_SCHEDULED
    assert state_held != sched.PREMATURE_LIVE


def test_canvas_comparable_announcement_message_decodes_harmless_entities():
    authored = '<a href="https://example.com/x?a=1&b=2">link</a>'
    canvas = '<a href="https://example.com/x?a=1&amp;b=2">link</a>'
    assert _canvas_comparable_announcement_message(authored) == _canvas_comparable_announcement_message(canvas)
    different = '<a href="https://example.com/x?a=1&b=3">link</a>'
    assert _canvas_comparable_announcement_message(authored) != _canvas_comparable_announcement_message(different)


def test_weekly_idempotent_skip_does_not_duplicate_on_second_post_count():
    client = FakeDeployClient(courses={26404: {"id": 26404, "name": "Math"}})
    title = "Math Canvas Weekly Update"
    message = "<p>Good afternoon,</p><p>Week 5 agenda</p>"
    delayed = "2027-06-01T20:00:00Z"
    client.create_announcement(
        26404, title=title, message="<p>Prior week</p>",
        published=True, delayed_post_at=None,
    )
    first = client.create_announcement(
        26404, title=title, message=message,
        published=True, delayed_post_at=delayed,
    )
    posts_before = client._write_counts["POST"]
    matches = []
    for item in client.list_announcements(26404):
        if (item.get("title") or "") != title:
            continue
        cand = client.get_announcement(26404, str(item["id"]))
        live = _canvas_comparable_announcement_message(cand.get("message") or "")
        exp = _canvas_comparable_announcement_message(message)
        if live == exp and cand.get("delayed_post_at") == delayed:
            matches.append(cand)
    assert len(matches) == 1
    assert matches[0]["id"] == first["id"]
    assert client._write_counts["POST"] == posts_before


def _run():
    failed = 0
    fns = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
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
