"""Brief formatting (deterministic, <=15 lines) and CLI behavior offline."""
from __future__ import annotations

import contextlib
import io
import json

from support import FakeRunner, StateDirTest, fixture, make_ctx

from cos import cli
from cos.brief import MAX_LINES, format_brief, gather
from cos.config import ensure_state_dir
from cos.policy import KillSwitch, PolicyGate
from cos.tools import build_registry

SAMPLE = {
    "time.now": {"display": "Thursday, October 1, 2026"},
    "weather.today": {"now_f": 61, "conditions": "partly cloudy", "high_f": 75, "low_f": 55,
                      "rain_chance_pct": 10},
    "calendar.today": {"events": [
        {"title": "Spirit Week", "all_day": True, "start": None},
        {"title": "Planning block", "all_day": False, "start": "8:00 AM"},
        {"title": "Staff meeting", "all_day": False, "start": "3:30 PM"}]},
    "reminders.due": {"reminders": [
        {"title": "Return library books", "due": "Tue Sep 29", "overdue": True},
        {"title": "Copy math packets", "due": "2:00 PM", "overdue": False}]},
    "mac.status": {"battery_pct": 80, "battery_state": "AC attached", "memory_free_pct": 60,
                   "disk_free_gb": 1128, "uptime": "2d 10h", "ollama_loaded": []},
    "status.daily": {"output": fixture("status-daily.txt")},
    "status.next_action": {"output": fixture("status-next-action.txt")},
}

EXPECTED = [
    "Daily Brief — Thursday, October 1, 2026",
    "Weather: 61°F partly cloudy · H 75 / L 55 · rain 10%",
    "Calendar (3):",
    "   all day  Spirit Week",
    "   8:00 AM  Planning block",
    "   3:30 PM  Staff meeting",
    "Reminders due (2):",
    "  - Return library books (overdue since Tue Sep 29)",
    "  - Copy math packets (due 2:00 PM)",
    "Mac: battery 80% (AC attached) · memory 60% free · disk 1128 GB free · up 2d 10h · Ollama: no model loaded",
    "Status:",
    "  Recommended daily focus: Example focus for the synthetic fixture.",
    "  Roadmap immediate mission heading: Example Mission (approval-gated)",
    "  Canvas LLM: frozen (stop marker active)",
]


class BriefFormatTests(StateDirTest):
    def test_exact_deterministic_output(self):
        self.assertEqual(format_brief(SAMPLE), EXPECTED)
        self.assertEqual(format_brief(SAMPLE), format_brief(json.loads(json.dumps(SAMPLE))))

    def test_never_more_than_15_lines(self):
        busy = dict(SAMPLE)
        busy["calendar.today"] = {"events": [{"title": f"Event {i}", "all_day": False, "start": "9:00 AM"}
                                             for i in range(12)]}
        busy["reminders.due"] = {"reminders": [{"title": f"R{i}", "due": "today", "overdue": False}
                                               for i in range(9)]}
        lines = format_brief(busy)
        self.assertLessEqual(len(lines), MAX_LINES)
        self.assertIn("Calendar (12, showing 4):", lines)
        self.assertIn("Reminders due (9, showing 3):", lines)
        self.assertIn("Status:", lines)
        self.assertTrue(all(len(l) <= 120 for l in lines))

    def test_failures_are_one_line_each(self):
        lines = format_brief({"time.now": {"display": "Thursday, October 1, 2026"}})
        self.assertEqual(lines[1], "Weather: unavailable (not run)")
        self.assertEqual(lines[2], "Calendar: unavailable (not run)")
        self.assertEqual(lines[-1], "Status: no highlights")

    def test_gather_uses_gate_and_kill_switch_blocks_it(self):
        ensure_state_dir(self.state)
        cfg = self.config()
        run = FakeRunner({"batt": fixture("pmset-batt.txt"), "/usr/bin/memory_pressure": fixture("memory-pressure.txt"),
                          "/": fixture("df-k.txt"), "kern.boottime": fixture("boottime.txt"),
                          "--daily-status": fixture("status-daily.txt"),
                          "--next-action": fixture("status-next-action.txt")})
        ctx = make_ctx(cfg, run=run, eventkit_helper=self.state / "missing")
        reg = build_registry(ctx)
        ks = KillSwitch(self.state)
        results = gather(reg, PolicyGate(reg, ks))
        self.assertEqual(results["time.now"]["weekday"], "Thursday")
        self.assertIn("not built", results["calendar.today"]["error"])
        ks.stop("test")
        run.calls.clear()
        blocked = gather(reg, PolicyGate(reg, ks))
        self.assertTrue(all("denied" in r["error"] for r in blocked.values()))
        self.assertEqual(run.calls, [])


class CliTests(StateDirTest):
    def run_cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = cli.main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def test_tools_lists_all_read_only(self):
        code, out, _ = self.run_cli("tools")
        self.assertEqual(code, 0)
        self.assertIn("8 tools · mode: read-only", out)
        self.assertNotIn("side_effect=local", out)

    def test_stop_blocks_ask_and_brief_then_resume(self):
        self.assertEqual(self.run_cli("stop", "testing")[0], 0)
        code, out, _ = self.run_cli("ask", "--json", "what time is it")
        self.assertEqual(code, cli.EXIT_STOPPED)
        self.assertFalse(json.loads(out)["ok"])
        self.assertEqual(self.run_cli("brief")[0], cli.EXIT_STOPPED)
        self.assertEqual(self.run_cli("resume")[0], 0)
        self.assertFalse(KillSwitch(self.state).is_set())
        code, out, _ = self.run_cli("audit", "verify")
        self.assertEqual(code, 0)
        self.assertIn("OK: chain intact", out)

    def test_non_local_model_in_config_is_refused(self):
        ensure_state_dir(self.state)
        (self.state / "config.json").write_text(json.dumps({"ollama_url": "https://api.openai.com"}))
        code, out, _ = self.run_cli("ask", "--json", "hi")
        self.assertEqual(code, cli.EXIT_USAGE)
        self.assertIn("must be local Ollama", json.loads(out)["error"])

    def test_ask_requires_question(self):
        self.assertEqual(self.run_cli("ask")[0], cli.EXIT_USAGE)


if __name__ == "__main__":
    import unittest
    unittest.main()
