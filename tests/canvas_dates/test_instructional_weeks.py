"""The shared instructional-weeks parser and every reader that uses it.

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

from scripts import instructional_weeks as iw  # noqa: E402
from scripts.canvas_llm_grade_check import config as gc  # noqa: E402
from scripts.canvas_llm_grade_check import health as gh  # noqa: E402
from scripts.canvas_llm_intake import week_resolution as wr  # noqa: E402
from scripts.canvas_llm_phase22 import phase22_workstation as p22  # noqa: E402
from scripts.canvas_llm_phase3 import pacing_extractor as pe  # noqa: E402

D = dt.date


class ParseWeekRangeTest(unittest.TestCase):
    def test_same_month(self) -> None:
        self.assertEqual(iw.parse_week_range("Q1W1 - July 20-24, 2026"), (D(2026, 7, 20), D(2026, 7, 24)))
        self.assertEqual(iw.parse_week_range("Q2W3 -  October 26–30, 2026"), (D(2026, 10, 26), D(2026, 10, 30)))

    def test_cross_month(self) -> None:
        self.assertEqual(iw.parse_week_range("August 31–September 4, 2026"), (D(2026, 8, 31), D(2026, 9, 4)))
        self.assertEqual(iw.parse_week_range("November 30 – December 4, 2026"), (D(2026, 11, 30), D(2026, 12, 4)))

    def test_cross_year(self) -> None:
        self.assertEqual(iw.parse_week_range("December 28 – January 1, 2027"), (D(2026, 12, 28), D(2027, 1, 1)))
        self.assertEqual(iw.parse_week_range("Dec 28-Jan 1, 2027"), (D(2026, 12, 28), D(2027, 1, 1)))

    def test_every_dash_with_or_without_spaces(self) -> None:
        want = (D(2026, 11, 30), D(2026, 12, 4))
        for dash in ("-", "–", "—"):
            for sep in (dash, f" {dash} ", f" {dash}", f"{dash} "):
                with self.subTest(sep=sep):
                    self.assertEqual(iw.parse_week_range(f"November 30{sep}December 4, 2026"), want)

    def test_abbreviated_months(self) -> None:
        want = (D(2026, 11, 30), D(2026, 12, 4))
        self.assertEqual(iw.parse_week_range("Nov 30 – Dec 4, 2026"), want)
        self.assertEqual(iw.parse_week_range("Nov. 30 – Dec. 4, 2026"), want)
        self.assertEqual(iw.parse_week_range("Sept 7-11, 2026"), (D(2026, 9, 7), D(2026, 9, 11)))

    def test_subtitle_and_nbsp(self) -> None:
        self.assertEqual(
            iw.parse_week_range("Quarter 2, Week 7 |&nbsp;November 30–December 4, 2026"),
            (D(2026, 11, 30), D(2026, 12, 4)),
        )

    def test_unparsable(self) -> None:
        for text in ("", None, "Q1W1", "Quarter 1, Week 1", "Smarch 3-7, 2026", "February 30-31, 2027", "July 24-20, 2026"):
            with self.subTest(text=text):
                self.assertIsNone(iw.parse_week_range(text))


class ConfigWeeksTest(unittest.TestCase):
    """Every week in the committed config, through every reader."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.weeks = iw.load_weeks()

    def test_every_week_has_dates_in_order_without_overlap(self) -> None:
        self.assertEqual(len(self.weeks), 37)
        prev_end = None
        for w in self.weeks:
            with self.subTest(code=w["code"]):
                self.assertIsNotNone(w["startsOn"])
                self.assertIsNotNone(w["endsOn"])
                self.assertLessEqual(w["startsOn"], w["endsOn"])
                if prev_end is not None:
                    self.assertGreater(w["startsOn"], prev_end)
                prev_end = w["endsOn"]

    def test_cross_month_weeks_exact_dates(self) -> None:
        by_code = {w["code"]: (w["startsOn"], w["endsOn"]) for w in self.weeks}
        self.assertEqual(by_code["Q1W7"], ("2026-08-31", "2026-09-04"))
        self.assertEqual(by_code["Q2W7"], ("2026-11-30", "2026-12-04"))
        self.assertEqual(by_code["Q4W9"], ("2027-05-31", "2027-06-04"))

    def test_every_reader_agrees(self) -> None:
        p22_weeks = {w["code"]: (w["startsOn"], w["endsOn"]) for w in p22.load_instructional_weeks()}
        for w in self.weeks:
            want = (w["startsOn"], w["endsOn"])
            with self.subTest(code=w["code"]):
                self.assertEqual(p22_weeks[w["code"]], want)
                start, end = pe.week_bounds_from_title(w["pageTitle"])
                self.assertEqual((start.date().isoformat(), end.date().isoformat()), want)
                start, end = gc._parse_week_dates(w["pageTitle"])
                self.assertEqual((start.isoformat(), end.isoformat()), want)
                self.assertEqual(wr._week_start(w).isoformat(), w["startsOn"])

    def test_grade_check_quarters_and_school_days(self) -> None:
        self.assertEqual(
            gc.quarter_date_ranges(),
            {
                1: (D(2026, 7, 20), D(2026, 9, 18)),
                2: (D(2026, 10, 12), D(2026, 12, 18)),
                3: (D(2027, 1, 11), D(2027, 3, 12)),
                4: (D(2027, 4, 5), D(2027, 6, 11)),
            },
        )
        days, label = gh.school_days()
        self.assertEqual(len(days), 37 * 5)
        self.assertIn(D(2026, 12, 1), days)
        self.assertNotIn(D(2026, 11, 25), days)  # Thanksgiving week is a break
        self.assertTrue(label.startswith("instructional-week calendar"))


class StartupWeekCrossMonthTest(unittest.TestCase):
    def test_dec_1_starts_in_q2w7(self) -> None:
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as tmp, \
                mock.patch.dict(os.environ, {"TAW_TODAY": "2026-12-01"}):
            db = p22.WorkstationDB(Path(tmp) / "w.sqlite3")
            db.migrate()
            sel = p22.select_startup_week(db)
            self.assertNotEqual(sel["mode"], "break")
            self.assertEqual(sel["week"]["code"], "Q2W7")
            self.assertEqual(p22.instructional_week_for_date(p22.today_eastern())["code"], "Q2W7")
            self.assertEqual(wr.current_week(), (2, 7))
            self.assertEqual(gc.resolve_quarter(), 2)

    def test_q1w7_and_q4w9_resolve(self) -> None:
        self.assertEqual(wr.current_week(today=D(2026, 9, 2)), (1, 7))
        self.assertEqual(wr.current_week(today=D(2027, 6, 4)), (4, 9))
        self.assertEqual(p22.instructional_week_for_date(D(2026, 9, 2))["code"], "Q1W7")
        self.assertEqual(p22.instructional_week_for_date(D(2027, 6, 1))["code"], "Q4W9")


if __name__ == "__main__":
    unittest.main()
