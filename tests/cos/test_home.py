"""cos home: sections, per-section freshness, one failing source, cache-first, greeting by time.
Synthetic data only; every test has its own temp state directory."""
from __future__ import annotations

import contextlib
import fcntl
import io
import json
import os
import stat
from datetime import datetime, timedelta

from support import EDT, REPO_ROOT, StateDirTest

from cos import cli, home
from cos.brief import greeting

FIXTURES = REPO_ROOT / "evals" / "fixtures" / "default"
T0 = datetime(2026, 10, 1, 14, 30, tzinfo=EDT)


class Counting:
    """A fake source fetch: returns data (or raises) and counts calls."""

    def __init__(self, data=None, error: Exception | None = None):
        self.data, self.error, self.calls = data if data is not None else {"v": 1}, error, 0

    def __call__(self):
        self.calls += 1
        if self.error is not None:
            raise self.error
        return dict(self.data)


def fakes(**overrides):
    fns = {name: Counting({"name": name}) for name in home.SECTIONS}
    fns.update(overrides)
    return fns, [home.Source(n, home.INTERVALS[n], fns[n]) for n in home.SECTIONS]


class HomeSnapshotTests(StateDirTest):
    def snap(self, sources, now=T0, **kw):
        return home.snapshot(self.state, sources, now, place="Sims, NC", **kw)

    def test_every_section_carries_freshness(self):
        _, sources = fakes()
        snap = self.snap(sources)
        self.assertEqual(snap["place"], "Sims, NC")
        for name in home.SECTIONS:
            s = snap[name]
            self.assertEqual(set(s), {"status", "generated_at", "interval_s", "reason", "data"}, name)
            self.assertEqual(s["status"], "current", name)
            self.assertIsNone(s["reason"], name)
            self.assertEqual(s["generated_at"], T0.isoformat(timespec="seconds"))
            self.assertEqual(s["interval_s"], home.INTERVALS[name])
            self.assertEqual(s["data"], {"name": name})

    def test_intervals_match_the_plan(self):
        self.assertEqual((home.INTERVALS["weather"], home.INTERVALS["calendar"], home.INTERVALS["reminders"],
                          home.INTERVALS["mac"], home.INTERVALS["builds"]), (900, 300, 300, 30, 600))

    def test_cached_only_runs_nothing_and_says_updating(self):
        fns, sources = fakes()
        snap = self.snap(sources, cached_only=True)
        self.assertEqual(sum(f.calls for f in fns.values()), 0)
        for name in home.SECTIONS:
            self.assertEqual((snap[name]["status"], snap[name]["reason"]), ("updating", "Checking for the first time"))
            self.assertIsNone(snap[name]["data"])

    def test_cache_first_render_returns_the_last_snapshot(self):
        fns, sources = fakes()
        self.snap(sources)
        later = T0 + timedelta(seconds=10)
        snap = self.snap(sources, now=later, cached_only=True)
        self.assertEqual(sum(f.calls for f in fns.values()), len(home.SECTIONS))  # only the first refresh
        self.assertEqual(snap["weather"]["status"], "current")
        self.assertEqual(snap["weather"]["data"], {"name": "weather"})

    def test_cached_section_past_its_interval_is_updating_then_stale(self):
        _, sources = fakes()
        self.snap(sources)
        later = T0 + timedelta(seconds=45)
        cached = self.snap(sources, now=later, cached_only=True)
        self.assertEqual(cached["mac"]["status"], "updating")
        self.assertEqual(cached["mac"]["reason"], "Refreshing · last checked 2:30 PM")
        self.assertEqual(cached["mac"]["data"], {"name": "mac"})  # the numbers stay, the window fades them
        self.assertEqual(cached["weather"]["status"], "current")
        only_weather = self.snap(sources, now=later, only={"weather"})
        self.assertEqual(only_weather["mac"]["status"], "updating")

    def test_each_source_refreshes_on_its_own_interval(self):
        fns, sources = fakes()
        self.snap(sources)
        self.snap(sources, now=T0 + timedelta(seconds=31))
        self.assertEqual(fns["mac"].calls, 2)
        self.assertEqual((fns["weather"].calls, fns["calendar"].calls, fns["builds"].calls), (1, 1, 1))
        self.snap(sources, now=T0 + timedelta(minutes=6))
        self.assertEqual((fns["calendar"].calls, fns["reminders"].calls, fns["weather"].calls), (2, 2, 1))
        self.snap(sources, now=T0 + timedelta(minutes=16))
        self.assertEqual((fns["weather"].calls, fns["builds"].calls), (2, 2))

    def test_one_failing_source_never_blanks_the_others(self):
        fns, sources = fakes(weather=Counting(error=home.SourceError("Open-Meteo is down")),
                             calendar=Counting(error=RuntimeError("boom")))
        snap = self.snap(sources)
        self.assertEqual((snap["weather"]["status"], snap["weather"]["reason"]), ("unavailable", "Open-Meteo is down"))
        self.assertEqual((snap["calendar"]["status"], snap["calendar"]["reason"]), ("unavailable", "RuntimeError"))
        for name in ("reminders", "mac", "needs", "builds", "agents"):
            self.assertEqual(snap[name]["status"], "current", name)

    def test_a_failed_refresh_keeps_the_last_good_data_and_turns_stale(self):
        good = Counting({"temp_f": 61})
        _, sources = fakes(weather=good)
        self.snap(sources)
        good.error = home.SourceError("Open-Meteo is down")
        snap = self.snap(sources, now=T0 + timedelta(minutes=20))
        w = snap["weather"]
        self.assertEqual(w["status"], "stale")
        self.assertEqual(w["data"], {"temp_f": 61})
        self.assertEqual(w["generated_at"], T0.isoformat(timespec="seconds"))
        self.assertEqual(w["reason"], "Couldn't refresh: Open-Meteo is down · last checked 2:30 PM")

    def test_kill_switch_refreshes_nothing(self):
        fns, sources = fakes()
        self.snap(sources)
        snap = self.snap(sources, now=T0 + timedelta(hours=1), stopped=True)
        self.assertEqual(sum(f.calls for f in fns.values()), len(home.SECTIONS))
        self.assertTrue(snap["stopped"])
        self.assertEqual(snap["weather"]["status"], "stale")
        self.assertTrue(snap["weather"]["reason"].startswith("Chief is stopped"))
        empty = home.snapshot(self.state / "other", sources, T0, place=None, stopped=True)
        self.assertEqual((empty["mac"]["status"], empty["mac"]["reason"]), ("unavailable", "Chief is stopped"))

    def test_a_refresh_already_running_returns_the_cache(self):
        fns, sources = fakes()
        lock = home.cache_path(self.state).with_name("home.lock")
        with open(lock, "a") as fh:
            fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
            snap = self.snap(sources)
        self.assertEqual(sum(f.calls for f in fns.values()), 0)
        self.assertEqual(snap["mac"]["status"], "updating")

    def test_cache_file_is_private_and_damage_is_survivable(self):
        _, sources = fakes()
        self.snap(sources)
        path = home.cache_path(self.state)
        self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
        path.write_text("{not json", encoding="utf-8")
        snap = self.snap(sources, cached_only=True)
        self.assertEqual(snap["mac"]["status"], "updating")
        self.assertEqual(self.snap(sources)["mac"]["status"], "current")

    def test_greeting_and_date_are_computed_now_never_cached(self):
        _, sources = fakes()
        evening = datetime(2026, 10, 19, 23, 30, tzinfo=EDT)
        self.assertEqual(self.snap(sources, now=evening)["greeting"], "Good evening, Owen")
        after_midnight = self.snap(sources, now=evening + timedelta(hours=1), cached_only=True)
        self.assertEqual(after_midnight["greeting"], "Working late, Owen")
        self.assertEqual(after_midnight["date"], "Tuesday, October 20")


