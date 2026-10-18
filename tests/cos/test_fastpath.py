"""Deterministic fast path (no model) and live-fact authority in the system prompt."""
from __future__ import annotations

import contextlib
import io
import json
from datetime import datetime, timedelta
from unittest import mock

from support import (FIXED_NOW, FakeHttp, FakeRunner, StateDirTest, answer, fixture, make_ctx)

from cos import cli
from cos.agent import Stopped
from cos.config import ensure_state_dir
from cos.fastpath import FastPath, match, normalize
from cos.model import ModelClient
from cos.policy import KillSwitch, PolicyGate
from cos.tools import build_registry

MATCHES = {
    "time": ["what time is it", "What time is it?", "time?", "Time", "what's the time",
             "WHAT’S THE TIME?!", "what time is it right now", "current time"],
    "date": ["what day is it", "What's the date?", "what's today's date", "what’s today’s date",
             "what day is today", "today's date"],
    "days_until": ["how many days until friday", "How many days until Friday?", "days until monday",
                   "how many days till next tuesday", "how many days until 2026-12-18"],
    "weather": ["what's the weather", "weather", "Weather?", "is it going to rain", "will it rain today?",
                "what's the weather like", "how's the weather today"],
    "mac": ["how's my mac", "How's my Mac?", "mac status", "how is my mac doing"],
}
NON_MATCHES = [
    "what time is my meeting",
    "What time is my meeting?",
    "what's the weather like for Saturday's field trip",
    "is my mac fast enough for X",
    "is my mac fast enough for final cut",
    "what time does school start",
    "weather in paris tomorrow",
    "is it going to rain on saturday",
    "how many days until the field trip",
    "how many days until winter break",
    "what day is the assembly",
    "time to leave?",
    "my mac status page is broken",
    "tell me the weather and my calendar",
    "",
]


class Recorder:
    def __init__(self):
        self.events = []

    def __call__(self, kind, **fields):
        self.events.append((kind, fields))

    def kinds(self):
        return [k for k, _ in self.events]


class MatchingTests(StateDirTest):
    def test_anchored_patterns_match_whole_questions(self):
        for intent, questions in MATCHES.items():
            for q in questions:
                with self.subTest(q=q):
                    hit = match(q)
                    self.assertIsNotNone(hit, q)
                    self.assertEqual(hit[0].name, intent)

    def test_keyword_only_questions_fall_through(self):
        for q in NON_MATCHES:
            with self.subTest(q=q):
                self.assertIsNone(match(q), q)

    def test_normalize(self):
        self.assertEqual(normalize("  What’s   the TIME?! "), "whats the time")
        self.assertEqual(normalize("days until 2026-12-18."), "days until 2026-12-18")


class FastPathAnswerTests(StateDirTest):
    def setUp(self):
        super().setUp()
        ensure_state_dir(self.state)
        self.audit = Recorder()
        self.ks = KillSwitch(self.state)

    def fastpath(self, cfg=None, run=None, http=None, loaded=None):
        ctx = make_ctx(cfg or self.config(), run=run, http=http, loaded_models=loaded)
        reg = build_registry(ctx)
        self.registry = reg
        return FastPath(reg, PolicyGate(reg, self.ks, audit=self.audit), ctx.clock, audit=self.audit)

    def test_time_answer_template_and_marker(self):
        result = self.fastpath().answer("What time is it?")
        self.assertEqual(result.text(),
                         "It's 7:30 AM on Thursday, October 1, 2026.\n\n"
                         "Tools used: time.now · fast path (no model)")
        self.assertEqual(result.as_json()["fast_path"], True)
        self.assertIsNone(result.model)

    def test_date_answer(self):
        self.assertEqual(self.fastpath().answer("what's today's date").answer,
                         "Today is Thursday, October 1, 2026.")

    def test_days_until_weekday_and_date(self):
        fp = self.fastpath()
        self.assertEqual(fp.answer("how many days until friday").answer,
                         "1 day until Friday, October 2 (1 weekday, holidays not counted).")
        # Asking for today's weekday means the next one, a week out.
        self.assertTrue(fp.answer("how many days until thursday").answer.startswith(
            "7 days until Thursday, October 8"))
        self.assertEqual(fp.answer("how many days until 2026-10-12").answer,
                         "11 days until Monday, October 12 (7 weekdays, holidays not counted).")

    def test_weather_answer_and_unconfigured(self):
        http = FakeHttp([fixture("open-meteo.json").encode()])
        fp = self.fastpath(cfg=self.config(latitude=35.78, longitude=-78.64), http=http)
        self.assertEqual(fp.answer("is it going to rain?").answer,
                         "Now 61°F and partly cloudy (feels like 60°F). "
                         "Today: high 75°F, low 55°F, 10% chance of rain.")
        self.assertTrue(self.fastpath().answer("weather").answer.startswith("Weather is unavailable:"))

    def test_mac_answer(self):
        run = FakeRunner({"batt": fixture("pmset-batt.txt"),
                          "/usr/bin/memory_pressure": fixture("memory-pressure.txt"),
                          "/": fixture("df-k.txt"), "kern.boottime": fixture("boottime.txt")})
        result = self.fastpath(run=run, loaded=lambda: []).answer("how's my mac")
        self.assertEqual(result.answer, "Mac: battery 80% (AC attached) · memory 60% free · "
                                        "disk 1128 GB free · up 2d 14h · Ollama: no model loaded.")
        self.assertEqual(result.tools_used, ["mac.status"])

    def test_non_match_returns_none_without_audit(self):
        self.assertIsNone(self.fastpath().answer("what time is my meeting"))
        self.assertEqual(self.audit.events, [])

    def test_gate_and_audit_records(self):
        self.fastpath().answer("what time is it")
        kinds = self.audit.kinds()
        self.assertEqual(kinds, ["request", "decision", "tool_result", "answer"])
        request, decision, tool_result, final = (f for _, f in self.audit.events)
        self.assertEqual((request["path"], request["intent"]), ("fast_path", "time"))
        self.assertEqual((decision["subject"], decision["tool"], decision["allowed"]),
                         ("fast_path", "time.now", True))
        self.assertIsInstance(tool_result["tool_ms"], int)
        self.assertEqual((final["path"], final["model_ms"], final["tools_used"]),
                         ("fast_path", 0, ["time.now"]))
        self.assertIsInstance(final["total_ms"], int)

    def test_kill_switch_blocks_fast_path(self):
        run = FakeRunner({})
        fp = self.fastpath(run=run)
        self.ks.stop("test")
        with self.assertRaises(Stopped):
            fp.answer("how's my mac")
        self.assertEqual(run.calls, [], "no tool ran")
        self.assertNotIn("tool_result", self.audit.kinds())
        decision = [f for k, f in self.audit.events if k == "decision"][0]
        self.assertEqual((decision["subject"], decision["allowed"], decision["rule"]),
                         ("fast_path", False, "kill_switch"))
        self.assertEqual(self.audit.kinds()[-1], "request_stopped")
        self.assertIsInstance(self.audit.events[-1][1]["total_ms"], int)

    def test_kill_switch_set_during_tool_discards_answer(self):
        ks = self.ks

        def run(argv, timeout, cwd=None):
            ks.stop("mid fast path")
            raise OSError("probe")

        with self.assertRaises(Stopped):
            self.fastpath(run=run).answer("mac status")
        self.assertEqual(self.audit.kinds()[-1], "request_stopped")


