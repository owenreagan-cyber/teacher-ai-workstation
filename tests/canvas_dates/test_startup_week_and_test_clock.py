"""Date handling: None-safe startup-week selection and the TAW_TODAY test clock.

Run: python3.12 -m unittest discover -s tests/canvas_dates -p 'test_*.py'
"""
from __future__ import annotations

import datetime as dt
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.canvas_llm_grade_check import config as gc  # noqa: E402
from scripts.canvas_llm_intake import week_resolution as wr  # noqa: E402
from scripts.canvas_llm_phase22 import phase22_workstation as p22  # noqa: E402
from scripts.teacher_workstation import adapter  # noqa: E402


class StartupWeekTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp = tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR"))
        cls.db = p22.WorkstationDB(Path(cls.tmp.name) / "w.sqlite3")
        cls.db.migrate()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.tmp.cleanup()

    def test_some_weeks_have_no_parsed_dates(self) -> None:
        # Cross-month ranges (e.g. "August 31–September 4") do not parse, so
        # those weeks carry startsOn/endsOn None. The selector must cope.
        undated = [w["code"] for w in p22.load_instructional_weeks() if not w["startsOn"]]
        self.assertIn("Q1W7", undated)

    def test_break_after_an_undated_week_does_not_compare_none(self) -> None:
        # 2026-10-18 is a Sunday between Q2W1 and Q2W2. Before the fix this
        # raised TypeError: '>' not supported between 'NoneType' and 'str'.
        sel = p22.select_startup_week(self.db, dt.date(2026, 10, 18))
        self.assertEqual(sel["mode"], "break")
        self.assertEqual(sel["week"]["code"], "Q2W2")
        sel = p22.select_startup_week(self.db, dt.date(2026, 9, 25))
        self.assertEqual(sel["week"]["code"], "Q2W1")

    def test_unchanged_results_for_normal_dates(self) -> None:
        self.assertEqual(p22.select_startup_week(self.db, dt.date(2026, 7, 1))["mode"], "chooser")
        self.assertEqual(p22.select_startup_week(self.db, dt.date(2027, 7, 1))["mode"], "chooser")
        self.assertEqual(p22.select_startup_week(self.db, dt.date(2026, 7, 21))["week"]["code"], "Q1W1")
        self.assertEqual(p22.select_startup_week(self.db, dt.date(2026, 8, 19))["week"]["code"], "Q1W5")

    def test_no_dated_weeks_falls_back_to_chooser(self) -> None:
        weeks = [{**w, "startsOn": None, "endsOn": None} for w in p22.load_instructional_weeks()]
        with mock.patch.object(p22, "load_instructional_weeks", return_value=weeks):
            sel = p22.select_startup_week(self.db, dt.date(2026, 10, 18))
        self.assertEqual(sel["mode"], "chooser")


class TestClockTest(unittest.TestCase):
    def test_unset_means_real_today(self) -> None:
        with mock.patch.dict(os.environ, {}):
            os.environ.pop("TAW_TODAY", None)
            before = dt.datetime.now(p22.EASTERN).date()
            got = p22.today_eastern()
            after = dt.datetime.now(p22.EASTERN).date()
            self.assertIn(got, (before, after))
            self.assertLess(abs(wr._now_local() - dt.datetime.now(wr._TZ)), dt.timedelta(seconds=5))

    def test_taw_today_pins_every_clock(self) -> None:
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as tmp, \
                mock.patch.dict(os.environ, {"TAW_TODAY": "2026-08-19"}):
            db = p22.WorkstationDB(Path(tmp) / "w.sqlite3")
            db.migrate()
            self.assertEqual(p22.today_eastern(), dt.date(2026, 8, 19))
            self.assertEqual(wr._now_local().date(), dt.date(2026, 8, 19))
            self.assertEqual(adapter._today_local(), "Wednesday, August 19, 2026")
            self.assertEqual(gc.resolve_quarter(), 1)
            self.assertEqual(p22.select_startup_week(db)["week"]["code"], "Q1W5")
        with mock.patch.dict(os.environ, {"TAW_TODAY": "2026-10-28"}):
            self.assertEqual(gc.resolve_quarter(), 2)

    def test_explicit_argument_still_wins(self) -> None:
        with mock.patch.dict(os.environ, {"TAW_TODAY": "2026-08-19"}):
            self.assertEqual(gc.resolve_quarter(dt.date(2027, 1, 13)), 3)


if __name__ == "__main__":
    unittest.main()
