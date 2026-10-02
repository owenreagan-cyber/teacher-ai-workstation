"""Every M1 tool against mocked command and API output (synthetic fixtures)."""
from __future__ import annotations

import json
import os
import stat
import subprocess
from datetime import timedelta
from pathlib import Path

from support import (FIXED_NOW, FakeHttp, FakeOpenRunner, FakeRunner, StateDirTest,
                     fake_helper_app, fixture, make_ctx)

from cos.config import ensure_state_dir
from cos.tools import CmdResult, build_registry
from cos.tools import calendar, mac_status, reminders, status_scripts, time_tool, weather


class RegistryContentsTests(StateDirTest):
    def test_all_m1_tools_registered_read_only(self):
        reg = build_registry(make_ctx(self.config()))
        expected = {"time.now": "P2", "weather.today": "P2", "mac.status": "P1",
                    "calendar.today": "P1", "reminders.due": "P1", "status.daily": "P1",
                    "status.next_action": "P1", "status.local_llm": "P1", "web.search": "P2"}
        self.assertEqual({t.name: t.data_class for t in reg.all()}, expected)
        self.assertTrue(all(t.side_effect == "none" for t in reg.all()))
        self.assertTrue(all(t.timeout_s > 0 for t in reg.all()))


class TimeToolTests(StateDirTest):
    def test_now(self):
        info = time_tool.now_info(make_ctx(self.config()), {})
        self.assertEqual(info["date"], "2026-10-01")
        self.assertEqual(info["weekday"], "Thursday")
        self.assertEqual(info["time"], "7:30 AM")
        self.assertEqual(info["display"], "Thursday, October 1, 2026")

    def test_days_until_and_school_days(self):
        info = time_tool.now_info(make_ctx(self.config()), {"days_until": "2026-10-12"})
        self.assertEqual(info["days_until"]["days"], 11)
        self.assertEqual(info["days_until"]["weekday"], "Monday")
        self.assertEqual(info["days_until"]["school_days"], 7)  # Fri, Mon-Fri, Mon

    def test_bad_date(self):
        self.assertIn("error", time_tool.now_info(make_ctx(self.config()), {"days_until": "soon"}))


class WeatherToolTests(StateDirTest):
    def test_unconfigured_location_reports_how_to_fix(self):
        out = weather.today(make_ctx(self.config()), {})
        self.assertIn("latitude and longitude", out["error"])

    def test_fetch_parse_and_round_coordinates(self):
        http = FakeHttp([fixture("open-meteo.json").encode()])
        out = weather.today(make_ctx(self.config(latitude=35.78712, longitude=-78.64431), http=http), {})
        self.assertEqual(out, {"now_f": 61, "feels_like_f": 60, "conditions": "partly cloudy",
                               "wind_mph": 5, "high_f": 75, "low_f": 55, "rain_chance_pct": 10,
                               "day_conditions": "overcast", "cached": False, "as_of": "7:30 AM"})
        url = http.calls[0]["url"]
        self.assertTrue(url.startswith("https://api.open-meteo.com/v1/forecast?"))
        self.assertIn("latitude=35.79", url)
        self.assertIn("longitude=-78.64", url)
        self.assertNotIn("35.787", url)

    def test_cache_for_30_minutes(self):
        cfg = self.config(latitude=35.78, longitude=-78.64)
        ensure_state_dir(self.state)
        http = FakeHttp([fixture("open-meteo.json").encode(), fixture("open-meteo.json").encode()])
        weather.today(make_ctx(cfg, http=http), {})
        cached = weather.today(make_ctx(cfg, http=http, clock=FIXED_NOW + timedelta(minutes=29)), {})
        self.assertTrue(cached["cached"])
        self.assertEqual(len(http.calls), 1)
        fresh = weather.today(make_ctx(cfg, http=http, clock=FIXED_NOW + timedelta(minutes=31)), {})
        self.assertFalse(fresh["cached"])
        self.assertEqual(len(http.calls), 2)
        cache_file = self.state / "cache" / "weather.json"
        self.assertEqual(stat.S_IMODE(os.stat(cache_file).st_mode), 0o600)

    def test_tool_routes_through_egress_allowlist_by_default(self):
        from cos import egress
        from cos.tools import ToolContext
        self.assertIs(ToolContext(config=self.config()).http, egress.request)


