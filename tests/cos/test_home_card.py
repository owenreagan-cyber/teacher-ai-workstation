"""Home card (deterministic, no model): greeting, date, next event, reminders, weather, error states."""
from __future__ import annotations

import contextlib
import io
import json
import os
from datetime import datetime

from support import EDT, REPO_ROOT, StateDirTest

from cos import cli
from cos.brief import greeting, home_card

AT = lambda h, m=0: datetime(2026, 10, 1, h, m, tzinfo=EDT)  # noqa: E731 - a Thursday
EVENTS = {"date": "2026-10-01", "count": 3, "events": [
    {"title": "Test All-Day Event C", "all_day": True, "start": None, "start_iso": "2026-10-01T00:00:00-04:00"},
    {"title": "Test Event A", "all_day": False, "start": "9:00 AM", "start_iso": "2026-10-01T09:00:00-04:00"},
    {"title": "Test Event B", "all_day": False, "start": "3:30 PM", "start_iso": "2026-10-01T15:30:00-04:00"}]}
REMINDERS = {"count": 3, "overdue": 1, "reminders": [
    {"title": "Test Reminder B", "overdue": True}, {"title": "Test Reminder A", "overdue": False},
    {"title": "Test Reminder C", "overdue": False}]}
WEATHER = {"now_f": 68, "conditions": "partly cloudy", "high_f": 74, "low_f": 55, "rain_chance_pct": 20}
FULL = {"calendar.today": EVENTS, "reminders.due": REMINDERS, "weather.today": WEATHER}


class GreetingTests(StateDirTest):
    def test_time_of_day_greeting_names_owen(self):
        for hour, want in ((5, "Good morning"), (11, "Good morning"), (12, "Good afternoon"),
                           (16, "Good afternoon"), (17, "Good evening"), (23, "Good evening"),
                           (0, "Good evening"), (4, "Good evening")):
            self.assertEqual(greeting(AT(hour)), f"{want}, Owen", hour)


class HomeCardTests(StateDirTest):
    def test_full_card(self):
        card = home_card(FULL, AT(8, 15))
        self.assertEqual((card["greeting"], card["date"], card["date_iso"]),
                         ("Good morning, Owen", "Thursday, October 1", "2026-10-01"))
        self.assertEqual(card["calendar"], {"status": "ok", "count": 3,
                                            "next": {"title": "Test Event A", "start": "9:00 AM"},
                                            "text": "Next: 9:00 AM Test Event A · 3 events today"})
        self.assertEqual(card["reminders"], {"status": "ok", "due": 3, "overdue": 1,
                                             "text": "3 reminders due (1 overdue)"})
        self.assertEqual(card["weather"], {"status": "ok", "text": "68°F partly cloudy · H 74 / L 55 · rain 20%"})

    def test_next_event_skips_past_and_all_day_events(self):
        self.assertEqual(home_card(FULL, AT(14, 30))["calendar"]["next"]["title"], "Test Event B")
        self.assertEqual(home_card(FULL, AT(15, 30))["calendar"]["next"]["title"], "Test Event B")
        late = home_card(FULL, AT(18))["calendar"]
        self.assertEqual((late["next"], late["text"]), (None, "No more events · 3 events today"))
        only_all_day = {"events": [EVENTS["events"][0]]}
        cal = home_card({**FULL, "calendar.today": only_all_day}, AT(8))["calendar"]
        self.assertEqual((cal["next"], cal["text"]), (None, "No more events · 1 event today"))

    def test_empty_states(self):
        card = home_card({"calendar.today": {"events": []}, "reminders.due": {"reminders": []},
                          "weather.today": WEATHER}, AT(9))
        self.assertEqual(card["calendar"]["text"], "Nothing scheduled")
        self.assertEqual(card["calendar"]["status"], "empty")
        self.assertEqual(card["reminders"]["text"], "No reminders due")

    def test_unavailable_states_never_leak_the_error(self):
        err = {"error": "EventKit access denied: grant access on the first live run (docs/x.md)\nTraceback"}
        card = home_card({"calendar.today": err, "reminders.due": err, "weather.today": err}, AT(9))
        self.assertEqual(card["calendar"], {"status": "unavailable", "count": 0, "next": None,
                                            "text": "Calendar unavailable"})
        self.assertEqual(card["reminders"]["text"], "Reminders unavailable")
        self.assertEqual(card["weather"]["text"], "Weather unavailable")
        self.assertNotIn("Traceback", json.dumps(card))
        self.assertNotIn("EventKit", json.dumps(card))
        self.assertEqual(home_card({}, AT(9))["calendar"]["text"], "Calendar unavailable")

    def test_one_overdue_and_singular_counts(self):
        card = home_card({**FULL, "reminders.due": {"reminders": [{"title": "x", "overdue": True}]},
                          "calendar.today": {"events": [EVENTS["events"][2]]}}, AT(9))
        self.assertEqual(card["reminders"]["text"], "1 reminder due (1 overdue)")
        self.assertEqual(card["calendar"]["text"], "Next: 3:30 PM Test Event B · 1 event today")


class BriefJsonTests(StateDirTest):
    def run_cli(self, fixtures, *argv):
        os.environ["COS_FIXTURE_DIR"] = str(REPO_ROOT / "evals" / "fixtures" / fixtures)
        try:
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = cli.main(list(argv))
        finally:
            os.environ.pop("COS_FIXTURE_DIR", None)
        return code, out.getvalue()

    def test_brief_json_carries_the_card_and_text_mode_is_unchanged(self):
        code, out = self.run_cli("default", "brief", "--json")
        self.assertEqual(code, 0)
        data = json.loads(out)
        self.assertEqual(set(data), {"ok", "lines", "card"})
        self.assertEqual(data["card"]["greeting"], "Good afternoon, Owen")
        self.assertEqual(data["card"]["calendar"]["next"]["title"], "Test Event B")
        code, text = self.run_cli("default", "brief")
        self.assertTrue(text.startswith("Daily Brief — "))
        self.assertNotIn("Good afternoon", text)

    def test_brief_json_while_stopped_has_no_card(self):
        self.run_cli("default", "stop")
        code, out = self.run_cli("default", "brief", "--json")
        data = json.loads(out)
        self.assertEqual((code, data["ok"], data["error_kind"]), (3, False, "stopped"))
        self.assertNotIn("card", data)


if __name__ == "__main__":
    import unittest
    unittest.main()