class FastPathCliTests(StateDirTest):
    def run_cli(self, *argv, chat=None):
        out, err = io.StringIO(), io.StringIO()
        fake_registry = lambda ctx: build_registry(make_ctx(self.config()))  # synthetic tools only
        model_chat = chat or (lambda self_, *a, **k: (_ for _ in ()).throw(
            AssertionError("model must not be called on the fast path")))
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err), \
                mock.patch.object(cli, "build_registry", fake_registry), \
                mock.patch.object(ModelClient, "chat", model_chat):
            code = cli.main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def test_fast_path_makes_zero_model_calls(self):
        code, out, _ = self.run_cli("ask", "what time is it")
        self.assertEqual(code, 0)
        self.assertTrue(out.strip().endswith("Tools used: time.now · fast path (no model)"))
        records = [json.loads(l) for l in (self.state / "audit.jsonl").read_text().splitlines()]
        self.assertNotIn("model_call", [r["kind"] for r in records])
        self.assertFalse(any(r.get("subject") == "model_call" for r in records))

    def test_fast_path_json(self):
        code, out, _ = self.run_cli("ask", "--json", "what's the date")
        payload = json.loads(out)
        self.assertEqual((payload["ok"], payload["fast_path"], payload["model"]), (True, True, None))
        self.assertEqual(payload["tools_used"], ["time.now"])

    def test_non_match_uses_agent_loop(self):
        calls = []

        def model_chat(self_, messages, tools=None, fmt=None):
            calls.append(messages)
            return answer("Your meeting is at 3:30 PM."), "qwen3.6:35b"

        code, out, _ = self.run_cli("ask", "--json", "what time is my meeting", chat=model_chat)
        self.assertEqual(code, 0)
        self.assertEqual(len(calls), 1)
        self.assertFalse(json.loads(out)["fast_path"])

    def test_kill_switch_blocks_fast_path_cli(self):
        self.run_cli("stop", "test")
        code, out, err = self.run_cli("ask", "what time is it")
        self.assertEqual(code, cli.EXIT_STOPPED)
        self.assertNotIn("It's", out)
        self.assertIn("kill switch", err)


class LiveFactAuthorityTests(StateDirTest):
    def test_system_prompt_contains_no_current_timestamp(self):
        before = datetime.now()
        prompt = cli.make_agent(cli.build_runtime()).system_prompt
        after = datetime.now()
        self.assertNotIn("Current local date", prompt)
        for moment in {before, after, before - timedelta(minutes=1)}:
            self.assertNotIn(moment.date().isoformat(), prompt)
            self.assertNotIn(moment.strftime("%B ") + str(moment.day) + moment.strftime(", %Y"), prompt)
            self.assertNotIn(moment.strftime("%I:%M %p").lstrip("0"), prompt)
            self.assertNotIn(moment.strftime("%H:%M"), prompt)
        # The prompt does not depend on the clock at all.
        with mock.patch("cos.cli.datetime") as fake_dt:
            fake_dt.now.return_value = datetime(2031, 1, 2, 3, 4)
            self.assertEqual(cli.make_agent(cli.build_runtime()).system_prompt, prompt)

    def test_prompt_and_identity_require_tools_for_live_facts(self):
        prompt = cli.make_agent(cli.build_runtime()).system_prompt
        self.assertIn("come only from tool results", prompt)
        self.assertIn("You never state the current time, date, weather, calendar, or reminders from memory",
                      prompt)


if __name__ == "__main__":
    import unittest
    unittest.main()