class MacStatusTests(StateDirTest):
    def runner(self, **overrides):
        table = {"batt": fixture("pmset-batt.txt"), "/usr/bin/memory_pressure": fixture("memory-pressure.txt"),
                 "/": fixture("df-k.txt"), "kern.boottime": fixture("boottime.txt")}
        table.update(overrides)
        return FakeRunner(table)

    def test_status_and_one_line(self):
        run = self.runner()
        ctx = make_ctx(self.config(), run=run, loaded_models=lambda: ["qwen3.6:35b"])
        s = mac_status.status(ctx, {})
        self.assertEqual(s["battery_pct"], 80)
        self.assertEqual(s["battery_state"], "AC attached")
        self.assertEqual(s["memory_free_pct"], 60)
        self.assertEqual(s["disk_free_gb"], 1128)
        self.assertEqual(s["uptime"], "2d 14h")
        self.assertEqual(mac_status.one_line(s),
                         "battery 80% (AC attached) · memory 60% free · disk 1128 GB free · up 2d 14h · Ollama: qwen3.6:35b")

    def test_never_lists_processes(self):
        run = self.runner()
        mac_status.status(make_ctx(self.config(), run=run), {})
        for argv, _, _ in run.calls:
            self.assertNotIn("ps", Path(argv[0]).name)
            self.assertTrue(argv[0].startswith("/"), "fixed absolute argv only")

    def test_one_failed_probe_keeps_the_rest(self):
        run = self.runner(**{"/": subprocess.TimeoutExpired("df", 5)})
        ctx = make_ctx(self.config(), run=run, loaded_models=lambda: (_ for _ in ()).throw(OSError()))
        s = mac_status.status(ctx, {})
        self.assertEqual(s["df_error"], "TimeoutExpired")
        self.assertEqual(s["battery_pct"], 80)
        self.assertIn("unavailable", s["ollama_loaded"])

    def test_desktop_mac_without_battery(self):
        self.assertEqual(mac_status.parse_battery("Now drawing from 'AC Power'\n"), {"battery": "unknown"})


