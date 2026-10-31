"""Deterministic Class 4-A birthday engine + weekly Homeroom tests.

All roster values in this file are synthetic. Real roster values are never
printed or committed.
"""
import sys
from datetime import date
from pathlib import Path

if str(Path(__file__).resolve().parents[2]) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import hashlib
import json
import subprocess
import tempfile

from scripts.canvas_llm_deploy.client import FakeDeployClient
from scripts.canvas_llm_intake import manifest as intake_manifest
from scripts.canvas_llm_rollover import birthdays as bday
from scripts.canvas_llm_rollover import homeroom_newsletter as hn
from scripts.canvas_llm_rollover import homeroom_weekly as hw

ROSTER = [
    bday.Birthday("Synthetic January", 1, 9),
    bday.Birthday("Synthetic February", 2, 12),
    bday.Birthday("Synthetic March", 3, 20),
    bday.Birthday("Synthetic April", 4, 12),
    bday.Birthday("Synthetic May", 5, 4),
    bday.Birthday("Synthetic June", 6, 9),
    bday.Birthday("Synthetic July", 7, 1),
    bday.Birthday("Synthetic August", 8, 21),
    bday.Birthday("Synthetic September", 9, 4),
    bday.Birthday("Synthetic October", 10, 13),
    bday.Birthday("Synthetic November", 11, 20),
    bday.Birthday("Synthetic December", 12, 12),
]


def test_every_month_lookup():
    for month in range(1, 13):
        found = bday.birthdays_in_month(month, roster=ROSTER)
        assert len(found) == 1, (month, found)
        assert found[0].month == month


def test_november_birthday_list():
    found = bday.birthdays_in_month(11, roster=ROSTER)
    assert [b.name for b in found] == ["Synthetic November"]
    assert found[0].day == 20


def test_weekly_birthday_lookup():
    # Q2W4: the November birthday is later in the month, so no weekly birthday.
    found = bday.birthdays_in_week(date(2026, 11, 2), date(2026, 11, 6), roster=ROSTER)
    assert found == []
    # A synthetic birthday inside the week is found and sorted.
    roster = ROSTER + [bday.Birthday("Synthetic Weekday", 11, 4)]
    found2 = bday.birthdays_in_week(date(2026, 11, 2), date(2026, 11, 6), roster=roster)
    assert [item.date for item in found2] == [date(2026, 11, 4)]


def test_birthday_on_monday_and_friday():
    mon = bday.birthdays_in_week(
        date(2026, 11, 2), date(2026, 11, 6),
        roster=[bday.Birthday("Synthetic Monday", 11, 2)],
    )
    fri = bday.birthdays_in_week(
        date(2026, 11, 2), date(2026, 11, 6),
        roster=[bday.Birthday("Synthetic Friday", 11, 6)],
    )
    assert mon and mon[0].date == date(2026, 11, 2)
    assert fri and fri[0].date == date(2026, 11, 6)


def test_adjacent_weekend_birthdays():
    prev_sun = bday.birthdays_in_week(
        date(2026, 11, 2), date(2026, 11, 6),
        roster=[bday.Birthday("Synthetic Prev", 11, 1)],
    )
    next_sat = bday.birthdays_in_week(
        date(2026, 11, 2), date(2026, 11, 6),
        roster=[bday.Birthday("Synthetic Next", 11, 7)],
    )
    assert prev_sun and prev_sun[0].date == date(2026, 11, 1)
    assert next_sat and next_sat[0].date == date(2026, 11, 7)


def test_month_boundary():
    found = bday.birthdays_in_week(
        date(2026, 10, 26), date(2026, 10, 30),
        roster=[bday.Birthday("Synthetic Boundary", 11, 1)],
    )
    assert found and found[0].date == date(2026, 11, 1), found


def test_december_january_transition():
    found = bday.birthdays_in_week(
        date(2026, 12, 28), date(2027, 1, 1),
        roster=[bday.Birthday("Synthetic New Year", 1, 2)],
    )
    assert found and found[0].date == date(2027, 1, 2), found
    assert bday.months_in_week(date(2026, 12, 28), date(2027, 1, 1)) == [12, 1]


def test_dst_transition_calendar_arithmetic():
    # Spring forward and fall back do not change calendar-day windows.
    assert (date(2026, 3, 8) - date(2026, 3, 7)).days == 1
    assert (date(2026, 11, 1) - date(2026, 10, 31)).days == 1
    spring = bday.birthdays_in_week(
        date(2026, 3, 2), date(2026, 3, 6),
        roster=[bday.Birthday("Synthetic Spring", 3, 8)],
    )
    fall = bday.birthdays_in_week(
        date(2026, 10, 26), date(2026, 10, 30),
        roster=[bday.Birthday("Synthetic Fall", 11, 1)],
    )
    assert spring and spring[0].date == date(2026, 3, 8)
    assert fall and fall[0].date == date(2026, 11, 1)


def test_empty_birthday_month_and_week():
    assert bday.birthdays_in_month(6, roster=[]) == []
    assert bday.birthdays_in_week(date(2026, 6, 1), date(2026, 6, 5), roster=[]) == []
    assert bday.weekly_shoutout(date(2026, 6, 1), date(2026, 6, 5), roster=[]) == ""


