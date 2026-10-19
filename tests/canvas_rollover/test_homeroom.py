"""Homeroom copy-forward regression tests (plain-python runnable)."""
import sys
from pathlib import Path

if str(Path(__file__).resolve().parents[2]) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from datetime import date

from scripts.canvas_llm_rollover import homeroom


def test_next_page_content_copied():
    content = homeroom.load_approved_content()
    proposed = homeroom.copy_forward(content, today=date(2026, 10, 23),
                                     to_date_range={"start": "2026-10-26", "end": "2026-10-30"})
    psec = homeroom._sections(proposed)
    sec = homeroom._sections(content)
    assert psec["classMotto"]["motto"] == sec["classMotto"]["motto"]
    assert psec["behaviorTracker"]["title"] == "Behavior Tracker"
    assert psec["carpool"]["rules"] == sec["carpool"]["rules"]


def test_future_dates_preserved():
    content = homeroom.load_approved_content()
    proposed = homeroom.copy_forward(content, today=date(2026, 10, 23))
    dates = [d.get("date") for d in homeroom._sections(proposed)["importantDates"]["dates"]]
    assert "October 30" in dates
    assert "November 6" in dates
    assert "December 22" in dates


def test_expired_dates_removed():
    content = homeroom.load_approved_content()
    proposed = homeroom.copy_forward(content, today=date(2026, 10, 23))
    dates = [d.get("date") for d in homeroom._sections(proposed)["importantDates"]["dates"]]
    assert "Tuesday, October 20" not in dates
    assert "pictureRetakes" not in homeroom._sections(proposed)


def test_motto_and_links_preserved():
    content = homeroom.load_approved_content()
    proposed = homeroom.copy_forward(content, today=date(2026, 10, 23))
    psec = homeroom._sections(proposed)
    assert psec["familyQuickLinks"]["links"] == homeroom._sections(content)["familyQuickLinks"]["links"]
    assert psec["contactGuidance"]["body"] == homeroom._sections(content)["contactGuidance"]["body"]


def test_no_new_page_created():
    # copy_forward is a pure transform; it never touches Canvas or creates pages.
    content = homeroom.load_approved_content()
    proposed = homeroom.copy_forward(content, today=date(2026, 10, 23))
    assert set(homeroom._sections(proposed)) <= set(homeroom._sections(content)) | {"_week_identity"}


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