class EventKitToolTests(StateDirTest):
    def setUp(self):
        super().setUp()
        ensure_state_dir(self.state)
        self.app = fake_helper_app(self.state)

    def ctx(self, table):
        self.runner = FakeOpenRunner(table)
        return make_ctx(self.config(), run=self.runner, eventkit_app=self.app)

    def test_calendar_today(self):
        out = calendar.today(self.ctx({("events", "--days", "1"): fixture("eventkit-events.json")}), {})
        self.assertEqual(out["count"], 3)
        titles = [(e["title"], e["start"]) for e in out["events"]]
        self.assertEqual(titles, [("Spirit Week", None), ("Planning block", "8:00 AM"),
                                  ("Staff meeting", "3:30 PM")])
        self.assertEqual(set(out["events"][1]), {"title", "all_day", "start", "end", "start_iso", "calendar"})

    def test_launched_through_launchservices_only(self):
        calendar.today(self.ctx({("events", "--days", "1"): fixture("eventkit-events.json")}), {})
        argv = self.runner.calls[0]
        self.assertEqual(argv[:8], ["/usr/bin/open", "-W", "-n", "-g", "-j",
                                    "--env", "COS_EVENTKIT_NO_PROMPT=1", "--stdout"])
        self.assertEqual(argv[argv.index("--args") - 1], str(self.app))
        self.assertNotIn(str(self.app / "Contents" / "MacOS" / "eventkit-reader"), argv)
        self.assertEqual(sorted((self.state / "eventkit").iterdir()), [], "temp output removed")

    def test_every_launch_disables_prompting(self):
        table = {("events", "--days", "1"): fixture("eventkit-events.json"),
                 ("reminders", "--due-within-days", "1"): fixture("eventkit-reminders.json")}
        ctx = self.ctx(table)
        calendar.today(ctx, {})
        reminders.due(ctx, {})
        for argv in self.runner.calls:
            i = argv.index("--env")
            self.assertEqual(argv[i + 1], "COS_EVENTKIT_NO_PROMPT=1")
            self.assertLess(i, argv.index("--args"))

    def test_test_suite_cannot_reach_real_helper(self):
        self.assertFalse(calendar.DEFAULT_APP.exists())
        with self.assertRaises(AssertionError):
            subprocess.run(["/usr/bin/open", "-W", "--args", "status"])

    def test_reminders_due(self):
        out = reminders.due(self.ctx({("reminders", "--due-within-days", "1"): fixture("eventkit-reminders.json")}), {})
        self.assertEqual((out["count"], out["overdue"]), (3, 1))
        self.assertEqual([(r["title"], r["due"], r["overdue"]) for r in out["reminders"]],
                         [("Return library books", "Tue Sep 29", True),
                          ("Order printer toner", "today", False),
                          ("Copy math packets", "2:00 PM", False)])

    def test_access_denied_explains_live_check(self):
        out = calendar.today(self.ctx({("events", "--days", "1"): fixture("eventkit-denied.json")}), {})
        self.assertIn("EventKit access denied", out["error"])
        self.assertIn("cos-m1-live-checks", out["error"])

    def test_wrong_launch_refusal_is_reported(self):
        data = json.dumps({"status": "wrong_launch", "message": "launched as a child of pid 686"})
        out = calendar.today(self.ctx({("events", "--days", "1"): data}), {})
        self.assertIn("refused", out["error"])

    def test_no_output_within_timeout(self):
        runner = lambda argv, timeout, cwd=None: CmdResult(1, "")  # helper wrote nothing
        ctx = make_ctx(self.config(), run=runner, eventkit_app=self.app)
        with self.assertRaises(calendar.HelperError) as cm:
            calendar.call_helper(ctx, ["reminders", "--due-within-days", "1"], timeout=0.2)
        self.assertIn("no JSON", str(cm.exception))

    def test_helper_not_built(self):
        ctx = make_ctx(self.config(), eventkit_app=self.state / "missing.app")
        self.assertIn("not built", calendar.today(ctx, {})["error"])

    def test_long_titles_capped(self):
        data = json.dumps({"status": "ok", "events": [{"title": "x" * 500, "all_day": True}]})
        out = calendar.today(self.ctx({("events", "--days", "1"): data}), {})
        self.assertEqual(len(out["events"][0]["title"]), calendar.TITLE_CAP)


class StatusScriptTests(StateDirTest):
    def test_output_passed_through_unchanged(self):
        text = fixture("status-daily.txt")
        run = FakeRunner({"--daily-status": text})
        cfg = self.config()
        out = status_scripts.run_status(make_ctx(cfg, run=run), "--daily-status")
        self.assertEqual(out["output"], text)
        self.assertEqual((out["exit_code"], out["truncated"]), (0, False))
        argv, timeout, cwd = run.calls[0]
        self.assertEqual(argv, [str(cfg.repo_root / "bin" / "chief-of-staff"), "--daily-status"])
        self.assertEqual((timeout, cwd), (status_scripts.TIMEOUT_S, cfg.repo_root))

    def test_size_limit(self):
        run = FakeRunner({"--next-action": "y" * 10_000})
        out = status_scripts.run_status(make_ctx(self.config(), run=run), "--next-action")
        self.assertEqual(len(out["output"]), status_scripts.OUTPUT_CAP)
        self.assertTrue(out["truncated"])

    def test_timeout(self):
        run = FakeRunner({"--local-llm-workstation-status": subprocess.TimeoutExpired("x", 20)})
        out = status_scripts.run_status(make_ctx(self.config(), run=run), "--local-llm-workstation-status")
        self.assertIn("timed out", out["error"])

    def test_only_the_three_approved_flags(self):
        flags = [flag for _, flag, _, _ in status_scripts.SCRIPTS]
        self.assertEqual(flags, ["--daily-status", "--next-action", "--local-llm-workstation-status"])


if __name__ == "__main__":
    import unittest
    unittest.main()