def test_duplicate_prevention():
    source = (
        '<div style="max-width:900px;">'
        '<div><span>Track 2, Week 3 · October 26–30, 2026</span></div>'
        '<div><p style="font-size: 16px; margin: 10px 0 0;">We are looking forward to a great week.</p></div>'
        '<div><h2>📅 Important Dates</h2><div></div></div>'
        '</div>'
    )
    section = hn.build_monthly_birthday_section([(11, [bday.Birthday("Synthetic Kid", 11, 20)])])
    out1 = hn.build_monthly_update(
        source, week_badge="Track 2, Week 4 · November 2–6, 2026",
        intro_paragraph="We are looking forward to a great week.", important_dates=[], birthday_section=section,
    )
    out2 = hn.build_monthly_update(
        out1, week_badge="Track 2, Week 4 · November 2–6, 2026",
        intro_paragraph="We are looking forward to a great week.", important_dates=[], birthday_section=section,
    )
    assert out1.count(hn.BIRTHDAY_SECTION_START) == 1
    assert out2.count(hn.BIRTHDAY_SECTION_START) == 1
    assert out2.count("Synthetic Kid") == 1


def test_html_escaping():
    section = hn.build_monthly_birthday_section([(11, [bday.Birthday("A & B <Kid>", 11, 20)])])
    assert "A &amp; B &lt;Kid&gt;" in section
    assert "<Kid>" not in section
    assert bday.escape_name('A & B <Kid>') == "A &amp; B &lt;Kid&gt;"


def test_roster_authorization_fails_closed():
    for payload, auth in [
        ({"authorized": False, "classLabel": "4-A", "entries": [{"name": "X", "month": 1, "day": 1}]}, {"classLabel": "4-A"}),
        ({"authorized": True, "classLabel": "4-B", "entries": [{"name": "X", "month": 1, "day": 1}]}, {"classLabel": "4-A"}),
        ({"authorized": True, "classLabel": "4-A", "entries": []}, {"classLabel": "4-A"}),
    ]:
        try:
            bday.parse_roster(payload, authorization=auth)
            raise AssertionError("expected BirthdayRosterError")
        except bday.BirthdayRosterError:
            pass


def test_private_roster_git_exclusion():
    path = ".local/canvas-llm/homeroom/class-4a-birthday-roster-2026-2027.json"
    result = subprocess.run(
        ["git", "check-ignore", path], cwd=Path(__file__).resolve().parents[2],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    plan = json.loads((Path(__file__).resolve().parents[2] / "config/curriculum/canvas/homeroom-newsletter-november-2026-plan.json").read_text())
    assert plan["monthlyBirthdays"]["entries"] == []
    assert plan["monthlyBirthdays"]["status"] == "OWNER_APPROVED_PRIVATE_ROSTER"


def test_q2w4_and_q2w5_page_resolution():
    orig = intake_manifest.staging_dir
    with tempfile.TemporaryDirectory() as tmp:
        intake_manifest.staging_dir = lambda q, w: Path(tmp) / f"q{q}w{w}"
        try:
            client = FakeDeployClient(courses={hw.COURSE_ID: {"id": hw.COURSE_ID, "name": "Homeroom"}})
            q4 = client.seed_page(hw.COURSE_ID, "q2w4-november-2-6-2026", title="Q2W4", body="", front_page=False)
            q4["page_id"] = 798094
            q5 = client.seed_page(hw.COURSE_ID, "q2w5-november-9-13-2026", title="Q2W5", body="", front_page=False)
            q5["page_id"] = 798096
            r4 = hw.resolve_page(2, 4, client)
            r5 = hw.resolve_page(2, 5, client)
            assert r4["page_id"] == 798094 and r4["status"] == "FOUND"
            assert r5["page_id"] == 798096 and r5["status"] == "FOUND"
            assert hw.load_page_resolution(2, 4)["slug"] == "q2w4-november-2-6-2026"
            assert hw.load_page_resolution(2, 5)["slug"] == "q2w5-november-9-13-2026"
        finally:
            intake_manifest.staging_dir = orig


def test_duplicate_page_resolution_fails_closed():
    orig = intake_manifest.staging_dir
    with tempfile.TemporaryDirectory() as tmp:
        intake_manifest.staging_dir = lambda q, w: Path(tmp) / f"q{q}w{w}"
        try:
            client = FakeDeployClient(courses={hw.COURSE_ID: {"id": hw.COURSE_ID, "name": "Homeroom"}})
            client.seed_page(hw.COURSE_ID, "q2w4-november-2-6-2026", title="Q2W4", body="")
            client.seed_page(hw.COURSE_ID, "q2w4-copy", title="Q2W4", body="")
            try:
                hw.resolve_page(2, 4, client)
                raise AssertionError("expected HomeroomWeeklyError")
            except hw.HomeroomWeeklyError:
                pass
            assert hw.load_page_resolution(2, 4)["status"] == "DUPLICATE"
        finally:
            intake_manifest.staging_dir = orig


def test_weekly_rollover_manifest_uses_weekly_page():
    orig = intake_manifest.staging_dir
    with tempfile.TemporaryDirectory() as tmp:
        intake_manifest.staging_dir = lambda q, w: Path(tmp) / f"q{q}w{w}"
        try:
            page = {"status": "FOUND", "page_id": 798094, "slug": "q2w4-november-2-6-2026", "title": "Q2W4", "front_page": False}
            hw.write_page_resolution(2, 4, {"schemaVersion": 1, "week": "Q2W4", "course_id": 26429, **page, "method": "LIVE_GET"})
            body = "<div>Weekly newsletter</div>"
            hw.record_preview(2, 4, page=page, body=body, source_body_hash="src", roster_version="v")
            from scripts.canvas_llm_rollover import manifest as rm
            block = rm.build_rollover_manifest(2, 3, 2, 4)["homeroom"]
            assert block["to_page_id"] == 798094
            assert block["to_page_slug"] == "q2w4-november-2-6-2026"
            assert block["mode"] == hw.KIND
            assert block["approved"] is False
        finally:
            intake_manifest.staging_dir = orig


def _run():
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
