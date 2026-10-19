"""Date-format regression tests (plain-python runnable)."""
import sys
from pathlib import Path

if str(Path(__file__).resolve().parents[2]) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.canvas_llm_phase3 import pacing_extractor as pe
from scripts.canvas_llm_deploy import plan as plan_mod


def test_weekday_date_format():
    # Body/announcement dates use "Day of the week, Month day".
    assert pe.format_weekday_date_iso("2026-10-26") == "Monday, October 26"
    assert pe.format_weekday_date_iso("2026-10-27") == "Tuesday, October 27"
    assert pe.format_weekday_date_iso("2026-10-28") == "Wednesday, October 28"
    assert pe.format_weekday_date_iso("2026-10-29") == "Thursday, October 29"
    assert pe.format_weekday_date_iso("2026-10-30") == "Friday, October 30"


def test_no_slashed_or_iso_dates_in_bodies():
    for d in ("2026-10-26", "2026-10-30"):
        out = pe.format_weekday_date_iso(d)
        assert "/" not in out and out != d
        assert "," in out  # "Monday, October 26"


def test_page_title_compact_exception():
    title = plan_mod._page_title("Q2W3")
    assert title.startswith("Q2W3")
    assert "October 26" in title  # compact "October 26–30, 2026" is allowed


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