class GreetingTests(StateDirTest):
    def test_greeting_by_time_of_day_including_after_midnight(self):
        cases = {(0, 0): "Working late", (0, 30): "Working late", (4, 59): "Working late",
                 (5, 0): "Good morning", (11, 59): "Good morning", (12, 0): "Good afternoon",
                 (16, 59): "Good afternoon", (17, 0): "Good evening", (23, 59): "Good evening"}
        for (h, m), want in cases.items():
            self.assertEqual(greeting(datetime(2026, 10, 19, h, m, tzinfo=EDT)), f"{want}, Owen", (h, m))


class ShapingTests(StateDirTest):
    def test_course_code_chips(self):
        self.assertEqual(home.course_chip("SM5: Lesson 42"), ("SM5", "Lesson 42"))
        self.assertEqual(home.course_chip("HIST - Unit review"), ("HIST", "Unit review"))
        self.assertEqual(home.course_chip("Staff meeting"), (None, "Staff meeting"))
        self.assertEqual(home.course_chip("Re: lunch"), (None, "Re: lunch"))

    def test_merge_commits_become_build_rows(self):
        text = ("abc1234\x1fMerge pull request #392 from someone/branch\x1fInclude dates\n\x1f2026-10-19T21:26:38-04:00\x1e\n"
                "def5678\x1fMerge branch 'x'\x1f\x1f2026-10-18T10:00:00-04:00\x1e\n")
        self.assertEqual(home.parse_merges(text), [
            {"title": "Include dates", "ref": "abc1234", "pr": 392, "merged_at": "2026-10-19T21:26:38-04:00"},
            {"title": "Merge branch 'x'", "ref": "def5678", "pr": None, "merged_at": "2026-10-18T10:00:00-04:00"}])

    def test_mac_health_label(self):
        ok = home.mac_data({"memory_free_pct": 60, "cpu_load_pct": 20, "disk_free_gb": 200, "battery_pct": 80,
                            "power_source": "battery power", "ollama_loaded": ["m:latest"]})
        self.assertEqual((ok["health"], ok["attention"], ok["loaded_models"]), ("healthy", [], ["m:latest"]))
        bad = home.mac_data({"memory_free_pct": 9, "cpu_load_pct": 120, "disk_free_gb": 5, "battery_pct": 10,
                             "power_source": "battery power"})
        self.assertEqual(bad["health"], "attention")
        self.assertEqual(len(bad["attention"]), 4)
        charging = home.mac_data({"battery_pct": 10, "power_source": "AC power"})
        self.assertEqual(charging["health"], "healthy")

    def test_reminders_line(self):
        r = home.reminders_data({"reminders": [{"title": "A", "due": "today", "overdue": False},
                                               {"title": "B", "due": "Mon Sep 28", "overdue": True}]})
        self.assertEqual((r["count"], r["overdue"], r["line"]), (2, 1, "2 reminders due (1 overdue)"))
        self.assertEqual(home.reminders_data({"reminders": []})["line"], "No reminders due")


