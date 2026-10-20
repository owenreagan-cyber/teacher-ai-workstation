"""Subject-isolation + narrative regression tests (plain-python runnable)."""
import sys
from pathlib import Path

if str(Path(__file__).resolve().parents[2]) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.canvas_llm_rollover import narrative


PRIOR = {
    "days": {
        "Monday": {"date": "2026-10-19",
                   "subjects": {"math": {"raw": "inv 3"}, "reading": {"raw": "41"},
                                "spelling": {"raw": "36"}, "language_arts": {"raw": "5.3, CP20"},
                                "science": {"raw": "Ch. 3"}}},
        "Tuesday": {"date": "2026-10-20",
                    "subjects": {"math": {"raw": "WA6/ FA6*"}, "reading": {"raw": "42"},
                                 "spelling": {"raw": "37"}, "language_arts": {"raw": "5.4, CP21"},
                                 "science": {"raw": "Ramp Lab"}}},
        "Wednesday": {"date": "2026-10-21",
                      "subjects": {"math": {"raw": "L36"}, "reading": {"raw": "43"},
                                   "spelling": {"raw": "38"}, "language_arts": {"raw": "5.5"},
                                   "science": {"raw": "Ramp Lab"}}},
        "Thursday": {"date": "2026-10-22",
                     "subjects": {"math": {"raw": "L37"}, "reading": {"raw": "44"},
                                  "spelling": {"raw": "39"}, "language_arts": {"raw": "5.6"},
                                  "science": {"raw": "Ch. 3"}}},
        "Friday": {"date": "2026-10-23",
                   "subjects": {"math": {"raw": "L38"}, "reading": {"raw": "45"},
                                "spelling": {"raw": "Test 40"}, "language_arts": {"raw": "Review / CP23"},
                                "science": {"raw": "Ch. 3 Check"}}},
    }
}
UPCOMING = {
    "days": {
        "Monday": {"date": "2026-10-26",
                   "subjects": {"math": {"raw": "L39"}, "reading": {"raw": "46"},
                                "spelling": {"raw": "41"}, "language_arts": {"raw": "CH 5 Checkup"},
                                "science": {"raw": "U1 Ch4 Electricity Transfer"}}},
        "Tuesday": {"date": "2026-10-27",
                    "subjects": {"math": {"raw": "L40"}, "reading": {"raw": "47"},
                                 "spelling": {"raw": "42"}, "language_arts": {"raw": "CH 5 Test"},
                                 "science": {"raw": "U1 Ch4 Electricity Detective"}}},
        "Wednesday": {"date": "2026-10-28",
                      "subjects": {"math": {"raw": "Review"}, "reading": {"raw": "48"},
                                   "spelling": {"raw": "43"}, "language_arts": {"raw": "Ch 7 L1 + CP25"},
                                   "science": {"raw": "U1 Ch4 Check (MC)"}}},
        "Thursday": {"date": "2026-10-29",
                     "subjects": {"math": {"raw": "WA7/ FA7*"}, "reading": {"raw": "49"},
                                  "spelling": {"raw": "44"}, "language_arts": {"raw": "Ch 7 L2 + CP26"},
                                  "science": {"raw": "U1 Ch5 Collisions / Crash Lab"}}},
        "Friday": {"date": "2026-10-30",
                   "subjects": {"math": {"raw": "INV 4"}, "reading": {"raw": "50"},
                                "spelling": {"raw": "Test 45"}, "language_arts": {"raw": "Ch 7 Compound + CP27 bridge"},
                                "science": {"raw": "U1 Ch5 Check (MC)"}}},
    }
}

FORBIDDEN = {
    "math": ["Reading Lesson", "Spelling Test", "Shurley", "Electricity",
             "Crash Lab", "chapter checkup", "chapter test"],
    "reading_spelling": ["Written Assessment", "Fact Assessment", "Shurley",
                         "Electricity", "Crash Lab", "chapter checkup"],
    "language_arts": ["Written Assessment", "Fact Assessment", "Reading Lesson",
                      "Spelling Test", "Electricity", "Crash Lab"],
    "science": ["Written Assessment", "Fact Assessment", "Reading Lesson",
                "Spelling Test", "Shurley", "chapter checkup"],
}


