"""Response blocks (cos/blocks.py, cos/present.py): validation, what each path returns, links only
as ids, and blocks kept in session history. Synthetic data only."""
from __future__ import annotations

import contextlib
import io
import json
import os
from unittest import mock

from support import REPO_ROOT, StateDirTest

from cos import blocks as B
from cos import cli
from cos.model import ModelClient
from cos.sessions import TurnError, check_turn, read_turns

FIXTURES = REPO_ROOT / "evals" / "fixtures" / "default"
TURN = {"ts": "t", "question": "q", "answer": "a", "tools_used": [], "fast_path": True, "model": None,
        "notices": [], "total_ms": 1}


class ValidationTests(StateDirTest):
    GOOD = [
        {"type": "text", "text": "It's sunny."},
        {"type": "searched", "query": "when do the ny rangers play"},
        {"type": "sources", "items": [{"title": "A", "site": "example.com", "link_id": "lnk-0123456789abcdef"},
                                      {"title": "B", "site": "example.org", "link_id": None}]},
        {"type": "suggestions", "items": [{"label": "Tomorrow", "message": "weather tomorrow"},
                                          {"label": "Hourly", "message": "hourly forecast"}]},
        {"type": "notice", "level": "info", "text": "Note."},
        {"type": "forecast_daily", "place": "Sims, NC", "days": [{"date": "2026-10-02", "label": "tomorrow",
                                                                  "high_f": 66, "low_f": 48, "rain_chance_pct": 60,
                                                                  "conditions": "light rain"}]},
        {"type": "forecast_hourly", "place": "Sims, NC", "points": [{"time": "2 PM", "temp_f": 68, "rain_chance_pct": 20,
                                                                      "conditions": "partly cloudy", "is_day": True}]},
    ]

    def test_good_blocks(self):
        self.assertEqual(B.validate_blocks(self.GOOD), self.GOOD)

    def test_unknown_types_and_bad_fields_are_rejected(self):
        bad = [
            {"type": "html", "html": "<b>x</b>"},
            {"type": "link", "url": "https://example.com"},
            {"text": "no type"},
            {"type": "text", "text": "see https://example.com/x"},
            {"type": "text", "text": "visit www.example.com today"},
            {"type": "text", "text": "x", "extra": 1},
            {"type": "sources", "items": [{"title": "A", "site": "s", "link_id": "https://example.com"}]},
            {"type": "suggestions", "items": [{"label": "Only one", "message": "x"}]},
            {"type": "suggestions", "items": [{"label": "L", "message": "javascript:alert(1)"}] * 2},
            {"type": "notice", "level": "error", "text": "x"},
            {"type": "weather_now", "place": "Sims, NC"},
            {"type": "forecast_daily", "place": "Sims", "days": [{"date": "Oct 2", "label": "x", "high_f": 1,
                                                                  "low_f": 1, "rain_chance_pct": 1, "conditions": "c"}]},
            "text",
        ]
        for b in bad:
            with self.subTest(b=b), self.assertRaises(B.BlockError):
                B.validate_blocks([b])

    def test_resources(self):
        good = [{"id": B.link_id("https://example.com/a"), "url": "https://example.com/a"}]
        self.assertEqual(B.validate_resources(good), good)
        for bad in ([{"id": "x", "url": "https://example.com"}], [{"id": B.link_id("a"), "url": "http://example.com"}],
                    [{"id": B.link_id("a"), "url": "javascript:alert(1)"}], [{"id": B.link_id("a")}]):
            with self.subTest(bad=bad), self.assertRaises(B.BlockError):
                B.validate_resources(bad)

    def test_sessions_keep_valid_blocks_and_refuse_bad_ones(self):
        turn = {**TURN, "blocks": self.GOOD[:2], "resources": []}
        self.assertEqual(check_turn(turn)["blocks"], self.GOOD[:2])
        with self.assertRaises(TurnError):
            check_turn({**TURN, "blocks": [{"type": "html", "html": "x"}]})
        self.assertNotIn("blocks", check_turn(TURN))  # old turns stay valid


class PathBlockTests(StateDirTest):
    def ask(self, question, session="b"):
        os.environ["COS_FIXTURE_DIR"] = str(FIXTURES)
        self.addCleanup(os.environ.pop, "COS_FIXTURE_DIR", None)
        out = io.StringIO()
        model = lambda self_, messages, tools=None, fmt=None: (  # noqa: E731
            {"role": "assistant", "content": "The Rangers play Friday (see https://evil.example/x)."}, "fake-model")
        with mock.patch.object(ModelClient, "chat", model), contextlib.redirect_stdout(out):
            self.assertEqual(cli.main(["ask", "--session", session, "--json", "--", question]), 0)
        res = json.loads(out.getvalue())
        B.validate_blocks(res["blocks"])
        B.validate_resources(res["resources"])
        return res

    def types(self, res):
        return [b["type"] for b in res["blocks"]]

    def test_weather_blocks(self):
        res = self.ask("weather")
        self.assertEqual(self.types(res), ["text", "weather_now", "suggestions"])
        now = res["blocks"][1]
        self.assertEqual((now["place"], now["temp_f"], now["conditions"], now["is_day"]), ("Sims, NC", 68, "partly cloudy", True))
        self.assertEqual([i["message"] for i in res["blocks"][2]["items"]],
                         ["weather tomorrow", "hourly forecast", "5 day forecast", "weather at work"])
        self.assertIn("forecast_daily", self.types(self.ask("5 day forecast")))
        self.assertEqual(len(self.ask("5 day forecast")["blocks"][1]["days"]), 5)
        self.assertIn("forecast_hourly", self.types(self.ask("hourly forecast")))

    def test_search_blocks_carry_link_ids_not_urls(self):
        res = self.ask("when do the ny rangers play?")
        self.assertEqual(self.types(res), ["text", "searched", "sources"])
        self.assertEqual(res["blocks"][0]["text"], "The Rangers play Friday (see).")
        self.assertEqual(res["blocks"][1]["query"], "when do the ny rangers play")
        items = res["blocks"][2]["items"]
        self.assertEqual([i["site"] for i in items][:2], ["example.com", "example.org"])
        self.assertNotIn("http", json.dumps(res["blocks"]))
        self.assertEqual({r["id"] for r in res["resources"]}, {i["link_id"] for i in items})
        self.assertTrue(all(r["url"].startswith("https://example.") for r in res["resources"]))

    def test_blocks_and_resources_survive_in_history(self):
        res = self.ask("when do the ny rangers play?", session="keep")
        turn = read_turns(self.state, "keep")[-1]
        self.assertEqual((turn["blocks"], turn["resources"]), (res["blocks"], res["resources"]))

    def test_fixed_answers_offer_follow_ups(self):
        for q in ("what can you do?", "brief", "weather in raleigh"):
            with self.subTest(q=q):
                self.assertEqual(self.types(self.ask(q))[-1], "suggestions")