class HomeCliTests(StateDirTest):
    def run_cli(self, *argv):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            code = cli.main(list(argv))
        return code, out.getvalue()

    def setUp(self):
        super().setUp()
        self._old_fixture = os.environ.get("COS_FIXTURE_DIR")
        os.environ["COS_FIXTURE_DIR"] = str(FIXTURES)

    def tearDown(self):
        if self._old_fixture is None:
            os.environ.pop("COS_FIXTURE_DIR", None)
        else:
            os.environ["COS_FIXTURE_DIR"] = self._old_fixture
        super().tearDown()

    def test_fixture_snapshot(self):
        code, out = self.run_cli("home", "--json", "--cached")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["weather"]["status"], "updating")
        code, out = self.run_cli("home", "--json")
        snap = json.loads(out)
        self.assertEqual((snap["greeting"], snap["date"], snap["place"]),
                         ("Good afternoon, Owen", "Thursday, October 1", "Sims, NC"))
        self.assertEqual(snap["weather"]["data"]["temp_f"], 68)
        self.assertEqual(len(snap["weather"]["data"]["days"]), 7)
        self.assertEqual(snap["calendar"]["data"]["count"], 3)
        self.assertEqual(snap["reminders"]["data"]["line"], "3 reminders due (1 overdue)")
        self.assertEqual(snap["mac"]["data"]["memory_free_pct"], 61)
        self.assertEqual([b["ref"] for b in snap["builds"]["data"]["items"]], ["aaaa005", "aaaa004", "aaaa003"])
        self.assertEqual(snap["agents"]["data"], {"available": False, "items": []})

    def test_unknown_section_is_a_usage_error(self):
        code, out = self.run_cli("home", "--json", "--only", "mac,bogus")
        self.assertEqual(code, cli.EXIT_USAGE)
        self.assertEqual(json.loads(out)["error_kind"], "usage")

    def test_polling_writes_no_gate_records(self):
        self.run_cli("home", "--json")
        self.run_cli("home", "--json", "--only", "mac")
        kinds = [json.loads(l)["kind"] for l in (self.state / "audit.jsonl").read_text().splitlines()]
        self.assertNotIn("decision", kinds)
        self.assertEqual(kinds.count("home_refresh"), 1)