def _texts(subject):
    return [narrative.week_in_review(subject, PRIOR),
            narrative.next_week_overview(subject, UPCOMING)]


def test_math_review_math_only():
    rv = narrative.week_in_review("math", PRIOR)
    assert "Math" in rv and "36-38" in rv and "Written Assessment 6" in rv
    assert "Fact Assessment 6" in rv


def test_reading_review_reading_only():
    rv = narrative.week_in_review("reading_spelling", PRIOR)
    assert "Reading" in rv and "41-45" in rv and "Spelling Test 40" in rv


def test_science_overview_science_only():
    ov = narrative.next_week_overview("science", UPCOMING)
    assert "Unit 1" in ov and "Electricity" in ov


def test_no_cross_subject_leakage():
    for subject, toks in FORBIDDEN.items():
        for text in _texts(subject):
            for tok in toks:
                assert tok not in text, (subject, tok, text)


def test_spelling_test_not_a_lesson():
    rv = narrative.week_in_review("reading_spelling", PRIOR)
    assert "36-40" not in rv  # Test 40 is a test, not lesson 40


def test_deterministic():
    assert narrative.week_in_review("math", PRIOR) == narrative.week_in_review("math", PRIOR)
    assert narrative.next_week_overview("science", UPCOMING) == narrative.next_week_overview("science", UPCOMING)


# ---- Assessment-date hardening (§5–§7 of the follow-up contract) ----------

def test_case_a_math_same_day_dual_assessment_dated():
    ov = narrative.next_week_overview("math", UPCOMING)
    assert "Written Assessment 7 and Fact Assessment 7 on Thursday, October 29" in ov, ov


def test_case_b_reading_spelling_dated_test():
    ov = narrative.next_week_overview("reading_spelling", UPCOMING)
    assert "Spelling Test 45 on Friday, October 30" in ov, ov


def test_case_c_language_arts_dated_chapter_test():
    ov = narrative.next_week_overview("language_arts", UPCOMING)
    assert "Chapter 5 Test on Tuesday, October 27" in ov, ov


def test_case_d_science_non_assessment_no_date():
    ov = narrative.next_week_overview("science", UPCOMING)
    for bad in ("Test", "Quiz", "Assessment"):
        assert bad not in ov, (bad, ov)
    assert "on Thursday" not in ov and "on Friday" not in ov, ov


def test_case_e_no_major_assessment_natural():
    # A science week with no test/quiz still yields a natural, non-dated sentence.
    week = {
        "days": {
            "Monday": {"date": "2026-11-02", "subjects": {"science": {"raw": "U2 Ch1 Notes"}}},
            "Tuesday": {"date": "2026-11-03", "subjects": {"science": {"raw": "U2 Ch2 Lab"}}},
        }
    }
    ov = narrative.next_week_overview("science", week)
    assert ov.startswith("Next week, students will "), ov
    assert "on " not in ov, ov


def test_case_f_subject_isolation():
    math_ov = narrative.next_week_overview("math", UPCOMING)
    assert "Spelling Test" not in math_ov and "Chapter 5 Test" not in math_ov, math_ov
    rs_ov = narrative.next_week_overview("reading_spelling", UPCOMING)
    assert "Written Assessment" not in rs_ov and "Chapter 5 Test" not in rs_ov, rs_ov


def test_case_g_date_format():
    for subject in ("math", "reading_spelling", "language_arts"):
        ov = narrative.next_week_overview(subject, UPCOMING)
        for bad in ("2026-10-29", "2026-10-30", "10/29", "Thu 10/29"):
            assert bad not in ov, (subject, bad, ov)


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
